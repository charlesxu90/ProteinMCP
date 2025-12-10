# Step 4: Execute Common Use Cases (Bugfix if Needed)

## Role
You are an expert code executor and debugger. Your mission is to execute each identified use case from the previous step, fix any bugs encountered, and document working examples.

## Input Parameters
- `repo/${repo_name}`: Repository codebase directory  
- `repo_name`: ${repo_name}
- `reports/use_cases.json`: Use cases identified in Step 3
- `env/${repo_name}-env`: Conda environment from Step 3
- `api_key`: ${api_key} (if needed for API calls)

## Prerequisites
- Activate the conda environment before executing any code:
  ```bash
  conda activate ./env/${repo_name}-env
  ```

## Tasks

### Task 1: Execute Each Use Case

For each use case in `reports/use_cases.json`:

1. **Prepare Test Data**
   - Find or create appropriate test input files
   - Copy test data to `examples/` directory
   - Document data sources and formats

2. **Execute the Use Case**
   - Run the example code in a controlled environment
   - Capture all outputs (stdout, stderr, files)
   - Record execution time

3. **Document Results**
   - Save successful outputs to `examples/{use_case_id}/`
   - Screenshot or save any visualizations
   - Record the exact commands used

### Task 2: Debug and Fix Issues

When execution fails:

1. **Analyze the Error**
   - Identify error type (ImportError, ValueError, FileNotFoundError, etc.)
   - Trace the root cause
   - Check for missing dependencies or configuration

2. **Apply Fixes**
   - Fix bugs in the repository code if needed
   - Document all changes made
   - Create workarounds for unfixable issues

3. **Retry Execution**
   - Re-run after applying fixes
   - Verify the fix resolves the issue
   - Test with multiple inputs if possible

4. **Document Fixes**
   - Record what was broken and how it was fixed
   - Note any upstream issues to report
   - Create patches or modified scripts in `scripts/`

### Task 3: Create Working Examples

For each successfully executed use case:

1. **Create Standalone Script**
   - Write a clean, documented script in `scripts/{use_case_id}.py`
   - Include all necessary imports and setup
   - Add argument parsing for inputs
   - Include example usage in docstring

2. **Test the Script**
   - Run with provided test data
   - Verify output matches expected results
   - Test edge cases if time permits

## Expected Outputs

### 1. Execution Results: `reports/execution_results.json`
```json
{
  "repo_name": "${repo_name}",
  "execution_date": "YYYY-MM-DD",
  "environment": "./env/${repo_name}-env",
  "results": [
    {
      "use_case_id": "uc_001",
      "name": "Use Case Name",
      "status": "success|failed|partial",
      "execution_time_seconds": 12.5,
      "test_data": "examples/uc_001/input.pdb",
      "output_files": ["examples/uc_001/output.csv"],
      "script_created": "scripts/uc_001.py",
      "bugs_fixed": [
        {
          "file": "repo/${repo_name}/src/module.py",
          "line": 42,
          "issue": "Description of bug",
          "fix": "Description of fix applied"
        }
      ],
      "notes": "Any additional notes"
    }
  ],
  "summary": {
    "total": 10,
    "successful": 8,
    "failed": 1,
    "partial": 1
  }
}
```

### 2. Working Scripts in `scripts/` Directory
```python
#!/usr/bin/env python3
"""
Use Case: {name}
Description: {description}

Usage:
    python scripts/uc_001.py --input input.pdb --output output.csv

Example:
    python scripts/uc_001.py --input examples/uc_001/input.pdb --output results.csv
"""

import argparse
from pathlib import Path
import sys

# Add repo to path
sys.path.insert(0, str(Path(__file__).parent.parent / "repo" / "${repo_name}"))

# Imports from the repository
from module import function

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, help='Input file path')
    parser.add_argument('--output', required=True, help='Output file path')
    args = parser.parse_args()
    
    # Execute the use case
    result = function(args.input)
    
    # Save output
    with open(args.output, 'w') as f:
        f.write(result)
    
    print(f"Output saved to {args.output}")

if __name__ == '__main__':
    main()
```

### 3. Test Data in `examples/` Directory
```
examples/
├── uc_001/
│   ├── input.pdb
│   ├── output.csv
│   └── README.md
├── uc_002/
│   ├── input.fasta
│   └── output.json
...
```

## Success Criteria

- [ ] All high-priority use cases attempted
- [ ] At least 70% of use cases execute successfully
- [ ] Working scripts created for successful use cases
- [ ] All bugs documented with fixes applied
- [ ] Test data and outputs saved in examples/

## Error Handling

- If a use case consistently fails after 3 fix attempts, mark as "failed" and move on
- Document all error messages and stack traces
- Create minimal reproducible examples for unfixed bugs
- Note which use cases might work with different inputs/configurations

## Important Notes

- Always activate the conda environment before running code
- Use relative paths within the project directory
- Don't modify the original repository code unless necessary
- Keep track of all changes for potential upstream contributions
