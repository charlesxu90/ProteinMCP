#!/usr/bin/env python3
"""
Defines the Skill class, which represents a workflow skill.
"""

import re
import shutil
from pathlib import Path
from typing import List, Optional


# Path configuration - use absolute paths based on project structure
SCRIPT_DIR = Path(__file__).parent.resolve()  # src/skill/
SRC_DIR = SCRIPT_DIR.parent  # src/
PROJECT_ROOT = SRC_DIR.parent  # ProteinMCP root


class Skill:
    """Represents a workflow skill defined in a markdown file."""

    def __init__(
        self,
        name: str,
        file_path: Path,
        description: Optional[str] = None,
        required_mcps: Optional[List[str]] = None,
    ):
        """
        Initializes a Skill instance.

        Args:
            name: The name of the skill, derived from the filename.
            file_path: The path to the skill's markdown file.
            description: Optional description from config (overrides file parsing).
            required_mcps: Optional list of required MCPs from config.
        """
        self.name = name
        self.file_path = file_path
        self._description = description
        self._required_mcps = required_mcps

        # Derive command name from skill name
        command_name_base = self.name.replace("_", "-")
        if "modeling" in command_name_base:
            self.command_name = command_name_base.replace("modeling", "model")
        else:
            self.command_name = command_name_base

        # Use absolute paths based on PROJECT_ROOT so pskill works from any directory
        self.claude_commands_dir = PROJECT_ROOT / ".claude/commands"
        self.claude_skills_dir = PROJECT_ROOT / ".claude/skills"

        self.command_file_path = self.claude_commands_dir / f"{self.command_name}.md"
        self.skill_file_path = self.claude_skills_dir / f"{self.name.replace('_', '-')}.md"

    @property
    def description(self) -> str:
        """Returns description from config or extracts from skill file."""
        # Use config description if available
        if self._description:
            return self._description

        # Fall back to parsing from file
        try:
            content = self.file_path.read_text()
            # Find first non-empty line after the title
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if line.strip().startswith("#"):  # title
                    for desc_line in lines[i + 1 :]:
                        if desc_line.strip():
                            return desc_line.strip()
            return "No description found."
        except Exception:
            return "Could not read description."

    def get_required_mcps(self) -> List[str]:
        """Returns required MCPs from config or parses from skill file."""
        # Use config MCPs if available
        if self._required_mcps is not None:
            return self._required_mcps

        # Fall back to parsing from file
        try:
            content = self.file_path.read_text()
            matches = re.findall(r"pmcp install ([\w_]+)", content)
            return sorted(list(set(matches)))
        except Exception:
            return []

    def get_cleanup_mcps(self) -> List[str]:
        """Returns MCPs to cleanup (same as required_mcps)."""
        # Cleanup MCPs are the same as required MCPs
        return self.get_required_mcps()

    def get_status(self) -> str:
        """Checks if the skill is installed."""
        is_skill_installed = self.skill_file_path.exists()
        is_command_installed = self.command_file_path.exists()

        if is_skill_installed and is_command_installed:
            return "✅ Installed"
        elif is_skill_installed:
            return "🟡 Partially installed (skill only)"
        elif is_command_installed:
            return "🟡 Partially installed (command only)"
        else:
            return "❌ Not Installed"

    def install(self):
        """Installs the skill by copying its file to .claude directories."""
        try:
            self.claude_commands_dir.mkdir(parents=True, exist_ok=True)
            self.claude_skills_dir.mkdir(parents=True, exist_ok=True)

            shutil.copy(self.file_path, self.command_file_path)
            shutil.copy(self.file_path, self.skill_file_path)

            print(f"  Copied skill to: {self.skill_file_path}")
            print(f"  Created command: {self.command_file_path}")
            return True
        except Exception as e:
            print(f"  Error installing skill '{self.name}': {e}")
            return False

    def uninstall(self):
        """Uninstalls the skill by removing its files from .claude directories."""
        removed = False
        try:
            if self.command_file_path.exists():
                self.command_file_path.unlink()
                print(f"  Removed command: {self.command_file_path}")
                removed = True
            if self.skill_file_path.exists():
                self.skill_file_path.unlink()
                print(f"  Removed skill: {self.skill_file_path}")
                removed = True

            if not removed:
                print("  Skill not found, nothing to remove.")
            return True
        except Exception as e:
            print(f"  Error uninstalling skill '{self.name}': {e}")
            return False

    def get_execution_steps(self):
        """Parses the skill file for execution steps (prompts)."""
        content = self.file_path.read_text()
        steps = re.split(r"\n(?:---\n|## Step \d+)", content)

        prompts = []
        for step in steps:
            if "**Prompt:**" in step:
                prompt_text = step.split("**Prompt:**")[1].strip()
                
                # clean up prompt text
                prompt_lines = [line.strip(">").strip() for line in prompt_text.split("\n")]
                cleaned_prompt = "\n".join(line for line in prompt_lines if line)

                title_match = re.search(r"^\s*##\s*(.*)", step, re.MULTILINE)
                title = title_match.group(1).strip() if title_match else "Unnamed Step"
                
                prompts.append({"title": title, "prompt": cleaned_prompt})
        return prompts
