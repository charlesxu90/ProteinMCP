# Step 7: Test Claude and Gemini Integration (Bugfix if Needed)

## Role
You are an expert in LLM integration testing. Your mission is to verify the MCP server works correctly with Claude and Gemini, fix any integration issues, and document the final working solution.

## Input Parameters
- `repo_name`: ${repo_name}
- `src/${repo_name}_mcp.py`: MCP server from Step 6
- `env/${repo_name}-env`: Conda environment
- `api_key`: ${api_key}

## Prerequisites
```bash
conda activate ./env/${repo_name}-env
pip install fastmcp anthropic google-generativeai
```

## Tasks

### Task 1: Local MCP Server Testing

1. **Start MCP Server in Dev Mode**
   ```bash
   fastmcp dev src/${repo_name}_mcp.py
   ```

2. **Test with MCP Inspector**
   ```bash
   npx @anthropic/mcp-inspector src/${repo_name}_mcp.py
   ```
   
   Verify:
   - Server starts without errors
   - All tools are listed
   - Tool descriptions are clear
   - Parameters are correctly typed

3. **Manual Tool Testing**
   Test each tool through the inspector:
   - Call with valid inputs
   - Call with edge cases
   - Call with invalid inputs
   - Verify error messages are helpful

### Task 2: Claude Desktop Integration

1. **Install MCP Server**
   ```bash
   # Option 1: Using fastmcp
   fastmcp install claude-code src/${repo_name}_mcp.py --python ./env/${repo_name}-env/bin/python
   
   # Option 2: Manual config
   # Edit ~/.config/claude/claude_desktop_config.json (Linux)
   # Edit ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
   ```

2. **Configuration File**
   ```json
   {
     "mcpServers": {
       "${repo_name}": {
         "command": "./env/${repo_name}-env/bin/python",
         "args": ["./src/${repo_name}_mcp.py"],
         "cwd": "/absolute/path/to/mcp/directory"
       }
     }
   }
   ```

3. **Test in Claude Desktop**
   - Restart Claude Desktop
   - Verify server appears in MCP list
   - Test each tool with natural language prompts:
     ```
     "Use the ${repo_name} tool to predict the structure of protein MKFLILF..."
     "Analyze the protein structure in /path/to/file.pdb"
     ```

4. **Document Issues and Fixes**
   - Note any errors in Claude's responses
   - Fix tool descriptions if Claude misunderstands usage
   - Adjust parameter names if they're confusing

### Task 3: Claude Code (CLI) Integration

1. **Add MCP Server**
   ```bash
   claude mcp add ${repo_name} -- ./env/${repo_name}-env/bin/python ./src/${repo_name}_mcp.py
   ```

2. **Test in Claude Code**
   ```bash
   claude
   > Use ${repo_name} to predict structure for sequence MKFLILF
   ```

3. **Verify Tool Calling**
   - Tools are discovered correctly
   - Parameters are passed correctly
   - Results are displayed properly
   - Errors are handled gracefully

### Task 4: Gemini Integration (Optional)

If API key is available, test with Gemini:

1. **Create Gemini Test Script**
   ```python
   # tests/test_gemini_integration.py
   
   import google.generativeai as genai
   import json
   from pathlib import Path
   
   # Configure API
   genai.configure(api_key="${api_key}")
   
   # Import MCP tools
   from src.${repo_name}_mcp import mcp
   
   # Define tools for Gemini
   tools = []
   for tool_name, tool_info in mcp.list_tools().items():
       tools.append({
           "name": tool_name,
           "description": tool_info["description"],
           "parameters": tool_info["parameters"]
       })
   
   # Create model with tools
   model = genai.GenerativeModel(
       model_name="gemini-pro",
       tools=tools
   )
   
   # Test conversation
   chat = model.start_chat()
   response = chat.send_message(
       "Predict the structure of protein with sequence MKFLILF"
   )
   
   # Handle tool calls
   if response.candidates[0].content.parts[0].function_call:
       call = response.candidates[0].content.parts[0].function_call
       result = mcp.call_tool(call.name, dict(call.args))
       print(f"Tool result: {result}")
   ```

2. **Run Integration Test**
   ```bash
   python tests/test_gemini_integration.py
   ```

### Task 5: Fix Integration Issues

Common issues and solutions:

1. **Tool Not Found**
   - Check tool name matches exactly
   - Verify server is running
   - Check MCP config paths are absolute

2. **Parameter Errors**
   - Improve parameter descriptions
   - Add type hints and examples
   - Validate inputs in tool function

3. **Timeout Issues**
   - Add progress logging
   - Break into smaller operations
   - Consider async implementation

4. **Path Issues**
   - Use absolute paths in config
   - Set correct working directory
   - Handle relative/absolute path conversion in tools

5. **Environment Issues**
   - Ensure correct Python is used
   - Check all dependencies installed
   - Verify environment activation

### Task 6: Final Documentation

1. **Create Integration Guide**
   ```markdown
   # ${repo_name} MCP Integration Guide
   
   ## Claude Desktop Setup
   1. Install the MCP server...
   2. Configure Claude Desktop...
   3. Test with these prompts...
   
   ## Claude Code Setup
   1. Add MCP server...
   2. Example usage...
   
   ## Gemini Setup (Optional)
   1. Configure API key...
   2. Run integration script...
   
   ## Troubleshooting
   - Issue 1: Solution...
   - Issue 2: Solution...
   ```

2. **Update README**
   Add integration instructions and examples.

## Expected Outputs

### 1. Integration Test Results: `reports/integration_tests.json`
```json
{
  "repo_name": "${repo_name}",
  "test_date": "YYYY-MM-DD",
  "tests": {
    "mcp_inspector": {
      "status": "passed",
      "tools_listed": 5,
      "all_tools_working": true
    },
    "claude_desktop": {
      "status": "passed",
      "server_connected": true,
      "tools_callable": true,
      "natural_language_works": true,
      "notes": "Works well with structured prompts"
    },
    "claude_code": {
      "status": "passed",
      "installation": "successful",
      "tool_discovery": true,
      "execution": true
    },
    "gemini": {
      "status": "skipped|passed|failed",
      "notes": "API key not provided / Works correctly"
    }
  },
  "issues_fixed": [
    {
      "issue": "Tool description unclear",
      "fix": "Added examples to docstring",
      "file": "src/${repo_name}_mcp.py"
    }
  ],
  "final_status": "ready_for_production"
}
```

### 2. Updated MCP Server
Any fixes applied to `src/${repo_name}_mcp.py`

### 3. Integration Guide: `docs/integration_guide.md`
Complete guide for setting up integrations.

### 4. Example Prompts: `docs/example_prompts.md`
```markdown
# Example Prompts for ${repo_name} MCP

## Structure Prediction
- "Predict the structure of protein MKFLILF using the fast model"
- "Generate a PDB file for sequence ACDEFGHIKLMNPQRSTVWY"

## Analysis
- "Analyze the protein structure in /path/to/protein.pdb"
- "Compare structures file1.pdb and file2.pdb"

## Batch Processing
- "Process all PDB files in /data/structures/ directory"
```

## Success Criteria

- [ ] MCP Inspector shows all tools correctly
- [ ] Claude Desktop integration working
- [ ] Claude Code integration working
- [ ] All tools callable through natural language
- [ ] Error messages are helpful and actionable
- [ ] Documentation complete with examples
- [ ] (Optional) Gemini integration tested

## Final Checklist

Before marking complete:

1. **Server Reliability**
   - [ ] Server starts without errors
   - [ ] Server handles multiple requests
   - [ ] Server recovers from tool errors

2. **Tool Quality**
   - [ ] All tools have clear descriptions
   - [ ] Parameters are well-documented
   - [ ] Examples included in docstrings

3. **Integration Quality**
   - [ ] Works with Claude Desktop
   - [ ] Works with Claude Code CLI
   - [ ] Natural language prompts work

4. **Documentation**
   - [ ] README updated
   - [ ] Integration guide complete
   - [ ] Example prompts provided
   - [ ] Troubleshooting section included

## Installation Command

After all tests pass, provide the final installation command:

```bash
# For Claude Code
fastmcp install claude-code src/${repo_name}_mcp.py --python ./env/${repo_name}-env/bin/python

# Verify installation
claude mcp list
```

The MCP server is now ready for production use!
