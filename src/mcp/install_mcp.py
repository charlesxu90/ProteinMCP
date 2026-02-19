#!/usr/bin/env python3
"""
MCP Installation Tool

List and install MCP servers from:
1. Local MCPs (tool-mcps/) - from src/configs/mcps.yaml
2. Public MCPs (tool-mcps/public/) - from src/configs/public_mcps.yaml

Usage:
    pmcp avail                   # Show all available MCPs
    pmcp avail --local           # Show local MCPs only
    pmcp avail --public          # Show public MCPs only
    pmcp status                  # Show downloaded/installed status
    pmcp status --refresh        # Refresh cache (slower)
    pmcp install <mcp_name>      # Install and register with Claude Code
    pmcp install <mcp_name> --cli gemini  # Install with Gemini CLI
    pmcp install <mcp_name> --no-register # Install only, don't register
    pmcp search <query>          # Search MCPs
    pmcp info <mcp_name>         # Show MCP details
    pmcp uninstall <mcp_name>    # Unregister MCP from CLI

Note: Status checks are cached for 5 minutes to improve performance. Use --refresh to force update.
"""

import argparse

from .mcp_manager import MCPManager
from .mcp import MCPStatus


# =============================================================================
# Global MCP Manager Instance
# =============================================================================

# Create global MCPManager instance for use throughout the module
mcp_manager = MCPManager()


# =============================================================================
# Core Functions
# =============================================================================

def show_available_mcps(local_only: bool = False, public_only: bool = False) -> None:
    """Show all available MCPs that can be installed."""

    # Load MCPs
    local_mcps = {}
    public_mcps = {}

    if not public_only:
        local_mcps = mcp_manager.load_installed_mcps()

    if not local_only:
        public_mcps = mcp_manager.load_public_mcps()

    # Display MCPs in ProteinMCP (located in tool-mcps/ if installed)
    if local_mcps and not public_only:
        print("\n📁 MCPs in ProteinMCP (located in tool-mcps/ if installed)")
        print("=" * 80)
        print("\n  Available local MCPs:")
        for name, mcp in sorted(local_mcps.items()):
            desc = mcp.description[:60] + "..." if len(mcp.description) > 60 else mcp.description
            print(f"    • {name:<20} [{mcp.runtime:<6}] {desc}")
        print(f"\n  Total: {len(local_mcps)} local MCPs")

    # Display public MCPs
    if public_mcps and not local_only:
        print("\n🌐 Public MCPs (from public registry, located in tool-mcps/public if installed)")
        print("=" * 80)

        # Group by source
        sources = {}
        for name, mcp in public_mcps.items():
            source = mcp.source
            if source not in sources:
                sources[source] = []
            sources[source].append((name, mcp))

        for source, mcp_list in sorted(sources.items()):
            print(f"\n  [{source}]")
            for name, mcp in sorted(mcp_list):
                desc = mcp.description[:60] + "..." if len(mcp.description) > 60 else mcp.description
                print(f"    • {name:<20} [{mcp.runtime:<6}] {desc}")

        print(f"\n  Total: {len(public_mcps)} public MCPs")

    if not local_mcps and not public_mcps:
        print("  No MCPs found.")

    print()


def show_status(refresh_cache: bool = False) -> None:
    """Show status of downloaded and installed MCPs."""

    # Refresh cache if requested
    if refresh_cache:
        from .status_cache import get_cache
        cache = get_cache()
        cache.invalidate()
        print("🔄 Cache invalidated, fetching fresh status...\n")

    # Load all MCPs
    local_mcps = mcp_manager.load_installed_mcps()
    public_mcps = mcp_manager.load_public_mcps()

    # Combine all MCPs
    all_mcps = {}
    all_mcps.update(public_mcps)
    all_mcps.update(local_mcps)  # Local MCPs override public ones

    # Separate MCPs by status
    downloaded = {}  # Installed on filesystem
    registered = {}  # Registered with Claude
    both = {}        # Both downloaded and registered

    for name, mcp in all_mcps.items():
        status = mcp.get_status()
        if status == MCPStatus.BOTH:
            both[name] = mcp
        elif status == MCPStatus.INSTALLED:
            downloaded[name] = mcp
        elif status == MCPStatus.REGISTERED:
            registered[name] = mcp

    # Display status
    print("📊 MCP Status Overview")
    print("=" * 80)

    # Show fully installed MCPs
    if both:
        print("\n🟢 Downloaded & Registered with Claude:")
        for name, mcp in sorted(both.items()):
            desc = mcp.description[:50] + "..." if len(mcp.description) > 50 else mcp.description
            scope = "Local" if name in local_mcps else "Public"
            print(f"    • {name:<20} [{scope:<7}] [{mcp.runtime:<6}] {desc}")
        print(f"\n  Total: {len(both)} MCPs")

    # Show downloaded but not registered
    if downloaded:
        print("\n🔵 Downloaded but not registered with Claude:")
        for name, mcp in sorted(downloaded.items()):
            desc = mcp.description[:50] + "..." if len(mcp.description) > 50 else mcp.description
            scope = "Local" if name in local_mcps else "Public"
            print(f"    • {name:<20} [{scope:<7}] [{mcp.runtime:<6}] {desc}")
        print(f"\n  Total: {len(downloaded)} MCPs")
        print(f"  Tip: Register with 'pmcp install <mcp_name>'")

    # Show registered but not downloaded (shouldn't happen often)
    if registered:
        print("\n🟡 Registered but not downloaded:")
        for name, mcp in sorted(registered.items()):
            desc = mcp.description[:50] + "..." if len(mcp.description) > 50 else mcp.description
            scope = "Local" if name in local_mcps else "Public"
            print(f"    • {name:<20} [{scope:<7}] [{mcp.runtime:<6}] {desc}")
        print(f"\n  Total: {len(registered)} MCPs")

    if not both and not downloaded and not registered:
        print("\n  No MCPs downloaded or installed.")
        print("  Use 'pmcp avail' to see available MCPs")
        print("  Use 'pmcp install <mcp_name>' to install")

    print()


def list_mcps(local_only: bool = False, public_only: bool = False, refresh_cache: bool = False) -> None:
    """List all available MCPs. (Deprecated - use show_available_mcps or show_status)"""

    # Refresh cache if requested
    if refresh_cache:
        from .status_cache import get_cache
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
        print(f"   Run 'pmcp avail' to see available MCPs.")
        return False

    # Invalidate cache to get fresh status (in case claude mcp remove was called)
    mcp.invalidate_status_cache(cli)

    # Check current status
    status = mcp.get_status(cli, use_cache=False)
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
            if not mcp_manager.register_mcp(mcp_name, cli=cli):
                return False
        else:
            print(f"✅ MCP '{mcp_name}' already registered with {cli}")

    # Show final status (use fresh data, not cache)
    final_status = mcp.get_status(cli, use_cache=False)
    print(f"\n✨ Final status: {final_status.value}")

    if final_status == MCPStatus.BOTH:
        print(f"🎉 Successfully installed and registered '{mcp_name}'!")

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

    if mcp.docker_image:
        print(f"  Docker Image: {mcp.docker_image}")

    if mcp.docker_args:
        print(f"  Docker Args: {' '.join(mcp.docker_args)}")

    if mcp.docker_volumes:
        print(f"  Docker Volumes: {', '.join(mcp.docker_volumes)}")

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
    else:
        print(f"✅ Successfully unregistered '{mcp_name}'")
    return True


def sync_mcps() -> None:
    """Synchronize MCP registry with filesystem."""
    print("🔄 Synchronizing MCP registry with filesystem...")
    mcp_manager.sync_installed_with_filesystem()
