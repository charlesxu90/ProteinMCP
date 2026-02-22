---
title: Installation
layout: default
nav_order: 2
---

# Installation
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

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

---

## Step 1 — Create the Python Environment

```bash
mamba env create -f environment.yml
mamba activate protein-mcp
pip install -r requirements.txt
pip install -e .
```

## Step 2 — Install Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code
```

## Step 3 — Verify the Installation

```bash
pmcp avail     # List all available MCPs
pskill avail   # List all available workflow skills
claude --version
```

---

## Installing MCPs

MCPs come in two runtime types:

| Type | MCPs | Install method |
|------|------|----------------|
| **Python** (local venv) | msa_mcp, alphafold2_mcp, mmseqs2_mcp, ... | `quick_setup.sh` creates a local `env/` venv |
| **Docker** (GPU container) | esm_mcp, prottrans_mcp, plmc_mcp, ev_onehot_mcp, bindcraft_mcp, boltzgen_mcp | Docker image build or pull |

### Docker MCPs (local build recommended)

Local builds are faster than pulling from the registry:

```bash
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
pmcp install plmc_mcp
pmcp install ev_onehot_mcp
pmcp install bindcraft_mcp
pmcp install boltzgen_mcp
```

### Auto-install (pulls from registry)

```bash
pmcp install esm_mcp        # Pulls ghcr.io/macromnex/esm_mcp:latest
```

### Python MCPs (no Docker needed)

```bash
pmcp install msa_mcp         # Runs quick_setup.sh, creates local venv
```

### Verify Installed MCPs

```bash
pmcp status                  # Shows installed/registered status
claude mcp list              # Health-check all registered MCPs
```
