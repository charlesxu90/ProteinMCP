# Protein Fitness Prediction Skill

A comprehensive workflow for building and comparing protein fitness prediction models using multiple backbone architectures.

---

## Configuration Parameters

Before running this workflow, set the following parameters:

```yaml
# Required Inputs
PROTEIN_NAME: "MyProtein"           # Name of your protein (used for naming files)
WORK_DIR: "@examples/my_project"    # Working directory for all outputs
WT_FASTA: "@examples/my_project/wt.fasta"      # Wild-type sequence file
DATA_CSV: "@examples/my_project/data.csv"      # Fitness data with 'seq' and 'log_fitness' columns
MSA_FILE: "@examples/my_project/protein.a3m"   # MSA file (will be generated if not exists)

# Optional Settings
HEAD_MODELS: ["svr", "knn", "xgboost"]         # Head models to try
ESM_BACKBONES: ["esm2_t33_650M_UR50D", "esm2_t36_3B_UR50D"]  # ESM backbones
ESM1V_ENSEMBLE: true                            # Use ESM1v ensemble (1-5)
PROTTRANS_BACKBONES: ["ProtT5-XL", "ProtAlbert"] # ProtTrans backbones
```

**Data CSV Format:**
Your data.csv should contain at minimum:
- `seq`: Full protein sequence
- `log_fitness`: Log-transformed fitness value (target)

---

## Step 1: Generate MSA (if needed)

Install and use the MSA MCP server to generate multiple sequence alignment.

```bash
pmcp install msa_mcp
```

**Prompt:**
> Can you obtain the MSA for {PROTEIN_NAME} from {WT_FASTA} using msa mcp and save it to {MSA_FILE}.
> Please convert the relative path to absolute path before calling the MCP servers.

**Cleanup:**
```bash
pmcp uninstall msa_mcp
```

---

## Step 2: Build PLMC Evolutionary Coupling Model

Install and use the PLMC MCP server to build an evolutionary coupling model.

```bash
pmcp install plmc_mcp
```

**Prompt:**
> I have created an a3m file in {MSA_FILE}. Can you help build an EV model using plmc mcp and save it to {WORK_DIR}/plmc directory. The wild-type sequence is {WT_FASTA}.
> Please convert the relative path to absolute path before calling the MCP servers.

**Cleanup:**
```bash
pmcp uninstall plmc_mcp
```

---

## Step 3: Build EV+OneHot Model

Install and use the EV+OneHot MCP server to combine evolutionary features with one-hot encoding.

```bash
pmcp install ev_onehot_mcp
```

**Prompt:**
> I have created a plmc model in directory {WORK_DIR}/plmc. Can you help build an EV+OneHot model using ev_onehot_mcp and save it to {WORK_DIR}/ directory. The wild-type sequence is {WT_FASTA}, and the dataset is {DATA_CSV}.
> Please convert the relative path to absolute path before calling the MCP servers.

**Expected Output:**
- `{WORK_DIR}/metrics_summary.csv` - Cross-validation results
- `{WORK_DIR}/ridge_model.joblib` - Trained model

**Cleanup:**
```bash
pmcp uninstall ev_onehot_mcp
```

---

## Step 4: Build ESM Models

Install and use the ESM MCP server for deep learning embeddings.

```bash
pmcp install esm_mcp
```

### 4.1 ESM2-650M Models

**Prompt:**
> Can you help train an ESM model for data {WORK_DIR}/ and save it to {WORK_DIR}/esm2_650M_{head_model} using the esm mcp server with svr, xgboost, and knn as the head models.
> Please convert the relative path to absolute path before calling the MCP servers.
> Obtain the embeddings if they are not created.

### 4.2 ESM2-3B Models

**Prompt:**
> Can you help train an ESM model for data {WORK_DIR}/ and save it to {WORK_DIR}/esm2_3B_{head_model} using the esm mcp server with svr, xgboost, and knn as the head models and esm2_t36_3B_UR50D as the backbone.
> Please convert the relative path to absolute path before calling the MCP servers.
> Obtain the embeddings if they are not created.

### 4.3 ESM1v Ensemble Models (Optional)

Train models using all 5 ESM1v checkpoints for ensemble predictions.

**Prompt:**
> Can you help train ESM models for data {WORK_DIR}/ and save them to {WORK_DIR}/esm1v_t33_650M_UR90S_{num}_{head_model} using the esm mcp server with svr, knn, and xgboost as the head models and `esm1v_t33_650M_UR90S_1` to `esm1v_t33_650M_UR90S_5` as the backbones.
> Please convert the relative path to absolute path before calling the MCP servers.
> Obtain the embeddings if they are not created.

**Expected Output per model:**
- `{WORK_DIR}/{backbone}_{head}/training_summary.csv` - Training metrics
- `{WORK_DIR}/{backbone}_{head}/final_model/` - Trained model files

**Cleanup:**
```bash
pmcp uninstall esm_mcp
```

---

## Step 5: Build ProtTrans Models

Install and use the ProtTrans MCP server for transformer-based embeddings.

```bash
pmcp install prottrans_mcp
```

**Prompt:**
> Can you help train ProtTrans models for data {WORK_DIR}/ and save them to {WORK_DIR}/{backbone_model}_{head_model} using the prottrans mcp server with ProtT5-XL and ProtAlbert as backbone_models and knn, xgboost, and svr as the head models.
> Please convert the relative path to absolute path before calling the MCP servers.
> Create the embeddings if they are not created.

**Expected Output per model:**
- `{WORK_DIR}/{backbone}_{head}/training_summary.csv` - Training metrics
- `{WORK_DIR}/{backbone}_{head}/final_model/` - Trained model files

**Cleanup:**
```bash
pmcp uninstall prottrans_mcp
```

---

## Step 6: Compare and Visualize Results

After training all models, create a comparison figure showing Spearman correlations with error bars.

### 6.1 Collect Results

**Prompt:**
> I have the metrics for EV+OneHot and different ESM and ProtTrans models in {WORK_DIR}/metrics_summary.csv and {WORK_DIR}/*/training_summary.csv. Can you:
> 1. Parse all training_summary.csv files to extract CV Spearman correlations
> 2. Select the best head model for each backbone
> 3. Create a comparison table with mean and standard deviation
> 4. Generate a bar chart visualization

### 6.2 Visualization Code

Use the following code as reference for creating the comparison figure:

```python
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def prettify_ax(ax):
    """
    Make axes more pleasant to look at
    """
    for i, spine in enumerate(ax.spines.values()):
        if i == 3 or i == 1:
            spine.set_visible(False)
    ax.set_frameon = True
    ax.tick_params(direction='out', length=3, color='k')
    ax.set_axisbelow(True)

# Example data structure (extract from your results)
methods = ['EV+onehot', 'esm2_3B', 'ProtT5-XL', 'ProtAlbert', 'esm2_650M',
           'esm1v_650M_1', 'esm1v_650M_3', 'esm1v_650M_2', 'esm1v_650M_5', 'esm1v_650M_4']
spearman = [0.491, 0.463, 0.451, 0.442, 0.440, 0.423, 0.416, 0.415, 0.413, 0.400]
spearman_std = [0.036, 0.045, 0.058, 0.038, 0.054, 0.047, 0.050, 0.038, 0.049, 0.048]

# Create figure
sns.set(style="white", context="paper")
fig = plt.figure(figsize=(6, 4))
ax = fig.add_subplot(111)
prettify_ax(ax)

# Plot bars with error bars
ax.bar(methods, spearman, color='#1f77b4')
ax.errorbar(methods, spearman, yerr=spearman_std, fmt='none', ecolor='#ff7f0e')

# Labels and styling
ax.set_title('Comparison on activity prediction')
ax.set_ylabel('Spearman correlation')
ax.set_ylim([0, 0.65])
ax.set_xticks(range(len(methods)))
ax.set_xticklabels(methods, rotation=45, ha='right')

# Save figure
fig.savefig(f"{WORK_DIR}/backbone_comparison.pdf", dpi=300, bbox_inches='tight', transparent=True)
fig.savefig(f"{WORK_DIR}/backbone_comparison.png", dpi=300, bbox_inches='tight')
plt.show()
```

### 6.3 Implementation Details

The visualization should:
1. **Extract metrics** from all `training_summary.csv` files
2. **Parse CV results** to get mean and std of Spearman correlations
3. **Select best head** for each backbone (highest mean Spearman)
4. **Sort models** by performance (descending)
5. **Create bar chart** with error bars showing standard deviation
6. **Save outputs** as both PDF (vector) and PNG (raster)

**Key Features:**
- Bar chart showing mean Spearman correlation
- Error bars representing standard deviation across CV folds
- Clean, publication-ready styling with prettify_ax
- Models sorted by performance for easy comparison

**Expected Output:**
- `{WORK_DIR}/backbone_comparison.pdf` - Vector format for publication
- `{WORK_DIR}/backbone_comparison.png` - Raster format for preview
- `{WORK_DIR}/backbone_comparison_table.csv` - Summary table with all metrics

---

## Quick Start Template

For a new protein fitness prediction project, copy and modify:

```markdown
# {PROTEIN_NAME} Fitness Modeling

## Setup
Working directory: {WORK_DIR}
Wild-type: {WT_FASTA}
Dataset: {DATA_CSV}

## Step 1: MSA
pmcp install msa_mcp
[Run MSA generation prompt]
pmcp uninstall msa_mcp

## Step 2: PLMC
pmcp install plmc_mcp
[Run PLMC prompt]
pmcp uninstall plmc_mcp

## Step 3: EV+OneHot
pmcp install ev_onehot_mcp
[Run EV+OneHot prompt]
pmcp uninstall ev_onehot_mcp

## Step 4: ESM Models
pmcp install esm_mcp
[Run ESM prompts]
pmcp uninstall esm_mcp

## Step 5: ProtTrans Models
pmcp install prottrans_mcp
[Run ProtTrans prompts]
pmcp uninstall prottrans_mcp

## Step 6: Compare
[Run comparison prompt]
```

**Note:** Uninstalling MCPs after each step keeps the CLI clean and avoids potential conflicts between servers.

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

## MCP Cleanup

### Uninstall All Fitness MCPs at Once

If you want to clean up all fitness-related MCPs after completing the workflow:

```bash
pmcp uninstall msa_mcp plmc_mcp ev_onehot_mcp esm_mcp prottrans_mcp
```

### Check Currently Installed MCPs

```bash
pmcp status
```

---

## Troubleshooting

### Common Issues

1. **GPU Out of Memory**
   - Use smaller batch sizes
   - Try ESM2-650M instead of ESM2-3B
   - Run embeddings extraction separately

2. **Low Spearman Correlation**
   - Check data quality (remove outliers)
   - Ensure proper log-transformation of fitness
   - Try different head models

3. **High Variance Across Folds**
   - Increase dataset size
   - Use SVR instead of XGBoost
   - Consider ensemble methods

---

## References

- ESM: https://github.com/facebookresearch/esm
- ProtTrans: https://github.com/agemagician/ProtTrans
- PLMC: https://github.com/debbiemarkslab/plmc
