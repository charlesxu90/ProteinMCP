# MCP Debugging & Creation Skills Guide

## Quick Reference

This guide explains how to use the new **mcp_docker_debug** and **mcp_creation_validator** workflow skills to create and maintain MCPs with reliable Docker builds.

## Two New Skills Available

### 1. **MCP Docker Build Debugger** (`mcp_docker_debug`)
**Purpose:** Debug and fix Docker build failures
**When to use:** When GitHub Actions builds fail or local Docker builds error

**Key capabilities:**
- Retrieves GitHub Actions logs
- Identifies root causes of errors
- Suggests and implements fixes
- Monitors builds until they pass
- Validates solutions

**Common issues it helps fix:**
- Permission denied errors
- Missing system dependencies
- C compilation failures (gcc not found)
- PyTorch version conflicts
- Git clone timeouts
- Missing files in build context

### 2. **MCP Creation & Docker Build Validator** (`mcp_creation_validator`)
**Purpose:** Create new MCPs with validated Docker builds
**When to use:** Setting up a new MCP or adding Docker support to existing tools

**Key capabilities:**
- Complete setup checklist
- Dockerfile patterns and templates
- GitHub Actions workflow setup
- Local testing procedures
- Validation checklist
- Registration with ProteinMCP

---

## Workflow 1: Creating a New MCP from Scratch

### Step-by-Step Process

#### 1. Gather Repository Information
```
Use: mcp_creation_validator skill
Ask: "Help me create a new MCP for {TOOL_NAME}"

Provide:
- GitHub repository URL
- What the tool does
- Key dependencies
- Required system packages
- GPU requirements (if any)
```

#### 2. Set Up Repository Structure
```
The skill will guide you through:
- Creating proper directory structure
- Setting up git repository
- Creating .gitignore
- Making initial commit

Follow the provided checklist step-by-step
```

#### 3. Create Dockerfile
```
Use: mcp_creation_validator skill
Ask: "Create the Dockerfile for this MCP"

It will help with:
- Choosing the right base image
- Adding system dependencies
- Cloning the external repository with retry logic
- Installing Python dependencies
- Fixing file permissions
- Setting up environment

Key patterns provided:
- Repository cloning with 3x retry
- Dependency filtering (especially PyTorch)
- Permission fixes with chmod
- Working directory setup
```

#### 4. Test Locally
```
Use: mcp_creation_validator skill
Ask: "Help me test the Dockerfile locally"

It will guide:
- Building the Docker image
- Running with different flags (--user, --gpus)
- Testing the MCP server
- Verifying all dependencies work

Troubleshooting:
- If errors occur → use mcp_docker_debug skill
```

#### 5. Set Up GitHub Actions
```
Use: mcp_creation_validator skill
Ask: "Set up GitHub Actions for Docker builds"

It provides:
- Complete workflow template
- Caching configuration
- Registry push setup
- Triggers (push, PR, manual)
```

#### 6. Trigger and Monitor Build
```
1. Commit and push to main branch
2. Use mcp_docker_debug skill to monitor:
   "Monitor the GitHub Actions build for {MCP_NAME}"
3. It will:
   - Check build status
   - Watch for completion
   - Alert you to success or failure
```

#### 7. Final Validation
```
Use: mcp_creation_validator skill
Ask: "Validate that the MCP is ready for use"

It will verify:
- Build success
- Image push to registry
- Can be registered with Claude Code
- All documentation is complete
```

---

## Workflow 2: Fixing a Failed Docker Build

### Step-by-Step Debugging Process

#### 1. Get Error Logs
```
Use: mcp_docker_debug skill
Ask: "Debug the failed Docker build for {MCP_NAME}"

The skill will:
- List recent GitHub Actions builds
- Find the failed one
- Retrieve detailed error logs
- Extract the actual error message
```

#### 2. Analyze Root Cause
```
The skill guides you through categorizing the error:

Is it a:
□ Permission error (Permission denied)
□ Missing dependency (not found, No such file)
□ Compilation error (gcc failed, build error)
□ Network timeout (connection refused, timeout)
□ Version conflict (version mismatch)
□ Other

Determine the root cause and solution category
```

#### 3. Implement Fix
```
The skill provides specific fixes for each category:

Example fixes:
- Permission: Add chmod -R a+r after COPY
- Missing tool: Add to apt-get install
- Compilation: Add build-essential
- Timeout: Add retry logic to git clone
- Version conflict: Filter from requirements.txt

It helps you:
- Edit the Dockerfile correctly
- Explain why the fix works
- Ensure no side effects
```

#### 4. Commit and Push
```
The skill guides you through:
1. Staging the Dockerfile changes
2. Writing a descriptive commit message
3. Pushing to remote repository

Commit message should explain:
- What the issue was
- Why it occurred
- How the fix resolves it
```

#### 5. Monitor New Build
```
The skill monitors the GitHub Actions build:
- Checks for new build triggered by push
- Polls status every 10-30 seconds
- Alerts when build completes
- Tells you if it succeeded or failed

If it failed again:
- Repeat from step 2 with new error
- Use deeper analysis if pattern unclear
```

#### 6. Validate Solution
```
Once build succeeds:
- Verify image was pushed to registry
- Confirm no new issues were introduced
- Document the fix for future reference
- Check if fix applies to other MCPs
```

---

## Real-World Example: Creating ligandmpnn_mcp

Here's how we used these skills to create and debug ligandmpnn_mcp:

### Phase 1: Initial Creation
```
Step 1: Gather info
- Repository: https://github.com/dauparas/LigandMPNN
- Base image: pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime
- Dependencies: numpy, scipy, networkx, ProDy, etc.

Step 2: Create Dockerfile
- Add build-essential early
- Clone repo with retry logic
- Install dependencies

Step 3: Test locally
- docker build -t ligandmpnn_mcp:test .
- docker run --rm ligandmpnn_mcp:test python -c "import torch"
```

### Phase 2: GitHub Actions First Failure
```
Build failed with: "pip install -r requirements.txt failed"

Using mcp_docker_debug:
1. Retrieved logs
2. Found: PyTorch 2.2.1 vs 2.2.0 conflict
3. Fix: Filter torch from requirements
4. Commit: 0a91b0b
5. Resubmitted
```

### Phase 3: Second Build Failure
```
New error: "command 'gcc' failed: No such file or directory"

Using mcp_docker_debug:
1. Retrieved new logs
2. Found: ProDy needs C compiler
3. Fix: Add build-essential to apt
4. Commit: f2d366e
5. Build succeeded! ✅
```

### Phase 4: Validation
```
Using mcp_creation_validator:
1. ✅ Image pushed to ghcr.io
2. ✅ No new issues introduced
3. ✅ Registered with Claude Code
4. ✅ Ready for use
```

**Total time: ~2 hours** (including build times)

---

## Integration with ProteinMCP

After creating/fixing an MCP:

### 1. Register with Claude Code
```bash
claude mcp add {mcp_name} -- \
  docker run -i --rm --gpus all --ipc=host \
  -v {ABSOLUTE_PATH}:{ABSOLUTE_PATH} \
  ghcr.io/{owner}/{mcp_name}:latest
```

### 2. Add to mcps.yaml
```yaml
{mcp_name}:
  runtime: docker
  image: ghcr.io/{owner}/{mcp_name}:latest
  docker_cmd: docker run -i --rm --gpus all --ipc=host ...
```

### 3. Update Fitness Modeling Skill
```
If the MCP is used in fitness_modeling:
- Add to required_mcps in skill/configs.yaml
- Include in fitness_modeling.md prompts
```

### 4. Update Documentation
```
- Add to tool-mcps/README.md
- Create/update MCP-specific README
- Add to main ProteinMCP README
```

---

## Skill Usage Patterns

### Pattern 1: Create from Scratch
```
1. Use mcp_creation_validator
   "Create new MCP for {TOOL}"
2. Follow the checklist
3. Use mcp_docker_debug if builds fail
4. Return to mcp_creation_validator for final validation
```

### Pattern 2: Quick Fix
```
1. Use mcp_docker_debug
   "Fix failed build for {MCP}"
2. Implement the suggested fix
3. Commit and push
4. Monitor new build
```

### Pattern 3: Pre-Launch Check
```
1. Use mcp_creation_validator
   "Validate {MCP} is ready for release"
2. Go through validation checklist
3. Use mcp_docker_debug if any issues
4. Document and publish
```

### Pattern 4: Apply Fix to Similar MCPs
```
1. Note the fix from one MCP
2. Use mcp_creation_validator to identify similar MCPs
3. Apply same pattern to others
4. Test each with mcp_docker_debug
```

---

## Common Questions

### Q: How long does it take to create an MCP?
**A:**
- With pre-existing Dockerfile: 30-60 minutes
- From scratch: 1-3 hours
- Includes: setup, testing, builds, troubleshooting

### Q: What if my MCP uses a different base image?
**A:**
The skills are generic:
- Replace base image in provided examples
- Same patterns apply (permissions, dependencies, retries)
- Build tools vary by base image (apt for Debian, apk for Alpine)

### Q: How do I know if my build succeeded?
**A:**
Use mcp_docker_debug to:
- Check GitHub Actions status: `gh run list --limit 1 --json status,conclusion`
- Should show: `"conclusion":"success"`

### Q: Can I use these skills for non-Docker MCPs?
**A:**
These are Docker-specific. For Python MCPs:
- Use quick_setup.sh approach instead
- Manually create venv and install dependencies
- See mcp_creation_validator for adaptation tips

### Q: What if I need to update an existing MCP's Docker?
**A:**
1. Use mcp_docker_debug to identify issues
2. Use mcp_creation_validator patterns for fixes
3. Test thoroughly before pushing
4. Update both Dockerfile and documentation

### Q: How do I handle proprietary tools/binaries?
**A:**
Patterns provided for:
- Downloading from official sources (see NetMHC hybrid approach)
- GitHub Actions caching
- License attribution
- Error handling with helpful messages

---

## Checklist Before Using Skills

### Before Creating an MCP
- [ ] Have the tool's GitHub repository URL
- [ ] Understand what the tool does
- [ ] Know key dependencies and system requirements
- [ ] Know if GPU support is needed
- [ ] Have Docker installed locally for testing

### Before Debugging a Build
- [ ] Access to GitHub Actions (via `gh` CLI)
- [ ] Write access to the MCP repository
- [ ] Understanding of the error message (or willing to learn)
- [ ] Local Docker installed (optional but helpful)

### Before Final Validation
- [ ] Build is passing in GitHub Actions
- [ ] Image is pushed to registry
- [ ] Can register with Claude Code
- [ ] Documentation is updated

---

## Key Takeaways

1. **Use mcp_docker_debug** for troubleshooting
   - When builds fail
   - To understand errors
   - To implement fixes
   - To monitor progress

2. **Use mcp_creation_validator** for creation
   - When starting new MCPs
   - For best practices and patterns
   - For validation before release
   - For documentation

3. **Iterate between them**
   - Create → Test → Debug → Validate
   - Quick feedback loops
   - Systematic approach

4. **Learn the patterns**
   - Permission fixes
   - Dependency management
   - Retry logic
   - GitHub Actions caching
   - Apply to new situations

5. **Document your process**
   - Why you made changes
   - What issues you fixed
   - Patterns that work
   - Edge cases you found

---

## Next Steps

1. **Install the skills**
   ```bash
   pskill install mcp_docker_debug
   pskill install mcp_creation_validator
   ```

2. **Create your first MCP**
   ```
   /mcp_creation_validator
   "Create new MCP for {TOOL_NAME}"
   ```

3. **Debug if needed**
   ```
   /mcp_docker_debug
   "Debug the Docker build for {MCP_NAME}"
   ```

4. **Share and improve**
   - Use the skills on new MCPs
   - Document new patterns
   - Contribute improvements
   - Help other teams create MCPs

---

## Resources

- **Skills location**: `workflow-skills/mcp_docker_debug.md` and `mcp_creation_validator.md`
- **Configuration**: `src/skill/configs.yaml`
- **Docker docs**: https://docs.docker.com
- **GitHub Actions**: https://docs.github.com/en/actions
- **FastMCP**: https://github.com/jlowin/FastMCP
- **ProteinMCP CLAUDE.md**: Full project architecture

