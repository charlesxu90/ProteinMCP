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


# Global variables
step_status = {}
repo_name = None


# ============================================================================
# Helper Functions
# ============================================================================

def log_progress(step_num: int, description: str, status: str):
    """Log progress of pipeline steps"""
    emoji_map = {
        "start": "🚀",
        "complete": "✅",
        "skip": "⏭️"
    }
    emoji = emoji_map.get(status, "📋")
    click.echo(f"{emoji} Step {step_num}: {description} - {status.upper()}")


def check_marker(marker_path: Path) -> bool:
    """Check if a step has already been completed"""
    return marker_path.exists()


def create_marker(marker_path: Path):
    """Create a marker file to indicate step completion"""
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.touch()


def run_command(cmd: list, cwd: Optional[Path] = None, capture_output: bool = False) -> Optional[str]:
    """Run a shell command"""
    try:
        if capture_output:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, cwd=cwd, check=True)
            return None
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Command failed: {' '.join(cmd)}", err=True)
        click.echo(f"Error: {e}", err=True)
        raise


def run_claude_with_streaming(prompt_content: str, output_file: Path, cwd: Path) -> bool:
    """
    Run Claude AI with real-time output streaming
    
    Args:
        prompt_content: The prompt to send to Claude
        output_file: Path to save the output JSON
        cwd: Working directory for the command
    
    Returns:
        True if successful, False otherwise
    """
    try:
        click.echo("  🤖 Running Claude AI agent...")
        click.echo("  📝 Streaming output:\n")
        
        # Run Claude with real-time output streaming
        cmd = [
            "claude",
            "--model", "claude-sonnet-4-20250514",
            "--verbose",
            "--output-format", "stream-json",
            "--dangerously-skip-permissions",
            "-p", "-"
        ]
        
        # Stream output in real-time while also saving to file
        with open(output_file, 'w') as out_file:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Send prompt to stdin
            process.stdin.write(prompt_content)
            process.stdin.close()
            
            # Read and display output line by line
            for line in process.stdout:
                click.echo(line, nl=False)  # Print to console in real-time
                out_file.write(line)  # Save to file
                out_file.flush()  # Ensure it's written immediately
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code != 0:
                raise subprocess.CalledProcessError(return_code, cmd)
        
        click.echo("\n")
        return True
        
    except Exception as e:
        click.echo(f"  ❌ Error running Claude: {e}", err=True)
        return False


# ============================================================================
# Pipeline Steps
# ============================================================================

def step1_setup_project(mcp_dir: Path, script_dir: Path) -> Path:
    """Setup project environment and directory structure"""
    pipeline_dir = mcp_dir / ".pipeline"
    marker = pipeline_dir / "01_setup_done"
    
    if check_marker(marker):
        log_progress(1, "Setup project environment", "skip")
        step_status['setup'] = 'skipped'
        return mcp_dir
    
    log_progress(1, "Setup project environment", "start")
    
    # Create project directory
    mcp_dir.mkdir(parents=True, exist_ok=True)
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy configs/templates if they exist and not already present
    for folder_name_item in ['claude', 'templates', 'tools']:
        src = script_dir / folder_name_item
        dst = mcp_dir / folder_name_item if folder_name_item != 'claude' else mcp_dir / f'.{folder_name_item}'
        
        if not dst.exists() and src.exists():
            shutil.copytree(src, dst)
            click.echo(f"  Copied {folder_name_item}")
        else:
            click.echo(f"  {folder_name_item} already exists or source missing")
    
    create_marker(marker)
    log_progress(1, "Setup project environment", "complete")
    step_status['setup'] = 'executed'
    
    return mcp_dir


def step2_clone_repo(mcp_dir: Path, github_url: str) -> str:
    """Clone the GitHub repository"""
    global repo_name
    # Extract repo name from URL
    repo_name = Path(github_url.rstrip('.git')).name
    repo_dir = mcp_dir / "repo" / repo_name
    marker = mcp_dir / ".pipeline" / "02_clone_done"
    
    if check_marker(marker):
        log_progress(2, "Clone GitHub repository", "skip")
        step_status['clone'] = 'skipped'
        return repo_name
    
    log_progress(2, "Clone GitHub repository", "start")
    
    # Create repo directory
    (mcp_dir / "repo").mkdir(parents=True, exist_ok=True)
    
    # Skip if already cloned
    if repo_dir.exists():
        click.echo(f"  Repository already exists: {repo_dir}")
    else:
        # Try different cloning strategies
        try:
            # Try with submodules first
            click.echo(f"  Cloning {github_url} with submodules...")
            run_command(["git", "clone", "--recurse-submodules", github_url, str(repo_dir)])
            click.echo("  Cloned with submodules")
        except:
            try:
                # Try shallow clone
                click.echo("  Trying shallow clone...")
                run_command(["git", "clone", "--depth=1", github_url, str(repo_dir)])
                click.echo("  Shallow clone successful")
            except:
                # Try plain clone
                click.echo("  Trying plain clone...")
                run_command(["git", "clone", github_url, str(repo_dir)])
                click.echo("  Plain clone successful")
    
    create_marker(marker)
    log_progress(2, "Clone GitHub repository", "complete")
    step_status['clone'] = 'executed'
    
    return repo_name


def step3_prepare_folders(mcp_dir: Path):
    """Create necessary folder structure for the pipeline"""
    marker = mcp_dir / ".pipeline" / "03_folders_done"
    
    if check_marker(marker):
        log_progress(3, "Prepare working directories", "skip")
        step_status['folders'] = 'skipped'
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
        folder_path = mcp_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        click.echo(f"  Created: {folder}")
    
    create_marker(marker)
    log_progress(3, "Prepare working directories", "complete")
    step_status['folders'] = 'executed'


def step4_add_context7_mcp(mcp_dir: Path, skip_context7: bool = False):
    """Add context7 MCP server (optional)"""
    if skip_context7:
        click.echo("  ⏭️ Skipping context7 MCP (--skip-context7 flag set)")
        step_status['context7'] = 'skipped'
        return
    
    marker = mcp_dir / ".pipeline" / "04_context7_done"
    
    if check_marker(marker):
        log_progress(4, "Add context MCP server", "skip")
        step_status['context7'] = 'skipped'
        return
    
    log_progress(4, "Add context MCP server", "start")
    
    try:
        # Try to add context7 MCP
        run_command(["claude", "mcp", "add", "context7", "--", "npx", "-y", "@upstash/context7-mcp@latest"])
        click.echo("  context7 MCP added successfully")
        create_marker(marker)
        log_progress(4, "Add context MCP server", "complete")
        step_status['context7'] = 'executed'
    except Exception as e:
        click.echo(f"  ⚠️ Warning: Failed to add context7 MCP - {e}", err=True)
        click.echo("  Continuing without context7...")
        # Don't create marker on failure
        step_status['context7'] = 'failed'


def step5_1_setup_env(mcp_dir: Path, prompts_dir: Path, tutorial_filter: str = ""):
    """Step 5.1: Setup Python environment & scan tutorials"""
    marker = mcp_dir / ".pipeline" / "05_step1_done"
    output_file = mcp_dir / "claude_outputs" / "step1_output.json"
    
    if check_marker(marker):
        log_progress(5, "Setup Python environment & scan tutorials", "skip")
        step_status['step1'] = 'skipped'
        return
    
    log_progress(5, "Setup Python environment & scan tutorials", "start")
    
    # Read and prepare prompt
    prompt_file = prompts_dir / "step1_prompt.md"
    if not prompt_file.exists():
        click.echo(f"  ⚠️ Prompt file not found: {prompt_file}", err=True)
        click.echo("  You'll need to run this step manually or ensure prompts/ directory exists", err=True)
        return
    
    with open(prompt_file, 'r') as f:
        prompt_content = f.read()
    
    # Replace placeholders
    prompt_content = prompt_content.replace('${github_repo_name}', repo_name)
    prompt_content = prompt_content.replace('${tutorial_filter}', tutorial_filter or '')
    
    # Run Claude
    if run_claude_with_streaming(prompt_content, output_file, mcp_dir):
        create_marker(marker)
        log_progress(5, "Setup Python environment & scan tutorials", "complete")
        step_status['step1'] = 'executed'
    else:
        step_status['step1'] = 'failed'


def step5_2_execute_tutorials(mcp_dir: Path, prompts_dir: Path, api_key: str = ""):
    """Step 5.2: Execute tutorial notebooks"""
    marker = mcp_dir / ".pipeline" / "05_step2_done"
    output_file = mcp_dir / "claude_outputs" / "step2_output.json"
    
    if check_marker(marker):
        log_progress(6, "Execute tutorial notebooks", "skip")
        step_status['step2'] = 'skipped'
        return
    
    log_progress(6, "Execute tutorial notebooks", "start")
    
    # Read and prepare prompt
    prompt_file = prompts_dir / "step2_prompt.md"
    if not prompt_file.exists():
        click.echo(f"  ⚠️ Prompt file not found: {prompt_file}", err=True)
        click.echo("  You'll need to run this step manually or ensure prompts/ directory exists", err=True)
        return
    
    with open(prompt_file, 'r') as f:
        prompt_content = f.read()
    
    # Replace placeholders
    prompt_content = prompt_content.replace('${api_key}', api_key or '')
    
    # Run Claude
    if run_claude_with_streaming(prompt_content, output_file, mcp_dir):
        create_marker(marker)
        log_progress(6, "Execute tutorial notebooks", "complete")
        step_status['step2'] = 'executed'
    else:
        step_status['step2'] = 'failed'


def step5_3_extract_tools(mcp_dir: Path, prompts_dir: Path, api_key: str = ""):
    """Step 5.3: Extract tools from tutorials"""
    marker = mcp_dir / ".pipeline" / "05_step3_done"
    output_file = mcp_dir / "claude_outputs" / "step3_output.json"
    
    if check_marker(marker):
        log_progress(7, "Extract tools from tutorials", "skip")
        step_status['step3'] = 'skipped'
        return
    
    log_progress(7, "Extract tools from tutorials", "start")
    
    # Read and prepare prompt
    prompt_file = prompts_dir / "step3_prompt.md"
    if not prompt_file.exists():
        click.echo(f"  ⚠️ Prompt file not found: {prompt_file}", err=True)
        click.echo("  You'll need to run this step manually or ensure prompts/ directory exists", err=True)
        return
    
    with open(prompt_file, 'r') as f:
        prompt_content = f.read()
    
    # Replace placeholders
    prompt_content = prompt_content.replace('${api_key}', api_key or '')
    
    # Run Claude
    if run_claude_with_streaming(prompt_content, output_file, mcp_dir):
        create_marker(marker)
        log_progress(7, "Extract tools from tutorials", "complete")
        step_status['step3'] = 'executed'
    else:
        step_status['step3'] = 'failed'


def step5_4_wrap_mcp(mcp_dir: Path, prompts_dir: Path):
    """Step 5.4: Wrap tools in MCP server"""
    marker = mcp_dir / ".pipeline" / "05_step4_done"
    output_file = mcp_dir / "claude_outputs" / "step4_output.json"
    
    if check_marker(marker):
        log_progress(8, "Wrap tools in MCP server", "skip")
        step_status['step4'] = 'skipped'
        return
    
    log_progress(8, "Wrap tools in MCP server", "start")
    
    # Read prompt (no variable substitution needed for step 4)
    prompt_file = prompts_dir / "step4_prompt.md"
    if not prompt_file.exists():
        click.echo(f"  ⚠️ Prompt file not found: {prompt_file}", err=True)
        click.echo("  You'll need to run this step manually or ensure prompts/ directory exists", err=True)
        return
    
    with open(prompt_file, 'r') as f:
        prompt_content = f.read()
    
    # Run Claude
    if run_claude_with_streaming(prompt_content, output_file, mcp_dir):
        create_marker(marker)
        log_progress(8, "Wrap tools in MCP server", "complete")
        step_status['step4'] = 'executed'
    else:
        step_status['step4'] = 'failed'


def step6_launch_mcp(mcp_dir: Path):
    """Step 6: Launch MCP server"""
    marker = mcp_dir / ".pipeline" / "06_mcp_done"
    
    if check_marker(marker):
        log_progress(9, "Launch MCP server", "skip")
        step_status['mcp'] = 'skipped'
        return
    
    log_progress(9, "Launch MCP server", "start")
    
    tool_py = mcp_dir / "src" / f"{repo_name}_mcp.py"
    python_path = mcp_dir / f"{repo_name}-env" / "bin" / "python"
    
    if tool_py.exists():
        click.echo(f"  Found {tool_py}")
        click.echo(f"  Installing to claude-code with Python: {python_path}")
        
        try:
            # Install MCP
            run_command([
                "fastmcp", "install", "claude-code", str(tool_py),
                "--python", str(python_path)
            ])
            
            click.echo("\n  ✅ MCP server installed!")
            click.echo(f"\n  To launch Claude Code, run: claude")
            
            create_marker(marker)
            log_progress(9, "Launch MCP server", "complete")
            step_status['mcp'] = 'executed'
            
        except Exception as e:
            click.echo(f"  ❌ Error installing MCP: {e}", err=True)
            step_status['mcp'] = 'failed'
    else:
        click.echo(f"  ⚠️ MCP tool file not found: {tool_py}", err=True)
        click.echo("  Make sure Step 5.4 completed successfully", err=True)
        step_status['mcp'] = 'failed'


def print_summary():
    """Print final pipeline summary"""
    click.echo("\n" + "="*50)
    click.echo("🎉 Pipeline Execution Summary")
    click.echo("="*50)
    
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
        status = step_status.get(key, 'not run')
        emoji = {
            'executed': '✅',
            'skipped': '⏭️',
            'failed': '❌',
            'not run': '⚪'
        }.get(status, '⚪')
        
        click.echo(f"{emoji} {desc}: {status}")
    
    click.echo("="*50)
    
    # Show next steps
    if step_status.get('mcp') == 'executed' and repo_name:
        click.echo("\n📋 Next Steps:")
        click.echo("  - Your MCP server has been installed")
        click.echo("  - Run 'claude' in terminal to launch Claude Code")


# ============================================================================
# CLI Command
# ============================================================================

@click.command()
@click.option('--github-url', required=True, help='GitHub repository URL (e.g., https://github.com/user/repo)')
@click.option('--mcp-dir', required=True, type=click.Path(path_type=Path), 
              help='MCP project directory to create (e.g., /path/to/my-mcp-project)')
@click.option('--tutorial-filter', default='', help='Optional filter for tutorials (e.g., "data visualization", "ML tutorial")')
@click.option('--api-key', default='', envvar='ANTHROPIC_API_KEY', help='API key for notebook execution and testing (or set ANTHROPIC_API_KEY env var)')
@click.option('--skip-context7', is_flag=True, help='Skip adding context7 MCP server')
def create_mcp(github_url: str, mcp_dir: Path, tutorial_filter: str, api_key: str, 
               skip_context7: bool):
    """
    Create an MCP (Model Context Protocol) server from a GitHub repository with tutorials.
    
    This pipeline will:
    1. Setup project environment
    2. Clone the GitHub repository
    3. Prepare working directories
    4. Add context7 MCP server (optional)
    5. Run Claude AI to process tutorials (4 sub-steps)
    6. Launch the MCP server
    
    Example:
        python create_mcp.py \\
            --github-url https://github.com/user/repo \\
            --mcp-dir /path/to/my-mcp-project \\
            --tutorial-filter "machine learning" \\
            --api-key sk-ant-...
    """
    # Get script directory (directory containing this file)
    script_dir = Path(__file__).parent
    
    # Prompts are always in ./prompts/ subdirectory
    prompts_dir = script_dir / "prompts"
    
    # Validate prompts directory exists
    if not prompts_dir.exists():
        click.echo(f"❌ Error: Prompts directory not found: {prompts_dir}", err=True)
        click.echo(f"   Please ensure prompts are in: {prompts_dir}", err=True)
        return
    
    # Convert to absolute path
    mcp_dir = mcp_dir.resolve()
    
    # Display configuration
    click.echo("🚀 Starting MCP Creation Pipeline\n")
    click.echo(f"📦 Repository: {github_url}")
    click.echo(f"📁 MCP Directory: {mcp_dir}")
    click.echo(f"🔍 Tutorial Filter: {tutorial_filter or 'None'}")
    click.echo(f"🔑 API Key: {'Set' if api_key else 'Not set'}")
    click.echo(f"📂 Prompts Directory: {prompts_dir}")
    click.echo("\n" + "-"*50 + "\n")
    
    # Run all steps
    try:
        step1_setup_project(mcp_dir, script_dir)
        click.echo(f"\n📁 MCP directory: {mcp_dir}\n")
        
        step2_clone_repo(mcp_dir, github_url)
        click.echo(f"\n📦 Repository: {repo_name}\n")
        
        step3_prepare_folders(mcp_dir)
        click.echo()
        
        step4_add_context7_mcp(mcp_dir, skip_context7)
        click.echo()
        
        step5_1_setup_env(mcp_dir, prompts_dir, tutorial_filter)
        
        step5_2_execute_tutorials(mcp_dir, prompts_dir, api_key)
        
        step5_3_extract_tools(mcp_dir, prompts_dir, api_key)
        
        step5_4_wrap_mcp(mcp_dir, prompts_dir)
        
        step6_launch_mcp(mcp_dir)
        
        # Print summary
        print_summary()
        
    except Exception as e:
        click.echo(f"\n❌ Pipeline failed with error: {e}", err=True)
        print_summary()
        raise click.Abort()


if __name__ == '__main__':
    create_mcp()
