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
RESULTS_DIR/                              # All outputs go here
├── config/                               # Generated configuration directory
│   ├── target_settings.json              # BindCraft target settings
│   ├── default_filters.json              # Default design filters
│   ├── default_4stage_multimer.json      # Default advanced settings
│   └── job_output/                       # BindCraft output (design_path)
│       ├── Accepted/                     # Accepted designs
│       │   └── Ranked/                   # Ranked PDB files (final output)
│       │       ├── 1_Binder_*.pdb        # Best design
│       │       ├── 2_Binder_*.pdb
│       │       └── ...
│       ├── Rejected/                     # Rejected designs
│       ├── MPNN/                         # MPNN sequence designs
│       ├── Trajectory/                   # Trajectory data
│       ├── final_design_stats.csv        # Final accepted design metrics
│       ├── mpnn_design_stats.csv         # All MPNN design metrics
│       ├── trajectory_stats.csv          # Trajectory-level statistics
│       ├── failure_csv.csv               # Failed design records
│       └── bindcraft_run.log             # Execution log
├── designs/                              # (reserved for user copies)
└── logs/                                 # Execution logs
```

---

## Step 1: Explore Default Configurations

**Description**: Get information about available configuration files and their settings.

**Prompt:**
> Can you show me the available default configurations for BindCraft using the bindcraft_mcp server? I want to understand what settings are available for binder design.

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__generate_config` tool with `analysis_type`: "basic" to see what settings are generated
- Returns available config options and target analysis

**Expected Output:**
- List of config options with descriptions
- Target protein analysis results

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

**Description**: Analyze the target PDB structure and generate an optimized configuration directory.

**Prompt:**
> Can you generate a BindCraft configuration for my target protein at {TARGET_PDB}? Target chain(s) {TARGET_CHAINS} and aim for a binder of length {BINDER_LENGTH}. Save the config to {RESULTS_DIR}/config/.
> Please convert relative paths to absolute paths before calling the MCP server.

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__generate_config` tool
- Parameters:
  - `input_file`: Path to target PDB
  - `output_file`: Path for config output directory
  - `chains`: Target chains
  - `binder_length`: Desired binder length
  - `validate`: true (to validate the config)
  - `analysis_type`: "basic" or "detailed"
- The tool creates a directory with `target_settings.json`, `default_filters.json`, etc.

**Expected Output:**
- `{RESULTS_DIR}/config/target_settings.json` - Generated target settings
- `{RESULTS_DIR}/config/default_filters.json` - Design filters
- `{RESULTS_DIR}/config/default_4stage_multimer.json` - Advanced settings
- Validation results if enabled

---

## Step 4: Submit Async Design Job (Multiple Binders)

**Description**: Submit an asynchronous job for generating multiple binder designs.

**Prompt:**
> Can you submit an async binder design job for {TARGET_PDB} using BindCraft? Generate {NUM_DESIGNS} designs targeting chain(s) {TARGET_CHAINS} with binder length {BINDER_LENGTH}. Save results to {RESULTS_DIR}/designs/. Use the config file at {RESULTS_DIR}/config/target_settings.json if available.
> Please convert relative paths to absolute paths before calling the MCP server.

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__bindcraft_submit` tool
- Parameters:
  - `target_pdb`: Path to target PDB
  - `output_dir`: Output directory
  - `settings_json`: Path to target_settings.json (optional)
  - `num_designs`: Number of designs
  - `target_chains`: Target chains
  - `binder_name`: Name prefix for designs
  - `min_binder_length` / `max_binder_length`: Binder length range
  - `device`: GPU device
  - `hotspot_residues`: Optional hotspot residues
- Returns a job_id and output_dir for tracking

**Expected Output:**
- Job submission confirmation with status='submitted'
- Use output_dir for monitoring with `mcp__bindcraft_mcp__bindcraft_check_status`

---

## Step 5: Monitor Job Progress

**Description**: Check the progress of running design jobs.

**Prompt:**
> Can you check the status of my BindCraft design job? The output directory is {RESULTS_DIR}/config/job_output/. Also show me the recent log output from bindcraft_run.log.

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__bindcraft_check_status` to check job status
- Parameters:
  - `output_dir`: Path to BindCraft output directory
- Returns job status, number of completed trajectories, accepted/rejected designs, and CSV stats

**Expected Output:**
- Job status (running, completed, failed, unknown)
- Number of completed trajectories and accepted designs
- Result summary when finished

---

## Step 6: Get Job Results

**Description**: Retrieve the results of a completed design job.

**Prompt:**
> Can you check the results of my completed BindCraft job in {RESULTS_DIR}/config/job_output/? List all output files and print any available design quality metrics from final_design_stats.csv.

**Implementation Notes:**
- Use `mcp__bindcraft_mcp__bindcraft_check_status` tool
- Parameters:
  - `output_dir`: Path to BindCraft output directory
- When job is complete, returns detailed summary with design statistics

**Expected Output:**
- Design results including:
  - Output file paths
  - Design metrics and scores (pLDDT, pAE, interface scores)
  - CSV statistics files available

---

## Step 7: Visualize Results

**Description**: Generate publication-ready figures showcasing design quality metrics.

**Prompt:**
> Can you generate visualization figures for the binder design results in {RESULTS_DIR}/? Create all quality assessment figures and a merged summary figure.

**Implementation Notes:**

Use the binder design visualization script. Point it at the BindCraft output directory (where `final_design_stats.csv` lives):

```bash
# The BindCraft output directory is the design_path from target_settings.json
# Typically: {RESULTS_DIR}/config/job_output/

# Run the visualization script
python @workflow-skills/scripts/binder_design_viz.py {RESULTS_DIR}/config/job_output

# Or with custom output prefix:
python @workflow-skills/scripts/binder_design_viz.py {RESULTS_DIR}/config/job_output --output {RESULTS_DIR}/binder_design
```

**Note:** The `@` paths should be resolved to absolute paths:
- `@tool-mcps/` → `<project_root>/tool-mcps/`
- `@workflow-skills/` → `<project_root>/workflow-skills/`

**Generated Figures (6 individual + 1 merged):**

1. `binder_design_plddt_comparison.png` - Bar chart comparing pLDDT scores across designs
2. `binder_design_interface_pae.png` - Bar chart of interface pAE scores
3. `binder_design_metrics_table.png` - Table showing all metrics for each design
4. `binder_design_quality_scatter.png` - Scatter plot of pLDDT vs pAE with quality zones
5. `binder_design_design_ranking.png` - Horizontal bar chart ranking designs by composite score
6. `binder_design_execution_timeline.png` - Gantt chart showing step execution times
7. `binder_design_summary.png` - **Merged 2x3 panel summary figure** (publication-ready, via `--merged`)

**Composite Quality Score Formula:**
```
Composite Score = 0.3×pLDDT(norm) + 0.2×pAE(inv,norm) + 0.3×i_pAE(inv,norm) + 0.2×i_pTM
```

**Quality Thresholds:**
- pLDDT: ≥80 (higher is better)
- pAE: ≤5 (lower is better)
- i_pAE (interface pAE): ≤10 (lower is better)
- i_pTM (interface pTM): ≥0.6 (higher is better)

**Display Results Interactively (Python):**
```python
import sys
sys.path.append("@workflow-skills/scripts")
from binder_design_viz import display_results

# Display all figures in a GUI window
display_results("{RESULTS_DIR}/config/job_output")

# Or display only the merged summary
display_results("{RESULTS_DIR}/config/job_output", show_all=False)
```

**Expected Output:**

*Individual Figures (6 files):*
- `{output_prefix}_plddt_comparison.png/.pdf` - pLDDT bar chart
- `{output_prefix}_interface_pae.png/.pdf` - Interface pAE bar chart
- `{output_prefix}_metrics_table.png/.pdf` - Metrics summary table
- `{output_prefix}_quality_scatter.png/.pdf` - pLDDT vs pAE scatter
- `{output_prefix}_design_ranking.png/.pdf` - Composite score ranking
- `{output_prefix}_execution_timeline.png/.pdf` - Execution timeline

*Merged Summary Figure (2x3 panels):*
- `{output_prefix}.png/.pdf` - **Publication-ready 6-panel figure**

**Figure Descriptions:**

*Merged Summary Figure (2x3 panels):*
- Panel 1: Design pLDDT scores with quality threshold lines
- Panel 2: Interface pAE scores (lower is better)
- Panel 3: Quality distribution scatter (pLDDT vs pAE, colored by composite score)
- Panel 4: Design ranking by composite score
- Panel 5: Design metrics summary table
- Panel 6: Execution timeline (Gantt chart)

---

## Step 8: Analyze Results

**Description**: Analyze the designed binders and compare metrics.

**Prompt:**
> Can you analyze the binder designs in {RESULTS_DIR}/config/job_output/? Summarize the key metrics and identify the best candidates.

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
   - Use `mcp__bindcraft_mcp__bindcraft_check_status` with output_dir to verify

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
