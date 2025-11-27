# localdoc - Doctown CLI

A command-line tool for creating, managing, and running AI-powered documentation on `.docpack` archives.

## Installation

### Build from source

```bash
cd cli
cargo build --release
```

The binary will be available at `target/release/localdoc`.

### Install globally

```bash
cargo install --path .
```

## Commands

### `ingest` - Create a docpack from source

Create a new `.docpack` from a source directory, zip file, or git repository.

```bash
localdoc ingest <SOURCE> [OPTIONS]
```

**Arguments:**
- `<SOURCE>` - Path to source directory, zip file, or git URL

**Options:**
- `-o, --out <OUT>` - Output .docpack directory path (default: `out.docpack`)
- `-n, --name <NAME>` - Docpack name (defaults to source directory name)
- `-d, --description <DESCRIPTION>` - Description for the docpack
- `-l, --language <LANGUAGE>` - Primary language of the source code
- `--all-tools` - Enable all available tools (default: basic subset)
- `--build-index` - Build search index during ingestion
- `--build-graph` - Build semantic graph during ingestion

**Examples:**

```bash
# Create a docpack from a local directory
localdoc ingest ./my-project -o my-project.docpack

# Create with all tools and indexing enabled
localdoc ingest ./my-project --all-tools --build-index --build-graph

# Create with custom metadata
localdoc ingest ./my-project \
  -n "My Awesome Project" \
  -d "Documentation for my awesome project" \
  -l "python"
```

### `run` - Execute documenter on a docpack

Run the AI documenter agent on a `.docpack` using Docker.

```bash
localdoc run <DOCPACK> [OPTIONS]
```

**Arguments:**
- `<DOCPACK>` - Path to .docpack directory

**Options:**
- `-i, --image <IMAGE>` - Docker image to use (default: `doctown:latest`)
- `-f, --follow` - Follow logs in real-time

**Examples:**

```bash
# Run documenter on a docpack
localdoc run my-project.docpack

# Run with custom Docker image
localdoc run my-project.docpack -i doctown:v2

# Run and follow logs
localdoc run my-project.docpack -f
```

**Prerequisites:**
- Docker must be installed and running
- `.env` file with `OPENAI_API_KEY` must exist in current directory
- Docker image must be built: `docker build -t doctown:latest ../documenter/`

### `inspect` - View docpack metadata

Inspect a `.docpack`'s structure, metadata, and contents.

```bash
localdoc inspect <DOCPACK> [OPTIONS]
```

**Arguments:**
- `<DOCPACK>` - Path to .docpack directory

**Options:**
- `-v, --verbose` - Show detailed information including file tree and task list

**Examples:**

```bash
# Basic inspection
localdoc inspect my-project.docpack

# Detailed inspection with file tree
localdoc inspect my-project.docpack -v
```

**Output:**
- Docpack metadata (name, version, description)
- Environment configuration (tools, constraints)
- Content statistics (file count, total size)
- Index availability (search index, graph, embeddings)
- Tasks summary
- Generated output files

### `validate` - Validate docpack structure

Validate a `.docpack` against the DOCPACK_SPEC to ensure it's well-formed.

```bash
localdoc validate <DOCPACK>
```

**Arguments:**
- `<DOCPACK>` - Path to .docpack directory

**Examples:**

```bash
localdoc validate my-project.docpack
```

**Checks:**
- Required directories exist (`files/`, `index/`, `output/`)
- `docpack.json` exists and is valid JSON
- `docpack.json` has required fields (version, environment)
- Tools are recognized
- `tasks.json` is valid JSON (if present)
- Index files are valid JSON (if present)

### `init` - Initialize empty docpack

Create a new empty `.docpack` structure with template files.

```bash
localdoc init <PATH> [OPTIONS]
```

**Arguments:**
- `<PATH>` - Path for new .docpack directory

**Options:**
- `-n, --name <NAME>` - Docpack name
- `--with-tasks` - Create a minimal example tasks.json

**Examples:**

```bash
# Create minimal docpack
localdoc init my-project.docpack

# Create with name and tasks template
localdoc init my-project.docpack -n "My Project" --with-tasks
```

## Typical Workflow

### 1. Create a docpack from your project

```bash
localdoc ingest ./my-codebase \
  -o my-codebase.docpack \
  --all-tools \
  --build-index
```

### 2. Customize tasks (optional)

Edit `my-codebase.docpack/tasks.json` to define your documentation goals:

```json
{
  "mission": "Create comprehensive API documentation",
  "tasks": [
    {
      "id": "task_1",
      "name": "Document REST API",
      "description": "Create OpenAPI-style documentation for all endpoints",
      "output": {
        "type": "markdown",
        "path": "output/api-docs.md"
      }
    }
  ]
}
```

### 3. Validate the docpack

```bash
localdoc validate my-codebase.docpack
```

### 4. Run the documenter

```bash
localdoc run my-codebase.docpack -f
```

### 5. Inspect the results

```bash
localdoc inspect my-codebase.docpack -v
```

### 6. View generated documentation

```bash
cat my-codebase.docpack/output/*.md
```

## Environment Variables

The `run` command expects an `.env` file in the current directory with:

```env
OPENAI_API_KEY=your_api_key_here
```

## Integration with Doctown

This CLI is designed to work with the Doctown documenter pipeline:

1. **CLI** (`localdoc`) - Creates and manages `.docpack` archives
2. **Documenter** (Python agent) - Runs inside Docker to generate documentation
3. **DOCPACK_SPEC.md** - Defines the `.docpack` format specification

## Building for Release

```bash
cargo build --release
strip target/release/localdoc  # Optional: reduce binary size
```

## Development

```bash
# Run with cargo
cargo run -- inspect ../example.docpack

# Run tests
cargo test

# Check code
cargo clippy
```

## License

MIT
