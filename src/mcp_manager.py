#!/usr/bin/env python3
"""
MCPManager Class - Manages collections of MCPs and maintains YAML registries
"""

import re
from pathlib import Path
from typing import Optional, Dict
import yaml

# Import MCP class and related types
from .mcp import (
    MCP,
    MCPScope,
    MCPStatus,
    PUBLIC_MCPS_CONFIG,
    MCPS_CONFIG,
    PUBLIC_MCPS_DIR,
)


# =============================================================================
# MCPManager Class - Manages collections of MCPs
# =============================================================================

class MCPManager:
    """
    Manages available (public) and installed MCPs using YAML config files.

    - Public MCPs: src/configs/public_mcps.yaml
    - Installed MCPs: src/configs/mcps.yaml
    """

    def __init__(
        self,
        public_config: Path = PUBLIC_MCPS_CONFIG,
        installed_config: Path = MCPS_CONFIG
    ):
        """
        Initialize MCPManager.

        Args:
            public_config: Path to public MCPs YAML config
            installed_config: Path to installed MCPs YAML config
        """
        self.public_config = Path(public_config)
        self.installed_config = Path(installed_config)
        self._public_mcps_cache: Optional[Dict[str, MCP]] = None
        self._installed_mcps_cache: Optional[Dict[str, MCP]] = None
        self._ensure_configs_exist()

    # -------------------------------------------------------------------------
    # Configuration Management
    # -------------------------------------------------------------------------

    def _ensure_configs_exist(self):
        """Ensure configuration files exist"""
        if not self.public_config.exists():
            self.public_config.parent.mkdir(parents=True, exist_ok=True)
            with open(self.public_config, "w") as f:
                f.write("mcps: {}\n")

        if not self.installed_config.exists():
            self.installed_config.parent.mkdir(parents=True, exist_ok=True)
            with open(self.installed_config, "w") as f:
                f.write("mcps: {}\n")

    # -------------------------------------------------------------------------
    # Loading Methods
    # -------------------------------------------------------------------------

    def load_public_mcps(self, force_reload: bool = False) -> Dict[str, MCP]:
        """
        Load public MCPs from YAML config.

        Args:
            force_reload: If True, bypass cache and reload from file

        Returns:
            Dictionary of MCP objects keyed by name
        """
        if self._public_mcps_cache is not None and not force_reload:
            return self._public_mcps_cache

        try:
            with open(self.public_config, "r") as f:
                config = yaml.safe_load(f)

            # Handle empty YAML file
            if config is None:
                config = {}

            raw_mcps = config.get("mcps", {})
            mcps = {}

            for name, info in raw_mcps.items():
                try:
                    # Ensure info is a dict
                    if info is None:
                        info = {}
                    # Add name to info if not present
                    if 'name' not in info:
                        info['name'] = name
                    mcps[name] = MCP(**info)
                except Exception as e:
                    print(f"⚠️  Failed to load MCP '{name}': {e}")

            self._public_mcps_cache = mcps
            return mcps

        except Exception as e:
            print(f"❌ Failed to load public MCPs config: {e}")
            return {}

    def load_installed_mcps(self, force_reload: bool = False) -> Dict[str, MCP]:
        """
        Load installed MCPs from YAML config.

        Args:
            force_reload: If True, bypass cache and reload from file

        Returns:
            Dictionary of MCP objects keyed by name
        """
        if self._installed_mcps_cache is not None and not force_reload:
            return self._installed_mcps_cache

        try:
            with open(self.installed_config, "r") as f:
                config = yaml.safe_load(f)

            # Handle empty YAML file
            if config is None:
                config = {}

            raw_mcps = config.get("mcps", {})
            mcps = {}

            for name, info in raw_mcps.items():
                try:
                    # Ensure info is a dict
                    if info is None:
                        info = {}
                    # Add name to info if not present
                    if 'name' not in info:
                        info['name'] = name
                    mcps[name] = MCP(**info)
                except Exception as e:
                    print(f"⚠️  Failed to load MCP '{name}': {e}")

            self._installed_mcps_cache = mcps
            return mcps

        except Exception as e:
            print(f"❌ Failed to load installed MCPs config: {e}")
            return {}

    # -------------------------------------------------------------------------
    # Saving Methods
    # -------------------------------------------------------------------------

    def save_public_mcps(self, mcps: Dict[str, MCP]):
        """
        Save public MCPs to YAML config.

        Args:
            mcps: Dictionary of MCP objects
        """

        # Convert MCP objects to dictionaries
        mcps_dict = {}
        for name, mcp in mcps.items():
            mcp_data = mcp.to_dict()
            # Remove name from data (it's the key)
            mcp_data.pop('name', None)
            mcps_dict[name] = mcp_data

        with open(self.public_config, "w") as f:
            yaml.safe_dump({"mcps": mcps_dict}, f, default_flow_style=False)

        self._public_mcps_cache = mcps

    def save_installed_mcps(self, mcps: Dict[str, MCP]):
        """
        Save installed MCPs to YAML config.

        Args:
            mcps: Dictionary of MCP objects
        """
        # Convert MCP objects to dictionaries
        mcps_dict = {}
        for name, mcp in mcps.items():
            mcp_data = mcp.to_dict()
            # Remove name from data (it's the key)
            mcp_data.pop('name', None)
            mcps_dict[name] = mcp_data

        with open(self.installed_config, "w") as f:
            yaml.safe_dump({"mcps": mcps_dict}, f, default_flow_style=False)

        self._installed_mcps_cache = mcps

    # -------------------------------------------------------------------------
    # CRUD Operations - Public MCPs
    # -------------------------------------------------------------------------

    def add_public_mcp(self, mcp: MCP):
        """
        Add a new public MCP to registry.

        Args:
            mcp: MCP object to add
        """
        mcps = self.load_public_mcps()
        mcps[mcp.name] = mcp
        self.save_public_mcps(mcps)
        print(f"✅ Added '{mcp.name}' to public MCPs registry")

    def remove_public_mcp(self, name: str) -> bool:
        """
        Remove a public MCP from registry.

        Args:
            name: Name of MCP to remove

        Returns:
            True if removed, False if not found
        """
        mcps = self.load_public_mcps()
        if name in mcps:
            del mcps[name]
            self.save_public_mcps(mcps)
            print(f"✅ Removed '{name}' from public MCPs registry")
            return True
        else:
            print(f"⚠️  MCP '{name}' not found in public registry")
            return False

    def update_public_mcp(self, mcp: MCP):
        """
        Update an existing public MCP.

        Args:
            mcp: MCP object with updated information
        """
        mcps = self.load_public_mcps()
        if mcp.name in mcps:
            mcps[mcp.name] = mcp
            self.save_public_mcps(mcps)
            print(f"✅ Updated '{mcp.name}' in public MCPs registry")
        else:
            print(f"⚠️  MCP '{mcp.name}' not found. Use add_public_mcp() instead.")

    # -------------------------------------------------------------------------
    # CRUD Operations - Installed MCPs
    # -------------------------------------------------------------------------

    def add_installed_mcp(self, mcp: MCP):
        """
        Add an MCP to installed registry.

        Args:
            mcp: MCP object to add
        """
        mcps = self.load_installed_mcps()
        mcps[mcp.name] = mcp
        self.save_installed_mcps(mcps)
        print(f"✅ Added '{mcp.name}' to installed MCPs registry")

    def remove_installed_mcp(self, name: str) -> bool:
        """
        Remove an MCP from installed registry.

        Args:
            name: Name of MCP to remove

        Returns:
            True if removed, False if not found
        """
        mcps = self.load_installed_mcps()
        if name in mcps:
            del mcps[name]
            self.save_installed_mcps(mcps)
            print(f"✅ Removed '{name}' from installed MCPs registry")
            return True
        else:
            print(f"⚠️  MCP '{name}' not found in installed registry")
            return False

    def update_installed_mcp(self, mcp: MCP):
        """
        Update an existing installed MCP.

        Args:
            mcp: MCP object with updated information
        """
        mcps = self.load_installed_mcps()
        if mcp.name in mcps:
            mcps[mcp.name] = mcp
            self.save_installed_mcps(mcps)
            print(f"✅ Updated '{mcp.name}' in installed MCPs registry")
        else:
            print(f"⚠️  MCP '{mcp.name}' not found. Use add_installed_mcp() instead.")

    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------

    def get_mcp(self, name: str) -> Optional[MCP]:
        """
        Get an MCP by name (searches both public and installed).

        Args:
            name: Name of MCP

        Returns:
            MCP object or None if not found
        """
        # Check installed first
        installed = self.load_installed_mcps()
        if name in installed:
            return installed[name]

        # Check public
        public = self.load_public_mcps()
        if name in public:
            return public[name]

        return None

    def get_public_mcp(self, name: str) -> Optional[MCP]:
        """Get a public MCP by name"""
        return self.load_public_mcps().get(name)

    def get_installed_mcp(self, name: str) -> Optional[MCP]:
        """Get an installed MCP by name"""
        return self.load_installed_mcps().get(name)

    def list_mcps(
        self,
        source: Optional[str] = None,
        runtime: Optional[str] = None,
        installed_only: bool = False,
        public_only: bool = False
    ) -> Dict[str, MCP]:
        """
        List MCPs with optional filters.

        Args:
            source: Filter by source organization
            runtime: Filter by runtime type
            installed_only: Only return installed MCPs
            public_only: Only return public MCPs

        Returns:
            Dictionary of filtered MCPs
        """
        results = {}

        # Collect MCPs based on filters
        if not public_only:
            results.update(self.load_installed_mcps())

        if not installed_only:
            results.update(self.load_public_mcps())

        # Apply filters
        if source:
            results = {k: v for k, v in results.items() if v.source == source}

        if runtime:
            results = {k: v for k, v in results.items() if v.runtime == runtime}

        return results

    def search_mcps(self, query: str) -> Dict[str, MCP]:
        """
        Search MCPs by name or description.

        Args:
            query: Search query string

        Returns:
            Dictionary of matching MCPs
        """
        query = query.lower()
        results = {}

        # Search all MCPs
        all_mcps = self.list_mcps()

        for name, mcp in all_mcps.items():
            if (query in name.lower() or
                query in mcp.description.lower() or
                query in mcp.source.lower()):
                results[name] = mcp

        return results

    # -------------------------------------------------------------------------
    # MCP Creation Operations
    # -------------------------------------------------------------------------

    def create_mcp_from_github(
        self,
        github_url: str,
        mcp_dir: Optional[Path] = None,
        use_case_filter: str = "",
        add_to_registry: bool = True,
        rerun_from_step: int = 0
    ) -> Optional['MCP']:
        """
        Create a new MCP from a GitHub repository.

        Args:
            github_url: GitHub repository URL
            mcp_dir: Directory to create MCP in (defaults to tool-mcps/<repo_name>_mcp)
            use_case_filter: Filter for specific use cases
            add_to_registry: If True, add to public MCPs registry
            rerun_from_step: Force rerun from this step number (1-8)

        Returns:
            MCP object if successful, None otherwise
        """
        try:
            from mcp_creator import MCPCreator
            from pathlib import Path as PathLib

            # Determine MCP directory
            if mcp_dir is None:
                repo_name = PathLib(github_url.rstrip('.git')).name
                mcp_dir = PUBLIC_MCPS_DIR.parent / f"{repo_name}_mcp"

            # Get script directory (assuming mcp_manager.py is in src/)
            script_dir = Path(__file__).parent
            prompts_dir = script_dir / "prompts"

            # Create MCP using MCPCreator
            creator = MCPCreator(
                mcp_dir=mcp_dir,
                script_dir=script_dir,
                prompts_dir=prompts_dir,
                github_url=github_url,
                use_case_filter=use_case_filter,
                rerun_from_step=rerun_from_step
            )

            # Run the creation pipeline
            creator.run_all()

            # Get MCP info
            mcp_info = creator.get_created_mcp_info()

            # Create MCP object
            mcp = MCP(
                name=mcp_info['name'],
                url=github_url,
                description=f"MCP created from {github_url}",
                source="Generated",
                runtime="python",
                path=mcp_info['mcp_dir'],
                server_command="python",
                server_args=[mcp_info['server_file']] if mcp_info['server_file'] else []
            )

            # Add to registry if requested
            if add_to_registry:
                self.add_public_mcp(mcp)

            return mcp

        except Exception as e:
            print(f"❌ Failed to create MCP: {e}")
            return None

    def create_mcp_from_local(
        self,
        local_repo_path: Path,
        mcp_dir: Optional[Path] = None,
        use_case_filter: str = "",
        add_to_registry: bool = True,
        rerun_from_step: int = 0
    ) -> Optional['MCP']:
        """
        Create a new MCP from a local repository.

        Args:
            local_repo_path: Path to local repository
            mcp_dir: Directory to create MCP in (defaults to tool-mcps/<repo_name>_mcp)
            use_case_filter: Filter for specific use cases
            add_to_registry: If True, add to public MCPs registry
            rerun_from_step: Force rerun from this step number (1-8)

        Returns:
            MCP object if successful, None otherwise
        """
        try:
            from mcp_creator import MCPCreator

            local_repo_path = Path(local_repo_path)

            # Determine MCP directory
            if mcp_dir is None:
                repo_name = local_repo_path.name
                mcp_dir = PUBLIC_MCPS_DIR.parent / f"{repo_name}_mcp"

            # Get script directory (assuming mcp_manager.py is in src/)
            script_dir = Path(__file__).parent
            prompts_dir = script_dir / "prompts"

            # Create MCP using MCPCreator
            creator = MCPCreator(
                mcp_dir=mcp_dir,
                script_dir=script_dir,
                prompts_dir=prompts_dir,
                local_repo_path=str(local_repo_path),
                use_case_filter=use_case_filter,
                rerun_from_step=rerun_from_step
            )

            # Run the creation pipeline
            creator.run_all()

            # Get MCP info
            mcp_info = creator.get_created_mcp_info()

            # Create MCP object
            mcp = MCP(
                name=mcp_info['name'],
                description=f"MCP created from {local_repo_path}",
                source="Generated",
                runtime="python",
                path=mcp_info['mcp_dir'],
                server_command="python",
                server_args=[mcp_info['server_file']] if mcp_info['server_file'] else []
            )

            # Add to registry if requested
            if add_to_registry:
                self.add_public_mcp(mcp)

            return mcp

        except Exception as e:
            print(f"❌ Failed to create MCP: {e}")
            return None

    # -------------------------------------------------------------------------
    # High-level Operations
    # -------------------------------------------------------------------------

    def install_mcp(self, name: str, force: bool = False) -> bool:
        """
        Install an MCP by name.

        Args:
            name: Name of MCP to install
            force: Force re-installation

        Returns:
            True if successful, False otherwise
        """
        mcp = self.get_mcp(name)
        if not mcp:
            print(f"❌ MCP '{name}' not found")
            return False

        # Install the MCP
        success = mcp.install(force=force)

        # Add to installed registry if successful
        if success:
            self.add_installed_mcp(mcp)

        return success

    def uninstall_mcp(self, name: str, remove_files: bool = True) -> bool:
        """
        Uninstall an MCP by name.

        Args:
            name: Name of MCP to uninstall
            remove_files: Remove installation files

        Returns:
            True if successful, False otherwise
        """
        mcp = self.get_installed_mcp(name)
        if not mcp:
            print(f"⚠️  MCP '{name}' not found in installed registry")
            return False

        # Uninstall the MCP
        success = mcp.uninstall(remove_files=remove_files)

        # Remove from installed registry if successful
        if success:
            self.remove_installed_mcp(name)

        return success

    def register_mcp(
        self,
        name: str,
        cli: str = "claude",
        scope: MCPScope = MCPScope.GLOBAL
    ) -> bool:
        """
        Register an MCP with CLI.

        Args:
            name: Name of MCP to register
            cli: CLI tool (claude or gemini)
            scope: Registration scope

        Returns:
            True if successful, False otherwise
        """
        mcp = self.get_mcp(name)
        if not mcp:
            print(f"❌ MCP '{name}' not found")
            return False

        return mcp.register(cli=cli, scope=scope)

    def unregister_mcp(self, name: str, cli: str = "claude") -> bool:
        """
        Unregister an MCP from CLI.

        Args:
            name: Name of MCP to unregister
            cli: CLI tool

        Returns:
            True if successful, False otherwise
        """
        mcp = self.get_mcp(name)
        if not mcp:
            print(f"❌ MCP '{name}' not found")
            return False

        return mcp.unregister(cli=cli)

    def install_and_register(
        self,
        name: str,
        cli: str = "claude",
        scope: MCPScope = MCPScope.GLOBAL,
        force: bool = False
    ) -> bool:
        """
        Install and register an MCP in one operation.

        Args:
            name: Name of MCP
            cli: CLI tool
            scope: Registration scope
            force: Force re-installation

        Returns:
            True if both operations successful, False otherwise
        """
        # Install first
        if not self.install_mcp(name, force=force):
            return False

        # Then register
        return self.register_mcp(name, cli=cli, scope=scope)

    # -------------------------------------------------------------------------
    # Scanning and Discovery
    # -------------------------------------------------------------------------

    def scan_local_mcps(self) -> Dict[str, MCP]:
        """
        Scan filesystem for locally installed MCPs.

        Returns:
            Dictionary of discovered MCPs
        """
        mcps = {}

        if not PUBLIC_MCPS_DIR.exists():
            return mcps

        for item in PUBLIC_MCPS_DIR.iterdir():
            if item.is_dir():
                # Try to extract info from README
                readme = item / "README.md"
                description = "Locally installed MCP"

                if readme.exists():
                    try:
                        content = readme.read_text()
                        for line in content.split("\n"):
                            line = line.strip()
                            if not line or line.startswith("#") or line.startswith("```"):
                                continue
                            # Remove markdown links
                            line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
                            if len(line) > 10:
                                description = line[:80] + "..." if len(line) > 80 else line
                                break
                    except:
                        pass

                mcp = MCP(
                    name=item.name,
                    description=description,
                    source="Local",
                    path=str(item)
                )

                mcps[item.name] = mcp

        return mcps

    def sync_installed_with_filesystem(self):
        """
        Synchronize installed MCPs registry with filesystem.
        Adds newly discovered MCPs and removes non-existent ones.
        """
        installed = self.load_installed_mcps()
        local = self.scan_local_mcps()

        # Add newly discovered MCPs
        for name, mcp in local.items():
            if name not in installed:
                print(f"📦 Found new MCP: {name}")
                installed[name] = mcp

        # Remove non-existent MCPs
        to_remove = []
        for name, mcp in installed.items():
            if mcp.path and not Path(mcp.path).exists():
                print(f"🗑️  Removing non-existent MCP: {name}")
                to_remove.append(name)

        for name in to_remove:
            del installed[name]

        # Save updated registry
        self.save_installed_mcps(installed)
        print(f"✅ Synchronized {len(installed)} MCPs")

    # -------------------------------------------------------------------------
    # Display Methods
    # -------------------------------------------------------------------------

    def print_mcps(self, mcps: Dict[str, MCP], title: str = "MCPs"):
        """
        Pretty print MCPs.

        Args:
            mcps: Dictionary of MCPs to print
            title: Title for the output
        """
        if not mcps:
            print(f"\n{title}: None")
            return

        print(f"\n{title}")
        print("=" * 80)

        # Group by source
        sources = {}
        for name, mcp in mcps.items():
            source = mcp.source
            if source not in sources:
                sources[source] = []
            sources[source].append((name, mcp))

        for source, mcp_list in sorted(sources.items()):
            print(f"\n  [{source}]")
            for name, mcp in sorted(mcp_list):
                status = mcp.get_status()
                status_icon = {
                    MCPStatus.NOT_INSTALLED: "⚪",
                    MCPStatus.INSTALLED: "🔵",
                    MCPStatus.REGISTERED: "🟡",
                    MCPStatus.BOTH: "🟢"
                }.get(status, "⚪")

                desc = mcp.description[:50] + "..." if len(mcp.description) > 50 else mcp.description
                print(f"    {status_icon} {name:<20} [{mcp.runtime:<6}] {desc}")

        print(f"\n  Total: {len(mcps)} MCPs")
        print()


# =============================================================================
# Global Instance
# =============================================================================

# Create global MCPManager instance for convenience
mcp_manager = MCPManager()


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    print("MCPManager Class")
    print("=" * 80)

    # Create manager
    manager = MCPManager()

    # List all MCPs
    print("\n1. Listing all public MCPs:")
    public = manager.load_public_mcps()
    manager.print_mcps(public, "Public MCPs")

    # Get a specific MCP
    print("\n2. Getting a specific MCP:")
    mcp = manager.get_mcp("uniprot")
    if mcp:
        print(f"   Found: {mcp}")
        print(f"   Status: {mcp.get_status()}")

    # Search MCPs
    print("\n3. Searching MCPs:")
    results = manager.search_mcps("protein")
    manager.print_mcps(results, "Search Results for 'protein'")
