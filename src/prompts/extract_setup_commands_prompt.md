# Extract Setup Commands from README

## Role
You are an expert at analyzing README files and extracting installation/setup commands.

## Input Parameters
- `README.md`: The README file in the current MCP directory

## Task

Analyze the README.md file in this directory and extract the setup commands needed to install and configure this MCP.

### Step 1: Read the README

Read the README.md file in the current directory.

### Step 2: Identify Installation Section

Find the Installation or Setup section in the README. This is typically marked with:
- `## Installation`
- `## Setup`
- `# Installation`
- Or similar headers

### Step 3: Extract Commands

From the installation section, extract all bash commands that are needed to set up the environment. These typically include:

1. **Environment creation** - Commands like:
   - `mamba env create -p ./env python=3.10 -y`
   - `conda env create -p ./env python=3.10 -y`
   - `python3 -m venv ./env`

2. **Package installation** - Commands like:
   - `pip install torch ...`
   - `pip install -r requirements.txt`
   - `pip install fastmcp`

3. **Additional setup** - Commands like:
   - Downloading models
   - Compiling code
   - Setting up config files

### Step 4: Convert to setup_commands Format

Convert the extracted commands to the setup_commands format used in mcps.yaml:

1. **Environment creation**: Use this standard pattern with fallback:
   ```
   (command -v mamba >/dev/null 2>&1 && mamba env create -p ./env python=3.10 -y) || (command -v conda >/dev/null 2>&1 && conda env create -p ./env python=3.10 -y) || (echo "Warning: Neither mamba nor conda found, creating venv instead" && python3 -m venv ./env)
   ```

2. **Skip activation commands**: Do not include `mamba activate` or `conda activate` commands

3. **Convert pip commands**: Replace `pip install` with `./env/bin/pip install`

4. **Convert python commands**: Replace `python` with `./env/bin/python`

5. **Ensure fastmcp**: Make sure `./env/bin/pip install --ignore-installed fastmcp` is included

### Step 5: Output the Commands

Write the setup commands as a JSON array to `reports/setup_commands.json`. Please follow the schema below to extract the information from `README.md`. Typically, it is in `Install` or `Installation` section.

```json
{
  "setup_commands": [
    "(command -v mamba >/dev/null 2>&1 && mamba env create -p ./env python=3.10 -y) || (command -v conda >/dev/null 2>&1 && conda env create -p ./env python=3.10 -y) || (echo \"Warning: Neither mamba nor conda found, creating venv instead\" && python3 -m venv ./env)",
    "./env/bin/pip install torch==2.4.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118",
    "./env/bin/pip install -r requirements.txt",
    "./env/bin/pip install --ignore-installed fastmcp"
  ]
}
```

## Expected Output

A JSON file at `reports/setup_commands.json` containing the extracted and formatted setup commands.

## Important Notes

- Always include the environment creation command with mamba/conda/venv fallback
- Skip any `cd` commands or directory navigation
- Skip any `mamba activate` or `conda activate` commands
- Replace `pip` with `./env/bin/pip`
- Replace `python` with `./env/bin/python`
- Ensure fastmcp installation is included
- Keep the order of commands as they appear in the README
- If no Installation section is found, create default commands based on requirements.txt if present
