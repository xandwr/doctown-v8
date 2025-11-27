# CLI Integration Guide

This document explains how the `localdoc` CLI integrates with the Doctown documenter pipeline and DOCPACK_SPEC.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interaction                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │  localdoc CLI    │
                  │  (Rust binary)   │
                  └────────┬─────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌───────────┐  ┌──────────────┐  ┌─────────┐
    │  ingest   │  │   inspect    │  │   run   │
    │  init     │  │   validate   │  │         │
    └─────┬─────┘  └──────┬───────┘  └────┬────┘
          │                │               │
          ▼                ▼               ▼
    ┌──────────────────────────────────────────┐
    │         .docpack Directory               │
    │  ┌────────────────────────────────────┐  │
    │  │ docpack.json (manifest)            │  │
    │  │ tasks.json (agent goals)           │  │
    │  │ files/ (content)                   │  │
    │  │ index/ (search + graph)            │  │
    │  │ output/ (results)                  │  │
    │  └────────────────────────────────────┘  │
    └───────────────────┬──────────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  Docker Container│
              │  (doctown:latest)│
              └────────┬─────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Documenter      │
              │  (Python agent)  │
              │                  │
              │  - main.py       │
              │  - sandbox.py    │
              │  - tools.py      │
              └────────┬─────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  OpenAI API     │
              │  (or Ollama)    │
              └─────────────────┘
```

## Component Responsibilities

### 1. localdoc CLI (Rust)

**Purpose**: Create, manage, and orchestrate `.docpack` archives

**Responsibilities**:
- Create `.docpack` structures from source code
- Validate `.docpack` format compliance
- Inspect `.docpack` metadata and contents
- Trigger Docker-based documentation generation
- Initialize empty `.docpack` templates

**Key Files**:
- [cli/src/main.rs](cli/src/main.rs) - Command routing
- [cli/src/commands/ingest.rs](cli/src/commands/ingest.rs) - Docpack creation
- [cli/src/commands/run.rs](cli/src/commands/run.rs) - Docker orchestration
- [cli/src/commands/inspect.rs](cli/src/commands/inspect.rs) - Metadata display
- [cli/src/commands/validate.rs](cli/src/commands/validate.rs) - Spec validation
- [cli/src/commands/init.rs](cli/src/commands/init.rs) - Template creation

### 2. DOCPACK_SPEC.md

**Purpose**: Define the canonical `.docpack` format

**Defines**:
- Directory structure (files/, index/, output/)
- Manifest schema (docpack.json)
- Tasks schema (tasks.json)
- Index formats (graph.json, search.json)
- Tool APIs available to agents
- Runtime behavior and constraints

**Reference**: [DOCPACK_SPEC.md](DOCPACK_SPEC.md)

### 3. Documenter Pipeline (Python)

**Purpose**: Execute AI agent within a `.docpack` sandbox

**Responsibilities**:
- Load and parse `.docpack` manifest
- Initialize sandbox environment
- Provide tool APIs to OpenAI agent
- Manage agent execution loop
- Write results to output/

**Key Files**:
- [documenter/main.py](documenter/main.py) - Agent orchestrator
- [documenter/sandbox.py](documenter/sandbox.py) - Sandbox environment
- [documenter/tools.py](documenter/tools.py) - Tool implementations

## Data Flow

### Creating a Docpack

```
User Command:
  localdoc ingest ./my-project -o my.docpack --build-index

CLI Process:
  1. Validate source path exists
  2. Create directory structure:
     - my.docpack/files/
     - my.docpack/index/
     - my.docpack/output/
  3. Copy source files → my.docpack/files/
  4. Generate docpack.json with metadata
  5. Create default tasks.json
  6. [optional] Build search index → my.docpack/index/search.json
  7. [optional] Build graph → my.docpack/index/graph.json

Result:
  ✓ my.docpack/ ready for documentation
```

### Running the Documenter

```
User Command:
  localdoc run my.docpack -f

CLI Process:
  1. Validate my.docpack/docpack.json exists
  2. Get absolute path to my.docpack
  3. Execute Docker command:
     docker run --rm \
       --env-file .env \
       -v $(pwd)/my.docpack:/workspace \
       doctown:latest

Docker Container:
  1. Start with my.docpack mounted at /workspace
  2. Python main.py begins execution
  3. Load /workspace/docpack.json
  4. Load /workspace/tasks.json
  5. Initialize OpenAI client
  6. Create agent with tools from manifest
  7. Agent explores /workspace/files/
  8. Agent uses index/search.json, index/graph.json
  9. Agent writes to /workspace/output/
  10. Container exits

Result:
  ✓ Documentation in my.docpack/output/
```

### Inspecting Results

```
User Command:
  localdoc inspect my.docpack -v

CLI Process:
  1. Read my.docpack/docpack.json
  2. Parse metadata
  3. Count files in my.docpack/files/
  4. Check index/ contents
  5. List output/ files
  6. Display formatted report

Result:
  User sees comprehensive docpack overview
```

## File Format Compliance

The CLI enforces DOCPACK_SPEC.md compliance:

### Required Files

| File | Required | Created By | Validated By |
|------|----------|------------|--------------|
| `docpack.json` | Yes | `ingest`, `init` | `validate` |
| `tasks.json` | No (recommended) | `ingest`, `init --with-tasks` | `validate` |
| `files/` | Yes | `ingest`, `init` | `validate` |
| `index/` | No | `ingest --build-index` | - |
| `output/` | No (runtime) | Documenter | - |

### docpack.json Schema

```json
{
  "version": "1.0",              // Required by spec
  "name": "string",              // Required by spec
  "description": "string",       // Recommended
  "environment": {               // Required by spec
    "tools": [...],              // Required: array of tool names
    "interpreter": "python3.12", // Required
    "constraints": {...}         // Required: resource limits
  },
  "metadata": {                  // Optional
    "created": "ISO8601",
    "creator": "string",
    "source_type": "string",
    "language": "string"
  }
}
```

The CLI's `validate` command checks all these requirements.

## Tool Definitions

Available tools (defined in DOCPACK_SPEC.md, implemented in tools.py):

| Tool | Purpose | CLI Flag |
|------|---------|----------|
| `list_files` | List directory contents | Default |
| `read_file` | Read text files | Default |
| `write_output` | Write to output/ | Default |
| `read_image` | Read images for vision analysis | `--all-tools` |
| `read_pdf` | Convert PDF pages to images | `--all-tools` |
| `search_code` | Query inverted index | `--all-tools` |
| `query_graph` | Query semantic graph | `--all-tools` |

## Environment Setup

### Required for `localdoc run`

1. **Docker installed and running**
   ```bash
   docker --version
   docker ps
   ```

2. **Docker image built**
   ```bash
   cd documenter/
   docker build -t doctown:latest .
   ```

3. **.env file with API key**
   ```bash
   echo "OPENAI_API_KEY=sk-..." > .env
   ```

## Extension Points

### Adding New Commands

1. Create `cli/src/commands/newcommand.rs`
2. Add to `cli/src/commands/mod.rs`
3. Add variant to `Commands` enum in `main.rs`
4. Add match arm in `main()`

### Adding New Tools

1. Define in DOCPACK_SPEC.md
2. Implement in `documenter/tools.py`
3. Add to `all_tools` dict in `get_tool_definitions()`
4. Update CLI to enable via flag (optional)

### Custom Task Templates

Users can create reusable task templates:

```bash
# Save template
cat > ~/.doctown/api-docs.json << 'EOF'
{
  "mission": "Document REST API",
  "tasks": [...]
}
EOF

# Use template
localdoc init my.docpack
cp ~/.doctown/api-docs.json my.docpack/tasks.json
```

## Development Workflow

### Building the CLI

```bash
cd cli/
cargo build --release
```

### Testing

```bash
# Test CLI commands
./target/release/localdoc --help
./target/release/localdoc ingest ../example.docpack -o test.docpack
./target/release/localdoc inspect test.docpack -v
./target/release/localdoc validate test.docpack

# Test integration with documenter
docker build -t doctown:latest ../documenter/
./target/release/localdoc run test.docpack -f
```

### Iterating

1. Make changes to CLI (Rust code)
2. Rebuild: `cargo build --release`
3. Test command: `./target/release/localdoc ...`

OR

1. Make changes to Documenter (Python code)
2. Rebuild Docker: `docker build -t doctown:latest ../documenter/`
3. Run: `localdoc run my.docpack -f`

## Troubleshooting

### Common Issues

**Issue**: `localdoc: command not found`
- **Solution**: Build CLI with `cargo build --release`, use `./target/release/localdoc`

**Issue**: `Docker command failed`
- **Solution**: Ensure Docker is running (`docker ps`), image is built (`docker images | grep doctown`)

**Issue**: `OPENAI_API_KEY environment variable not set`
- **Solution**: Create `.env` file in current directory with `OPENAI_API_KEY=...`

**Issue**: `Path does not exist`
- **Solution**: Check paths are correct, use absolute paths if needed

**Issue**: `Validation failed`
- **Solution**: Run `localdoc validate my.docpack` to see specific errors

## Quick Reference

```bash
# Create from source
localdoc ingest ./code -o code.docpack --all-tools --build-index

# Validate
localdoc validate code.docpack

# Inspect
localdoc inspect code.docpack -v

# Run documenter
localdoc run code.docpack -f

# View results
ls -la code.docpack/output/
```

## Further Reading

- [CLI README](cli/README.md) - CLI usage and installation
- [CLI Examples](cli/EXAMPLES.md) - Real-world examples
- [DOCPACK_SPEC.md](DOCPACK_SPEC.md) - Format specification
- [Project README](README.md) - Overall project overview
