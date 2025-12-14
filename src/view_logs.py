#!/usr/bin/env python3
"""
Log Viewer for MCP Creation Pipeline

This script provides a Claude Code-style view of pipeline logs stored in JSON format.
"""

import sys
import json
from pathlib import Path
import click
import re


def format_output_snippet(text: str, max_lines: int = 20) -> str:
    """Format output text showing first and last N lines"""
    lines = text.split('\n')
    
    if len(lines) <= max_lines * 2:
        return text
    
    first_lines = lines[:max_lines]
    last_lines = lines[-max_lines:]
    omitted = len(lines) - (max_lines * 2)
    
    return '\n'.join(first_lines) + f'\n\n... ({omitted} lines omitted) ...\n\n' + '\n'.join(last_lines)


def display_log_summary(log_data: dict, verbose: bool = False):
    """Display a clean summary of the log in Claude Code style"""
    
    # Header
    click.echo("\n" + "="*80)
    click.echo("📋 MCP Pipeline Execution Log")
    click.echo("="*80)
    
    # Metadata
    click.echo(f"\n🤖 Method: {log_data.get('method', 'Unknown')}")
    if 'command' in log_data:
        click.echo(f"⚙️  Command: {log_data['command']}")
    if 'model' in log_data:
        click.echo(f"🧠 Model: {log_data['model']}")
    click.echo(f"📁 Working Directory: {log_data.get('working_directory', 'Unknown')}")
    click.echo(f"🕐 Timestamp: {log_data.get('timestamp', 'Unknown')}")
    
    status = log_data.get('status', 'unknown')
    status_emoji = "✅" if status == "success" else "❌" if status == "error" else "⏳"
    click.echo(f"{status_emoji} Status: {status.upper()}")
    
    if 'return_code' in log_data:
        click.echo(f"🔢 Return Code: {log_data['return_code']}")
    
    # Progress Events
    progress_events = log_data.get('progress_events', [])
    if progress_events:
        click.echo(f"\n📊 Progress Timeline ({len(progress_events)} events):")
        click.echo("-"*80)
        for event in progress_events:
            timestamp = event.get('timestamp', '??:??:??')
            message = event.get('message', 'Unknown event')
            click.echo(f"  [{timestamp}] {message}")
    
    # Output Preview
    raw_output = log_data.get('raw_output', '')
    if raw_output:
        click.echo("\n📝 Output Preview:")
        click.echo("-"*80)
        
        if verbose:
            click.echo(raw_output)
        else:
            # Show condensed version
            preview = format_output_snippet(raw_output, max_lines=15)
            click.echo(preview)
            
            if len(raw_output.split('\n')) > 30:
                click.echo("\n💡 Use --verbose to see full output")
    
    click.echo("\n" + "="*80 + "\n")


@click.command()
@click.argument('log_file', type=click.Path(exists=True, path_type=Path))
@click.option('--verbose', '-v', is_flag=True, help='Show full output (not just preview)')
@click.option('--raw', '-r', is_flag=True, help='Show raw output only (no formatting)')
@click.option('--progress', '-p', is_flag=True, help='Show only progress events')
@click.option('--json', '-j', 'show_json', is_flag=True, help='Show raw JSON')
@click.option('--search', '-s', type=str, default=None, help='Search for text in output')
def view_log(log_file: Path, verbose: bool, raw: bool, progress: bool, show_json: bool, search: str):
    """
    View MCP pipeline logs in a clean, Claude Code-style format.
    
    Examples:
    
        # View log summary
        python view_logs.py claude_outputs/step3_output.json
        
        # View with full output
        python view_logs.py claude_outputs/step3_output.json --verbose
        
        # View only progress events
        python view_logs.py claude_outputs/step3_output.json --progress
        
        # View raw output only
        python view_logs.py claude_outputs/step3_output.json --raw
        
        # Search in output
        python view_logs.py claude_outputs/step3_output.json --search "error"
        
        # View raw JSON
        python view_logs.py claude_outputs/step3_output.json --json
    """
    
    try:
        with open(log_file, 'r') as f:
            log_data = json.load(f)
    except json.JSONDecodeError:
        click.echo(f"❌ Error: {log_file} is not a valid JSON file", err=True)
        return 1
    except Exception as e:
        click.echo(f"❌ Error reading file: {e}", err=True)
        return 1
    
    # JSON output
    if show_json:
        click.echo(json.dumps(log_data, indent=2))
        return 0
    
    # Progress only
    if progress:
        progress_events = log_data.get('progress_events', [])
        if not progress_events:
            click.echo("No progress events recorded")
            return 0
        
        click.echo("\n📊 Progress Timeline:")
        click.echo("-"*80)
        for event in progress_events:
            timestamp = event.get('timestamp', '??:??:??')
            message = event.get('message', 'Unknown event')
            click.echo(f"  [{timestamp}] {message}")
        click.echo()
        return 0
    
    # Raw output only
    if raw:
        output = log_data.get('raw_output', '')
        if search:
            # Filter lines containing search term
            lines = [line for line in output.split('\n') if search.lower() in line.lower()]
            click.echo('\n'.join(lines))
        else:
            click.echo(output)
        return 0
    
    # Search in output
    if search:
        output = log_data.get('raw_output', '')
        lines = output.split('\n')
        matches = []
        
        for i, line in enumerate(lines):
            if search.lower() in line.lower():
                # Show context: 2 lines before and after
                start = max(0, i-2)
                end = min(len(lines), i+3)
                context = '\n'.join(lines[start:end])
                matches.append(f"Line {i+1}:\n{context}\n")
        
        if matches:
            click.echo(f"\n🔍 Found {len(matches)} matches for '{search}':")
            click.echo("-"*80)
            for match in matches[:10]:  # Show first 10 matches
                click.echo(match)
            
            if len(matches) > 10:
                click.echo(f"... and {len(matches) - 10} more matches")
        else:
            click.echo(f"❌ No matches found for '{search}'")
        return 0
    
    # Default: show formatted summary
    display_log_summary(log_data, verbose=verbose)
    return 0


@click.command()
@click.argument('mcp_dir', type=click.Path(exists=True, path_type=Path))
def list_logs(mcp_dir: Path):
    """
    List all available log files in the MCP directory.
    
    Example:
        python view_logs.py list /path/to/mcp-project
    """
    claude_outputs = mcp_dir / "claude_outputs"
    
    if not claude_outputs.exists():
        click.echo(f"❌ No claude_outputs directory found in {mcp_dir}")
        return 1
    
    log_files = sorted(claude_outputs.glob("*.json"))
    
    if not log_files:
        click.echo(f"📭 No log files found in {claude_outputs}")
        return 0
    
    click.echo(f"\n📋 Log files in {claude_outputs}:\n")
    click.echo("-"*80)
    
    for log_file in log_files:
        size = log_file.stat().st_size
        size_str = f"{size:,} bytes"
        if size > 1024*1024:
            size_str = f"{size/(1024*1024):.1f} MB"
        elif size > 1024:
            size_str = f"{size/1024:.1f} KB"
        
        # Try to read status from JSON
        try:
            with open(log_file, 'r') as f:
                data = json.load(f)
                status = data.get('status', 'unknown')
                method = data.get('method', 'Unknown')
                timestamp = data.get('timestamp', 'Unknown')
                
                status_emoji = "✅" if status == "success" else "❌" if status == "error" else "⏳"
                
                click.echo(f"  {status_emoji} {log_file.name}")
                click.echo(f"     📅 {timestamp} | 🤖 {method} | 📦 {size_str}")
                click.echo(f"     View: python src/view_logs.py {log_file}")
                click.echo()
        except:
            click.echo(f"  📄 {log_file.name} ({size_str})")
            click.echo(f"     View: python src/view_logs.py {log_file}")
            click.echo()
    
    click.echo("-"*80 + "\n")
    return 0


@click.group()
def cli():
    """MCP Pipeline Log Viewer - View Claude execution logs in a clean format"""
    pass


cli.add_command(view_log, name='view')
cli.add_command(list_logs, name='list')


if __name__ == '__main__':
    # If single argument provided, assume it's a log file to view
    if len(sys.argv) == 2 and not sys.argv[1].startswith('-'):
        arg_path = Path(sys.argv[1])
        if arg_path.exists() and arg_path.is_file():
            sys.exit(view_log.main([sys.argv[1]], standalone_mode=False) or 0)
    
    cli()
