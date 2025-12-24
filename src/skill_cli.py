#!/usr/bin/env python3
"""
ProteinMCP Skill CLI - Skill Management Command Line Interface

Provides unified access to skill management functionality through subcommands:
- skill avail: Show all available skills to install
- skill status: Show installed status of skills
- skill info: Show detailed information about a skill
- skill install: Install a skill and its required MCPs
- skill execute: Guide through skill execution
- skill uninstall: Uninstall a skill and cleanup MCPs
"""

import sys
import textwrap

import click

from .skill.skill_manager import SkillManager


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="skill")
@click.pass_context
def cli(ctx):
    """
    ProteinMCP Skill Manager - Workflow Skills for Claude Code

    A toolkit for installing and managing workflow skills that combine
    multiple MCP servers into cohesive protein engineering workflows.
    """
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
    click.echo("Finding available skills in 'workflow-skills/'...")
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
        click.echo(f"\n  Required MCPs ({len(required_mcps)}):")
        for mcp in required_mcps:
            click.echo(f"    - {mcp}")

    cleanup_mcps = skill.get_cleanup_mcps()
    if cleanup_mcps:
        click.echo(f"\n  Cleanup MCPs ({len(cleanup_mcps)}):")
        for mcp in cleanup_mcps:
            click.echo(f"    - {mcp}")
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


@cli.command(name="execute")
@click.argument('skill_name')
def execute_command(skill_name: str):
    """
    Guide through the execution of an installed skill.

    Displays step-by-step prompts that you can copy and paste
    into your conversation with the assistant.

    Examples:

      # Execute the fitness_modeling skill:
      skill execute fitness_modeling
    """
    manager = SkillManager()
    skill = manager.get_skill(skill_name)

    if not skill:
        click.echo(f"Skill '{skill_name}' not found.", err=True)
        sys.exit(1)

    click.echo(f"\nExecuting Skill: {skill.name}")
    click.echo("=" * 70)
    click.echo("This will guide you through the steps defined in the skill file.")
    click.echo("Copy and paste the prompts into your conversation with the assistant.")
    click.echo("=" * 70)

    steps = skill.get_execution_steps()
    if not steps:
        click.echo("\nNo executable steps (prompts) found in this skill.")
        return

    for i, step in enumerate(steps, 1):
        click.echo(f"\n--- Step {i}: {step['title']} ---")
        click.echo("\nPrompt to copy:")
        prompt_block = textwrap.indent(step['prompt'], "    ")
        click.echo(prompt_block)

        if i < len(steps):
            click.prompt("\nPress Enter to continue to the next step", default="", show_default=False)


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


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
