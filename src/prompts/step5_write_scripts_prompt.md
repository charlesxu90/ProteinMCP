# Step 5: Extract Clean Scripts for MCP Functions

## Role
You are an expert Python developer specializing in creating clean, minimal, and self-contained function libraries. Your mission is to extract the core functionality from the verified use cases (Step 4) into clean scripts that:
1. **Minimize dependencies** - Only import what's absolutely necessary
2. **Reduce reliance on repo code** - Inline or simplify repo functions where possible
3. **Are self-contained** - Each script should work independently
4. **Are MCP-ready** - Easy to wrap as MCP tools in the next step

## Input Parameters
- `repo/`: Repository codebase directory
- `examples/`: Verified use case scripts from Step 4
- `examples/data/`: Demo data from Step 3
- `reports/use_cases.json`: Use cases documentation
- `reports/execution_results.json`: Execution results from Step 4
- `env/`: Main conda environment
- `env_py{version}/`: Legacy environment (if exists)

## Prerequisites
- All use cases in `examples/` have been verified to work (Step 4)
- Read `reports/execution_results.json` to understand which use cases are successful

## Design Principles

### 1. Dependency Minimization
```python
# BAD: Importing entire library for one function
from big_library import everything
result = everything.utils.helpers.process(data)

# GOOD: Import only what's needed or inline simple functions
from big_library.core import process  # Direct import
# OR: Inline if function is simple
def process(data):
    # Inlined implementation
    return processed_data
```

### 2. Reduce Repo Reliance
```python
# BAD: Deep dependency on repo structure
import sys
sys.path.insert(0, "repo/library/src/submodule")
from internal.helpers import complex_function

# GOOD: Extract and simplify core logic
def complex_function(input_data):
    """Simplified version of repo's complex_function.
    
    Original: repo/library/src/submodule/internal/helpers.py
    Simplified to remove unnecessary features for MCP use case.
    """
    # Core logic extracted and simplified
    return result
```

### 3. Configuration Over Code
```python
# BAD: Hardcoded paths and parameters scattered in code
model_path = "/absolute/path/to/model.pt"
default_params = {"lr": 0.001, "epochs": 100}

# GOOD: Centralized configuration
# configs/use_case_config.yaml or configs/use_case_config.json
CONFIG = {
    "model_path": "models/model.pt",  # Relative path
    "default_params": {"lr": 0.001, "epochs": 100},
    "input_format": "pdb",
    "output_format": "csv"
}
```

## Tasks

### Task 1: Analyze Use Case Dependencies

For each verified use case in `examples/`:

1. **List All Imports**
   ```bash
   # Extract imports from each script
   grep -E "^import |^from " examples/use_case_*.py
   ```

2. **Categorize Dependencies**
   - **Essential**: Core functionality (numpy, pandas, torch)
   - **Repo-specific**: Imports from `repo/` directory
   - **Utilities**: Helper functions that can be inlined
   - **Optional**: Features that can be removed for minimal version

3. **Document Dependency Tree**
   ```
   use_case_1_predict.py
   ├── Essential: numpy, torch
   ├── Repo: repo.model.predict() -> Can be simplified
   └── Utility: repo.utils.load_data() -> Inline
   ```

### Task 2: Extract Core Functions to Scripts

For each use case, create a clean script in `scripts/`:

1. **Script Structure**
   ```python
   #!/usr/bin/env python3
   """
   Script: <use_case_name>.py
   Description: <what this script does>
   
   Original Use Case: examples/<original_script>.py
   Dependencies Removed: <list of inlined/removed dependencies>
   
   Usage:
       python scripts/<use_case_name>.py --input <input_file> --output <output_file>
   
   Example:
       python scripts/<use_case_name>.py --input examples/data/sample.pdb --output results/output.csv
   """
   
   # ==============================================================================
   # Minimal Imports (only essential packages)
   # ==============================================================================
   import argparse
   from pathlib import Path
   from typing import Union, Optional, Dict, Any
   import json
   
   # Essential scientific packages (if needed)
   import numpy as np
   # import torch  # Only if ML is required
   
   # ==============================================================================
   # Configuration (extracted from use case)
   # ==============================================================================
   DEFAULT_CONFIG = {
       "param1": "default_value",
       "param2": 100,
       # Add all configurable parameters here
   }
   
   # ==============================================================================
   # Inlined Utility Functions (simplified from repo)
   # ==============================================================================
   def load_input(file_path: Path) -> Any:
       """Load input file. Simplified from repo/utils/io.py"""
       # Inlined implementation
       pass
   
   def save_output(data: Any, file_path: Path) -> None:
       """Save output file. Simplified from repo/utils/io.py"""
       # Inlined implementation
       pass
   
   # ==============================================================================
   # Core Function (main logic extracted from use case)
   # ==============================================================================
   def run_<use_case_name>(
       input_file: Union[str, Path],
       output_file: Optional[Union[str, Path]] = None,
       config: Optional[Dict[str, Any]] = None,
       **kwargs
   ) -> Dict[str, Any]:
       """
       Main function for <use case description>.
       
       Args:
           input_file: Path to input file
           output_file: Path to save output (optional)
           config: Configuration dict (uses DEFAULT_CONFIG if not provided)
           **kwargs: Override specific config parameters
       
       Returns:
           Dict containing:
               - result: Main computation result
               - output_file: Path to output file (if saved)
               - metadata: Execution metadata
       
       Example:
           >>> result = run_<use_case_name>("input.pdb", "output.csv")
           >>> print(result['output_file'])
       """
       # Setup
       input_file = Path(input_file)
       config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}
       
       if not input_file.exists():
           raise FileNotFoundError(f"Input file not found: {input_file}")
       
       # Load input
       data = load_input(input_file)
       
       # Core processing (extracted and simplified from use case)
       result = process_core_logic(data, config)
       
       # Save output if requested
       output_path = None
       if output_file:
           output_path = Path(output_file)
           output_path.parent.mkdir(parents=True, exist_ok=True)
           save_output(result, output_path)
       
       return {
           "result": result,
           "output_file": str(output_path) if output_path else None,
           "metadata": {
               "input_file": str(input_file),
               "config": config
           }
       }
   
   # ==============================================================================
   # CLI Interface
   # ==============================================================================
   def main():
       parser = argparse.ArgumentParser(
           description=__doc__,
           formatter_class=argparse.RawDescriptionHelpFormatter
       )
       parser.add_argument('--input', '-i', required=True, help='Input file path')
       parser.add_argument('--output', '-o', help='Output file path')
       parser.add_argument('--config', '-c', help='Config file (JSON)')
       # Add use-case specific arguments
       
       args = parser.parse_args()
       
       # Load config if provided
       config = None
       if args.config:
           with open(args.config) as f:
               config = json.load(f)
       
       # Run
       result = run_<use_case_name>(
           input_file=args.input,
           output_file=args.output,
           config=config
       )
       
       print(f"✅ Success: {result.get('output_file', 'Completed')}")
       return result
   
   if __name__ == '__main__':
       main()
   ```

2. **Extraction Guidelines**

   **For Simple Functions (inline them):**
   ```python
   # Original repo code:
   # repo/utils/parsers.py
   def parse_pdb(file_path):
       with open(file_path) as f:
           lines = f.readlines()
       atoms = [l for l in lines if l.startswith('ATOM')]
       return atoms
   
   # Inlined in script (no repo dependency):
   def parse_pdb(file_path: Path) -> list:
       """Parse PDB file. Inlined from repo/utils/parsers.py"""
       with open(file_path) as f:
           return [l for l in f if l.startswith('ATOM')]
   ```

   **For Complex Functions (minimal wrapper):**
   ```python
   # If repo function is complex but essential, create minimal wrapper
   import sys
   from pathlib import Path
   
   # Add repo to path only when needed
   REPO_PATH = Path(__file__).parent.parent / "repo"
   
   def get_repo_model():
       """Lazy load repo model to minimize startup time."""
       sys.path.insert(0, str(REPO_PATH))
       from library.model import Model
       return Model()
   ```

   **For Model/Data Files (use relative paths):**
   ```python
   # Configuration for model paths
   SCRIPT_DIR = Path(__file__).parent
   MCP_ROOT = SCRIPT_DIR.parent
   
   PATHS = {
       "model": MCP_ROOT / "models" / "pretrained.pt",
       "config": MCP_ROOT / "configs" / "model_config.json",
       "data": MCP_ROOT / "examples" / "data"
   }
   ```

### Task 3: Create Configuration Files

For each use case that needs configuration:

1. **Create Config Directory**
   ```
   configs/
   ├── use_case_1_config.json
   ├── use_case_2_config.json
   └── default_config.json
   ```

2. **Config File Format**
   ```json
   {
     "_description": "Configuration for <use case name>",
     "_source": "Extracted from examples/<original_script>.py",
     
     "model": {
       "path": "models/pretrained.pt",
       "type": "transformer",
       "device": "cuda"
     },
     
     "processing": {
       "batch_size": 32,
       "max_length": 512
     },
     
     "output": {
       "format": "csv",
       "include_metadata": true
     }
   }
   ```

### Task 4: Verify Scripts Work Independently

1. **Test Each Script**
   ```bash
   # Activate environment (prefer mamba over conda)
   # First check: which mamba && mamba activate ./env || conda activate ./env
   mamba activate ./env  # or: conda activate ./env
   
   # Run each script with example data
   python scripts/use_case_1.py --input examples/data/sample.pdb --output results/test_output.csv
   
   # Verify output
   cat results/test_output.csv
   ```

2. **Test Without Repo Access** (if possible)
   ```bash
   # Temporarily rename repo to test independence
   mv repo repo_backup
   python scripts/use_case_1.py --input examples/data/sample.pdb --output results/test.csv
   mv repo_backup repo
   ```

3. **Document Any Remaining Repo Dependencies**
   - If a script still needs repo, document exactly what and why
   - Consider if that code can be copied to `scripts/lib/`

### Task 5: Create Shared Library (if needed)

If multiple scripts share common functions:

```
scripts/
├── lib/
│   ├── __init__.py
│   ├── io.py           # Shared I/O functions
│   ├── parsers.py      # Shared parsers
│   └── utils.py        # Shared utilities
├── use_case_1.py
├── use_case_2.py
└── use_case_3.py
```

```python
# scripts/lib/io.py
"""Shared I/O functions for MCP scripts.

These are extracted and simplified from repo code to minimize dependencies.
"""
from pathlib import Path
from typing import Union, Any
import json

def load_json(file_path: Union[str, Path]) -> dict:
    """Load JSON file."""
    with open(file_path) as f:
        return json.load(f)

def save_json(data: dict, file_path: Union[str, Path]) -> None:
    """Save data to JSON file."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

# Add other shared functions...
```

## Expected Outputs

### 1. Clean Scripts: `scripts/` Directory
```
scripts/
├── lib/                        # Shared utilities (if needed)
│   ├── __init__.py
│   ├── io.py
│   └── utils.py
├── use_case_1_<name>.py       # Clean, self-contained script
├── use_case_2_<name>.py
├── use_case_3_<name>.py
└── README.md                   # Script documentation
```

### 2. Configuration Files: `configs/` Directory
```
configs/
├── use_case_1_config.json
├── use_case_2_config.json
└── README.md                   # Config documentation
```

### 3. Script Documentation: `reports/scripts.json`
```json
{
  "extraction_date": "YYYY-MM-DD",
  "scripts": [
    {
      "name": "use_case_1_predict.py",
      "path": "scripts/use_case_1_predict.py",
      "source_use_case": "examples/use_case_1_predict.py",
      "description": "Predict protein structure from sequence",
      
      "main_function": "run_predict",
      "function_signature": "run_predict(input_file, output_file=None, config=None, **kwargs)",
      
      "dependencies": {
        "essential": ["numpy", "torch"],
        "inlined": ["repo.utils.parsers.parse_pdb"],
        "repo_required": ["repo.model.Predictor (lazy loaded)"]
      },
      
      "config_file": "configs/use_case_1_config.json",
      
      "inputs": [
        {"name": "input_file", "type": "file", "format": "pdb", "description": "Input structure"}
      ],
      "outputs": [
        {"name": "result", "type": "dict", "description": "Prediction results"},
        {"name": "output_file", "type": "file", "format": "csv", "description": "Saved results"}
      ],
      
      "cli_usage": "python scripts/use_case_1_predict.py --input FILE --output FILE",
      "example": "python scripts/use_case_1_predict.py --input examples/data/sample.pdb --output results/pred.csv",
      
      "tested": true,
      "independent_of_repo": false,
      "repo_dependencies_reason": "Requires pretrained model loading from repo.model"
    }
  ],
  "shared_lib": {
    "path": "scripts/lib/",
    "modules": ["io.py", "utils.py"],
    "functions_count": 12
  },
  "summary": {
    "total_scripts": 5,
    "fully_independent": 3,
    "repo_dependent": 2,
    "total_inlined_functions": 15,
    "config_files_created": 5
  }
}
```

### 4. Updated README.md in scripts/
```markdown
# MCP Scripts

Clean, self-contained scripts extracted from use cases for MCP tool wrapping.

## Design Principles

1. **Minimal Dependencies**: Only essential packages imported
2. **Self-Contained**: Functions inlined where possible
3. **Configurable**: Parameters in config files, not hardcoded
4. **MCP-Ready**: Each script has a main function ready for MCP wrapping

## Scripts

| Script | Description | Repo Dependent | Config |
|--------|-------------|----------------|--------|
| `use_case_1_predict.py` | Predict structure | No | `configs/use_case_1.json` |
| `use_case_2_analyze.py` | Analyze results | Yes (model) | `configs/use_case_2.json` |

## Usage

```bash
# Activate environment (prefer mamba over conda)
mamba activate ./env  # or: conda activate ./env

# Run a script
python scripts/use_case_1_predict.py --input examples/data/sample.pdb --output results/output.csv

# With custom config
python scripts/use_case_1_predict.py --input FILE --output FILE --config configs/custom.json
```

## Shared Library

Common functions are in `scripts/lib/`:
- `io.py`: File loading/saving
- `utils.py`: General utilities

## For MCP Wrapping (Step 6)

Each script exports a main function that can be wrapped:
```python
from scripts.use_case_1_predict import run_predict

# In MCP tool:
@mcp.tool()
def predict_structure(input_file: str, output_file: str = None):
    return run_predict(input_file, output_file)
```
```

## Success Criteria

- [ ] All verified use cases have corresponding scripts in `scripts/`
- [ ] Each script has a clearly defined main function (e.g., `run_<name>()`)
- [ ] Dependencies are minimized - only essential imports
- [ ] Repo-specific code is inlined or isolated with lazy loading
- [ ] Configuration is externalized to `configs/` directory
- [ ] Scripts work with example data: `python scripts/X.py --input examples/data/Y`
- [ ] `reports/scripts.json` documents all scripts with dependencies
- [ ] Scripts are tested and produce correct outputs
- [ ] README.md in `scripts/` explains usage

## Dependency Checklist

For each script, verify:
- [ ] No unnecessary imports
- [ ] Simple utility functions are inlined
- [ ] Complex repo functions use lazy loading
- [ ] Paths are relative, not absolute
- [ ] Config values are externalized
- [ ] No hardcoded credentials or API keys

## Important Notes

- **Goal is MCP-ready scripts**: These will be wrapped in Step 6
- **Prefer inlining over importing**: If a function is <20 lines, inline it
- **Use lazy loading for heavy imports**: `torch`, repo models, etc.
- **Test independence**: Try running without repo access when possible
- **Document what can't be simplified**: Some repo code may be essential
