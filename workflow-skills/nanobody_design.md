# Nanobody Design Skill

Design nanobody CDR regions using BoltzGen with optimized cysteine filtering for single-domain antibodies (VHH)

---

## Prerequisites

Before running this workflow, install the skill and all required MCPs:

```bash
pskill install nanobody_design
```

This will install the following MCP servers:
- `boltzgen_mcp` - Boltzgen Mcp

**Verify MCPs are installed:**
```bash
pmcp status
```

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

## Step 0: Setup Results Directory

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

## Step 1: Prepare BoltzGen Configuration

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

## Step 2: Validate Configuration

**Description**: Validate the BoltzGen configuration file before running the design.

**Prompt:**
> Can you validate the BoltzGen configuration at {RESULTS_DIR}/config.yaml? Check that the target CIF file exists and the YAML structure is correct.
> Please convert the relative path to absolute path before executing.

**Implementation Notes:**
- Read the config.yaml and verify:
  - Target CIF file path exists
  - Chain ID is valid
  - YAML structure has correct `entities` format
  - Scaffold YAML files exist (if specified)
- Use Bash/Read tools to validate file existence and YAML syntax

**Expected Output:**
- Validation status (valid/invalid)
- Any errors or warnings about the configuration

---

## Step 3: Submit Nanobody Design Job

**Description**: Submit the nanobody CDR design job using BoltzGen with the nanobody-anything protocol.

**Prompt:**
> Can you submit a nanobody design job using BoltzGen with the configuration at {RESULTS_DIR}/config.yaml?
> Use the nanobody-anything protocol with {NUM_DESIGNS} designs and budget {BUDGET}.
> Save the outputs to {RESULTS_DIR}/designs/.
> Please convert the relative path to absolute path before calling the MCP server.

**Implementation Notes:**
- Use `mcp__boltzgen_mcp__boltzgen_submit` tool
- Parameters:
  - `config`: {RESULTS_DIR}/config.yaml
  - `output`: {RESULTS_DIR}/designs
  - `protocol`: "nanobody-anything" (specialized for nanobody CDR design)
  - `num_designs`: {NUM_DESIGNS}
  - `budget`: {BUDGET}
- GPU is automatically assigned from the pool (no need to specify cuda_device)
- The nanobody-anything protocol:
  - Filters cysteines from design
  - Optimized for single-domain antibodies (VHH)
  - Specialized for CDR loop design

**Expected Output:**
- Job submission with status='queued', job_id, and queue position
- Use job_id or output_dir for monitoring progress

---

## Step 4: Monitor Job Progress

**Description**: Check the status of the submitted nanobody design job.

**Prompt:**
> Can you check the status of my BoltzGen nanobody design job with ID {job_id}? Also show me the recent log output.

**Implementation Notes:**
- Use `mcp__boltzgen_mcp__boltzgen_job_status` to check by job_id
  - Parameters: `job_id` (from submission)
- Or use `mcp__boltzgen_mcp__boltzgen_check_status` to check by output directory
  - Parameters: `output_dir` ({RESULTS_DIR}/designs)
- Use `mcp__boltzgen_mcp__boltzgen_queue_status` to see overall queue state

**Expected Output:**
- Job status (running, completed, failed, unknown)
- Number of generated designs (PDB files)
- Result summary when finished

---

## Step 5: Get Job Results

**Description**: Retrieve the results of the completed nanobody design job.

**Prompt:**
> Can you get the results of my completed BoltzGen nanobody design job? Check the output at {RESULTS_DIR}/designs/ and list all generated PDB files and metrics.

**Implementation Notes:**
- Use `mcp__boltzgen_mcp__boltzgen_check_status` tool
- Parameters:
  - `output_dir`: {RESULTS_DIR}/designs
- Returns detailed summary when job is complete

**Expected Output:**
- List of generated PDB files
- Design metrics and scores
- Job configuration and parameters

---

## Step 6: Analyze Designed Nanobodies

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

---

## References

- BoltzGen: https://github.com/jwohlwend/boltzgen
- Boltz2 Structure Prediction: https://github.com/jwohlwend/boltz
- Nanobody Resources: https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/

---

## Cleanup

When you're done with the workflow, uninstall the skill and all its MCPs:

```bash
pskill uninstall nanobody_design
```
