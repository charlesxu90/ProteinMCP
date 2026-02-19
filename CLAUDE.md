# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ProteinMCP is an agentic AI framework for autonomous protein engineering. It provides a registry of MCP (Model Context Protocol) servers for protein tools, a workflow skill system that orchestrates multi-MCP pipelines, and CLI tools (`pmcp`, `pskill`) to manage everything.

## Build & Install

```bash
mamba env create -f environment.yml
mamba activate protein-mcp
pip install -e .
```

Dev extras (pytest, black, flake8, mypy) are declared in `setup.py` under `extras_require['dev']` but no test suite exists yet.

## CLI Commands

**`pmcp`** — MCP management:
```bash
pmcp avail              # List available MCPs
pmcp status             # Show installed/registered status
pmcp install <name>     # Clone/pull + register with Claude Code
pmcp uninstall <name>   # Remove registration
pmcp info <name>        # Show MCP details
pmcp create             # Auto-generate MCP from GitHub repo (8-step pipeline)
```

**`pskill`** — Workflow skill management:
```bash
pskill avail            # List available skills
pskill install <name>   # Install skill + all required MCPs
pskill uninstall <name> # Remove skill
pskill create           # Interactive skill authoring
```

## Architecture

### Core Abstraction: MCP Dataclass

`src/mcp/mcp.py` defines the `MCP` dataclass with lifecycle methods: `install()`, `register()`, `uninstall()`, `is_installed()`. Status enum: `NOT_INSTALLED → INSTALLED → REGISTERED → BOTH`.

**Two registries** (YAML-backed, managed by `MCPManager` in `src/mcp/mcp_manager.py`):
- `src/mcp/configs/mcps.yaml` — local tool-MCPs (primary)
- `src/mcp/configs/public_mcps.yaml` — community MCPs (cloned to `tool-mcps/public/`)

### MCP Server Pattern

All tool-MCPs use **FastMCP**. Servers live in `tool-mcps/<name>/src/server.py`:
```python
from fastmcp import FastMCP
mcp = FastMCP(name="<name>")
mcp.mount(sub_mcp)  # Tools organized in src/tools/ as mountable sub-servers
```

**Local Python MCPs** (`runtime: python`): installed via `quick_setup.sh` which creates a `./env` venv. Registered as `claude mcp add <name> -- /path/env/bin/python src/server.py`.

**Docker MCPs** (`runtime: docker`): installed via `docker pull <image>`. Registered as `claude mcp add <name> -- docker run -i --rm [--gpus all --ipc=host] -v $CWD:$CWD <image>`. The CWD bind-mount ensures absolute file paths work inside containers.

### Workflow Skills

Skills are **Markdown files** in `workflow-skills/` with structured prompts and MCP tool references. On install, they're copied to both `.claude/commands/` (slash commands) and `.claude/skills/` (Claude Code skills). Required MCPs are declared in `src/skill/configs.yaml`.

Three workflows exist:
- **fitness_modeling** — requires `msa_mcp`, `plmc_mcp`, `ev_onehot_mcp`, `esm_mcp`, `prottrans_mcp`
- **binder_design** — requires `bindcraft_mcp`
- **nanobody_design** — requires `boltzgen_mcp`

### Package Structure

`setup.py` uses an unusual mapping: `package_dir={"proteinmcp": "src"}`. Entry points `pmcp` and `pskill` point to `src/mcp_cli.py:main` and `src/skill_cli.py:main` (Click-based CLIs).

### Status Caching

`src/mcp/status_cache.py` caches MCP status for 5 minutes in `tool-mcps/mcp.status` (JSON with `fcntl` file locking). This avoids repeated `docker image inspect` and filesystem checks during parallel installs.

### Key Conventions

- Skill markdown prompts instruct Claude to convert relative paths to absolute paths before calling MCP tools (required for Docker bind-mounts)
- Docker MCPs use `--gpus all --ipc=host` for GPU/PyTorch shared memory access
- MCP auto-creation pipeline (`pmcp create`) uses LLM-generated prompts from `src/prompts/` across 8 steps
- `.claude/settings.local.json` contains the project permission allowlist for Claude Code tools
