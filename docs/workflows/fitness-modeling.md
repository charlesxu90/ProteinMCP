---
title: Fitness Modeling
layout: default
parent: Workflows
nav_order: 1
---

# Protein Fitness Prediction
{: .no_toc }

Build and compare protein fitness prediction models using multiple backbone architectures.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

This workflow predicts the fitness landscape of protein variants using five ML approaches:

1. **MSA generation** via ColabFold/MMseqs2
2. **PLMC** evolutionary coupling model
3. **EV+OneHot** combined evolutionary + one-hot encoding
4. **ESM** protein language model embeddings (ESM2-650M, ESM2-3B)
5. **ProtTrans** transformer embeddings (ProtT5-XL, ProtAlbert)

All models are evaluated with 5-fold cross-validation and compared in a publication-ready four-panel figure.

## Required MCPs

```bash
pskill install fitness_modeling
```

This installs: `msa_mcp`, `plmc_mcp`, `ev_onehot_mcp`, `esm_mcp`, `prottrans_mcp`

## Configuration

```yaml
PROTEIN_NAME: "MyProtein"
DATA_DIR: "examples/my_project"
WT_FASTA: "examples/my_project/wt.fasta"       # Wild-type sequence
DATA_CSV: "examples/my_project/data.csv"        # Must have 'seq' and 'log_fitness' columns
RESULTS_DIR: "results/fitness_modeling"
```

### Input Data Format

Your `data.csv` must contain:
- `seq` — Full protein sequence
- `log_fitness` — Log-transformed fitness value (target)

## Pipeline Steps

### Step 0: Setup
Create results directory and copy input files.

### Step 1: Generate MSA
Use `msa_mcp` to generate a multiple sequence alignment from the wild-type sequence via ColabFold/MMseqs2 server.

### Step 2: Build PLMC Model
Convert MSA from A3M to A2M format, then build an evolutionary coupling model using `plmc_mcp`.

### Step 3: EV+OneHot Model
Train a combined evolutionary coupling + one-hot encoding model using `ev_onehot_mcp` with 5-fold cross-validation.

### Step 4: ESM Models
Extract ESM embeddings (ESM2-650M and ESM2-3B) and train regression heads (SVR, XGBoost, KNN) using `esm_mcp`.

### Step 5: ProtTrans Models
Extract ProtTrans embeddings (ProtT5-XL, ProtAlbert) and train regression heads using `prottrans_mcp`.

### Step 6: Compare and Visualize
Aggregate all model results and generate a four-panel figure:
1. **Model Performance Comparison** — Bar chart of best Spearman rho per backbone
2. **Predicted vs Observed** — Scatter plot for the best model
3. **Head Model Comparison** — Table of all backbone + head combinations
4. **Execution Timeline** — Gantt chart of step timings

## Output Structure

```
RESULTS_DIR/
├── msa.a3m                         # Generated MSA
├── plmc/                           # PLMC model files
├── metrics_summary.csv             # EV+OneHot results
├── esm2_650M_*/                    # ESM model outputs
├── esm2_3B_*/                      # ESM-3B model outputs
├── ProtT5-XL_*/                    # ProtTrans model outputs
├── all_models_comparison.csv       # All model results combined
├── fitness_modeling_summary.png    # Four-panel summary figure
└── fitness_modeling_summary.pdf    # Publication-ready figure
```

## Model Performance Reference

| Model | Typical Spearman | Best Use Case |
|-------|-----------------|---------------|
| EV+OneHot | 0.20–0.35 | Baseline, interpretable |
| ESM2-650M | 0.15–0.25 | Fast, good balance |
| ESM2-3B | 0.18–0.28 | Higher accuracy |
| ProtT5-XL | 0.15–0.25 | Alternative to ESM |

## Run the Workflow

```bash
pskill install fitness_modeling
claude
> /fitness-model
```
