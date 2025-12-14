# Step 4: Execute Common Use Cases (Bugfix if Needed)

## Role
You are an expert code executor and debugger. Your mission is to execute each use case script created in Step 3, fix any bugs encountered (code issues, data issues, dependency issues), and ensure all use cases actually work end-to-end.

## Input Parameters
- `repo/`: Repository codebase directory
- `examples/`: Use case scripts created in Step 3
- `examples/data/`: Demo data copied in Step 3
- `reports/use_cases.json`: Use cases documented in Step 3
- `env/`: Main conda environment from Step 3
- `env_py{version}/`: Legacy environment (if created in Step 3)
- `api_key`: ${api_key} (if needed for API calls)

## Prerequisites
- Read `reports/use_cases.json` to understand all use cases and their requirements
- Check which environment each use case requires (`./env` or `./env_py{version}`)
- Verify demo data exists in `examples/data/`

## Tasks

### Task 1: Execute Each Use Case Script

For each use case script in `examples/`:

1. **Activate the Correct Environment**
   ```bash
   # Check which environment is needed from use_cases.json
   # Use mamba if available, otherwise conda
   mamba activate ./env  # or: conda activate ./env
   # OR for legacy:
   mamba activate ./env_py{version}  # or: conda activate ./env_py{version}
   ```

2. **Run the Use Case Script**
   ```bash
   # Execute with example data from examples/data/
   python examples/use_case_name.py --input examples/data/sample.pdb --output results/output.csv
   ```

3. **Capture Results**
   - Record stdout, stderr
   - Check if output files are generated correctly
   - Verify output format and content
   - Record execution time

### Task 2: Debug and Fix Issues

When execution fails, systematically debug:

1. **Import Errors**
   - Missing packages: Install in the correct environment
   - Wrong Python version: Use legacy environment if needed
   - Path issues: Fix sys.path or PYTHONPATH

2. **Data Issues**
   - Missing demo data: Find alternative data in repo or create minimal test data
   - Wrong data format: Convert or fix the data
   - File path issues: Update paths in scripts to use `examples/data/`
   - Data corruption: Re-copy from source or download fresh

3. **Code Issues**
   - API changes: Update function calls to match current library version
   - Deprecated functions: Replace with current alternatives
   - Logic errors: Fix the script code
   - Missing configuration: Add required config files or environment variables

4. **Dependency Issues**
   - Version conflicts: Pin specific versions or find compatible ones
   - Missing system libraries: Document required system dependencies
   - GPU/CUDA issues: Add CPU fallback or document GPU requirements

5. **Apply Fixes**
   - Fix the use case script in `examples/`
   - If repository code needs modification, create patches in `patches/` directory
   - Document all changes made

### Task 3: Validate Working Use Cases

For each successfully executed use case:

1. **Verify Output**
   - Check output files exist and are valid
   - Verify output format matches expected schema
   - Compare with expected results if available

2. **Test Variations**
   - Try with different input data if available
   - Test edge cases (empty input, large files, etc.)
   - Verify error handling works

3. **Update Script if Needed**
   - Add better error messages
   - Add input validation
   - Improve output formatting
   - Add progress indicators for long-running tasks

### Task 4: Update Documentation

1. **Update Use Case Scripts**
   - Add verified example commands in docstrings
   - Document any required environment variables
   - Add troubleshooting notes

2. **Update README.md**
   - Add verified working examples
   - Document any additional setup steps discovered
   - Add troubleshooting section with solutions found

## Expected Outputs

### 1. Execution Results: `reports/execution_results.json`
```json
{
  "execution_date": "YYYY-MM-DD",
  "results": [
    {
      "use_case_id": "uc_001",
      "name": "Use Case Name",
      "script_path": "examples/use_case_1_name.py",
      "status": "success|failed|partial",
      "environment_used": "./env or ./env_py{version}",
      "execution_time_seconds": 12.5,
      "command_executed": "python examples/use_case_1_name.py --input examples/data/sample.pdb --output results/output.csv",
      "input_data": "examples/data/sample.pdb",
      "output_files": ["results/output.csv"],
      "issues_found": [
        {
          "type": "import_error|data_issue|code_bug|dependency_issue",
          "description": "Description of the issue",
          "file": "examples/use_case_1_name.py",
          "line": 42,
          "error_message": "Original error message",
          "fix_applied": "Description of fix applied",
          "fixed": true
        }
      ],
      "notes": "Any additional notes about this use case"
    }
  ],
  "summary": {
    "total": 10,
    "successful": 8,
    "failed": 1,
    "partial": 1,
    "issues_fixed": 15,
    "issues_remaining": 2
  }
}
```

### 2. Updated Use Case Scripts in `examples/`
- All scripts should run without errors
- Scripts should have verified example commands
- Scripts should handle common error cases

### 3. Results Directory: `results/`
```
results/
├── uc_001/
│   ├── output.csv          # Actual output from execution
│   └── execution.log       # Execution log with timing
├── uc_002/
│   └── output.json
...
```

### 4. Patches Directory (if repo code was modified): `patches/`
```
patches/
├── fix_import_error.patch
├── fix_deprecated_api.patch
└── README.md              # Description of each patch
```

### 5. Updated README.md
Add a "Verified Examples" section with actually working commands:
```markdown
## Verified Examples

These examples have been tested and verified to work:

### Example 1: <Use Case Name>
```bash
# Activate environment
mamba activate ./env

# Run the example
python examples/use_case_1_name.py --input examples/data/sample.pdb --output results/output.csv

# Expected output: results/output.csv with <description>
```

### Example 2: <Use Case Name>
...
```

## Success Criteria

- [ ] All use case scripts in `examples/` have been executed
- [ ] At least 80% of use cases run successfully
- [ ] All fixable issues have been resolved
- [ ] Output files are generated and valid
- [ ] `reports/execution_results.json` documents all results
- [ ] `results/` directory contains actual outputs
- [ ] README.md updated with verified working examples
- [ ] Unfixable issues are documented with clear explanations

## Error Handling Strategy

1. **First Attempt**: Run script as-is, capture all errors
2. **Quick Fixes**: Apply obvious fixes (missing imports, path issues)
3. **Data Fixes**: Fix or replace problematic data files
4. **Deep Debug**: Trace through code to find root cause
5. **Environment Fixes**: Install missing packages or use different environment
6. **Document & Skip**: If still failing after 3 attempts, document and move on

## Important Notes

- Always use the correct environment for each use case
- Keep original scripts as backup before modifying: `cp script.py script.py.bak`
- Test fixes thoroughly before marking as successful
- Document ALL changes made for reproducibility
- If modifying repo code, create patches instead of editing in place
- Prefer mamba over conda for faster package operations
