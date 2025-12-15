#!/usr/bin/env python3
"""
MCP Installation Tool

List and install MCP servers from:
1. Local tool-mcps/ directory
2. Public repositories (Augmented Nature, community)

Usage:
    python src/install_mcp.py list                    # List all available MCPs
    python src/install_mcp.py list --local            # List local MCPs only
    python src/install_mcp.py list --public           # List public MCPs only
    python src/install_mcp.py install <mcp_name>      # Install MCP with Claude Code (default)
    python src/install_mcp.py install <mcp_name> --cli gemini  # Install with Gemini CLI
    python src/install_mcp.py install <mcp_name> --no-register # Clone only, don't register
"""

import os
import sys
import re
import json
import shutil
import subprocess
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Get paths
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
TOOL_MCPS_DIR = PROJECT_ROOT / "tool-mcps"
PUBLIC_MCPS_DIR = TOOL_MCPS_DIR / "public"
PUBLIC_MCPS_CONFIG = PUBLIC_MCPS_DIR / "available_mcps.yaml"

# =============================================================================
# Public MCP Registry
# =============================================================================

def load_public_mcps() -> Dict[str, Any]:
    """Load public MCPs from available_mcps.yaml config file."""
    if not PUBLIC_MCPS_CONFIG.exists():
        print(f"⚠️  Public MCPs config not found: {PUBLIC_MCPS_CONFIG}")
        return {}
    
    if not HAS_YAML:
        print("⚠️  PyYAML not installed. Install with: pip install pyyaml")
        return {}
    
    try:
        with open(PUBLIC_MCPS_CONFIG, "r") as f:
            config = yaml.safe_load(f)
        
        mcps = {}
        for name, info in config.get("mcps", {}).items():
            # Convert setup_commands list to single install command string
            setup_cmds = info.get("setup_commands", [])
            install_cmd = " && ".join(setup_cmds) if setup_cmds else ""
            
            mcps[name] = {
                "name": info.get("name", name),
                "url": info.get("url", ""),
                "description": info.get("description", ""),
                "source": info.get("source", "Community"),
                "type": info.get("runtime", "python"),  # runtime -> type
                "install_command": install_cmd,
                "server_command": info.get("server_command", ""),
                "server_args": info.get("server_args", []),
                "env_vars": info.get("env_vars", {}),
            }
        return mcps
    except Exception as e:
        print(f"❌ Failed to load public MCPs config: {e}")
        return {}


# Load public MCPs (will be populated on first access)
_PUBLIC_MCPS_CACHE = None

def get_public_mcps() -> Dict[str, Any]:
    """Get public MCPs, loading from config if not cached."""
    global _PUBLIC_MCPS_CACHE
    if _PUBLIC_MCPS_CACHE is None:
        _PUBLIC_MCPS_CACHE = load_public_mcps()
    return _PUBLIC_MCPS_CACHE

# For backwards compatibility
PUBLIC_MCPS = property(lambda self: get_public_mcps())


# =============================================================================
# Core Functions
# =============================================================================

def get_local_mcps() -> dict:
    """Get all MCPs from local tool-mcps/ directory."""
    mcps = {}
    if not TOOL_MCPS_DIR.exists():
        return mcps
    
    for item in TOOL_MCPS_DIR.iterdir():
        if item.is_dir() and item.name.endswith("_mcp"):
            name = item.name.replace("_mcp", "")
            # Try to get description from README
            readme = item / "README.md"
            description = "Local MCP server"
            if readme.exists():
                try:
                    content = readme.read_text()
                    # Get first meaningful description line
                    for line in content.split("\n"):
                        line = line.strip()
                        # Skip empty, headers, code blocks, badges, quotes starting with >
                        if not line or line.startswith("#") or line.startswith("```") or \
                           line.startswith("[") or line.startswith("!") or line.startswith(">"):
                            continue
                        # Clean up markdown links and get plain text
                        line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
                        if len(line) > 10:  # Meaningful content
                            description = line[:60] + "..." if len(line) > 60 else line
                            break
                except:
                    pass
            
            mcps[name] = {
                "name": item.name,
                "path": str(item),
                "description": description,
                "source": "Local",
            }
    
    # Also include public MCPs that have been cloned
    if PUBLIC_MCPS_DIR.exists():
        for item in PUBLIC_MCPS_DIR.iterdir():
            if item.is_dir():
                name = item.name.lower().replace("-", "_").replace("_mcp", "").replace("mcp_", "")
                readme = item / "README.md"
                description = "Public MCP (installed)"
                if readme.exists():
                    try:
                        content = readme.read_text()
                        for line in content.split("\n"):
                            line = line.strip()
                            if not line or line.startswith("#") or line.startswith("```") or \
                               line.startswith("[") or line.startswith("!") or line.startswith(">"):
                                continue
                            line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
                            if len(line) > 10:
                                description = line[:60] + "..." if len(line) > 60 else line
                                break
                    except:
                        pass
                
                mcps[f"public/{item.name}"] = {
                    "name": item.name,
                    "path": str(item),
                    "description": description,
                    "source": "Public (installed)",
                }
    
    return mcps


def list_mcps(local_only: bool = False, public_only: bool = False) -> None:
    """List all available MCPs."""
    
    if not public_only:
        local_mcps = get_local_mcps()
        if local_mcps:
            print("\n📁 Local MCPs (tool-mcps/)")
            print("=" * 60)
            for key, mcp in sorted(local_mcps.items()):
                print(f"  {key:<20} {mcp['description'][:50]}")
            print(f"\n  Total: {len(local_mcps)} local MCPs")
    
    if not local_only:
        public_mcps = get_public_mcps()
        print("\n🌐 Public MCPs")
        print("=" * 60)
        
        if not public_mcps:
            print("  No public MCPs found. Check available_mcps.yaml")
        else:
            # Group by source
            sources = {}
            for key, mcp in public_mcps.items():
                source = mcp.get("source", "Unknown")
                if source not in sources:
                    sources[source] = []
                sources[source].append((key, mcp))
            
            for source, mcps in sorted(sources.items()):
                print(f"\n  [{source}]")
                for key, mcp in sorted(mcps):
                    mcp_type = mcp.get("type", "python")
                    desc = mcp.get("description", "")[:40]
                    print(f"    {key:<18} [{mcp_type:<6}] {desc}")
            
            print(f"\n  Total: {len(public_mcps)} public MCPs")
    
    print()


def install_mcp(mcp_name: str, cli: str = "claude", no_register: bool = False) -> bool:
    """
    Install an MCP and register it with the specified CLI.
    
    For local MCPs: register directly from tool-mcps/
    For public MCPs: clone to tool-mcps/public/ then register
    
    Args:
        mcp_name: Name of the MCP to install
        cli: CLI tool to register with ("claude" or "gemini")
        no_register: If True, only clone/copy without registering
    """
    # Check local MCPs first
    local_mcps = get_local_mcps()
    public_mcps = get_public_mcps()
    
    if mcp_name in local_mcps:
        mcp_path = Path(local_mcps[mcp_name]["path"])
        if no_register:
            print(f"✅ MCP '{mcp_name}' is available at: {mcp_path}")
            return True
        return register_mcp_with_cli(mcp_name, mcp_path, cli)
    elif mcp_name in public_mcps:
        mcp_info = public_mcps[mcp_name]
        mcp_type = mcp_info.get("type", "python")
        
        # Handle uvx/npx types (no clone needed)
        if mcp_type == "uvx":
            if no_register:
                print(f"✅ MCP '{mcp_name}' is a uvx package: {mcp_info.get('server_args', [])}")
                return True
            return register_uvx_mcp(mcp_name, mcp_info, cli)
        elif mcp_type == "npx":
            if no_register:
                print(f"✅ MCP '{mcp_name}' is an npx package: {mcp_info.get('server_args', [])}")
                return True
            return register_npx_mcp(mcp_name, mcp_info, cli)
        
        # Clone to tool-mcps/public/ for node/python types
        mcp_path = clone_public_mcp(mcp_name, mcp_info)
        if mcp_path is None:
            return False
        
        # Run install command if specified
        install_cmd = mcp_info.get("install_command", "")
        if install_cmd:
            print(f"📦 Running install command: {install_cmd}")
            result = subprocess.run(install_cmd, shell=True, cwd=mcp_path, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"⚠️  Install command failed: {result.stderr}")
                # Continue anyway, user may need to fix manually
        
        if no_register:
            print(f"✅ MCP '{mcp_name}' cloned to: {mcp_path}")
            return True
        
        if mcp_type == "node":
            return register_node_mcp(mcp_name, mcp_info, mcp_path, cli)
        else:
            return register_mcp_with_cli(mcp_name, mcp_path, cli, mcp_info)
    else:
        print(f"❌ MCP '{mcp_name}' not found.")
        print(f"   Run 'python src/install_mcp.py list' to see available MCPs.")
        return False


def clone_public_mcp(mcp_name: str, mcp_info: dict) -> Optional[Path]:
    """Clone a public MCP to tool-mcps/public/ directory."""
    url = mcp_info.get("url", "")
    if not url:
        print(f"❌ No URL found for MCP '{mcp_name}'")
        return None
    
    repo_name = url.rstrip("/").split("/")[-1]
    
    # Ensure public directory exists
    PUBLIC_MCPS_DIR.mkdir(parents=True, exist_ok=True)
    target_path = PUBLIC_MCPS_DIR / repo_name
    
    if target_path.exists():
        print(f"📁 MCP '{mcp_name}' already cloned at: {target_path}")
        response = input("   Re-clone? [y/N]: ").strip().lower()
        if response != "y":
            return target_path
        shutil.rmtree(target_path)
    
    source = mcp_info.get("source", "Unknown")
    print(f"📦 Cloning {mcp_name} from {source}...")
    print(f"   URL: {url}")
    print(f"   Destination: {target_path}")
    
    try:
        result = subprocess.run(
            ["git", "clone", url, str(target_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"❌ Git clone failed: {result.stderr}")
            return None
        
        print(f"✅ Successfully cloned {mcp_name}")
        return target_path
    except FileNotFoundError:
        print("❌ Git not found. Please install git first.")
        return None
    except Exception as e:
        print(f"❌ Clone failed: {e}")
        return None


def find_mcp_server(mcp_path: Path) -> Optional[Path]:
    """Find the MCP server entry point in a directory."""
    # Common locations for MCP server
    candidates = [
        mcp_path / "src" / "server.py",
        mcp_path / "server.py",
        mcp_path / "src" / "index.py",
        mcp_path / "index.py",
        mcp_path / "main.py",
        mcp_path / "src" / "main.py",
    ]
    
    for candidate in candidates:
        if candidate.exists():
            return candidate
    
    # Search for any server.py or main.py
    for pattern in ["**/server.py", "**/main.py", "**/index.py"]:
        matches = list(mcp_path.glob(pattern))
        if matches:
            return matches[0]
    
    return None


def find_python_env(mcp_path: Path) -> Optional[Path]:
    """Find Python executable in MCP directory."""
    # Check for local env
    env_candidates = [
        mcp_path / "env" / "bin" / "python",
        mcp_path / ".venv" / "bin" / "python",
        mcp_path / "venv" / "bin" / "python",
    ]
    
    for env in env_candidates:
        if env.exists():
            return env
    
    # Fall back to system python
    return None


def register_mcp_with_cli(mcp_name: str, mcp_path: Path, cli: str, mcp_info: dict = None) -> bool:
    """Register MCP with Claude Code or Gemini CLI."""
    
    # If we have mcp_info with server_command, use it
    if mcp_info and mcp_info.get("server_command"):
        server_cmd = mcp_info["server_command"]
        server_args = mcp_info.get("server_args", [])
        # Replace $MCP_PATH placeholder
        server_args = [arg.replace("$MCP_PATH", str(mcp_path)) for arg in server_args]
        
        clean_name = mcp_name.replace("/", "_").replace("-", "_")
        
        if cli == "claude":
            return register_with_claude_cmd(clean_name, server_cmd, server_args, mcp_info.get("env_vars", {}))
        elif cli == "gemini":
            return register_with_gemini_cmd(clean_name, server_cmd, server_args, mcp_path, mcp_info.get("env_vars", {}))
        else:
            print(f"❌ Unknown CLI: {cli}. Use 'claude' or 'gemini'.")
            return False
    
    # Fall back to auto-detection for local MCPs
    # Find server entry point
    server_path = find_mcp_server(mcp_path)
    if server_path is None:
        print(f"⚠️  Could not find MCP server in: {mcp_path}")
        print(f"   Please check the README.md for setup instructions.")
        return False
    
    # Find Python environment
    python_path = find_python_env(mcp_path)
    if python_path is None:
        print(f"⚠️  No local Python environment found in: {mcp_path}")
        print(f"   Using system Python. You may need to create an environment first.")
        python_cmd = "python"
    else:
        python_cmd = str(python_path)
    
    # Clean MCP name for registration (remove special chars)
    clean_name = mcp_name.replace("/", "_").replace("-", "_")
    
    if cli == "claude":
        return register_with_claude(clean_name, python_cmd, server_path)
    elif cli == "gemini":
        return register_with_gemini(clean_name, python_cmd, server_path, mcp_path)
    else:
        print(f"❌ Unknown CLI: {cli}. Use 'claude' or 'gemini'.")
        return False


def register_uvx_mcp(mcp_name: str, mcp_info: dict, cli: str) -> bool:
    """Register a uvx-based MCP."""
    server_args = mcp_info.get("server_args", [])
    env_vars = mcp_info.get("env_vars", {})
    clean_name = mcp_name.replace("/", "_").replace("-", "_")
    
    if cli == "claude":
        return register_with_claude_cmd(clean_name, "uvx", server_args, env_vars)
    elif cli == "gemini":
        return register_with_gemini_cmd(clean_name, "uvx", server_args, None, env_vars)
    else:
        print(f"❌ Unknown CLI: {cli}. Use 'claude' or 'gemini'.")
        return False


def register_npx_mcp(mcp_name: str, mcp_info: dict, cli: str) -> bool:
    """Register an npx-based MCP."""
    server_args = mcp_info.get("server_args", [])
    env_vars = mcp_info.get("env_vars", {})
    clean_name = mcp_name.replace("/", "_").replace("-", "_")
    
    if cli == "claude":
        return register_with_claude_cmd(clean_name, "npx", server_args, env_vars)
    elif cli == "gemini":
        return register_with_gemini_cmd(clean_name, "npx", server_args, None, env_vars)
    else:
        print(f"❌ Unknown CLI: {cli}. Use 'claude' or 'gemini'.")
        return False


def register_node_mcp(mcp_name: str, mcp_info: dict, mcp_path: Path, cli: str) -> bool:
    """Register a Node.js-based MCP."""
    server_cmd = mcp_info.get("server_command", "node")
    server_args = mcp_info.get("server_args", [])
    # Replace $MCP_PATH placeholder
    server_args = [arg.replace("$MCP_PATH", str(mcp_path)) for arg in server_args]
    env_vars = mcp_info.get("env_vars", {})
    clean_name = mcp_name.replace("/", "_").replace("-", "_")
    
    if cli == "claude":
        return register_with_claude_cmd(clean_name, server_cmd, server_args, env_vars)
    elif cli == "gemini":
        return register_with_gemini_cmd(clean_name, server_cmd, server_args, mcp_path, env_vars)
    else:
        print(f"❌ Unknown CLI: {cli}. Use 'claude' or 'gemini'.")
        return False


def register_with_claude_cmd(mcp_name: str, command: str, args: list, env_vars: dict = None) -> bool:
    """Register MCP with Claude Code CLI using command and args."""
    print(f"\n🔧 Registering '{mcp_name}' with Claude Code...")
    
    if shutil.which("claude") is None:
        print("❌ Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code")
        return False
    
    # Build registration command
    cmd = ["claude", "mcp", "add", mcp_name]
    
    # Add environment variables if present
    if env_vars:
        for key, value in env_vars.items():
            cmd.extend(["--env", f"{key}={value}"])
    
    cmd.append("--")
    cmd.append(command)
    cmd.extend(args)
    
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            if "already exists" in result.stderr.lower():
                print(f"⚠️  MCP '{mcp_name}' already registered. Updating...")
                subprocess.run(["claude", "mcp", "remove", mcp_name], capture_output=True)
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"❌ Registration failed: {result.stderr}")
                    return False
            else:
                print(f"❌ Registration failed: {result.stderr}")
                return False
        
        print(f"✅ Successfully registered '{mcp_name}' with Claude Code")
        print(f"\n   Verify with: claude mcp list")
        print(f"   Remove with: claude mcp remove {mcp_name}")
        return True
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        return False


def register_with_gemini_cmd(mcp_name: str, command: str, args: list, mcp_path: Path = None, env_vars: dict = None) -> bool:
    """Register MCP with Gemini CLI using command and args."""
    print(f"\n🔧 Registering '{mcp_name}' with Gemini CLI...")
    
    if shutil.which("gemini") is None:
        print("❌ Gemini CLI not found.")
        return False
    
    # Build registration command
    cmd = ["gemini", "mcp", "add", mcp_name]
    
    # Add environment variables if present
    if env_vars:
        for key, value in env_vars.items():
            cmd.extend(["--env", f"{key}={value}"])
    
    cmd.append("--")
    cmd.append(command)
    cmd.extend(args)
    
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            if "already exists" in result.stderr.lower():
                print(f"⚠️  MCP '{mcp_name}' already registered. Updating...")
                subprocess.run(["gemini", "mcp", "remove", mcp_name], capture_output=True)
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"❌ Registration failed: {result.stderr}")
                    return False
            else:
                print(f"❌ Registration failed: {result.stderr}")
                return False
        
        print(f"✅ Successfully registered '{mcp_name}' with Gemini CLI")
        print(f"\n   Verify with: gemini mcp list")
        print(f"   Remove with: gemini mcp remove {mcp_name}")
        return True
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        return False


def register_with_claude(mcp_name: str, python_cmd: str, server_path: Path) -> bool:
    """Register MCP with Claude Code CLI."""
    print(f"\n🔧 Registering '{mcp_name}' with Claude Code...")
    
    # Check if claude CLI is available
    if shutil.which("claude") is None:
        print("❌ Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code")
        return False
    
    # Build registration command
    cmd = ["claude", "mcp", "add", mcp_name, "--", python_cmd, str(server_path)]
    
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Check if already exists
            if "already exists" in result.stderr.lower():
                print(f"⚠️  MCP '{mcp_name}' already registered. Updating...")
                # Remove and re-add
                subprocess.run(["claude", "mcp", "remove", mcp_name], capture_output=True)
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"❌ Registration failed: {result.stderr}")
                    return False
            else:
                print(f"❌ Registration failed: {result.stderr}")
                return False
        
        print(f"✅ Successfully registered '{mcp_name}' with Claude Code")
        print(f"\n   Verify with: claude mcp list")
        print(f"   Remove with: claude mcp remove {mcp_name}")
        return True
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        return False


def register_with_gemini(mcp_name: str, python_cmd: str, server_path: Path, mcp_path: Path) -> bool:
    """Register MCP with Gemini CLI."""
    print(f"\n🔧 Registering '{mcp_name}' with Gemini CLI...")
    
    if shutil.which("gemini") is None:
        print("❌ Gemini CLI not found. Install with: npm install -g @anthropic-ai/gemini-cli")
        return False
    
    # Build registration command
    cmd = ["gemini", "mcp", "add", mcp_name, "--", python_cmd, str(server_path)]
    
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            if "already exists" in result.stderr.lower():
                print(f"⚠️  MCP '{mcp_name}' already registered. Updating...")
                subprocess.run(["gemini", "mcp", "remove", mcp_name], capture_output=True)
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"❌ Registration failed: {result.stderr}")
                    return False
            else:
                print(f"❌ Registration failed: {result.stderr}")
                return False
        
        print(f"✅ Successfully registered '{mcp_name}' with Gemini CLI")
        print(f"\n   Verify with: gemini mcp list")
        print(f"   Remove with: gemini mcp remove {mcp_name}")
        return True
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        return False


def search_mcps(query: str) -> None:
    """Search MCPs by name or description."""
    query = query.lower()
    results = []
    
    # Search local
    for key, mcp in get_local_mcps().items():
        if query in key.lower() or query in mcp["description"].lower():
            results.append((key, mcp, "Local"))
    
    # Search public
    public_mcps = get_public_mcps()
    for key, mcp in public_mcps.items():
        if query in key.lower() or query in mcp.get("description", "").lower() or query in mcp.get("name", "").lower():
            results.append((key, mcp, "Public"))
    
    if results:
        print(f"\n🔍 Search results for '{query}':")
        print("=" * 60)
        for key, mcp, source in results:
            mcp_type = mcp.get("type", "python") if source == "Public" else "local"
            desc = mcp.get("description", "")[:40]
            print(f"  [{source}] {key:<18} [{mcp_type:<6}] {desc}")
        print(f"\n  Found: {len(results)} MCPs")
    else:
        print(f"   No MCPs found matching '{query}'")
    print()


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="List and install MCP servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/install_mcp.py list                     # List all MCPs
  python src/install_mcp.py list --local             # List local MCPs only
  python src/install_mcp.py search blast             # Search for MCPs
  python src/install_mcp.py install proteinmpnn      # Install with Claude Code (default)
  python src/install_mcp.py install pdb --cli gemini # Install with Gemini CLI
  python src/install_mcp.py install arxiv --no-register  # Clone only
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available MCPs")
    list_parser.add_argument("--local", action="store_true", help="Show local MCPs only")
    list_parser.add_argument("--public", action="store_true", help="Show public MCPs only")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search MCPs")
    search_parser.add_argument("query", help="Search query")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install an MCP")
    install_parser.add_argument("mcp_name", help="Name of MCP to install")
    install_parser.add_argument("--cli", choices=["claude", "gemini"], default="claude",
                                help="CLI tool to register with (default: claude)")
    install_parser.add_argument("--no-register", action="store_true",
                                help="Clone/locate only, don't register with CLI")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show MCP details")
    info_parser.add_argument("mcp_name", help="Name of MCP")
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall an MCP from CLI")
    uninstall_parser.add_argument("mcp_name", help="Name of MCP to uninstall")
    uninstall_parser.add_argument("--cli", choices=["claude", "gemini"], default="claude",
                                  help="CLI tool to unregister from (default: claude)")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_mcps(local_only=args.local, public_only=args.public)
    elif args.command == "search":
        search_mcps(args.query)
    elif args.command == "install":
        install_mcp(args.mcp_name, cli=args.cli, no_register=args.no_register)
    elif args.command == "info":
        show_info(args.mcp_name)
    elif args.command == "uninstall":
        uninstall_mcp(args.mcp_name, cli=args.cli)
    else:
        parser.print_help()


def show_info(mcp_name: str) -> None:
    """Show detailed info about an MCP."""
    local_mcps = get_local_mcps()
    public_mcps = get_public_mcps()
    
    if mcp_name in local_mcps:
        mcp = local_mcps[mcp_name]
        print(f"\n📁 {mcp['name']}")
        print("=" * 40)
        print(f"  Type: Local")
        print(f"  Path: {mcp['path']}")
        print(f"  Description: {mcp['description']}")
        
        # Check for server and env
        mcp_path = Path(mcp['path'])
        server = find_mcp_server(mcp_path)
        python_env = find_python_env(mcp_path)
        print(f"  Server: {server or 'Not found'}")
        print(f"  Python: {python_env or 'System'}")
    elif mcp_name in public_mcps:
        mcp = public_mcps[mcp_name]
        mcp_type = mcp.get("type", "python")
        print(f"\n🌐 {mcp.get('name', mcp_name)}")
        print("=" * 40)
        print(f"  Type: Public ({mcp.get('source', 'Unknown')})")
        print(f"  Runtime: {mcp_type}")
        print(f"  URL: {mcp.get('url', 'N/A')}")
        print(f"  Description: {mcp.get('description', 'N/A')}")
        
        if mcp_type in ["uvx", "npx"]:
            print(f"  Command: {mcp_type} {' '.join(mcp.get('server_args', []))}")
        else:
            print(f"  Install: {mcp.get('install_command', 'N/A')}")
            print(f"  Server: {mcp.get('server_command', 'N/A')} {' '.join(mcp.get('server_args', []))}")
        
        if mcp.get("env_vars"):
            print(f"  Env Vars: {', '.join(mcp['env_vars'].keys())}")
        
        # Check if already cloned
        url = mcp.get("url", "")
        if url:
            repo_name = url.rstrip("/").split("/")[-1]
            cloned_path = PUBLIC_MCPS_DIR / repo_name
            if cloned_path.exists():
                print(f"  Status: ✅ Cloned to {cloned_path}")
            else:
                print(f"  Status: Not installed")
    else:
        print(f"❌ MCP '{mcp_name}' not found.")
    print()


def uninstall_mcp(mcp_name: str, cli: str = "claude") -> bool:
    """Uninstall MCP from CLI."""
    clean_name = mcp_name.replace("/", "_").replace("-", "_")
    
    if cli == "claude":
        print(f"🗑️  Unregistering '{clean_name}' from Claude Code...")
        if shutil.which("claude") is None:
            print("❌ Claude CLI not found.")
            return False
        
        result = subprocess.run(["claude", "mcp", "remove", clean_name], 
                                capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Uninstall failed: {result.stderr}")
            return False
        print(f"✅ Successfully removed '{clean_name}' from Claude Code")
        return True
    
    elif cli == "gemini":
        print(f"🗑️  Unregistering '{clean_name}' from Gemini CLI...")
        if shutil.which("gemini") is None:
            print("❌ Gemini CLI not found.")
            return False
        
        result = subprocess.run(["gemini", "mcp", "remove", clean_name], 
                                capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Uninstall failed: {result.stderr}")
            return False
        print(f"✅ Successfully removed '{clean_name}' from Gemini CLI")
        return True
    
    return False


if __name__ == "__main__":
    main()
