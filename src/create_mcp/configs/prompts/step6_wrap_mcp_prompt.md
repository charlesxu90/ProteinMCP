# Step 6: Extract MCP Tools & Wrap in MCP Server (Test and Bugfix)

## Role
You are an expert MCP (Model Context Protocol) developer. Your mission is to convert the tested Python functions from Step 5 into MCP tools and create a fully functional MCP server.

## Input Parameters
- `repo_name`: ${repo_name}
- `src/`: Function library from Step 5
- `reports/functions.json`: Function documentation from Step 5
- `env/${repo_name}-env`: Conda environment

## Prerequisites
```bash
conda activate ./env/${repo_name}-env
pip install fastmcp loguru
```

## Tasks

### Task 1: Design MCP Tools

1. **Review Functions for MCP Suitability**
   - Functions should be stateless
   - Inputs should be serializable (strings, numbers, lists, dicts)
   - Outputs should be JSON-serializable
   - File paths should be handled carefully

2. **Map Functions to MCP Tools**
   For each function, design the MCP tool interface:
   - Tool name (snake_case, descriptive)
   - Description (clear, concise)
   - Input parameters with types and descriptions
   - Return value format

### Task 2: Create MCP Server

1. **Server Structure**
   ```python
   # src/${repo_name}_mcp.py
   
   from fastmcp import FastMCP
   from pathlib import Path
   import sys
   
   # Add source to path
   SCRIPT_DIR = Path(__file__).parent.resolve()
   sys.path.insert(0, str(SCRIPT_DIR))
   
   # Import your functions
   from functions.prediction import predict_structure
   from functions.analysis import analyze_results
   
   # Create MCP server
   mcp = FastMCP("${repo_name}")
   
   @mcp.tool()
   def tool_name(
       param1: str,
       param2: int = 10
   ) -> dict:
       """
       Tool description that will be shown to the LLM.
       
       Args:
           param1: Description of param1
           param2: Description of param2 (default: 10)
       
       Returns:
           Dictionary with results
       """
       result = your_function(param1, param2)
       return result
   ```

2. **Tool Implementation Pattern**
   ```python
   from fastmcp import FastMCP
   from pathlib import Path
   from typing import Optional
   from loguru import logger
   
   mcp = FastMCP("${repo_name}")
   
   @mcp.tool()
   def predict_protein_structure(
       sequence: str,
       output_dir: Optional[str] = None,
       model: str = "default"
   ) -> dict:
       """
       Predict 3D structure of a protein from its amino acid sequence.
       
       Args:
           sequence: Amino acid sequence (single letter codes, e.g., "MKFLILF...")
           output_dir: Directory to save output PDB file (optional)
           model: Model to use for prediction (default, fast, accurate)
       
       Returns:
           Dictionary containing:
               - pdb_content: PDB file content as string
               - output_file: Path to saved PDB file (if output_dir provided)
               - confidence: Prediction confidence score
               - metadata: Additional prediction information
       """
       from functions.prediction import predict_structure
       
       try:
           result = predict_structure(
               sequence=sequence,
               output_dir=Path(output_dir) if output_dir else None,
               model=model
           )
           return {
               "status": "success",
               "pdb_content": result.get("pdb_content"),
               "output_file": str(result.get("output_file")) if result.get("output_file") else None,
               "confidence": result.get("confidence"),
               "metadata": result.get("metadata", {})
           }
       except FileNotFoundError as e:
           return {"status": "error", "error": f"File not found: {e}"}
       except ValueError as e:
           return {"status": "error", "error": f"Invalid input: {e}"}
       except Exception as e:
           logger.error(f"Prediction failed: {e}")
           return {"status": "error", "error": str(e)}
   ```

### Task 3: Handle File Operations

MCP tools need special handling for files:

1. **File Input Options**
   ```python
   @mcp.tool()
   def analyze_structure(
       pdb_file: Optional[str] = None,
       pdb_content: Optional[str] = None
   ) -> dict:
       """
       Analyze protein structure.
       
       Provide either pdb_file (path) OR pdb_content (PDB text).
       
       Args:
           pdb_file: Path to PDB file on disk
           pdb_content: PDB file content as string
       """
       if pdb_file:
           content = Path(pdb_file).read_text()
       elif pdb_content:
           content = pdb_content
       else:
           return {"status": "error", "error": "Provide pdb_file or pdb_content"}
       
       # Process content...
   ```

2. **File Output Options**
   ```python
   @mcp.tool()
   def generate_report(
       data: dict,
       output_file: Optional[str] = None
   ) -> dict:
       """
       Generate analysis report.
       
       Args:
           data: Input data dictionary
           output_file: Optional path to save report
       
       Returns:
           Report content (and saves to file if output_file provided)
       """
       report = create_report(data)
       
       result = {"status": "success", "report": report}
       
       if output_file:
           Path(output_file).write_text(report)
           result["output_file"] = output_file
       
       return result
   ```

### Task 4: Test MCP Server

1. **Unit Test Tools**
   ```python
   # tests/test_mcp.py
   import pytest
   from src.${repo_name}_mcp import mcp
   
   def test_predict_protein_structure():
       """Test the predict_protein_structure tool."""
       result = mcp.call_tool(
           "predict_protein_structure",
           {"sequence": "MKFLILF", "model": "fast"}
       )
       assert result["status"] == "success"
       assert "pdb_content" in result
   
   def test_predict_invalid_sequence():
       """Test error handling for invalid sequence."""
       result = mcp.call_tool(
           "predict_protein_structure",
           {"sequence": "INVALID123"}
       )
       assert result["status"] == "error"
   ```

2. **Interactive Testing**
   ```bash
   # Test server startup
   fastmcp dev src/${repo_name}_mcp.py
   
   # In another terminal, test with MCP inspector
   npx @anthropic/mcp-inspector src/${repo_name}_mcp.py
   ```

3. **Integration Test**
   ```python
   # Test full workflow
   def test_full_workflow(tmp_path):
       """Test complete analysis workflow."""
       # Step 1: Predict structure
       pred_result = mcp.call_tool(
           "predict_protein_structure",
           {"sequence": "MKFLILF...", "output_dir": str(tmp_path)}
       )
       assert pred_result["status"] == "success"
       
       # Step 2: Analyze structure
       analysis_result = mcp.call_tool(
           "analyze_structure",
           {"pdb_file": pred_result["output_file"]}
       )
       assert analysis_result["status"] == "success"
   ```

## Expected Outputs

### 1. MCP Server: `src/${repo_name}_mcp.py`

Complete MCP server with all tools implemented.

### 2. Updated Tests: `tests/test_mcp.py`

Tests for all MCP tools.

### 3. Tool Documentation: `reports/mcp_tools.json`
```json
{
  "server_name": "${repo_name}",
  "version": "1.0.0",
  "created_date": "YYYY-MM-DD",
  "tools": [
    {
      "name": "predict_protein_structure",
      "description": "Predict 3D structure of a protein from sequence",
      "parameters": [
        {"name": "sequence", "type": "string", "required": true},
        {"name": "output_dir", "type": "string", "required": false},
        {"name": "model", "type": "string", "required": false, "default": "default"}
      ],
      "returns": "Dictionary with pdb_content, output_file, confidence",
      "source_function": "src.functions.prediction.predict_structure",
      "tested": true
    }
  ],
  "test_summary": {
    "total_tools": 5,
    "tested": 5,
    "passing": 5
  }
}
```

### 4. README: `README.md`
```markdown
# ${repo_name} MCP Server

MCP server providing tools for [description].

## Installation

\`\`\`bash
# Activate environment
conda activate ./env/${repo_name}-env

# Install MCP server
pip install fastmcp
\`\`\`

## Usage

### With Claude Desktop
Add to your Claude config:
\`\`\`json
{
  "mcpServers": {
    "${repo_name}": {
      "command": "python",
      "args": ["path/to/src/${repo_name}_mcp.py"]
    }
  }
}
\`\`\`

### With fastmcp CLI
\`\`\`bash
fastmcp install claude-code src/${repo_name}_mcp.py
\`\`\`

## Available Tools

### predict_protein_structure
Predict 3D structure of a protein from sequence.

**Parameters:**
- \`sequence\` (required): Amino acid sequence
- \`output_dir\` (optional): Directory to save output
- \`model\` (optional): Model to use (default, fast, accurate)

**Example:**
\`\`\`
Use the predict_protein_structure tool with sequence "MKFLILF..."
\`\`\`

## Development

\`\`\`bash
# Run tests
pytest tests/ -v

# Test server
fastmcp dev src/${repo_name}_mcp.py
\`\`\`
```

## Success Criteria

- [ ] MCP server created with FastMCP
- [ ] All suitable functions wrapped as MCP tools  
- [ ] Tools have clear descriptions for LLM use
- [ ] Error handling returns structured error responses
- [ ] File inputs/outputs handled appropriately
- [ ] All tools tested and passing
- [ ] Server starts without errors
- [ ] README with installation and usage instructions

## Common Issues and Solutions

### Issue: Import errors when running MCP server
**Solution:** Ensure SCRIPT_DIR is added to sys.path before imports

### Issue: File paths not working
**Solution:** Always use Path objects and resolve to absolute paths

### Issue: Large outputs causing issues
**Solution:** For large results, save to file and return path instead of content

### Issue: Long-running operations timing out
**Solution:** Add progress logging and consider breaking into smaller steps
