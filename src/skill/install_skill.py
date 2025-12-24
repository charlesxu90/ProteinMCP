#!/usr/bin/env python3
"""
Skill Installation and Execution Tool

This tool manages workflow skills for Claude Code, allowing you to list,
install, execute, and uninstall complex workflows.

Usage:
    pskill avail              # Show all available skills
    pskill status             # Show installed status of skills
    pskill info <skill_name>  # Show details about a skill
    pskill install <skill_name> # Install a skill and its MCPs
    pskill execute <skill_name> # Guide through skill execution
    pskill uninstall <skill_name> # Uninstall skill and cleanup MCPs
"""

import argparse
import textwrap
from typing import List, Tuple

from .skill_manager import SkillManager
from ..mcp.mcp_manager import MCPManager


def show_available_skills(manager: SkillManager):
    """Shows all available skills."""
    print("🔎 Finding available skills in 'workflow-skills/'...")
    skills = manager.load_available_skills()
    if not skills:
        print("  No skills found.")
        return

    print("\n📚 Available Skills:")
    print("=" * 60)
    for name, skill in sorted(skills.items()):
        desc = skill.description[:70] + "..." if len(skill.description) > 70 else skill.description
        print(f"  • {name:<25} {desc}")
    print(f"\nTotal: {len(skills)} skills found.")


def show_status(manager: SkillManager):
    """Shows the installation status of all skills."""
    print("📊 Checking skill installation status...")
    skills = manager.load_available_skills()
    if not skills:
        print("  No skills found to check.")
        return

    print("\nSkill Status:")
    print("=" * 60)
    for name, skill in sorted(skills.items()):
        status = skill.get_status()
        print(f"  • {name:<25} {status}")
    print()


def check_required_mcps(required_mcps: List[str], cli: str = "claude") -> Tuple[List[str], List[str]]:
    """
    Check if required MCPs are installed and registered.

    Args:
        required_mcps: List of MCP names to check
        cli: CLI tool to check registration against

    Returns:
        Tuple of (available_mcps, missing_mcps)
    """
    mcp_manager = MCPManager()
    available = []
    missing = []

    for mcp_name in required_mcps:
        mcp = mcp_manager.get_mcp(mcp_name)
        if mcp and mcp.is_registered(cli):
            available.append(mcp_name)
        else:
            missing.append(mcp_name)

    return available, missing


def show_info(manager: SkillManager, skill_name: str):
    """Displays detailed information about a single skill."""
    skill = manager.get_skill(skill_name)
    if not skill:
        print(f"❌ Skill '{skill_name}' not found.")
        return

    print(f"\nℹ️  Details for Skill: {skill.name}")
    print("=" * 60)
    print(f"  Description: {skill.description}")
    print(f"  File Path: {skill.file_path}")
    print(f"  Status: {skill.get_status()}")
    print(f"  Command Name: '{skill.command_name}'")

    required_mcps = skill.get_required_mcps()
    if required_mcps:
        # Check MCP availability
        available, missing = check_required_mcps(required_mcps)

        print(f"\n  Required MCPs ({len(required_mcps)}):")
        for mcp in required_mcps:
            status = "✅" if mcp in available else "❌"
            print(f"    {status} {mcp}")

        if missing:
            print(f"\n  ⚠️  {len(missing)} MCP(s) not registered. Install with:")
            print(f"      pskill install {skill_name}")
    print()


def execute_skill(manager: SkillManager, skill_name: str):
    """Guides the user through executing a skill."""
    skill = manager.get_skill(skill_name)
    if not skill:
        print(f"❌ Skill '{skill_name}' not found.")
        return

    # Check if required MCPs are available
    required_mcps = skill.get_required_mcps()
    if required_mcps:
        print(f"\n🔍 Checking required MCPs for '{skill_name}'...")
        available, missing = check_required_mcps(required_mcps)

        if missing:
            print(f"\n❌ Missing required MCPs ({len(missing)}):")
            for mcp in missing:
                print(f"    - {mcp}")
            print(f"\n💡 Please install the skill first:")
            print(f"    pskill install {skill_name}")
            print(f"\n   Or install MCPs manually:")
            print(f"    pmcp install {' '.join(missing)}")
            return

        print(f"✅ All {len(available)} required MCPs are available")

    print(f"\n▶️  Executing Skill: {skill.name}")
    print("=" * 70)
    print("This will guide you through the steps defined in the skill file.")
    print("Copy and paste the prompts into your conversation with the assistant.")
    print("=" * 70)

    steps = skill.get_execution_steps()
    if not steps:
        print("\nNo executable steps (prompts) found in this skill.")
        return

    for i, step in enumerate(steps, 1):
        print(f"\n--- Step {i}: {step['title']} ---")
        print("\n📋 Prompt to copy:")
        # Indent the prompt for clarity
        prompt_block = textwrap.indent(step['prompt'], "    ")
        print(prompt_block)

        if i < len(steps):
            input("\nPress Enter to continue to the next step...")

def main():
    """Main function to handle command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Skill Installation and Execution Tool for Claude Code",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent("""
Examples:
  # See all skills you can install
  python -m src.install_skill avail

  # Check which skills are already installed
  python -m src.install_skill status

  # Get more info about a specific skill
  python -m src.install_skill info fitness_modeling

  # Install a skill and all its required tools
  python -m src.install_skill install fitness_modeling

  # Get guided prompts to run an installed skill
  python -m src.install_skill execute fitness_modeling

  # Remove a skill and clean up its tools
  python -m src.install_skill uninstall fitness_modeling
""")
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute", required=True)

    subparsers.add_parser("avail", help="Show all available skills to install.")
    subparsers.add_parser("status", help="Show the installed status of all skills.")
    
    info_parser = subparsers.add_parser("info", help="Show detailed information about a skill.")
    info_parser.add_argument("skill_name", help="The name of the skill.")

    install_parser = subparsers.add_parser("install", help="Install a skill and its required MCPs.")
    install_parser.add_argument("skill_name", help="The name of the skill to install.")

    execute_parser = subparsers.add_parser("execute", help="Guide through the execution of a skill.")
    execute_parser.add_argument("skill_name", help="The name of the skill to execute.")

    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall a skill and clean up its MCPs.")
    uninstall_parser.add_argument("skill_name", help="The name of the skill to uninstall.")

    args = parser.parse_args()
    manager = SkillManager()

    if args.command == "avail":
        show_available_skills(manager)
    elif args.command == "status":
        show_status(manager)
    elif args.command == "info":
        show_info(manager, args.skill_name)
    elif args.command == "install":
        manager.install_skill_and_mcps(args.skill_name)
    elif args.command == "execute":
        execute_skill(manager, args.skill_name)
    elif args.command == "uninstall":
        manager.uninstall_skill_and_mcps(args.skill_name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
