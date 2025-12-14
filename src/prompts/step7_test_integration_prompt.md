# Step 7: Test MCP Integration with Claude Code & Gemini CLI

## Role
You are an expert in MCP (Model Context Protocol) integration testing. Your mission is to install, test, and validate the MCP server with Claude Code and Gemini CLI, ensuring all tools work correctly in real-world scenarios, and fix any issues discovered during testing.

## Input Parameters
- `src/server.py`: MCP server from Step 6
- `scripts/`: Clean scripts from Step 5
- `examples/data/`: Demo data for testing
- `env/`: Main conda environment
- `reports/step6_mcp_tools.md`: Tool documentation from Step 6

## Prerequisites

```bash
# Determine package manager (prefer mamba over conda)
if command -v mamba &> /dev/null; then
    PKG_MGR="mamba"
else
    PKG_MGR="conda"
fi
echo "Using package manager: $PKG_MGR"

# Activate environment
$PKG_MGR activate ./env

# Ensure fastmcp is installed
pip install fastmcp loguru

# For Gemini CLI testing (optional)
pip install google-generativeai
```

## Tasks

### Task 1: Pre-flight Server Validation

Before installing in any client, validate the server works standalone:

1. **Syntax Check**
   ```bash
   python -m py_compile src/server.py
   ```

2. **Import Test**
   ```bash
   python -c "from src.server import mcp; print('Server imports OK')"
   ```

3. **List Tools**
   ```bash
   python -c "
   from src.server import mcp
   tools = mcp.list_tools()
   print(f'Found {len(tools)} tools:')
   for name in tools:
       print(f'  - {name}')
   "
   ```

4. **Start Server in Dev Mode**
   ```bash
   # Test server starts without errors
   fastmcp dev src/server.py
   # Press Ctrl+C after verifying startup
   ```

### Task 2: Install in Claude Code

Claude Code (VS Code extension or CLI) uses MCP servers for tool calling.

1. **Register MCP Server**
   ```bash
   # Navigate to MCP directory (use absolute path)
   cd /absolute/path/to/mcp/directory
   
   # Add MCP server to Claude Code
   # Format: claude mcp add <name> -- <command> [args...]
   claude mcp add ${server_name} -- $(pwd)/env/bin/python $(pwd)/src/server.py
   
   # Or with full paths explicitly
   claude mcp add ${server_name} -- /path/to/mcp/env/bin/python /path/to/mcp/src/server.py
   ```

2. **Verify Installation**
   ```bash
   # List all registered MCP servers
   claude mcp list
   
   # Should show:
   # ${server_name}: /path/to/env/bin/python /path/to/src/server.py
   ```

3. **Check Server Configuration**
   ```bash
   # View the configuration file
   cat ~/.claude/settings.json | grep -A5 "${server_name}"
   ```

4. **Test Connection**
   ```bash
   # Start Claude Code and verify server connects
   claude
   
   # In Claude Code, check MCP servers are loaded
   # Look for tool icons or use /mcp command if available
   ```

### Task 3: Comprehensive Testing in Claude Code

Run a series of tests to validate all tool categories work correctly.

#### 3.1 Test Sync Tools (Fast Operations)

For each sync tool, test with demo data:

```
Test Prompt 1: Basic Tool Discovery
"What tools are available from ${server_name}? List them with their descriptions."

Test Prompt 2: Sync Tool Execution
"Use the <sync_tool_name> tool with input file examples/data/<sample_file> and show me the results."

Test Prompt 3: Parameter Validation
"Run <sync_tool_name> with these parameters: <param1>=<value1>, <param2>=<value2>"

Test Prompt 4: Error Handling
"Try to run <sync_tool_name> with an invalid file path '/nonexistent/file.pdb'"
```

**Expected Behavior:**
- Tool executes within seconds
- Results returned in structured format
- Clear error messages for invalid inputs
- Output file paths are valid and accessible

#### 3.2 Test Submit API (Long-Running Tasks)

Test the job submission and tracking workflow:

```
Test Prompt 1: Submit Job
"Submit a long-running task using submit_<task_name> with input file examples/data/<sample_file>"

Expected Response:
{
  "status": "submitted",
  "job_id": "abc12345",
  "message": "Job submitted. Use get_job_status('abc12345') to check progress."
}

Test Prompt 2: Check Status
"Check the status of job abc12345"

Expected Response:
{
  "job_id": "abc12345",
  "status": "running|completed|failed",
  "submitted_at": "2024-01-01T12:00:00",
  ...
}

Test Prompt 3: Get Results
"Get the results for completed job abc12345"

Expected Response:
{
  "status": "success",
  "result": { ... actual results ... }
}

Test Prompt 4: View Logs
"Show me the last 20 lines of logs for job abc12345"

Test Prompt 5: List All Jobs
"List all submitted jobs and their current status"

Test Prompt 6: Cancel Job (if applicable)
"Cancel the running job xyz98765"
```

#### 3.3 Test Batch Processing

Test batch operations with multiple inputs:

```
Test Prompt 1: Batch Submit
"Process these files in batch: examples/data/file1.pdb, examples/data/file2.pdb, examples/data/file3.pdb"

Test Prompt 2: Batch Status
"Check the status of batch job <batch_job_id>"

Test Prompt 3: Batch Results
"Get all results from the batch processing job <batch_job_id>"
```

#### 3.4 Test Real-World Scenarios

Design practical scenarios that mimic actual usage:

**Scenario 1: End-to-End Pipeline**
```
"I have a protein structure in examples/data/sample.pdb. 
First, analyze its properties, then predict stability changes for mutation A100G, 
and finally visualize the results."
```

**Scenario 2: Iterative Analysis**
```
"Load the sequence from examples/data/sample.fasta, 
predict its structure, 
then analyze the predicted structure for binding sites."
```

**Scenario 3: Comparison Task**
```
"Compare the structures examples/data/wild_type.pdb and examples/data/mutant.pdb 
and summarize the key differences."
```

**Scenario 4: Long-Running with Progress**
```
"Submit a structure prediction for the sequence in examples/data/long_sequence.fasta.
While it's running, check the progress every minute until it completes,
then show me the final results."
```

### Task 4: Install and Test with Gemini CLI

Gemini CLI can use MCP servers through the mcp-server configuration.

1. **Install Gemini CLI** (if not already installed)
   ```bash
   # Using npm
   npm install -g @anthropic-ai/gemini-cli
   
   # Or using pipx
   pipx install gemini-cli
   ```

2. **Configure MCP Server for Gemini**
   
   Create or update `~/.gemini/settings.json`:
   ```json
   {
     "mcpServers": {
       "${server_name}": {
         "command": "/absolute/path/to/mcp/env/bin/python",
         "args": ["/absolute/path/to/mcp/src/server.py"],
         "env": {
           "PYTHONPATH": "/absolute/path/to/mcp"
         }
       }
     }
   }
   ```

3. **Start Gemini CLI and Test**
   ```bash
   gemini
   
   # Test tool discovery
   > What tools do you have access to?
   
   # Test tool execution
   > Use ${server_name} to analyze the file examples/data/sample.pdb
   ```

4. **Run Same Test Suite as Claude Code**
   - Repeat sync tool tests
   - Repeat submit API tests
   - Repeat batch processing tests
   - Repeat real-world scenarios

### Task 5: Systematic Bug Fixing

When issues are discovered, follow this debugging workflow:

#### 5.1 Common Issues and Solutions

**Issue 1: Server Won't Start**
```bash
# Check for syntax errors
python -m py_compile src/server.py

# Check for import errors
python -c "from src.server import mcp" 2>&1

# Check for missing dependencies
pip list | grep -E "fastmcp|loguru"
```

**Issue 2: Tool Not Found**
```bash
# Verify tool is registered
python -c "
from src.server import mcp
print(mcp.list_tools().keys())
"

# Check tool decorator
grep -n "@mcp.tool" src/server.py
```

**Issue 3: Path Resolution Errors**
```python
# Fix: Use absolute paths in server.py
from pathlib import Path
MCP_ROOT = Path(__file__).parent.parent.resolve()
SCRIPTS_DIR = MCP_ROOT / "scripts"
# Pass absolute paths to functions
input_path = Path(input_file).resolve()
```

**Issue 4: Environment/Import Errors**
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/path/to/mcp:$PYTHONPATH

# Or add to server.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
```

**Issue 5: Job Status Not Updating**
```python
# Check job directory exists
ls -la jobs/

# Check metadata file
cat jobs/<job_id>/metadata.json

# Check log file for errors
tail -50 jobs/<job_id>/job.log
```

**Issue 6: Timeout on Long Operations**
- Ensure long operations use submit API (>10 min)
- Add proper timeout handling in scripts
- Use background threads correctly in JobManager

#### 5.2 Debugging Commands

```bash
# Watch server logs in real-time
tail -f logs/mcp_server.log

# Test specific tool directly
python -c "
from src.server import mcp
result = mcp.call_tool('tool_name', {'param1': 'value1'})
print(result)
"

# Check job queue
python -c "
from src.jobs.manager import job_manager
print(job_manager.list_jobs())
"
```

#### 5.3 Apply Fixes

After identifying issues:

1. **Update server.py** with fixes
2. **Re-validate** with pre-flight checks
3. **Restart Claude Code/Gemini CLI** to reload server
4. **Re-run failing tests** to confirm fix
5. **Document the fix** in reports/step7_integration.md

### Task 6: Create Test Report and Documentation

#### 6.1 Generate Test Report

Create a comprehensive test report:

```bash
# Create tests directory if not exists
mkdir -p tests reports
```

```python
# tests/run_integration_tests.py
"""Automated integration test runner for MCP server."""

import json
import subprocess
from datetime import datetime
from pathlib import Path

class MCPTestRunner:
    def __init__(self, server_path: str):
        self.server_path = Path(server_path)
        self.results = {
            "test_date": datetime.now().isoformat(),
            "server_path": str(server_path),
            "tests": {},
            "issues": [],
            "summary": {}
        }
    
    def test_server_startup(self) -> bool:
        """Test that server starts without errors."""
        try:
            result = subprocess.run(
                ["python", "-c", f"from src.server import mcp; print(len(mcp.list_tools()))"],
                capture_output=True, text=True, timeout=30
            )
            success = result.returncode == 0
            self.results["tests"]["server_startup"] = {
                "status": "passed" if success else "failed",
                "output": result.stdout,
                "error": result.stderr
            }
            return success
        except Exception as e:
            self.results["tests"]["server_startup"] = {"status": "error", "error": str(e)}
            return False
    
    def test_tool_listing(self) -> bool:
        """Test that all expected tools are available."""
        # Implementation...
        pass
    
    def test_sync_tool(self, tool_name: str, params: dict) -> bool:
        """Test a synchronous tool."""
        # Implementation...
        pass
    
    def test_submit_workflow(self, tool_name: str, params: dict) -> bool:
        """Test submit -> status -> result workflow."""
        # Implementation...
        pass
    
    def generate_report(self) -> str:
        """Generate JSON report."""
        total = len(self.results["tests"])
        passed = sum(1 for t in self.results["tests"].values() if t.get("status") == "passed")
        self.results["summary"] = {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "N/A"
        }
        return json.dumps(self.results, indent=2)

if __name__ == "__main__":
    runner = MCPTestRunner("src/server.py")
    runner.test_server_startup()
    # Add more tests...
    
    report = runner.generate_report()
    Path("reports/step7_integration.md").write_text(report)
    print(report)
```

#### 6.2 Create Practical Test Prompts File

```markdown
# tests/test_prompts.md

## Tool Discovery Tests

### Prompt 1: List All Tools
"What MCP tools are available? Give me a brief description of each."

### Prompt 2: Tool Details
"Explain how to use the <tool_name> tool, including all parameters."

## Sync Tool Tests

### Prompt 3: Basic Execution
"Use <tool_name> with input_file='examples/data/sample.pdb'"

### Prompt 4: With Custom Parameters
"Run <tool_name> on examples/data/sample.pdb with param1='value1' and save output to results/output.json"

### Prompt 5: Error Handling
"Try running <tool_name> with a non-existent file '/fake/path.pdb'"

## Submit API Tests

### Prompt 6: Submit Long Task
"Submit a <long_task_name> job for examples/data/sample.fasta"

### Prompt 7: Check Job Status
"What's the status of job <job_id>?"

### Prompt 8: Get Results
"Show me the results of job <job_id>"

### Prompt 9: View Logs
"Show the last 30 lines of logs for job <job_id>"

### Prompt 10: List Jobs
"List all jobs with status 'completed'"

## Batch Processing Tests

### Prompt 11: Batch Submit
"Process multiple files in batch: examples/data/file1.pdb, examples/data/file2.pdb"

### Prompt 12: Batch Results
"Get all results from batch job <batch_job_id>"

## End-to-End Scenarios

### Prompt 13: Full Workflow
"Analyze the protein in examples/data/sample.pdb:
1. First check its basic properties
2. Then predict stability
3. Finally summarize the results"

### Prompt 14: Conditional Processing
"If the structure in examples/data/sample.pdb has more than 500 residues, 
submit it for batch processing. Otherwise, analyze it directly."

### Prompt 15: Error Recovery
"Submit a structure prediction job. If it fails, show me the error log 
and suggest what might be wrong."
```

### Task 7: Final Validation Checklist

Before marking step complete, verify:

#### Server Validation
- [ ] Server starts without errors: `python -c "from src.server import mcp"`
- [ ] All tools listed: `mcp.list_tools()` returns expected tools
- [ ] Dev mode works: `fastmcp dev src/server.py`

#### Claude Code Integration
- [ ] Server registered: `claude mcp list` shows server
- [ ] Tools discoverable: LLM can list available tools
- [ ] Sync tools work: Execute and return results < 1 min
- [ ] Submit API works: Submit → Status → Result workflow
- [ ] Job management works: list_jobs, cancel_job, get_job_log
- [ ] Batch processing works: Multiple inputs in single job
- [ ] Error handling: Invalid inputs return helpful errors
- [ ] Path resolution: Relative and absolute paths work

#### Gemini CLI Integration (if applicable)
- [ ] Server configured in settings.json
- [ ] Tools discoverable
- [ ] Same functionality as Claude Code

#### Documentation
- [ ] Test prompts documented in tests/test_prompts.md
- [ ] Test results saved in reports/step7_integration.md
- [ ] Known issues documented with workarounds
- [ ] README updated with installation instructions

## Expected Outputs

### 1. Test Results: `reports/step7_integration.md`
```markdown
# Step 7: Integration Test Results

## Test Information
- **Test Date**: YYYY-MM-DD
- **Server Name**: ${server_name}
- **Server Path**: `src/server.py`
- **Environment**: `./env`

## Test Results Summary

| Test Category | Status | Notes |
|---------------|--------|-------|
| Server Startup | ✅ Passed | Found 12 tools, startup time 0.5s |
| Claude Code Installation | ✅ Passed | Verified with `claude mcp list` |
| Sync Tools | ✅ Passed | All 3 tools respond < 30s |
| Submit API | ✅ Passed | Full workflow works |
| Batch Processing | ✅ Passed | Processed 3 files |
| Error Handling | ✅ Passed | All error cases handled |
| Gemini CLI | ⏭️ Skipped | Optional |

## Detailed Results

### Server Startup
- **Status**: ✅ Passed
- **Tools Found**: 12
- **Startup Time**: 0.5s

### Claude Code Installation
- **Status**: ✅ Passed
- **Method**: `claude mcp add`
- **Verification**: `claude mcp list` shows server

### Sync Tools
- **Status**: ✅ Passed
- **Tools Tested**: tool1, tool2, tool3
- **All Passed**: ✅ Yes
- **Notes**: All sync tools respond within 30 seconds

### Submit API
- **Status**: ✅ Passed
- **Workflow Tested**: submit → status → result → log → cancel
- **Notes**: Full workflow completes correctly

### Batch Processing
- **Status**: ✅ Passed
- **Files Tested**: 3
- **Notes**: Batch job processes all files

### Error Handling
- **Status**: ✅ Passed
- **Scenarios Tested**: invalid_path, invalid_params, missing_required
- **Notes**: All errors return structured messages

### Gemini CLI
- **Status**: ⏭️ Skipped
- **Notes**: Optional - requires Gemini CLI setup

---

## Issues Found & Fixed

### Issue #001: Path Resolution
- **Description**: Path not resolved correctly for relative inputs
- **Severity**: Medium
- **Fix Applied**: Added `Path().resolve()` in tool functions
- **File Modified**: `src/server.py`
- **Verified**: ✅ Yes

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 7 |
| Passed | 7 |
| Failed | 0 |
| Pass Rate | 100% |
| Ready for Production | ✅ Yes |
```

### 2. Test Prompts: `tests/test_prompts.md`
Comprehensive list of test prompts for manual testing.

### 3. Integration Test Script: `tests/run_integration_tests.py`
Automated test runner for CI/CD.

### 4. Updated README.md
Add installation and usage section:

```markdown
## Installation

### Claude Code (Recommended)

```bash
# Navigate to MCP directory
cd /path/to/mcp/directory

# Add MCP server
claude mcp add ${server_name} -- $(pwd)/env/bin/python $(pwd)/src/server.py

# Verify
claude mcp list
```

### Gemini CLI

Add to `~/.gemini/settings.json`:
```json
{
  "mcpServers": {
    "${server_name}": {
      "command": "/path/to/mcp/env/bin/python",
      "args": ["/path/to/mcp/src/server.py"]
    }
  }
}
```

## Quick Start Examples

### In Claude Code:
```
# List available tools
"What tools do you have from ${server_name}?"

# Run a quick analysis
"Analyze the protein in examples/data/sample.pdb"

# Submit a long-running job
"Submit structure prediction for examples/data/sequence.fasta"

# Check job status
"Check status of job abc123"
```

## Troubleshooting

### Server won't start
```bash
# Check Python environment
which python
python --version

# Verify imports
python -c "from src.server import mcp"
```

### Tools not found
```bash
# List available tools
python -c "from src.server import mcp; print(list(mcp.list_tools().keys()))"
```

### Jobs stuck in pending
```bash
# Check job directory
ls -la jobs/

# View job log
cat jobs/<job_id>/job.log
```
```

## Success Criteria

- [ ] Server passes all pre-flight validation checks
- [ ] Successfully registered in Claude Code (`claude mcp list`)
- [ ] All sync tools execute and return results correctly
- [ ] Submit API workflow (submit → status → result) works end-to-end
- [ ] Job management tools work (list, cancel, get_log)
- [ ] Batch processing handles multiple inputs
- [ ] Error handling returns structured, helpful messages
- [ ] Test report generated with all results
- [ ] Documentation updated with installation instructions
- [ ] At least 3 real-world scenarios tested successfully
- [ ] (Optional) Gemini CLI integration verified

## Quick Reference Commands

```bash
# Pre-flight validation
python -c "from src.server import mcp; print(f'Found {len(mcp.list_tools())} tools')"

# Claude Code installation
claude mcp add ${server_name} -- $(pwd)/env/bin/python $(pwd)/src/server.py
claude mcp list
claude mcp remove ${server_name}  # if needed to re-add

# Start dev server for debugging
fastmcp dev src/server.py

# Check job status directly
python -c "from src.jobs.manager import job_manager; print(job_manager.list_jobs())"

# View recent job logs
tail -50 jobs/*/job.log
```
