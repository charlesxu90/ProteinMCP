# MCP Docker Build Debugger

## Overview
This skill helps debug and fix Docker build failures in MCP repositories. It provides a systematic approach to identifying root causes and implementing fixes based on common issues.

## Use Cases
- **Failed GitHub Actions Docker builds** - Diagnose build errors and implement fixes
- **Slow builds** - Optimize caching and dependencies
- **Permission issues** - Fix file permission and user execution problems
- **Dependency conflicts** - Resolve version conflicts and compilation errors
- **Network resilience** - Add retry logic to prevent timeout failures

## Workflow

### Step 1: Identify the MCP and Build Status

Start by getting information about the MCP repository:

```
I need to debug Docker build issues for the {MCP_NAME} repository.

Please:
1. Navigate to the MCP directory at the absolute path provided
2. List recent GitHub Actions builds using: gh run list --limit 5
3. Check the latest build status and conclusion
4. Identify which builds failed and which succeeded

Provide the build history and current status.
```

### Step 2: Retrieve and Analyze Build Logs

Once you've identified a failed build:

```
The {MCP_NAME} Docker build failed. Please:

1. Get the database ID of the latest failed build from GitHub Actions
2. Retrieve the full build logs using: gh run view {RUN_ID} --log
3. Search for error messages using grep patterns like:
   - "error:" and "ERROR:"
   - "failed" and "FAILED"
   - "exception" and "EXCEPTION"
4. Extract and summarize the actual error message

Show me the context around the error (5 lines before and after).
```

### Step 3: Diagnose the Root Cause

Analyze the error and determine the category:

```
Based on the error message: {ERROR_MESSAGE}

Please analyze and categorize this error:

1. **Error Type**: Is this a:
   - Permission/user execution issue (Permission denied)
   - Dependency conflict (version mismatch, package not found)
   - Missing system dependency (gcc, build tools, etc.)
   - Network issue (timeout, download failed, connection refused)
   - Compilation error (failed to build C extension)
   - Git clone failure (repository access, timeout)
   - Other (specify)

2. **Root Cause**: What's the underlying issue?

3. **Impact**: Does this affect just this MCP or is it a pattern?

4. **Solution Category**: Is the fix:
   - Dockerfile modification
   - Dependency filtering
   - Build tool installation
   - Retry logic addition
   - Permission fix
   - Other
```

### Step 4: Implement the Fix

Based on the diagnosis, implement the appropriate fix:

```
The root cause is: {ROOT_CAUSE}

The fix requires: {FIX_TYPE}

Please implement the fix by:
1. Reading the current Dockerfile
2. Identifying the exact location to make changes
3. Modifying the Dockerfile with the fix
4. Explaining what the change does and why it fixes the issue

For reference, here are common fixes:

**Permission Fix**:
Add after COPY directives:
  RUN chmod -R a+r /app/{directory}

**Missing Build Tools**:
Add to apt-get install:
  build-essential

**Dependency Filtering**:
Filter out problematic packages:
  grep -v -E "^(package1|package2)" requirements.txt | tr '\n' ' '

**Git Clone Retry Logic**:
Wrap git clone with retry:
  for attempt in 1 2 3; do
    git clone --depth 1 {url} {dir} && break
    if [ $attempt -lt 3 ]; then sleep 5; fi
  done

**System Dependency**:
Add to apt-get install:
  {missing_package}

**Symlink Resolution**:
Remove .resolve() from paths:
  Path(__file__).parent.parent (instead of .resolve())
```

### Step 5: Commit and Push the Fix

After implementing the fix:

```
The fix has been implemented. Please:

1. Stage the modified Dockerfile:
   git add Dockerfile

2. Create a descriptive commit message explaining:
   - What the issue was
   - Why it occurred
   - What the fix does
   - How it resolves the problem

3. Push to the remote repository:
   git push origin main

4. Provide the commit hash and confirmation that the push succeeded
```

### Step 6: Monitor the GitHub Actions Build

Monitor the new build triggered by your push:

```
The fix has been pushed. Please monitor the GitHub Actions build:

1. Check for a new build triggered by the commit:
   gh run list --limit 3 --json databaseId,status,conclusion,createdAt

2. If the new build is in_progress:
   - Wait for it to complete
   - Check periodically every 30 seconds
   - Look for the status to change from "in_progress" to "completed"

3. Once completed, check the conclusion:
   - "success" = Fix worked! ✅
   - "failure" = New error appeared, need further debugging

4. If it failed, retrieve the new error logs and return to Step 2
```

### Step 7: Verify the Fix

Once the build succeeds:

```
The GitHub Actions build succeeded! Please verify:

1. Confirm the build status shows "success"
2. Verify the image was pushed to the registry (if applicable)
3. Check that the fix doesn't introduce new issues:
   - Compare the before/after Dockerfile
   - Ensure no functionality was removed
   - Check that dependencies are still properly installed

4. Document the fix by:
   - Recording the commit hash
   - Noting the root cause and solution
   - Identifying if this pattern applies to other MCPs
```

## Common Docker Build Issues and Fixes

### 1. Permission Denied Errors
```
ERROR: Permission denied
SYMPTOM: Non-root user (--user flag) can't read/execute files
FIX: Add chmod after COPY directives
  COPY src/ ./src/
  RUN chmod -R a+r /app/src/
```

### 2. Missing System Dependencies
```
ERROR: gcc/git/wget not found, No such file or directory
SYMPTOM: System tool not installed in container
FIX: Add to apt-get install
  RUN apt-get update && apt-get install -y build-essential git wget
```

### 3. PyTorch Version Conflicts
```
ERROR: pip can't install/upgrade PyTorch in PyTorch base image
SYMPTOM: Base image has PyTorch, requirements.txt specifies different version
FIX: Filter out torch packages from requirements
  pip install $(grep -v -E "^(torch|torchaudio|torchvision)" requirements.txt)
```

### 4. C Compilation Errors
```
ERROR: error: command 'gcc' failed: No such file or directory
SYMPTOM: Package with C extensions needs compiler
FIX: Add build-essential
  build-essential provides gcc, g++, make, etc.
```

### 5. Git Clone Timeouts
```
ERROR: failed to solve: process failed
SYMPTOM: Network timeout downloading repository
FIX: Add retry logic with exponential backoff
  for attempt in 1 2 3; do
    git clone --depth 1 [url] && break
    [ $attempt -lt 3 ] && sleep 5
  done
```

### 6. Missing Dependencies in Downloaded Archives
```
ERROR: [file] not found, No such file or directory
SYMPTOM: .gitignore excludes large files, not available in CI/CD
FIX: Either download from source or make COPY conditional
  if [ -f cached/file ]; then use it; else download it; fi
```

### 7. Symlink Resolution Breaking Docker Paths
```
ERROR: /mnt/data/... not found in container
SYMPTOM: .resolve() converts symlinks, breaks Docker bind-mount paths
FIX: Remove .resolve() from path construction
  Path(__file__).parent.parent (not .resolve())
```

## Tools and Commands Used

### GitHub Actions
```bash
# List recent builds
gh run list --limit 5

# View specific build status
gh run list --limit 1 --json status,conclusion,createdAt

# Get build logs
gh run view {RUN_ID} --log

# Monitor build in real-time (with polling)
for i in {1..30}; do
  STATUS=$(gh run list --limit 1 --json status)
  echo "Check $i - Status: $STATUS"
  sleep 10
done
```

### Docker Debugging
```bash
# Build locally for testing
docker build -t {mcp_name}:test .

# Build with detailed output
docker build -t {mcp_name}:test --progress=plain .

# Run and inspect errors
docker run {mcp_name}:test bash

# Check image layers
docker history {mcp_name}:test
```

### Git Operations
```bash
# View recent commits
git log --oneline -5

# Show changes
git diff Dockerfile

# Commit with message
git commit -m "Fix: description"

# Push to remote
git push origin main
```

## Best Practices

1. **Always read the full error context** - Look 5+ lines before and after the error message
2. **Reproduce locally first** - Build the Dockerfile locally to understand the issue
3. **One fix at a time** - Implement single fixes and test before combining
4. **Document the root cause** - Include "why" in commit messages
5. **Check for patterns** - If one MCP has an issue, others might too
6. **Use retry logic** - Network operations should always have retries
7. **Add helpful error messages** - Include links and instructions if operations fail
8. **Test with different users** - Use `--user` flag to test permission issues
9. **Keep Docker images lean** - Remove cache and temporary files
10. **Use .dockerignore** - Exclude unnecessary files from build context

## Example: Complete Debug Session

```
User: "Fix Docker build for plmc_mcp"

Step 1: Check status
→ gh run list shows latest build failed

Step 2: Get logs
→ gh run view {ID} --log | grep -i error
→ Found: "error: command 'gcc' failed"

Step 3: Diagnose
→ Root cause: Missing build-essential for C extension compilation
→ Solution: Add build-essential to apt-get install

Step 4: Implement fix
→ Edit Dockerfile: add build-essential
→ Commit: "Add build-essential to fix C extension compilation"

Step 5: Push and monitor
→ git push origin main
→ gh run list shows new build in_progress
→ Wait for completion...
→ Build succeeds! ✅

Step 6: Verify
→ Check image in registry
→ Confirm no new issues introduced
→ Document fix for future reference
```

## Integration with ProteinMCP

This skill works with:
- **All MCPs** in the tool-mcps/ directory
- **Any GitHub-based MCP repository**
- **Docker-based MCPs** using standard patterns
- **Both local and CI/CD builds**

Use this skill when:
- A GitHub Actions Docker build fails
- You need to debug local Docker builds
- You're adding a new MCP and need to optimize the build
- You want to add resilience to network operations
- You need to fix permission or dependency issues

## References

- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices/
- GitHub Actions: https://docs.github.com/en/actions
- Alpine Linux Base: https://hub.docker.com/_/alpine (lightweight alternative)
- Python Base Images: https://hub.docker.com/_/python
- PyTorch Docker: https://hub.docker.com/r/pytorch/pytorch

