---
title: pskill
layout: default
parent: CLI Reference
nav_order: 2
---

# pskill — Workflow Skill Management
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

`pskill` manages workflow skills — Markdown-based guided pipelines that orchestrate multiple MCP servers via Claude Code.

## Commands

### `pskill avail`

List all available workflow skills.

```bash
pskill avail
```

### `pskill info <name>`

Show details about a workflow skill including required MCPs and description.

```bash
pskill info binder_design
```

### `pskill install <name>`

Install a workflow skill and all its required MCPs. The skill is copied to both `.claude/commands/` (slash commands) and `.claude/skills/` (Claude Code skills).

```bash
pskill install fitness_modeling    # Installs skill + msa_mcp, plmc_mcp, ev_onehot_mcp, esm_mcp, prottrans_mcp
pskill install binder_design       # Installs skill + bindcraft_mcp
pskill install nanobody_design     # Installs skill + boltzgen_mcp
```

### `pskill uninstall <name>`

Remove a workflow skill.

```bash
pskill uninstall fitness_modeling
```

### `pskill create`

Interactive skill authoring — create a new workflow skill with MCP tool references.

```bash
pskill create
```
