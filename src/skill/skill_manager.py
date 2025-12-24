#!/usr/bin/env python3
"""
Manages workflow skills, including loading, installation, and uninstallation.
"""

from pathlib import Path

from ..mcp.install_mcp import install_mcp_cmd, uninstall_mcp_cmd
from .skill import Skill


class SkillManager:
    """Manages discovery and handling of workflow skills."""

    def __init__(self, skills_dir="workflow-skills"):
        self.skills_dir = Path(skills_dir)

    def load_available_skills(self) -> dict[str, Skill]:
        """Loads all available skills from the skills directory."""
        skills = {}
        if not self.skills_dir.exists():
            return skills
        for f in self.skills_dir.glob("*.md"):
            skill_name = f.stem
            if skill_name.endswith("_skill"):
                skill_name = skill_name[:-6]
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

        cleanup_mcps = skill.get_cleanup_mcps()
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
