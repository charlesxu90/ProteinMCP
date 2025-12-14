# Step 6: Create MCP Server from Scripts

## Role
You are an expert MCP (Model Context Protocol) developer. Your mission is to convert the clean scripts from Step 5 (`scripts/` directory) into MCP tools and create a fully functional MCP server with support for both synchronous and asynchronous (submit) APIs.

## Input Parameters
- `scripts/`: Clean, self-contained scripts from Step 5
- `scripts/lib/`: Shared library functions (if exists)
- `configs/`: Configuration files from Step 5
- `reports/scripts.json`: Script documentation from Step 5
- `examples/data/`: Demo data for testing
- `env/`: Main conda environment

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

# Install MCP dependencies
pip install fastmcp loguru
```

## Design Principles

### API Types

1. **Synchronous API** - For fast operations (<10 minutes)
   - Direct function call, immediate response
   - Suitable for: quick predictions, data parsing, simple analysis

2. **Submit API** - For long-running tasks (>10 minutes) or batch processing
   - Submit job, get job_id, check status, retrieve results
   - Suitable for: structure prediction, large-scale analysis, batch processing

### When to Use Submit API
- Task takes more than 10 minutes
- Processing multiple inputs (batch mode)
- GPU-intensive computations
- Tasks that may need to be resumed

## Tasks

### Task 1: Analyze Scripts for API Design

For each script in `scripts/`:

1. **Determine API Type**
   ```
   scripts/use_case_1_predict.py
   ├── Estimated runtime: 30 min → Submit API
   ├── Batch support needed: Yes → Submit API with batch
   └── Main function: run_predict()
   
   scripts/use_case_2_analyze.py
   ├── Estimated runtime: 30 sec → Sync API
   ├── Batch support needed: No
   └── Main function: run_analyze()
   ```

2. **Map to MCP Tools**
   - `run_predict()` → `submit_predict()` + `get_predict_status()` + `get_predict_result()`
   - `run_analyze()` → `analyze()` (sync)

### Task 2: Create MCP Server Structure

```
src/
├── server.py              # Main MCP server entry point
├── tools/
│   ├── __init__.py
│   ├── sync_tools.py      # Synchronous tools
│   └── async_tools.py     # Submit/async tools
├── jobs/
│   ├── __init__.py
│   ├── manager.py         # Job queue management
│   └── store.py           # Job state persistence
└── utils.py               # Shared utilities
```

### Task 3: Implement Job Management System

```python
# src/jobs/manager.py
"""Job management for long-running tasks."""

import uuid
import json
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from loguru import logger

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobManager:
    """Manages asynchronous job execution."""
    
    def __init__(self, jobs_dir: Path = None):
        self.jobs_dir = jobs_dir or Path(__file__).parent.parent.parent / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self._running_jobs: Dict[str, subprocess.Popen] = {}
    
    def submit_job(
        self,
        script_path: str,
        args: Dict[str, Any],
        job_name: str = None
    ) -> Dict[str, Any]:
        """Submit a new job for background execution.
        
        Args:
            script_path: Path to the script to run
            args: Arguments to pass to the script
            job_name: Optional name for the job
        
        Returns:
            Dict with job_id and status
        """
        job_id = str(uuid.uuid4())[:8]
        job_dir = self.jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Save job metadata
        metadata = {
            "job_id": job_id,
            "job_name": job_name or f"job_{job_id}",
            "script": script_path,
            "args": args,
            "status": JobStatus.PENDING.value,
            "submitted_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None
        }
        
        self._save_metadata(job_id, metadata)
        
        # Start job in background
        self._start_job(job_id, script_path, args, job_dir)
        
        return {
            "status": "submitted",
            "job_id": job_id,
            "message": f"Job submitted. Use get_job_status('{job_id}') to check progress."
        }
    
    def _start_job(self, job_id: str, script_path: str, args: Dict, job_dir: Path):
        """Start job execution in background thread."""
        def run_job():
            metadata = self._load_metadata(job_id)
            metadata["status"] = JobStatus.RUNNING.value
            metadata["started_at"] = datetime.now().isoformat()
            self._save_metadata(job_id, metadata)
            
            try:
                # Build command
                cmd = ["python", script_path]
                for key, value in args.items():
                    if value is not None:
                        cmd.extend([f"--{key}", str(value)])
                
                # Set output paths
                output_file = job_dir / "output.json"
                cmd.extend(["--output", str(output_file)])
                
                # Run script
                log_file = job_dir / "job.log"
                with open(log_file, 'w') as log:
                    process = subprocess.Popen(
                        cmd,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        cwd=str(Path(script_path).parent.parent)
                    )
                    self._running_jobs[job_id] = process
                    process.wait()
                
                # Update status
                if process.returncode == 0:
                    metadata["status"] = JobStatus.COMPLETED.value
                else:
                    metadata["status"] = JobStatus.FAILED.value
                    metadata["error"] = f"Process exited with code {process.returncode}"
                
            except Exception as e:
                metadata["status"] = JobStatus.FAILED.value
                metadata["error"] = str(e)
                logger.error(f"Job {job_id} failed: {e}")
            
            finally:
                metadata["completed_at"] = datetime.now().isoformat()
                self._save_metadata(job_id, metadata)
                self._running_jobs.pop(job_id, None)
        
        thread = threading.Thread(target=run_job, daemon=True)
        thread.start()
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a submitted job."""
        metadata = self._load_metadata(job_id)
        if not metadata:
            return {"status": "error", "error": f"Job {job_id} not found"}
        
        result = {
            "job_id": job_id,
            "job_name": metadata.get("job_name"),
            "status": metadata["status"],
            "submitted_at": metadata.get("submitted_at"),
            "started_at": metadata.get("started_at"),
            "completed_at": metadata.get("completed_at")
        }
        
        if metadata["status"] == JobStatus.FAILED.value:
            result["error"] = metadata.get("error")
        
        return result
    
    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        """Get results of a completed job."""
        metadata = self._load_metadata(job_id)
        if not metadata:
            return {"status": "error", "error": f"Job {job_id} not found"}
        
        if metadata["status"] != JobStatus.COMPLETED.value:
            return {
                "status": "error",
                "error": f"Job not completed. Current status: {metadata['status']}"
            }
        
        # Load output
        job_dir = self.jobs_dir / job_id
        output_file = job_dir / "output.json"
        
        if output_file.exists():
            with open(output_file) as f:
                result = json.load(f)
            return {"status": "success", "result": result}
        else:
            return {"status": "error", "error": "Output file not found"}
    
    def get_job_log(self, job_id: str, tail: int = 50) -> Dict[str, Any]:
        """Get log output from a job."""
        job_dir = self.jobs_dir / job_id
        log_file = job_dir / "job.log"
        
        if not log_file.exists():
            return {"status": "error", "error": f"Log not found for job {job_id}"}
        
        with open(log_file) as f:
            lines = f.readlines()
        
        return {
            "status": "success",
            "job_id": job_id,
            "log_lines": lines[-tail:] if tail else lines,
            "total_lines": len(lines)
        }
    
    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a running job."""
        if job_id in self._running_jobs:
            self._running_jobs[job_id].terminate()
            metadata = self._load_metadata(job_id)
            metadata["status"] = JobStatus.CANCELLED.value
            metadata["completed_at"] = datetime.now().isoformat()
            self._save_metadata(job_id, metadata)
            return {"status": "success", "message": f"Job {job_id} cancelled"}
        
        return {"status": "error", "error": f"Job {job_id} not running"}
    
    def list_jobs(self, status: Optional[str] = None) -> Dict[str, Any]:
        """List all jobs, optionally filtered by status."""
        jobs = []
        for job_dir in self.jobs_dir.iterdir():
            if job_dir.is_dir():
                metadata = self._load_metadata(job_dir.name)
                if metadata:
                    if status is None or metadata["status"] == status:
                        jobs.append({
                            "job_id": metadata["job_id"],
                            "job_name": metadata.get("job_name"),
                            "status": metadata["status"],
                            "submitted_at": metadata.get("submitted_at")
                        })
        
        return {"status": "success", "jobs": jobs, "total": len(jobs)}
    
    def _save_metadata(self, job_id: str, metadata: Dict):
        """Save job metadata to disk."""
        meta_file = self.jobs_dir / job_id / "metadata.json"
        meta_file.parent.mkdir(parents=True, exist_ok=True)
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _load_metadata(self, job_id: str) -> Optional[Dict]:
        """Load job metadata from disk."""
        meta_file = self.jobs_dir / job_id / "metadata.json"
        if meta_file.exists():
            with open(meta_file) as f:
                return json.load(f)
        return None

# Global job manager instance
job_manager = JobManager()
```

### Task 4: Create MCP Server with Both API Types

```python
# src/server.py
"""MCP Server for ${repo_name}

Provides both synchronous and asynchronous (submit) APIs for all tools.
"""

from fastmcp import FastMCP
from pathlib import Path
from typing import Optional, List
import sys

# Setup paths
SCRIPT_DIR = Path(__file__).parent.resolve()
MCP_ROOT = SCRIPT_DIR.parent
SCRIPTS_DIR = MCP_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from jobs.manager import job_manager
from loguru import logger

# Create MCP server
mcp = FastMCP("${repo_name}")

# ==============================================================================
# Job Management Tools (for async operations)
# ==============================================================================

@mcp.tool()
def get_job_status(job_id: str) -> dict:
    """
    Get the status of a submitted job.
    
    Args:
        job_id: The job ID returned from a submit_* function
    
    Returns:
        Dictionary with job status, timestamps, and any errors
    """
    return job_manager.get_job_status(job_id)

@mcp.tool()
def get_job_result(job_id: str) -> dict:
    """
    Get the results of a completed job.
    
    Args:
        job_id: The job ID of a completed job
    
    Returns:
        Dictionary with the job results or error if not completed
    """
    return job_manager.get_job_result(job_id)

@mcp.tool()
def get_job_log(job_id: str, tail: int = 50) -> dict:
    """
    Get log output from a running or completed job.
    
    Args:
        job_id: The job ID to get logs for
        tail: Number of lines from end (default: 50, use 0 for all)
    
    Returns:
        Dictionary with log lines and total line count
    """
    return job_manager.get_job_log(job_id, tail)

@mcp.tool()
def cancel_job(job_id: str) -> dict:
    """
    Cancel a running job.
    
    Args:
        job_id: The job ID to cancel
    
    Returns:
        Success or error message
    """
    return job_manager.cancel_job(job_id)

@mcp.tool()
def list_jobs(status: Optional[str] = None) -> dict:
    """
    List all submitted jobs.
    
    Args:
        status: Filter by status (pending, running, completed, failed, cancelled)
    
    Returns:
        List of jobs with their status
    """
    return job_manager.list_jobs(status)

# ==============================================================================
# Synchronous Tools (for fast operations < 10 min)
# ==============================================================================

@mcp.tool()
def example_sync_tool(
    input_file: str,
    param1: str = "default",
    output_file: Optional[str] = None
) -> dict:
    """
    Example synchronous tool for fast operations.
    
    Use this pattern for operations that complete in under 10 minutes.
    
    Args:
        input_file: Path to input file
        param1: Example parameter
        output_file: Optional path to save output
    
    Returns:
        Dictionary with results
    """
    # Import the script's main function
    from use_case_sync import run_sync_operation
    
    try:
        result = run_sync_operation(
            input_file=input_file,
            param1=param1,
            output_file=output_file
        )
        return {"status": "success", **result}
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        return {"status": "error", "error": str(e)}

# ==============================================================================
# Submit Tools (for long-running operations > 10 min)
# ==============================================================================

@mcp.tool()
def submit_long_running_task(
    input_file: str,
    param1: str = "default",
    output_dir: Optional[str] = None,
    job_name: Optional[str] = None
) -> dict:
    """
    Submit a long-running task for background processing.
    
    This task may take more than 10 minutes. Use get_job_status() to monitor
    progress and get_job_result() to retrieve results when completed.
    
    Args:
        input_file: Path to input file
        param1: Example parameter
        output_dir: Directory to save outputs
        job_name: Optional name for the job (for easier tracking)
    
    Returns:
        Dictionary with job_id for tracking. Use:
        - get_job_status(job_id) to check progress
        - get_job_result(job_id) to get results when completed
        - get_job_log(job_id) to see execution logs
    """
    script_path = str(SCRIPTS_DIR / "use_case_long_running.py")
    
    return job_manager.submit_job(
        script_path=script_path,
        args={
            "input": input_file,
            "param1": param1,
            "output_dir": output_dir
        },
        job_name=job_name
    )

# ==============================================================================
# Batch Processing Tools
# ==============================================================================

@mcp.tool()
def submit_batch_processing(
    input_files: List[str],
    param1: str = "default",
    output_dir: Optional[str] = None,
    job_name: Optional[str] = None
) -> dict:
    """
    Submit batch processing for multiple input files.
    
    Processes multiple inputs in a single job. Suitable for:
    - Processing many sequences/structures at once
    - Large-scale analysis
    - Parallel processing of independent inputs
    
    Args:
        input_files: List of input file paths to process
        param1: Parameter applied to all inputs
        output_dir: Directory to save all outputs
        job_name: Optional name for the batch job
    
    Returns:
        Dictionary with job_id for tracking the batch job
    """
    script_path = str(SCRIPTS_DIR / "use_case_batch.py")
    
    # Convert list to comma-separated string for CLI
    inputs_str = ",".join(input_files)
    
    return job_manager.submit_job(
        script_path=script_path,
        args={
            "inputs": inputs_str,
            "param1": param1,
            "output_dir": output_dir
        },
        job_name=job_name or f"batch_{len(input_files)}_files"
    )

# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    mcp.run()
```

### Task 5: Wrap Each Script as MCP Tool

For each script in `scripts/`, create the appropriate MCP tool:

1. **For Fast Operations (Sync API)**
   ```python
   @mcp.tool()
   def <tool_name>(
       input_file: str,
       # ... other params from script's CLI args
       output_file: Optional[str] = None
   ) -> dict:
       """
       <Description from script docstring>
       
       Args:
           input_file: <description>
           output_file: Optional path to save output
       
       Returns:
           Dictionary with results and output_file path
       """
       from <script_module> import run_<function_name>
       
       try:
           result = run_<function_name>(
               input_file=input_file,
               output_file=output_file,
               # ... other params
           )
           return {"status": "success", **result}
       except FileNotFoundError as e:
           return {"status": "error", "error": f"File not found: {e}"}
       except ValueError as e:
           return {"status": "error", "error": f"Invalid input: {e}"}
       except Exception as e:
           logger.error(f"<tool_name> failed: {e}")
           return {"status": "error", "error": str(e)}
   ```

2. **For Long Operations (Submit API)**
   ```python
   @mcp.tool()
   def submit_<tool_name>(
       input_file: str,
       # ... other params
       output_dir: Optional[str] = None,
       job_name: Optional[str] = None
   ) -> dict:
       """
       Submit <task description> for background processing.
       
       This operation may take >10 minutes. Returns a job_id for tracking.
       
       Args:
           input_file: <description>
           output_dir: Directory for outputs
           job_name: Optional name for tracking
       
       Returns:
           Dictionary with job_id. Use:
           - get_job_status(job_id) to check progress
           - get_job_result(job_id) to get results
           - get_job_log(job_id) to see logs
       """
       script_path = str(SCRIPTS_DIR / "<script_name>.py")
       
       return job_manager.submit_job(
           script_path=script_path,
           args={
               "input": input_file,
               # ... map to script CLI args
           },
           job_name=job_name
       )
   ```

### Task 6: Test MCP Server

1. **Test Sync Tools**
   ```bash
   # Activate environment
   mamba activate ./env  # or: conda activate ./env
   
   # Start server in dev mode
   fastmcp dev src/server.py
   
   # In another terminal, test sync tool
   # (using MCP inspector or direct call)
   ```

2. **Test Submit API**
   ```python
   # tests/test_mcp.py
   import pytest
   import time
   from src.server import mcp
   
   def test_submit_and_check_job():
       """Test submit API workflow."""
       # Submit job
       submit_result = mcp.call_tool(
           "submit_long_running_task",
           {"input_file": "examples/data/sample.pdb", "param1": "test"}
       )
       assert submit_result["status"] == "submitted"
       job_id = submit_result["job_id"]
       
       # Check status
       status = mcp.call_tool("get_job_status", {"job_id": job_id})
       assert status["status"] in ["pending", "running", "completed"]
       
       # Wait for completion (with timeout)
       for _ in range(60):  # 60 second timeout for test
           status = mcp.call_tool("get_job_status", {"job_id": job_id})
           if status["status"] == "completed":
               break
           time.sleep(1)
       
       # Get result
       if status["status"] == "completed":
           result = mcp.call_tool("get_job_result", {"job_id": job_id})
           assert result["status"] == "success"
   
   def test_list_jobs():
       """Test job listing."""
       result = mcp.call_tool("list_jobs", {})
       assert result["status"] == "success"
       assert "jobs" in result
   ```

## Expected Outputs

### 1. MCP Server: `src/server.py`
Complete MCP server with:
- Job management tools (get_job_status, get_job_result, get_job_log, cancel_job, list_jobs)
- Sync tools for fast operations
- Submit tools for long-running tasks
- Batch processing support

### 2. Job Manager: `src/jobs/manager.py`
Job queue system for async operations.

### 3. Tool Documentation: `reports/mcp_tools.json`
```json
{
  "server_name": "${repo_name}",
  "version": "1.0.0",
  "created_date": "YYYY-MM-DD",
  "tools": {
    "job_management": [
      {"name": "get_job_status", "description": "Check job progress"},
      {"name": "get_job_result", "description": "Get completed job results"},
      {"name": "get_job_log", "description": "View job execution logs"},
      {"name": "cancel_job", "description": "Cancel running job"},
      {"name": "list_jobs", "description": "List all jobs"}
    ],
    "sync_tools": [
      {
        "name": "<tool_name>",
        "description": "<description>",
        "source_script": "scripts/<script>.py",
        "estimated_runtime": "<X seconds/minutes>",
        "parameters": [...]
      }
    ],
    "submit_tools": [
      {
        "name": "submit_<tool_name>",
        "description": "<description>",
        "source_script": "scripts/<script>.py",
        "estimated_runtime": ">10 minutes",
        "supports_batch": true,
        "parameters": [...]
      }
    ]
  }
}
```

### 4. Updated README.md
```markdown
# ${repo_name} MCP Server

MCP server providing tools for [description].

## Installation

\`\`\`bash
# Activate environment (prefer mamba over conda)
mamba activate ./env  # or: conda activate ./env

# Install dependencies
pip install fastmcp loguru
\`\`\`

## Usage

### With Claude Desktop
Add to Claude config:
\`\`\`json
{
  "mcpServers": {
    "${repo_name}": {
      "command": "mamba",
      "args": ["run", "-p", "./env", "python", "src/server.py"]
    }
  }
}
\`\`\`

### With fastmcp CLI
\`\`\`bash
fastmcp install claude-code src/server.py
\`\`\`

## Available Tools

### Quick Operations (Sync API)
These tools return results immediately:

| Tool | Description | Runtime |
|------|-------------|---------|
| `<tool_name>` | <description> | ~30 sec |

### Long-Running Tasks (Submit API)
These tools return a job_id for tracking:

| Tool | Description | Runtime |
|------|-------------|---------|
| `submit_<tool_name>` | <description> | >10 min |

### Job Management
| Tool | Description |
|------|-------------|
| `get_job_status` | Check job progress |
| `get_job_result` | Get results when completed |
| `get_job_log` | View execution logs |
| `cancel_job` | Cancel running job |
| `list_jobs` | List all jobs |

## Workflow Example

### Quick Analysis (Sync)
\`\`\`
Use the analyze_structure tool with input_file "examples/data/sample.pdb"
\`\`\`

### Long-Running Prediction (Async)
\`\`\`
1. Submit: Use submit_predict_structure with input_file "examples/data/sample.fasta"
   → Returns: {"job_id": "abc123", "status": "submitted"}

2. Check: Use get_job_status with job_id "abc123"
   → Returns: {"status": "running", ...}

3. Get result: Use get_job_result with job_id "abc123"
   → Returns: {"status": "success", "result": {...}}
\`\`\`

### Batch Processing
\`\`\`
Use submit_batch_processing with input_files ["file1.pdb", "file2.pdb", "file3.pdb"]
→ Processes all files in a single job
\`\`\`

## Development

\`\`\`bash
# Run tests
pytest tests/ -v

# Test server
fastmcp dev src/server.py

# Test with MCP inspector
npx @anthropic/mcp-inspector src/server.py
\`\`\`
```

## Success Criteria

- [ ] MCP server created at `src/server.py`
- [ ] Job manager implemented for async operations
- [ ] Sync tools created for fast operations (<10 min)
- [ ] Submit tools created for long-running operations (>10 min)
- [ ] Batch processing support for applicable tools
- [ ] Job management tools working (status, result, log, cancel, list)
- [ ] All tools have clear descriptions for LLM use
- [ ] Error handling returns structured responses
- [ ] Server starts without errors: `fastmcp dev src/server.py`
- [ ] README updated with all tools and usage examples

## Tool Classification Checklist

For each script in `scripts/`:
- [ ] Estimated runtime determined
- [ ] API type chosen (sync vs submit)
- [ ] Batch support evaluated
- [ ] MCP tool implemented
- [ ] Tool tested with example data
- [ ] Documentation added to reports/mcp_tools.json

## Important Notes

- **Prefer mamba over conda** for all environment operations
- **Sync API** for operations completing in <10 minutes
- **Submit API** for operations taking >10 minutes
- **Batch API** when processing multiple inputs is common
- **Job persistence** ensures jobs survive server restarts
- **Structured errors** help LLMs understand and recover from failures
