# MSA Generation MCP Server

This MCP server provides tools for generating Multiple Sequence Alignments (MSA) using the ColabFold/MMseqs2 API server.

## Features

- **generate_msa**: Generate MSA for protein sequences using ColabFold/MMseqs2 server
  - Searches UniRef30 and environmental databases
  - Returns A3M format alignment files
  - Automatic job submission, polling, and result retrieval

## Running as Standalone FastMCP Service

You can run this as a standalone FastMCP server:

```bash
cd src
python msa_mcp.py
```

This will start the MCP server that can be connected to by Claude Code or other MCP clients.

## Integration with Claude Code
To use this MCP server with Claude Code, add it using the following command:
```shell
fastmcp install claude-code  msa_server_mcp/src/msa_mcp.py
```

## Integration with Gemini CLI
For Gemini CLI, add the mcp using a similar command.
```shell
fastmcp install gemini-cli  msa_server_mcp/src/msa_mcp.py
```

## Available Tools

### generate_msa

Generate a multiple sequence alignment for a protein sequence.

**Parameters:**
- `sequence` (required): Protein sequence (single-letter amino acid codes)
- `job_name` (optional): Job name for tracking (default: auto-generated timestamp)
- `output_filename` (optional): Output filename for MSA in A3M format (default: {job_name}.a3m)
- `max_wait_time` (optional): Maximum time to wait in seconds (default: 600)

**Returns:**
- `status`: "success" or "error"
- `ticket_id`: Server ticket ID
- `output_file`: Absolute path to the generated MSA file
- `msa_depth`: Number of sequences in the MSA
- `msa_length`: Length of the alignment
- `message`: Status message

## **Example usage in Claude Code:**

```claude
Can you generate an MSA for this protein sequence: MQYKLILNGKTLKGETTTEAVDAATAEKVFKQYANDNGVDGEWTYDDATKTFTVTE
```

### Output
MSA files are saved to `msa_server_mcp/tmp/outputs/` by default. You can change this by setting the `MSA_GENERATION_OUTPUT_DIR` environment variable.

```claude
 Perfect! I've successfully generated the MSA for your protein sequence. Here are the results:

  MSA Generation Summary:
  - Status: Success ✓
  - Sequence Length: 56 amino acids
  - MSA Depth: 144 sequences (found 144 homologous sequences)
  - Output File: protein_msa_query.a3m
  - Location: /home/xux/Desktop/ProteinMCP/ProteinMCP/mcp-servers/msa_server_mcp/tmp/outputs/protein_msa_query.a3m

  The MSA was generated using ColabFold/MMseqs2 by searching against UniRef30 and environmental databases. The resulting
   A3M format file contains the alignment of 144 related protein sequences, which can be used for downstream
  applications like structure prediction, evolutionary analysis, or protein design.
```

## How It Works

1. **Submit**: Submits your protein sequence to the ColabFold/MMseqs2 API
2. **Poll**: Monitors the job status until completion (typically 2-10 minutes)
3. **Download**: Retrieves and extracts the A3M alignment file

## Notes

- MSA generation typically takes 2-10 minutes depending on sequence length and server load
- The server searches UniRef30 and ColabFold environmental databases
- Results are returned in A3M format, compatible with AlphaFold, ColabFold, and other structure prediction tools
