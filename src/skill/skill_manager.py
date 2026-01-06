#!/usr/bin/env python3
"""
Manages workflow skills, including loading, installation, and uninstallation.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from ..mcp.install_mcp import install_mcp_cmd, uninstall_mcp_cmd
from ..mcp.mcp_manager import MCPManager
from .skill import Skill


# Path configuration - use absolute paths based on project structure
SCRIPT_DIR = Path(__file__).parent.resolve()  # src/skill/
SRC_DIR = SCRIPT_DIR.parent  # src/
PROJECT_ROOT = SRC_DIR.parent  # ProteinMCP root

# Path to the skills config file
SKILL_CONFIG_PATH = SCRIPT_DIR / "configs.yaml"
# Default skills directory
DEFAULT_SKILLS_DIR = PROJECT_ROOT / "workflow-skills"


class SkillManager:
    """Manages discovery and handling of workflow skills."""

    def __init__(self, skills_dir: Path = None):
        self.skills_dir = skills_dir if skills_dir is not None else DEFAULT_SKILLS_DIR
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
                    # Resolve path relative to PROJECT_ROOT if not absolute
                    path = Path(file_path)
                    full_path = path if path.is_absolute() else (PROJECT_ROOT / path).resolve()
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

    def _check_mcp_status(self, mcp_names: List[str], cli: str = "claude") -> Tuple[List[str], List[str]]:
        """
        Check which MCPs are already fully installed and which need installation.

        Args:
            mcp_names: List of MCP names to check
            cli: CLI tool to check registration against

        Returns:
            Tuple of (already_installed, needs_installation)
        """
        from ..mcp.mcp import MCPStatus

        mcp_manager = MCPManager()
        already_installed = []
        needs_installation = []

        for mcp_name in mcp_names:
            mcp = mcp_manager.get_mcp(mcp_name)
            if mcp:
                # Check if MCP is both installed and registered
                status = mcp.get_status(cli)
                if status == MCPStatus.BOTH:
                    already_installed.append(mcp_name)
                else:
                    needs_installation.append(mcp_name)
            else:
                # MCP not found, will need to try installing
                needs_installation.append(mcp_name)

        return already_installed, needs_installation

    def install_skill_and_mcps(self, skill_name: str) -> bool:
        """
        Installs a skill and its required MCPs.

        Only installs MCPs that are not already fully installed (both downloaded
        and registered with Claude). This speeds up workflow installation by
        skipping MCPs that are already ready to use.

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
            print(f"\n📊 Checking status of {len(required_mcps)} required MCPs...")
            already_installed, needs_installation = self._check_mcp_status(required_mcps)

            # Report already installed MCPs
            if already_installed:
                print(f"\n✅ Already installed ({len(already_installed)}):")
                for mcp_name in already_installed:
                    print(f"    • {mcp_name}")

            # Install only the MCPs that need installation
            if needs_installation:
                print(f"\n📦 Installing {len(needs_installation)} MCPs: {', '.join(needs_installation)}")
                for mcp_name in needs_installation:
                    print(f"\n--- Installing MCP: {mcp_name} ---")
                    if not install_mcp_cmd(mcp_name, cli="claude"):
                        print(f"⚠️ Failed to install MCP '{mcp_name}'. Continuing...")
                print("\n--- Finished MCP installation ---")
            else:
                print("\n✅ All required MCPs are already installed!")
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
            print(f"\nUnregistering associated MCPs: {', '.join(cleanup_mcps)}")
            for mcp_name in cleanup_mcps:
                print(f"\n--- Unregistering MCP: {mcp_name} ---")
                if not uninstall_mcp_cmd(mcp_name, cli="claude"):
                    print(f"⚠️ Failed to unregister MCP '{mcp_name}'.")
            print("\n--- Finished MCP cleanup ---")
        else:
            print("No MCPs specified for cleanup in this skill.")

        print(f"\n✅ Successfully uninstalled skill '{skill_name}'.")
        return True
