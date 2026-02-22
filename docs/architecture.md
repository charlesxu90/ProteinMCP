---
title: Architecture
layout: default
nav_order: 7
---

# Architecture
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Core Abstraction: MCP Dataclass

`src/mcp/mcp.py` defines the `MCP` dataclass with lifecycle methods: `install()`, `register()`, `uninstall()`, `is_installed()`.

Status transitions:

```
NOT_INSTALLED → INSTALLED → REGISTERED → BOTH
```

## Registries

Two YAML-backed registries managed by `MCPManager` (`src/mcp/mcp_manager.py`):

| Registry | File | Purpose |
|----------|------|---------|
| Local tool-MCPs | `src/mcp/configs/mcps.yaml` | 24 in-house MCPs |
| Public MCPs | `src/mcp/configs/public_mcps.yaml` | 14 community MCPs (cloned to `tool-mcps/public/`) |

## MCP Server Pattern

All tool-MCPs use **FastMCP**. Servers live in `tool-mcps/<name>/src/server.py`:

```python
from fastmcp import FastMCP
mcp = FastMCP(name="<name>")
mcp.mount(sub_mcp)  # Tools organized in src/tools/ as mountable sub-servers
```

### Python MCPs (`runtime: python`)

Installed via `quick_setup.sh` which creates a local `./env` venv. Registered as:

```
claude mcp add <name> -- /path/env/bin/python src/server.py
```

### Docker MCPs (`runtime: docker`)

Installed via `docker pull <image>` or local `docker build`. Registered as:

```
claude mcp add <name> -- docker run -i --rm --gpus all --ipc=host -v $CWD:$CWD <image>
```

The `$CWD` bind-mount ensures absolute file paths work inside containers. `--gpus all --ipc=host` provides GPU access and shared memory for PyTorch.

## Workflow Skills

Skills are **Markdown files** in `workflow-skills/` with structured prompts and MCP tool references. On install, they are copied to:

- `.claude/commands/` — slash commands (e.g., `/fitness-model`)
- `.claude/skills/` — Claude Code skills

Required MCPs are declared in `src/skill/configs.yaml`.

## Package Structure

`setup.py` uses a custom mapping:

```python
package_dir={"proteinmcp": "src"}
```

Entry points:
- `pmcp` → `src/mcp_cli.py:main` (Click-based CLI)
- `pskill` → `src/skill_cli.py:main` (Click-based CLI)

## Status Caching

`src/mcp/status_cache.py` caches MCP status for 5 minutes in `tool-mcps/mcp.status` (JSON with `fcntl` file locking). This avoids repeated `docker image inspect` and filesystem checks during parallel installs.

## MCP Auto-Creation Pipeline

`pmcp create` runs an 8-step LLM-powered pipeline (prompts in `src/prompts/`) that:

1. Analyzes a GitHub repository
2. Identifies use cases
3. Generates FastMCP server code
4. Creates Dockerfiles and setup scripts
5. Validates the result

## Key Conventions

- Skill prompts instruct Claude to convert relative paths to absolute paths before calling MCP tools (required for Docker bind-mounts)
- Docker MCPs use `--gpus all --ipc=host` for GPU/PyTorch shared memory access
- `.claude/settings.local.json` contains the project permission allowlist for Claude Code tools
