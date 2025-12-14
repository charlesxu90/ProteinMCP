# MCP Pipeline Logging

The MCP creation pipeline now uses a clean, Claude Code-style logging approach that shows concise progress in the terminal while saving full detailed logs to JSON files.

## Features

### Clean Terminal Output
- **Progress Spinner**: Shows animated spinner during processing
- **Progress Updates**: Displays key milestones (e.g., "Step 1/6", "Processing: 10/50")
- **Status Messages**: Clear success/failure indicators
- **Method Indicator**: Shows whether Claude Code CLI or API is being used

### Structured JSON Log Files
- All output is saved to `.json` files in `claude_outputs/` directory
- Each step gets its own log file (e.g., `step3_output.json`)
- Structured data includes:
  - Method used (CLI or API)
  - Timestamps
  - Progress events timeline
  - Full raw output
  - Status and return codes

## Example Output

```
🚀 Step 3: Setup conda environment & scan common use cases - START

  🤖 Using Claude Code CLI (logged-in account)
  ⠋ Processing with Claude...
  ⚙️  Step 1/6
  ⠙ Processing with Claude...
  ⚙️  Creating environment
  ⠹ Processing with Claude...
  ✅ Successfully completed using Claude Code CLI
  📄 Log saved to: claude_outputs/step3_output.json
  💡 View log: python src/view_logs.py claude_outputs/step3_output.json

✅ Step 3: Setup conda environment & scan common use cases - COMPLETE
```

## Viewing Logs

### Using the Log Viewer Script (Recommended)

The log viewer provides a clean, Claude Code-style display of the structured JSON logs:

```bash
# View log summary (default - shows metadata and progress timeline)
python src/view_logs.py claude_outputs/step3_output.json

# View with full output (not just preview)
python src/view_logs.py claude_outputs/step3_output.json --verbose

# View only progress events timeline
python src/view_logs.py claude_outputs/step3_output.json --progress

# View raw output only (no formatting)
python src/view_logs.py claude_outputs/step3_output.json --raw

# Search for specific text in output
python src/view_logs.py claude_outputs/step3_output.json --search "error"
python src/view_logs.py claude_outputs/step3_output.json --search "Step 1/6"

# View raw JSON structure
python src/view_logs.py claude_outputs/step3_output.json --json

# List all available logs with status
python src/view_logs.py list /path/to/mcp-project
```

### Example Log Viewer Output

```
================================================================================
📋 MCP Pipeline Execution Log
================================================================================

🤖 Method: Claude Code CLI
⚙️  Command: claude --model claude-sonnet-4-20250514 --verbose --output-format stream-json --dangerously-skip-permissions -p -
📁 Working Directory: /path/to/mcp-project
🕐 Timestamp: 2025-12-14 15:45:30
✅ Status: SUCCESS
🔢 Return Code: 0

📊 Progress Timeline (4 events):
--------------------------------------------------------------------------------
  [15:45:32] Step 1/6
  [15:45:45] Creating environment
  [15:46:12] Running setup
  [15:46:30] Complete

📝 Output Preview:
--------------------------------------------------------------------------------
[First 15 lines of output]
...
[Last 15 lines of output]

💡 Use --verbose to see full output

================================================================================
```

## JSON Log Structure

Each JSON log file includes:

```json
{
  "method": "Claude Code CLI",
  "command": "claude --model ...",
  "working_directory": "/path/to/project",
  "timestamp": "2025-12-14 15:45:30",
  "status": "success",
  "return_code": 0,
  "progress_events": [
    {
      "timestamp": "15:45:32",
      "message": "Step 1/6"
    }
  ],
  "raw_output": "Full output text..."
}
```

## Tips

1. **Terminal Output**: Focus on high-level progress and key milestones during execution
2. **Log Files**: Use the viewer to review execution details after completion
3. **Progress Timeline**: Use `--progress` to see just the key events
4. **Search**: Use `--search` to find specific content (errors, steps, etc.)
5. **Quick Preview**: Default view shows condensed output; use `--verbose` for full text
6. **List Logs**: Use `list` command to see all logs with their status at a glance

## Benefits

- **Less Terminal Noise**: Clean, focused progress display during execution
- **Better Focus**: See what matters in real-time, review details later
- **Structured Data**: JSON format enables easy parsing and analysis
- **Easy Review**: Claude Code-style viewer makes logs readable and navigable
- **Progress Timeline**: Track execution flow with timestamped events
- **Professional Look**: Clean, modern CLI experience similar to Claude Code
