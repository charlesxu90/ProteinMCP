---
title: MCP Catalog
layout: default
nav_order: 4
has_children: true
---

# MCP Catalog
{: .no_toc }

ProteinMCP includes **38 MCP servers**: 24 local tool-MCPs developed in-house and 14 public community MCPs.

---

## Quick Reference

```bash
pmcp avail             # List all available MCPs
pmcp info <name>       # Show MCP details (tools, runtime, description)
pmcp install <name>    # Install and register an MCP
pmcp status            # Show installed/registered status for all MCPs
```

## Runtime Types

| Runtime | Install method | GPU | MCPs |
|---------|---------------|-----|------|
| **Python** | `quick_setup.sh` creates local `env/` venv | No | msa_mcp, mmseqs2_mcp, interpro_mcp, alphafold2_mcp, alphafold3_mcp, ... |
| **Docker** | `docker build` or `docker pull` | Yes | esm_mcp, prottrans_mcp, plmc_mcp, ev_onehot_mcp, bindcraft_mcp, boltzgen_mcp |

## Categories

| Category | MCPs | Description |
|----------|------|-------------|
| [Structure Prediction]({{ site.baseurl }}/mcps/structure-prediction) | 5 | AlphaFold2/3, Boltz, Chai-1, ESMFold |
| [Protein Design]({{ site.baseurl }}/mcps/protein-design) | 4 | ProteinMPNN, LigandMPNN, RFdiffusion2, Rosetta |
| [Binder Design]({{ site.baseurl }}/mcps/binder-design) | 2 | BindCraft, BoltzGen |
| [Molecular Dynamics]({{ site.baseurl }}/mcps/molecular-dynamics) | 2 | AMBER, GROMACS |
| [Fitness Modeling]({{ site.baseurl }}/mcps/fitness-modeling) | 5 | ESM, EV+OneHot, MutCompute, PLMC, ProtTrans |
| [Sequence Analysis]({{ site.baseurl }}/mcps/sequence-analysis) | 3 | MMseqs2, MSA, InterPro |
| [Immunology]({{ site.baseurl }}/mcps/immunology) | 2 | NetMHCpan, NetMHCIIpan |
| [Other Tools]({{ site.baseurl }}/mcps/other-tools) | 1 | Protein-Sol |
| [Public MCPs]({{ site.baseurl }}/mcps/public-mcps) | 14 | Community-contributed servers |
