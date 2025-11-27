# Doctown v8 Implementation Plan

## Vision

Transform Doctown from a static AST/embedding analysis tool into a **dynamic agent orchestration platform** where AI agents explore
and document arbitrary content types within secure Docker containers.

## Core Innovation: The .docpack Format

A `.docpack` is a self-contained documentation universe with four conceptual layers:

### Layer 1: Environment Manifest (`docpack.json`)
- Defines sandbox bootstrapping
- Specifies available tools
- Sets resource constraints
- Configures execution environment

### Layer 2: Content Universe (`files/`)
- Arbitrary file types: code, PDFs, CSVs, images, binaries
- Completely opaque to packaging system
- Agent interprets through tools

### Layer 3: Semantic Index (`index/`)
- `graph.json` - Entity relationship graph
- `search.json` - Inverted keyword index
- `embeddings.bin` - Optional pre-computed embeddings
- Gives agents "cognitive footholds"

### Layer 4: Task Definitions (`tasks.json`)
- Mission statement
- Concrete task list with outputs
- Constraints and policies
- Validation criteria

## Architecture

```
Upload Zip + Instructions
         ↓
    Build .docpack
    (future: builder tool)
         ↓
    Docker Container
    ┌─────────────────────────┐
    │ Agent Orchestrator      │
    │   ↓                     │
    │ Sandbox Environment     │
    │   ↓                     │
    │ Tool Execution Layer    │
    │   ↓                     │
    │ .docpack Volume         │
    │ (files, index, tasks)   │
    └─────────────────────────┘
         ↓
    Generated Docs
    (output/ directory)
```

## Current Implementation Status

### Completed

1. **Specification**
   - [DOCPACK_SPEC.md](DOCPACK_SPEC.md) - Complete format specification
   - [QUICKSTART.md](QUICKSTART.md) - User guide
   - [README.md](README.md) - Project overview

2. **Docker Infrastructure**
   - [Dockerfile](documenter/Dockerfile) - Agent container definition
   - [docker-compose.yml](docker-compose.yml) - Local testing
   - [.dockerignore](documenter/.dockerignore) - Build optimization
   - Build/run scripts in [scripts/](scripts/)

3. **Core Engine**
   - [sandbox.py](documenter/sandbox.py) - Secure path resolution, manifest loading
   - [tools.py](documenter/tools.py) - Agent tool implementations
   - [main.py](documenter/main.py) - Agent orchestrator with task loop

4. **Example .docpack**
   - [example.docpack/](example.docpack/) - Fully functional test case
   - Includes manifest, tasks, index, and sample Python files
