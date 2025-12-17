#!/usr/bin/env python3
"""
MCPCreator Class - Creates MCP servers from GitHub/local repositories

This module provides the MCPCreator class which handles the entire pipeline
of creating an MCP (Model Context Protocol) server from a repository.
"""

import shutil
from pathlib import Path
from typing import Optional
from loguru import logger

from .utils import (
    log_progress,
    check_marker,
    create_marker,
    run_command,
    run_claude_with_streaming
)


class MCPCreator:
    """
    MCP (Model Context Protocol) Creator

    Creates an MCP server from a GitHub repository or local code with tutorials.
    Manages the entire pipeline from cloning to deployment.

    Pipeline Steps:
    1. Setup project environment and prepare working directories
    2. Clone GitHub repository (or use local repository)
    3. Setup conda environment & scan common use cases
    4. Execute the common use cases in repository (bugfix if needed)
    5. Write script for functions to execute common use cases (test and bugfix if needed)
    6. Extract MCP tools from use case scripts and wrap in MCP server (test and bugfix if needed)
    7. Test Claude and Gemini integration (bugfix if needed)
    8. Create comprehensive README documentation
    """

    def __init__(
        self,
        mcp_dir: Path,
        script_dir: Path,
        prompts_dir: Path,
        github_url: str = "",
        local_repo_path: str = "",
        use_case_filter: str = "",
        api_key: str = "",
        rerun_from_step: int = 0
    ):
        """
        Initialize MCP Creator

        Args:
            mcp_dir: Target directory for MCP project
            script_dir: Directory containing the create_mcp script
            prompts_dir: Directory containing prompt templates
            github_url: GitHub repository URL to clone (optional if local_repo_path provided)
            local_repo_path: Path to local repository (alternative to github_url)
            use_case_filter: Optional filter for use cases to focus on
            api_key: API key for Claude/Gemini integration testing
            rerun_from_step: Force rerun from this step number (1-8), 0 means no forced rerun
        """
        self.mcp_dir = mcp_dir.resolve()
        self.github_url = github_url
        self.local_repo_path = Path(local_repo_path) if local_repo_path else None
        self.script_dir = script_dir
        self.prompts_dir = prompts_dir
        self.use_case_filter = use_case_filter
        self.api_key = api_key
        self.rerun_from_step = rerun_from_step

        # Validate that either github_url or local_repo_path is provided
        if not github_url and not local_repo_path:
            raise ValueError("Either github_url or local_repo_path must be provided")

        # Extract repo name from URL or local path
        if local_repo_path:
            self.repo_name = Path(local_repo_path).name
        else:
            self.repo_name = Path(github_url.rstrip('.git')).name

        # Track step execution status
        self.step_status = {}

    def _get_marker(self, step: str) -> Path:
        """Get marker file path for a step"""
        return self.mcp_dir / ".pipeline" / f"{step}_done"

    def _clear_markers_from_step(self, from_step: int):
        """Clear markers from a certain step onwards to force rerun"""
        step_markers = {
            1: "01_setup",
            2: "02_clone",
            3: "03_setup_env",
            4: "04_execute_cases",
            5: "05_write_scripts",
            6: "06_wrap_mcp",
            7: "07_test_integration",
            8: "08_create_readme"
        }

        pipeline_dir = self.mcp_dir / ".pipeline"
        if not pipeline_dir.exists():
            return

        cleared = []
        for step_num in range(from_step, 9):
            if step_num in step_markers:
                marker = self._get_marker(step_markers[step_num])
                if marker.exists():
                    marker.unlink()
                    cleared.append(step_num)

        if cleared:
            logger.info(f"🔄 Cleared markers for steps: {cleared} (will rerun)")

    # ========================================================================
    # Step 1: Setup project environment and prepare working directories
    # ========================================================================
    def step1_setup_project(self) -> Path:
        """Step 1: Setup project environment and prepare working directories"""
        pipeline_dir = self.mcp_dir / ".pipeline"
        marker = self._get_marker("01_setup")

        if check_marker(marker):
            log_progress(1, "Setup project environment and prepare working directories", "skip")
            self.step_status['step1'] = 'skipped'
            return self.mcp_dir

        log_progress(1, "Setup project environment and prepare working directories", "start")

        # Create project directory
        self.mcp_dir.mkdir(parents=True, exist_ok=True)
        pipeline_dir.mkdir(parents=True, exist_ok=True)

        # Copy configs/templates if they exist and not already present
        for folder_name_item in ['claude', 'templates', 'tools']:
            src = self.script_dir / 'configs' / folder_name_item
            dst = self.mcp_dir / folder_name_item if folder_name_item != 'claude' else self.mcp_dir / f'.{folder_name_item}'

            if not dst.exists() and src.exists():
                shutil.copytree(src, dst)
                logger.info(f"  Copied {folder_name_item}")
            else:
                logger.info(f"  {folder_name_item} already exists or source missing")

        # Create all required directories
        folders = [
            "repo",
            "scripts",
            "src",
            "examples",
            "claude_outputs"
        ]

        for folder in folders:
            folder_path = self.mcp_dir / folder
            folder_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"  Created: {folders}")

        create_marker(marker)
        log_progress(1, "Setup project environment and prepare working directories", "complete")
        self.step_status['step1'] = 'executed'

        return self.mcp_dir

    # ========================================================================
    # Step 2: Clone GitHub repository
    # ========================================================================
    def step2_clone_repo(self) -> str:
        """Step 2: Clone the GitHub repository or use local repository"""
        repo_dir = self.mcp_dir / "repo" / self.repo_name
        marker = self._get_marker("02_clone")

        if check_marker(marker):
            log_progress(2, "Clone GitHub repository", "skip")
            self.step_status['step2'] = 'skipped'
            return self.repo_name

        # Use local repository if provided
        if self.local_repo_path:
            log_progress(2, "Setup repository (local)", "start")

            if repo_dir.exists():
                logger.info(f"  Repository already exists: {repo_dir}")
            else:
                # Verify local path exists
                if not self.local_repo_path.exists():
                    raise FileNotFoundError(f"Local repository not found: {self.local_repo_path}")

                # Copy or symlink local repository
                logger.info(f"  Copying local repository from {self.local_repo_path}...")
                shutil.copytree(self.local_repo_path, repo_dir, symlinks=True)
                logger.info("  Local repository copied successfully")

            create_marker(marker)
            log_progress(2, "Setup repository (local)", "complete")
            self.step_status['step2'] = 'executed'
            return self.repo_name

        # Clone from GitHub
        log_progress(2, "Clone GitHub repository", "start")

        # Skip if already cloned
        if repo_dir.exists():
            logger.info(f"  Repository already exists: {repo_dir}")
        else:
            # Try different cloning strategies
            try:
                # Try with submodules first
                logger.info(f"  Cloning {self.github_url} with submodules...")
                run_command(["git", "clone", "--recurse-submodules", self.github_url, str(repo_dir)])
                logger.info("  Cloned with submodules")
            except:
                try:
                    # Try shallow clone
                    logger.info("  Trying shallow clone...")
                    run_command(["git", "clone", "--depth=1", self.github_url, str(repo_dir)])
                    logger.info("  Shallow clone successful")
                except:
                    # Try plain clone
                    logger.info("  Trying plain clone...")
                    run_command(["git", "clone", self.github_url, str(repo_dir)])
                    logger.info("  Plain clone successful")

        create_marker(marker)
        log_progress(2, "Clone GitHub repository", "complete")
        self.step_status['step2'] = 'executed'

        return self.repo_name

    # ========================================================================
    # Step 3: Setup conda environment & scan common use cases
    # ========================================================================
    def step3_setup_env_and_scan(self):
        """Step 3: Setup conda environment & scan common use cases"""
        marker = self._get_marker("03_setup_env")
        output_file = self.mcp_dir / "claude_outputs" / "step3_output.json"

        if check_marker(marker):
            log_progress(3, "Setup conda environment & scan common use cases", "skip")
            self.step_status['step3'] = 'skipped'
            return

        log_progress(3, "Setup conda environment & scan common use cases", "start")

        # Read and prepare prompt
        prompt_file = self.prompts_dir / "step3_setup_env_prompt.md"
        if not prompt_file.exists():
            logger.warning(f"  ⚠️ Prompt file not found: {prompt_file}")
            logger.warning("  You'll need to run this step manually or create the prompt file")
            self.step_status['step3'] = 'failed'
            return

        with open(prompt_file, 'r') as f:
            prompt_content = f.read()

        # Replace placeholders
        prompt_content = prompt_content.replace('${repo_name}', self.repo_name)
        prompt_content = prompt_content.replace('${use_case_filter}', self.use_case_filter or '')

        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir, self.api_key):
            create_marker(marker)
            log_progress(3, "Setup conda environment & scan common use cases", "complete")
            self.step_status['step3'] = 'executed'
        else:
            self.step_status['step3'] = 'failed'

    # ========================================================================
    # Step 4: Execute the common use cases in repository (bugfix if needed)
    # ========================================================================
    def step4_execute_use_cases(self):
        """Step 4: Execute the common use cases in repository (bugfix if needed)"""
        marker = self._get_marker("04_execute_cases")
        output_file = self.mcp_dir / "claude_outputs" / "step4_output.json"

        if check_marker(marker):
            log_progress(4, "Execute common use cases (bugfix if needed)", "skip")
            self.step_status['step4'] = 'skipped'
            return

        log_progress(4, "Execute common use cases (bugfix if needed)", "start")

        # Read and prepare prompt
        prompt_file = self.prompts_dir / "step4_execute_cases_prompt.md"
        if not prompt_file.exists():
            logger.warning(f"  ⚠️ Prompt file not found: {prompt_file}")
            logger.warning("  You'll need to run this step manually or create the prompt file")
            self.step_status['step4'] = 'failed'
            return

        with open(prompt_file, 'r') as f:
            prompt_content = f.read()

        # Replace placeholders
        prompt_content = prompt_content.replace('${repo_name}', self.repo_name)
        prompt_content = prompt_content.replace('${api_key}', self.api_key or '')

        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir, self.api_key):
            create_marker(marker)
            log_progress(4, "Execute common use cases (bugfix if needed)", "complete")
            self.step_status['step4'] = 'executed'
        else:
            self.step_status['step4'] = 'failed'

    # ========================================================================
    # Step 5: Write script for functions to execute common use cases
    # ========================================================================
    def step5_write_scripts(self):
        """Step 5: Write script for functions to execute common use cases (test and bugfix if needed)"""
        marker = self._get_marker("05_write_scripts")
        output_file = self.mcp_dir / "claude_outputs" / "step5_output.json"

        if check_marker(marker):
            log_progress(5, "Write scripts for use case functions (test & bugfix)", "skip")
            self.step_status['step5'] = 'skipped'
            return

        log_progress(5, "Write scripts for use case functions (test & bugfix)", "start")

        # Read and prepare prompt
        prompt_file = self.prompts_dir / "step5_write_scripts_prompt.md"
        if not prompt_file.exists():
            logger.warning(f"  ⚠️ Prompt file not found: {prompt_file}")
            logger.warning("  You'll need to run this step manually or create the prompt file")
            self.step_status['step5'] = 'failed'
            return

        with open(prompt_file, 'r') as f:
            prompt_content = f.read()

        # Replace placeholders
        prompt_content = prompt_content.replace('${repo_name}', self.repo_name)
        prompt_content = prompt_content.replace('${api_key}', self.api_key or '')

        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir, self.api_key):
            create_marker(marker)
            log_progress(5, "Write scripts for use case functions (test & bugfix)", "complete")
            self.step_status['step5'] = 'executed'
        else:
            self.step_status['step5'] = 'failed'

    # ========================================================================
    # Step 6: Extract MCP tools from use case scripts and wrap in MCP server
    # ========================================================================
    def step6_extract_and_wrap_mcp(self):
        """Step 6: Extract MCP tools from use case scripts and wrap in MCP server (test and bugfix if needed)"""
        marker = self._get_marker("06_wrap_mcp")
        output_file = self.mcp_dir / "claude_outputs" / "step6_output.json"

        if check_marker(marker):
            log_progress(6, "Extract MCP tools & wrap in MCP server (test & bugfix)", "skip")
            self.step_status['step6'] = 'skipped'
            return

        log_progress(6, "Extract MCP tools & wrap in MCP server (test & bugfix)", "start")

        # Read prompt
        prompt_file = self.prompts_dir / "step6_wrap_mcp_prompt.md"
        if not prompt_file.exists():
            logger.warning(f"  ⚠️ Prompt file not found: {prompt_file}")
            logger.warning("  You'll need to run this step manually or create the prompt file")
            self.step_status['step6'] = 'failed'
            return

        with open(prompt_file, 'r') as f:
            prompt_content = f.read()

        # Replace placeholders
        prompt_content = prompt_content.replace('${repo_name}', self.repo_name)

        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir, self.api_key):
            create_marker(marker)
            log_progress(6, "Extract MCP tools & wrap in MCP server (test & bugfix)", "complete")
            self.step_status['step6'] = 'executed'
        else:
            self.step_status['step6'] = 'failed'

    # ========================================================================
    # Step 7: Test Claude and Gemini integration (bugfix if needed)
    # ========================================================================
    def step7_test_integration(self):
        """Step 7: Test Claude and Gemini integration (bugfix if needed)"""
        marker = self._get_marker("07_test_integration")
        output_file = self.mcp_dir / "claude_outputs" / "step7_output.json"

        if check_marker(marker):
            log_progress(7, "Test Claude and Gemini integration (bugfix if needed)", "skip")
            self.step_status['step7'] = 'skipped'
            return

        log_progress(7, "Test Claude and Gemini integration (bugfix if needed)", "start")

        # Check if MCP server file exists (try multiple possible locations)
        server_py = self.mcp_dir / "src" / "server.py"
        legacy_tool_py = self.mcp_dir / "src" / f"{self.repo_name}_mcp.py"

        if server_py.exists():
            mcp_server_file = server_py
        elif legacy_tool_py.exists():
            mcp_server_file = legacy_tool_py
        else:
            logger.warning(f"  ⚠️ MCP server file not found. Checked:")
            logger.warning(f"     - {server_py}")
            logger.warning(f"     - {legacy_tool_py}")
            logger.warning("  Make sure Step 6 completed successfully")
            self.step_status['step7'] = 'failed'
            return

        # Read prompt
        prompt_file = self.prompts_dir / "step7_test_integration_prompt.md"
        if not prompt_file.exists():
            logger.warning(f"  ⚠️ Prompt file not found: {prompt_file}")
            logger.warning("  You'll need to run this step manually or create the prompt file")
            self.step_status['step7'] = 'failed'
            return

        with open(prompt_file, 'r') as f:
            prompt_content = f.read()

        # Replace placeholders
        prompt_content = prompt_content.replace('${repo_name}', self.repo_name)
        prompt_content = prompt_content.replace('${api_key}', self.api_key or '')
        prompt_content = prompt_content.replace('${server_name}', self.repo_name)

        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir, self.api_key):
            create_marker(marker)
            log_progress(7, "Test Claude and Gemini integration (bugfix if needed)", "complete")
            self.step_status['step7'] = 'executed'
        else:
            self.step_status['step7'] = 'failed'

    # ========================================================================
    # Step 8: Create comprehensive README documentation
    # ========================================================================
    def step8_create_readme(self):
        """Step 8: Create comprehensive README documentation"""
        marker = self._get_marker("08_create_readme")
        output_file = self.mcp_dir / "claude_outputs" / "step8_output.json"

        if check_marker(marker):
            log_progress(8, "Create comprehensive README documentation", "skip")
            self.step_status['step8'] = 'skipped'
            return

        log_progress(8, "Create comprehensive README documentation", "start")

        # Read prompt
        prompt_file = self.prompts_dir / "step8_create_readme_prompt.md"
        if not prompt_file.exists():
            logger.warning(f"  ⚠️ Prompt file not found: {prompt_file}")
            logger.warning("  You'll need to run this step manually or create the prompt file")
            self.step_status['step8'] = 'failed'
            return

        with open(prompt_file, 'r') as f:
            prompt_content = f.read()

        # Replace placeholders
        prompt_content = prompt_content.replace('${repo_name}', self.repo_name)
        prompt_content = prompt_content.replace('${project_name}', self.repo_name)
        prompt_content = prompt_content.replace('${mcp_directory}', str(self.mcp_dir))

        # Run Claude
        if run_claude_with_streaming(prompt_content, output_file, self.mcp_dir, self.api_key):
            create_marker(marker)
            log_progress(8, "Create comprehensive README documentation", "complete")
            self.step_status['step8'] = 'executed'

            # Show success message
            readme_path = self.mcp_dir / "README.md"
            if readme_path.exists():
                logger.info(f"\n  📄 README created: {readme_path}")
        else:
            self.step_status['step8'] = 'failed'

    def print_summary(self):
        """Print final pipeline summary"""
        logger.info("\n" + "="*60)
        logger.info("🎉 Pipeline Execution Summary")
        logger.info("="*60)

        step_descriptions = {
            'step1': '1. Setup project environment & directories',
            'step2': '2. Clone GitHub repository',
            'step3': '3. Setup conda env & scan use cases',
            'step4': '4. Execute common use cases',
            'step5': '5. Write scripts for use case functions',
            'step6': '6. Extract MCP tools & wrap in server',
            'step7': '7. Test Claude & Gemini integration',
            'step8': '8. Create comprehensive README'
        }

        for key, desc in step_descriptions.items():
            status = self.step_status.get(key, 'not run')
            emoji = {
                'executed': '✅',
                'skipped': '⏭️',
                'failed': '❌',
                'not run': '⚪'
            }.get(status, '⚪')

            logger.info(f"{emoji} {desc}: {status}")

        logger.info("="*60)

        # Show next steps
        if self.step_status.get('step8') in ['executed', 'skipped']:
            # Determine MCP server file path
            server_py = self.mcp_dir / "src" / "server.py"
            legacy_tool_py = self.mcp_dir / "src" / f"{self.repo_name}_mcp.py"
            mcp_file = server_py if server_py.exists() else legacy_tool_py

            logger.info("\n📋 Next Steps:")
            logger.info("  - Your MCP server has been created and documented")
            logger.info(f"  - README: {self.mcp_dir}/README.md")
            logger.info(f"  - MCP file: {mcp_file}")
            logger.info(f"  - Install with: claude mcp add {self.repo_name} -- $(pwd)/env/bin/python {mcp_file}")
            logger.info("  - Then run 'claude' in terminal to use it")

    def run_all(self):
        """Run the complete pipeline"""
        try:
            # Clear markers if rerun_from_step is set
            if self.rerun_from_step > 0:
                self._clear_markers_from_step(self.rerun_from_step)

            # Step 1: Setup project environment and prepare working directories
            self.step1_setup_project()
            logger.info(f"\n📁 MCP directory: {self.mcp_dir}\n")

            # Step 2: Clone GitHub repository
            self.step2_clone_repo()
            logger.info(f"\n📦 Repository: {self.repo_name}\n")

            # Step 3: Setup conda environment & scan common use cases
            self.step3_setup_env_and_scan()
            logger.info(f"\n⚙️  Conda environment setup & use cases scanned\n")

            # Step 4: Execute the common use cases in repository
            self.step4_execute_use_cases()
            logger.info(f"\n🔄 Common use cases executed\n")

            # Step 5: Write script for functions to execute common use cases
            self.step5_write_scripts()
            logger.info(f"\n📝 Scripts written for use case functions\n")

            # Step 6: Extract MCP tools from use case scripts and wrap in MCP server
            self.step6_extract_and_wrap_mcp()
            logger.info(f"\n🛠️  MCP tools extracted and wrapped\n")

            # Step 7: Test Claude and Gemini integration
            self.step7_test_integration()
            logger.info(f"\n🧪 Integration testing complete\n")

            # Step 8: Create comprehensive README documentation
            self.step8_create_readme()
            logger.info(f"\n📄 README documentation created\n")

            # Print summary
            self.print_summary()

        except Exception as e:
            logger.error(f"\n❌ Pipeline failed with error: {e}")
            self.print_summary()
            raise

    def get_created_mcp_info(self) -> dict:
        """
        Get information about the created MCP.

        Returns:
            Dictionary with MCP information including name, path, server file, etc.
        """
        server_py = self.mcp_dir / "src" / "server.py"
        legacy_tool_py = self.mcp_dir / "src" / f"{self.repo_name}_mcp.py"

        mcp_file = server_py if server_py.exists() else legacy_tool_py

        return {
            'name': self.repo_name,
            'mcp_dir': str(self.mcp_dir),
            'repo_dir': str(self.mcp_dir / "repo" / self.repo_name),
            'server_file': str(mcp_file) if mcp_file.exists() else None,
            'readme': str(self.mcp_dir / "README.md"),
            'source_url': self.github_url or str(self.local_repo_path),
            'step_status': self.step_status.copy()
        }
