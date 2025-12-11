# MCP servers

Please clone and download the corresponding MCP servers from [Biomolecular Design Nexus repositories](https://github.com/Biomolecular-Design-Nexus), and put it under `./tool-mcps` directory.

## Examples

```shell

```

## Public MCP servers
### [Augmented Nature](https://github.com/Augmented-Nature)
* [UniProt MCP Server](https://github.com/Augmented-Nature/Augmented-Nature-UniProt-MCP-Server): provides advanced access to the UniProt protein database with 26 specialized bioinformatics tools.
* [Alphafold DB MCP Server](https://github.com/Augmented-Nature/AlphaFold-MCP-Server): provides access to the AlphaFold Protein Structure Database through a rich set of tools and resources for protein structure prediction analysis.
* [PDB MCP Server](https://github.com/Augmented-Nature/PDB-MCP-Server): provides access to the Protein Data Bank (PDB) - the worldwide repository of information about the 3D structures of proteins, nucleic acids, and complex assemblies.
* [STRING DB MCP Server](https://github.com/Augmented-Nature/STRING-db-MCP-Server): for accessing the STRING protein interaction database.
* [ProteinAtlas MCP Server](https://github.com/Augmented-Nature/ProteinAtlas-MCP-Server): for accessing Human Protein Atlas data, providing information about protein expression, subcellular localization, pathology, and more.
* [KEGG MCP Server](https://github.com/Augmented-Nature/KEGG-MCP-Server): provides comprehensive access to the KEGG (Kyoto Encyclopedia of Genes and Genomes) database through its REST API.
* [Open Targets MCP Server](https://github.com/Augmented-Nature/OpenTargets-MCP-Server): for accessing Open Targets platform data for gene-drug-disease associations research.
* [NCBI Datasets MCP Server](https://github.com/Augmented-Nature/NCBI-Datasets-MCP-Server): provides comprehensive access to the NCBI Datasets API with 31 specialized tools.

### Other MCP servers
* [PyMOL MCP](https://github.com/vrtejus/pymol-mcp): enabling AI agents to directly interact with and control PyMOL.
* [BLAST MCP](https://github.com/bio-mcp/bio-mcp-blast): for NCBI BLAST sequence similarity search.
* [Arxiv MCP](https://github.com/blazickjp/arxiv-mcp-server): allow AI models to search for papers and access their content in a programmatic way.
* [bioRxiv MCP](https://github.com/JackKuo666/bioRxiv-MCP-Server): enable AI assistants to search and access bioRxiv papers through a simple MCP interface.
* [PubMed MCP](https://github.com/JackKuo666/PubMed-MCP-Server): enable AI assistants to search, access, and analyze PubMed articles.
* [BioMCP](https://github.com/acashmoney/bio-mcp): enhance large language models with protein structure analysis capabilities. 
* [Biomedical MCP](https://github.com/genomoncology/biomcp): empowers AI assistants and agents with specialized biomedical knowledge and connects AI systems to authoritative biomedical data sources, enabling them to answer questions about clinical trials, scientific literature, and genomic variants with precision and depth.
* [Brave Search MCP Server](https://github.com/brave/brave-search-mcp-server): integrates the Brave Search API, providing comprehensive search capabilities including web search, local business search, image search, video search, news search, and AI-powered summarization. 


## Workflow to create MCP servers
```shell
mkdir tool-mcps/xxx_mcp
cd tool-mcps/xxx_mcp
mkdir repo scripts src examples

cd repo
git clone git@github.com:xxx/xxx.git
cd ..

# Create environment

# Implement local scripts
claude
# Please implement function ABC in @scripts for local running

# Test local scripts with python scripts/xxx.py

# Implement MCP API
claude
# Please adapte function ABC in @scripts as MCP APIs in @src

# Test MCP API

# Install MCP API in claude code and run
```