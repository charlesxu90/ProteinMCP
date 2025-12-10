
import os
import click
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional



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
