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

## Step 1: Explore Default Configurations

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

## Step 2: Setup Results Directory

**Description**: Create the output directory structure for the binder design workflow.

**Prompt:**
> Please create the results directory at {RESULTS_DIR} for the binder design workflow. Set up the necessary subdirectories.

**Implementation Notes:**
```bash
mkdir -p {RESULTS_DIR}/
mkdir -p {RESULTS_DIR}/designs
mkdir -p {RESULTS_DIR}/logs
```

**Expected Output:**
- `{RESULTS_DIR}/` directory created
- `{RESULTS_DIR}/designs/` subdirectory
- `{RESULTS_DIR}/logs/` subdirectory

---

## Step 3: Generate Configuration from Target PDB

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

## Step 4: Submit Async Design Job (Multiple Binders)

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

## Step 5: Monitor Job Progress

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

## Step 6: List All Jobs

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

## Step 7: Get Job Results

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

## Step 8: Visualize Results

**Description**: Generate publication-ready figures showcasing design quality metrics.

**Prompt:**
> Can you generate visualization figures for the binder design results in {RESULTS_DIR}/? Create all quality assessment figures and a merged summary figure.

**Implementation Notes:**

Use the binder design visualization script:

```bash
# Run the visualization script (using ev_onehot_mcp environment which has matplotlib)
@tool-mcps/ev_onehot_mcp/env/bin/python @workflow-skills/scripts/binder_design_viz.py {RESULTS_DIR}

# Or with custom output prefix:
@tool-mcps/ev_onehot_mcp/env/bin/python @workflow-skills/scripts/binder_design_viz.py {RESULTS_DIR} --output {RESULTS_DIR}/custom_prefix
```

**Note:** The `@` paths should be resolved to absolute paths:
- `@tool-mcps/` → `<project_root>/tool-mcps/`
- `@workflow-skills/` → `<project_root>/workflow-skills/`

**Generated Figures (8 individual + 1 merged):**

1. `binder_design_composite_score.png` - Composite quality score distribution histogram
2. `binder_design_quality_assessment.png` - pLDDT vs Interface scatter plot (colored by quality)
3. `binder_design_normalized_heatmap.png` - Heatmap of normalized metrics per design
4. `binder_design_statistics_table.png` - Table with Mean, Std, Min, Max, Pass Rate
5. `binder_design_quality_boxplot.png` - Boxplots with threshold lines
6. `binder_design_sasa_binding_energy.png` - SASA vs Binding Energy scatter plot
7. `binder_design_top5_designs.png` - Top 5 designs ranked by composite score
8. `binder_design_correlation.png` - Correlation heatmap of metrics
9. `binder_design_summary.png` - **Merged 8-panel summary figure** (publication-ready)

**Composite Quality Score Formula:**
```
Composite Score = 0.3×pLDDT(norm) + 0.3×pAE(inv,norm) + 0.2×Interface(inv,norm) + 0.2×pTM
```

**Quality Thresholds:**
- pLDDT: ≥80 (higher is better)
- pAE: ≤4Å (lower is better)
- Interface Score: ≤-13 REU (more negative is better)
- pTM: ≥0.8 (higher is better)

**Display Results Interactively (Python):**
```python
import sys
sys.path.append("@workflow-skills/scripts")
from binder_design_viz import display_results

# Display all figures in a GUI window
display_results("{RESULTS_DIR}")

# Or display only the merged summary
display_results("{RESULTS_DIR}", show_all=False)
```

**Expected Output:**

*Individual Figures (8 files):*
- `{RESULTS_DIR}/binder_design_composite_score.png/.pdf` - Composite score histogram
- `{RESULTS_DIR}/binder_design_quality_assessment.png/.pdf` - Quality scatter plot
- `{RESULTS_DIR}/binder_design_normalized_heatmap.png/.pdf` - Metrics heatmap
- `{RESULTS_DIR}/binder_design_statistics_table.png/.pdf` - Statistics table
- `{RESULTS_DIR}/binder_design_quality_boxplot.png/.pdf` - Boxplots with thresholds
- `{RESULTS_DIR}/binder_design_sasa_binding_energy.png/.pdf` - SASA vs binding energy
- `{RESULTS_DIR}/binder_design_top5_designs.png/.pdf` - Top 5 designs table
- `{RESULTS_DIR}/binder_design_correlation.png/.pdf` - Correlation heatmap

*Merged Summary Figure (2x4 panels):*
- `{RESULTS_DIR}/binder_design_summary.png/.pdf` - **Publication-ready 8-panel figure**

**Figure Descriptions:**

*Merged Summary Figure (2x4 panels):*
- Panel A: Composite score distribution with mean and threshold lines
- Panel B: Quality assessment scatter (pLDDT vs Interface, colored by quality score)
- Panel C: Normalized metrics heatmap per design
- Panel D: Metrics statistics table (Mean, Std, Min, Max, Pass Rate)
- Panel E: Quality boxplots for each metric
- Panel F: SASA vs Binding Energy scatter colored by pLDDT
- Panel G: Top 5 designs ranked by composite score with status
- Panel H: Correlation heatmap between quality metrics

---

## Step 9: Analyze Results

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

8. **Settings File Format Errors (KeyError)**
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
