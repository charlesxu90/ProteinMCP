# MCP Development Skills

This directory contains workflow skills for **developing and debugging MCP (Model Context Protocol) servers**, distinct from protein design workflows.

## Skills

### 1. MCP Docker Build Debugger (`mcp_docker_debug`)
**File:** `mcp_docker_debug.md`

Debug and fix Docker build failures in MCP repositories.

**When to use:**
- GitHub Actions Docker builds fail
- Local Docker builds error
- Need to understand build errors
- Implementing fixes systematically

**Key capabilities:**
- Retrieve GitHub Actions build logs
- Identify root causes of errors
- Suggest and implement fixes
- Monitor builds until completion
- Validate solutions

**Common issues it helps fix:**
- Permission denied errors
- Missing system dependencies
- C compilation failures
- PyTorch version conflicts
- Git clone timeouts
- Missing files in build context

---

### 2. MCP Creation & Docker Build Validator (`mcp_creation_validator`)
**File:** `mcp_creation_validator.md`

Create new MCPs with validated Docker builds.

**When to use:**
- Creating a new MCP from scratch
- Adding Docker support to existing tools
- Setting up GitHub Actions workflows
- Pre-launch validation
- Ensuring build consistency

**Key capabilities:**
- Complete setup checklist (6 phases)
- Dockerfile creation with best practices
- GitHub Actions workflow templates
- Local testing procedures
- Final validation before release
- Integration with ProteinMCP

**What it covers:**
- Repository structure setup
- Base image selection
- System dependencies
- Dockerfile patterns and templates
- GitHub Actions configuration
- Local Docker testing
- MCP registration

---

## Usage

### Installation
```bash
pskill install mcp_docker_debug
pskill install mcp_creation_validator
```

### Using the Skills

**For debugging:**
```
/mcp_docker_debug
"Debug the Docker build failure for {MCP_NAME}"
```

**For creating new MCPs:**
```
/mcp_creation_validator
"Create new MCP for {TOOL_NAME}"
```

---

## Documentation

For comprehensive guide covering:
- When to use each skill
- Complete workflows
- Real-world examples
- Integration with ProteinMCP
- Common patterns
- FAQs and troubleshooting

See: `../MCP_SKILLS_GUIDE.md`

---

## Architecture

```
ProteinMCP/
├── workflow-skills/          (Protein design workflows)
│   ├── fitness_modeling.md
│   ├── binder_design.md
│   └── nanobody_design.md
│
├── mcp-skills/               (MCP development utilities)
│   ├── README.md             (this file)
│   ├── mcp_docker_debug.md
│   └── mcp_creation_validator.md
│
└── MCP_SKILLS_GUIDE.md       (Guide for using MCP skills)
```

---

## Key Patterns

Both skills document and provide:

### Docker Patterns
- Repository cloning with 3x retry logic
- Dependency filtering (PyTorch, etc.)
- Permission fixes for non-root users
- Build-essential for C extensions
- GitHub Actions caching strategy

### Common Fixes
| Issue | Solution |
|-------|----------|
| Permission denied | `chmod -R a+r` after COPY |
| gcc not found | Add `build-essential` |
| PyTorch conflict | Filter from requirements.txt |
| Git timeout | Add 3x retry logic |
| Missing files | Download or cache |

---

## Configuration

Skills are registered in: `src/skill/configs.yaml`

```yaml
mcp_docker_debug:
  description: Debug and fix Docker build failures...
  file_path: mcp-skills/mcp_docker_debug.md
  required_mcps: []

mcp_creation_validator:
  description: Create new MCPs with validated Docker builds...
  file_path: mcp-skills/mcp_creation_validator.md
  required_mcps: []
```

---

## Resources

- **Full Usage Guide:** `../MCP_SKILLS_GUIDE.md`
- **Docker Documentation:** https://docs.docker.com
- **GitHub Actions:** https://docs.github.com/en/actions
- **FastMCP:** https://github.com/jlowin/FastMCP
- **ProteinMCP Architecture:** `../CLAUDE.md`

---

## Related Directories

- **Protein Design Workflows:** `../workflow-skills/`
- **MCP Repositories:** `../tool-mcps/`
- **Project Configuration:** `../src/`
- **GitHub Workflows:** `../.github/workflows/`

