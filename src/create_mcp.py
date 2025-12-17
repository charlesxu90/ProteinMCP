#!/usr/bin/env python3
"""
MCP Creation Pipeline

This script creates an MCP (Model Context Protocol) server from a GitHub/local repository with tutorials.

Steps:
1. Setup project environment and prepare working directories
2. Clone GitHub repository
3. Setup conda environment & scan common use cases
4. Execute the common use cases in repository (bugfix if needed)
5. Write script for functions to execute common use cases (test and bugfix if needed)
6. Extract MCP tools from use case scripts and wrap in MCP server (test and bugfix if needed)
7. Test Claude and Gemini integration (bugfix if needed)
8. Create comprehensive README documentation
"""

from pathlib import Path
from typing import Optional
import click
from loguru import logger

from .mcp_creator import MCPCreator


# ============================================================================
# Helper Function
# ============================================================================


# ============================================================================
# CLI Command
# ============================================================================

def create_mcp(github_url: str, local_repo_path: Optional[Path], mcp_dir: Path, 
               use_case_filter: str, api_key: str, rerun_from_step: int = 0):
    """
    Create an MCP (Model Context Protocol) server from a GitHub repository or local code.
    
    This pipeline will:
    1. Setup project environment and prepare working directories
    2. Clone GitHub repository
    3. Setup conda environment & scan common use cases
    4. Execute the common use cases in repository (bugfix if needed)
    5. Write script for functions to execute common use cases (test and bugfix if needed)
    6. Extract MCP tools from use case scripts and wrap in MCP server (test and bugfix if needed)
    7. Test Claude and Gemini integration (bugfix if needed)
    8. Create comprehensive README documentation
    
    Examples:\n
        # From GitHub repository:\n
        python create_mcp.py --github-url https://github.com/user/repo --mcp-dir /path/to/my-mcp
        \n
        # From local repository:\n
        python create_mcp.py --local-repo-path /path/to/local/repo --mcp-dir /path/to/my-mcp
        \n
        # Force rerun from step 3:\n
        python create_mcp.py --local-repo-path /path/to/repo --mcp-dir /path/to/mcp --rerun-from-step 3
    """
    # Validate that either github_url or local_repo_path is provided
    if not github_url and not local_repo_path:
        logger.error("❌ Error: Either --github-url or --local-repo-path must be provided")
        return
    
    if github_url and local_repo_path:
        logger.warning("⚠️  Warning: Both --github-url and --local-repo-path provided. Using --local-repo-path")
    
    # Get script directory (directory containing this file)
    script_dir = Path(__file__).parent
    
    # Prompts are always in ./prompts/ subdirectory
    prompts_dir = script_dir / "prompts"
    
    # Validate prompts directory exists
    if not prompts_dir.exists():
        logger.error(f"❌ Error: Prompts directory not found: {prompts_dir}")
        logger.error(f"   Please ensure prompts are in: {prompts_dir}")
        return
    
    # Convert to absolute path
    mcp_dir = mcp_dir.resolve()
    
    # Display configuration
    logger.info("🚀 Starting MCP Creation Pipeline\n")
    if local_repo_path:
        logger.info(f"📦 Repository: {local_repo_path} (local)")
    else:
        logger.info(f"📦 Repository: {github_url} (GitHub)")
    logger.info(f"📁 MCP Directory: {mcp_dir}")
    logger.info(f"🔍 Use Case Filter: {use_case_filter or 'None'}")
    logger.info(f"🤖 Using: Claude Code CLI (logged-in account)")
    logger.info(f"📂 Prompts Directory: {prompts_dir}")
    if rerun_from_step > 0:
        logger.info(f"🔄 Rerun From Step: {rerun_from_step}")
    logger.info("\n" + "-"*50 + "\n")
    
    # Create and run MCP Creator
    creator = MCPCreator(
        mcp_dir=mcp_dir,
        script_dir=script_dir,
        prompts_dir=prompts_dir,
        github_url=github_url,
        local_repo_path=str(local_repo_path) if local_repo_path else "",
        use_case_filter=use_case_filter,
        api_key=api_key,
        rerun_from_step=rerun_from_step
    )
    
    try:
        creator.run_all()
    except Exception:
        raise Exception("MCP Creation Pipeline failed")


@click.command()
@click.option('--github-url', default='', help='GitHub repository URL to clone (e.g., https://github.com/user/repo)')
@click.option('--local-repo-path', default=None, type=click.Path(exists=True, path_type=Path),
              help='Path to local repository (alternative to --github-url)')
@click.option('--mcp-dir', required=True, type=click.Path(path_type=Path), 
              help='MCP project directory to create (e.g., /path/to/my-mcp-project)')
@click.option('--use-case-filter', default='', help='Optional filter for use cases (e.g., "prediction", "analysis")')
@click.option('--rerun-from-step', default=0, type=click.IntRange(0, 8),
              help='Force rerun from this step number (1-8). Clears markers for this step and all subsequent steps.')
def cli(github_url: str, local_repo_path: Optional[Path], mcp_dir: Path, 
        use_case_filter: str, rerun_from_step: int):
    create_mcp(
        github_url=github_url,
        local_repo_path=local_repo_path,
        mcp_dir=mcp_dir,
        use_case_filter=use_case_filter,
        api_key="",  # Not needed - uses Claude Code CLI with logged-in account
        rerun_from_step=rerun_from_step
    )


if __name__ == '__main__':
    cli()
