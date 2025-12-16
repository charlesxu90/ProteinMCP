# ProteinMCP: a Tool Universe for Autonomous Protein Design

## TODO list
[ ] Support easy MCP creation 
[ ] Support easy MCP installation
[ ] Create common MCP servers for protein design tasks
[ ] Support Claude code, Gemini cli, Codex, Qwen code, and CodeBuddy
[ ] Support standard workflows: 1) protein sequence analysis; 2) protein structure analysis; 3) train fitness model; 4) binder design; 5) antibody design.

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
## 1. MCP tool usage:

### Create from github repository
```shell
python src/create_mcp.py --github-url https://github.com/jwohlwend/boltz --mcp-dir tool-mcps/boltz_mcp --use-case-filter 'structure prediction with boltz2, affinity prediciton with boltz2, batch structure prediction for protein variants given prepared configs'
```
### Create from local code repository
```shell
python src/create_mcp.py --local-repo-path /opt/rosetta/rosetta.binary.ubuntu.release-371/main/ --mcp-dir tool-mcps/rosetta_mcp --use-case-filter 'Membrane protein structure prediction, Loop modeling, Enzyme design, Protein Design with non-canonical amino acids, Protein-protein docking, Ligand docking, Antibody-antigen docking (SnugDock), Symmetric docking, RNA design, RNA-protein complex prediction, CDR loop modeling, Antibody design, Relax, Structure quality analysis, Clustering, Covalent docking, Ligand design, Peptide modeling, Symmetric assembly modeling, Membrane protein design, Multi-state design, ddG calculations, NMR-guided modeling, Cryo-EM refinement, Comparative modeling'
```

### Install a public MCP
```shell
python src/install_mcp.py list                     # List all MCPs
python src/install_mcp.py list --local             # List local MCPs only
```

### Install a MCP in ProteinMCP
```shell
python src/install_mcp.py install proteinmpnn      # Install with Claude Code (default)
```

### Call MCP service

## Demo cases:

### Protein sequence analysis

### Protein structural analysis

### Train a protein language model on fitness dataset

### Desing a binder to bind target protein

### Design a SARS-COV-2 nanobody


## Licences
This software is open-sourced under [![License license](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
