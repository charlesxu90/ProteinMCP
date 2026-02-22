---
title: Binder Design
layout: default
parent: MCP Catalog
nav_order: 3
---

# Binder Design MCPs

Design protein binders and nanobodies targeting specific proteins.

| MCP | Runtime | Description |
|-----|---------|-------------|
| [BindCraft MCP](https://github.com/Biomolecular-Design-Nexus/bindcraft_mcp) | docker | BindCraft for protein binder design (RFdiffusion + ProteinMPNN + AF2) |
| [BoltzGen MCP](https://github.com/Biomolecular-Design-Nexus/boltzgen_mcp) | docker | BoltzGen for nanobody CDR loop design |

## Install

These are Docker MCPs — local build is recommended:

```bash
cd tool-mcps/bindcraft_mcp && docker build -t bindcraft_mcp:latest . && cd ../..
cd tool-mcps/boltzgen_mcp && docker build -t boltzgen_mcp:latest . && cd ../..

pmcp install bindcraft_mcp
pmcp install boltzgen_mcp
```
