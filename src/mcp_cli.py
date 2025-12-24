#!/usr/bin/env python3
"""
ProteinMCP CLI - Main Command Line Interface

Provides unified access to ProteinMCP functionality through subcommands:
- pmcp create: Create new MCP servers from repositories
- pmcp avail: Show all available MCP servers to install
- pmcp status: Show downloaded and installed MCP servers
- pmcp install: Install MCP servers
- pmcp uninstall: Uninstall MCP servers
"""

import sys
import click
from pathlib import Path
from typing import Optional

# Import functions from existing modules
from .mcp.create_mcp import create_mcp
from .mcp.install_mcp import show_available_mcps, show_status, install_mcp_cmd, uninstall_mcp_cmd, search_mcps, show_info

# Logo for ProteinMCP
LOGO = """\033[31m
  ____            _       _       __  __  ____ ____
 |  _ \\ _ __ ___ | |_ ___(_)_ __ |  \\/  |/ ___| _  \\
 | |_) | '__/ _ \\| __/ _ \\ | '_ \\| |\\/| | |   | |_) |
 |  __/| | | (_) | ||  __/ | | | | |  | | |___|  __/
 |_|   |_|  \\___/ \\__\\___|_|_| |_|_|  |_|\\____|_|
\033[0m"""


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="proteinmcp")
@click.pass_context
def cli(ctx):
    """
    ProteinMCP - Protein Engineering Model Context Protocol Package

    A comprehensive toolkit for creating, installing, and managing MCP servers
    for protein engineering, analysis, and prediction.
    """
    # Display logo whenever proteinmcp is called
    click.echo(LOGO)

    # Show help when no command is given
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command(name="create")
@click.option('--github-url', default='', help='GitHub repository URL to clone')
@click.option('--local-repo-path', default=None, type=click.Path(exists=True, path_type=Path),
              help='Path to local repository (alternative to --github-url)')
@click.option('--mcp-dir', required=True, type=click.Path(path_type=Path),
              help='MCP project directory to create')
@click.option('--use-case-filter', default='', help='Optional filter for use cases')
@click.option('--rerun-from-step', default=0, type=click.IntRange(0, 8),
              help='Force rerun from this step number (1-8)')
def create_command(github_url: str, local_repo_path: Optional[Path], mcp_dir: Path,
                   use_case_filter: str, rerun_from_step: int):
    """
    Create an MCP server from a GitHub repository or local code.

    This pipeline will analyze the repository, extract common use cases,
    and generate an MCP server with appropriate tools and documentation.

    Examples:

      # From GitHub repository:
      pmcp create --github-url https://github.com/user/repo --mcp-dir /path/to/my-mcp

      # From local repository:
      pmcp create --local-repo-path /path/to/local/repo --mcp-dir /path/to/my-mcp

      # Force rerun from step 3:
      pmcp create --local-repo-path /path/to/repo --mcp-dir /path/to/mcp --rerun-from-step 3
    """
    create_mcp(
        github_url=github_url,
        local_repo_path=local_repo_path,
        mcp_dir=mcp_dir,
        use_case_filter=use_case_filter,
        api_key="",  # Uses Claude Code CLI with logged-in account
        rerun_from_step=rerun_from_step
    )


@cli.command(name="avail")
@click.option('--local', is_flag=True, help='Show local MCPs only')
@click.option('--public', is_flag=True, help='Show public MCPs only')
def avail_command(local: bool, public: bool):
    """
    Show all available MCP servers that can be installed.

    By default, shows both local MCPs (developed in MCP directory) and
    public MCPs (from public registry). Use --local or --public to filter.

    Examples:

      # Show all available MCPs:
      pmcp avail

      # Show only local MCPs:
      pmcp avail --local

      # Show only public MCPs:
      pmcp avail --public
    """
    show_available_mcps(local_only=local, public_only=public)


@cli.command(name="status")
@click.option('--refresh', is_flag=True, help='Refresh status cache (slower but accurate)')
def status_command(refresh: bool):
    """
    Show status of downloaded and installed MCPs.

    Displays which MCPs are currently downloaded to your system and
    which ones are registered with Claude Code CLI. Use --refresh to
    update the status cache.

    Examples:

      # Show current MCP status:
      pmcp status

      # Refresh cache and show status:
      pmcp status --refresh
    """
    show_status(refresh_cache=refresh)


@cli.command(name="install")
@click.argument('mcp_name')
@click.option('--cli', type=click.Choice(['claude', 'gemini']), default='claude',
              help='CLI tool to register with (default: claude)')
@click.option('--no-register', is_flag=True,
              help='Install only, do not register with CLI')
def install_command(mcp_name: str, cli: str, no_register: bool):
    """
    Install an MCP server and optionally register it with a CLI.

    By default, installs the MCP and registers it with Claude Code.
    Use --no-register to skip CLI registration.

    Examples:

      # Install and register with Claude Code:
      pmcp install proteinmpnn

      # Install and register with Gemini CLI:
      pmcp install pdb --cli gemini

      # Install only, don't register:
      pmcp install arxiv --no-register
    """
    success = install_mcp_cmd(mcp_name, cli=cli, no_register=no_register)
    if not success:
        sys.exit(1)


@cli.command(name="uninstall")
@click.argument('mcp_name')
@click.option('--cli', type=click.Choice(['claude', 'gemini']), default='claude',
              help='CLI tool to unregister from (default: claude)')
@click.option('--remove-files', is_flag=True,
              help='Also remove installation files')
def uninstall_command(mcp_name: str, cli: str, remove_files: bool):
    """
    Uninstall an MCP server from CLI and optionally remove files.

    By default, only unregisters the MCP from the CLI. Use --remove-files
    to also delete the installation files.

    Examples:

      # Unregister from CLI only:
      pmcp uninstall arxiv

      # Unregister and delete files:
      pmcp uninstall arxiv --remove-files

      # Unregister from Gemini CLI:
      pmcp uninstall pdb --cli gemini
    """
    success = uninstall_mcp_cmd(mcp_name, cli=cli, remove_files=remove_files)
    if not success:
        sys.exit(1)


@cli.command(name="search")
@click.argument('query')
def search_command(query: str):
    """
    Search for MCP servers by name or description.

    Examples:

      # Search for blast-related MCPs:
      pmcp search blast

      # Search for prediction tools:
      pmcp search prediction
    """
    search_mcps(query)


@cli.command(name="info")
@click.argument('mcp_name')
def info_command(mcp_name: str):
    """
    Show detailed information about an MCP server.

    Examples:

      # Show info about UniProt MCP:
      pmcp info uniprot

      # Show info about ProteinMPNN MCP:
      pmcp info proteinmpnn
    """
    show_info(mcp_name)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
