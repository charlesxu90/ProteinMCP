# ProteinMCP: An Agentic AI Framework for Autonomous Protein Engineering

![ProteinMCP overview](./figures/ProteinMCP.png)
## Install:
```shell
mamba env create -f environment.yml
mamba activate protein-mcp
pip install -r requirements.txt

# Install claude code
npm install -g @anthropic-ai/claude-code

pip install -e .
```
## Supported MCPS:

Please find the 38 supported MCPS in [the MCP list](./tool-mcps/README.md).

## Usage:

### MCP usage
```shell
# List all available MCPs
pmcp avail

# Show MCP details
pmcp info msa

# Install an MCP
pmcp install msa

# Uninstall an MCP
pmcp uninstall msa
```

### MCP creation
```shell
# create from github repository
pmcp create --github-url https://github.com/jwohlwend/boltz --mcp-dir tool-mcps/boltz_mcp --use-case-filter 'structure prediction with boltz2, affinity prediciton with boltz2, batch structure prediction for protein variants given prepared configs'

# create from local dir
pmcp create --local-repo-path tool-mcps/protein_sol_mcp/scripts/protein-sol/ --mcp-dir tool-mcps/protein_sol_mcp 
```

### Workflow Skill usage
```shell
# List available Workflow Skills
pskill avail

# Show Workflow details
pskill info binder_design

# Install a Workflow Skills
pskill install binder_design

# Uninstall a Workflow Skills
pskill uninstall binder_design
```


## Licences
This software is open-sourced under [![License license](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
