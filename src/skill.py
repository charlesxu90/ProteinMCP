#!/usr/bin/env python3
"""
Defines the Skill class, which represents a workflow skill.
"""

import re
import shutil
from pathlib import Path


class Skill:
    """Represents a workflow skill defined in a markdown file."""

    def __init__(self, name: str, file_path: Path):
        """
        Initializes a Skill instance.

        Args:
            name: The name of the skill, derived from the filename.
            file_path: The path to the skill's markdown file.
        """
        self.name = name
        self.file_path = file_path

        # Derive command name from skill name
        command_name_base = self.name.replace("_", "-")
        if "modeling" in command_name_base:
            self.command_name = command_name_base.replace("modeling", "model")
        else:
            self.command_name = command_name_base

        self.claude_commands_dir = Path(".claude/commands")
        self.claude_skills_dir = Path(".claude/skills")

        self.command_file_path = self.claude_commands_dir / f"{self.command_name}.md"
        self.skill_file_path = self.claude_skills_dir / f"{self.name.replace('_', '-')}.md"

    @property
    def description(self) -> str:
        """Extracts the description from the skill file."""
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

    def get_required_mcps(self) -> list[str]:
        """Parses the skill file for required MCPs to install."""
        content = self.file_path.read_text()
        matches = re.findall(r"pmcp install ([\w_]+)", content)
        return sorted(list(set(matches)))

    def get_cleanup_mcps(self) -> list[str]:
        """Parses the skill file for MCPs to uninstall during cleanup."""
        content = self.file_path.read_text()
        matches = re.findall(r"pmcp uninstall ([\w\s_]+)", content)
        mcps = []
        for match in matches:
            mcps.extend(match.split())
        return sorted(list(set(mcps)))

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
