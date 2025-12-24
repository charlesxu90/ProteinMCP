# Protein Fitness Prediction Skill

A comprehensive workflow for building and comparing protein fitness prediction models using multiple backbone architectures.

---

## Prerequisites

Before running this workflow, install the skill and all required MCPs:

```bash
pskill install fitness_modeling
```

This will install the following MCP servers:
- `msa_mcp` - Multiple sequence alignment generation
- `plmc_mcp` - PLMC evolutionary coupling model
- `ev_onehot_mcp` - EV+OneHot feature combination
- `esm_mcp` - ESM protein language model embeddings
- `prottrans_mcp` - ProtTrans transformer embeddings

**Verify MCPs are installed:**
```bash
pmcp status
```

---

## Configuration Parameters

Before running this workflow, set the following parameters:

```yaml
# Required Inputs
PROTEIN_NAME: "MyProtein"                       # Name of your protein (used for naming files)
DATA_DIR: "@examples/my_project"                # Input directory containing data files
WT_FASTA: "@examples/my_project/wt.fasta"       # Wild-type sequence file
DATA_CSV: "@examples/my_project/data.csv"       # Fitness data with 'seq' and 'log_fitness' columns

# Output Directories
RESULTS_DIR: "@results/fitness_modeling"        # Output directory for all results and models
MSA_FILE: "@results/fitness_modeling/msa.a3m"   # MSA file (will be generated if not exists)

# Optional Settings
HEAD_MODELS: ["svr", "knn", "xgboost"]          # Head models to try
ESM_BACKBONES: ["esm2_t33_650M_UR50D", "esm2_t36_3B_UR50D"]  # ESM backbones
ESM1V_ENSEMBLE: true                             # Use ESM1v ensemble (1-5)
PROTTRANS_BACKBONES: ["ProtT5-XL", "ProtAlbert"] # ProtTrans backbones
```

**Data CSV Format:**
Your data.csv should contain at minimum:
- `seq`: Full protein sequence
- `log_fitness`: Log-transformed fitness value (target)

**Directory Structure:**
```
DATA_DIR/                    # Input data (read-only)
├── wt.fasta                 # Wild-type sequence
└── data.csv                 # Fitness data

RESULTS_DIR/                 # All outputs go here
├── msa.a3m                  # Generated MSA
├── plmc/                    # PLMC model files
├── sequences.fasta          # Extracted sequences for embeddings
├── data.csv                 # Copy of input data (for training tools)
├── wt.fasta                 # Copy of wild-type (for training tools)
├── metrics_summary.csv      # EV+OneHot results
├── esm2_650M_*/             # ESM model outputs
├── esm2_3B_*/               # ESM-3B model outputs
├── ProtT5-XL_*/             # ProtTrans model outputs
├── ProtAlbert_*/            # ProtAlbert model outputs
├── backbone_comparison.png  # Final comparison figure
└── backbone_comparison.pdf  # Publication-ready figure
```

---

## Step 0: Setup Results Directory

Before starting, create the results directory and copy input files.

**Prompt:**
> Please setup the results directory at {RESULTS_DIR} for protein {PROTEIN_NAME}. Copy the input files from {DATA_DIR} (wt.fasta and data.csv) to the results directory.
> Please convert the relative path to absolute path before executing.

**Implementation Notes:**
```bash
mkdir -p {RESULTS_DIR}
cp {DATA_DIR}/wt.fasta {RESULTS_DIR}/
cp {DATA_DIR}/data.csv {RESULTS_DIR}/
```

---

## Step 1: Generate MSA with msa_mcp (if needed)

Use the MSA MCP server to generate multiple sequence alignment.

**Prompt:**
> Can you obtain the MSA for {PROTEIN_NAME} from {WT_FASTA} using msa mcp and save it to {RESULTS_DIR}/{PROTEIN_NAME}.a3m.
> Please convert the relative path to absolute path before calling the MCP servers.

**Implementation Notes:**
- Use the `mcp__msa_mcp__generate_msa` tool
- Required parameters: `sequence` (from WT_FASTA), `output_filename` (absolute path to {RESULTS_DIR}/{PROTEIN_NAME}.a3m), `job_name` (PROTEIN_NAME)
- The tool returns MSA depth and length information

---

## Step 2: Build PLMC Evolutionary Coupling Model

Use the PLMC MCP server to build an evolutionary coupling model.

**Prompt:**
> I have created an a3m file in {RESULTS_DIR}/{PROTEIN_NAME}.a3m. Can you help build an EV model using plmc mcp and save it to {RESULTS_DIR}/plmc directory. The wild-type sequence is {WT_FASTA}.
> Please convert the relative path to absolute path before calling the MCP servers.

**Implementation Notes:**

1. **Create the plmc directory first:**
   ```bash
   mkdir -p {RESULTS_DIR}/plmc
   ```

2. **Convert A3M to A2M format:**
   - Use `mcp__plmc_mcp__plmc_convert_a3m_to_a2m`
   - Parameters: `a3m_file_path` ({RESULTS_DIR}/{PROTEIN_NAME}.a3m), `out_prefix` ({RESULTS_DIR}/plmc/{PROTEIN_NAME})

3. **Generate PLMC model:**
   - Use `mcp__plmc_mcp__plmc_generate_model`
   - Parameters: `alignment_path` (the .a2m file), `focus_seq_id` (PROTEIN_NAME), `out_prefix` ({RESULTS_DIR}/plmc/{PROTEIN_NAME})

4. **CRITICAL: Create symlinks for ev_onehot_mcp compatibility:**
   The ev_onehot_mcp expects files named `uniref100.model_params` and `uniref100.EC`. Create symlinks:
   ```bash
   cd {RESULTS_DIR}/plmc
   ln -sf {PROTEIN_NAME}.model_params uniref100.model_params
   ln -sf {PROTEIN_NAME}.EC uniref100.EC
   ```

**Expected Output:**
- `{RESULTS_DIR}/plmc/{PROTEIN_NAME}.a2m` - Converted alignment
- `{RESULTS_DIR}/plmc/{PROTEIN_NAME}.model_params` - Model parameters
- `{RESULTS_DIR}/plmc/{PROTEIN_NAME}.EC` - Evolutionary couplings
- `{RESULTS_DIR}/plmc/uniref100.model_params` - Symlink (required by ev_onehot_mcp)
- `{RESULTS_DIR}/plmc/uniref100.EC` - Symlink (required by ev_onehot_mcp)

---

## Step 3: Build EV+OneHot Model

Use the EV+OneHot MCP server to combine evolutionary features with one-hot encoding.

**Prompt:**
> I have created a plmc model in directory {RESULTS_DIR}/plmc. Can you help build an EV+OneHot model using ev_onehot_mcp and save it to {RESULTS_DIR}/ directory. The wild-type sequence is {RESULTS_DIR}/wt.fasta, and the dataset is {RESULTS_DIR}/data.csv.
> Please convert the relative path to absolute path before calling the MCP servers.

**Implementation Notes:**
- Use `mcp__ev_onehot_mcp__ev_onehot_train_fitness_predictor`
- Parameters:
  - `data_dir`: {RESULTS_DIR} (must contain plmc/ subdirectory with uniref100.model_params and uniref100.EC, plus wt.fasta)
  - `train_data_path`: {RESULTS_DIR}/data.csv
  - `out_prefix`: {RESULTS_DIR}/ev_onehot
  - `cross_val`: true

**Expected Output:**
- `{RESULTS_DIR}/metrics_summary.csv` - Cross-validation results with columns: stage, fold, n_train, n_test, spearman_correlation
- `{RESULTS_DIR}/ridge_model.joblib` - Trained model

---

## Step 4: Build ESM Models

Use the ESM MCP server for deep learning embeddings.

### 4.1 Extract ESM Embeddings

Before training, extract embeddings for all sequences in data.csv.

**For ESM2-650M:**
- Use `mcp__esm_mcp__extract_protein_embeddings` with:
  - `input_file`: Path to FASTA file with sequences
  - `output_dir`: {RESULTS_DIR}/esm2_t33_650M_UR50D
  - `model`: "esm2_t33_650M_UR50D"
  - `include_per_tok`: false (use mean representations)

**Alternative (if MCP tool fails):** Run esm-extract directly:
```bash
# First create sequences.fasta from data.csv (extract unique sequences)
# Then run:
mkdir -p {RESULTS_DIR}/esm2_t33_650M_UR50D
esm-extract esm2_t33_650M_UR50D {RESULTS_DIR}/sequences.fasta {RESULTS_DIR}/esm2_t33_650M_UR50D --repr_layers 33 --include mean
```

**Creating sequences.fasta from data.csv:**
```python
import pandas as pd
from pathlib import Path

csv_path = Path("{RESULTS_DIR}/data.csv")
df = pd.read_csv(csv_path)
unique_sequences = df['seq'].unique()
seq_ids = [f"seq_{i}" for i in range(len(unique_sequences))]

fasta_path = Path("{RESULTS_DIR}") / "sequences.fasta"
with open(fasta_path, 'w') as f:
    for seq_id, seq in zip(seq_ids, unique_sequences):
        f.write(f">{seq_id}\n{seq}\n")
```

### 4.2 Train ESM2-650M Models

**Prompt:**
> Can you help train ESM models for data in {RESULTS_DIR}/ and save them to {RESULTS_DIR}/esm2_650M_{head_model} using the esm mcp server with svr, xgboost, and knn as the head models.
> Please convert the relative path to absolute path before calling the MCP servers.
> Obtain the embeddings if they are not created.

**Implementation Notes:**
- The training tool expects in input_dir ({RESULTS_DIR}):
  - `data.csv` - fitness data
  - `sequences.fasta` - extracted sequences
  - `esm2_t33_650M_UR50D/` directory with .pt embedding files

### 4.3 ESM2-3B Models

**Prompt:**
> Can you help train ESM models for data in {RESULTS_DIR}/ and save them to {RESULTS_DIR}/esm2_3B_{head_model} using the esm mcp server with svr, xgboost, and knn as the head models and esm2_t36_3B_UR50D as the backbone.
> Please convert the relative path to absolute path before calling the MCP servers.
> Obtain the embeddings if they are not created.

Same process but use `esm2_t36_3B_UR50D` as backbone and `--repr_layers 36`.

**Expected Output per model:**
- `{RESULTS_DIR}/{backbone}_{head}/training_summary.csv` - Training metrics with columns: backbone_model, head_model, mean_cv_spearman, std_cv_spearman
- `{RESULTS_DIR}/{backbone}_{head}/final_model/` - Trained model files

---

## Step 5: Build ProtTrans Models

Use the ProtTrans MCP server for transformer-based embeddings.

### 5.1 Extract ProtTrans Embeddings

**Prompt:**
> Extract ProtTrans embeddings for the sequences in {RESULTS_DIR}/data.csv using ProtT5-XL and ProtAlbert models.
> Please convert the relative path to absolute path before calling the MCP servers.

**Implementation Notes:**
- Use `mcp__prottrans_mcp__prottrans_extract_embeddings`
- Parameters:
  - `csv_path`: {RESULTS_DIR}/data.csv
  - `model_name`: "ProtT5-XL" or "ProtAlbert"
  - `seq_col`: "seq"

This creates:
- `{RESULTS_DIR}/ProtT5-XL/ProtT5-XL.npy` - Embeddings file
- `{RESULTS_DIR}/ProtAlbert/ProtAlbert.npy` - Embeddings file

### 5.2 Train ProtTrans Models

**Prompt:**
> Can you help train ProtTrans models for data in {RESULTS_DIR}/ and save them to {RESULTS_DIR}/{backbone_model}_{head_model} using the prottrans mcp server with ProtT5-XL and ProtAlbert as backbone_models and knn, xgboost, and svr as the head models.
> Please convert the relative path to absolute path before calling the MCP servers.
> Create the embeddings if they are not created.

**Implementation Notes:**
- Use `mcp__prottrans_mcp__prottrans_train_fitness_model`
- Parameters:
  - `input_dir`: {RESULTS_DIR}
  - `output_dir`: {RESULTS_DIR}/{backbone}_{head}
  - `backbone_model`: "ProtT5-XL" or "ProtAlbert"
  - `head_model`: "svr", "knn", or "xgboost"
  - `target_col`: "log_fitness"

**Expected Output per model:**
- `{RESULTS_DIR}/{backbone}_{head}/training_summary.csv` - Training metrics with columns: cv_mean, cv_std, etc.
- `{RESULTS_DIR}/{backbone}_{head}/final_model/` - Trained model files

---

## Step 6: Compare and Visualize Results

After training all models, create a comparison figure showing Spearman correlations with error bars.

### 6.1 Collect Results

**Prompt:**
> I have the metrics for EV+OneHot and different ESM and ProtTrans models in {RESULTS_DIR}/metrics_summary.csv and {RESULTS_DIR}/*/training_summary.csv. Can you:
> 1. Parse all training_summary.csv files to extract CV Spearman correlations
> 2. Select the best head model for each backbone
> 3. Create a comparison table with mean and standard deviation
> 4. Generate a bar chart visualization and save to {RESULTS_DIR}/

### 6.2 Results Collection Code

**IMPORTANT:** Different model types have different CSV formats:

```python
import os
import pandas as pd

results_dir = "{RESULTS_DIR}"
results = []

# EV+OneHot - metrics_summary.csv format:
# stage,fold,n_train,n_test,spearman_correlation
ev_metrics = pd.read_csv(os.path.join(results_dir, "metrics_summary.csv"))
cv_mean = ev_metrics[ev_metrics['fold'] == 'mean']['spearman_correlation'].values[0]
cv_std = ev_metrics[ev_metrics['fold'] == 'std']['spearman_correlation'].values[0]
results.append({'backbone': 'EV+OneHot', 'head': 'ridge', 'mean_cv_spearman': cv_mean, 'std_cv_spearman': cv_std})

# ESM models - training_summary.csv format:
# backbone_model,head_model,mean_cv_spearman,std_cv_spearman
for dir_name in os.listdir(results_dir):
    summary_file = os.path.join(results_dir, dir_name, "training_summary.csv")
    if os.path.exists(summary_file):
        df = pd.read_csv(summary_file)
        # Handle different column names between ESM and ProtTrans
        if 'mean_cv_spearman' in df.columns:
            mean_sp = df['mean_cv_spearman'].values[0]
            std_sp = df['std_cv_spearman'].values[0]
        elif 'cv_mean' in df.columns:
            mean_sp = df['cv_mean'].values[0]
            std_sp = df['cv_std'].values[0]
        # Parse backbone and head from directory name
        # ...
```

### 6.3 Visualization Code

**NOTE:** Use ev_onehot_mcp environment for visualization (has matplotlib/seaborn):

```python
# Run with: /path/to/ev_onehot_mcp/env/bin/python

import matplotlib
matplotlib.use('Agg')  # Required for non-interactive mode
import matplotlib.pyplot as plt
import pandas as pd

def prettify_ax(ax):
    """Make axes more pleasant to look at"""
    for i, spine in enumerate(ax.spines.values()):
        if i == 3 or i == 1:
            spine.set_visible(False)
    ax.set_frameon = True
    ax.tick_params(direction='out', length=3, color='k')
    ax.set_axisbelow(True)

# Load comparison table
best_results = pd.read_csv("{RESULTS_DIR}/backbone_comparison_table.csv")

# Create visualization
fig = plt.figure(figsize=(8, 5))
ax = fig.add_subplot(111)
prettify_ax(ax)

methods = best_results['backbone'].tolist()
spearman = best_results['mean_cv_spearman'].tolist()
spearman_std = best_results['std_cv_spearman'].tolist()
head_models = best_results['head'].tolist()

# Create bar chart
colors = ['#2ecc71', '#3498db', '#e74c3c', '#9b59b6', '#f39c12']
bars = ax.bar(methods, spearman, color=colors[:len(methods)], alpha=0.85)
ax.errorbar(methods, spearman, yerr=spearman_std, fmt='none', ecolor='black', capsize=5)

# Add head model labels
for bar, head in zip(bars, head_models):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height()/2,
            f'({head})', ha='center', va='center', fontsize=9, color='white', fontweight='bold')

ax.set_title('Protein Fitness Prediction: {PROTEIN_NAME}', fontsize=13, fontweight='bold')
ax.set_ylabel('Spearman Correlation (5-fold CV)', fontsize=11)
ax.set_xlabel('Model Backbone', fontsize=11)
ax.set_ylim([0, max(spearman) * 1.35])
ax.set_xticklabels(methods, rotation=25, ha='right')
ax.yaxis.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
fig.savefig("{RESULTS_DIR}/backbone_comparison.pdf", dpi=300, bbox_inches='tight')
fig.savefig("{RESULTS_DIR}/backbone_comparison.png", dpi=300, bbox_inches='tight')
```

**Expected Output:**
- `{RESULTS_DIR}/backbone_comparison.pdf` - Vector format for publication
- `{RESULTS_DIR}/backbone_comparison.png` - Raster format for preview
- `{RESULTS_DIR}/backbone_comparison_table.csv` - Summary table with best models
- `{RESULTS_DIR}/all_models_comparison.csv` - All tested models

---

## Quick Start Template

For a new protein fitness prediction project:

```bash
# 1. Install the skill and all required MCPs
pskill install fitness_modeling

# 2. Set your parameters
PROTEIN_NAME="TEVp_S219V"
DATA_DIR="@examples/case3_fitness_modeling"
RESULTS_DIR="@results/fitness_modeling"

# 3. Run the workflow steps (Step 0-6 above)

# 4. Uninstall when done (optional)
pskill uninstall fitness_modeling
```

---

## Model Performance Reference

Based on typical benchmarks, expected performance ranges (CV Spearman):

| Model | Typical Range | Best Use Case |
|-------|---------------|---------------|
| EV+OneHot | 0.20-0.35 | Baseline, interpretable |
| ESM2-650M | 0.15-0.25 | Fast, good balance |
| ESM2-3B | 0.18-0.28 | Higher accuracy |
| ESM1v ensemble | 0.15-0.25 | Uncertainty estimation |
| ProtT5-XL | 0.15-0.25 | Alternative to ESM |
| ProtAlbert | 0.08-0.15 | Lightweight option |

**Recommended Head Models:**
- **SVR**: Most stable, best for small datasets
- **XGBoost**: Higher potential but prone to overfitting
- **KNN**: Simple baseline, good for well-clustered data

---

## Cleanup

When you're done with the workflow, uninstall the skill and all its MCPs:

```bash
pskill uninstall fitness_modeling
```

To check currently installed MCPs:

```bash
pmcp status
```

---

## Troubleshooting

### Common Issues

1. **PLMC Directory Not Found**
   - Ensure you create the plmc directory before running conversion:
     ```bash
     mkdir -p {RESULTS_DIR}/plmc
     ```

2. **EV+OneHot "uniref100.model_params not found"**
   - Create symlinks in the plmc directory:
     ```bash
     cd {RESULTS_DIR}/plmc
     ln -sf {PROTEIN_NAME}.model_params uniref100.model_params
     ln -sf {PROTEIN_NAME}.EC uniref100.EC
     ```

3. **EV+OneHot "wt.fasta not found"**
   - Ensure wt.fasta is copied to RESULTS_DIR:
     ```bash
     cp {DATA_DIR}/wt.fasta {RESULTS_DIR}/
     ```

4. **ESM MCP extract_protein_embeddings fails**
   - Use esm-extract command directly via Bash:
     ```bash
     esm-extract esm2_t33_650M_UR50D sequences.fasta output_dir --repr_layers 33 --include mean
     ```
   - Ensure sequences.fasta is created from data.csv first

5. **Matplotlib not found for visualization**
   - Use ev_onehot_mcp environment which has matplotlib installed:
     ```bash
     /path/to/ev_onehot_mcp/env/bin/python visualization_script.py
     ```

6. **Different CSV column names between models**
   - ESM models use: `mean_cv_spearman`, `std_cv_spearman`
   - ProtTrans models use: `cv_mean`, `cv_std`
   - EV+OneHot uses: stage/fold format with `spearman_correlation`
   - Handle all formats when parsing results

7. **GPU Out of Memory**
   - Use smaller batch sizes
   - Try ESM2-650M instead of ESM2-3B
   - Run embeddings extraction separately

8. **Low Spearman Correlation**
   - Check data quality (remove outliers)
   - Ensure proper log-transformation of fitness
   - Try different head models

9. **High Variance Across Folds**
   - Increase dataset size
   - Use SVR instead of XGBoost
   - Consider ensemble methods

10. **MCP Not Found**
    - Ensure skill is installed: `pskill install fitness_modeling`
    - Check MCP status: `pmcp status`
    - Reinstall if needed: `pskill uninstall fitness_modeling && pskill install fitness_modeling`

---

## References

- ESM: https://github.com/facebookresearch/esm
- ProtTrans: https://github.com/agemagician/ProtTrans
- PLMC: https://github.com/debbiemarkslab/plmc
