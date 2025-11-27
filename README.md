# Doctown v8

> "npm but for documentation" - AI-powered documentation generation for anything

Turn any codebase (or really, any collection of files) into a structured, explorable .docpack with AI-generated documentation.

## The Simplest Version (Web Interface)

1. Upload a .zip folder → 2. AI generates documentation → 3. Explore your docpack

No cloud, no complexity - just localhost magic.

```bash
# Start the web interface
./start_web.sh

# Open http://localhost:5173
# Drag and drop a .zip file
# Wait for the magic
```

## Core Concept

A **docpack** is a self-contained universe consisting of:

1. **Environment manifest** (`docpack.json`) - Defines tools, constraints, and capabilities
2. **Content universe** (`files/`) - Source code, PDFs, CSVs, images, or any other files
3. **Semantic index** (`index/`) - Pre-built graph, search index, and embeddings
4. **Agent tasks** (`tasks.json`) - Goals, constraints, and expected outputs

The agent "lives in" the docpack container, using tools to explore and reason about the content.

## Quick Start

### Local Development

1. **Set up environment:**
   ```bash
   cd documenter
   cp .env.example .env
   # Add your OPENAI_API_KEY to .env
   ```

2. **Build the Docker image:**
   ```bash
   docker build -t doctown:latest documenter/
   ```

3. **Run with example docpack:**
   ```bash
   docker run --env-file documenter/.env \
     -v $(pwd)/example.docpack:/workspace \
     doctown:latest
   ```

   Or use docker-compose:
   ```bash
   docker-compose up doctown-agent
   ```

4. **Check the output:**
   ```bash
   ls -la example.docpack/output/
   cat example.docpack/output/architecture.md
   ```

### Create Your Own Docpack

```bash
# Create structure
mkdir my-project.docpack
cd my-project.docpack
mkdir files index output

# Add your content
cp -r /path/to/your/project/* files/

# Create manifest (see DOCPACK_SPEC.md for schema)
cat > docpack.json << 'EOF'
{
  "version": "1.0",
  "name": "my-project",
  "description": "My project documentation",
  "environment": {
    "tools": ["list_files", "read_file", "write_output"],
    "constraints": {
      "max_file_reads": 1000,
      "max_execution_time_seconds": 300
    }
  }
}
EOF

# Create tasks
cat > tasks.json << 'EOF'
{
  "mission": "Document this project",
  "tasks": [
    {
      "id": "task_1",
      "name": "Create overview",
      "description": "Write a comprehensive overview",
      "output": {"type": "markdown", "path": "overview.md"}
    }
  ]
}
EOF

# Run the agent
docker run --env-file ../documenter/.env \
  -v $(pwd):/workspace \
  doctown:latest
```

## Production Deployment (RunPod, Modal, etc.)

1. **Push your image:**
   ```bash
   docker tag doctown:latest your-registry/doctown:latest
   docker push your-registry/doctown:latest
   ```

2. **Deploy to RunPod:**
   - Use the pushed image
   - Mount your .docpack as a volume at `/workspace`
   - Set `OPENAI_API_KEY` environment variable
   - Container will run, process, and exit

3. **Retrieve results:**
   - Output will be in `/workspace/output/` inside the container
   - Mount this as a persistent volume to retrieve results

## Architecture

```
┌─────────────────────────────────────────┐
│         Docker Container                │
│  ┌───────────────────────────────────┐  │
│  │   Agent Orchestrator (main.py)   │  │
│  └───────────┬───────────────────────┘  │
│              │                           │
│  ┌───────────▼───────────┐              │
│  │   Sandbox (sandbox.py)│              │
│  │   - Loads manifest    │              │
│  │   - Manages paths     │              │
│  │   - Enforces security │              │
│  └───────────┬───────────┘              │
│              │                           │
│  ┌───────────▼───────────┐              │
│  │   Tools (tools.py)    │              │
│  │   - list_files        │              │
│  │   - read_file         │              │
│  │   - search_code       │              │
│  │   - query_graph       │              │
│  │   - write_output      │              │
│  └───────────────────────┘              │
│                                          │
│  Volume: /workspace (.docpack)          │
│  ├── docpack.json                       │
│  ├── tasks.json                         │
│  ├── files/          (input)            │
│  ├── index/          (prebuilt)         │
│  └── output/         (results)          │
└─────────────────────────────────────────┘
```

## Key Files

- [`DOCPACK_SPEC.md`](DOCPACK_SPEC.md) - Complete .docpack format specification
- [`documenter/Dockerfile`](documenter/Dockerfile) - Container definition
- [`documenter/main.py`](documenter/main.py) - Agent orchestrator
- [`documenter/sandbox.py`](documenter/sandbox.py) - Sandbox environment
- [`documenter/tools.py`](documenter/tools.py) - Agent tools implementation
- [`docker-compose.yml`](docker-compose.yml) - Local testing setup
- [`example.docpack/`](example.docpack/) - Example docpack for testing

## Development Workflow

1. **Make changes to documenter code**
2. **Rebuild image:** `docker-compose build`
3. **Test locally:** `docker-compose up`
4. **Inspect output:** `cat example.docpack/output/*`
5. **Iterate**

## Security

- Agent runs as non-root user
- File access restricted to `/workspace` volume
- Path traversal protection via `sandbox.resolve()`
- Resource limits configurable in `docpack.json`
- No network access by default (add if needed)

## What's Inside

### Web Interface (`/website`)
- **Drag & drop upload** - Just drop a .zip file
- **Browse docpacks** - See all your generated documentation
- **Explore content** - View source files and AI-generated docs
- **Localhost-first** - Everything runs on your machine

### CLI (`/cli`)
Rust-based command-line tool:
```bash
localdoc ingest ./my-project --out my-project.docpack
localdoc run my-project.docpack
localdoc inspect my-project.docpack
```

### Documenter (`/documenter`)
Docker container running AI agent:
- Sandboxed Python environment
- OpenAI GPT-4 powered
- Custom tool access (read files, search code, write output)

## Storage

Everything lives in `~/.localdoc/`:

```
~/.localdoc/
├── temp/              # Temporary upload processing
└── outputs/           # All generated .docpacks
    ├── project1-abc123.docpack/
    ├── project2-def456.docpack/
    └── ...
```

## Philosophy

Started with AST parsing and complex code analysis. Ended up here - a much simpler, more elegant solution:

1. **Universal Input** - Not just code, anything you want documented
2. **AI-Powered** - Let the model figure out what matters
3. **Deterministic Output** - .docpack files are portable and reproducible
4. **Localhost First** - Build locally, share later

## Future Enhancements

- [ ] Markdown rendering in viewer
- [ ] Syntax highlighting for code
- [ ] Real-time progress updates via WebSocket
- [ ] Share docpacks via links
- [ ] R2 storage integration
- [ ] Public docpack registry
- [ ] Support for embeddings-based semantic search
- [ ] Multi-agent collaboration

## License

MIT
