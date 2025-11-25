"""
MSA generation tools using ColabFold/MMseqs2 server.

This MCP Server provides 1 tool:
1. generate_msa: Generate multiple sequence alignment for a protein sequence using ColabFold/MMseqs2 server

All tools extracted from the MSA server notebook for protein sequence analysis.
"""

# Standard imports
from typing import Annotated
from pathlib import Path
import os
import sys
import time
import io
import tarfile
from fastmcp import FastMCP
from datetime import datetime

# Third-party imports
import requests

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
DEFAULT_INPUT_DIR = PROJECT_ROOT / "tmp" / "inputs"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "tmp" / "outputs"

INPUT_DIR = Path(os.environ.get("MSA_GENERATION_INPUT_DIR", DEFAULT_INPUT_DIR))
OUTPUT_DIR = Path(os.environ.get("MSA_GENERATION_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Timestamp for unique outputs
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# MCP server instance
msa_generation_mcp = FastMCP(name="msa_generation")

# Configuration for the ColabFold/MMseqs2 Server
MSA_SERVER_URL = "https://api.colabfold.com"
User_Agent = "MCP-MSA-Server"


# ============================================================================
# Helper Functions
# ============================================================================

def submit_job(sequence: str, job_name: str = "msa_job") -> str:
    """
    Submits a protein sequence to the MSA server.

    Args:
        sequence: Protein sequence string
        job_name: Optional job name for tracking

    Returns:
        Ticket ID for the submitted job
    """
    endpoint = f"{MSA_SERVER_URL}/ticket/msa"

    # Standard ColabFold parameters
    payload = {
        "q": f">{job_name}\n{sequence}",
        "mode": "all",  # Searches UniRef30 + Environmental
        "db": "uniref30,colabfold_envdb_202108",
        "use_templates": 0,
        "use_pairing": 1,
    }

    try:
        response = requests.post(endpoint, data=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "id" not in data:
            raise ValueError(f"No Job ID received. Server said: {data}")

        ticket_id = data["id"]
        return ticket_id
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Connection error during submission: {e}")


def poll_status(ticket_id: str, max_wait_time: int = 600) -> bool:
    """
    Polls the server status until the MSA generation is complete.

    Args:
        ticket_id: Ticket ID from job submission
        max_wait_time: Maximum time to wait in seconds (default: 600 = 10 minutes)

    Returns:
        True if successful, raises exception otherwise
    """
    status_endpoint = f"{MSA_SERVER_URL}/ticket/{ticket_id}"

    start_time = time.time()

    while True:
        # Check timeout
        if time.time() - start_time > max_wait_time:
            raise TimeoutError(f"MSA generation timed out after {max_wait_time} seconds")

        try:
            response = requests.get(status_endpoint, timeout=30)
            response.raise_for_status()
            data = response.json()

            status = data.get("status")

            if status == "COMPLETE":
                return True
            elif status == "ERROR":
                raise RuntimeError(f"Server reported an error: {data.get('msg', 'Unknown error')}")
            elif status in ["RUNNING", "PENDING"]:
                # Wait 5 seconds before checking again
                time.sleep(5)
            else:
                # Unknown status, wait and retry
                time.sleep(5)

        except requests.exceptions.RequestException as e:
            # Network error, retry after a longer delay
            time.sleep(10)


def download_results(ticket_id: str, output_filename: str) -> str:
    """
    Downloads and extracts the A3M file from the server.

    Args:
        ticket_id: Ticket ID from job submission
        output_filename: Path to save the A3M file

    Returns:
        Absolute path to the saved A3M file
    """
    download_endpoint = f"{MSA_SERVER_URL}/result/download/{ticket_id}"

    try:
        response = requests.get(download_endpoint, stream=True, timeout=60)
        response.raise_for_status()

        # The server returns a tarball containing multiple files (a3m, pdb70, etc.)
        # We need to extract just the .a3m file.
        with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz") as tar:
            # Look for the .a3m file in the tarball
            a3m_files = [m for m in tar.getmembers() if m.name.endswith(".a3m")]

            if not a3m_files:
                raise ValueError("No .a3m file found in the server response")

            # Extract the first A3M file found (usually there is only one relevant one)
            target_file = a3m_files[0]
            f = tar.extractfile(target_file)
            content = f.read().decode("utf-8")

            # Save to local disk
            with open(output_filename, "w") as out:
                out.write(content)

            return os.path.abspath(output_filename)

    except Exception as e:
        raise RuntimeError(f"Error downloading/extracting results: {e}")

# ============================================================================
# MCP Tools
# ============================================================================

@msa_generation_mcp.tool
def generate_msa(
    sequence: Annotated[str, "Protein sequence (single-letter amino acid codes)"],
    job_name: Annotated[str | None, "Optional job name for tracking"] = None,
    output_filename: Annotated[str | None, "Output filename for the MSA (A3M format). If not provided, will use job_name.a3m"] = None,
    max_wait_time: Annotated[int, "Maximum time to wait for MSA generation in seconds"] = 600,
) -> dict:
    """
    Generate multiple sequence alignment (MSA) for a protein sequence using ColabFold/MMseqs2 server.
    Input is a protein sequence and output is an A3M format MSA file with alignment information.

    The MSA is generated by searching against UniRef30 and environmental databases.
    This typically takes 2-10 minutes depending on sequence length and server load.
    """
    # Input validation
    if not sequence:
        raise ValueError("Protein sequence must be provided")

    # Validate sequence contains only valid amino acids
    valid_amino_acids = set("ACDEFGHIKLMNPQRSTVWY")
    if not all(c.upper() in valid_amino_acids for c in sequence.replace(" ", "").replace("\n", "")):
        raise ValueError("Sequence contains invalid amino acid characters. Use single-letter codes (A-Z)")

    # Clean sequence
    sequence = sequence.replace(" ", "").replace("\n", "").upper()

    # Set defaults
    if job_name is None:
        job_name = f"msa_{timestamp}"

    if output_filename is None:
        output_filename = f"{job_name}.a3m"

    # Ensure output is in the output directory
    if not os.path.isabs(output_filename):
        output_filename = str(OUTPUT_DIR / output_filename)

    try:
        # Step 1: Submit job
        print(f"🚀 Submitting sequence to {MSA_SERVER_URL}...")
        ticket_id = submit_job(sequence, job_name)
        print(f"✅ Job submitted successfully. Ticket ID: {ticket_id}")

        # Step 2: Poll status
        print(f"⏳ Waiting for MSA generation (this can take 2-10 minutes)...")
        poll_status(ticket_id, max_wait_time)
        print("✅ MSA Generation Complete!")

        # Step 3: Download results
        print("⬇️  Downloading results...")
        output_path = download_results(ticket_id, output_filename)
        print(f"🎉 Success! MSA saved to: {output_path}")

        # Read and analyze the MSA file
        with open(output_path, "r") as f:
            msa_content = f.read()

        # Count sequences in MSA
        num_sequences = msa_content.count(">")

        # Get first sequence length (reference sequence)
        lines = msa_content.split("\n")
        seq_length = 0
        for line in lines[1:]:
            if line.startswith(">"):
                break
            seq_length += len(line.strip())

        return {
            "status": "success",
            "ticket_id": ticket_id,
            "output_file": output_path,
            "job_name": job_name,
            "sequence_length": len(sequence),
            "msa_depth": num_sequences,
            "msa_length": seq_length,
            "message": f"MSA generated successfully with {num_sequences} sequences"
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to generate MSA: {str(e)}"
        }
