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
                 use_case_filter: str = "", api_key: str = ""):
        """
        Initialize MCP Creator
        
        Args:
            mcp_dir: Target directory for MCP project
            script_dir: Directory containing this script
            prompts_dir: Directory containing prompt templates
            github_url: GitHub repository URL to clone (optional if local_repo_path provided)
            local_repo_path: Path to local repository (alternative to github_url)
            use_case_filter: Optional filter for use cases to focus on
            api_key: API key for Claude/Gemini integration testing
        """
        self.mcp_dir = mcp_dir.resolve()
        self.github_url = github_url
        self.local_repo_path = Path(local_repo_path) if local_repo_path else None
        self.script_dir = script_dir
        self.prompts_dir = prompts_dir
        self.use_case_filter = use_case_filter
        self.api_key = api_key
        
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
    
    # ========================================================================
    # Step 1: Setup project environment and prepare working directories
    # ========================================================================
    def step1_setup_project(self) -> Path:
        """Step 1: Setup project environment and prepare working directories"""
        pipeline_dir = self.mcp_dir / ".pipeline"
        marker = self._get_marker("01_setup")
        
        if check_marker(marker):
            log_progress(1, "Setup project environment and prepare working directories", "skip")
            self.step_status['step1'] = 'skipped'
            return self.mcp_dir
        
        log_progress(1, "Setup project environment and prepare working directories", "start")
        
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
        
        # Create all required directories
        folders = [
            "repo",
            "env",
            "scripts",
            "src",
            "examples",
            "notebooks",
            "tests",
            "logs",
            "tmp",
            "claude_outputs"
        ]
        
        for folder in folders:
            folder_path = self.mcp_dir / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"  Created: {folder}")
        
        create_marker(marker)
        log_progress(1, "Setup project environment and prepare working directories", "complete")
        self.step_status['step1'] = 'executed'
        
        return self.mcp_dir

    # ========================================================================
    # Step 2: Clone GitHub repository
    # ========================================================================
    def step2_clone_repo(self) -> str:
        """Step 2: Clone the GitHub repository or use local repository"""
        repo_dir = self.mcp_dir / "repo" / self.repo_name
        marker = self._get_marker("02_clone")
        
        if check_marker(marker):
            log_progress(2, "Clone GitHub repository", "skip")
            self.step_status['step2'] = 'skipped'
            return self.repo_name
        
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
            self.step_status['step2'] = 'executed'
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
        self.step_status['step2'] = 'executed'
        
        return self.repo_name

    # ========================================================================
    # Step 3: Setup conda environment & scan common use cases
    # ========================================================================
    def step3_setup_env_and_scan(self):
        """Step 3: Setup conda environment & scan common use cases"""
        marker = self._get_marker("03_setup_env")
        output_file = self.mcp_dir / "claude_outputs" / "step3_output.json"
        
        if check_marker(marker):
            log_progress(3, "Setup conda environment & scan common use cases", "skip")
            self.step_status['step3'] = 'skipped'
            return
        
        log_progress(3, "Setup conda environment & scan common use cases", "start")
        
        # Read and prepare prompt
        prompt_file = self.prompts_dir / "step3_setup_env_prompt.md"
        if not prompt_file.exists():
            logger.warning(f"  ⚠️ Prompt file not found: {prompt_file}")
            logger.warning("  You'll need to run this step manually or create the prompt file")
            self.step_status['step3'] = 'failed'
            return
        
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
        
        # Replace placeholders
        prompt_content = prompt_content.replace('${repo_name}', self.repo_name)
        prompt_content = prompt_content.replace('${use_case_filter}', self.use_case_filter or '')
        
        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir):
            create_marker(marker)
            log_progress(3, "Setup conda environment & scan common use cases", "complete")
            self.step_status['step3'] = 'executed'
        else:
            self.step_status['step3'] = 'failed'

    # ========================================================================
    # Step 4: Execute the common use cases in repository (bugfix if needed)
    # ========================================================================
    def step4_execute_use_cases(self):
        """Step 4: Execute the common use cases in repository (bugfix if needed)"""
        marker = self._get_marker("04_execute_cases")
        output_file = self.mcp_dir / "claude_outputs" / "step4_output.json"
        
        if check_marker(marker):
            log_progress(4, "Execute common use cases (bugfix if needed)", "skip")
            self.step_status['step4'] = 'skipped'
            return
        
        log_progress(4, "Execute common use cases (bugfix if needed)", "start")
        
        # Read and prepare prompt
        prompt_file = self.prompts_dir / "step4_execute_cases_prompt.md"
        if not prompt_file.exists():
            logger.warning(f"  ⚠️ Prompt file not found: {prompt_file}")
            logger.warning("  You'll need to run this step manually or create the prompt file")
            self.step_status['step4'] = 'failed'
            return
        
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
        
        # Replace placeholders
        prompt_content = prompt_content.replace('${repo_name}', self.repo_name)
        prompt_content = prompt_content.replace('${api_key}', self.api_key or '')
        
        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir):
            create_marker(marker)
            log_progress(4, "Execute common use cases (bugfix if needed)", "complete")
            self.step_status['step4'] = 'executed'
        else:
            self.step_status['step4'] = 'failed'

    # ========================================================================
    # Step 5: Write script for functions to execute common use cases
    # ========================================================================
    def step5_write_scripts(self):
        """Step 5: Write script for functions to execute common use cases (test and bugfix if needed)"""
        marker = self._get_marker("05_write_scripts")
        output_file = self.mcp_dir / "claude_outputs" / "step5_output.json"
        
        if check_marker(marker):
            log_progress(5, "Write scripts for use case functions (test & bugfix)", "skip")
            self.step_status['step5'] = 'skipped'
            return
        
        log_progress(5, "Write scripts for use case functions (test & bugfix)", "start")
        
        # Read and prepare prompt
        prompt_file = self.prompts_dir / "step5_write_scripts_prompt.md"
        if not prompt_file.exists():
            logger.warning(f"  ⚠️ Prompt file not found: {prompt_file}")
            logger.warning("  You'll need to run this step manually or create the prompt file")
            self.step_status['step5'] = 'failed'
            return
        
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
        
        # Replace placeholders
        prompt_content = prompt_content.replace('${repo_name}', self.repo_name)
        prompt_content = prompt_content.replace('${api_key}', self.api_key or '')
        
        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir):
            create_marker(marker)
            log_progress(5, "Write scripts for use case functions (test & bugfix)", "complete")
            self.step_status['step5'] = 'executed'
        else:
            self.step_status['step5'] = 'failed'

    # ========================================================================
    # Step 6: Extract MCP tools from use case scripts and wrap in MCP server
    # ========================================================================
    def step6_extract_and_wrap_mcp(self):
        """Step 6: Extract MCP tools from use case scripts and wrap in MCP server (test and bugfix if needed)"""
        marker = self._get_marker("06_wrap_mcp")
        output_file = self.mcp_dir / "claude_outputs" / "step6_output.json"
        
        if check_marker(marker):
            log_progress(6, "Extract MCP tools & wrap in MCP server (test & bugfix)", "skip")
            self.step_status['step6'] = 'skipped'
            return
        
        log_progress(6, "Extract MCP tools & wrap in MCP server (test & bugfix)", "start")
        
        # Read prompt
        prompt_file = self.prompts_dir / "step6_wrap_mcp_prompt.md"
        if not prompt_file.exists():
            logger.warning(f"  ⚠️ Prompt file not found: {prompt_file}")
            logger.warning("  You'll need to run this step manually or create the prompt file")
            self.step_status['step6'] = 'failed'
            return
        
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
        
        # Replace placeholders
        prompt_content = prompt_content.replace('${repo_name}', self.repo_name)
        
        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir):
            create_marker(marker)
            log_progress(6, "Extract MCP tools & wrap in MCP server (test & bugfix)", "complete")
            self.step_status['step6'] = 'executed'
        else:
            self.step_status['step6'] = 'failed'

    # ========================================================================
    # Step 7: Test Claude and Gemini integration (bugfix if needed)
    # ========================================================================
    def step7_test_integration(self):
        """Step 7: Test Claude and Gemini integration (bugfix if needed)"""
        marker = self._get_marker("07_test_integration")
        output_file = self.mcp_dir / "claude_outputs" / "step7_output.json"
        
        if check_marker(marker):
            log_progress(7, "Test Claude and Gemini integration (bugfix if needed)", "skip")
            self.step_status['step7'] = 'skipped'
            return
        
        log_progress(7, "Test Claude and Gemini integration (bugfix if needed)", "start")
        
        # Check if MCP server file exists
        tool_py = self.mcp_dir / "src" / f"{self.repo_name}_mcp.py"
        if not tool_py.exists():
            logger.warning(f"  ⚠️ MCP tool file not found: {tool_py}")
            logger.warning("  Make sure Step 6 completed successfully")
            self.step_status['step7'] = 'failed'
            return
        
        # Read prompt
        prompt_file = self.prompts_dir / "step7_test_integration_prompt.md"
        if not prompt_file.exists():
            logger.warning(f"  ⚠️ Prompt file not found: {prompt_file}")
            logger.warning("  You'll need to run this step manually or create the prompt file")
            self.step_status['step7'] = 'failed'
            return
        
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
        
        # Replace placeholders
        prompt_content = prompt_content.replace('${repo_name}', self.repo_name)
        prompt_content = prompt_content.replace('${api_key}', self.api_key or '')
        
        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir):
            create_marker(marker)
            log_progress(7, "Test Claude and Gemini integration (bugfix if needed)", "complete")
            self.step_status['step7'] = 'executed'
            
            # Show success message
            logger.info("\n  ✅ MCP server created and tested!")
            logger.info(f"  📁 MCP server location: {tool_py}")
            logger.info(f"\n  To install the MCP server, run:")
            logger.info(f"    fastmcp install claude-code {tool_py}")
        else:
            self.step_status['step7'] = 'failed'

    def print_summary(self):
        """Print final pipeline summary"""
        logger.info("\n" + "="*60)
        logger.info("🎉 Pipeline Execution Summary")
        logger.info("="*60)
        
        step_descriptions = {
            'step1': '1. Setup project environment & directories',
            'step2': '2. Clone GitHub repository',
            'step3': '3. Setup conda env & scan use cases',
            'step4': '4. Execute common use cases',
            'step5': '5. Write scripts for use case functions',
            'step6': '6. Extract MCP tools & wrap in server',
            'step7': '7. Test Claude & Gemini integration'
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
        
        logger.info("="*60)
        
        # Show next steps
        if self.step_status.get('step7') == 'executed':
            logger.info("\n📋 Next Steps:")
            logger.info("  - Your MCP server has been created and tested")
            logger.info(f"  - MCP file: {self.mcp_dir}/src/{self.repo_name}_mcp.py")
            logger.info("  - Install with: fastmcp install claude-code <mcp_file>")
            logger.info("  - Then run 'claude' in terminal to use it")

    def run_all(self):
        """Run the complete pipeline"""
        try:
            # Step 1: Setup project environment and prepare working directories
            self.step1_setup_project()
            logger.info(f"\n📁 MCP directory: {self.mcp_dir}\n")
            
            # Step 2: Clone GitHub repository
            self.step2_clone_repo()
            logger.info(f"\n📦 Repository: {self.repo_name}\n")
            
            # Step 3: Setup conda environment & scan common use cases
            self.step3_setup_env_and_scan()
            logger.info(f"\n⚙️  Conda environment setup & use cases scanned\n")
            
            # Step 4: Execute the common use cases in repository
            self.step4_execute_use_cases()
            logger.info(f"\n🔄 Common use cases executed\n")
            
            # Step 5: Write script for functions to execute common use cases
            self.step5_write_scripts()
            logger.info(f"\n📝 Scripts written for use case functions\n")
            
            # Step 6: Extract MCP tools from use case scripts and wrap in MCP server
            self.step6_extract_and_wrap_mcp()
            logger.info(f"\n🛠️  MCP tools extracted and wrapped\n")
            
            # Step 7: Test Claude and Gemini integration
            self.step7_test_integration()
            logger.info(f"\n🧪 Integration testing complete\n")
            
            # Print summary
            self.print_summary()
            
        except Exception as e:
            logger.error(f"\n❌ Pipeline failed with error: {e}")
            self.print_summary()
            raise


# ============================================================================
# CLI Command
# ============================================================================

def create_mcp(github_url: str, local_repo_path: Optional[Path], mcp_dir: Path, 
               use_case_filter: str, api_key: str):
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
    
    Examples:\n
        # From GitHub repository:\n
        python create_mcp.py --github-url https://github.com/user/repo --mcp-dir /path/to/my-mcp
        \n
        # From local repository:\n
        python create_mcp.py --local-repo-path /path/to/local/repo --mcp-dir /path/to/my-mcp
    """
    # Validate that either github_url or local_repo_path is provided
    if not github_url and not local_repo_path:
        logger.error("❌ Error: Either --github-url or --local-repo-path must be provided")
        return
    
    if github_url and local_repo_path:
        logger.warning("⚠️  Warning: Both --github-url and --local-repo-path provided. Using --local-repo-path")
    
    # Get script directory (directory containing this file)
    script_dir = Path(__file__).parent
    
    # Prompts are always in ./configs/prompts/ subdirectory
    prompts_dir = script_dir / "configs" / "prompts"
    
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
        use_case_filter=use_case_filter,
        api_key=api_key
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
@click.option('--api-key', default='', envvar='ANTHROPIC_API_KEY', 
              help='API key for Claude/Gemini testing (or set ANTHROPIC_API_KEY env var)')
def cli(github_url: str, local_repo_path: Optional[Path], mcp_dir: Path, 
        use_case_filter: str, api_key: str):
    create_mcp(
        github_url=github_url,
        local_repo_path=local_repo_path,
        mcp_dir=mcp_dir,
        use_case_filter=use_case_filter,
        api_key=api_key
    )


if __name__ == '__main__':
    cli()
