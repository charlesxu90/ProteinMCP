#!/usr/bin/env python3
"""
MCP Creation Pipeline

This script creates an MCP (Model Context Protocol) server from a GitHub repository with tutorials.

Steps:
1. Setup project environment
2. Clone GitHub repository
3. Prepare working directories
4. Add context7 MCP server (optional)
5. Core Pipeline Steps:
   - Setup Python environment & scan tutorials
   - Execute tutorial notebooks
   - Extract tools from tutorials
   - Wrap tools in MCP server
6. Launch MCP server
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional
import json
import click
from loguru import logger

from utils import (
    log_progress,
    check_marker,
    create_marker,
    run_command,
    run_claude_with_streaming
)


# ============================================================================
# MCP Creator Class
# ============================================================================

class MCPCreator:
    """
    MCP (Model Context Protocol) Creator
    
    Creates an MCP server from a GitHub repository with tutorials.
    Manages the entire pipeline from cloning to deployment.
    """
    
    def __init__(self, mcp_dir: Path, script_dir: Path, 
                 prompts_dir: Path, github_url: str = "", local_repo_path: str = "",
                 tutorial_filter: str = "", api_key: str = "",
                 skip_context7: bool = False):
        """
        Initialize MCP Creator
        
        Args:
            mcp_dir: Target directory for MCP project
            script_dir: Directory containing this script
            prompts_dir: Directory containing prompt templates
            github_url: GitHub repository URL to clone (optional if local_repo_path provided)
            local_repo_path: Path to local repository (alternative to github_url)
            tutorial_filter: Optional filter for tutorials
            api_key: API key for notebook execution
            skip_context7: Whether to skip context7 MCP installation
        """
        self.mcp_dir = mcp_dir.resolve()
        self.github_url = github_url
        self.local_repo_path = Path(local_repo_path) if local_repo_path else None
        self.script_dir = script_dir
        self.prompts_dir = prompts_dir
        self.tutorial_filter = tutorial_filter
        self.api_key = api_key
        self.skip_context7 = skip_context7
        
        # Validate that either github_url or local_repo_path is provided
        if not github_url and not local_repo_path:
            raise ValueError("Either github_url or local_repo_path must be provided")
        
        # Extract repo name from URL or local path
        if local_repo_path:
            self.repo_name = Path(local_repo_path).name
        else:
            self.repo_name = Path(github_url.rstrip('.git')).name
        
        # Track step execution status
        self.step_status = {}
        
    def _get_marker(self, step: str) -> Path:
        """Get marker file path for a step"""
        return self.mcp_dir / ".pipeline" / f"{step}_done"
    
    def step1_setup_project(self) -> Path:
        """Setup project environment and directory structure"""
        pipeline_dir = self.mcp_dir / ".pipeline"
        marker = self._get_marker("01_setup")
        
        if check_marker(marker):
            log_progress(1, "Setup project environment", "skip")
            self.step_status['setup'] = 'skipped'
            return self.mcp_dir
        
        log_progress(1, "Setup project environment", "start")
        
        # Create project directory
        self.mcp_dir.mkdir(parents=True, exist_ok=True)
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy configs/templates if they exist and not already present
        for folder_name_item in ['claude', 'templates', 'tools']:
            src = self.script_dir / 'configs' / folder_name_item
            dst = self.mcp_dir / folder_name_item if folder_name_item != 'claude' else self.mcp_dir / f'.{folder_name_item}'
            
            if not dst.exists() and src.exists():
                shutil.copytree(src, dst)
                logger.info(f"  Copied {folder_name_item}")
            else:
                logger.info(f"  {folder_name_item} already exists or source missing")
        
        create_marker(marker)
        log_progress(1, "Setup project environment", "complete")
        self.step_status['setup'] = 'executed'
        
        return self.mcp_dir

    def step2_clone_repo(self) -> str:
        """Clone the GitHub repository or use local repository"""
        repo_dir = self.mcp_dir / "repo" / self.repo_name
        marker = self._get_marker("02_clone")
        
        if check_marker(marker):
            log_progress(2, "Setup repository", "skip")
            self.step_status['clone'] = 'skipped'
            return self.repo_name
        
        # Create repo directory
        (self.mcp_dir / "repo").mkdir(parents=True, exist_ok=True)
        
        # Use local repository if provided
        if self.local_repo_path:
            log_progress(2, "Setup repository (local)", "start")
            
            if repo_dir.exists():
                logger.info(f"  Repository already exists: {repo_dir}")
            else:
                # Verify local path exists
                if not self.local_repo_path.exists():
                    raise FileNotFoundError(f"Local repository not found: {self.local_repo_path}")
                
                # Copy or symlink local repository
                logger.info(f"  Copying local repository from {self.local_repo_path}...")
                shutil.copytree(self.local_repo_path, repo_dir, symlinks=True)
                logger.info("  Local repository copied successfully")
            
            create_marker(marker)
            log_progress(2, "Setup repository (local)", "complete")
            self.step_status['clone'] = 'executed'
            return self.repo_name
        
        # Clone from GitHub
        log_progress(2, "Clone GitHub repository", "start")
        
        # Skip if already cloned
        if repo_dir.exists():
            logger.info(f"  Repository already exists: {repo_dir}")
        else:
            # Try different cloning strategies
            try:
                # Try with submodules first
                logger.info(f"  Cloning {self.github_url} with submodules...")
                run_command(["git", "clone", "--recurse-submodules", self.github_url, str(repo_dir)])
                logger.info("  Cloned with submodules")
            except:
                try:
                    # Try shallow clone
                    logger.info("  Trying shallow clone...")
                    run_command(["git", "clone", "--depth=1", self.github_url, str(repo_dir)])
                    logger.info("  Shallow clone successful")
                except:
                    # Try plain clone
                    logger.info("  Trying plain clone...")
                    run_command(["git", "clone", self.github_url, str(repo_dir)])
                    logger.info("  Plain clone successful")
        
        create_marker(marker)
        log_progress(2, "Clone GitHub repository", "complete")
        self.step_status['clone'] = 'executed'
        
        return self.repo_name

    def step3_prepare_folders(self):
        """Create necessary folder structure for the pipeline"""
        marker = self._get_marker("03_folders")
        
        if check_marker(marker):
            log_progress(3, "Prepare working directories", "skip")
            self.step_status['folders'] = 'skipped'
            return
        
        log_progress(3, "Prepare working directories", "start")
        
        # Create all required directories
        folders = [
            "reports",
            "src/tools",
            "tests/code",
            "tests/data",
            "notebooks",
            "tests/results",
            "tests/logs",
            "tests/summary",
            "tmp/inputs",
            "tmp/outputs",
            "claude_outputs"
        ]
        
        for folder in folders:
            folder_path = self.mcp_dir / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"  Created: {folder}")
        
        create_marker(marker)
        log_progress(3, "Prepare working directories", "complete")
        self.step_status['folders'] = 'executed'

    def _is_context7_installed(self) -> bool:
        """Check if context7 MCP is already installed"""
        try:
            result = subprocess.run(
                ["claude", "mcp", "list"],
                capture_output=True,
                text=True,
                check=False
            )
            return "context7" in result.stdout.lower()
        except Exception:
            return False

    def step4_add_context7_mcp(self):
        """Add context7 MCP server (optional)"""
        if self.skip_context7:
            logger.info("  ⏭️ Skipping context7 MCP (--skip-context7 flag set)")
            self.step_status['context7'] = 'skipped'
            return
        
        # Check if already installed globally
        if self._is_context7_installed():
            logger.info("  ✅ context7 MCP already installed globally")
            self.step_status['context7'] = 'skipped'
            return
        
        marker = self._get_marker("04_context7")
        
        if check_marker(marker):
            log_progress(4, "Add context MCP server", "skip")
            self.step_status['context7'] = 'skipped'
            return
        
        log_progress(4, "Add context MCP server", "start")
        
        try:
            # Try to add context7 MCP
            run_command(["claude", "mcp", "add", "context7", "--", "npx", "-y", "@upstash/context7-mcp@latest"])
            logger.info("  context7 MCP added successfully")
            create_marker(marker)
            log_progress(4, "Add context MCP server", "complete")
            self.step_status['context7'] = 'executed'
        except Exception as e:
            logger.info(f"  ⚠️ Warning: Failed to add context7 MCP - {e}", err=True)
            logger.info("  Continuing without context7...")
            # Don't create marker on failure
            self.step_status['context7'] = 'failed'

    def step5_1_setup_env(self):
        """Step 5.1: Setup Python environment & scan tutorials"""
        marker = self._get_marker("05_step1")
        output_file = self.mcp_dir / "claude_outputs" / "step1_output.json"
        
        if check_marker(marker):
            log_progress(5, "Setup Python environment & scan tutorials", "skip")
            self.step_status['step1'] = 'skipped'
            return
        
        log_progress(5, "Setup Python environment & scan tutorials", "start")
        
        # Read and prepare prompt
        prompt_file = self.prompts_dir / "step1_prompt.md"
        if not prompt_file.exists():
            logger.info(f"  ⚠️ Prompt file not found: {prompt_file}", err=True)
            logger.info("  You'll need to run this step manually or ensure prompts/ directory exists", err=True)
            return
        
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
        
        # Replace placeholders
        prompt_content = prompt_content.replace('${github_repo_name}', self.repo_name)
        prompt_content = prompt_content.replace('${tutorial_filter}', self.tutorial_filter or '')
        
        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir):
            create_marker(marker)
            log_progress(5, "Setup Python environment & scan tutorials", "complete")
            self.step_status['step1'] = 'executed'
        else:
            self.step_status['step1'] = 'failed'

    def step5_2_execute_tutorials(self):
        """Step 5.2: Execute tutorial notebooks"""
        marker = self._get_marker("05_step2")
        output_file = self.mcp_dir / "claude_outputs" / "step2_output.json"
        
        if check_marker(marker):
            log_progress(6, "Execute tutorial notebooks", "skip")
            self.step_status['step2'] = 'skipped'
            return
        
        log_progress(6, "Execute tutorial notebooks", "start")
        
        # Read and prepare prompt
        prompt_file = self.prompts_dir / "step2_prompt.md"
        if not prompt_file.exists():
            logger.info(f"  ⚠️ Prompt file not found: {prompt_file}", err=True)
            logger.info("  You'll need to run this step manually or ensure prompts/ directory exists", err=True)
            return
        
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
        
        # Replace placeholders
        prompt_content = prompt_content.replace('${api_key}', self.api_key or '')
        
        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir):
            create_marker(marker)
            log_progress(6, "Execute tutorial notebooks", "complete")
            self.step_status['step2'] = 'executed'
        else:
            self.step_status['step2'] = 'failed'

    def step5_3_extract_tools(self):
        """Step 5.3: Extract tools from tutorials"""
        marker = self._get_marker("05_step3")
        output_file = self.mcp_dir / "claude_outputs" / "step3_output.json"
        
        if check_marker(marker):
            log_progress(7, "Extract tools from tutorials", "skip")
            self.step_status['step3'] = 'skipped'
            return
        
        log_progress(7, "Extract tools from tutorials", "start")
        
        # Read and prepare prompt
        prompt_file = self.prompts_dir / "step3_prompt.md"
        if not prompt_file.exists():
            logger.info(f"  ⚠️ Prompt file not found: {prompt_file}", err=True)
            logger.info("  You'll need to run this step manually or ensure prompts/ directory exists", err=True)
            return
        
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
        
        # Replace placeholders
        prompt_content = prompt_content.replace('${api_key}', self.api_key or '')
        
        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir):
            create_marker(marker)
            log_progress(7, "Extract tools from tutorials", "complete")
            self.step_status['step3'] = 'executed'
        else:
            self.step_status['step3'] = 'failed'

    def step5_4_wrap_mcp(self):
        """Step 5.4: Wrap tools in MCP server"""
        marker = self._get_marker("05_step4")
        output_file = self.mcp_dir / "claude_outputs" / "step4_output.json"
        
        if check_marker(marker):
            log_progress(8, "Wrap tools in MCP server", "skip")
            self.step_status['step4'] = 'skipped'
            return
        
        log_progress(8, "Wrap tools in MCP server", "start")
        
        # Read prompt (no variable substitution needed for step 4)
        prompt_file = self.prompts_dir / "step4_prompt.md"
        if not prompt_file.exists():
            logger.info(f"  ⚠️ Prompt file not found: {prompt_file}", err=True)
            logger.info("  You'll need to run this step manually or ensure prompts/ directory exists", err=True)
            return
        
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
        
        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir):
            create_marker(marker)
            log_progress(8, "Wrap tools in MCP server", "complete")
            self.step_status['step4'] = 'executed'
        else:
            self.step_status['step4'] = 'failed'

    def step6_launch_mcp(self):
        """Step 6: Launch MCP server"""
        marker = self._get_marker("06_mcp")
        
        if check_marker(marker):
            log_progress(9, "Launch MCP server", "skip")
            self.step_status['mcp'] = 'skipped'
            return
        
        log_progress(9, "Launch MCP server", "start")
        
        tool_py = self.mcp_dir / "src" / f"{self.repo_name}_mcp.py"
        python_path = self.mcp_dir / f"{self.repo_name}-env" / "bin" / "python"
        
        if tool_py.exists():
            logger.info(f"  Found {tool_py}")
            logger.info(f"  Installing to claude-code with Python: {python_path}")
            
            try:
                # Install MCP
                run_command([
                    "fastmcp", "install", "claude-code", str(tool_py),
                    "--python", str(python_path)
                ])
                
                logger.info("\n  ✅ MCP server installed!")
                logger.info(f"\n  To launch Claude Code, run: claude")
                
                create_marker(marker)
                log_progress(9, "Launch MCP server", "complete")
                self.step_status['mcp'] = 'executed'
                
            except Exception as e:
                logger.info(f"  ❌ Error installing MCP: {e}", err=True)
                self.step_status['mcp'] = 'failed'
        else:
            logger.info(f"  ⚠️ MCP tool file not found: {tool_py}", err=True)
            logger.info("  Make sure Step 5.4 completed successfully", err=True)
            self.step_status['mcp'] = 'failed'

    def print_summary(self):
        """Print final pipeline summary"""
        logger.info("\n" + "="*50)
        logger.info("🎉 Pipeline Execution Summary")
        logger.info("="*50)
        
        step_descriptions = {
            'setup': '01 Setup project',
            'clone': '02 Clone repository',
            'folders': '03 Prepare folders',
            'context7': '04 Add context MCP',
            'step1': '05.1 Setup env & scan',
            'step2': '05.2 Execute tutorials',
            'step3': '05.3 Extract tools',
            'step4': '05.4 Wrap MCP server',
            'mcp': '06 Launch MCP'
        }
        
        for key, desc in step_descriptions.items():
            status = self.step_status.get(key, 'not run')
            emoji = {
                'executed': '✅',
                'skipped': '⏭️',
                'failed': '❌',
                'not run': '⚪'
            }.get(status, '⚪')
            
            logger.info(f"{emoji} {desc}: {status}")
        
        logger.info("="*50)
        
        # Show next steps
        if self.step_status.get('mcp') == 'executed':
            logger.info("\n📋 Next Steps:")
            logger.info("  - Your MCP server has been installed")
            logger.info("  - Run 'claude' in terminal to launch Claude Code")

    def run_all(self):
        """Run the complete pipeline"""
        try:
            self.step1_setup_project()
            logger.info(f"\n📁 MCP directory: {self.mcp_dir}\n")
            
            self.step2_clone_repo()
            logger.info(f"\n📦 Repository: {self.repo_name}\n")
            
            self.step3_prepare_folders()
            logger.info(f"\n🗂️  Working directories prepared\n")
            
            self.step4_add_context7_mcp()
            logger.info(f"\n🧩 Context7 MCP added\n")
            
            self.step5_1_setup_env()
            logger.info(f"\n⚙️  Python environment setup & tutorials scanned\n")
            
            self.step5_2_execute_tutorials()
            logger.info(f"\n📚 Tutorials executed\n")
            
            self.step5_3_extract_tools()
            logger.info(f"\n🔧 Tools extracted from tutorials\n") 
            
            self.step5_4_wrap_mcp()
            logger.info(f"\n🛠️ MCP server wrapped\n")
            
            self.step6_launch_mcp()
            logger.info(f"\n🚀 MCP server launched\n")
            
            # Print summary
            self.print_summary()
            
        except Exception as e:
            logger.error(f"\n❌ Pipeline failed with error: {e}", err=True)
            self.print_summary()
            raise


# ============================================================================
# CLI Command
# ============================================================================

def create_mcp(github_url: str, local_repo_path: Optional[Path], mcp_dir: Path, tutorial_filter: str, api_key: str, 
               skip_context7: bool):
    """
    Create an MCP (Model Context Protocol) server from a GitHub repository or local code.
    
    This pipeline will:
    1. Setup project environment
    2. Clone the GitHub repository or copy local repository
    3. Prepare working directories
    4. Add context7 MCP server (optional)
    5. Run Claude AI to process tutorials (4 sub-steps)
    6. Launch the MCP server
    
    Examples:\n
        # From GitHub repository:\n
        python create_mcp.py --github-url https://github.com/user/repo  --mcp-dir /path/to/my-mcp-project  --tutorial-filter "machine learning"  --api-key sk-ant-...
        \n
        # From local repository:\n
        python create_mcp.py  --local-repo-path /path/to/local/repo  --mcp-dir /path/to/my-mcp-project --api-key sk-ant-...
    """
    # Validate that either github_url or local_repo_path is provided
    if not github_url and not local_repo_path:
        logger.error("❌ Error: Either --github-url or --local-repo-path must be provided")
        return
    
    if github_url and local_repo_path:
        logger.error("⚠️  Warning: Both --github-url and --local-repo-path provided. Using --local-repo-path")
    
    # Get script directory (directory containing this file)
    script_dir = Path(__file__).parent
    
    # Prompts are always in ./prompts/ subdirectory
    prompts_dir = script_dir / "configs" / "prompts"
    
    # Validate prompts directory exists
    if not prompts_dir.exists():
        logger.info(f"❌ Error: Prompts directory not found: {prompts_dir}")
        logger.info(f"   Please ensure prompts are in: {prompts_dir}")
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
    logger.info(f"🔍 Tutorial Filter: {tutorial_filter or 'None'}")
    logger.info(f"🔑 API Key: {'Set' if api_key else 'Not set'}")
    logger.info(f"📂 Prompts Directory: {prompts_dir}")
    logger.info("\n" + "-"*50 + "\n")
    
    # Create and run MCP Creator
    creator = MCPCreator(
        mcp_dir=mcp_dir,
        script_dir=script_dir,
        prompts_dir=prompts_dir,
        github_url=github_url,
        local_repo_path=str(local_repo_path) if local_repo_path else "",
        tutorial_filter=tutorial_filter,
        api_key=api_key,
        skip_context7=skip_context7
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
@click.option('--tutorial-filter', default='', help='Optional filter for tutorials (e.g., "data visualization", "ML tutorial")')
@click.option('--api-key', default='', envvar='ANTHROPIC_API_KEY', help='API key for notebook execution and testing (or set ANTHROPIC_API_KEY env var)')
@click.option('--skip-context7', is_flag=True, help='Skip adding context7 MCP server')
def cli(github_url: str, local_repo_path: Optional[Path], mcp_dir: Path, tutorial_filter: str, api_key: str, 
        skip_context7: bool):
    create_mcp(
        github_url=github_url,
        local_repo_path=local_repo_path,
        mcp_dir=mcp_dir,
        tutorial_filter=tutorial_filter,
        api_key=api_key,
        skip_context7=skip_context7
    )


if __name__ == '__main__':
    cli()
