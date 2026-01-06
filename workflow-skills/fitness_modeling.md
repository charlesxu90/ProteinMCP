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
DATA_DIR/                           # Input data (read-only)
├── wt.fasta                        # Wild-type sequence
└── data.csv                        # Fitness data

RESULTS_DIR/                        # All outputs go here
├── msa.a3m                         # Generated MSA
├── plmc/                           # PLMC model files
├── sequences.fasta                 # Extracted sequences for embeddings
├── data.csv                        # Copy of input data (for training tools)
├── wt.fasta                        # Copy of wild-type (for training tools)
├── metrics_summary.csv             # EV+OneHot results
├── esm2_650M_*/                    # ESM model outputs
├── esm2_3B_*/                      # ESM-3B model outputs
├── ProtT5-XL_*/                    # ProtTrans model outputs
├── ProtAlbert_*/                   # ProtAlbert model outputs
├── all_models_comparison.csv       # All model results combined
├── execution_timeline.json         # Step execution times
├── fitness_modeling_summary.png    # Four-panel summary figure
└── fitness_modeling_summary.pdf    # Publication-ready figure
```

---

## Execution Time Tracking

**IMPORTANT:** Track execution time for each step to generate the timeline visualization.

The workflow uses a Python helper to record step timing. At the start of each step, call `record_step_start()`, and at the end call `record_step_end()`.

**Standalone Helper Script:** `@workflow-skills/scripts/timing_helper.py`

**Command-line usage:**
```bash
# Start timing a step
python @workflow-skills/scripts/timing_helper.py start -d {RESULTS_DIR} -s MSA

# End timing a step
python @workflow-skills/scripts/timing_helper.py end -d {RESULTS_DIR} -s MSA

# Get timing summary
python @workflow-skills/scripts/timing_helper.py summary -d {RESULTS_DIR}

# Reset timeline (start fresh)
python @workflow-skills/scripts/timing_helper.py reset -d {RESULTS_DIR}
```

**Python import usage:**
```python
import sys
sys.path.append("@workflow-skills/scripts")
from timing_helper import record_step_start, record_step_end, get_timing_summary
```

**Timing Helper Code:**
```python
import json
import time
from pathlib import Path
from datetime import datetime

def get_timeline_path(results_dir):
    """Get path to execution_timeline.json"""
    return Path(results_dir) / "execution_timeline.json"

def load_timeline(results_dir):
    """Load existing timeline or create empty one"""
    timeline_path = get_timeline_path(results_dir)
    if timeline_path.exists():
        with open(timeline_path) as f:
            return json.load(f)
    return []

def save_timeline(results_dir, timeline):
    """Save timeline to JSON file"""
    timeline_path = get_timeline_path(results_dir)
    with open(timeline_path, 'w') as f:
        json.dump(timeline, f, indent=2)

def record_step_start(results_dir, step_name):
    """Record the start time of a step"""
    timeline = load_timeline(results_dir)
    # Remove any existing incomplete entry for this step
    timeline = [s for s in timeline if s.get('name') != step_name]
    timeline.append({
        'name': step_name,
        'start_time': time.time(),
        'start_datetime': datetime.now().isoformat(),
        'status': 'running'
    })
    save_timeline(results_dir, timeline)
    print(f"[TIMING] Started step: {step_name}")

def record_step_end(results_dir, step_name):
    """Record the end time of a step and calculate duration"""
    timeline = load_timeline(results_dir)
    for step in timeline:
        if step.get('name') == step_name and step.get('status') == 'running':
            end_time = time.time()
            start_time = step['start_time']
            duration_minutes = (end_time - start_time) / 60
            step['end_time'] = end_time
            step['end_datetime'] = datetime.now().isoformat()
            step['duration'] = round(duration_minutes, 2)
            step['status'] = 'completed'
            # Calculate relative start time from first step
            first_start = min(s.get('start_time', float('inf')) for s in timeline)
            step['start'] = round((start_time - first_start) / 60, 2)
            break
    save_timeline(results_dir, timeline)
    print(f"[TIMING] Completed step: {step_name} ({step.get('duration', 0):.2f} min)")

def get_timing_summary(results_dir):
    """Get a summary of all step timings"""
    timeline = load_timeline(results_dir)
    total_time = sum(s.get('duration', 0) for s in timeline if s.get('status') == 'completed')
    print(f"\n=== Execution Timeline Summary ===")
    for step in timeline:
        if step.get('status') == 'completed':
            print(f"  {step['name']}: {step['duration']:.2f} min (started at +{step['start']:.2f} min)")
    print(f"  Total: {total_time:.2f} min")
    return timeline
```

**Usage in each step:**
```python
# At the START of each step:
record_step_start("{RESULTS_DIR}", "StepName")

# ... execute the step ...

# At the END of each step:
record_step_end("{RESULTS_DIR}", "StepName")
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

**Timing:** This step is quick (setup only), no timing required.

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

**Timing:** Record timing for this step:
```python
record_step_start("{RESULTS_DIR}", "MSA")
# ... call mcp__msa_mcp__generate_msa ...
record_step_end("{RESULTS_DIR}", "MSA")
```

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

**Timing:** Record timing for this step:
```python
record_step_start("{RESULTS_DIR}", "PLMC")
# ... convert A3M to A2M and generate PLMC model ...
record_step_end("{RESULTS_DIR}", "PLMC")
```

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

**Timing:** Record timing for this step:
```python
record_step_start("{RESULTS_DIR}", "EV+OneHot")
# ... call mcp__ev_onehot_mcp__ev_onehot_train_fitness_predictor ...
record_step_end("{RESULTS_DIR}", "EV+OneHot")
```

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

**Timing:** Record timing for all ESM models (embeddings + training):
```python
record_step_start("{RESULTS_DIR}", "ESM")
# ... extract ESM embeddings (ESM2-650M and ESM2-3B) ...
# ... train all ESM models with different head models ...
record_step_end("{RESULTS_DIR}", "ESM")
```

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

**Timing:** Record timing for all ProtTrans models (embeddings + training):
```python
record_step_start("{RESULTS_DIR}", "ProtTrans")
# ... extract ProtTrans embeddings (ProtT5-XL and ProtAlbert) ...
# ... train all ProtTrans models with different head models ...
record_step_end("{RESULTS_DIR}", "ProtTrans")
```

---

## Step 6: Compare and Visualize Results

After training all models, create a comprehensive four-panel visualization showing:
1. **Model Performance Comparison** - Bar chart comparing best models per backbone
2. **Predicted vs Observed** - Scatter plot for the best model
3. **Head Model Comparison** - Table showing all head model results for pLMs
4. **Execution Timeline** - Gantt chart showing step execution times

### 6.1 Collect and Aggregate Results

**Prompt:**
> I have the metrics for EV+OneHot and different ESM and ProtTrans models in {RESULTS_DIR}/metrics_summary.csv and {RESULTS_DIR}/*/training_summary.csv. Can you:
> 1. Parse all training_summary.csv files to extract CV Spearman correlations
> 2. Create a combined all_models_comparison.csv with columns: backbone, head, mean_cv_spearman, std_cv_spearman
> 3. Save to {RESULTS_DIR}/all_models_comparison.csv

### 6.2 Results Collection Code

**IMPORTANT:** Different model types have different CSV formats. Use this code to aggregate all results:

```python
import os
import pandas as pd

results_dir = "{RESULTS_DIR}"
results = []

# EV+OneHot - metrics_summary.csv format:
# stage,fold,n_train,n_test,spearman_correlation
ev_metrics_path = os.path.join(results_dir, "metrics_summary.csv")
if os.path.exists(ev_metrics_path):
    ev_metrics = pd.read_csv(ev_metrics_path)
    cv_mean = ev_metrics[ev_metrics['fold'] == 'mean']['spearman_correlation'].values[0]
    cv_std = ev_metrics[ev_metrics['fold'] == 'std']['spearman_correlation'].values[0]
    results.append({'backbone': 'EV+OneHot', 'head': 'ridge', 'mean_cv_spearman': cv_mean, 'std_cv_spearman': cv_std})

# ESM and ProtTrans models - training_summary.csv format
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
        else:
            continue
        # Parse backbone and head from directory name (format: backbone_head)
        parts = dir_name.rsplit('_', 1)
        if len(parts) == 2:
            backbone, head = parts
            results.append({'backbone': backbone, 'head': head, 'mean_cv_spearman': mean_sp, 'std_cv_spearman': std_sp})

# Save combined results
all_models_df = pd.DataFrame(results)
all_models_df.to_csv(os.path.join(results_dir, "all_models_comparison.csv"), index=False)
print(f"Saved {len(results)} model results to all_models_comparison.csv")
```

### 6.3 Generate Four-Panel Visualization

**Prompt:**
> Generate the four-panel visualization figure for the fitness modeling results in {RESULTS_DIR}. Use the provided visualization script.

**Run the visualization script:**
```bash
# Use ev_onehot_mcp environment (has matplotlib, numpy, pandas, scipy)
# Paths are relative to the ProteinMCP project root
@tool-mcps/ev_onehot_mcp/env/bin/python @workflow-skills/scripts/fitness_modeling_viz.py {RESULTS_DIR}
```

**Note:** The `@` paths should be resolved to absolute paths:
- `@tool-mcps/` → `<project_root>/tool-mcps/`
- `@workflow-skills/` → `<project_root>/workflow-skills/`

### 6.4 Four-Panel Figure Description

The generated figure contains four panels:

1. **Model Performance Comparison** (top-left)
   - Bar chart comparing Spearman ρ (5-fold CV) for best model per backbone
   - Error bars showing standard deviation across folds
   - Backbones: EV+OneHot, ESM2-650M, ESM2-3B, ProtT5-XL, etc.

2. **Predicted vs Observed** (top-right)
   - Scatter plot showing predictions vs observed fitness values
   - Displays correlation coefficient and sample size
   - Indicates best model name

3. **Head Model Comparison** (bottom-left)
   - Table showing performance of SVR, XGB, KNN for each pLM backbone
   - Best combination highlighted
   - Summary of best backbone + head model

4. **Execution Timeline** (bottom-right)
   - Gantt chart showing execution time of each workflow step
   - Steps: MSA, PLMC, EV+OneHot, ESM, ProtTrans, Plot
   - Timeline is automatically inferred from file timestamps
   - Total execution time displayed

**Expected Output:**
- `{RESULTS_DIR}/fitness_modeling_summary.png` - Four-panel figure (150 DPI)
- `{RESULTS_DIR}/fitness_modeling_summary.pdf` - Vector format for publication
- `{RESULTS_DIR}/all_models_comparison.csv` - All tested models
- `{RESULTS_DIR}/execution_timeline.json` - Step timing data

**Timing:** Record timing for visualization step:
```python
record_step_start("{RESULTS_DIR}", "Plot")
# ... aggregate results and generate visualization ...
record_step_end("{RESULTS_DIR}", "Plot")

# Print final timing summary
get_timing_summary("{RESULTS_DIR}")
```

---

## Step 7: Display Results (Interactive)

After the workflow completes, display the results directly in a GUI window or notebook for immediate visual feedback.

**Prompt:**
> Display the fitness modeling results from {RESULTS_DIR} in the current session.

**Implementation - From Terminal (recommended):**

```bash
# One-liner to display results in a GUI window
python -c "
import sys
sys.path.insert(0, '@workflow-skills/scripts')
from fitness_modeling_viz import display_results
display_results('{RESULTS_DIR}')
"
```

Or using the ev_onehot_mcp environment (guaranteed to have all dependencies):
```bash
@tool-mcps/ev_onehot_mcp/env/bin/python -c "
import sys
sys.path.insert(0, '@workflow-skills/scripts')
from fitness_modeling_viz import display_results
display_results('{RESULTS_DIR}')
"
```

**Implementation - In Jupyter Notebook:**

```python
import sys
sys.path.append("@workflow-skills/scripts")
from fitness_modeling_viz import display_results

# Display all 4 figures with summary
display_results("{RESULTS_DIR}")

# Or display only the backbone comparison
display_results("{RESULTS_DIR}", show_all=False)
```

**Parameters:**
- `results_dir`: Path to results directory
- `show_all`: If True (default), show all 4 figures. If False, only show backbone comparison.
- `block`: If True (default), block until window is closed. If False, continue execution.

**What it displays:**
1. **Model Performance Comparison** - Bar chart comparing all backbones
2. **Predicted vs Observed** - Scatter plot showing prediction quality
3. **Head Model Comparison** - Table of all head model results
4. **Execution Timeline** - Gantt chart of workflow timing
5. **Text Summary** - Top 5 models with Spearman correlations (printed to terminal)

**Note:** When running from terminal, a GUI window will open with all figures. Close the window to continue.

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
