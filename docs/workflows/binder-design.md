---
title: Binder Design
layout: default
parent: Workflows
nav_order: 2
---

# De Novo Binder Design
{: .no_toc }

Design protein binders using BindCraft with GPU-accelerated deep learning.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

This workflow designs de novo protein binders against a target protein using BindCraft's integrated pipeline:

1. **AF2 Hallucination** — Generate binder backbone conformations guided by target structure
2. **MPNN Sequence Design** — Optimize amino acid sequences for designed backbones
3. **AF2 Prediction** — Validate binder-target complexes with structure prediction
4. **PyRosetta Analysis** — Score interface quality, energy, and structural metrics

## Required MCPs

```bash
pskill install binder_design
```

This installs: `bindcraft_mcp`

## Configuration

```yaml
TARGET_PDB: "examples/data/target.pdb"     # Target protein PDB file
TARGET_CHAINS: "A"                          # Target chains to design binders for
BINDER_LENGTH: 130                          # Length of designed binder
RESULTS_DIR: "results/binder_design"        # Output directory
NUM_DESIGNS: 3                              # Number of designs to generate
HOTSPOT_RESIDUES: null                      # Optional: specific residues to target
```

### Target PDB Requirements
- Clean PDB file with target protein structure
- All heteroatoms and waters removed (unless needed)
- Chain IDs properly assigned

## Pipeline Steps

### Step 1: Explore Configurations
Use `generate_config` to see available settings and analyze the target structure.

### Step 2: Setup Results Directory
Create the output directory structure.

### Step 3: Generate Configuration
Analyze the target PDB and generate an optimized BindCraft configuration including `target_settings.json`, design filters, and advanced settings.

### Step 4: Submit Design Job
Submit an asynchronous design job. BindCraft runs RFdiffusion for backbone generation, ProteinMPNN for sequence design, and AlphaFold2 for validation.

### Step 5: Monitor Progress
Check job status using `bindcraft_check_status`. The job reports completed trajectories, accepted designs, and rejected designs.

### Step 6: Get Results
Retrieve completed designs with quality metrics (pLDDT, pAE, interface scores).

### Step 7: Visualize Results
Generate publication-ready figures:
- pLDDT comparison bar chart
- Interface pAE scores
- Quality scatter plot (pLDDT vs pAE)
- Design ranking by composite score
- Metrics summary table
- Execution timeline

## Output Structure

```
RESULTS_DIR/
├── config/
│   ├── target_settings.json
│   ├── default_filters.json
│   └── job_output/
│       ├── Accepted/Ranked/       # Final ranked PDB designs
│       ├── Rejected/
│       ├── final_design_stats.csv
│       └── bindcraft_run.log
└── designs/
```

## Quality Thresholds

| Metric | Threshold | Direction |
|--------|-----------|-----------|
| pLDDT | ≥ 80 | Higher is better |
| pAE | ≤ 5 | Lower is better |
| i_pAE (interface) | ≤ 10 | Lower is better |
| i_pTM (interface) | ≥ 0.6 | Higher is better |

## Run the Workflow

```bash
pskill install binder_design
claude
> /binder-design
```
