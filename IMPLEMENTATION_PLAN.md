# Doctown v8 Implementation Plan

## Vision

Transform Doctown from a static AST/embedding analysis tool into a **dynamic agent orchestration platform** where AI agents explore and document arbitrary content types within secure Docker containers.

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

### ✅ Completed (Phase 1)

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

### 🚧 Next Steps (Phase 2)

#### 2.1 Builder Tool
Create a CLI tool to generate .docpacks from raw projects:

```bash
doctown-build \
  --input ~/my-project \
  --output my-project.docpack \
  --type codebase \
  --index-level full
```

Features:
- Auto-detect project type (Python, JS, legal docs, etc.)
- Generate semantic graph using AST/tree-sitter
- Build search index
- Create reasonable default tasks
- Optional: pre-compute embeddings

**Files to create:**
- `builder/main.py` - CLI entry point
- `builder/analyzers/python.py` - Python AST analyzer
- `builder/analyzers/javascript.py` - JS/TS analyzer
- `builder/indexer.py` - Graph/search index builder
- `builder/embeddings.py` - Embedding generator

#### 2.2 Enhanced Tool Set

Add more powerful tools for agents:

- `execute_bash(command)` - Run safe shell commands (with whitelist)
- `semantic_search(query, top_k)` - Vector similarity search
- `render_diagram(spec)` - Generate architecture diagrams
- `query_embeddings(text)` - Find similar code chunks
- `git_history(file)` - Understand file evolution
- `dependency_graph()` - Show import relationships

**Files to update:**
- `documenter/tools.py` - Add new tool implementations
- `documenter/sandbox.py` - Add embeddings loader

#### 2.3 Multi-Format Support

Currently only handles text files. Add:

- **PDF reading** - OCR + vision models
- **Image analysis** - Vision API for diagrams, screenshots
- **Binary inspection** - For compiled artifacts
- **Database schemas** - SQL/NoSQL schema docs

**Approach:** New tool types that handle non-text formats

#### 2.4 Streaming & Progress

Real-time feedback during long-running jobs:

- WebSocket connection for live updates
- Progress bars for file processing
- Intermediate result streaming
- Cancellation support

**Files to create:**
- `documenter/streaming.py` - WebSocket handler
- `documenter/progress.py` - Progress tracking

#### 2.5 Validation & Quality Checks

Ensure output meets standards:

- Parse task constraints from `tasks.json`
- Validate output against rules
- Check for required sections
- Measure documentation completeness
- Quality scoring

**Files to create:**
- `documenter/validator.py` - Output validation
- `documenter/quality.py` - Quality metrics

### 🔮 Future Enhancements (Phase 3)

#### 3.1 Multi-Agent Collaboration
- Specialist agents (architecture, API, testing)
- Agent coordination protocols
- Shared knowledge base

#### 3.2 Web UI
- Upload interface for .docpack creation
- Real-time agent monitoring
- Interactive documentation browser
- .docpack marketplace

#### 3.3 Advanced Indexing
- Incremental index updates
- Multi-modal embeddings
- Custom embedding models per domain
- Graph query language

#### 3.4 Production Optimizations
- Checkpoint/resume for long jobs
- Parallel agent execution
- Smart caching
- Cost optimization strategies

## Development Priorities

**Immediate (This Week):**
1. Test current implementation with example.docpack
2. Fix any bugs in orchestrator loop
3. Add basic error handling
4. Document API properly

**Short Term (2-4 Weeks):**
1. Build the docpack builder tool
2. Test with real codebases (5-10 different projects)
3. Add semantic search capability
4. Improve agent prompting for better outputs

**Medium Term (1-3 Months):**
1. Add PDF/image support
2. Create web interface for .docpack viewing
3. Implement validation system
4. Deploy to RunPod/Modal for production testing

## Success Metrics

1. **Correctness**: Generated docs accurately reflect codebase
2. **Completeness**: All important components documented
3. **Cost**: <$1 per medium-sized project
4. **Speed**: <5 min for typical project
5. **Portability**: .docpack works identically local vs cloud

## Technical Decisions

### Why Docker?
- True isolation vs filesystem tricks
- Reproducible environments
- Easy deployment to cloud platforms
- Resource limiting built-in

### Why OpenAI?
- Best tool-use capability
- Reliable function calling
- Good code understanding
- Can swap later if needed

### Why JSON for schemas?
- Universal compatibility
- Easy to parse/validate
- Human-readable
- Extensible

### Why separate index/?
- Pre-computation saves tokens
- Faster agent execution
- Supports offline analysis
- Enables smart search

## Risk Mitigation

**Risk: Agent costs too much**
- Mitigation: Resource limits, index guidance, task scoping

**Risk: Agent produces poor docs**
- Mitigation: Validation, examples, better prompting, iteration

**Risk: Security vulnerabilities**
- Mitigation: Docker isolation, path sanitization, no network by default

**Risk: Can't scale to large codebases**
- Mitigation: Smart chunking, incremental processing, semantic index

## Getting Started Today

```bash
cd /home/xander/Documents/doctown-v8

# Setup
./scripts/build.sh

# Test
./scripts/run-local.sh

# Iterate
# Edit documenter/*.py
# Rebuild and test
```

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.
