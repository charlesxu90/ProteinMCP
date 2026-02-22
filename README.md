# ProteinMCP: An Agentic AI Framework for Autonomous Protein Engineering

![ProteinMCP overview](./figures/ProteinMCP.png)

## Prerequisites

The following tools must be installed on your system:

| Tool | Purpose | Install Guide |
|------|---------|---------------|
| **Python 3.10+** | Core runtime | [python.org](https://www.python.org/downloads/) |
| **Conda/Mamba** | Environment management | [miniforge](https://github.com/conda-forge/miniforge) |
| **Node.js / npm** | Claude Code CLI | [nodejs.org](https://nodejs.org/) |
| **Docker** (with GPU support) | Containerized MCP servers | [docs.docker.com](https://docs.docker.com/get-docker/) |
| **NVIDIA drivers + nvidia-container-toolkit** | GPU access in Docker | [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) |

Verify your setup:
```bash
python --version       # >= 3.10
conda --version        # or mamba --version
npm --version
docker --version
nvidia-smi             # GPU available
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi  # GPU in Docker
```

## Installation

### Step 1 — Create the Python environment

```bash
mamba env create -f environment.yml
mamba activate protein-mcp
pip install -r requirements.txt
pip install -e .
```

### Step 2 — Install Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code
```

### Step 3 — Verify the installation

```bash
pmcp avail     # List all available MCPs
pskill avail   # List all available workflow skills
claude --version
```

## Supported MCPs

Please find the 38 supported MCPs in [the MCP list](./tool-mcps/README.md).

MCPs come in two runtime types:

| Type | MCPs | Install method |
|------|------|----------------|
| **Python** (local venv) | msa_mcp, alphafold2_mcp, msa_mcp, mmseqs2_mcp, ... | `quick_setup.sh` creates a local `env/` venv |
| **Docker** (GPU container) | esm_mcp, prottrans_mcp, plmc_mcp, ev_onehot_mcp, bindcraft_mcp, boltzgen_mcp | Docker image build or pull |

### Installing MCPs

**Recommended: local Docker build** (faster than pulling from registry):

```bash
# For Docker MCPs — build locally (recommended, avoids slow image pulls)
cd tool-mcps/esm_mcp && docker build -t esm_mcp:latest . && cd ../..
cd tool-mcps/prottrans_mcp && docker build -t prottrans_mcp:latest . && cd ../..
cd tool-mcps/plmc_mcp && docker build -t plmc_mcp:latest . && cd ../..
cd tool-mcps/ev_onehot_mcp && docker build -t ev_onehot_mcp:latest . && cd ../..
cd tool-mcps/bindcraft_mcp && docker build -t bindcraft_mcp:latest . && cd ../..
cd tool-mcps/boltzgen_mcp && docker build -t boltzgen_mcp:latest . && cd ../..
```

Then register with Claude Code:
```bash
# pmcp install detects the local image and skips pulling from registry
pmcp install esm_mcp
pmcp install prottrans_mcp
# ... etc
```

**Alternative: auto-install** (pulls from registry if no local image):
```bash
pmcp install esm_mcp        # Pulls ghcr.io/macromnex/esm_mcp:latest
```

**For Python MCPs** (no Docker needed):
```bash
pmcp install msa_mcp         # Runs quick_setup.sh, creates local venv
```

### Verify installed MCPs
```bash
pmcp status                  # Shows installed/registered status
claude mcp list              # Health-check all registered MCPs
```

## Quick Start

### Option A — Workflow Skills (recommended)

Skills are guided workflows that orchestrate multiple MCP servers via Claude Code.

```bash
# Install a workflow (auto-installs all required MCPs)
pskill install fitness_modeling

# Launch Claude Code and run the skill
claude
> /fitness-model
```

Claude will prompt you for inputs (protein name, data location, etc.) and execute the full pipeline.

**Available skills:**

| Skill | Required MCPs | Description |
|-------|---------------|-------------|
| `fitness_modeling` | msa_mcp, plmc_mcp, ev_onehot_mcp, esm_mcp, prottrans_mcp | Protein fitness prediction |
| `binder_design` | bindcraft_mcp | De novo binder design (RFdiffusion + ProteinMPNN + AF2) |
| `nanobody_design` | boltzgen_mcp | Nanobody CDR loop design with BoltzGen |

### Option B — Jupyter Notebooks

Standalone notebooks for step-by-step exploration. Each notebook installs dependencies, registers MCPs, and walks through the full workflow.

| Notebook | Workflow | Description |
|----------|----------|-------------|
| [fitness_modeling.ipynb](./notebooks/fitness_modeling.ipynb) | Fitness Prediction | MSA, PLMC, EV+OneHot, ESM, ProtTrans, and visualization |
| [binder_design.ipynb](./notebooks/binder_design.ipynb) | Binder Design | De novo binder design with BindCraft |
| [nanobody_design.ipynb](./notebooks/nanobody_design.ipynb) | Nanobody Design | Nanobody CDR loop design with BoltzGen |

## Usage

### MCP management
```bash
pmcp avail                # List all available MCPs
pmcp info msa_mcp         # Show MCP details
pmcp install msa_mcp      # Install an MCP
pmcp uninstall msa_mcp    # Uninstall an MCP
pmcp status               # Show installed/registered status
```

### MCP creation
```bash
# Create from GitHub repository
pmcp create --github-url https://github.com/jwohlwend/boltz \
  --mcp-dir tool-mcps/boltz_mcp \
  --use-case-filter 'structure prediction with boltz2, affinity prediction with boltz2'

# Create from local directory
pmcp create --local-repo-path tool-mcps/protein_sol_mcp/scripts/protein-sol/ \
  --mcp-dir tool-mcps/protein_sol_mcp
```

### Workflow Skill management
```bash
pskill avail              # List available workflow skills
pskill info binder_design # Show workflow details
pskill install binder_design   # Install skill + all required MCPs
pskill uninstall binder_design # Remove skill
```

## Licenses
This software is open-sourced under [![License](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
