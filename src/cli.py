#!/usr/bin/env python3
"""
ProteinMCP CLI - Main Command Line Interface

Provides unified access to ProteinMCP functionality through subcommands:
- proteinmcp create: Create new MCP servers from repositories
- proteinmcp install: Install MCP servers
- proteinmcp list: List available MCP servers
- proteinmcp uninstall: Uninstall MCP servers
"""

import sys
import click
from pathlib import Path
from typing import Optional

# Import functions from existing modules
from .create_mcp import create_mcp
from .install_mcp import list_mcps, install_mcp_cmd, uninstall_mcp_cmd, search_mcps, show_info


@click.group()
@click.version_option(version="0.1.0", prog_name="proteinmcp")
def cli():
    """
    ProteinMCP - Protein Engineering Model Context Protocol Package

    A comprehensive toolkit for creating, installing, and managing MCP servers
    for protein engineering, analysis, and prediction.
    """
    pass


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
      proteinmcp create --github-url https://github.com/user/repo --mcp-dir /path/to/my-mcp

      # From local repository:
      proteinmcp create --local-repo-path /path/to/local/repo --mcp-dir /path/to/my-mcp

      # Force rerun from step 3:
      proteinmcp create --local-repo-path /path/to/repo --mcp-dir /path/to/mcp --rerun-from-step 3
    """
    create_mcp(
        github_url=github_url,
        local_repo_path=local_repo_path,
        mcp_dir=mcp_dir,
        use_case_filter=use_case_filter,
        api_key="",  # Uses Claude Code CLI with logged-in account
        rerun_from_step=rerun_from_step
    )


@cli.command(name="list")
@click.option('--local', is_flag=True, help='Show local MCPs only')
@click.option('--public', is_flag=True, help='Show public MCPs only')
@click.option('--refresh', is_flag=True, help='Refresh status cache (slower but accurate)')
def list_command(local: bool, public: bool, refresh: bool):
    """
    List available MCP servers.

    By default, shows both local and public MCPs. Use --local or --public
    to filter results. Use --refresh to update the status cache.

    Examples:

      # List all MCPs:
      proteinmcp list

      # List only local MCPs:
      proteinmcp list --local

      # List only public MCPs:
      proteinmcp list --public

      # Refresh cache and list:
      proteinmcp list --refresh
    """
    list_mcps(local_only=local, public_only=public, refresh_cache=refresh)


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
      proteinmcp install proteinmpnn

      # Install and register with Gemini CLI:
      proteinmcp install pdb --cli gemini

      # Install only, don't register:
      proteinmcp install arxiv --no-register
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
      proteinmcp uninstall arxiv

      # Unregister and delete files:
      proteinmcp uninstall arxiv --remove-files

      # Unregister from Gemini CLI:
      proteinmcp uninstall pdb --cli gemini
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
      proteinmcp search blast

      # Search for prediction tools:
      proteinmcp search prediction
    """
    search_mcps(query)


@cli.command(name="info")
@click.argument('mcp_name')
def info_command(mcp_name: str):
    """
    Show detailed information about an MCP server.

    Examples:

      # Show info about UniProt MCP:
      proteinmcp info uniprot

      # Show info about ProteinMPNN MCP:
      proteinmcp info proteinmpnn
    """
    show_info(mcp_name)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
