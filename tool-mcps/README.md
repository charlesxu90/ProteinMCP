# MCP Servers

ProteinMCP includes 38 MCP servers: 24 local tool-MCPs developed in-house and 14 public community MCPs.

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

### Installing Docker MCPs (local build recommended)

Local builds are faster than pulling from the registry:

```bash
# Build all Docker MCPs locally
cd tool-mcps/esm_mcp && docker build -t esm_mcp:latest . && cd ../..
cd tool-mcps/prottrans_mcp && docker build -t prottrans_mcp:latest . && cd ../..
cd tool-mcps/plmc_mcp && docker build -t plmc_mcp:latest . && cd ../..
cd tool-mcps/ev_onehot_mcp && docker build -t ev_onehot_mcp:latest . && cd ../..
cd tool-mcps/bindcraft_mcp && docker build -t bindcraft_mcp:latest . && cd ../..
cd tool-mcps/boltzgen_mcp && docker build -t boltzgen_mcp:latest . && cd ../..

# Register with Claude Code (detects local image, skips pull)
pmcp install esm_mcp
pmcp install prottrans_mcp
pmcp install plmc_mcp
pmcp install ev_onehot_mcp
pmcp install bindcraft_mcp
pmcp install boltzgen_mcp
```

### Installing Python MCPs

```bash
pmcp install msa_mcp          # Runs quick_setup.sh, creates local env/
pmcp install mmseqs2_mcp
```

---

## MCP Servers Developed in ProteinMCP

### Structure Prediction
| MCP | Runtime | Description |
|-----|---------|-------------|
| [AlphaFold2 MCP](https://github.com/Biomolecular-Design-Nexus/alphafold2_mcp) | python | Protein structure prediction, supporting complex and batch predictions |
| [AlphaFold3 MCP](https://github.com/Biomolecular-Design-Nexus/alphafold3_mcp) | python | Protein structure prediction, supporting batch prediction |
| [Boltz MCP](https://github.com/Biomolecular-Design-Nexus/boltz_mcp) | python | Boltz2 for protein structure and affinity prediction |
| [Chai-1 MCP](https://github.com/Biomolecular-Design-Nexus/chai1_mcp) | python | Chai-1 for protein structure prediction |
| [ESMFold MCP](https://github.com/Biomolecular-Design-Nexus/esmfold_mcp) | python | ESMFold for protein structure prediction |

### Protein Design
| MCP | Runtime | Description |
|-----|---------|-------------|
| [ProteinMPNN MCP](https://github.com/Biomolecular-Design-Nexus/proteinmpnn_mcp) | python | ProteinMPNN for protein design (inverse folding) |
| [LigandMPNN MCP](https://github.com/Biomolecular-Design-Nexus/ligandmpnn_mcp) | python | LigandMPNN for ligand-aware scaffold-based sequence generation |
| [RFdiffusion2 MCP](https://github.com/Biomolecular-Design-Nexus/rfdiffusion2_mcp) | python | RFdiffusion2 for protein structure generation (backbone) |
| [Rosetta MCP](https://github.com/Biomolecular-Design-Nexus/rosetta_mcp) | python | Rosetta molecular modeling and protein design suite |

### Binder Design
| MCP | Runtime | Description |
|-----|---------|-------------|
| [BindCraft MCP](https://github.com/Biomolecular-Design-Nexus/bindcraft_mcp) | docker | BindCraft for protein binder design (RFdiffusion + ProteinMPNN + AF2) |
| [BoltzGen MCP](https://github.com/Biomolecular-Design-Nexus/boltzgen_mcp) | docker | BoltzGen for nanobody CDR loop design |

### Molecular Dynamics
| MCP | Runtime | Description |
|-----|---------|-------------|
| [AMBER MCP](https://github.com/Biomolecular-Design-Nexus/amber_mcp) | python | AMBER for MD simulations and analysis |
| [GROMACS MCP](https://github.com/Biomolecular-Design-Nexus/gromacs_mcp) | python | GROMACS 2025.4 for molecular dynamics simulations |

### Fitness Modeling & Mutation Prediction
| MCP | Runtime | Description |
|-----|---------|-------------|
| [ESM MCP](https://github.com/Biomolecular-Design-Nexus/esm_mcp) | docker | ESM for protein embedding and fitness modeling |
| [EV+Onehot MCP](https://github.com/Biomolecular-Design-Nexus/ev_onehot_mcp) | docker | Protein fitness prediction (evolutionary coupling + one-hot encoding) |
| [MutCompute MCP](https://github.com/Biomolecular-Design-Nexus/mutcompute_mcp) | python | MutCompute for protein mutation effect prediction |
| [PLMC MCP](https://github.com/Biomolecular-Design-Nexus/plmc_mcp) | docker | Evolutionary coupling analysis using PLMC |
| [ProtTrans MCP](https://github.com/Biomolecular-Design-Nexus/prottrans_mcp) | docker | ProtTrans for protein embeddings and fitness modeling |

### Sequence Analysis
| MCP | Runtime | Description |
|-----|---------|-------------|
| [MMseqs2 MCP](https://github.com/Biomolecular-Design-Nexus/mmseqs2_mcp) | python | Sequence search, clustering, and MSA generation using MMseqs2 |
| [MSA MCP](https://github.com/Biomolecular-Design-Nexus/msa_mcp) | python | Generate Multiple Sequence Alignments (MSA) using ColabFold server |
| [InterPro MCP](https://github.com/Biomolecular-Design-Nexus/interpro_mcp) | python | InterProScan for protein domain and functional analysis |

### Immunology (MHC Binding Prediction)
| MCP | Runtime | Description |
|-----|---------|-------------|
| [NetMHCpan MCP](https://github.com/Biomolecular-Design-Nexus/netmhcpan_mcp) | python | NetMHCpan-4.2 for MHC Class I binding prediction |
| [NetMHCIIpan MCP](https://github.com/Biomolecular-Design-Nexus/netmhc2pan_mcp) | python | NetMHCIIpan-4.3 for MHC Class II binding prediction |

### Other Tools
| MCP | Runtime | Description |
|-----|---------|-------------|
| [Protein-Sol MCP](https://github.com/Biomolecular-Design-Nexus/protein_sol_mcp) | python | Protein-Sol for protein solubility prediction |

---

## Public MCP Servers

### [Augmented Nature](https://github.com/Augmented-Nature)
* [UniProt MCP](https://github.com/Augmented-Nature/Augmented-Nature-UniProt-MCP-Server): advanced access to the UniProt protein database with 26 specialized bioinformatics tools.
* [Alphafold DB MCP](https://github.com/Augmented-Nature/AlphaFold-MCP-Server): access to the AlphaFold Protein Structure Database.
* [PDB MCP](https://github.com/Augmented-Nature/PDB-MCP-Server): access to the Protein Data Bank (PDB) 3D structure repository.
* [STRING DB MCP](https://github.com/Augmented-Nature/STRING-db-MCP-Server): STRING protein interaction database.
* [ProteinAtlas MCP](https://github.com/Augmented-Nature/ProteinAtlas-MCP-Server): Human Protein Atlas data (expression, localization, pathology).
* [KEGG MCP](https://github.com/Augmented-Nature/KEGG-MCP-Server): KEGG database access through REST API.
* [Open Targets MCP](https://github.com/Augmented-Nature/OpenTargets-MCP-Server): Open Targets platform for gene-drug-disease associations.
* [NCBI Datasets MCP](https://github.com/Augmented-Nature/NCBI-Datasets-MCP-Server): NCBI Datasets API with 31 specialized tools.

### Other MCP Servers
* [PyMOL MCP](https://github.com/vrtejus/pymol-mcp): AI agents interact with and control PyMOL.
* [Arxiv MCP](https://github.com/blazickjp/arxiv-mcp-server): search and access arXiv papers.
* [PubMed MCP](https://github.com/JackKuo666/PubMed-MCP-Server): search, access, and analyze PubMed articles.
* [BioMCP](https://github.com/acashmoney/bio-mcp): protein structure analysis capabilities.
* [Biomedical MCP](https://github.com/genomoncology/biomcp): biomedical knowledge (clinical trials, literature, genomic variants).
* [InterPro MCP](https://github.com/bio-mcp/bio-mcp-interpro): InterProScan for protein domain and family analysis.
* [AMBER MCP](https://github.com/bio-mcp/bio-mcp-amber): molecular dynamics simulations through AMBER suite.
