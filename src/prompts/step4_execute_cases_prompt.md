# Step 4: Execute Common Use Cases (Bugfix if Needed)

## Role
You are an expert code executor and debugger. Your mission is to execute each use case script created in Step 3, fix any bugs encountered (code issues, data issues, dependency issues), and ensure all use cases actually work end-to-end.

## Input Parameters
- `repo/`: Repository codebase directory
- `examples/`: Use case scripts created in Step 3
- `examples/data/`: Demo data copied in Step 3
- `reports/step3_use_cases.md`: Use cases documented in Step 3
- `env/`: Main conda environment from Step 3
- `env_py{version}/`: Legacy environment (if created in Step 3)
- `api_key`: ${api_key} (if needed for API calls)

## Prerequisites
- Read `reports/step3_use_cases.md` to understand all use cases and their requirements
- Check which environment each use case requires (`./env` or `./env_py{version}`)
- Verify demo data exists in `examples/data/`
- Check package manager availability:
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

### Task 1: Execute Each Use Case Script

For each use case script in `examples/`:

1. **Activate the Correct Environment**
   ```bash
   # Check which environment is needed from step3_use_cases.md
   # Use the PKG_MGR variable determined in prerequisites
   $PKG_MGR activate ./env
   # OR for legacy:
   $PKG_MGR activate ./env_py{version}
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

### 1. Execution Results: `reports/step4_execution.md`
```markdown
# Step 4: Execution Results Report

## Execution Information
- **Execution Date**: YYYY-MM-DD
- **Total Use Cases**: 10
- **Successful**: 8
- **Failed**: 1
- **Partial**: 1

## Results Summary

| Use Case | Status | Environment | Time | Output Files |
|----------|--------|-------------|------|-------------|
| UC-001: Use Case Name | ✅ Success | ./env | 12.5s | `results/output.csv` |
| UC-002: Another Case | ❌ Failed | ./env_py3.9 | - | - |
| UC-003: Third Case | ⚠️ Partial | ./env | 45.2s | `results/partial.json` |

---

## Detailed Results

### UC-001: Use Case Name
- **Status**: ✅ Success
- **Script**: `examples/use_case_1_name.py`
- **Environment**: `./env`
- **Execution Time**: 12.5 seconds
- **Command**: `python examples/use_case_1_name.py --input examples/data/sample.pdb --output results/output.csv`
- **Input Data**: `examples/data/sample.pdb`
- **Output Files**: `results/output.csv`

**Issues Found**: None

---

### UC-002: Another Case
- **Status**: ❌ Failed
- **Script**: `examples/use_case_2_name.py`
- **Environment**: `./env_py3.9`

**Issues Found:**

| Type | Description | File | Line | Fixed? |
|------|-------------|------|------|--------|
| import_error | Missing package xyz | `examples/use_case_2_name.py` | 42 | ✅ Yes |
| data_issue | Wrong data format | `examples/data/input.csv` | - | ❌ No |

**Error Message:**
```
Original error message here
```

**Fix Applied:**
Description of fix applied

---

## Issues Summary

| Metric | Count |
|--------|-------|
| Issues Fixed | 15 |
| Issues Remaining | 2 |

### Remaining Issues
1. **UC-002**: Data format issue - needs manual data conversion
2. **UC-005**: GPU required but not available

---

## Notes
Any additional notes about this execution run
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
# Activate environment (use mamba if available, otherwise conda)
mamba activate ./env  # or: conda activate ./env

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
- [ ] `reports/step4_execution.md` documents all results
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
