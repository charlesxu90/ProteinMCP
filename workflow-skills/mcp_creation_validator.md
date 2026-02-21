# MCP Creation & Docker Build Validator

## Overview
This skill provides a systematic checklist and validation process for creating new MCPs with reliable Docker builds. It ensures quality, consistency, and successful GitHub Actions builds.

## When to Use This Skill
- **Creating a new MCP** from a GitHub repository
- **Adding Docker support** to an existing MCP
- **Setting up GitHub Actions** for Docker builds
- **Pre-launch validation** before publishing an MCP
- **Ensuring build consistency** across multiple MCPs

## MCP Creation Checklist

### Phase 1: Repository Setup

#### 1.1 Repository Information
```
Please gather the following information about the target repository:

1. Repository URL: {REPO_URL}
2. Repository owner and name
3. Main language(s) used
4. Key dependencies and tools
5. Does it have existing Docker setup? (Dockerfile, docker-compose.yml)
6. License type
7. Installation requirements
```

#### 1.2 Create Directory Structure
```
Create the MCP directory with proper structure:

tool-mcps/{mcp_name}/
├── Dockerfile              (Docker image definition)
├── .dockerignore           (exclude unnecessary files)
├── .github/
│   └── workflows/
│       └── docker-build.yml (GitHub Actions workflow)
├── src/
│   └── server.py          (FastMCP server)
├── scripts/               (helper scripts)
├── configs/               (configuration files)
├── examples/              (example inputs/outputs)
├── requirements.txt       (Python dependencies)
├── quick_setup.sh         (local development setup)
└── README.md              (documentation)
```

#### 1.3 Initialize Git Repository
```
Set up version control:

1. Initialize git in the MCP directory:
   git init
   git remote add origin {REPO_URL}
   git branch -M main

2. Create .gitignore with standard patterns:
   __pycache__/
   *.egg-info/
   .venv/
   env/
   results/
   cache/
   *.pyc
   .env

3. Create initial commit:
   git add .
   git commit -m "Initial MCP setup"
   git push -u origin main
```

### Phase 2: Dockerfile Creation

#### 2.1 Choose Base Image
```
Select appropriate base image based on requirements:

1. **For PyTorch/ML models**:
   FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime
   - Includes PyTorch, CUDA, cuDNN
   - Need to add: build-essential for C extensions

2. **For Python applications**:
   FROM python:3.10-slim
   - Lightweight Python image
   - Need to add: system dependencies as needed

3. **For specific frameworks**:
   - TensorFlow: tensorflow/tensorflow:latest-gpu
   - JAX: jax/jax:latest-gpu
   - MLflow: python:3.10 with mlflow package

Base image selection impacts:
- Build size
- Pre-installed dependencies
- GPU/CUDA support
- Build time
```

#### 2.2 System Dependencies
```
Add necessary system packages:

CRITICAL packages (add to all Dockerfiles):
- build-essential (for C extensions)
- git (for cloning repositories)
- wget (for downloading files)

Python-specific packages:
- python3-dev (for packages needing compilation)
- libffi-dev (for cffi)
- libssl-dev (for cryptography)

Application-specific packages:
- tcsh, gawk (for legacy bioinformatics tools)
- libopenblas-dev (for numerical libraries)
- graphviz (for visualization)

Minimize package installs:
RUN apt-get update && apt-get install -y \
    build-essential git wget \
    && rm -rf /var/lib/apt/lists/*
```

#### 2.3 Key Dockerfile Patterns

**Pattern 1: Clone External Repository**
```dockerfile
RUN mkdir -p repo && \
    for attempt in 1 2 3; do \
      echo "Clone attempt $attempt/3"; \
      git clone --depth 1 {REPO_URL} repo/{DIR_NAME} && break; \
      if [ $attempt -lt 3 ]; then sleep 5; fi; \
    done
```

**Pattern 2: Install Python Dependencies**
```dockerfile
# Method A: From requirements.txt (filter if needed)
RUN pip install --no-cache-dir \
    $(grep -v -E "^(torch|tensorflow)" requirements.txt | tr '\n' ' ')

# Method B: Explicit dependencies
RUN pip install --no-cache-dir \
    numpy pandas scipy scikit-learn loguru fastmcp

# Always ignore installed versions to prevent conflicts:
RUN pip install --no-cache-dir --ignore-installed fastmcp
```

**Pattern 3: Download Large Binaries/Models**
```dockerfile
# With caching (check local first)
RUN mkdir -p repo && \
    if [ -d repo/model_cache ]; then \
      cp -r repo/model_cache /app/repo/; \
    else \
      wget -O repo/model.tar.gz {URL} && \
      tar -xzf repo/model.tar.gz -C repo/; \
    fi
```

**Pattern 4: File Permissions (Non-root User)**
```dockerfile
COPY src/ ./src/
RUN chmod -R a+r /app/src/

COPY scripts/ ./scripts/
RUN chmod -R a+r /app/scripts/

COPY configs/ ./configs/
RUN chmod -R a+r /app/configs/
```

**Pattern 5: Environment Setup**
```dockerfile
# Create necessary directories
RUN mkdir -p /app/results /app/jobs /app/tmp /app/cache

# Set Python path
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Entry point
CMD ["python", "src/server.py"]
```

#### 2.4 Dockerfile Validation Checklist
```
Before testing, verify your Dockerfile has:

□ Appropriate base image for the use case
□ build-essential in apt-get install
□ All external repos cloned with retry logic (3 attempts, 5s delays)
□ Dependencies installed with --no-cache-dir flag
□ File permissions fixed with chmod -R a+r after COPY
□ Working directories created (results, jobs, tmp, cache)
□ PYTHONPATH and WORKDIR set
□ CMD or ENTRYPOINT defined
□ License/attribution comments for proprietary tools
□ .dockerignore file to exclude unnecessary files
□ Error handling and helpful error messages

Common pitfalls to avoid:
□ PyTorch version conflicts (filter from requirements)
□ Missing build-essential for C extensions
□ Unset file permissions (breaks --user flag)
□ Missing retry logic for git clone
□ Large files in build context (use .dockerignore)
□ Hardcoded paths (use /app based paths)
```

### Phase 3: GitHub Actions Workflow

#### 3.1 Create Workflow File
```
Create .github/workflows/docker-build.yml with:

name: Build & Push Docker Image

on:
  push:
    branches: [main]
    paths:
      - 'Dockerfile'
      - '.dockerignore'
      - 'src/**'
      - 'scripts/**'
      - 'configs/**'
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - uses: actions/checkout@v4

      # Optional: Cache large downloads
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: |
            model_cache/
            repo/
          key: ${{ runner.os }}-mcp-${{ hashFiles('Dockerfile') }}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to GHCR
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: ${{ github.event_name == 'push' }}
          tags: ghcr.io/${{ github.repository_owner }}/{mcp_name}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

#### 3.2 Workflow Optimization
```
For faster builds:

1. Use BuildKit caching:
   cache-from: type=gha
   cache-to: type=gha,mode=max

2. Cache large downloads:
   - model weights
   - cloned repositories
   - build artifacts

3. Use .dockerignore:
   results/
   cache/
   __pycache__/
   *.egg-info/
   .venv/
   .pytest_cache/
   .git/

4. Shallow clones:
   git clone --depth 1 (instead of full clone)

5. Multi-stage builds:
   FROM base as builder
   FROM base as runtime
```

### Phase 4: Local Testing

#### 4.1 Build Locally
```
Test the Dockerfile locally before pushing:

1. Build the image:
   docker build -t {mcp_name}:test .

2. With detailed output:
   docker build -t {mcp_name}:test --progress=plain .

3. Check build size:
   docker images | grep {mcp_name}

4. Expected sizes:
   - Lightweight Python: 500MB - 1GB
   - PyTorch: 3GB - 5GB
   - Large models included: 5GB+
```

#### 4.2 Run Locally
```
Test the running container:

1. Basic test:
   docker run --rm {mcp_name}:test python -c "import fastmcp; print('OK')"

2. With GPU:
   docker run --rm --gpus all {mcp_name}:test nvidia-smi

3. With user flag:
   docker run --rm --user 1000:1000 {mcp_name}:test id

4. Interactive shell:
   docker run -it --rm {mcp_name}:test bash

5. Test the MCP server:
   docker run -i --rm {mcp_name}:test python src/server.py &
   # Send test request
   kill %1
```

#### 4.3 Common Local Test Failures
```
If build fails locally:

1. Permission error:
   → Add chmod -R a+r after COPY directives

2. gcc not found:
   → Add build-essential to apt-get install

3. Python package not found:
   → Check requirements.txt, add missing packages

4. Clone timeout:
   → Add retry logic (3 attempts, 5s delays)

5. File not found:
   → Check .dockerignore, verify COPY paths
   → Use absolute paths in Dockerfile

6. PyTorch conflict:
   → Filter torch packages from requirements.txt

7. Port already in use:
   → Stop other containers: docker stop $(docker ps -q)
```

### Phase 5: GitHub Actions Testing

#### 5.1 Trigger Build
```
Push to GitHub to trigger workflow:

1. Make a test commit:
   git add Dockerfile
   git commit -m "Initial Dockerfile"
   git push origin main

2. Check GitHub Actions:
   gh run list --limit 5

3. View specific run:
   gh run view {RUN_ID} --log

4. Expected duration:
   - First build: 5-15 minutes
   - Subsequent builds (cached): 2-5 minutes
```

#### 5.2 Monitor Build
```
Monitor the GitHub Actions build:

1. List recent runs:
   gh run list --limit 1 --json status,conclusion

2. If in_progress, wait for completion:
   for i in {1..30}; do
     STATUS=$(gh run list --limit 1 --json status)
     [ "$STATUS" = "completed" ] && break
     sleep 10
   done

3. Check conclusion:
   - success: Build passed ✅
   - failure: Build failed ❌

4. If failed, retrieve logs:
   gh run view {RUN_ID} --log | grep -A 5 -B 5 "error"
```

#### 5.3 Troubleshoot Failures
```
If GitHub Actions build fails:

1. Get the error message (see mcp_docker_debug skill)

2. Categorize the error:
   - Permission issue
   - Missing dependency
   - Compilation error
   - Network timeout
   - Conflicting versions

3. Implement fix in Dockerfile

4. Commit and push:
   git add Dockerfile
   git commit -m "Fix: {issue}"
   git push origin main

5. Monitor new build

6. If still failing, use mcp_docker_debug skill for detailed analysis
```

### Phase 6: Final Validation

#### 6.1 Build Success Verification
```
Once build succeeds in GitHub Actions:

1. Verify build status:
   gh run list --limit 1 --json status,conclusion
   → Should show: "success"

2. Check image push:
   gh run view {RUN_ID} --log | grep -i "push"
   → Should see: "Successfully pushed image"

3. Verify registry:
   For GHCR: ghcr.io/{owner}/{mcp_name}:latest

4. Pull and test image:
   docker pull ghcr.io/{owner}/{mcp_name}:latest
   docker run --rm ghcr.io/{owner}/{mcp_name}:latest python -c "import fastmcp; print('OK')"
```

#### 6.2 MCP Registration
```
Register the MCP with ProteinMCP:

1. Add to configs/mcps.yaml:
   - name: {mcp_name}
     runtime: docker
     image: ghcr.io/{owner}/{mcp_name}:latest
     docker_cmd: |
       docker run -i --rm --gpus all --ipc=host \
       -v {ABSOLUTE_PATH}:{ABSOLUTE_PATH} \
       ghcr.io/{owner}/{mcp_name}:latest

2. Register with Claude Code:
   claude mcp add {mcp_name} -- \
     docker run -i --rm --gpus all --ipc=host \
     -v {ABSOLUTE_PATH}:{ABSOLUTE_PATH} \
     ghcr.io/{owner}/{mcp_name}:latest

3. Test MCP:
   claude mcp list
   → Should show {mcp_name} as registered

4. Verify tools are available:
   mcp__{{mcp_name}}__{{tool_name}}
```

#### 6.3 Documentation
```
Create comprehensive documentation:

1. README.md in MCP directory:
   - Description of what the MCP does
   - Installation instructions
   - Usage examples
   - Configuration options
   - Troubleshooting guide

2. Add to ProteinMCP README:
   - Link to the MCP
   - Brief description
   - Category (Structure Prediction, Design, etc.)

3. Add examples/:
   - Sample input files
   - Sample output files
   - Usage notebooks if applicable

4. Document dependencies:
   - External tools required
   - License restrictions
   - System requirements
   - GPU memory needed (if applicable)
```

## Validation Checklist (Complete)

```
Before considering the MCP "complete":

DOCKERFILE:
□ Correct base image selected
□ All dependencies installed
□ Git clone has retry logic
□ File permissions fixed with chmod
□ Working directories created
□ Environment variables set
□ Error messages are helpful

GITHUB ACTIONS:
□ Workflow file created
□ Triggers configured correctly
□ Caching enabled for speed
□ Build passes consistently
□ Image pushes to registry

LOCAL TESTING:
□ Builds locally without errors
□ Runs with docker run
□ Runs with --user flag
□ Runs with --gpus flag (if applicable)
□ FastMCP server starts

REGISTRATION:
□ Added to mcps.yaml
□ Registered with Claude Code
□ Shows in claude mcp list
□ Tools are accessible

DOCUMENTATION:
□ README describes the MCP
□ Installation steps documented
□ Usage examples provided
□ Troubleshooting guide included
□ Links added to ProteinMCP README
□ Dependencies clearly stated

PERFORMANCE:
□ First build: reasonable time (< 20 minutes)
□ Subsequent builds: fast (< 5 minutes)
□ Image size: acceptable
□ Memory usage: within limits
□ GPU utilization: confirmed (if applicable)
```

## Integration with MCP Docker Debug Skill

When you encounter build failures:

1. Use this skill to set up the MCP structure
2. Use **mcp_docker_debug** skill when builds fail
3. Iterate between testing and fixing
4. Come back to this skill for final validation

The debug skill provides:
- Root cause identification
- Error analysis
- Fix implementation
- Build monitoring
- Verification procedures

## Expected Timelines

```
Complete MCP creation (new from scratch):
1. Repository setup: 10 minutes
2. Dockerfile creation: 30 minutes
3. Local testing: 20 minutes
4. GitHub Actions setup: 10 minutes
5. First build: 10-20 minutes
6. Troubleshooting (if needed): 10-60 minutes
7. Documentation: 20 minutes
Total: 1.5-3 hours

MCP with pre-existing Dockerfile:
1. Integrate into ProteinMCP structure: 15 minutes
2. Test locally: 10 minutes
3. Setup GitHub Actions: 5 minutes
4. First build: 10-20 minutes
5. Troubleshooting (if needed): 10-60 minutes
Total: 50 minutes - 1.5 hours

Troubleshooting single build failure:
1. Get error logs: 2 minutes
2. Diagnose root cause: 5 minutes
3. Implement fix: 5 minutes
4. Commit and push: 2 minutes
5. Monitor new build: 10-20 minutes
Total: 20-35 minutes
```

## References

- **FastMCP**: https://github.com/jlowin/FastMCP
- **Docker**: https://docs.docker.com
- **GitHub Actions**: https://docs.github.com/en/actions
- **ProteinMCP Architecture**: See CLAUDE.md
- **MCP Docker Debug Skill**: Use for troubleshooting

