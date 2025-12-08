# MCP servers

Please clone and download the corresponding MCP servers from [Biomolecular Design Nexus repositories](https://github.com/Biomolecular-Design-Nexus), and put it under `./tool-mcps` directory.

## Examples

```shell

```

## List of MCP servers


## Workflow to create MCP servers
```shell
mkdir tool-mcps/xxx_mcp
cd tool-mcps/xxx_mcp
mkdir repo scripts src examples

cd repo
git clone git@github.com:xxx/xxx.git
cd ..

# Create environment

# Implement local scripts
claude
# Please implement function ABC in @scripts for local running

# Test local scripts with python scripts/xxx.py

# Implement MCP API
claude
# Please adapte function ABC in @scripts as MCP APIs in @src

# Test MCP API

# Install MCP API in claude code and run
```