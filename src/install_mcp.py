#!/usr/bin/env python3
"""
MCP Installation Tool

List and install MCP servers from:
1. Local MCPs (tool-mcps/) - from src/configs/mcps.yaml
2. Public MCPs (tool-mcps/public/) - from src/configs/public_mcps.yaml

Usage:
    python src/install_mcp.py list                    # List all available MCPs (cached)
    python src/install_mcp.py list --local            # List local MCPs only
    python src/install_mcp.py list --public           # List public MCPs only
    python src/install_mcp.py list --refresh          # Refresh cache (slower)
    python src/install_mcp.py install <mcp_name>      # Install and register with Claude Code
    python src/install_mcp.py install <mcp_name> --cli gemini  # Install with Gemini CLI
    python src/install_mcp.py install <mcp_name> --no-register # Install only, don't register
    python src/install_mcp.py search <query>          # Search MCPs
    python src/install_mcp.py info <mcp_name>         # Show MCP details
    python src/install_mcp.py uninstall <mcp_name>    # Unregister MCP from CLI

Note: Status checks are cached for 5 minutes to improve performance. Use --refresh to force update.
"""

import argparse

from mcp_manager import MCPManager
from mcp import MCPStatus


# =============================================================================
# Global MCP Manager Instance
# =============================================================================

# Create global MCPManager instance for use throughout the module
mcp_manager = MCPManager()


# =============================================================================
# Core Functions
# =============================================================================

def list_mcps(local_only: bool = False, public_only: bool = False, refresh_cache: bool = False) -> None:
    """List all available MCPs."""

    # Refresh cache if requested
    if refresh_cache:
        from status_cache import get_cache
        cache = get_cache()
        cache.invalidate()
        print("🔄 Cache invalidated, will fetch fresh status...")

    # Load MCPs
    if not public_only:
        installed_mcps = mcp_manager.load_installed_mcps()
    else:
        installed_mcps = {}

    if not local_only:
        public_mcps = mcp_manager.load_public_mcps()
    else:
        public_mcps = {}

    # Display installed MCPs
    if installed_mcps and not public_only:
        print("\n📁 Installed MCPs (tool-mcps/)")
        print("=" * 80)
        mcp_manager.print_mcps(installed_mcps, "Installed MCPs")

    # Display public MCPs
    if public_mcps and not local_only:
        print("\n🌐 Public MCPs (tool-mcps/public/)")
        print("=" * 80)
        mcp_manager.print_mcps(public_mcps, "Public MCPs")

    if not installed_mcps and not public_mcps:
        print("  No MCPs found.")


def install_mcp_cmd(mcp_name: str, cli: str = "claude", no_register: bool = False) -> bool:
    """
    Install an MCP and optionally register it with the specified CLI.

    Args:
        mcp_name: Name of the MCP to install
        cli: CLI tool to register with ("claude" or "gemini")
        no_register: If True, only install without registering

    Returns:
        True if successful, False otherwise
    """
    # Try to get MCP from either registry
    mcp = mcp_manager.get_mcp(mcp_name)

    if not mcp:
        print(f"❌ MCP '{mcp_name}' not found.")
        print(f"   Run 'python src/install_mcp.py list' to see available MCPs.")
        return False

    # Check current status
    status = mcp.get_status(cli)
    print(f"\n📊 Current status: {status.value}")

    # Install if needed
    if status in [MCPStatus.NOT_INSTALLED, MCPStatus.REGISTERED]:
        print(f"\n📦 Installing '{mcp_name}'...")
        if not mcp_manager.install_mcp(mcp_name):
            return False
    else:
        print(f"✅ MCP '{mcp_name}' already installed")

    # Register if requested
    if not no_register:
        if status in [MCPStatus.NOT_INSTALLED, MCPStatus.INSTALLED]:
            print(f"\n🔧 Registering '{mcp_name}' with {cli}...")
            if not mcp_manager.register_mcp(mcp_name, cli=cli):
                return False
        else:
            print(f"✅ MCP '{mcp_name}' already registered with {cli}")

    # Show final status
    final_status = mcp.get_status(cli)
    print(f"\n✨ Final status: {final_status.value}")

    if final_status == MCPStatus.BOTH:
        print(f"🎉 Successfully installed and registered '{mcp_name}'!")
        print(f"\n   Verify with: {cli} mcp list")
        print(f"   Remove with: {cli} mcp remove {mcp._get_clean_name()}")

    return True


def search_mcps(query: str) -> None:
    """Search MCPs by name or description."""
    results = mcp_manager.search_mcps(query)

    if results:
        print(f"\n🔍 Search results for '{query}':")
        mcp_manager.print_mcps(results, f"Results for '{query}'")
    else:
        print(f"\n   No MCPs found matching '{query}'")
    print()


def show_info(mcp_name: str) -> None:
    """Show detailed info about an MCP."""
    mcp = mcp_manager.get_mcp(mcp_name)

    if not mcp:
        print(f"❌ MCP '{mcp_name}' not found.")
        return

    status = mcp.get_status()

    print(f"\n📦 {mcp.name}")
    print("=" * 60)
    print(f"  Description: {mcp.description}")
    print(f"  Source: {mcp.source}")
    print(f"  Runtime: {mcp.runtime}")

    if mcp.url:
        print(f"  URL: {mcp.url}")

    if mcp.path:
        print(f"  Path: {mcp.path}")

    print(f"  Status: {status.value}")
    print(f"  Installed: {'✅' if mcp.is_installed() else '❌'}")
    print(f"  Registered (Claude): {'✅' if mcp.is_registered('claude') else '❌'}")

    if mcp.server_command:
        print(f"  Server Command: {mcp.server_command}")

    if mcp.server_args:
        print(f"  Server Args: {' '.join(mcp.server_args)}")

    if mcp.env_vars:
        print(f"  Environment Variables:")
        for key, value in mcp.env_vars.items():
            print(f"    {key}={value}")

    if mcp.dependencies:
        print(f"  Dependencies: {', '.join(mcp.dependencies)}")

    if mcp.setup_commands:
        print(f"  Setup Commands:")
        for cmd in mcp.setup_commands:
            print(f"    - {cmd}")

    print()


def uninstall_mcp_cmd(mcp_name: str, cli: str = "claude", remove_files: bool = False) -> bool:
    """
    Uninstall MCP from CLI and optionally remove files.

    Args:
        mcp_name: Name of MCP to uninstall
        cli: CLI tool to unregister from
        remove_files: If True, also remove installation files

    Returns:
        True if successful, False otherwise
    """
    mcp = mcp_manager.get_mcp(mcp_name)

    if not mcp:
        print(f"❌ MCP '{mcp_name}' not found.")
        return False

    # Unregister from CLI
    if mcp.is_registered(cli):
        print(f"🗑️  Unregistering '{mcp_name}' from {cli}...")
        if not mcp_manager.unregister_mcp(mcp_name, cli=cli):
            print(f"⚠️  Failed to unregister, continuing...")

    # Remove files if requested
    if remove_files:
        if mcp.is_installed():
            print(f"🗑️  Removing installation files...")
            if not mcp_manager.uninstall_mcp(mcp_name, remove_files=True):
                return False

    print(f"✅ Successfully uninstalled '{mcp_name}'")
    return True


def sync_mcps() -> None:
    """Synchronize MCP registry with filesystem."""
    print("🔄 Synchronizing MCP registry with filesystem...")
    mcp_manager.sync_installed_with_filesystem()


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="List and install MCP servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/install_mcp.py list                          # List all MCPs
  python src/install_mcp.py list --local                  # List local MCPs only
  python src/install_mcp.py list --public                 # List public MCPs only
  python src/install_mcp.py search blast                  # Search for MCPs
  python src/install_mcp.py install proteinmpnn           # Install with Claude Code
  python src/install_mcp.py install pdb --cli gemini      # Install with Gemini CLI
  python src/install_mcp.py install arxiv --no-register   # Install only
  python src/install_mcp.py info uniprot                  # Show MCP details
  python src/install_mcp.py uninstall arxiv               # Unregister from CLI
  python src/install_mcp.py uninstall arxiv --remove-files # Unregister and delete
  python src/install_mcp.py sync                          # Sync registry with filesystem
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # List command
    list_parser = subparsers.add_parser("list", help="List available MCPs")
    list_parser.add_argument("--local", action="store_true", help="Show local MCPs only")
    list_parser.add_argument("--public", action="store_true", help="Show public MCPs only")
    list_parser.add_argument("--refresh", action="store_true", help="Refresh status cache (slower but accurate)")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search MCPs")
    search_parser.add_argument("query", help="Search query")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install an MCP")
    install_parser.add_argument("mcp_name", help="Name of MCP to install")
    install_parser.add_argument("--cli", choices=["claude", "gemini"], default="claude",
                                help="CLI tool to register with (default: claude)")
    install_parser.add_argument("--no-register", action="store_true",
                                help="Install only, don't register with CLI")

    # Info command
    info_parser = subparsers.add_parser("info", help="Show MCP details")
    info_parser.add_argument("mcp_name", help="Name of MCP")

    # Uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall an MCP")
    uninstall_parser.add_argument("mcp_name", help="Name of MCP to uninstall")
    uninstall_parser.add_argument("--cli", choices=["claude", "gemini"], default="claude",
                                  help="CLI tool to unregister from (default: claude)")
    uninstall_parser.add_argument("--remove-files", action="store_true",
                                  help="Also remove installation files")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync MCP registry with filesystem")

    args = parser.parse_args()

    if args.command == "list":
        list_mcps(local_only=args.local, public_only=args.public, refresh_cache=args.refresh)
    elif args.command == "search":
        search_mcps(args.query)
    elif args.command == "install":
        install_mcp_cmd(args.mcp_name, cli=args.cli, no_register=args.no_register)
    elif args.command == "info":
        show_info(args.mcp_name)
    elif args.command == "uninstall":
        uninstall_mcp_cmd(args.mcp_name, cli=args.cli, remove_files=args.remove_files)
    elif args.command == "sync":
        sync_mcps()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
