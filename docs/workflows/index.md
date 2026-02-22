---
title: Workflows
layout: default
nav_order: 5
has_children: true
---

# Workflow Skills

Workflow skills are guided multi-step pipelines that orchestrate multiple MCP servers via Claude Code. Each skill is a Markdown prompt that Claude follows to execute a complete protein engineering workflow.

## Available Workflows

| Skill | Required MCPs | Description |
|-------|---------------|-------------|
| [Fitness Modeling]({{ site.baseurl }}/workflows/fitness-modeling) | msa_mcp, plmc_mcp, ev_onehot_mcp, esm_mcp, prottrans_mcp | Protein fitness prediction with multiple ML backbones |
| [Binder Design]({{ site.baseurl }}/workflows/binder-design) | bindcraft_mcp | De novo binder design using RFdiffusion + ProteinMPNN + AF2 |
| [Nanobody Design]({{ site.baseurl }}/workflows/nanobody-design) | boltzgen_mcp | Nanobody CDR loop design with BoltzGen |

## How Skills Work

1. **Install** a skill with `pskill install <name>` — this auto-installs all required MCPs
2. **Launch** Claude Code and invoke the skill as a slash command (e.g., `/fitness-model`)
3. **Claude executes** the multi-step pipeline, prompting you for inputs as needed
4. **Results** are saved to a results directory with publication-ready visualizations

Skills are Markdown files installed to `.claude/commands/` (slash commands) and `.claude/skills/` (Claude Code skills).

## Quick Start

```bash
# Install a workflow skill
pskill install fitness_modeling

# Launch Claude Code
claude

# Run the skill
> /fitness-model
```
