#!/usr/bin/env python3
"""
Manages workflow skills, including loading, installation, and uninstallation.
"""

from pathlib import Path
from typing import Dict, Optional

import yaml

from ..mcp.install_mcp import install_mcp_cmd, uninstall_mcp_cmd
from .skill import Skill


# Path to the skills config file
SKILL_CONFIG_PATH = Path(__file__).parent / "configs.yaml"


class SkillManager:
    """Manages discovery and handling of workflow skills."""

    def __init__(self, skills_dir: str = "workflow-skills"):
        self.skills_dir = Path(skills_dir)
        self._config: Optional[Dict] = None

    def _load_config(self) -> Dict:
        """Load skills configuration from YAML file."""
        if self._config is not None:
            return self._config

        if SKILL_CONFIG_PATH.exists():
            try:
                with open(SKILL_CONFIG_PATH, "r") as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load skill config: {e}")
                self._config = {}
        else:
            self._config = {}

        return self._config

    def load_available_skills(self) -> Dict[str, Skill]:
        """Loads all available skills from config file and skills directory."""
        skills = {}

        # First, load skills from config file
        config = self._load_config()
        if "skills" in config:
            for skill_name, skill_config in config["skills"].items():
                file_path = skill_config.get("file_path", "")
                if file_path:
                    full_path = Path(file_path)
                    if full_path.exists():
                        skills[skill_name] = Skill(
                            name=skill_name,
                            file_path=full_path,
                            description=skill_config.get("description"),
                            required_mcps=skill_config.get("required_mcps"),
                        )

        # Then, scan skills directory for any skills not in config (backward compatibility)
        if self.skills_dir.exists():
            for f in self.skills_dir.glob("*.md"):
                skill_name = f.stem

                # Skip steps files (used for skill creation)
                if skill_name.endswith("_steps"):
                    continue

                if skill_name.endswith("_skill"):
                    skill_name = skill_name[:-6]

                # Only add if not already loaded from config
                if skill_name not in skills:
                    skills[skill_name] = Skill(skill_name, f)

        return skills

    def get_skill(self, skill_name: str) -> Skill | None:
        """
        Retrieves a skill by name.

        Args:
            skill_name: The name of the skill to retrieve.

        Returns:
            A Skill instance if found, otherwise None.
        """
        return self.load_available_skills().get(skill_name)

    def install_skill_and_mcps(self, skill_name: str) -> bool:
        """
        Installs a skill and its required MCPs.

        Args:
            skill_name: The name of the skill to install.

        Returns:
            True if installation was successful, False otherwise.
        """
        skill = self.get_skill(skill_name)
        if not skill:
            print(f"❌ Skill '{skill_name}' not found.")
            return False

        print(f"Installing skill '{skill_name}'...")
        if not skill.install():
            return False

        required_mcps = skill.get_required_mcps()
        if required_mcps:
            print(f"\nInstalling required MCPs: {', '.join(required_mcps)}")
            for mcp_name in required_mcps:
                print(f"\n--- Installing MCP: {mcp_name} ---")
                if not install_mcp_cmd(mcp_name, cli="claude"):
                    print(f"⚠️ Failed to install MCP '{mcp_name}'. Continuing...")
            print("\n--- Finished MCP installation ---")
        else:
            print("No required MCPs found for this skill.")

        print(f"\n✅ Successfully installed skill '{skill_name}'.")
        return True

    def uninstall_skill_and_mcps(self, skill_name: str) -> bool:
        """
        Uninstalls a skill and its associated MCPs.

        Args:
            skill_name: The name of the skill to uninstall.

        Returns:
            True if uninstallation was successful, False otherwise.
        """
        skill = self.get_skill(skill_name)
        if not skill:
            print(f"❌ Skill '{skill_name}' not found.")
            return False

        print(f"Uninstalling skill '{skill_name}'...")
        skill.uninstall()

        # Use required_mcps for cleanup (same MCPs that were installed)
        cleanup_mcps = skill.get_required_mcps()
        if cleanup_mcps:
            print(f"\nCleaning up associated MCPs: {', '.join(cleanup_mcps)}")
            for mcp_name in cleanup_mcps:
                print(f"\n--- Uninstalling MCP: {mcp_name} ---")
                if not uninstall_mcp_cmd(mcp_name, cli="claude"):
                    print(f"⚠️ Failed to uninstall MCP '{mcp_name}'.")
            print("\n--- Finished MCP cleanup ---")
        else:
            print("No MCPs specified for cleanup in this skill.")

        print(f"\n✅ Successfully uninstalled skill '{skill_name}'.")
        return True
