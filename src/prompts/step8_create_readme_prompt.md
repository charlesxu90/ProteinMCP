# Step 8: Create Comprehensive README Documentation

## Role
You are an expert technical writer and documentation specialist. Your mission is to create a clear, comprehensive README.md file for the MCP project that enables users to quickly understand, install, and use the MCP tools.

## Input Parameters
- `src/server.py`: MCP server from Step 6
- `scripts/`: Clean scripts from Step 5
- `examples/data/`: Demo data for testing
- `configs/`: Configuration files
- `env/`: Conda environment
- `reports/`: All reports from previous steps (step3_use_cases.md, step5_scripts.md, step6_mcp_tools.md, step7_integration.md)

## Prerequisites

```bash
# Determine package manager (prefer mamba over conda)
if command -v mamba &> /dev/null; then
    PKG_MGR="mamba"
else
    PKG_MGR="conda"
fi
echo "Using package manager: $PKG_MGR"
```

## Tasks

### Task 1: Gather Information from Previous Steps

1. **Read Reports**
   - `reports/step3_use_cases.md` - Use case documentation
   - `reports/step3_environment.md` - Environment setup details
   - `reports/step5_scripts.md` - Script documentation
   - `reports/step6_mcp_tools.md` - MCP tool documentation
   - `reports/step7_integration.md` - Test results

2. **Analyze Directory Structure**
   - List all scripts in `scripts/`
   - List all MCP tools in `src/server.py`
   - Identify demo data in `examples/data/`
   - Identify config files in `configs/`

3. **Extract Key Information**
   - Tool names and descriptions
   - Required parameters for each tool
   - Example data file paths
   - Config file paths

### Task 2: Create README.md Structure

Create a comprehensive README.md with the following sections:

```markdown
# ${project_name} MCP

> ${brief_description}

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Local Usage (Scripts)](#local-usage-scripts)
- [MCP Server Installation](#mcp-server-installation)
- [Using with Claude Code](#using-with-claude-code)
- [Using with Gemini CLI](#using-with-gemini-cli)
- [Available Tools](#available-tools)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

${detailed_description_of_what_this_mcp_does}

### Features
- ${feature_1}
- ${feature_2}
- ${feature_3}

### Directory Structure
\`\`\`
./
├── README.md               # This file
├── env/                    # Conda environment
├── src/
│   └── server.py           # MCP server
├── scripts/
│   ├── ${script_1}.py      # ${description_1}
│   ├── ${script_2}.py      # ${description_2}
│   └── lib/                # Shared utilities
├── examples/
│   └── data/               # Demo data
├── configs/                # Configuration files
└── repo/                   # Original repository
\`\`\`

---

## Installation

### Prerequisites
- Conda or Mamba (mamba recommended for faster installation)
- Python 3.10+
- ${any_other_prerequisites}

### Create Environment
Please strictly following the information in `reports/step3_environment.md` to obtain the procedure to setup the environment. An example workflow is shown below.

\`\`\`bash
# Navigate to the MCP directory
cd ${mcp_directory}

# Create conda environment (use mamba if available)
mamba create -p ./env python=3.10 -y
# or: conda create -p ./env python=3.10 -y

# Activate environment
mamba activate ./env
# or: conda activate ./env
# Install Dependencies

pip install -r requirements.txt

# Install MCP dependencies
pip install fastmcp loguru --ignore-installed
\`\`\`

---

## Local Usage (Scripts)

You can use the scripts directly without MCP for local processing.

### Available Scripts

| Script | Description | Example |
|--------|-------------|---------|
| `scripts/${script_1}.py` | ${description_1} | See below |
| `scripts/${script_2}.py` | ${description_2} | See below |

### Script Examples

#### ${script_1_name}

\`\`\`bash
# Activate environment
mamba activate ./env

# Run script
python scripts/${script_1}.py \\
  --input examples/data/${example_input} \\
  --output results/${output_name} \\
  --config configs/${config_file}.json
\`\`\`

**Parameters:**
- `--input, -i`: ${input_description} (required)
- `--output, -o`: ${output_description} (default: results/)
- `--config, -c`: ${config_description} (optional)

#### ${script_2_name}

\`\`\`bash
python scripts/${script_2}.py \\
  --input examples/data/${example_input_2} \\
  --param1 ${value1}
\`\`\`

---

## MCP Server Installation

### Option 1: Using fastmcp (Recommended)

\`\`\`bash
# Install MCP server for Claude Code
fastmcp install src/server.py --name ${project_name}
\`\`\`

### Option 2: Manual Installation for Claude Code

\`\`\`bash
# Add MCP server to Claude Code
claude mcp add ${project_name} -- $(pwd)/env/bin/python $(pwd)/src/server.py

# Verify installation
claude mcp list
\`\`\`

### Option 3: Configure in settings.json

Add to `~/.claude/settings.json`:

\`\`\`json
{
  "mcpServers": {
    "${project_name}": {
      "command": "${mcp_directory}/env/bin/python",
      "args": ["${mcp_directory}/src/server.py"]
    }
  }
}
\`\`\`

---

## Using with Claude Code

After installing the MCP server, you can use it directly in Claude Code.

### Quick Start

\`\`\`bash
# Start Claude Code
claude
\`\`\`

### Example Prompts

#### Tool Discovery
\`\`\`
What tools are available from ${project_name}?
\`\`\`

#### Basic Usage
\`\`\`
Use ${tool_name} with input file @examples/data/${sample_file}
\`\`\`

#### With Configuration
\`\`\`
Run ${tool_name} on @examples/data/${sample_file} using config @configs/${config_file}.json
\`\`\`

#### Long-Running Tasks (Submit API)
\`\`\`
Submit ${long_task_name} for @examples/data/${large_file}
Then check the job status
\`\`\`

#### Batch Processing
\`\`\`
Process these files in batch:
- @examples/data/file1.${ext}
- @examples/data/file2.${ext}
- @examples/data/file3.${ext}
\`\`\`

### Using @ References

In Claude Code, use `@` to reference files and directories:

| Reference | Description |
|-----------|-------------|
| `@examples/data/sample.pdb` | Reference a specific file |
| `@configs/default.json` | Reference a config file |
| `@results/` | Reference output directory |

---

## Using with Gemini CLI

### Configuration

Add to `~/.gemini/settings.json`:

\`\`\`json
{
  "mcpServers": {
    "${project_name}": {
      "command": "${mcp_directory}/env/bin/python",
      "args": ["${mcp_directory}/src/server.py"]
    }
  }
}
\`\`\`

### Example Prompts

\`\`\`bash
# Start Gemini CLI
gemini

# Example prompts (same as Claude Code)
> What tools are available?
> Use ${tool_name} with file examples/data/${sample_file}
\`\`\`

---

## Available Tools

### Quick Operations (Sync API)

These tools return results immediately (< 10 minutes):

| Tool | Description | Parameters |
|------|-------------|------------|
| `${sync_tool_1}` | ${description_1} | `input_file`, `output_file`, ... |
| `${sync_tool_2}` | ${description_2} | `input_file`, `param1`, ... |

### Long-Running Tasks (Submit API)

These tools return a job_id for tracking (> 10 minutes):

| Tool | Description | Parameters |
|------|-------------|------------|
| `submit_${async_tool_1}` | ${description_1} | `input_file`, `job_name`, ... |
| `submit_${async_tool_2}` | ${description_2} | `input_files`, `batch_name`, ... |

### Job Management Tools

| Tool | Description |
|------|-------------|
| `get_job_status` | Check job progress |
| `get_job_result` | Get results when completed |
| `get_job_log` | View execution logs |
| `cancel_job` | Cancel running job |
| `list_jobs` | List all jobs |

---

## Examples

### Example 1: ${use_case_1_name}

**Goal:** ${use_case_1_goal}

**Using Script:**
\`\`\`bash
python scripts/${script_1}.py \\
  --input examples/data/${input_1} \\
  --output results/example1/
\`\`\`

**Using MCP (in Claude Code):**
\`\`\`
Use ${tool_1} to process @examples/data/${input_1} and save results to results/example1/
\`\`\`

**Expected Output:**
- ${output_description_1}

### Example 2: ${use_case_2_name}

**Goal:** ${use_case_2_goal}

**Using Script:**
\`\`\`bash
python scripts/${script_2}.py \\
  --input examples/data/${input_2} \\
  --config configs/${config_2}.json
\`\`\`

**Using MCP (in Claude Code):**
\`\`\`
Run ${tool_2} on @examples/data/${input_2} with config @configs/${config_2}.json
\`\`\`

### Example 3: Batch Processing

**Goal:** Process multiple files at once

**Using Script:**
\`\`\`bash
for f in examples/data/*.${ext}; do
  python scripts/${script_1}.py --input "$f" --output results/batch/
done
\`\`\`

**Using MCP (in Claude Code):**
\`\`\`
Submit batch processing for all ${ext} files in @examples/data/
\`\`\`

---

## Demo Data

The `examples/data/` directory contains sample data for testing:

| File | Description | Use With |
|------|-------------|----------|
| `${demo_file_1}` | ${demo_description_1} | ${tool_name_1} |
| `${demo_file_2}` | ${demo_description_2} | ${tool_name_2} |

---

## Configuration Files

The `configs/` directory contains configuration templates:

| Config | Description | Parameters |
|--------|-------------|------------|
| `${config_1}.json` | ${config_description_1} | ${param_list_1} |
| `${config_2}.json` | ${config_description_2} | ${param_list_2} |

### Config Example

\`\`\`json
{
  "param1": "value1",
  "param2": 10,
  "param3": true
}
\`\`\`

---

## Troubleshooting

### Environment Issues

**Problem:** Environment not found
\`\`\`bash
# Recreate environment
mamba create -p ./env python=3.10 -y
mamba activate ./env
pip install -r requirements.txt
\`\`\`

**Problem:** Import errors
\`\`\`bash
# Verify installation
python -c "from src.server import mcp"
\`\`\`

### MCP Issues

**Problem:** Server not found in Claude Code
\`\`\`bash
# Check MCP registration
claude mcp list

# Re-add if needed
claude mcp remove ${project_name}
claude mcp add ${project_name} -- $(pwd)/env/bin/python $(pwd)/src/server.py
\`\`\`

**Problem:** Tools not working
\`\`\`bash
# Test server directly
python -c "
from src.server import mcp
print(list(mcp.list_tools().keys()))
"
\`\`\`

### Job Issues

**Problem:** Job stuck in pending
\`\`\`bash
# Check job directory
ls -la jobs/

# View job log
cat jobs/<job_id>/job.log
\`\`\`

**Problem:** Job failed
\`\`\`
Use get_job_log with job_id "<job_id>" and tail 100 to see error details
\`\`\`

---

## Development

### Running Tests

\`\`\`bash
# Activate environment
mamba activate ./env

# Run tests
pytest tests/ -v
\`\`\`

### Starting Dev Server

\`\`\`bash
# Run MCP server in dev mode
fastmcp dev src/server.py
\`\`\`

---

## License

${license_info}

## Credits

Based on [${original_repo}](${original_repo_url})
```

### Task 3: Fill in Template with Actual Data

1. **Replace all placeholders** with actual values from reports and analysis
2. **List actual tools** from `src/server.py`
3. **List actual scripts** from `scripts/`
4. **List actual demo data** from `examples/data/`
5. **List actual configs** from `configs/`

### Task 4: Add Project-Specific Examples

For each major use case, create:
1. A complete script example with real file paths
2. A complete MCP prompt example with `@` references
3. Expected output description

### Task 5: Validate README

1. **Check all paths exist**
   ```bash
   # Verify referenced files exist
   ls -la scripts/*.py
   ls -la examples/data/
   ls -la configs/
   ```

2. **Test script examples**
   ```bash
   # Run at least one example to verify it works
   python scripts/<first_script>.py --help
   ```

3. **Verify MCP tool names**
   ```python
   from src.server import mcp
   print(list(mcp.list_tools().keys()))
   ```

## Expected Outputs

### 1. README.md (in MCP root directory)

A comprehensive README.md file with:
- Clear installation instructions
- Script usage examples with real paths
- MCP installation commands
- Claude Code/Gemini CLI usage with `@` references
- Troubleshooting section
- All placeholders replaced with actual values

### 2. Updated reports/readme_info.json

```json
{
  "project_name": "${project_name}",
  "description": "${description}",
  "tools": [
    {
      "name": "tool_name",
      "type": "sync|submit",
      "description": "...",
      "example_prompt": "..."
    }
  ],
  "scripts": [
    {
      "name": "script.py",
      "description": "...",
      "example_command": "..."
    }
  ],
  "demo_data": [
    {
      "file": "sample.pdb",
      "description": "...",
      "used_by": ["tool1", "script1"]
    }
  ],
  "configs": [
    {
      "file": "default.json",
      "description": "...",
      "parameters": {}
    }
  ]
}
```

## Success Criteria

- [ ] README.md created in MCP root directory
- [ ] All placeholder values replaced with actual data
- [ ] Installation section complete with exact commands
- [ ] Local script usage section with working examples
- [ ] MCP installation section with multiple options
- [ ] Claude Code section with `@` reference examples
- [ ] Gemini CLI section with configuration
- [ ] All available tools documented
- [ ] At least 3 complete examples (script + MCP)
- [ ] Demo data documented with descriptions
- [ ] Config files documented with parameters
- [ ] Troubleshooting section covers common issues
- [ ] All referenced file paths verified to exist

## Important Notes

- **Use `@` references** for file paths in Claude Code examples (e.g., `@examples/data/sample.pdb`)
- **Prefer mamba over conda** in all environment commands
- **Include both script and MCP examples** for each use case
- **Document sync vs submit tools** clearly with expected runtime
- **Test at least one example** to ensure it works before finalizing
