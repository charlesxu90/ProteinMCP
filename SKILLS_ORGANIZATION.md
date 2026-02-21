# ProteinMCP Skills Organization

## Overview

Skills are organized into two distinct directories based on their purpose:

1. **workflow-skills/** - Protein design workflows
2. **mcp-skills/** - MCP development utilities

This separation clarifies the purpose of each skill and improves navigation for users.

---

## Directory Structure

```
ProteinMCP/
├── workflow-skills/                  ← Protein design workflows
│   ├── fitness_modeling.md
│   │   └── ESM, ProtTrans, PLMC, EV+OneHot model comparison
│   ├── binder_design.md
│   │   └── BindCraft-based binder design with GPU acceleration
│   ├── nanobody_design.md
│   │   └── BoltzGen-based nanobody CDR region design
│   └── [scripts, figures for protein workflows]
│
├── mcp-skills/                       ← MCP development utilities
│   ├── README.md                     ← Documentation for this directory
│   ├── mcp_docker_debug.md
│   │   └── Debug and fix Docker build failures
│   ├── mcp_creation_validator.md
│   │   └── Create new MCPs with validated Docker builds
│   └── [MCP development templates]
│
└── MCP_SKILLS_GUIDE.md               ← Guide for using MCP skills
```

---

## Workflow Skills (Protein Design)

### Purpose
Guide users through protein engineering workflows using available MCPs.

### Skills
| Skill | Purpose | Required MCPs |
|-------|---------|---------------|
| **fitness_modeling** | Build and compare protein fitness prediction models | msa_mcp, plmc_mcp, ev_onehot_mcp, esm_mcp, prottrans_mcp |
| **binder_design** | Design protein binders using BindCraft | bindcraft_mcp |
| **nanobody_design** | Design nanobody CDR regions using BoltzGen | boltzgen_mcp |

### Usage
```
/fitness_modeling
"I have a protein sequence and want to predict fitness..."

/binder_design
"Help me design a binder protein for my target..."

/nanobody_design
"Design a nanobody against this target protein..."
```

### Output
- Protein designs
- Fitness predictions
- Structure predictions
- Design metrics and visualizations

---

## MCP Skills (Development Utilities)

### Purpose
Help developers create, debug, and validate MCP Docker builds.

### Skills

#### 1. MCP Docker Build Debugger
**File:** `mcp_docker_debug.md`
**Purpose:** Debug and fix Docker build failures

**Use when:**
- GitHub Actions builds fail
- Local Docker builds error
- Need systematic error diagnosis
- Implementing fixes

**Helps fix:**
- Permission errors
- Missing dependencies
- C compilation failures
- Version conflicts
- Network timeouts

**Usage:**
```
/mcp_docker_debug
"Debug the Docker build failure for ligandmpnn_mcp"
```

#### 2. MCP Creation & Docker Build Validator
**File:** `mcp_creation_validator.md`
**Purpose:** Create new MCPs with validated Docker builds

**Use when:**
- Creating a new MCP
- Adding Docker support
- Setting up GitHub Actions
- Pre-launch validation
- Ensuring build consistency

**Provides:**
- 6-phase creation checklist
- Dockerfile patterns
- GitHub Actions templates
- Testing procedures
- Validation checklist

**Usage:**
```
/mcp_creation_validator
"Create new MCP for AlphaFold3 structure prediction"
```

### Not Tied to Specific MCPs
Unlike workflow skills, MCP skills have **no required MCPs** - they're utilities for developing MCPs.

---

## Configuration

Skills are registered in: `src/skill/configs.yaml`

### Protein Design Workflows
```yaml
skills:
  fitness_modeling:
    file_path: workflow-skills/fitness_modeling.md
    required_mcps:
      - msa_mcp
      - plmc_mcp
      - ev_onehot_mcp
      - esm_mcp
      - prottrans_mcp

  binder_design:
    file_path: workflow-skills/binder_design.md
    required_mcps:
      - bindcraft_mcp

  nanobody_design:
    file_path: workflow-skills/nanobody_design.md
    required_mcps:
      - boltzgen_mcp
```

### MCP Development Utilities
```yaml
  mcp_docker_debug:
    file_path: mcp-skills/mcp_docker_debug.md
    required_mcps: []  # No dependencies - utility skill

  mcp_creation_validator:
    file_path: mcp-skills/mcp_creation_validator.md
    required_mcps: []  # No dependencies - utility skill
```

---

## Installation

### Install All Skills
```bash
pskill install fitness_modeling
pskill install binder_design
pskill install nanobody_design
pskill install mcp_docker_debug
pskill install mcp_creation_validator
```

### Install Only Protein Design Workflows
```bash
pskill install fitness_modeling
pskill install binder_design
pskill install nanobody_design
```

### Install Only MCP Development Tools
```bash
pskill install mcp_docker_debug
pskill install mcp_creation_validator
```

---

## User Personas

### Protein Engineer
"I want to design proteins"
→ Use **workflow-skills**
- `/fitness_modeling` for fitness prediction
- `/binder_design` for binder design
- `/nanobody_design` for nanobodies

### MCP Developer
"I want to create/fix MCPs"
→ Use **mcp-skills**
- `/mcp_docker_debug` to debug build failures
- `/mcp_creation_validator` to create new MCPs

### Full Stack Developer
"I do both protein design and MCP development"
→ Install all skills from both directories

---

## Usage Examples

### Example 1: Design a Protein (Workflow)
```
User: "I want to predict fitness for my TEVp variant"
1. Use fitness_modeling workflow
2. Provides ESM embeddings, ProtTrans, PLMC fitness scores
3. Returns predictions and comparisons
4. Outputs design metrics and visualizations
```

### Example 2: Debug a Failed MCP Build (Development)
```
User: "My Docker build for alphafold3_mcp failed"
1. Use mcp_docker_debug skill
2. Retrieves GitHub Actions logs
3. Identifies root cause (e.g., gcc not found)
4. Implements fix (add build-essential)
5. Monitors new build
6. Confirms fix works ✅
```

### Example 3: Create New MCP (Development)
```
User: "I want to create an MCP for ESMFold"
1. Use mcp_creation_validator skill
2. Follow 6-phase checklist
3. Creates proper directory structure
4. Generates Dockerfile with best practices
5. Sets up GitHub Actions workflow
6. Tests locally
7. Validates in GitHub Actions
8. MCP ready for use ✅
```

---

## Directory Benefits

### For Users
- ✅ Clear understanding of what each skill does
- ✅ Easy to find the right skill for their task
- ✅ Obvious which skills do protein design vs. MCP development

### For Developers
- ✅ Organized code structure
- ✅ Easier to add new skills
- ✅ Clear conventions and patterns
- ✅ Better documentation organization

### For Maintenance
- ✅ Protein workflows separate from development tools
- ✅ Different update cycles
- ✅ Different user bases
- ✅ Different dependencies

---

## Adding New Skills

### New Protein Design Workflow
1. Create `workflow-skills/new_workflow.md`
2. Add to `src/skill/configs.yaml` under protein workflows
3. List required MCPs in config
4. Document in `workflow-skills/README.md`

### New MCP Development Tool
1. Create `mcp-skills/new_tool.md`
2. Add to `src/skill/configs.yaml` under MCP tools
3. Set `required_mcps: []` if utility skill
4. Document in `mcp-skills/README.md`

---

## Documentation

### Protein Design Workflows
- Individual skill files in `workflow-skills/`
- How-to guides for protein design
- Example inputs and outputs
- Troubleshooting protein workflows

### MCP Development Tools
- Individual skill files in `mcp-skills/`
- Comprehensive guide: `MCP_SKILLS_GUIDE.md`
- Docker debugging and creation patterns
- Real-world examples and solutions

---

## Related Files

| File | Purpose |
|------|---------|
| `src/skill/configs.yaml` | Skill registration and metadata |
| `workflow-skills/` | Protein design workflow skills |
| `mcp-skills/` | MCP development utility skills |
| `MCP_SKILLS_GUIDE.md` | Complete guide for MCP skills |
| `mcp-skills/README.md` | MCP skills directory documentation |

---

## Future Enhancements

Potential additions:

### Workflow Skills
- Enzyme engineering workflow
- Protein-protein interaction design
- Expression optimization

### MCP Skills
- MCP performance optimization
- MCP testing and validation
- MCP documentation generator

---

## Questions?

- **How do I use a skill?** → See `MCP_SKILLS_GUIDE.md`
- **How do I create an MCP?** → Use `/mcp_creation_validator`
- **How do I debug a build?** → Use `/mcp_docker_debug`
- **How do I design proteins?** → Use protein workflow skills
- **Where are skills stored?** → `workflow-skills/` and `mcp-skills/`

