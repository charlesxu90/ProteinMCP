# pmcp create --github-url https://github.com/jwohlwend/boltz --mcp-dir tool-mcps/boltz_mcp --use-case-filter 'structure prediction with boltz2, affinity prediciton with boltz2, batch structure prediction for protein variants given prepared configs'

# pmcp create --local-repo-path tool-mcps/protein_sol_mcp/scripts/protein-sol/ --mcp-dir tool-mcps/protein_sol_mcp

pmcp create --github-url https://github.com/chaidiscovery/chai-lab --mcp-dir tool-mcps/chai1_mcp --use-case-filter 'structure prediction given a sequence with chai-1, structure prediction given a config file with chai-1, batch prediction with chai-1'

pmcp create --local-repo-path /opt/rosetta/rosetta.binary.ubuntu.release-371/main/ --mcp-dir tool-mcps/rosetta_mcp --use-case-filter 'Membrane protein structure prediction, Loop modeling, Enzyme design, Protein Design with non-canonical amino acids, Protein-protein docking, Ligand docking, Antibody-antigen docking (SnugDock), Symmetric docking, RNA design, RNA-protein complex prediction, CDR loop modeling, Antibody design, Relax, Structure quality analysis, Clustering, Covalent docking, Ligand design, Peptide modeling, Symmetric assembly modeling, Membrane protein design, Multi-state design, ddG calculations, NMR-guided modeling, Cryo-EM refinement, Comparative modeling'

pmcp create --local-repo-path  tool-mcps/gromacs_mcp/repo/gromacs-2025.4 --mcp-dir tool-mcps/gromacs_mcp --use-case-filter 'Regular MD simulations, RMSD and RMSF analysis, binding affinity analysis, FEP'

pmcp create --local-repo-path tool-mcps/mutcompute_mcp/repo/mutcompute/ --mcp-dir tool-mcps/mutcompute_mcp --use-case-filter 'Predicting the effect of point mutations on protein stability, the demo code to run is in tool-mcps/mutcompute_mcp/repo/mutcompute/run_prediciton.sh'

# pmcp create --github-url https://github.com/dauparas/ProteinMPNN --mcp-dir tool-mcps/proteinmpnn_mcp --use-case-filter 'scaffold-based generation and likelihood calculation'

# pmcp create --github-url  https://github.com/dauparas/LigandMPNN --mcp-dir tool-mcps/ligandmpnn_mcp --use-case-filter 'scaffold-based generation and likelihood calculation'

# pmcp create --github-url https://github.com/RosettaCommons/RFdiffusion2 --mcp-dir tool-mcps/rfdiffusion2_mcp --use-case-filter 'inference'

pmcp create --local-repo-path tool-mcps/spired_stab_mcp/scripts --mcp-dir tool-mcps/spired_stab_mcp --use-case-filter 'Predicting protein stability changes upon mutation using Spired-Stab, the mcp is working and in tool-mcps/spired_stab_mcp/src/spired_stab_mcp.py, please extract the relevent information following the workflow'

pmcp create --local-repo-path tool-mcps/alphafold3_mcp/repo/alphafold3/ --mcp-dir tool-mcps/alphafold3_mcp --use-case-filter 'Protein structure prediction using AlphaFold 3, the mcp is working and in tool-mcps/alphafold3_mcp/src/alphafold3_mcp.py, please extract the relevent information following the workflow'

pmcp create --local-repo-path tool-mcps/boltzgen_mcp/repo/boltzgen/ --mcp-dir tool-mcps/boltzgen_mcp --use-case-filter 'Protein design using BoltzGen, the mcp is working and in tool-mcps/boltzgen_mcp/src/boltzgen_mcp.py, please extract the relevent information following the workflow'

pmcp create --local-repo-path tool-mcps/bindcraft_mcp/scripts/ --mcp-dir tool-mcps/bindcraft_mcp --use-case-filter 'Protein binder design using BindCraft, the mcp is working and in tool-mcps/bindcraft_mcp/src/bindcraft_mcp.py, please extract the relevent information following the workflow'

pmcp create --local-repo-path tool-mcps/netmhcpan_mcp/repo/netMHCpan-4.2 --mcp-dir tool-mcps/netmhcpan_mcp --use-case-filter 'MHC binding prediction using NetMHCpan-4.2'

pmcp create --local-repo-path tool-mcps/netmhc2pan_mcp/repo/netMHCIIpan-4.3 --mcp-dir tool-mcps/netmhc2pan_mcp --use-case-filter 'MHC2 binding prediction using netMHCIIpan-4.3'

pmcp create --github-url https://github.com/google-deepmind/alphafold --mcp-dir  tool-mcps/alphafold2_mcp --use-case-filter 'Proteinstructure prediction using AlphaFold2, protein multimer prediction using AlphaFold-Multimer'

pmcp create --github-url https://github.com/facebookresearch/esm --mcp-dir tool-mcps/esmfold_mcp --use-case-filter 'Protein structure prediction using ESMFold'

pmcp create --github-url https://github.com/bio-mcp/bio-mcp-interpro --mcp-dir tool-mcps/interpro_mcp --use-case-filter 'Protein analysis using interproscan'


pmcp create --github-url https://github.com/bio-mcp/bio-mcp-amber --mcp-dir tool-mcps/amber_mcp --use-case-filter 'Protein MD simulations with Amber, QM/MM of enzyme-substrate complex with amber'
