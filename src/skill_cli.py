#!/usr/bin/env python3
"""
ProteinMCP Skill CLI - Skill Management Command Line Interface

Provides unified access to skill management functionality through subcommands:
- skill avail: Show all available skills to install
- skill status: Show installed status of skills
- skill info: Show detailed information about a skill
- skill install: Install a skill and its required MCPs
- skill uninstall: Uninstall a skill and cleanup MCPs
- skill create: Create a new skill interactively
"""

import sys
from pathlib import Path
from typing import List, Tuple

import click

from .skill.skill_manager import SkillManager
from .skill.create_skill import SkillCreator, interactive_add_step
from .mcp.mcp_manager import MCPManager

# Logo for ProteinMCP
LOGO = """\033[31m
  ____            _       _       __  __  ____ ____
 |  _ \\ _ __ ___ | |_ ___(_)_ __ |  \\/  |/ ___| _  \\
 | |_) | '__/ _ \\| __/ _ \\ | '_ \\| |\\/| | |   | |_) |
 |  __/| | | (_) | ||  __/ | | | | |  | | |___|  __/
 |_|   |_|  \\___/ \\__\\___|_|_| |_|_|  |_|\\____|_|
\033[0m"""


class LogoGroup(click.Group):
    """Custom Click Group that displays logo before help text and commands."""

    def format_help(self, ctx, formatter):
        """Override to display logo before help."""
        click.echo(LOGO)
        super().format_help(ctx, formatter)

    def invoke(self, ctx):
        """Override to display logo before running subcommands."""
        # Only show logo if not showing help (help is handled by format_help)
        if not ctx.protected_args or '--help' not in ctx.protected_args:
            if ctx.invoked_subcommand is not None:
                click.echo(LOGO)
        return super().invoke(ctx)


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


@click.group(cls=LogoGroup, invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="skill")
@click.pass_context
def cli(ctx):
    """
    ProteinMCP Skill Manager - Workflow Skills for Claude Code

    A toolkit for installing and managing workflow skills that combine
    multiple MCP servers into cohesive protein engineering workflows.
    """
    # Show help when no command is given
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command(name="avail")
def avail_command():
    """
    Show all available skills that can be installed.

    Scans the workflow-skills directory and displays all skills
    with their descriptions.

    Examples:

      # Show all available skills:
      skill avail
    """
    manager = SkillManager()
    click.echo(f"Finding available skills in '{manager.skills_dir}'...")
    skills = manager.load_available_skills()

    if not skills:
        click.echo("  No skills found.")
        return

    click.echo("\nAvailable Skills:")
    click.echo("=" * 60)
    for name, skill in sorted(skills.items()):
        desc = skill.description[:70] + "..." if len(skill.description) > 70 else skill.description
        click.echo(f"  {name:<25} {desc}")
    click.echo(f"\nTotal: {len(skills)} skills found.")


@cli.command(name="status")
def status_command():
    """
    Show the installation status of all skills.

    Displays which skills are currently installed and registered
    with Claude Code.

    Examples:

      # Show skill installation status:
      skill status
    """
    manager = SkillManager()
    click.echo("Checking skill installation status...")
    skills = manager.load_available_skills()

    if not skills:
        click.echo("  No skills found to check.")
        return

    click.echo("\nSkill Status:")
    click.echo("=" * 60)
    for name, skill in sorted(skills.items()):
        status = skill.get_status()
        click.echo(f"  {name:<25} {status}")
    click.echo()


@cli.command(name="info")
@click.argument('skill_name')
def info_command(skill_name: str):
    """
    Show detailed information about a skill.

    Displays the skill description, required MCPs, cleanup MCPs,
    and installation status.

    Examples:

      # Show info about fitness_modeling skill:
      skill info fitness_modeling
    """
    manager = SkillManager()
    skill = manager.get_skill(skill_name)

    if not skill:
        click.echo(f"Skill '{skill_name}' not found.", err=True)
        sys.exit(1)

    click.echo(f"\nDetails for Skill: {skill.name}")
    click.echo("=" * 60)
    click.echo(f"  Description: {skill.description}")
    click.echo(f"  File Path: {skill.file_path}")
    click.echo(f"  Status: {skill.get_status()}")
    click.echo(f"  Command Name: '{skill.command_name}'")

    required_mcps = skill.get_required_mcps()
    if required_mcps:
        # Check MCP availability
        available, missing = check_required_mcps(required_mcps)

        click.echo(f"\n  Required MCPs ({len(required_mcps)}):")
        for mcp in required_mcps:
            status = "✅" if mcp in available else "❌"
            click.echo(f"    {status} {mcp}")

        if missing:
            click.echo(f"\n  ⚠️  {len(missing)} MCP(s) not registered. Install with:")
            click.echo(f"      pskill install {skill_name}")
    click.echo()


@cli.command(name="install")
@click.argument('skill_name')
def install_command(skill_name: str):
    """
    Install a skill and its required MCP servers.

    Downloads and registers the skill with Claude Code, then installs
    all MCP servers required by the skill.

    Examples:

      # Install the fitness_modeling skill:
      skill install fitness_modeling
    """
    manager = SkillManager()
    success = manager.install_skill_and_mcps(skill_name)
    if not success:
        sys.exit(1)


@cli.command(name="uninstall")
@click.argument('skill_name')
def uninstall_command(skill_name: str):
    """
    Uninstall a skill and clean up its MCP servers.

    Removes the skill from Claude Code and optionally uninstalls
    associated MCP servers.

    Examples:

      # Uninstall the fitness_modeling skill:
      skill uninstall fitness_modeling
    """
    manager = SkillManager()
    success = manager.uninstall_skill_and_mcps(skill_name)
    if not success:
        sys.exit(1)


# =============================================================================
# Skill Creation Commands
# =============================================================================

@cli.group(name="create")
def create_group():
    """
    Create new skills interactively.

    Use these subcommands to create new workflow skills by recording
    steps as you test MCP tools.

    Workflow:
      1. pskill create init <skill_name>
      2. Test MCP tools interactively in Claude Code
      3. pskill create add-step <skill_name> (repeat for each step)
      4. pskill create generate <skill_name>
      5. pskill install <skill_name>
    """
    pass


@create_group.command(name="init")
@click.argument('skill_name')
@click.option('--description', '-d', default="", help='Skill description')
@click.option('--mcps', '-m', multiple=True, help='Required MCP servers (can be repeated)')
def create_init_command(skill_name: str, description: str, mcps: tuple):
    """
    Initialize a new skill with a steps file template.

    Creates a template steps file that you can edit to add steps,
    or use the add-step command interactively.

    Examples:

      # Initialize a new binder design skill:
      pskill create init binder_design -d "Design protein binders" -m bindcraft_mcp

      # Initialize with multiple MCPs:
      pskill create init my_skill -m mcp1 -m mcp2
    """
    creator = SkillCreator(skill_name)
    mcps_list = list(mcps) if mcps else None
    creator.init_skill(description=description, required_mcps=mcps_list)


@create_group.command(name="add-step")
@click.argument('skill_name')
@click.option('--title', '-t', default=None, help='Step title (interactive if not provided)')
@click.option('--prompt', '-p', default=None, help='Step prompt (interactive if not provided)')
def create_add_step_command(skill_name: str, title: str, prompt: str):
    """
    Add a step to the skill interactively or with options.

    Adds a new step to the skill's steps file. If title and prompt
    are not provided, enters interactive mode.

    Examples:

      # Add step interactively:
      pskill create add-step binder_design

      # Add step with options:
      pskill create add-step binder_design -t "Generate config" -p "Generate a BindCraft config..."
    """
    creator = SkillCreator(skill_name)
    if title and prompt:
        creator.add_step(title=title, prompt=prompt)
    else:
        interactive_add_step(creator)


@create_group.command(name="list-steps")
@click.argument('skill_name')
def create_list_steps_command(skill_name: str):
    """
    List all steps in the skill's steps file.

    Displays the steps that have been recorded for the skill.

    Examples:

      # List steps for binder_design:
      pskill create list-steps binder_design
    """
    creator = SkillCreator(skill_name)
    steps = creator.list_steps()
    if steps:
        click.echo(f"\nSteps in '{skill_name}':")
        click.echo("-" * 40)
        for step in steps:
            click.echo(f"  Step {step['number']}: {step['title']}")
        click.echo()
    else:
        click.echo("No steps found.")


@create_group.command(name="generate")
@click.argument('skill_name')
@click.option('--description', '-d', default=None, help='Override description')
@click.option('--mcps', '-m', multiple=True, help='Override required MCPs')
def create_generate_command(skill_name: str, description: str, mcps: tuple):
    """
    Generate the skill file from the steps file.

    Transforms the steps file into a full skill markdown file and
    updates the configs.yaml to register the skill.

    Examples:

      # Generate skill from steps:
      pskill create generate binder_design

      # Generate with overrides:
      pskill create generate binder_design -d "New description" -m mcp1 -m mcp2
    """
    creator = SkillCreator(skill_name)
    mcps_list = list(mcps) if mcps else None
    creator.generate_skill(description=description, required_mcps=mcps_list)


@create_group.command(name="from-steps")
@click.argument('steps_file', type=click.Path(exists=True))
@click.option('--description', '-d', default=None, help='Override description')
@click.option('--mcps', '-m', multiple=True, help='Override required MCPs')
def create_from_steps_command(steps_file: str, description: str, mcps: tuple):
    """
    Generate a skill from an existing steps file.

    Useful when you've manually edited a steps file or have one
    from a previous session.

    Examples:

      # Generate from existing steps file:
      pskill create from-steps workflow-skills/my_steps.md

      # With overrides:
      pskill create from-steps my_steps.md -d "Description" -m mcp1
    """
    steps_path = Path(steps_file)
    creator = SkillCreator.from_steps_file(steps_path)
    if creator:
        mcps_list = list(mcps) if mcps else None
        creator.generate_skill(description=description, required_mcps=mcps_list)
    else:
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
