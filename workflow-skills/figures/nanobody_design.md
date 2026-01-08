# Nanobody Design Workflow Summary

Design nanobody CDR regions using BoltzGen with optimized cysteine filtering for single-domain antibodies (VHH).

---

## 1. Workflow Overview

The nanobody design workflow consists of 8 steps using the BoltzGen MCP server:

| Step | Name | Description | MCP Tool |
|------|------|-------------|----------|
| 0 | Setup Results Directory | Create output directory structure | - |
| 1 | Prepare BoltzGen Config | Generate YAML configuration file | - |
| 2 | Validate Configuration | Check config validity before running | `validate_config` |
| 3 | Submit Design Job | Launch nanobody-anything protocol | `submit_generic_boltzgen` |
| 4 | Monitor Progress | Check job status and logs | `get_job_status`, `get_job_log` |
| 5 | Get Job Results | Retrieve completed designs | `get_job_result` |
| 6 | Analyze Nanobodies | Summarize and evaluate designs | - |
| 7 | Visualize Results | Generate publication-ready figures | - |

### Workflow Diagram

```
Target Structure → Configuration → BoltzGen MCP → CDR Design → Nanobody PDBs
    (CIF/PDB)        (YAML)      (nanobody-anything)  (Cys-filtered)
```

---

## 2. Design Metrics Summary

### Input Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `TARGET_CIF` | Target protein structure (CIF/PDB format) | Required |
| `TARGET_CHAIN` | Target chain ID to design against | Required |
| `NANOBODY_SCAFFOLDS` | List of scaffold YAML files | Optional (uses defaults) |
| `NUM_DESIGNS` | Number of nanobody designs to generate | 10 |
| `BUDGET` | Computational budget (higher = more diverse) | 2 |
| `CUDA_DEVICE` | GPU device to use | 0 |

### Output Metrics

| Metric | CSV Column | Description | Quality Indicator |
|--------|------------|-------------|-------------------|
| pTM | `design_ptm` | Predicted template modeling score | Higher is better (>0.8 good) |
| iPTM | `design_to_target_iptm` | Interface predicted TM score | Higher is better (>0.5 good) |
| pAE | `min_design_to_target_pae` | Predicted aligned error at interface | Lower is better (<5 good) |
| H-bonds | `plip_hbonds_refolded` | Hydrogen bonds at interface | Higher is better (>=3 good) |
| delta_SASA | `delta_sasa_refolded` | Buried surface area change | Higher is better (>400 good) |
| Quality Score | `quality_score` | Pre-computed composite quality | Higher is better |
| Status | `pass_filters` | Passed BoltzGen quality filters | True = Passed |

---

## 3. Generation Procedure

### BoltzGen Pipeline Steps

The `nanobody-anything` protocol runs a multi-step pipeline:

| Step | Name | Description |
|------|------|-------------|
| 1 | **design** | Generate nanobody backbone conformations using Boltz structure models |
| 2 | **inverse_folding** | Design amino acid sequence for backbone (with cysteine filtering) |
| 3 | **folding** | Predict/validate the designed structure with Boltz folding |
| 4 | **design_folding** | Iterative design-fold optimization for improved quality |
| 5 | **affinity** | Evaluate binding affinity predictions |
| 6 | **analysis** | Quality assessment, ranking, and filtering |

### Step-by-Step Process

1. **Input Preparation**
   - Provide target protein structure (CIF or PDB format)
   - Specify target chain ID with clear binding interface
   - Optionally provide custom nanobody scaffolds

2. **Configuration Generation**
   ```yaml
   entities:
     - file:
         path: {TARGET_CIF}
         include:
           - chain:
               id: {TARGET_CHAIN}
     # Optional scaffolds
     - file:
         path:
           - scaffold1.yaml
           - scaffold2.yaml
   ```

3. **BoltzGen Execution**
   - Protocol: `nanobody-anything` (specialized for VHH antibodies)
   - Uses Boltz models for structure generation and validation
   - Inverse folding with cysteine filtering for sequence design
   - Iterative optimization of CDR loop regions
   - GPU-accelerated end-to-end pipeline

4. **Output Generation**
   - Multiple nanobody-target complex PDB structures
   - Each design contains optimized CDR loops
   - Structures ready for downstream validation

### Directory Structure

```
RESULTS_DIR/
├── config.yaml              # BoltzGen configuration
├── designs/                 # Designed nanobody structures
│   ├── final_ranked_designs/
│   │   ├── all_designs_metrics.csv  # Quality metrics for all designs
│   │   ├── design_001.pdb           # Nanobody-target complex
│   │   ├── design_002.pdb
│   │   └── ...
│   └── ...
├── figures/                 # Visualization outputs
│   ├── nanobody_design_quality_score.png
│   ├── nanobody_design_structure_quality.png
│   ├── nanobody_design_normalized_heatmap.png
│   ├── nanobody_design_statistics_table.png
│   ├── nanobody_design_quality_boxplot.png
│   ├── nanobody_design_interface_metrics.png
│   ├── nanobody_design_top5_designs.png
│   ├── nanobody_design_correlation.png
│   └── nanobody_design_summary.png   # Merged 8-panel figure
└── logs/                    # Execution logs
```

---

## 4. Filtering Steps and Thresholds

### Built-in Filters (nanobody-anything protocol)

| Filter | Description | Rationale |
|--------|-------------|-----------|
| **Cysteine Filtering** | Removes cysteine residues from CDR design | VHH antibodies lack the interchain disulfide bonds found in conventional antibodies; extra cysteines can cause aggregation |
| **CDR Loop Constraints** | Maintains framework regions | Preserves nanobody stability and folding |
| **Single-Domain Optimization** | Optimized for VHH format | Ensures designs are compatible with single-domain antibody architecture |

### Quality Thresholds for Design Selection

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| pTM | >0.8 | 0.6-0.8 | <0.6 |
| iPTM | >0.5 | 0.3-0.5 | <0.3 |
| pAE | <5 | 5-10 | >10 |
| H-bonds | >=3 | 1-2 | 0 |
| delta_SASA | >400 | 200-400 | <200 |

### Recommended Selection Criteria

1. **Primary Filter**: pTM > 0.8 AND iPTM > 0.5
2. **Secondary Filter**: pAE < 5 AND H-bonds >= 3
3. **Final Ranking**: Sort by pre-computed `quality_score`

### Quality Score

BoltzGen computes a pre-computed `quality_score` in the output CSV that combines multiple metrics for ranking designs.

---

## Key Features

- **VHH Single-Domain Design**: Optimized for camelid-derived nanobodies
- **CDR Loop Optimization**: Focused design of complementarity-determining regions
- **Cysteine Filtering**: Removes cysteines during inverse folding to prevent unwanted disulfide bonds
- **Boltz-Based Pipeline**: Uses Boltz models for structure generation, folding, and validation
- **Iterative Design-Fold**: Optimization loop for improved structure quality
- **Multiple Design Generation**: Produces diverse candidates for screening
- **Scaffold Support**: Optional custom framework regions

---

## 5. Generated Figures

The visualization script (`nanobody_design_viz.py`) produces 9 figures:

| Figure | Description |
|--------|-------------|
| `nanobody_design_quality_score.png` | Quality score distribution histogram (Passed/Failed) |
| `nanobody_design_structure_quality.png` | iPTM vs pTM scatter plot colored by pAE |
| `nanobody_design_normalized_heatmap.png` | Normalized metrics heatmap per design |
| `nanobody_design_statistics_table.png` | Statistics table (Mean, Std, Min, Max) |
| `nanobody_design_quality_boxplot.png` | Boxplots with threshold lines |
| `nanobody_design_interface_metrics.png` | H-bonds vs delta_SASA scatter colored by iPTM |
| `nanobody_design_top5_designs.png` | Top 5 designs ranked by quality score |
| `nanobody_design_correlation.png` | Correlation heatmap of metrics |
| `nanobody_design_summary.png` | **Merged 8-panel publication-ready figure** |

### Usage

```bash
python workflow-skills/scripts/nanobody_design_viz.py <results_dir> [--output PREFIX] [--display]
```

### Example

```bash
python workflow-skills/scripts/nanobody_design_viz.py results/nanobody_design/
```

---

## BoltzGen vs BindCraft Comparison

| Aspect | BoltzGen (Nanobody) | BindCraft (Binder) |
|--------|---------------------|-------------------|
| Structure Generation | Boltz models | AF2 Hallucination |
| Sequence Design | Inverse folding | ProteinMPNN |
| Validation | Boltz folding | AF2 Prediction |
| Scoring | Built-in affinity | PyRosetta |
| Cysteine Filtering | Yes (protocol-specific) | No |

---

## References

- BoltzGen: https://github.com/jwohlwend/boltzgen
- Boltz Structure Prediction: https://github.com/jwohlwend/boltz
- Nanobody Resources: https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/
