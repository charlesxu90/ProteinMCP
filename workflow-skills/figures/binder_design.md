# Binder Design Workflow Summary

Design protein binders using BindCraft with GPU-accelerated deep learning for de novo binder generation.

---

## 1. Workflow Overview

The binder design workflow consists of 13 steps using the BindCraft MCP server:

| Step | Name | Description | MCP Tool |
|------|------|-------------|----------|
| 1 | Explore Example Data | List available example PDB files | `list_example_data` |
| 2 | Explore Default Configs | Get available configuration settings | `get_default_configs` |
| 3 | Setup Results Directory | Create output directory structure | - |
| 4 | Generate Configuration | Analyze target and create config | `generate_config` |
| 5 | Quick Design | Run synchronous single binder test | `quick_design` |
| 6 | Submit Async Job | Launch multiple binder designs | `submit_async_design` |
| 7 | Monitor Progress | Check job status and logs | `get_job_status`, `get_job_log` |
| 8 | List All Jobs | View all submitted jobs | `list_jobs` |
| 9 | Get Job Results | Retrieve completed designs | `get_job_result` |
| 10 | Batch Design | Process multiple targets | `submit_batch_design` |
| 11 | Cancel Job | Stop running jobs | `cancel_job` |
| 12 | Analyze Results | Summarize metrics and rank candidates | - |
| 13 | Visualize Results | Generate publication-ready figures | - |

### Workflow Diagram

```
Target PDB → Config Generation → BindCraft MCP → Design Validation → Binder PDBs
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
            AF2 Hallucination   ProteinMPNN      AF2 Prediction
              (Structure)        (Sequence)       (Validation)
                                      │
                                      ▼
                              PyRosetta Scoring
                               (Interface)
```

---

## 2. Design Metrics Summary

### Input Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `TARGET_PDB` | Target protein PDB file | Required |
| `TARGET_CHAINS` | Target chains to design binders for | Required |
| `BINDER_LENGTH` | Length of designed binder sequence | 130 |
| `NUM_DESIGNS` | Number of binder designs to generate | 3 |
| `HOTSPOT_RESIDUES` | Specific residues to target | Optional |
| `GPU_DEVICE` | GPU device to use | 0 |
| `CONFIG_FILE` | Custom configuration file | Optional |

### Output Metrics

| Metric | Description | Quality Indicator |
|--------|-------------|-------------------|
| pLDDT | Predicted local distance difference test | Higher is better (>80 good) |
| pAE | Predicted aligned error | Lower is better (<5 good) |
| pTM | Predicted template modeling score | Higher is better (>0.8 good) |
| Interface Score | Binding interface quality (REU) | More negative is better (<-10 good) |
| Binding Energy | Predicted binding affinity | More negative is better |
| Interface Buried SASA | Buried surface area at interface | Higher indicates more contacts |

---

## 3. Generation Procedure

### Step-by-Step Process

1. **Input Preparation**
   - Provide clean target protein PDB file
   - Remove heteroatoms and waters (unless needed)
   - Ensure proper chain ID assignments
   - Optionally specify hotspot residues for targeted binding

2. **Configuration Generation**
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

3. **BindCraft Pipeline Execution**
   - **AF2 Hallucination**: Generates binder backbone conformations
   - **ProteinMPNN**: Designs optimal amino acid sequences for the backbone
   - **AF2 Prediction**: Validates designed binders with structure prediction
   - **PyRosetta Scoring**: Evaluates interface quality and binding energy
   - Supports multiple design algorithms: 2stage, 3stage, 4stage, greedy, mcmc

4. **Output Generation**
   - Multiple binder-target complex PDB structures
   - Quality metrics in `metrics.csv`
   - Detailed logs for troubleshooting

### Directory Structure

```
RESULTS_DIR/
├── config.json              # Generated configuration
├── designs/                 # Designed binder structures
│   ├── design_001.pdb      # Binder-target complex
│   ├── design_002.pdb
│   └── ...
├── metrics.csv              # Design quality metrics
└── logs/                    # Execution logs
```

---

## 4. Filtering Steps and Thresholds

### Quality Thresholds for Design Selection

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| pLDDT | ≥80 | 70-80 | <70 |
| pAE | ≤4 | 4-10 | >10 |
| pTM | ≥0.8 | 0.6-0.8 | <0.6 |
| Interface Score | ≤-13 REU | -13 to 0 | >0 |

### Recommended Selection Criteria

1. **Primary Filter**: pLDDT ≥ 80 AND pAE ≤ 5
2. **Secondary Filter**: Interface Score < -10 REU
3. **Tertiary Filter**: pTM ≥ 0.8
4. **Final Ranking**: Sort by composite quality score

### Composite Quality Score Formula

```
Quality Score = 0.3 × pLDDT(norm) + 0.3 × pAE(inv,norm) + 0.2 × Interface(inv,norm) + 0.2 × pTM

Where:
- pLDDT(norm) = pLDDT / 100
- pAE(inv,norm) = 1 - (pAE / 20)
- Interface(inv,norm) = 1 - (Interface + 20) / 20
```

### Pass Rate Calculation

For each metric, calculate the percentage of designs meeting the "Good" threshold:
- pLDDT Pass Rate = (designs with pLDDT ≥ 80) / total designs
- pAE Pass Rate = (designs with pAE ≤ 4) / total designs
- Interface Pass Rate = (designs with Interface ≤ -13) / total designs
- High-Quality = designs passing ALL primary criteria

---

## Key Features

- **De Novo Design**: Creates entirely new protein binders from scratch
- **Multi-Stage Pipeline**: AF2 Hallucination → ProteinMPNN → AF2 Prediction → PyRosetta
- **Multiple Algorithms**: 2stage, 3stage, 4stage, greedy, mcmc design strategies
- **Hotspot Targeting**: Specify key residues for focused binding
- **Batch Processing**: Design binders for multiple targets simultaneously
- **Async Execution**: Submit jobs and monitor progress asynchronously
- **Quality Validation**: Built-in AlphaFold2 structure prediction and PyRosetta scoring

---

## Generated Figures

The visualization script produces 9 figures:

| Figure | Description |
|--------|-------------|
| `binder_design_composite_score.png` | Composite score distribution histogram |
| `binder_design_quality_assessment.png` | pLDDT vs Interface scatter plot |
| `binder_design_normalized_heatmap.png` | Normalized metrics heatmap per design |
| `binder_design_statistics_table.png` | Statistics table (Mean, Std, Min, Max, Pass Rate) |
| `binder_design_quality_boxplot.png` | Boxplots with threshold lines |
| `binder_design_sasa_binding_energy.png` | SASA vs Binding Energy scatter |
| `binder_design_top5_designs.png` | Top 5 designs ranked by composite score |
| `binder_design_correlation.png` | Correlation heatmap of metrics |
| `binder_design_summary.png` | **Merged 8-panel publication-ready figure** |

---

## References

- BindCraft: https://github.com/martinpacesa/BindCraft
- AlphaFold2: https://github.com/google-deepmind/alphafold
- ProteinMPNN: https://github.com/dauparas/ProteinMPNN
- PyRosetta: https://www.pyrosetta.org/
