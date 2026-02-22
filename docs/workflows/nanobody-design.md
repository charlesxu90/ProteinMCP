---
title: Nanobody Design
layout: default
parent: Workflows
nav_order: 3
---

# Nanobody CDR Design
{: .no_toc }

Design nanobody CDR regions using BoltzGen with optimized cysteine filtering for single-domain antibodies (VHH).
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

This workflow designs nanobody complementarity-determining regions (CDRs) targeting a protein structure using BoltzGen:

1. **Configuration** — Create a BoltzGen YAML config specifying target structure and optional scaffolds
2. **Design Generation** — Run the nanobody-anything protocol for CDR loop design
3. **Inverse Folding** — Optimize sequences for designed backbones
4. **Filtering** — Cysteine filtering and quality assessment

## Required MCPs

```bash
pskill install nanobody_design
```

This installs: `boltzgen_mcp`

## Configuration

```yaml
TARGET_CIF: "examples/data/target.cif"     # Target protein (CIF or PDB)
TARGET_CHAIN: "A"                           # Target chain ID
RESULTS_DIR: "results/nanobody_design"      # Output directory
NUM_DESIGNS: 10                             # Number of designs
BUDGET: 2                                   # Computational budget (higher = more diverse)
```

## Pipeline Steps

### Step 0: Setup
Create results directory structure.

### Step 1: Prepare Configuration
Create a BoltzGen YAML configuration file specifying the target structure, chain, and optional nanobody scaffolds.

```yaml
entities:
  - file:
      path: /path/to/target.cif
      include:
        - chain:
            id: A
```

### Step 2: Validate Configuration
Verify the config file, check that target files exist and YAML structure is correct.

### Step 3: Submit Design Job
Submit the job using `boltzgen_submit` with the `nanobody-anything` protocol. The protocol is specialized for:
- Single-domain antibodies (VHH)
- CDR loop design
- Cysteine filtering

### Step 4: Monitor Progress
Check job status using `boltzgen_check_status` or `boltzgen_job_status`.

### Step 5: Get Results
Retrieve completed designs — BoltzGen outputs CIF files in subdirectories:
- `intermediate_designs/` — Backbone structures
- `intermediate_designs_inverse_folded/` — Sequence-designed structures

### Step 6: Analyze Designs
Summarize results, identify top candidates, and recommend designs for experimental validation.

## Output Structure

```
RESULTS_DIR/
├── config.yaml                    # BoltzGen configuration
├── designs/
│   ├── config.cif                 # Initial config structure
│   ├── intermediate_designs/      # Backbone designs (CIF)
│   ├── intermediate_designs_inverse_folded/  # Sequence-designed
│   ├── boltzgen_run.log           # Execution log
│   └── job_info.json              # Job metadata
└── logs/
```

## Available Protocols

| Protocol | Use Case |
|----------|----------|
| `nanobody-anything` | Nanobody CDR design (default for this workflow) |
| `protein-anything` | General protein binder design |
| `peptide-anything` | Peptide binder design |
| `antibody-anything` | Full antibody design |

## Run the Workflow

```bash
pskill install nanobody_design
claude
> /nanobody-design
```
