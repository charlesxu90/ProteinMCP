# Nanobody Design Skill Steps

## Metadata
- **Description**: Design nanobody CDR regions using BoltzGen with optimized cysteine filtering for single-domain antibodies (VHH)
- **Required MCPs**: boltzgen_mcp
- **Created**: 2025-12-25

---

## Configuration Parameters

```yaml
# Required Inputs
TARGET_CIF: "@examples/data/target.cif"         # Target protein structure (CIF or PDB format)
TARGET_CHAIN: "A"                                # Target chain ID to design nanobody against
NANOBODY_SCAFFOLDS: []                          # List of nanobody scaffold YAML files (optional)

# Output Settings
RESULTS_DIR: "@results/nanobody_design"          # Output directory for all results
JOB_NAME: "nanobody_design"                      # Name for tracking the design job

# Design Parameters
NUM_DESIGNS: 10                                  # Number of nanobody designs to generate
BUDGET: 2                                        # Computational budget (higher = more diverse designs)
CUDA_DEVICE: 0                                   # GPU device to use (optional)
```

**Target Structure Requirements:**
- CIF or PDB file with target protein structure
- Target chain should be well-defined with clear binding interface
- Nanobody scaffolds (optional) define the framework regions

**Directory Structure:**
```
RESULTS_DIR/                     # All outputs go here
├── config.yaml                  # Generated BoltzGen configuration
├── designs/                     # Designed nanobody structures
│   ├── design_001.pdb          # Nanobody-target complex
│   ├── design_002.pdb
│   └── ...
└── logs/                        # Execution logs
```

---

## Steps

### Step 0: Setup Results Directory

**Description**: Create the output directory structure for the nanobody design workflow.

**Prompt:**
> Please setup the results directory at {RESULTS_DIR} for nanobody design. Create the necessary subdirectories.
> Please convert the relative path to absolute path before executing.

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

### Step 1: Prepare BoltzGen Configuration

**Description**: Create a BoltzGen YAML configuration file for nanobody design targeting the specified protein.

**Prompt:**
> I want to design nanobodies targeting the protein structure at {TARGET_CIF}, chain {TARGET_CHAIN}. Please create a BoltzGen configuration file at {RESULTS_DIR}/config.yaml.
> The configuration should specify:
> - The target protein structure and chain
> - Nanobody scaffold files if provided: {NANOBODY_SCAFFOLDS}
> Please convert the relative path to absolute path before executing.

**Implementation Notes:**
- Create a YAML configuration file with the following structure:
  ```yaml
  entities:
    - file:
        path: {TARGET_CIF}
        include:
          - chain:
              id: {TARGET_CHAIN}

    # If using scaffolds:
    - file:
        path:
          - scaffold1.yaml
          - scaffold2.yaml
  ```
- If no scaffolds are provided, BoltzGen will use default nanobody scaffolds

**Expected Output:**
- `{RESULTS_DIR}/config.yaml` - BoltzGen configuration file

---

### Step 2: Validate Configuration

**Description**: Validate the BoltzGen configuration file before running the design.

**Prompt:**
> Can you validate the BoltzGen configuration at {RESULTS_DIR}/config.yaml using the boltzgen_mcp server?
> Please convert the relative path to absolute path before calling the MCP server.

**Implementation Notes:**
- Use `mcp__boltzgen_mcp__validate_config` tool
- Parameters:
  - `config_file`: Path to the config.yaml file
  - `verbose`: true (for detailed validation output)

**Expected Output:**
- Validation status (valid/invalid)
- Any errors or warnings about the configuration

---

### Step 3: Submit Nanobody Design Job

**Description**: Submit the nanobody CDR design job using BoltzGen with the nanobody-anything protocol.

**Prompt:**
> Can you submit a nanobody design job using BoltzGen with the configuration at {RESULTS_DIR}/config.yaml?
> Use the nanobody-anything protocol with {NUM_DESIGNS} designs and budget {BUDGET}.
> Save the outputs to {RESULTS_DIR}/designs/.
> Please convert the relative path to absolute path before calling the MCP server.

**Implementation Notes:**
- Use `mcp__boltzgen_mcp__submit_generic_boltzgen` tool
- Parameters:
  - `config_file`: {RESULTS_DIR}/config.yaml
  - `output_dir`: {RESULTS_DIR}/designs
  - `protocol`: "nanobody-anything" (specialized for nanobody CDR design)
  - `num_designs`: {NUM_DESIGNS}
  - `budget`: {BUDGET}
  - `cuda_device`: {CUDA_DEVICE} (optional)
  - `job_name`: {JOB_NAME}
- The nanobody-anything protocol:
  - Filters cysteines from design
  - Optimized for single-domain antibodies (VHH)
  - Specialized for CDR loop design

**Expected Output:**
- Job ID for tracking the design process
- Use this job_id for monitoring progress

---

### Step 4: Monitor Job Progress

**Description**: Check the status of the submitted nanobody design job.

**Prompt:**
> Can you check the status of my BoltzGen nanobody design job with ID {job_id}? Also show me the recent log output.

**Implementation Notes:**
- Use `mcp__boltzgen_mcp__get_job_status` to check job status
- Use `mcp__boltzgen_mcp__get_job_log` to view logs
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

### Step 5: Get Job Results

**Description**: Retrieve the results of the completed nanobody design job.

**Prompt:**
> Can you get the results of my completed BoltzGen nanobody design job with ID {job_id}?

**Implementation Notes:**
- Use `mcp__boltzgen_mcp__get_job_result` tool
- Parameters:
  - `job_id`: The job ID of a completed job
- Only works for completed jobs

**Expected Output:**
- List of generated PDB files
- Design metrics and scores
- Any errors or warnings

---

### Step 6: Analyze Designed Nanobodies

**Description**: Analyze the designed nanobody structures and summarize results.

**Prompt:**
> Can you analyze the nanobody designs in {RESULTS_DIR}/designs/? List all generated PDB files and summarize the results.

**Implementation Notes:**
- List PDB files in the output directory
- Each design is a nanobody-target complex
- Nanobody CDR regions have been designed while maintaining framework

**Expected Output:**
- List of PDB files with designed nanobodies
- Summary of number of designs
- Recommendations for further validation

---

## Troubleshooting

### Common Issues

1. **Configuration File Not Found**
   - Ensure the target structure file exists at the specified path
   - Check that file paths are absolute, not relative
   - Verify the file extension (.cif or .pdb)

2. **Invalid Chain ID**
   - Check that the specified chain exists in the target structure
   - Use a molecular viewer to identify correct chain IDs

3. **Job Fails to Start**
   - Check GPU availability: `nvidia-smi`
   - Verify CUDA device is correctly specified
   - Ensure sufficient GPU memory (nanobody design needs ~8GB)

4. **Low Quality Designs**
   - Increase the budget parameter for more diverse designs
   - Try different nanobody scaffolds
   - Ensure target structure is high quality

5. **MCP Connection Errors**
   - Verify MCP is registered: `pmcp status`
   - Reinstall if needed: `pmcp install boltzgen_mcp`
   - Check server logs for errors

6. **BoltzGen Not Found**
   - Ensure boltzgen is installed in the MCP environment
   - Run: `pmcp install boltzgen_mcp` to reinstall

7. **Scaffold Files Not Found**
   - Scaffolds are optional - BoltzGen has built-in defaults
   - If using custom scaffolds, ensure paths are correct

8. **Out of Memory**
   - Reduce num_designs parameter
   - Use a GPU with more memory
   - Run designs in smaller batches

---

## References

- BoltzGen: https://github.com/jwohlwend/boltzgen
- Boltz2 Structure Prediction: https://github.com/jwohlwend/boltz
- Nanobody Resources: https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/
