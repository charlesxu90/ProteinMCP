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

import json
from pathlib import Path
from typing import Optional, List
import click
from loguru import logger

from .mcp_creator import MCPCreator
from .mcp_manager import MCPManager
from .mcp import MCP, make_relative_path
from .status_cache import get_cache
from ..utils import run_claude_with_streaming


# ============================================================================
# Helper Functions
# ============================================================================

def extract_setup_commands_with_claude(mcp_dir: Path, prompts_dir: Path) -> List[str]:
    """
    Extract setup commands from README.md using Claude Code CLI.

    Args:
        mcp_dir: Path to the MCP directory containing README.md
        prompts_dir: Path to the prompts directory

    Returns:
        List of setup commands suitable for mcps.yaml
    """
    # Read and prepare prompt
    prompt_file = prompts_dir / "extract_setup_commands_prompt.md"
    if not prompt_file.exists():
        logger.warning(f"  ⚠️ Prompt file not found: {prompt_file}")
        return get_default_setup_commands(mcp_dir)

    with open(prompt_file, 'r') as f:
        prompt_content = f.read()

    # Ensure reports directory exists
    reports_dir = mcp_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    output_file = mcp_dir / "claude_outputs" / "setup_commands_output.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info("📝 Extracting setup commands from README using Claude...")

    # Run Claude to extract setup commands
    success = run_claude_with_streaming(prompt_content, output_file, mcp_dir, api_key=None)

    if not success:
        logger.warning("  ⚠️ Claude extraction failed, using default setup commands")
        return get_default_setup_commands(mcp_dir)

    # Read the extracted commands from the JSON file Claude created
    setup_commands_file = reports_dir / "setup_commands.json"
    if setup_commands_file.exists():
        try:
            with open(setup_commands_file, 'r') as f:
                data = json.load(f)
                commands = data.get('setup_commands', [])
                if commands:
                    logger.info(f"  ✅ Extracted {len(commands)} setup commands from README")
                    return commands
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"  ⚠️ Failed to parse setup_commands.json: {e}")

    # Fall back to defaults
    logger.warning("  ⚠️ No setup commands extracted, using defaults")
    return get_default_setup_commands(mcp_dir)


def get_default_setup_commands(mcp_dir: Path) -> List[str]:
    """
    Generate default setup commands when Claude extraction fails.

    Args:
        mcp_dir: Path to the MCP directory

    Returns:
        List of default setup commands
    """
    setup_commands = []

    # Standard environment creation command with mamba > conda > venv fallback
    env_create_cmd = (
        '(command -v mamba >/dev/null 2>&1 && mamba env create -p ./env python=3.10 -y) || '
        '(command -v conda >/dev/null 2>&1 && conda env create -p ./env python=3.10 -y) || '
        '(echo "Warning: Neither mamba nor conda found, creating venv instead" && '
        'python3 -m venv ./env)'
    )
    setup_commands.append(env_create_cmd)

    # Add requirements installation if requirements.txt exists
    requirements_path = mcp_dir / "requirements.txt"
    if requirements_path.exists():
        setup_commands.append('./env/bin/pip install -r requirements.txt')

    # Always ensure fastmcp is installed
    setup_commands.append('./env/bin/pip install --ignore-installed fastmcp')

    return setup_commands


def register_created_mcp(mcp_info: dict, github_url: str = "", local_repo_path: str = "") -> bool:
    """
    Register a newly created MCP to the mcps.yaml registry and update status cache.

    Args:
        mcp_info: Dictionary from MCPCreator.get_created_mcp_info()
        github_url: Original GitHub URL (if provided)
        local_repo_path: Original local repo path (if provided)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract info from mcp_info
        mcp_name = mcp_info.get('name', '')
        mcp_dir = mcp_info.get('mcp_dir', '')
        server_file = mcp_info.get('server_file')
        source_url = mcp_info.get('source_url', github_url or local_repo_path)

        if not mcp_name or not mcp_dir:
            logger.error("❌ Missing MCP name or directory in mcp_info")
            return False

        # Determine the MCP name with _mcp suffix if not present
        if not mcp_name.endswith('_mcp'):
            registry_name = f"{mcp_name}_mcp"
        else:
            registry_name = mcp_name

        # Determine description from README if available
        readme_path = Path(mcp_dir) / "README.md"
        description = f"MCP created from {source_url}"
        if readme_path.exists():
            try:
                content = readme_path.read_text()
                lines = content.split("\n")
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("```"):
                        continue
                    # Take first meaningful line as description
                    if len(line) > 10:
                        description = line[:100] + "..." if len(line) > 100 else line
                        break
            except Exception:
                pass

        # Determine server args (relative path to server file)
        server_args = []
        if server_file:
            server_path = Path(server_file)
            mcp_path = Path(mcp_dir)
            try:
                relative_server = server_path.relative_to(mcp_path)
                server_args = [str(relative_server)]
            except ValueError:
                server_args = [server_file]

        # Extract setup commands from README using Claude
        script_dir = Path(__file__).parent
        prompts_dir = script_dir / "prompts"
        mcp_path = Path(mcp_dir)

        logger.info("📋 Extracting setup commands from README...")
        setup_commands = extract_setup_commands_with_claude(mcp_path, prompts_dir)

        # Create MCP object
        mcp = MCP(
            name=registry_name,
            url=github_url if github_url else "",
            description=description,
            source="Tool",  # Mark as Tool source since it's locally created
            runtime="python",
            server_command="python",
            server_args=server_args,
            path=mcp_dir,
            setup_commands=setup_commands,
            env_vars={},
            dependencies=[]
        )

        # Add to mcps.yaml registry
        manager = MCPManager()
        mcps = manager.load_installed_mcps(force_reload=True)
        mcps[registry_name] = mcp
        manager.save_installed_mcps(mcps)
        logger.info(f"✅ Added '{registry_name}' to mcps.yaml registry")

        # Update status cache
        cache = get_cache()
        cache.set_status(f"{registry_name}:claude", "both")  # Assuming it was registered during step 7
        logger.info(f"✅ Updated status cache for '{registry_name}'")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to register MCP: {e}")
        return False


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

        # After successful creation, register the MCP to mcps.yaml and update status
        logger.info("\n" + "="*50)
        logger.info("📝 Registering MCP to ProteinMCP registry...")
        logger.info("="*50 + "\n")

        mcp_info = creator.get_created_mcp_info()
        local_path_str = str(local_repo_path) if local_repo_path else ""

        if register_created_mcp(mcp_info, github_url=github_url, local_repo_path=local_path_str):
            # Compute registry name for display
            mcp_name = mcp_info.get('name', '')
            registry_name = mcp_name if mcp_name.endswith('_mcp') else f"{mcp_name}_mcp"

            logger.info("\n🎉 MCP successfully created and registered!")
            logger.info(f"   View with: pmcp status")
            logger.info(f"   Info with: pmcp info {registry_name}")
            logger.info(f"   Install with: pmcp install {registry_name}")
        else:
            logger.warning("\n⚠️  MCP created but failed to register to mcps.yaml")
            logger.warning("   You can manually add it using: pmcp install <mcp_name>")

    except Exception:
        raise Exception("MCP Creation Pipeline failed")