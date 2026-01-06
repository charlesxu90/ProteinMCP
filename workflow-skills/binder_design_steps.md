# Binder Design Skill Steps

## Metadata
- **Description**: Design protein binders using BindCraft with GPU-accelerated deep learning for de novo binder generation
- **Required MCPs**: scripts_mcp
- **Created**: 2024-12-24

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

## Steps

### Step 1: Explore Available Example Data

**Description**: List available example PDB files to use as targets or understand the expected input format.

**Prompt:**
> Can you list the available example data files for BindCraft using the scripts_mcp server? Show me what files are available and their paths.

**Implementation Notes:**
- Use `mcp__scripts_mcp__list_example_data` tool
- Returns a list of example PDB files with paths and descriptions
- Use example files for testing the workflow before using your own targets

**Expected Output:**
- List of example files with paths
- PDL1.pdb is typically available as a default example

---

### Step 2: Explore Default Configurations

**Description**: Get information about available configuration files and their settings.

**Prompt:**
> Can you show me the available default configurations for BindCraft using the scripts_mcp server? I want to understand what settings are available.

**Implementation Notes:**
- Use `mcp__scripts_mcp__get_default_configs` tool
- Returns available config files and their settings
- Useful for understanding optimization parameters

**Expected Output:**
- List of config files with descriptions
- Settings for each configuration type

---

### Step 3: Setup Results Directory

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

### Step 4: Generate Configuration from Target PDB

**Description**: Analyze the target PDB structure and generate an optimized configuration file.

**Prompt:**
> Can you generate a BindCraft configuration for my target protein at {TARGET_PDB}? Target chain(s) {TARGET_CHAINS} and aim for a binder of length {BINDER_LENGTH}. Save the config to {RESULTS_DIR}/config.json.
> Please convert relative paths to absolute paths before calling the MCP server.

**Implementation Notes:**
- Use `mcp__scripts_mcp__generate_config` tool
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

### Step 5: Quick Design (Single Binder)

**Description**: Run a quick synchronous design to generate a single binder for testing.

**Prompt:**
> Can you run a quick binder design for my target at {TARGET_PDB} using BindCraft? Design one binder targeting chain(s) {TARGET_CHAINS} with binder length {BINDER_LENGTH}. Save results to {RESULTS_DIR}/quick_test/.
> Please convert relative paths to absolute paths before calling the MCP server.

**Implementation Notes:**
- Use `mcp__scripts_mcp__quick_design` tool
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

### Step 6: Submit Async Design Job (Multiple Binders)

**Description**: Submit an asynchronous job for generating multiple binder designs.

**Prompt:**
> Can you submit an async binder design job for {TARGET_PDB} using BindCraft? Generate {NUM_DESIGNS} designs targeting chain(s) {TARGET_CHAINS} with binder length {BINDER_LENGTH}. Save results to {RESULTS_DIR}/designs/. Use the config file at {RESULTS_DIR}/config.json if available.
> Please convert relative paths to absolute paths before calling the MCP server.

**Implementation Notes:**
- Use `mcp__scripts_mcp__submit_async_design` tool
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

### Step 7: Monitor Job Progress

**Description**: Check the progress of running design jobs.

**Prompt:**
> Can you check the status of my BindCraft design job with ID {job_id}? Also show me the recent log output.

**Implementation Notes:**
- Use `mcp__scripts_mcp__get_job_status` to check job status
- Use `mcp__scripts_mcp__get_job_log` to view logs
- Alternative: Use `mcp__scripts_mcp__monitor_progress` for directory-based monitoring
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

### Step 8: List All Jobs

**Description**: View all submitted jobs and their statuses.

**Prompt:**
> Can you list all BindCraft jobs I've submitted? Show me their statuses.

**Implementation Notes:**
- Use `mcp__scripts_mcp__list_jobs` tool
- Optional parameter:
  - `status`: Filter by status (pending, running, completed, failed, cancelled)

**Expected Output:**
- List of all jobs with IDs, names, and statuses
- Timestamps for job creation and completion

---

### Step 9: Get Job Results

**Description**: Retrieve the results of a completed design job.

**Prompt:**
> Can you get the results of my completed BindCraft job with ID {job_id}?

**Implementation Notes:**
- Use `mcp__scripts_mcp__get_job_result` tool
- Parameters:
  - `job_id`: The job ID of a completed job
- Only works for completed jobs

**Expected Output:**
- Design results including:
  - Output file paths
  - Design metrics and scores
  - Any errors or warnings

---

### Step 10: Batch Design (Multiple Targets)

**Description**: Submit batch processing for multiple target proteins.

**Prompt:**
> I have multiple target PDB files in {INPUT_DIR}. Can you submit a batch BindCraft job to design binders for all of them? Generate {NUM_DESIGNS} designs per target, save results to {RESULTS_DIR}/batch_results/.
> Please convert relative paths to absolute paths before calling the MCP server.

**Implementation Notes:**
- Use `mcp__scripts_mcp__submit_batch_design` tool
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

### Step 11: Cancel a Job

**Description**: Cancel a running job if needed.

**Prompt:**
> Can you cancel my BindCraft job with ID {job_id}?

**Implementation Notes:**
- Use `mcp__scripts_mcp__cancel_job` tool
- Parameters:
  - `job_id`: The job ID to cancel
- Only affects running or pending jobs

**Expected Output:**
- Confirmation of job cancellation
- Final job status

---

### Step 12: Analyze Results

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

### Step 13: Visualize Results

**Description**: Generate publication-ready figures showcasing design quality and workflow.

**Prompt:**
> Can you generate visualization figures for the binder design results in {RESULTS_DIR}/? Create a main figure showing quality metrics, a supplementary figure with detailed analysis, and a workflow overview diagram.

**Implementation Notes:**
- Use the standalone figure generation script:
  ```bash
  python workflow-skills/figures/binder_design_figures.py --results_dir {RESULTS_DIR}
  ```
- Or run the embedded Python code from the full binder_design.md documentation

**Expected Output:**
- `{RESULTS_DIR}/binder_design_main.pdf/png` - Main quality metrics figure (4-panel)
- `{RESULTS_DIR}/binder_design_supplementary.pdf/png` - Detailed analysis figure
- `{RESULTS_DIR}/binder_workflow_overview.pdf/png` - Workflow schematic diagram

**Figure Contents:**
- *Main Figure*: pLDDT distribution, pAE comparison, interface score ranking, pTM scores
- *Supplementary*: Quality heatmap, metric correlations, score distribution, selection summary
- *Workflow Overview*: BindCraft pipeline diagram (Target → RFdiffusion → ProteinMPNN → AlphaFold2)

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
   - Reinstall if needed: `pmcp install scripts_mcp`
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

---

## References

- BindCraft: https://github.com/martinpacesa/BindCraft
- RFdiffusion: https://github.com/RosettaCommons/RFdiffusion
- ProteinMPNN: https://github.com/dauparas/ProteinMPNN
- AlphaFold: https://github.com/google-deepmind/alphafold
