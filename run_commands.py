#!/usr/bin/env python3
"""
Script to run pmcp create commands one-by-one with session limit handling.
Parses commands from run_claude.sh and retries on rate limits.
"""

import subprocess
import re
import time
import sys
from pathlib import Path


def parse_commands_from_script(script_path: str | Path) -> list[str]:
    """Parse non-commented commands from the shell script."""
    commands = []
    with open(script_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            # Only include pmcp create commands
            if line.startswith('pmcp create') or line.startswith('python src/create_mcp.py'):
                commands.append(line)
    return commands


def extract_wait_time(output: str) -> int | None:
    """
    Extract wait time from claude's rate limit message.
    Common patterns:
    - "Please wait X seconds"
    - "Try again in X seconds"
    - "Rate limit... retry after X seconds"
    - "wait X minutes"
    """
    # Try to find seconds
    patterns = [
        r'wait\s+(\d+)\s*seconds?',
        r'try again in\s+(\d+)\s*seconds?',
        r'retry after\s+(\d+)\s*seconds?',
        r'(\d+)\s*seconds?\s*(?:remaining|left)',
        r'rate.?limit.*?(\d+)\s*seconds?',
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return int(match.group(1))

    # Try to find minutes
    minute_patterns = [
        r'wait\s+(\d+)\s*minutes?',
        r'try again in\s+(\d+)\s*minutes?',
        r'(\d+)\s*minutes?\s*(?:remaining|left)',
    ]

    for pattern in minute_patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return int(match.group(1)) * 60

    return None


def is_rate_limited(output: str) -> bool:
    """Check if the output indicates a rate limit."""
    rate_limit_indicators = [
        'rate limit',
        'session limit',
        'too many requests',
        'quota exceeded',
        'try again',
        'please wait',
        'throttl',
    ]
    output_lower = output.lower()
    return any(indicator in output_lower for indicator in rate_limit_indicators)


def run_command(command: str, max_retries: int = 10, default_wait: int = 60) -> bool:
    """
    Run a command with retry logic for rate limits.
    Streams output in real-time while also capturing for rate limit detection.

    Args:
        command: The command to run
        max_retries: Maximum number of retries on rate limit
        default_wait: Default wait time in seconds if not specified in error

    Returns:
        True if command succeeded, False otherwise
    """
    for attempt in range(max_retries + 1):
        print(f"\n{'='*60}")
        print(f"Running command (attempt {attempt + 1}/{max_retries + 1}):")
        print(f"  {command[:100]}{'...' if len(command) > 100 else ''}")
        print('='*60)
        sys.stdout.flush()

        try:
            # Use Popen for real-time output streaming
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                text=True,
                bufsize=1,  # Line buffered
            )

            # Collect output while streaming
            collected_output = []

            # Stream output line by line in real-time
            for line in process.stdout:
                print(line, end='', flush=True)
                collected_output.append(line)

            # Wait for process to complete
            return_code = process.wait()
            combined_output = ''.join(collected_output)

            # Check for rate limiting
            if is_rate_limited(combined_output):
                wait_time = extract_wait_time(combined_output)
                if wait_time is None:
                    wait_time = default_wait
                    print(f"\n⚠️  Rate limit detected but couldn't parse wait time. Using default: {wait_time}s")
                else:
                    print(f"\n⚠️  Rate limit detected. Waiting {wait_time} seconds...")

                # Add a small buffer to the wait time
                wait_time = wait_time + 5

                if attempt < max_retries:
                    print(f"💤 Sleeping for {wait_time} seconds before retry...")
                    sys.stdout.flush()
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Max retries ({max_retries}) reached. Moving to next command.")
                    return False

            # Command succeeded or failed without rate limit
            if return_code == 0:
                print("\n✅ Command completed successfully!")
                return True
            else:
                print(f"\n❌ Command failed with return code: {return_code}")
                return False

        except subprocess.TimeoutExpired:
            print("\n❌ Command timed out after 1 hour")
            process.kill()
            return False
        except Exception as e:
            print(f"\n❌ Error running command: {e}")
            return False

    return False


def main():
    script_path = Path(__file__).parent / "run_claude.sh"

    if not script_path.exists():
        print(f"Error: {script_path} not found")
        sys.exit(1)

    commands = parse_commands_from_script(script_path)

    if not commands:
        print("No commands found in run_claude.sh")
        sys.exit(1)

    print(f"Found {len(commands)} commands to run:")
    for i, cmd in enumerate(commands, 1):
        print(f"  {i}. {cmd[:80]}{'...' if len(cmd) > 80 else ''}")

    print("\n" + "="*60)
    print("Starting execution...")
    print("="*60)

    results = []
    for i, command in enumerate(commands, 1):
        print(f"\n\n{'#'*60}")
        print(f"# Command {i}/{len(commands)}")
        print(f"{'#'*60}")

        success = run_command(command)
        results.append((command, success))

        # Small delay between commands to be nice
        if i < len(commands):
            print("\nWaiting 5 seconds before next command...")
            time.sleep(5)

    # Summary
    print("\n\n" + "="*60)
    print("EXECUTION SUMMARY")
    print("="*60)

    successful = sum(1 for _, success in results if success)
    failed = len(results) - successful

    print(f"\nTotal commands: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if failed > 0:
        print("\nFailed commands:")
        for cmd, success in results:
            if not success:
                print(f"  - {cmd[:80]}...")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
