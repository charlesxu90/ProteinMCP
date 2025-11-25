"""
Model Context Protocol (MCP) for MSA Generation

This MCP server provides tools for generating Multiple Sequence Alignments (MSA) using the ColabFold/MMseqs2 server.
It enables researchers to generate MSAs for protein sequences by searching against UniRef30 and environmental databases.

This MCP Server contains tools extracted from the MSA generation notebook:
1. msa_generation
    - generate_msa: Generate multiple sequence alignment for a protein sequence using ColabFold/MMseqs2 server
"""

from fastmcp import FastMCP

# Import statements
from tools.msa_generation import msa_generation_mcp

# Server definition and mounting
mcp = FastMCP(name="msa")
mcp.mount(msa_generation_mcp)

if __name__ == "__main__":
    mcp.run()
