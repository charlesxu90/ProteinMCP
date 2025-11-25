# ProteinMCP: MCP Tool Universe for protein design

## Install:
```shell
mamba env create -f environment.yml
mamba activate protein-mcp
pip install -r requirements.txt

# Install claude code
npm install -g @anthropic-ai/claude-code

# Install gemini-cli (optional)
npm install -g @google/gemini-cli
```
## Create a new MCP tool:

### Create from github repository
```shell
python src/create_mcp/create_mcp.py  --github-url https://github.com/dauparas/ProteinMPNN  --mcp-dir mcp-servers/proteinmpnn_mcp
```
### Create from local code repository
```shell
python src/create_mcp/create_mcp.py  --local-repo-path /home/xux/Desktop/AlphaVariant/alphavariant/fitness_model/ev_onehot  --mcp-dir mcp-servers/ev_onehot_mcp
```

## 1. MCP tool usage:
- 1.1 Generate MSA for a given sequences with online MSA server.
- 1.2 Predict protein sturcute with AlphaFold3.
- 1.3 Sequence generation with ProteinMPNN.
- 1.4 Train an ev+onehot model for fitness prediction.
- 1.5 Zeroshot fitness prediction with MutComputeX.
- 1.6 Stability preidiction with SpiredStab.

## Demo cases:

### Train a protein language model on in-house dataset

### Engineer GB1 to improve its affinity

### Engineer DHFR to improve its activity

### Design a SARS-COV-2 nanobody


## Licences
This software is open-sourced under [![License license](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
