#!/usr/bin/env python3
"""
MCP Class - Represents a single MCP server with installation and registration operations
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from enum import Enum


# =============================================================================
# Constants and Path Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()  # src/mcp/
SRC_DIR = SCRIPT_DIR.parent  # src/
PROJECT_ROOT = SRC_DIR.parent  # ProteinMCP root
CONFIGS_DIR = SCRIPT_DIR / "configs"
PUBLIC_MCPS_CONFIG = CONFIGS_DIR / "public_mcps.yaml"
MCPS_CONFIG = CONFIGS_DIR / "mcps.yaml"
TOOL_MCPS_DIR = PROJECT_ROOT / "tool-mcps"
PUBLIC_MCPS_DIR = TOOL_MCPS_DIR / "public"


def resolve_path(path_str: str) -> Path:
    """
    Resolve a path that may be relative to PROJECT_ROOT.

    Args:
        path_str: Path string (absolute or relative to PROJECT_ROOT)

    Returns:
        Absolute Path object
    """
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def make_relative_path(abs_path: str) -> str:
    """
    Convert an absolute path to a relative path from PROJECT_ROOT.

    Args:
        abs_path: Absolute path string

    Returns:
        Relative path string if under PROJECT_ROOT, otherwise original path
    """
    try:
        path = Path(abs_path)
        if path.is_absolute():
            rel_path = path.relative_to(PROJECT_ROOT)
            return str(rel_path)
    except ValueError:
        pass
    return abs_path


# =============================================================================
# Enums
# =============================================================================

class MCPRuntime(Enum):
    """MCP runtime types"""
    PYTHON = "python"
    NODE = "node"
    UVX = "uvx"
    NPX = "npx"
    BINARY = "binary"


class MCPScope(Enum):
    """MCP registration scope"""
    PROJECT = "project"
    GLOBAL = "global"


class MCPStatus(Enum):
    """MCP installation status"""
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    REGISTERED = "registered"
    BOTH = "both"  # installed and registered


# =============================================================================
# MCP Class - Represents a single MCP server
# =============================================================================

@dataclass
class MCP:
    """
    Represents a single MCP server with full lifecycle operations.

    Attributes:
        name: MCP identifier
        url: Repository URL
        description: Brief description
        source: Source organization
        runtime: Runtime type (python, node, uvx, npx, binary)
        setup_commands: Commands to run after cloning
        setup_script: Shell script for setup (e.g., quick_setup.sh)
        server_command: Command to start the server
        server_args: Arguments for the server command
        env_vars: Environment variables needed
        dependencies: System dependencies required
        path: Local installation path (if installed)
    """

    name: str
    url: str = ""
    description: str = ""
    source: str = "Community"
    runtime: str = "python"
    setup_commands: List[str] = field(default_factory=list)
    setup_script: Optional[str] = None
    server_command: str = ""
    server_args: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    path: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize runtime type"""
        try:
            MCPRuntime(self.runtime)
        except ValueError:
            # Default to python if invalid
            self.runtime = MCPRuntime.PYTHON.value

    # -------------------------------------------------------------------------
    # Status Query Methods
    # -------------------------------------------------------------------------

    def is_installed(self) -> bool:
        """Check if MCP is installed locally"""
        if self.path:
            path = resolve_path(self.path)
            return path.exists()

        # Check in default locations
        if self.runtime in [MCPRuntime.UVX.value, MCPRuntime.NPX.value]:
            # Package-based MCPs don't need local installation
            return True

        # Check in public MCPs directory
        if self.url:
            repo_name = self.url.rstrip("/").split("/")[-1]
            cloned_path = PUBLIC_MCPS_DIR / repo_name
            if cloned_path.exists():
                self.path = str(cloned_path)
                return True

        return False

    def is_registered(self, cli: str = "claude") -> bool:
        """
        Check if MCP is registered with specified CLI.

        Args:
            cli: CLI tool name (claude or gemini)

        Returns:
            True if registered, False otherwise
        """
        clean_name = self._get_clean_name()

        try:
            if cli == "claude":
                result = subprocess.run(
                    ["claude", "mcp", "list"],
                    capture_output=True,
                    text=True,
                    timeout=30  # Increased timeout for health checks
                )
                return clean_name in result.stdout

            elif cli == "gemini":
                result = subprocess.run(
                    ["gemini", "mcp", "list"],
                    capture_output=True,
                    text=True,
                    timeout=30  # Increased timeout for health checks
                )
                return clean_name in result.stdout

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

        return False

    def get_status(self, cli: str = "claude", use_cache: bool = True) -> MCPStatus:
        """
        Get overall status of MCP.

        Args:
            cli: CLI tool to check registration against
            use_cache: If True, use cached status when available (default: True)

        Returns:
            MCPStatus enum value
        """
        # Try cache first if enabled
        if use_cache:
            from .status_cache import get_cache
            cache = get_cache()
            cached_status = cache.get_status(f"{self.name}:{cli}")
            if cached_status:
                try:
                    return MCPStatus(cached_status)
                except ValueError:
                    pass  # Invalid cached value, fall through to real check

        # Perform real status check
        installed = self.is_installed()
        registered = self.is_registered(cli)

        if installed and registered:
            status = MCPStatus.BOTH
        elif registered:
            status = MCPStatus.REGISTERED
        elif installed:
            status = MCPStatus.INSTALLED
        else:
            status = MCPStatus.NOT_INSTALLED

        # Update cache
        if use_cache:
            from .status_cache import get_cache
            cache = get_cache()
            cache.set_status(f"{self.name}:{cli}", status.value)

        return status

    def invalidate_status_cache(self, cli: str = "claude"):
        """
        Invalidate cached status for this MCP.

        Args:
            cli: CLI tool to invalidate cache for
        """
        from .status_cache import get_cache
        cache = get_cache()
        # Read cache, remove this MCP's status, and write back
        cache_data = cache.read_cache()
        statuses = cache_data.get("statuses", {})
        key = f"{self.name}:{cli}"
        if key in statuses:
            del statuses[key]
            cache.write_cache(statuses)

    # -------------------------------------------------------------------------
    # Installation Methods
    # -------------------------------------------------------------------------

    def install(self, force: bool = False) -> bool:
        """
        Install MCP to local machine.

        Args:
            force: If True, re-install even if already installed

        Returns:
            True if successful, False otherwise
        """
        # Invalidate status cache to ensure fresh status check
        # (in case claude mcp remove was called directly)
        self.invalidate_status_cache()

        # Check if already installed
        if self.is_installed() and not force:
            print(f"✅ MCP '{self.name}' is already installed at: {self.path}")
            return True

        # Package-based MCPs don't need installation
        if self.runtime in [MCPRuntime.UVX.value, MCPRuntime.NPX.value]:
            print(f"✅ MCP '{self.name}' is a {self.runtime} package (no installation needed)")
            # Invalidate cache since installation state may have changed
            self.invalidate_status_cache()
            return True

        # Handle local tool MCPs (check if already present in tool-mcps directory)
        if self.path:
            local_path = resolve_path(self.path)

            # If local path exists, use it (even if URL is provided)
            if local_path.exists():
                # Keep path as-is (may be relative) for portability
                print(f"📁 Found local MCP '{self.name}' at: {local_path}")

                # Invalidate cache since installation state may have changed
                self.invalidate_status_cache()

                # Run setup (script or commands)
                return self._run_setup()

                return True

            # If local path doesn't exist but URL is provided, fall through to clone
            elif self.url:
                print(f"📦 Local path not found at {local_path}, will clone from GitHub...")
            # If no URL and path doesn't exist, error
            else:
                print(f"❌ Local MCP path does not exist: {local_path}")
                return False

        # Clone repository for public/tool MCPs
        if not self.url:
            print(f"❌ No URL provided for MCP '{self.name}'")
            return False

        # Determine target path for cloning
        if self.path:
            # If path is specified, clone to that location
            target_path = resolve_path(self.path)
        else:
            # Default: clone to public MCPs directory
            repo_name = self.url.rstrip("/").split("/")[-1]
            PUBLIC_MCPS_DIR.mkdir(parents=True, exist_ok=True)
            target_path = PUBLIC_MCPS_DIR / repo_name

        # Handle existing installation
        if target_path.exists():
            if force:
                print(f"🗑️  Removing existing installation at: {target_path}")
                shutil.rmtree(target_path)
            else:
                print(f"📁 MCP '{self.name}' already exists at: {target_path}")
                self.path = str(target_path)
                return True

        # Create parent directory if it doesn't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Clone repository
        print(f"📦 Cloning {self.name} from {self.source}...")
        print(f"   URL: {self.url}")
        print(f"   Destination: {target_path}")

        try:
            result = subprocess.run(
                ["git", "clone", self.url, str(target_path)],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                print(f"❌ Git clone failed: {result.stderr}")
                return False

            self.path = str(target_path)
            print(f"✅ Successfully cloned {self.name}")

            # Invalidate cache since installation state changed
            self.invalidate_status_cache()

            # Run setup (script or commands)
            return self._run_setup()

        except FileNotFoundError:
            print("❌ Git not found. Please install git first.")
            return False
        except subprocess.TimeoutExpired:
            print("❌ Clone timed out (exceeded 5 minutes)")
            return False
        except Exception as e:
            print(f"❌ Clone failed: {e}")
            return False

    def uninstall(self, remove_files: bool = True) -> bool:
        """
        Uninstall MCP from local machine.

        Args:
            remove_files: If True, remove installation files

        Returns:
            True if successful, False otherwise
        """
        if not self.is_installed():
            print(f"⚠️  MCP '{self.name}' is not installed")
            return True

        # Package-based MCPs don't have local files
        if self.runtime in [MCPRuntime.UVX.value, MCPRuntime.NPX.value]:
            print(f"✅ MCP '{self.name}' is a {self.runtime} package (no files to remove)")
            self.path = None
            # Invalidate cache since uninstall state changed
            self.invalidate_status_cache()
            return True

        # Remove installation directory
        if remove_files and self.path:
            try:
                path = resolve_path(self.path)
                if path.exists():
                    print(f"🗑️  Removing {path}...")
                    shutil.rmtree(path)
                    print(f"✅ Successfully removed {self.name}")
                self.path = None
                # Invalidate cache since uninstall state changed
                self.invalidate_status_cache()
                return True
            except Exception as e:
                print(f"❌ Failed to remove files: {e}")
                return False

        return True

    def _run_setup_script(self) -> bool:
        """
        Run the setup_script (e.g., quick_setup.sh) if available.

        Returns:
            True if successful or no script exists, False on failure
        """
        if not self.path or not self.setup_script:
            return False

        cwd = resolve_path(self.path)
        script_path = cwd / self.setup_script

        if not script_path.exists():
            print(f"⚠️  Setup script not found: {script_path}")
            return False

        print(f"📦 Running setup script: {self.setup_script}")

        try:
            # Make the script executable
            import os
            os.chmod(script_path, 0o755)

            # Run the setup script
            result = subprocess.run(
                ["bash", str(script_path)],
                cwd=str(cwd),
                capture_output=False,  # Show output in real-time
                timeout=1800  # 30 minutes timeout for complex setups
            )

            if result.returncode != 0:
                print(f"⚠️  Setup script failed with exit code: {result.returncode}")
                return False

            print(f"✅ Setup script completed successfully")
            return True

        except subprocess.TimeoutExpired:
            print(f"⚠️  Setup script timed out (exceeded 30 minutes)")
            return False
        except Exception as e:
            print(f"⚠️  Setup script error: {e}")
            return False

    def _run_setup_commands(self) -> bool:
        """Run setup commands after installation"""
        if not self.path:
            return False

        # Resolve path to absolute for command execution
        cwd = resolve_path(self.path)
        print(f"📦 Running setup commands for {self.name}...")

        for cmd in self.setup_commands:
            print(f"   Running: {cmd}")
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=str(cwd),
                    capture_output=True,
                    text=True,
                    timeout=600
                )

                if result.returncode != 0:
                    print(f"⚠️  Setup command failed: {result.stderr}")
                    print(f"   You may need to run this manually: {cmd}")
                    # Continue with other commands
                else:
                    print(f"   ✅ {cmd}")

            except subprocess.TimeoutExpired:
                print(f"⚠️  Setup command timed out: {cmd}")
                return False
            except Exception as e:
                print(f"⚠️  Setup command error: {e}")
                return False

        return True

    def _run_setup(self) -> bool:
        """
        Run setup using setup_script if available, otherwise fall back to setup_commands.

        Returns:
            True if successful, False otherwise
        """
        # First, try to run setup_script (e.g., quick_setup.sh)
        if self.setup_script:
            cwd = resolve_path(self.path) if self.path else None
            if cwd and (cwd / self.setup_script).exists():
                print(f"🔧 Found setup script: {self.setup_script}")
                if self._run_setup_script():
                    return True
                else:
                    print("⚠️  Setup script failed, falling back to setup commands...")

        # Fall back to setup_commands
        if self.setup_commands:
            return self._run_setup_commands()

        # No setup needed
        print("ℹ️  No setup script or commands configured")
        return True

    # -------------------------------------------------------------------------
    # Registration Methods
    # -------------------------------------------------------------------------

    def register(self, cli: str = "claude", scope: MCPScope = MCPScope.GLOBAL) -> bool:
        """
        Register MCP with specified CLI.

        Args:
            cli: CLI tool (claude or gemini)
            scope: Registration scope (project or global) - currently not implemented

        Returns:
            True if successful, False otherwise
        """
        # Note: scope parameter is reserved for future use
        _ = scope  # Silence unused parameter warning
        clean_name = self._get_clean_name()

        # Check CLI availability
        if not shutil.which(cli):
            print(f"❌ {cli} CLI not found. Please install it first.")
            return False

        # Check if already registered
        if self.is_registered(cli):
            print(f"⚠️  MCP '{clean_name}' already registered with {cli}")
            response = input("   Update registration? [y/N]: ").strip().lower()
            if response != "y":
                return True
            # Unregister first
            self.unregister(cli)

        print(f"\n🔧 Registering '{clean_name}' with {cli}...")

        # Build registration command based on runtime type
        if self.runtime == MCPRuntime.UVX.value:
            return self._register_uvx(cli, clean_name)
        elif self.runtime == MCPRuntime.NPX.value:
            return self._register_npx(cli, clean_name)
        elif self.runtime == MCPRuntime.NODE.value:
            return self._register_node(cli, clean_name)
        else:  # Python
            return self._register_python(cli, clean_name)

    def unregister(self, cli: str = "claude") -> bool:
        """
        Unregister MCP from specified CLI.

        Args:
            cli: CLI tool (claude or gemini)

        Returns:
            True if successful, False otherwise
        """
        clean_name = self._get_clean_name()

        if not shutil.which(cli):
            print(f"❌ {cli} CLI not found")
            return False

        print(f"🗑️  Unregistering '{clean_name}' from {cli}...")

        try:
            result = subprocess.run(
                [cli, "mcp", "remove", clean_name],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                print(f"❌ Unregistration failed: {result.stderr}")
                return False

            print(f"✅ Successfully removed '{clean_name}' from {cli}")

            # Invalidate cache since unregistration state changed
            self.invalidate_status_cache(cli)

            return True

        except subprocess.TimeoutExpired:
            print("❌ Unregistration timed out")
            return False
        except Exception as e:
            print(f"❌ Unregistration failed: {e}")
            return False

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _get_clean_name(self) -> str:
        """Get cleaned name for CLI registration"""
        return self.name.replace("/", "_").replace("-", "_")

    def _register_uvx(self, cli: str, clean_name: str) -> bool:
        """Register uvx-based MCP"""
        cmd = [cli, "mcp", "add", clean_name]

        # Add environment variables
        for key, value in self.env_vars.items():
            cmd.extend(["--env", f"{key}={value}"])

        cmd.append("--")
        cmd.append("uvx")
        cmd.extend(self.server_args)

        return self._run_register_command(cmd, cli, clean_name)

    def _register_npx(self, cli: str, clean_name: str) -> bool:
        """Register npx-based MCP"""
        cmd = [cli, "mcp", "add", clean_name]

        # Add environment variables
        for key, value in self.env_vars.items():
            cmd.extend(["--env", f"{key}={value}"])

        cmd.append("--")
        cmd.append("npx")
        cmd.extend(self.server_args)

        return self._run_register_command(cmd, cli, clean_name)

    def _register_node(self, cli: str, clean_name: str) -> bool:
        """Register Node.js-based MCP"""
        if not self.path:
            print(f"❌ MCP not installed. Run install() first.")
            return False

        cmd = [cli, "mcp", "add", clean_name]

        # Add environment variables
        for key, value in self.env_vars.items():
            cmd.extend(["--env", f"{key}={value}"])

        cmd.append("--")
        cmd.append(self.server_command or "node")

        # Resolve path to absolute
        mcp_path = resolve_path(self.path)
        args = []
        for arg in self.server_args:
            # Replace $MCP_PATH placeholder with absolute path
            arg = arg.replace("$MCP_PATH", str(mcp_path))

            # Convert relative paths to absolute (for .js files and similar)
            arg_path = Path(arg)
            if not arg_path.is_absolute() and (arg.endswith('.js') or arg.endswith('.py') or '/' in arg):
                arg = str(mcp_path / arg)

            args.append(arg)

        cmd.extend(args)

        return self._run_register_command(cmd, cli, clean_name)

    def _register_python(self, cli: str, clean_name: str) -> bool:
        """Register Python-based MCP"""
        if not self.path:
            print(f"❌ MCP not installed. Run install() first.")
            return False

        # Find Python environment
        python_cmd = self._find_python_env()

        cmd = [cli, "mcp", "add", clean_name]

        # Add environment variables
        for key, value in self.env_vars.items():
            cmd.extend(["--env", f"{key}={value}"])

        cmd.append("--")
        cmd.append(python_cmd)

        if self.server_command and self.server_args:
            # Use specified server command and args
            # Resolve path to absolute
            mcp_path = resolve_path(self.path)
            args = []
            for arg in self.server_args:
                # Replace $MCP_PATH placeholder with absolute path
                arg = arg.replace("$MCP_PATH", str(mcp_path))

                # Convert relative paths to absolute
                arg_path = Path(arg)
                if not arg_path.is_absolute() and (arg.endswith('.py') or '/' in arg):
                    arg = str(mcp_path / arg)

                args.append(arg)
            cmd.extend(args)
        else:
            # Auto-detect server entry point
            server_path = self._find_server_entry()
            if not server_path:
                print(f"⚠️  Could not find server entry point in: {self.path}")
                return False
            cmd.append(str(server_path))

        return self._run_register_command(cmd, cli, clean_name)

    def _run_register_command(self, cmd: List[str], cli: str, clean_name: str) -> bool:
        """Execute registration command"""
        print(f"   Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                print(f"❌ Registration failed: {result.stderr}")
                return False

            print(f"✅ Successfully registered '{clean_name}' with {cli}")
            print(f"\n   Verify with: {cli} mcp list")
            print(f"   Remove with: {cli} mcp remove {clean_name}")

            # Invalidate cache since registration state changed
            self.invalidate_status_cache(cli)

            return True

        except subprocess.TimeoutExpired:
            print("❌ Registration timed out")
            return False
        except Exception as e:
            print(f"❌ Registration failed: {e}")
            return False

    def _find_server_entry(self) -> Optional[Path]:
        """Find MCP server entry point"""
        if not self.path:
            return None

        mcp_path = resolve_path(self.path)

        # Common locations
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

    def _find_python_env(self) -> str:
        """Find Python executable"""
        if not self.path:
            return "python"

        mcp_path = resolve_path(self.path)

        # Check for local environments
        env_candidates = [
            mcp_path / "env" / "bin" / "python",
            mcp_path / ".venv" / "bin" / "python",
            mcp_path / "venv" / "bin" / "python",
        ]

        for env in env_candidates:
            if env.exists():
                return str(env.resolve())

        # Fall back to system python
        return "python"

    # -------------------------------------------------------------------------
    # Serialization Methods
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Convert MCP to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCP':
        """Create MCP from dictionary"""
        return cls(**data)

    def __repr__(self) -> str:
        status = self.get_status()
        return f"MCP(name='{self.name}', runtime={self.runtime}, status={status.value})"
