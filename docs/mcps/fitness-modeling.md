---
title: Fitness Modeling
layout: default
parent: MCP Catalog
nav_order: 5
---

# Fitness Modeling & Mutation Prediction MCPs

Predict protein fitness landscapes and mutation effects using evolutionary and deep learning approaches.

| MCP | Runtime | Description |
|-----|---------|-------------|
| [ESM MCP](https://github.com/Biomolecular-Design-Nexus/esm_mcp) | docker | ESM for protein embedding and fitness modeling |
| [EV+OneHot MCP](https://github.com/Biomolecular-Design-Nexus/ev_onehot_mcp) | docker | Protein fitness prediction (evolutionary coupling + one-hot encoding) |
| [MutCompute MCP](https://github.com/Biomolecular-Design-Nexus/mutcompute_mcp) | python | MutCompute for protein mutation effect prediction |
| [PLMC MCP](https://github.com/Biomolecular-Design-Nexus/plmc_mcp) | docker | Evolutionary coupling analysis using PLMC |
| [ProtTrans MCP](https://github.com/Biomolecular-Design-Nexus/prottrans_mcp) | docker | ProtTrans for protein embeddings and fitness modeling |

## Install

Docker MCPs (local build recommended):

```bash
cd tool-mcps/esm_mcp && docker build -t esm_mcp:latest . && cd ../..
cd tool-mcps/ev_onehot_mcp && docker build -t ev_onehot_mcp:latest . && cd ../..
cd tool-mcps/plmc_mcp && docker build -t plmc_mcp:latest . && cd ../..
cd tool-mcps/prottrans_mcp && docker build -t prottrans_mcp:latest . && cd ../..

pmcp install esm_mcp
pmcp install ev_onehot_mcp
pmcp install plmc_mcp
pmcp install prottrans_mcp
```

Python MCP:

```bash
pmcp install mutcompute_mcp
```
