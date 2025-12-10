# Step 3: Setup Conda Environment & Scan Common Use Cases

## Role
You are an expert Python environment manager and codebase analyst. Your mission is to set up a working conda environment for the repository and identify common use cases that can be converted into MCP tools.

## Input Parameters
- `repo/${repo_name}`: Repository codebase directory
- `repo_name`: ${repo_name}
- `use_case_filter`: ${use_case_filter} (optional filter for specific use cases)

## Tasks

### Task 1: Setup Conda Environment

1. **Analyze Repository Requirements**
   - Check for `environment.yml`, `requirements.txt`, `setup.py`, `pyproject.toml`
   - Identify Python version requirements
   - List all dependencies

2. **Create Conda Environment**
   - Create environment named `${repo_name}-env` in the `env/` directory
   - Use Python 3.10+ (prefer 3.10 for compatibility)
   - Install all required dependencies
   
   ```bash
   # Example commands
   conda create -p ./env/${repo_name}-env python=3.10 -y
   conda activate ./env/${repo_name}-env
   pip install -r repo/${repo_name}/requirements.txt
   ```

3. **Verify Installation**
   - Test that key imports work
   - Run any existing tests if available
   - Document any issues or workarounds needed

### Task 2: Scan Common Use Cases

1. **Identify Use Cases from Documentation**
   - Read README.md, tutorials, examples, notebooks
   - Look for "Getting Started", "Quick Start", "Examples" sections
   - Identify the main functionalities the library provides

2. **Analyze Code Structure**
   - Find main entry points (CLI scripts, main functions)
   - Identify key classes and functions users would call
   - Look for example scripts in `examples/`, `scripts/`, `demo/` directories

3. **Filter Use Cases** (if `use_case_filter` is provided)
   - Only include use cases matching: "${use_case_filter}"
   - Match against use case names, descriptions, or file paths

4. **Classify Use Cases**
   For each use case, document:
   - **Name**: Short descriptive name
   - **Description**: What it does
   - **Input**: Required inputs (files, parameters)
   - **Output**: What it produces
   - **Complexity**: Simple/Medium/Complex
   - **Source**: Where the example/documentation was found
   - **Priority**: High/Medium/Low (based on usefulness as MCP tool)

## Expected Outputs

### 1. Environment Report: `reports/environment_setup.md`
```markdown
# Environment Setup Report

## Environment Details
- **Name**: ${repo_name}-env
- **Python Version**: 3.10.x
- **Location**: ./env/${repo_name}-env

## Dependencies Installed
- package1==1.0.0
- package2==2.0.0
...

## Installation Commands
\`\`\`bash
conda activate ./env/${repo_name}-env
\`\`\`

## Verification Status
- [x] Core imports working
- [x] Tests passing (if applicable)
- [ ] Issues encountered: <describe any issues>

## Notes
<Any special configuration or workarounds needed>
```

### 2. Use Cases Report: `reports/use_cases.json`
```json
{
  "repo_name": "${repo_name}",
  "scan_date": "YYYY-MM-DD",
  "filter_applied": "${use_case_filter}",
  "use_cases": [
    {
      "id": "uc_001",
      "name": "Use Case Name",
      "description": "What this use case does",
      "inputs": [
        {"name": "input_file", "type": "file", "description": "Input PDB file"}
      ],
      "outputs": [
        {"name": "result", "type": "file", "description": "Output CSV file"}
      ],
      "complexity": "simple|medium|complex",
      "source_file": "path/to/example.py",
      "source_docs": "README.md#section",
      "priority": "high|medium|low",
      "example_code": "# Code snippet showing usage"
    }
  ],
  "summary": {
    "total_found": 10,
    "high_priority": 3,
    "medium_priority": 4,
    "low_priority": 3
  }
}
```

## Success Criteria

- [ ] Conda environment created and activated successfully
- [ ] All core dependencies installed without errors
- [ ] At least 3 use cases identified
- [ ] Use cases documented with inputs/outputs
- [ ] Reports generated in `reports/` directory

## Error Handling

- If environment creation fails, try alternative Python versions (3.11, 3.12)
- If dependencies conflict, document which ones and suggest alternatives
- If no use cases found, expand search to include any code examples
- Document all errors and attempted fixes in the report
