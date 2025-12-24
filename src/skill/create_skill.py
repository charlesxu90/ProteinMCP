#!/usr/bin/env python3
"""
Skill Creation Tool

This tool helps create workflow skills by:
1. Recording interactive steps during MCP tool testing
2. Generating skill markdown files from steps
3. Updating skill configurations

Usage:
    pskill-create init <skill_name>          # Initialize a new skill
    pskill-create add-step <skill_name>      # Add a step interactively
    pskill-create list-steps <skill_name>    # List recorded steps
    pskill-create generate <skill_name>      # Generate skill from steps
    pskill-create from-steps <steps_file>    # Generate skill from steps file
"""

import argparse
import re
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml


# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
WORKFLOW_SKILLS_DIR = PROJECT_ROOT / "workflow-skills"
SKILL_CONFIG_PATH = Path(__file__).parent / "configs.yaml"


class SkillCreator:
    """Creates workflow skills from interactive steps or steps files."""

    def __init__(self, skill_name: str):
        self.skill_name = skill_name
        self.skill_dir = WORKFLOW_SKILLS_DIR
        self.steps_file = self.skill_dir / f"{skill_name}_steps.md"
        self.skill_file = self.skill_dir / f"{skill_name}.md"

    def init_skill(
        self,
        description: str = "",
        required_mcps: Optional[List[str]] = None
    ) -> bool:
        """Initialize a new skill with a steps file template."""
        if self.steps_file.exists():
            print(f"Warning: Steps file already exists: {self.steps_file}")
            response = input("Overwrite? (y/N): ").strip().lower()
            if response != 'y':
                print("Aborted.")
                return False

        template = self._generate_steps_template(description, required_mcps or [])
        self.steps_file.write_text(template)
        print(f"Created steps file: {self.steps_file}")
        print(f"\nNext steps:")
        print(f"  1. Test your MCP tools interactively")
        print(f"  2. Add steps: pskill-create add-step {self.skill_name}")
        print(f"  3. Or edit the steps file directly: {self.steps_file}")
        print(f"  4. Generate skill: pskill-create generate {self.skill_name}")
        return True

    def _generate_steps_template(
        self,
        description: str,
        required_mcps: List[str]
    ) -> str:
        """Generate a template for the steps file."""
        mcps_str = ", ".join(required_mcps) if required_mcps else "mcp1, mcp2"
        return f"""# {self.skill_name.replace('_', ' ').title()} Skill Steps

## Metadata
- **Description**: {description or "A workflow skill for ..."}
- **Required MCPs**: {mcps_str}
- **Created**: {datetime.now().strftime('%Y-%m-%d')}

---

## Configuration Parameters

```yaml
# Required Inputs
PARAM1: "value1"              # Description of param1
PARAM2: "@examples/path"      # Description of param2

# Output Settings
OUTPUT_DIR: "@results/{self.skill_name}"  # Output directory
```

---

## Steps

### Step 1: [Step Title]

**Description**: Brief description of what this step does.

**Prompt:**
> Your prompt here that will be copied to the conversation.
> Use {{PARAM1}} for parameter placeholders.

**Implementation Notes:**
- Note 1
- Note 2

**Expected Output:**
- Output file 1
- Output file 2

---

### Step 2: [Step Title]

**Description**: Brief description of what this step does.

**Prompt:**
> Your prompt here for step 2.

**Implementation Notes:**
- Use `mcp__server__tool` with parameters...

---

## Troubleshooting

### Common Issues

1. **Issue 1**: Description and solution

2. **Issue 2**: Description and solution

---

## References

- Reference 1: URL
- Reference 2: URL
"""

    def add_step(
        self,
        title: str,
        prompt: str,
        description: str = "",
        implementation_notes: Optional[List[str]] = None,
        expected_output: Optional[List[str]] = None
    ) -> bool:
        """Add a step to the steps file."""
        if not self.steps_file.exists():
            print(f"Error: Steps file not found: {self.steps_file}")
            print(f"Run: pskill-create init {self.skill_name}")
            return False

        content = self.steps_file.read_text()

        # Find the last step number
        step_matches = re.findall(r"### Step (\d+):", content)
        next_step = int(step_matches[-1]) + 1 if step_matches else 1

        # Build step content
        step_content = f"\n\n---\n\n### Step {next_step}: {title}\n\n"
        if description:
            step_content += f"**Description**: {description}\n\n"
        step_content += "**Prompt:**\n"
        for line in prompt.strip().split('\n'):
            step_content += f"> {line}\n"

        if implementation_notes:
            step_content += "\n**Implementation Notes:**\n"
            for note in implementation_notes:
                step_content += f"- {note}\n"

        if expected_output:
            step_content += "\n**Expected Output:**\n"
            for output in expected_output:
                step_content += f"- {output}\n"

        # Insert before Troubleshooting section if it exists
        if "## Troubleshooting" in content:
            content = content.replace(
                "## Troubleshooting",
                step_content + "\n## Troubleshooting"
            )
        else:
            content += step_content

        self.steps_file.write_text(content)
        print(f"Added Step {next_step}: {title}")
        return True

    def list_steps(self) -> List[Dict]:
        """List all steps in the steps file."""
        if not self.steps_file.exists():
            print(f"Error: Steps file not found: {self.steps_file}")
            return []

        content = self.steps_file.read_text()
        steps = []

        # Parse steps
        step_pattern = r"### Step (\d+): (.+?)(?=\n|$)"
        for match in re.finditer(step_pattern, content):
            step_num = int(match.group(1))
            title = match.group(2).strip()
            steps.append({"number": step_num, "title": title})

        return steps

    def generate_skill(
        self,
        description: Optional[str] = None,
        required_mcps: Optional[List[str]] = None
    ) -> bool:
        """Generate a skill file from the steps file."""
        if not self.steps_file.exists():
            print(f"Error: Steps file not found: {self.steps_file}")
            return False

        steps_content = self.steps_file.read_text()

        # Extract metadata from steps file
        desc = description
        mcps = required_mcps

        if not desc:
            desc_match = re.search(
                r"\*\*Description\*\*:\s*(.+?)(?:\n|$)",
                steps_content
            )
            if desc_match:
                desc = desc_match.group(1).strip()

        if not mcps:
            mcps_match = re.search(
                r"\*\*Required MCPs\*\*:\s*(.+?)(?:\n|$)",
                steps_content
            )
            if mcps_match:
                mcps_str = mcps_match.group(1).strip()
                mcps = [m.strip() for m in mcps_str.split(",")]

        # Generate skill content
        skill_content = self._transform_steps_to_skill(
            steps_content,
            desc or "A workflow skill",
            mcps or []
        )

        self.skill_file.write_text(skill_content)
        print(f"Generated skill file: {self.skill_file}")

        # Update configs.yaml
        if mcps:
            self._update_config(desc or "A workflow skill", mcps)

        return True

    def _transform_steps_to_skill(
        self,
        steps_content: str,
        description: str,
        required_mcps: List[str]
    ) -> str:
        """Transform steps file content to skill file format."""
        # Extract title from steps file
        title_match = re.search(r"^# (.+?)$", steps_content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).replace(" Steps", "")
            if not title.endswith("Skill"):
                title = f"{title} Skill"
        else:
            title = f"{self.skill_name.replace('_', ' ').title()} Skill"

        # Build skill header
        skill_content = f"# {title}\n\n{description}\n\n---\n\n"

        # Add prerequisites section
        skill_content += "## Prerequisites\n\n"
        skill_content += "Before running this workflow, install the skill and all required MCPs:\n\n"
        skill_content += f"```bash\npskill install {self.skill_name}\n```\n\n"
        skill_content += "This will install the following MCP servers:\n"
        for mcp in required_mcps:
            skill_content += f"- `{mcp}` - {mcp.replace('_', ' ').title()}\n"
        skill_content += "\n**Verify MCPs are installed:**\n```bash\npmcp status\n```\n\n---\n\n"

        # Copy Configuration Parameters section if present
        config_match = re.search(
            r"## Configuration Parameters\n\n(.*?)(?=\n---|\n## Steps)",
            steps_content,
            re.DOTALL
        )
        if config_match:
            skill_content += "## Configuration Parameters\n\n"
            skill_content += config_match.group(1).strip()
            skill_content += "\n\n---\n\n"

        # Copy steps
        steps_section = re.search(
            r"## Steps\n\n(.*?)(?=\n## Troubleshooting|\n## References|$)",
            steps_content,
            re.DOTALL
        )
        if steps_section:
            # Rename ### Step N to ## Step N for main sections
            steps_text = steps_section.group(1)
            steps_text = re.sub(r"### Step (\d+):", r"## Step \1:", steps_text)
            skill_content += steps_text

        # Add troubleshooting if present
        trouble_match = re.search(
            r"## Troubleshooting\n\n(.*?)(?=\n## References|$)",
            steps_content,
            re.DOTALL
        )
        if trouble_match:
            skill_content += "\n---\n\n## Troubleshooting\n\n"
            skill_content += trouble_match.group(1).strip()

        # Add references if present
        ref_match = re.search(
            r"## References\n\n(.*)$",
            steps_content,
            re.DOTALL
        )
        if ref_match:
            skill_content += "\n\n---\n\n## References\n\n"
            skill_content += ref_match.group(1).strip()

        # Add cleanup section
        skill_content += f"\n\n---\n\n## Cleanup\n\n"
        skill_content += f"When you're done with the workflow, uninstall the skill and all its MCPs:\n\n"
        skill_content += f"```bash\npskill uninstall {self.skill_name}\n```\n"

        return skill_content

    def _update_config(self, description: str, required_mcps: List[str]) -> bool:
        """Update configs.yaml with the new skill."""
        try:
            if SKILL_CONFIG_PATH.exists():
                with open(SKILL_CONFIG_PATH, 'r') as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {}

            if 'skills' not in config:
                config['skills'] = {}

            # Add or update skill entry
            config['skills'][self.skill_name] = {
                'description': description,
                'file_path': str(self.skill_file.relative_to(PROJECT_ROOT)),
                'required_mcps': required_mcps
            }

            with open(SKILL_CONFIG_PATH, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            print(f"Updated config: {SKILL_CONFIG_PATH}")
            return True
        except Exception as e:
            print(f"Warning: Failed to update config: {e}")
            return False

    @classmethod
    def from_steps_file(cls, steps_file: Path) -> Optional['SkillCreator']:
        """Create a SkillCreator from an existing steps file."""
        if not steps_file.exists():
            print(f"Error: Steps file not found: {steps_file}")
            return None

        # Derive skill name from filename
        skill_name = steps_file.stem
        if skill_name.endswith('_steps'):
            skill_name = skill_name[:-6]

        creator = cls(skill_name)
        creator.steps_file = steps_file
        return creator


def interactive_add_step(creator: SkillCreator):
    """Interactively add a step to the skill."""
    print(f"\n=== Adding Step to '{creator.skill_name}' ===\n")

    title = input("Step title: ").strip()
    if not title:
        print("Error: Title is required")
        return

    print("\nEnter the prompt (end with an empty line):")
    prompt_lines = []
    while True:
        line = input()
        if not line:
            break
        prompt_lines.append(line)
    prompt = '\n'.join(prompt_lines)

    if not prompt:
        print("Error: Prompt is required")
        return

    description = input("\nStep description (optional): ").strip()

    print("\nImplementation notes (one per line, empty to finish):")
    notes = []
    while True:
        note = input("  - ").strip()
        if not note:
            break
        notes.append(note)

    print("\nExpected outputs (one per line, empty to finish):")
    outputs = []
    while True:
        output = input("  - ").strip()
        if not output:
            break
        outputs.append(output)

    creator.add_step(
        title=title,
        prompt=prompt,
        description=description,
        implementation_notes=notes if notes else None,
        expected_output=outputs if outputs else None
    )


def main():
    """Main function to handle command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Skill Creation Tool for Claude Code",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent("""
Examples:
  # Initialize a new skill
  pskill-create init binder_design

  # Add a step interactively
  pskill-create add-step binder_design

  # List all steps
  pskill-create list-steps binder_design

  # Generate skill from steps
  pskill-create generate binder_design

  # Generate skill from an existing steps file
  pskill-create from-steps workflow-skills/my_steps.md

Workflow:
  1. pskill-create init <skill_name>
  2. Test MCP tools interactively in Claude Code
  3. pskill-create add-step <skill_name> (repeat for each step)
  4. pskill-create generate <skill_name>
  5. pskill install <skill_name>
""")
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new skill with a steps file template"
    )
    init_parser.add_argument("skill_name", help="Name of the skill")
    init_parser.add_argument(
        "--description", "-d",
        help="Skill description"
    )
    init_parser.add_argument(
        "--mcps", "-m",
        nargs="+",
        help="Required MCP servers"
    )

    # add-step command
    add_parser = subparsers.add_parser(
        "add-step",
        help="Add a step to the skill interactively"
    )
    add_parser.add_argument("skill_name", help="Name of the skill")
    add_parser.add_argument(
        "--title", "-t",
        help="Step title (interactive if not provided)"
    )
    add_parser.add_argument(
        "--prompt", "-p",
        help="Step prompt (interactive if not provided)"
    )

    # list-steps command
    list_parser = subparsers.add_parser(
        "list-steps",
        help="List all steps in the skill"
    )
    list_parser.add_argument("skill_name", help="Name of the skill")

    # generate command
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate skill file from steps"
    )
    gen_parser.add_argument("skill_name", help="Name of the skill")
    gen_parser.add_argument(
        "--description", "-d",
        help="Override description"
    )
    gen_parser.add_argument(
        "--mcps", "-m",
        nargs="+",
        help="Override required MCPs"
    )

    # from-steps command
    from_parser = subparsers.add_parser(
        "from-steps",
        help="Generate skill from an existing steps file"
    )
    from_parser.add_argument(
        "steps_file",
        help="Path to the steps file"
    )
    from_parser.add_argument(
        "--description", "-d",
        help="Override description"
    )
    from_parser.add_argument(
        "--mcps", "-m",
        nargs="+",
        help="Override required MCPs"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "init":
        creator = SkillCreator(args.skill_name)
        creator.init_skill(
            description=args.description or "",
            required_mcps=args.mcps
        )

    elif args.command == "add-step":
        creator = SkillCreator(args.skill_name)
        if args.title and args.prompt:
            creator.add_step(title=args.title, prompt=args.prompt)
        else:
            interactive_add_step(creator)

    elif args.command == "list-steps":
        creator = SkillCreator(args.skill_name)
        steps = creator.list_steps()
        if steps:
            print(f"\nSteps in '{args.skill_name}':")
            print("-" * 40)
            for step in steps:
                print(f"  Step {step['number']}: {step['title']}")
            print()
        else:
            print("No steps found.")

    elif args.command == "generate":
        creator = SkillCreator(args.skill_name)
        creator.generate_skill(
            description=args.description,
            required_mcps=args.mcps
        )

    elif args.command == "from-steps":
        steps_path = Path(args.steps_file)
        creator = SkillCreator.from_steps_file(steps_path)
        if creator:
            creator.generate_skill(
                description=args.description,
                required_mcps=args.mcps
            )


if __name__ == "__main__":
    main()
