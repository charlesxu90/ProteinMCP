#!/usr/bin/env python3
"""Test script to debug Claude Code CLI output"""

import subprocess
import sys

# Simple test prompt
test_prompt = "Say hello and then count to 3"

print("Testing Claude Code CLI output capture...")
print("=" * 60)

cmd = [
    "claude",
    "--model", "claude-sonnet-4-20250514",
    "-p", "-"
]

print(f"Command: {' '.join(cmd)}")
print(f"Prompt: {test_prompt}")
print("=" * 60)
print("Output:")
print()

process = subprocess.Popen(
    cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Send prompt
process.stdin.write(test_prompt)
process.stdin.close()

# Read and display output
line_count = 0
for line in process.stdout:
    line_count += 1
    print(f"Line {line_count}: {repr(line)}")
    sys.stdout.flush()

return_code = process.wait()
print()
print("=" * 60)
print(f"Return code: {return_code}")
print(f"Total lines read: {line_count}")
