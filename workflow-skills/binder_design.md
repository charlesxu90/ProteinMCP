# Binder Design Skill

Design protein binders using BindCraft with GPU-accelerated deep learning for de novo binder generation

---

## Prerequisites

Before running this workflow, install the skill and all required MCPs:

```bash
pskill install binder_design
```

This will install the following MCP servers:
- `bindcraft_mcp` - BindCraft protein binder design server

**Verify MCPs are installed:**
```bash
pmcp status
```

---

## Configuration Parameters

```yaml
# Required Inputs
TARGET_PDB: "@examples/data/target.pdb"           # Path to target protein PDB file
TARGET_CHAINS: "A"                                 # Target chains to design binders for
BINDER_LENGTH: 130                                 # Length of designed binder sequence

# Output Settings
RESULTS_DIR: "@results/binder_design"             # Output directory for all results
NUM_DESIGNS: 3                                     # Number of binder designs to generate

# Optional Settings
HOTSPOT_RESIDUES: null                            # Specific residues to target (e.g., "A:10,A:15,A:20")
GPU_DEVICE: 0                                      # GPU device to use
CONFIG_FILE: null                                  # Custom config file (optional)
```

**Target PDB Requirements:**
- Clean PDB file with target protein structure
- All heteroatoms and waters removed (unless needed)
- Chain IDs properly assigned

**Directory Structure:**
```
RESULTS_DIR/                     # All outputs go here
├── config.json                  # Generated configuration
├── designs/                     # Designed binder structures
│   ├── design_001.pdb          # Binder-target complex
│   ├── design_002.pdb
│   └── ...
├── metrics.csv                  # Design quality metrics
└── logs/                        # Execution logs
```

---

## Step 1: Explore Available Example Data

**Description**: List available example PDB files to use as targets or understand the expected input format.

**Prompt:**
> Can you list the available example data files for BindCraft using the scripts_mcp server? Show me what files are available and their paths.

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__list_example_data` tool
- Returns a list of example PDB files with paths and descriptions
- Use example files for testing the workflow before using your own targets

**Expected Output:**
- List of example files with paths
- PDL1.pdb is typically available as a default example

---

## Step 2: Explore Default Configurations

**Description**: Get information about available configuration files and their settings.

**Prompt:**
> Can you show me the available default configurations for BindCraft using the scripts_mcp server? I want to understand what settings are available.

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__get_default_configs` tool
- Returns available config files and their settings
- Useful for understanding optimization parameters

**Expected Output:**
- List of config files with descriptions
- Settings for each configuration type

---

## Step 3: Setup Results Directory

**Description**: Create the output directory structure for the binder design workflow.

**Prompt:**
> Please create the results directory at {RESULTS_DIR} for the binder design workflow. Set up the necessary subdirectories.

**Implementation Notes:**
```bash
mkdir -p {RESULTS_DIR}/designs
mkdir -p {RESULTS_DIR}/logs
```

**Expected Output:**
- `{RESULTS_DIR}/` directory created
- `{RESULTS_DIR}/designs/` subdirectory
- `{RESULTS_DIR}/logs/` subdirectory

---

## Step 4: Generate Configuration from Target PDB

**Description**: Analyze the target PDB structure and generate an optimized configuration file.

**Prompt:**
> Can you generate a BindCraft configuration for my target protein at {TARGET_PDB}? Target chain(s) {TARGET_CHAINS} and aim for a binder of length {BINDER_LENGTH}. Save the config to {RESULTS_DIR}/config.json.
> Please convert relative paths to absolute paths before calling the MCP server.

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__generate_config` tool
- Parameters:
  - `input_file`: Path to target PDB
  - `output_file`: Path for config output
  - `chains`: Target chains
  - `binder_length`: Desired binder length
  - `validate`: true (to validate the config)
  - `analysis_type`: "basic" or "detailed"

**Expected Output:**
- `{RESULTS_DIR}/config.json` - Generated configuration file
- Validation results if enabled

---

## Step 5: Quick Design (Single Binder)

**Description**: Run a quick synchronous design to generate a single binder for testing.

**Prompt:**
> Can you run a quick binder design for my target at {TARGET_PDB} using BindCraft? Design one binder targeting chain(s) {TARGET_CHAINS} with binder length {BINDER_LENGTH}. Save results to {RESULTS_DIR}/quick_test/.
> Please convert relative paths to absolute paths before calling the MCP server.

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__quick_design` tool
- Parameters:
  - `input_file`: Path to target PDB
  - `output_dir`: Output directory
  - `config`: Optional config file path
  - `num_designs`: 1 (for quick test)
  - `chains`: Target chains
  - `binder_length`: Binder length
  - `device`: GPU device (default 0)
  - `hotspot`: Optional hotspot residues
- This is synchronous and waits for completion
- Best for testing with 1-2 designs

**Expected Output:**
- `{RESULTS_DIR}/quick_test/design_001.pdb` - Designed binder structure
- Design metrics and scores

---

## Step 6: Submit Async Design Job (Multiple Binders)

**Description**: Submit an asynchronous job for generating multiple binder designs.

**Prompt:**
> Can you submit an async binder design job for {TARGET_PDB} using BindCraft? Generate {NUM_DESIGNS} designs targeting chain(s) {TARGET_CHAINS} with binder length {BINDER_LENGTH}. Save results to {RESULTS_DIR}/designs/. Use the config file at {RESULTS_DIR}/config.json if available.
> Please convert relative paths to absolute paths before calling the MCP server.

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__submit_async_design` tool
- Parameters:
  - `input_file`: Path to target PDB
  - `output_dir`: Output directory
  - `config`: Config file path (optional)
  - `num_designs`: Number of designs
  - `chains`: Target chains
  - `binder_length`: Binder length
  - `device`: GPU device
  - `hotspot`: Optional hotspot residues
  - `job_name`: Optional job name for tracking
- Returns a job_id for tracking

**Expected Output:**
- Job submission confirmation with job_id
- Use job_id for monitoring and retrieving results

---

## Step 7: Monitor Job Progress

**Description**: Check the progress of running design jobs.

**Prompt:**
> Can you check the status of my BindCraft design job with ID {job_id}? Also show me the recent log output.

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__get_job_status` to check job status
- Use `mcp__bindcraft_mcp__get_job_log` to view logs
- Alternative: Use `mcp__bindcraft_mcp__monitor_progress` for directory-based monitoring
- Parameters for get_job_status:
  - `job_id`: The job ID from submission
- Parameters for get_job_log:
  - `job_id`: The job ID
  - `tail`: Number of lines (default 50)

**Expected Output:**
- Job status (pending, running, completed, failed)
- Progress information
- Recent log output

---

## Step 8: List All Jobs

**Description**: View all submitted jobs and their statuses.

**Prompt:**
> Can you list all BindCraft jobs I've submitted? Show me their statuses.

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__list_jobs` tool
- Optional parameter:
  - `status`: Filter by status (pending, running, completed, failed, cancelled)

**Expected Output:**
- List of all jobs with IDs, names, and statuses
- Timestamps for job creation and completion

---

## Step 9: Get Job Results

**Description**: Retrieve the results of a completed design job.

**Prompt:**
> Can you get the results of my completed BindCraft job with ID {job_id}?

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__get_job_result` tool
- Parameters:
  - `job_id`: The job ID of a completed job
- Only works for completed jobs

**Expected Output:**
- Design results including:
  - Output file paths
  - Design metrics and scores
  - Any errors or warnings

---

## Step 10: Batch Design (Multiple Targets)

**Description**: Submit batch processing for multiple target proteins.

**Prompt:**
> I have multiple target PDB files in {INPUT_DIR}. Can you submit a batch BindCraft job to design binders for all of them? Generate {NUM_DESIGNS} designs per target, save results to {RESULTS_DIR}/batch_results/.
> Please convert relative paths to absolute paths before calling the MCP server.

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__submit_batch_design` tool
- Parameters:
  - `input_file`: Path to batch input file or directory with PDBs
  - `output_dir`: Base output directory
  - `config`: Config file (optional)
  - `num_designs`: Designs per target
  - `max_concurrent`: Maximum concurrent jobs (default 3)
  - `chains`: Target chains
  - `binder_length`: Binder length
  - `device`: GPU device
  - `job_name`: Optional batch job name

**Expected Output:**
- Batch job submission confirmation with job_id
- Results organized by target protein

---

## Step 11: Cancel a Job

**Description**: Cancel a running job if needed.

**Prompt:**
> Can you cancel my BindCraft job with ID {job_id}?

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__cancel_job` tool
- Parameters:
  - `job_id`: The job ID to cancel
- Only affects running or pending jobs

**Expected Output:**
- Confirmation of job cancellation
- Final job status

---

## Step 12: Analyze Results

**Description**: Analyze the designed binders and compare metrics.

**Prompt:**
> Can you analyze the binder designs in {RESULTS_DIR}/designs/? Summarize the key metrics and identify the best candidates.

**Implementation Notes:**
- Metrics to examine:
  - pLDDT (predicted local distance difference test) - higher is better
  - pAE (predicted aligned error) - lower is better
  - Interface scores
  - Binding affinity predictions
- Compare across designs to select top candidates

**Expected Output:**
- Summary of design metrics
- Ranking of best binder candidates
- Recommendations for experimental validation

---

## Step 13: Visualize Results

**Description**: Generate publication-ready figures showcasing design quality and workflow.

**Prompt:**
> Can you generate visualization figures for the binder design results in {RESULTS_DIR}/? Create a main figure showing quality metrics, a supplementary figure with detailed analysis, and a workflow overview diagram.

**Implementation Notes:**

Use the binder design figure generation script or run the following Python code:

```python
# Run with any Python environment that has matplotlib and numpy
# Example: python workflow-skills/figures/binder_design_figures.py --results_dir {RESULTS_DIR}

import matplotlib
matplotlib.use('Agg')  # Required for non-interactive mode
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np
import pandas as pd
from pathlib import Path

# Color palette
COLORS = {
    'primary': '#2ecc71',      # Green - success/quality
    'secondary': '#3498db',    # Blue - input/structure
    'warning': '#e74c3c',      # Red - low quality
    'accent': '#9b59b6',       # Purple - processing
    'highlight': '#f39c12',    # Orange - tools/MCP
    'teal': '#1abc9c',         # Teal - highlights
    'dark': '#2c3e50',         # Dark gray - text
    'light': '#7f8c8d',        # Light gray - secondary
    'background': '#f8f9fa',   # Very light gray
}

# Quality thresholds
THRESHOLDS = {
    'plddt_good': 80,
    'plddt_acceptable': 70,
    'pae_good': 5,
    'pae_acceptable': 10,
    'interface_good': -10,
}

def prettify_ax(ax):
    """Apply consistent styling to axes."""
    for i, spine in enumerate(ax.spines.values()):
        if i in [1, 3]:
            spine.set_visible(False)
    ax.tick_params(direction='out', length=3, color='k')
    ax.set_axisbelow(True)

results_dir = Path("{RESULTS_DIR}")

# Load metrics
metrics_file = results_dir / 'metrics.csv'
if metrics_file.exists():
    df = pd.read_csv(metrics_file)
else:
    # Generate mock data for demonstration
    np.random.seed(42)
    n = 10
    df = pd.DataFrame({
        'design_name': [f'design_{i:03d}' for i in range(1, n+1)],
        'plddt': np.random.normal(75, 10, n).clip(50, 95),
        'pae': np.random.exponential(6, n).clip(2, 20),
        'interface_score': np.random.normal(-8, 4, n).clip(-20, 0),
        'ptm': np.random.normal(0.7, 0.1, n).clip(0.4, 0.95),
    })

n_designs = len(df)
x_pos = np.arange(n_designs)

# ============================================================
# MAIN FIGURE: Multi-panel quality metrics
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('Binder Design Quality Assessment', fontsize=14, fontweight='bold', y=0.98)

# Panel A: pLDDT Distribution
ax = axes[0, 0]
prettify_ax(ax)
plddt_colors = [COLORS['primary'] if v >= THRESHOLDS['plddt_good']
               else COLORS['highlight'] if v >= THRESHOLDS['plddt_acceptable']
               else COLORS['warning'] for v in df['plddt']]
ax.bar(x_pos, df['plddt'], color=plddt_colors, alpha=0.85, edgecolor='white')
ax.axhline(y=THRESHOLDS['plddt_good'], color=COLORS['primary'], linestyle='--', alpha=0.7, label=f'Good (>{THRESHOLDS["plddt_good"]})')
ax.axhline(y=THRESHOLDS['plddt_acceptable'], color=COLORS['highlight'], linestyle='--', alpha=0.7, label=f'Acceptable (>{THRESHOLDS["plddt_acceptable"]})')
ax.set_xlabel('Design')
ax.set_ylabel('pLDDT Score')
ax.set_title('A. Predicted Local Distance Difference Test', fontsize=12, fontweight='bold', loc='left')
ax.set_xticks(x_pos)
ax.set_xticklabels([d.replace('design_', '') for d in df['design_name']], rotation=45, ha='right')
ax.set_ylim(0, 100)
ax.legend(loc='lower right', fontsize=9)
ax.yaxis.grid(True, linestyle='--', alpha=0.5)

# Panel B: pAE Comparison
ax = axes[0, 1]
prettify_ax(ax)
pae_colors = [COLORS['primary'] if v <= THRESHOLDS['pae_good']
              else COLORS['highlight'] if v <= THRESHOLDS['pae_acceptable']
              else COLORS['warning'] for v in df['pae']]
ax.bar(x_pos, df['pae'], color=pae_colors, alpha=0.85, edgecolor='white')
ax.axhline(y=THRESHOLDS['pae_good'], color=COLORS['primary'], linestyle='--', alpha=0.7, label=f'Good (<{THRESHOLDS["pae_good"]})')
ax.axhline(y=THRESHOLDS['pae_acceptable'], color=COLORS['highlight'], linestyle='--', alpha=0.7, label=f'Acceptable (<{THRESHOLDS["pae_acceptable"]})')
ax.set_xlabel('Design')
ax.set_ylabel('pAE Score (lower is better)')
ax.set_title('B. Predicted Aligned Error', fontsize=12, fontweight='bold', loc='left')
ax.set_xticks(x_pos)
ax.set_xticklabels([d.replace('design_', '') for d in df['design_name']], rotation=45, ha='right')
ax.legend(loc='upper right', fontsize=9)
ax.yaxis.grid(True, linestyle='--', alpha=0.5)

# Panel C: Interface Score Ranking
ax = axes[1, 0]
prettify_ax(ax)
sorted_df = df.sort_values('interface_score')
interface_colors = [COLORS['primary'] if v <= THRESHOLDS['interface_good'] else COLORS['highlight'] for v in sorted_df['interface_score']]
bars = ax.barh(np.arange(n_designs), sorted_df['interface_score'], color=interface_colors, alpha=0.85, edgecolor='white')
ax.axvline(x=THRESHOLDS['interface_good'], color=COLORS['primary'], linestyle='--', alpha=0.7, label=f'Good (<{THRESHOLDS["interface_good"]})')
ax.set_xlabel('Interface Score (REU, lower is better)')
ax.set_ylabel('Design (ranked)')
ax.set_title('C. Interface Score Ranking', fontsize=12, fontweight='bold', loc='left')
ax.set_yticks(np.arange(n_designs))
ax.set_yticklabels([n.replace('design_', '') for n in sorted_df['design_name']])
ax.legend(loc='lower right', fontsize=9)
ax.xaxis.grid(True, linestyle='--', alpha=0.5)

# Panel D: pTM Summary
ax = axes[1, 1]
prettify_ax(ax)
ptm_colors = [COLORS['primary'] if v >= 0.8 else COLORS['highlight'] if v >= 0.6 else COLORS['warning'] for v in df['ptm']]
ax.bar(x_pos, df['ptm'], color=ptm_colors, alpha=0.85, edgecolor='white')
ax.axhline(y=0.8, color=COLORS['primary'], linestyle='--', alpha=0.7, label='Good (>0.8)')
ax.axhline(y=0.6, color=COLORS['highlight'], linestyle='--', alpha=0.7, label='Acceptable (>0.6)')
ax.set_xlabel('Design')
ax.set_ylabel('pTM Score')
ax.set_title('D. Predicted Template Modeling Score', fontsize=12, fontweight='bold', loc='left')
ax.set_xticks(x_pos)
ax.set_xticklabels([d.replace('design_', '') for d in df['design_name']], rotation=45, ha='right')
ax.set_ylim(0, 1)
ax.legend(loc='lower right', fontsize=9)
ax.yaxis.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(results_dir / 'binder_design_main.pdf', dpi=300, bbox_inches='tight')
fig.savefig(results_dir / 'binder_design_main.png', dpi=300, bbox_inches='tight')
plt.close(fig)

print(f"Saved: {results_dir / 'binder_design_main.pdf'}")
print(f"Saved: {results_dir / 'binder_design_main.png'}")

# ============================================================
# SUPPLEMENTARY FIGURE: Detailed analysis
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('Binder Design - Supplementary Analysis', fontsize=14, fontweight='bold', y=0.98)

# Panel A: Quality Metrics Heatmap
ax = axes[0, 0]
metrics_normalized = np.array([
    df['plddt'].values / 100,
    1 - df['pae'].values / 20,
    1 - (df['interface_score'].values + 20) / 20,
    df['ptm'].values,
])
im = ax.imshow(metrics_normalized, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
ax.set_xticks(np.arange(n_designs))
ax.set_xticklabels([d.replace('design_', '') for d in df['design_name']], rotation=45, ha='right')
ax.set_yticks(np.arange(4))
ax.set_yticklabels(['pLDDT', 'pAE (inv)', 'Interface (inv)', 'pTM'])
ax.set_title('A. Normalized Quality Metrics', fontsize=12, fontweight='bold', loc='left')
cbar = plt.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label('Normalized Score (higher is better)', fontsize=9)

# Panel B: Scatter plot
ax = axes[0, 1]
prettify_ax(ax)
scatter = ax.scatter(df['plddt'], df['pae'], c=df['interface_score'], cmap='viridis_r', s=100, alpha=0.8, edgecolor='white')
ax.set_xlabel('pLDDT Score')
ax.set_ylabel('pAE Score')
ax.set_title('B. Quality Correlation', fontsize=12, fontweight='bold', loc='left')
cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
cbar.set_label('Interface Score', fontsize=9)
ax.grid(True, linestyle='--', alpha=0.3)

# Panel C: Quality Score Distribution
ax = axes[1, 0]
prettify_ax(ax)
quality_scores = (df['plddt']/100 * 0.3 + (1 - df['pae']/20) * 0.3 + (1 - (df['interface_score']+20)/20) * 0.2 + df['ptm'] * 0.2)
ax.hist(quality_scores, bins=10, color=COLORS['secondary'], alpha=0.7, edgecolor='white')
ax.axvline(x=0.7, color=COLORS['primary'], linestyle='--', linewidth=2, label='Good threshold')
ax.axvline(x=quality_scores.mean(), color=COLORS['warning'], linestyle='-', linewidth=2, label=f'Mean ({quality_scores.mean():.2f})')
ax.set_xlabel('Composite Quality Score')
ax.set_ylabel('Number of Designs')
ax.set_title('C. Quality Score Distribution', fontsize=12, fontweight='bold', loc='left')
ax.legend(loc='upper left', fontsize=9)
ax.yaxis.grid(True, linestyle='--', alpha=0.5)

# Panel D: Summary
ax = axes[1, 1]
ax.axis('off')
n_good_plddt = (df['plddt'] >= THRESHOLDS['plddt_good']).sum()
n_good_pae = (df['pae'] <= THRESHOLDS['pae_good']).sum()
n_high_quality = ((df['plddt'] >= THRESHOLDS['plddt_good']) & (df['pae'] <= THRESHOLDS['pae_good'])).sum()
best_idx = quality_scores.idxmax()
summary = f"""
DESIGN SUMMARY
{'='*40}
Total Designs: {n_designs}

Quality Breakdown:
- Good pLDDT (>{THRESHOLDS['plddt_good']}): {n_good_plddt}/{n_designs}
- Good pAE (<{THRESHOLDS['pae_good']}): {n_good_pae}/{n_designs}

High-Quality Designs: {n_high_quality}/{n_designs}

Best Design: {df.loc[best_idx, 'design_name']}
- pLDDT: {df.loc[best_idx, 'plddt']:.1f}
- pAE: {df.loc[best_idx, 'pae']:.1f}
- Interface: {df.loc[best_idx, 'interface_score']:.1f}
- Composite: {quality_scores[best_idx]:.3f}
{'='*40}
"""
ax.text(0.05, 0.95, summary, transform=ax.transAxes, fontsize=10, verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor=COLORS['background'], alpha=0.8))
ax.set_title('D. Selection Summary', fontsize=12, fontweight='bold', loc='left')

plt.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(results_dir / 'binder_design_supplementary.pdf', dpi=300, bbox_inches='tight')
fig.savefig(results_dir / 'binder_design_supplementary.png', dpi=300, bbox_inches='tight')
plt.close(fig)

print(f"Saved: {results_dir / 'binder_design_supplementary.pdf'}")
print(f"Saved: {results_dir / 'binder_design_supplementary.png'}")
```

**Alternatively, use the standalone script:**
```bash
python workflow-skills/figures/binder_design_figures.py --results_dir {RESULTS_DIR}
```

**Expected Output:**
- `{RESULTS_DIR}/binder_design_main.pdf` - Main quality metrics figure (4-panel)
- `{RESULTS_DIR}/binder_design_main.png` - PNG version for preview
- `{RESULTS_DIR}/binder_design_supplementary.pdf` - Detailed analysis figure
- `{RESULTS_DIR}/binder_design_supplementary.png` - PNG version for preview
- `{RESULTS_DIR}/binder_workflow_overview.pdf` - Workflow schematic diagram
- `{RESULTS_DIR}/binder_workflow_overview.png` - PNG version for preview

**Figure Descriptions:**

*Main Figure (2x2 panels):*
- Panel A: pLDDT distribution across designs with quality thresholds
- Panel B: pAE comparison with acceptability thresholds
- Panel C: Interface score ranking (sorted, lower is better)
- Panel D: pTM scores indicating structural confidence

*Supplementary Figure (2x2 panels):*
- Panel A: Heatmap of normalized quality metrics
- Panel B: Scatter plot showing metric correlations
- Panel C: Composite quality score distribution
- Panel D: Summary statistics and best design selection

*Workflow Overview:*
- Schematic diagram showing BindCraft pipeline: Target PDB → Config → RFdiffusion → ProteinMPNN → AlphaFold2 → Output

---

---

## Troubleshooting

### Common Issues

1. **Job Stuck in Pending Status**
   - Check GPU availability
   - Verify input file paths are correct
   - Check system resources

2. **Low Quality Designs (Low pLDDT)**
   - Try different binder lengths
   - Specify hotspot residues for better targeting
   - Use a different config with more iterations

3. **GPU Out of Memory**
   - Reduce binder length
   - Use a smaller model configuration
   - Run fewer concurrent jobs

4. **Invalid PDB Structure**
   - Ensure PDB has proper chain IDs
   - Remove waters and heteroatoms if not needed
   - Validate structure with standard tools first

5. **MCP Connection Errors**
   - Verify MCP is registered: `pmcp status`
   - Reinstall if needed: `pmcp install bindcraft_mcp`
   - Check server logs for errors

6. **Config Generation Fails**
   - Check target PDB is accessible
   - Verify chain IDs exist in the structure
   - Try with default settings first

7. **Async Job Not Found**
   - Job IDs may expire after completion
   - Check output directory for results
   - Use list_jobs to verify job exists

8. **Batch Processing Issues**
   - Ensure all PDB files in directory are valid
   - Check max_concurrent doesn't exceed GPU capacity
   - Monitor individual job statuses

9. **Settings File Format Errors (KeyError)**
   - BindCraft expects specific field names in target_settings.json
   - Required fields: `design_path`, `starting_pdb`, `chains`, `lengths`, `number_of_final_designs`, `binder_name`
   - `lengths` must be an array `[min, max]`, not a single integer
   - Example correct format:
     ```json
     {
       "design_path": "/path/to/output",
       "binder_name": "MyBinder",
       "starting_pdb": "/path/to/target.pdb",
       "chains": "A",
       "target_hotspot_residues": "18,30,42",
       "lengths": [65, 150],
       "number_of_final_designs": 1
     }
     ```

---

---

## References

- BindCraft: https://github.com/martinpacesa/BindCraft
- RFdiffusion: https://github.com/RosettaCommons/RFdiffusion
- ProteinMPNN: https://github.com/dauparas/ProteinMPNN
- AlphaFold: https://github.com/google-deepmind/alphafold

---

## Cleanup

When you're done with the workflow, uninstall the skill and all its MCPs:

```bash
pskill uninstall binder_design
```
