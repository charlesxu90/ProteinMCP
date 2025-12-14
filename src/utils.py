
import os
import re
import time
import sys
import click
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional
import threading



# ============================================================================
# Helper Functions
# ============================================================================

class ProgressSpinner:
    """Simple spinner for showing progress"""
    def __init__(self, message: str):
        self.message = message
        self.running = False
        self.thread = None
        self.frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current = 0
        
    def _spin(self):
        while self.running:
            frame = self.frames[self.current % len(self.frames)]
            click.echo(f'\r  {frame} {self.message}', nl=False)
            self.current += 1
            time.sleep(0.1)
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self, final_message: str = None):
        self.running = False
        if self.thread:
            self.thread.join()
        # Clear the spinner line
        click.echo('\r' + ' ' * (len(self.message) + 10), nl=False)
        click.echo('\r', nl=False)
        if final_message:
            click.echo(f'  {final_message}')


def extract_progress_info(text: str) -> Optional[str]:
    """Extract meaningful progress information from output"""
    # Look for common progress patterns
    patterns = [
        r'(Step \d+/\d+)',
        r'(\d+%)',
        r'(Predicting:.*?\d+/\d+)',
        r'(Processing:.*?\d+/\d+)',
        r'(Running:.*)',
        r'(Creating:.*)',
        r'(Loading:.*)',
        r'(Executing:.*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def format_claude_output(text: str) -> tuple[Optional[str], bool]:
    """
    Format Claude output for display, detecting different message types.
    Returns: (formatted_text, should_display)
    
    Detects:
    - Thinking blocks (marked with <) 
    - System messages (marked with [, like [thinking], [system])
    - Planning/reasoning keywords (I need to, I'll, Let me, I'm thinking, etc.)
    - Regular responses
    """
    text = text.rstrip()
    if not text:
        return None, False
    
    # Skip empty lines and just newlines
    if text.strip() == '':
        return None, False
    
    # Detect thinking blocks
    if text.startswith('<'):
        return f"  🤖💭 {text[:80]}...", True if len(text) > 80 else False
    
    # Detect system/status messages with thinking/planning
    if text.startswith('['):
        if '[thinking]' in text.lower() or '[analysis]' in text.lower():
            return f"  🤖🧠 {text}", True
        elif '[system]' in text.lower() or '[status]' in text.lower():
            return f"  ⚙️  {text}", True
        else:
            return f"  📋 {text}", True
    
    # Detect headers or important lines
    if text.startswith('#'):
        return f"  📝 {text}", True
    
    # Detect planning/thinking keywords
    planning_keywords = [
        'i need to', 'i\'ll', 'let me', 'i\'m thinking', 'i should', 
        'i will', 'i have to', 'i plan to', 'thinking about', 'analyzing',
        'let\'s', 'first, i', 'my plan', 'my approach', 'what i\'ll do',
        'considering', 'evaluating', 'determining', 'checking', 'verifying'
    ]
    
    text_lower = text.lower()
    if any(keyword in text_lower for keyword in planning_keywords):
        return f"  🤖 {text[:90]}", len(text) > 90
    
    # Regular content - check if it's substantial
    if len(text.strip()) > 3:
        return f"  {text[:90]}", len(text) > 90
    
    return None, False


def display_claude_streaming(line: str, buffer: list, buffer_threshold: int = 200) -> list:
    """
    Display Claude streaming output with buffering for readability.
    
    Args:
        line: Current line from Claude's output
        buffer: Accumulated text buffer
        buffer_threshold: Characters before displaying buffer
        
    Returns:
        Updated buffer list
    """
    buffer.append(line)
    accumulated = ''.join(buffer)
    
    # If we have enough accumulated text, display it
    if len(accumulated) >= buffer_threshold:
        formatted, is_partial = format_claude_output(accumulated)
        if formatted:
            click.echo(formatted)
        return []
    
    return buffer

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


def _display_claude_line(line: str, log_data: dict) -> None:
    """
    Parse and display a line from Claude CLI stream-json output.
    
    The stream-json format outputs JSON objects like:
    {"type": "assistant", "message": {...}, "session_id": "..."}
    {"type": "result", "subtype": "success", ...}
    {"type": "system", "subtype": "init", ...}
    """
    import json
    
    if not line.strip():
        return
    
    # Try to parse as JSON
    try:
        data = json.loads(line)
        msg_type = data.get('type', '')
        subtype = data.get('subtype', '')
        
        # Handle different message types
        if msg_type == 'system':
            if subtype == 'init':
                session_id = data.get('session_id', '')[:8]
                click.echo(f"  🤖 Session started: {session_id}...")
            elif subtype == 'transcript':
                click.echo(f"  📋 Transcript saved")
            else:
                click.echo(f"  ⚙️  System: {subtype}")
            sys.stdout.flush()
            
        elif msg_type == 'assistant':
            message = data.get('message', {})
            content = message.get('content', [])
            
            for block in content:
                block_type = block.get('type', '')
                
                if block_type == 'thinking':
                    thinking_text = block.get('thinking', '')[:100]
                    click.echo(f"  🤖💭 Thinking: {thinking_text}...")
                    log_data["progress_events"].append({
                        "timestamp": time.strftime('%H:%M:%S'),
                        "type": "thinking",
                        "message": thinking_text
                    })
                    
                elif block_type == 'text':
                    text = block.get('text', '')
                    # Show text content - split by lines and display
                    lines = text.strip().split('\n')
                    for text_line in lines[:5]:  # Show first 5 lines
                        if text_line.strip():
                            # Check for planning keywords
                            planning_keywords = [
                                'i need to', 'i\'ll', 'let me', 'i\'m thinking', 'i should', 
                                'i will', 'i have to', 'i plan to', 'analyzing',
                                'let\'s', 'first,', 'my plan', 'checking', 'verifying'
                            ]
                            line_lower = text_line.lower()
                            if any(kw in line_lower for kw in planning_keywords):
                                click.echo(f"  🤖 {text_line}")
                            elif text_line.startswith('#'):
                                click.echo(f"  📝 {text_line}")
                            else:
                                click.echo(f"  {text_line}")
                    if len(lines) > 5:
                        click.echo(f"  ... ({len(lines) - 5} more lines)")
                    log_data["progress_events"].append({
                        "timestamp": time.strftime('%H:%M:%S'),
                        "type": "text",
                        "message": text[:500]
                    })
                    
                elif block_type == 'tool_use':
                    tool_name = block.get('name', 'unknown')
                    tool_input = block.get('input', {})
                    
                    # Show tool details based on tool type
                    if tool_name == 'Bash':
                        cmd = tool_input.get('command', '')[:80]
                        click.echo(f"  🔧 Bash: {cmd}")
                    elif tool_name == 'Read':
                        file_path = tool_input.get('file_path', '')
                        click.echo(f"  📖 Read: {file_path}")
                    elif tool_name == 'Write' or tool_name == 'Edit':
                        file_path = tool_input.get('file_path', '')
                        click.echo(f"  ✏️  {tool_name}: {file_path}")
                    elif tool_name == 'Glob':
                        pattern = tool_input.get('pattern', '')
                        click.echo(f"  🔍 Glob: {pattern}")
                    elif tool_name == 'Grep':
                        pattern = tool_input.get('pattern', '')
                        click.echo(f"  🔎 Grep: {pattern}")
                    elif tool_name == 'Task':
                        description = tool_input.get('description', '')[:60]
                        click.echo(f"  📋 Task: {description}")
                    elif tool_name == 'TodoWrite':
                        todos = tool_input.get('todos', [])
                        click.echo(f"  📝 TodoWrite: {len(todos)} items")
                    elif tool_name == 'TodoRead':
                        click.echo(f"  📝 TodoRead")
                    else:
                        click.echo(f"  🔧 {tool_name}")
                    
                    log_data["progress_events"].append({
                        "timestamp": time.strftime('%H:%M:%S'),
                        "type": "tool_use",
                        "tool": tool_name,
                        "input": str(tool_input)[:200]
                    })
                    
            sys.stdout.flush()
            
        elif msg_type == 'user':
            message = data.get('message', {})
            content = message.get('content', [])
            for block in content:
                if block.get('type') == 'tool_result':
                    tool_id = block.get('tool_use_id', '')[:8]
                    is_error = block.get('is_error', False)
                    result_content = block.get('content', '')
                    
                    if is_error:
                        # Show error details
                        error_msg = result_content[:100] if isinstance(result_content, str) else str(result_content)[:100]
                        click.echo(f"  ❌ Error: {error_msg}")
                    else:
                        # Show brief result for successful tools
                        if isinstance(result_content, str) and result_content.strip():
                            # Show first line of result
                            first_line = result_content.strip().split('\n')[0][:80]
                            if first_line:
                                click.echo(f"  ✅ Result: {first_line}")
                        else:
                            click.echo(f"  ✅ Done")
                    
                    log_data["progress_events"].append({
                        "timestamp": time.strftime('%H:%M:%S'),
                        "type": "tool_result",
                        "is_error": is_error,
                        "content": str(result_content)[:500]
                    })
            sys.stdout.flush()
            
        elif msg_type == 'result':
            if subtype == 'success':
                click.echo(f"  ✅ Completed successfully")
            elif subtype == 'error':
                error = data.get('error', 'Unknown error')
                click.echo(f"  ❌ Error: {error}")
            sys.stdout.flush()
            
    except json.JSONDecodeError:
        # Not JSON, display as plain text
        if line.strip():
            click.echo(f"  {line}")
            sys.stdout.flush()
            log_data["progress_events"].append({
                "timestamp": time.strftime('%H:%M:%S'),
                "message": line[:200]
            })


def run_claude_with_streaming(prompt_content: str, output_file: Path, cwd: Path, api_key: Optional[str] = None) -> bool:
    """
    Run Claude AI with real-time output display and full logging
    
    Uses Claude Code CLI (logged-in Pro account) - no API key required.
    This function ALWAYS uses Claude Code CLI, never the API.
    Shows Claude's thinking, analysis, and responses in real-time in terminal, saves full output to JSON file.
    
    Args:
        prompt_content: The prompt to send to Claude
        output_file: Path to save the output JSON
        cwd: Working directory for the command
        api_key: IGNORED - Claude Code CLI uses logged-in account, not API key
    
    Returns:
        True if successful, False otherwise
    """
    import json
    
    # Always use Claude Code CLI (Pro account), ignore any API key
    click.echo("  🤖 Using Claude Code CLI (logged-in Pro account)")
    click.echo("  💡 Note: Using your Pro account subscription, NOT API credits")
    click.echo("  " + "-" * 58)
    
    # Check if claude CLI is available
    claude_path = shutil.which("claude")
    if not claude_path:
        click.echo("  ❌ Claude CLI not found. Please install Claude Code CLI:")
        click.echo("     npm install -g @anthropic-ai/claude-code")
        click.echo("     Then login with: claude login")
        return False
    
    click.echo(f"  📍 Using Claude at: {claude_path}")
    
    try:
        # Run Claude with real-time output streaming
        cmd = [
            "claude",
            "--model", "claude-sonnet-4-20250514",
            "-p", "-",
            "--output-format", "stream-json",
            "--verbose",
            "--dangerously-skip-permissions"
        ]
        
        log_data = {
            "method": "Claude Code CLI",
            "command": ' '.join(cmd),
            "working_directory": str(cwd),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "raw_output": "",
            "progress_events": [],
            "status": "running"
        }
        
        # Stream output while collecting data
        raw_output = []
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Send prompt to stdin
        process.stdin.write(prompt_content)
        process.stdin.close()
        
        # Read and process output line by line - display immediately
        # Read from both stdout (JSON events) and stderr (verbose logs)
        import select
        
        while True:
            # Check if process has ended
            if process.poll() is not None:
                # Read any remaining output
                remaining_stdout = process.stdout.read()
                remaining_stderr = process.stderr.read()
                if remaining_stdout:
                    raw_output.append(remaining_stdout)
                    for line in remaining_stdout.split('\n'):
                        if line.strip():
                            _display_claude_line(line, log_data)
                if remaining_stderr:
                    for line in remaining_stderr.split('\n'):
                        if line.strip():
                            click.echo(f"  ⚙️  {line}")
                            sys.stdout.flush()
                break
            
            # Use select to read from stdout and stderr without blocking
            try:
                readable, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)
            except (ValueError, OSError):
                break
            
            for stream in readable:
                line = stream.readline()
                if line:
                    if stream == process.stdout:
                        raw_output.append(line)
                        _display_claude_line(line.rstrip('\n'), log_data)
                    else:
                        # stderr - verbose output
                        line_text = line.rstrip('\n')
                        if line_text.strip():
                            click.echo(f"  ⚙️  {line_text}")
                            sys.stdout.flush()
        
        # Wait for process to complete
        return_code = process.wait()
        click.echo("  " + "-" * 58)
        
        if return_code != 0:
            click.echo(f"  ❌ Claude CLI exited with code {return_code}")
            log_data["status"] = "failed"
            log_data["return_code"] = return_code
            log_data["raw_output"] = ''.join(raw_output)
            
            with open(output_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            return False
        
        # Save to JSON
        log_data["raw_output"] = ''.join(raw_output)
        log_data["status"] = "success"
        log_data["return_code"] = return_code
        
        with open(output_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        click.echo("  ✅ Successfully completed using Claude Code CLI")
        click.echo(f"  📄 Log saved to: {output_file}")
        click.echo(f"  💡 View log: python src/view_logs.py {output_file}")
        return True
        
    except Exception as e:
        click.echo(f"  ❌ Claude Code CLI failed: {e}", err=True)
        click.echo("  💡 Make sure you're logged in with: claude login")
        return False
