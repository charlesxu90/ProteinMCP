# Step 3: Setup Conda Environment & Scan Common Use Cases

## Role
You are an expert Python environment manager and codebase analyst. Your mission is to set up working conda environments for the repository and identify common use cases that can be converted into MCP tools.

## Input Parameters
- `repo/`: Repository codebase directory (auto-detected, no repo_name prefix)
- `use_case_filter`: ${use_case_filter} (optional filter for specific use cases)

## Tasks

### Task 1: Setup Conda Environments

1. **Check Package Manager Availability**
   - First check if `mamba` is available: `which mamba`
   - If mamba exists, use `mamba` for all conda commands (faster)
   - If mamba doesn't exist, fall back to `conda`
   - Store the package manager in a variable for consistency:
     ```bash
     # Determine package manager (prefer mamba over conda)
     if command -v mamba &> /dev/null; then
         PKG_MGR="mamba"
     else
         PKG_MGR="conda"
     fi
     echo "Using package manager: $PKG_MGR"
     ```

2. **Analyze Repository Requirements**
   - Check for `environment.yml`, `requirements.txt`, `setup.py`, `pyproject.toml`
   - Identify Python version requirements from the repository
   - List all dependencies

3. **Determine Python Version Strategy**
   
   **If original Python >= 3.10:**
   - Use the detected Python version
   - Create single environment at `./env` with all dependencies
   
   **If original Python < 3.10:**
   - Create TWO environments (similar to MutCompute MCP pattern):
     - **Main MCP environment**: `./env` with Python 3.10+ (for MCP server & utilities)
     - **Legacy build environment**: `./env_py{version}` in the MCP home directory using the original Python version (for building dependencies that require specific Python)
   - Install core MCP dependencies in `./env` (loguru, click, fastmcp, etc.)
   - Install library-specific dependencies in `./env_py{version}` as needed

4. **Create Conda Environment(s)**

   **Single Environment (Python >= 3.10):**
   ```bash
   # Use mamba if available, otherwise conda
   $PKG_MGR create -p ./env python=3.10 -y
   $PKG_MGR activate ./env
   pip install -r repo/requirements.txt
   # or
   $PKG_MGR env update -p ./env -f repo/environment.yml
   ```

   **Dual Environment (Python < 3.10):**
   ```bash
   # Main environment for MCP
   $PKG_MGR create -p ./env python=3.10 pip -y
   $PKG_MGR activate ./env
   pip install loguru click pandas numpy tqdm
   pip install --ignore-installed fastmcp
   
   # Legacy environment for original dependencies (e.g., ./env_py3.9 if detected version is 3.9)
   $PKG_MGR env create -f repo/environment.yml -p ./env_py{version} -y
   $PKG_MGR activate ./env_py{version}
   # Install any additional build tools needed (CUDA, cudnn, etc.)
   ```

5. **Verify Installation**
   - Test core imports in `./env`
   - Test library imports in `./env_py{version}` (if created)
   - Run any existing tests if available
   - Document any issues or workarounds needed

### Task 2: Scan Common Use Cases & Extract to Python Scripts

1. **Identify Use Cases from Documentation**
   - Read README.md, tutorials, examples, and documentation
   - Look for "Getting Started", "Quick Start", "Examples" sections
   - Identify the main functionalities the library provides
   - Search for example code in `examples/`, `scripts/`, `demo/`, `notebooks/` directories

2. **Analyze Code Structure**
   - Find main entry points (CLI scripts, main functions)
   - Identify key classes and functions users would call
   - Extract runnable code from documentation, notebooks, and examples
   - Convert notebook examples to standalone Python scripts

3. **Filter Use Cases** (if `use_case_filter` is provided)
   - Only include use cases matching: "${use_case_filter}"
   - Match against use case names, descriptions, or file paths

4. **Create Python Scripts for Each Use Case**
   - Convert each use case into a standalone, runnable Python script
   - Save to `examples/` directory with descriptive names (e.g., `use_case_1_predict.py`)
   - Include:
     - Proper imports and environment setup
     - Input handling (file paths, parameters)
     - Clear comments explaining each step
     - Output generation
     - Error handling
   - Script should be runnable with: `python examples/use_case_name.py [args]`

5. **Copy Demo Data to Examples Directory**
   - Identify all demo/test data from the repository (test files, sample inputs, etc.)
   - Copy to `examples/data/` subdirectory for easy access
   - Maintain logical subdirectory structure (e.g., `examples/data/`, `examples/models/`)
   - Document the purpose of each demo file
   - Update scripts to use relative paths to `examples/data/` for default inputs
   - Example: `python examples/use_case_1_predict.py --input examples/data/sample.pdb`

6. **Classify Use Cases**
   For each use case, document:
   - **Name**: Short descriptive name
   - **Description**: What it does
   - **Script Path**: `examples/use_case_name.py`
   - **Input**: Required inputs (files, parameters)
   - **Output**: What it produces
   - **Complexity**: Simple/Medium/Complex
   - **Source**: Where the example/documentation was found
   - **Priority**: High/Medium/Low (based on usefulness as MCP tool)
   - **Environment**: Which environment to use (`./env` or `./env_py{version}`)
   - **Parameters**: Command-line arguments or configuration needed
   - **Example Data**: Path to demo data in `examples/data/` directory

## Expected Outputs

### 1. MCP README: `README.md` (in MCP root directory)
Create a comprehensive README.md file in the MCP directory root with **actual commands used during setup** - not a template, but the real installation steps that worked.

**IMPORTANT**: This README must contain:
- The **exact Python version** that was successfully used
- The **actual package manager** used (mamba or conda)
- The **exact installation commands** in the order they were executed
- Any **workarounds or fixes** that were needed
- The **actual packages** installed with versions if relevant

```markdown
# <Tool Name> MCP

<Brief description of what this MCP tool does, based on repo analysis>

## Quick Start

### Prerequisites
- Conda or Mamba (mamba recommended for faster installation)
- Python <ACTUAL_VERSION_USED> (e.g., 3.10, 3.11)
- <Any other prerequisites discovered, e.g., CUDA, specific OS>

### Installation

The following commands were tested and verified to work:

```bash
# Navigate to the MCP directory
cd <mcp_directory_path>

# Step 1: Create the conda environment
# (Use the ACTUAL command that was executed)
<mamba|conda> create -p ./env python=<ACTUAL_VERSION> -y

# Step 2: Activate the environment
<mamba|conda> activate ./env

# Step 3: Install dependencies (in the order they were installed)
# List each pip install or conda install command that was run
pip install <package1>
pip install <package2>
# OR if requirements.txt was used:
pip install -r requirements.txt

# Step 4: Any additional setup steps that were needed
<additional commands if any>
```

### Legacy Environment Setup (if applicable)

If a legacy Python environment was needed (Python < 3.10):

```bash
# Create legacy environment for library-specific dependencies
<mamba|conda> create -p ./env_py<VERSION> python=<LEGACY_VERSION> -y
<mamba|conda> activate ./env_py<VERSION>

# Install legacy dependencies
<actual commands used>
```

### Running the MCP Server

```bash
# Activate the environment
<mamba|conda> activate ./env

# Run the MCP server
python src/server.py
```

## Verified Use Cases

The following scripts have been tested and work with the installed environment:

| Script | Description | Example Command |
|--------|-------------|-----------------|
| `examples/<script1>.py` | <description> | `python examples/<script1>.py --input examples/data/sample.pdb` |
| `examples/<script2>.py` | <description> | `python examples/<script2>.py <args>` |

## Installed Packages

Key packages installed in `./env`:
- <package1>=<version>
- <package2>=<version>
- ...

<If legacy env exists>
Key packages in `./env_py<VERSION>`:
- <package1>=<version>
- ...

## Directory Structure

```
./
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── env/                    # Main conda environment (Python <VERSION>)
├── env_py<VERSION>/        # Legacy environment (if needed)
├── src/                    # MCP server source code
├── examples/               # Use case scripts and demo data
│   ├── use_case_*.py       # Standalone use case scripts
│   ├── data/               # Demo input data
│   └── models/             # Pre-trained models (if any)
├── reports/                # Setup reports
└── repo/                   # Original repository
```

## Troubleshooting

<Document any issues encountered during setup and how they were resolved>

### Known Issues
- <Issue 1>: <Solution>
- <Issue 2>: <Solution>

## Notes

<Any special configuration, environment variables, or setup requirements discovered>
```

### 2. Environment Report: `reports/environment_setup.md`
```markdown
# Environment Setup Report

## Python Version Detection
- **Detected Python Version**: X.X.X
- **Strategy**: Single/Dual environment setup

## Main MCP Environment
- **Location**: ./env
- **Python Version**: 3.10+ (for MCP server)

## Legacy Build Environment (if needed)
- **Location**: ./env_py{version} (if Python < 3.10, e.g., ./env_py3.9)
- **Python Version**: X.X.X (original detected version)
- **Purpose**: Build dependencies requiring specific Python

## Dependencies Installed

### Main Environment (./env)
- loguru
- click
- fastmcp
- pandas
- numpy
...

### Legacy Environment (./env_pyXX, if applicable)
- <library-specific dependencies>
...

## Activation Commands
```bash
# Main MCP environment
conda activate ./env  # or: mamba activate ./env

# Legacy environment (if needed, e.g., for Python 3.9)
conda activate ./env_py3.9  # or: mamba activate ./env_py3.9
```

## Verification Status
- [x] Main environment (./env) functional
- [ ] Legacy environment (./env_py{version}, if applicable) functional
- [x] Core imports working
- [x] Tests passing (if applicable)
- [ ] Issues encountered: <describe any issues>

## Notes
<Any special configuration, workarounds, or environment-specific requirements>
```

### 2. Use Cases Report: `reports/use_cases.json`
```json
{
  "scan_date": "YYYY-MM-DD",
  "filter_applied": "${use_case_filter}",
  "python_version": "X.X.X",
  "environment_strategy": "single|dual",
  "use_cases": [
    {
      "id": "uc_001",
      "name": "Use Case Name",
      "description": "What this use case does",
      "script_path": "examples/use_case_1_name.py",
      "inputs": [
        {"name": "input_file", "type": "file", "description": "Input PDB file", "parameter": "--input or -i"}
      ],
      "outputs": [
        {"name": "result", "type": "file", "description": "Output CSV file"}
      ],
      "complexity": "simple|medium|complex",
      "environment": "./env or ./env_py{version}",
      "source_file": "path/to/original/example.py",
      "source_docs": "README.md#section",
      "priority": "high|medium|low",
      "example_usage": "python examples/use_case_1_name.py --input examples/data/sample.pdb --output result.csv",
      "example_data": "examples/data/sample.pdb",
      "cli_args": [
        {"name": "input", "type": "str", "required": true, "description": "Input file path"},
        {"name": "output", "type": "str", "required": true, "description": "Output file path"}
      ]
    }
  ],
  "summary": {
    "total_found": 10,
    "scripts_created": 10,
    "demo_data_copied": true,
    "high_priority": 3,
    "medium_priority": 4,
    "low_priority": 3
  },
  "demo_data_index": [
    {"source": "repo/tests/data/sample.pdb", "destination": "examples/data/sample.pdb", "description": "Sample protein structure for testing"},
    {"source": "repo/examples/models/pretrained.pt", "destination": "examples/models/pretrained.pt", "description": "Pre-trained model weights"}
  ]
}
```

## Success Criteria

- [ ] Python version detected and strategy determined
- [ ] Main conda environment created at `./env` with Python 3.10+
- [ ] Legacy environment created at `./env_py{version}` (if Python < 3.10)
- [ ] All core dependencies installed without errors
- [ ] At least 3 use cases identified and converted to Python scripts
- [ ] All scripts saved to `examples/` directory with descriptive names
- [ ] Each script is standalone and runnable: `python examples/script_name.py [args]`
- [ ] Scripts include proper error handling and comments
- [ ] Demo/test data copied to `examples/data/` directory with proper organization
- [ ] Scripts use relative paths pointing to `examples/data/` for default inputs
- [ ] Use cases documented with inputs/outputs, CLI parameters, and example data locations
- [ ] Reports generated in `reports/` directory
- [ ] **README.md created with ACTUAL commands used during setup:**
  - [ ] Exact Python version that worked
  - [ ] Package manager used (mamba/conda)
  - [ ] Installation commands in exact order executed
  - [ ] All packages with versions
  - [ ] Any workarounds or fixes documented

## Output Directory Structure

After completion, the project should have:
```
./
├── README.md                     # MCP README with installation instructions
├── requirements.txt              # Python dependencies (if not already present)
├── env/                          # Main MCP environment (Python 3.10+)
├── env_py{version}/             # Legacy environment (if needed)
├── src/                          # MCP server source code (created in later steps)
├── examples/
│   ├── use_case_1_name.py       # Extracted use case scripts
│   ├── use_case_2_name.py
│   ├── use_case_3_name.py
│   ├── data/
│   │   ├── sample.pdb           # Copied demo data
│   │   └── sample.csv
│   ├── models/
│   │   └── pretrained.pt
│   └── README.md                # Index of examples and demo data
├── reports/
│   ├── environment_setup.md
│   └── use_cases.json
└── repo/                         # Original repository
```

## Error Handling

- If environment creation fails, try alternative Python versions (3.11, 3.12)
- If dependencies conflict in dual environment setup, document which ones
- If build tools needed (CUDA, cudnn, etc.), install in legacy environment (./env_py{version}) only
- If no use cases found, expand search to include any code examples
- Document all errors and attempted fixes in the report

