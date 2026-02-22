---
title: Quick Start
layout: default
nav_order: 3
---

# Quick Start
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Option A — Workflow Skills (Recommended)

Skills are guided workflows that orchestrate multiple MCP servers via Claude Code.

```bash
# Install a workflow (auto-installs all required MCPs)
pskill install fitness_modeling

# Launch Claude Code and run the skill
claude
> /fitness-model
```

Claude will prompt you for inputs (protein name, data location, etc.) and execute the full pipeline.

### Available Skills

| Skill | Required MCPs | Description |
|-------|---------------|-------------|
| `fitness_modeling` | msa_mcp, plmc_mcp, ev_onehot_mcp, esm_mcp, prottrans_mcp | Protein fitness prediction |
| `binder_design` | bindcraft_mcp | De novo binder design (RFdiffusion + ProteinMPNN + AF2) |
| `nanobody_design` | boltzgen_mcp | Nanobody CDR loop design with BoltzGen |

---

## Option B — Jupyter Notebooks

Standalone notebooks for step-by-step exploration. Each notebook installs dependencies, registers MCPs, and walks through the full workflow.

| Notebook | Workflow | Description |
|----------|----------|-------------|
| [fitness_modeling.ipynb](https://github.com/charlesxu90/ProteinMCP/blob/main/notebooks/fitness_modeling.ipynb) | Fitness Prediction | MSA, PLMC, EV+OneHot, ESM, ProtTrans, and visualization |
| [binder_design.ipynb](https://github.com/charlesxu90/ProteinMCP/blob/main/notebooks/binder_design.ipynb) | Binder Design | De novo binder design with BindCraft |
| [nanobody_design.ipynb](https://github.com/charlesxu90/ProteinMCP/blob/main/notebooks/nanobody_design.ipynb) | Nanobody Design | Nanobody CDR loop design with BoltzGen |
