---
title: pmcp
layout: default
parent: CLI Reference
nav_order: 1
---

# pmcp — MCP Management
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

`pmcp` manages MCP (Model Context Protocol) servers — listing, installing, registering with Claude Code, and creating new MCPs from GitHub repositories.

## Commands

### `pmcp avail`

List all available MCPs.

```bash
pmcp avail
```

### `pmcp info <name>`

Show details about an MCP including tools, runtime type, and description.

```bash
pmcp info msa_mcp
```

### `pmcp install <name>`

Install an MCP server and register it with Claude Code.

- **Python MCPs**: Runs `quick_setup.sh` to create a local `env/` venv
- **Docker MCPs**: Pulls or detects a local Docker image, then registers

```bash
pmcp install msa_mcp          # Python MCP
pmcp install esm_mcp          # Docker MCP
```

### `pmcp uninstall <name>`

Remove an MCP registration from Claude Code.

```bash
pmcp uninstall msa_mcp
```

### `pmcp status`

Show installed/registered status for all MCPs.

```bash
pmcp status
```

### `pmcp create`

Auto-generate an MCP server from a GitHub repository using an 8-step LLM-powered pipeline.

```bash
# Create from GitHub repository
pmcp create --github-url https://github.com/jwohlwend/boltz \
  --mcp-dir tool-mcps/boltz_mcp \
  --use-case-filter 'structure prediction with boltz2, affinity prediction with boltz2'

# Create from local directory
pmcp create --local-repo-path tool-mcps/protein_sol_mcp/scripts/protein-sol/ \
  --mcp-dir tool-mcps/protein_sol_mcp
```

The pipeline analyzes the repository, identifies use cases, generates server code with FastMCP, creates Dockerfiles, and validates the result.
