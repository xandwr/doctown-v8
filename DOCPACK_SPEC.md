# .docpack Format Specification v1.0

A `.docpack` is a portable, self-contained documentation universe that an AI agent can explore and reason about.

## Structure

```
my-project.docpack/
├── docpack.json          # Manifest - defines the environment and capabilities
├── files/                # The content universe (user uploads go here)
│   ├── src/
│   ├── docs/
│   └── ...
├── index/                # Semantic index and structural maps
│   ├── graph.json        # Graph of relationships between entities
│   ├── search.json       # Inverted index for fast lookup
│   └── embeddings.bin    # (Optional) Pre-computed embeddings
├── tasks.json            # Agent goals, constraints, and expected outputs
└── output/               # Where the agent writes results (created at runtime)
```

## Layer 1: Environment Manifest (`docpack.json`)

Defines how to build the sandbox and what tools are available.

```json
{
  "version": "1.0",
  "name": "my-project-docs",
  "description": "Documentation for MyProject",

  "environment": {
    "tools": [
      "list_files",
      "read_file",
      "read_image",        // NEW: Read image files for vision/OCR
      "read_pdf",          // NEW: Convert PDF pages to images for OCR
      "search_code",
      "query_graph",
      "write_output"
    ],
    "interpreter": "python3.12",
    "constraints": {
      "max_file_reads": 1000,
      "max_execution_time_seconds": 300,
      "memory_limit_mb": 2048
    }
  },

  "metadata": {
    "created": "2025-11-26T12:00:00Z",
    "creator": "doctown-builder",
    "source_type": "codebase",
    "language": "python"
  }
}
```

## Layer 2: Content Universe (`files/`)

This directory contains all user-uploaded content:
- Source code
- Documentation files
- PDFs, CSVs, images
- Configuration files
- Any other relevant files

The agent interacts with this through tools, not direct file access.

## Layer 3: Semantic Index (`index/`)

### `graph.json` - Relational graph of entities

```json
{
  "nodes": [
    {
      "id": "node_1",
      "type": "file",
      "path": "src/main.py",
      "metadata": {
        "lines": 150,
        "language": "python",
        "last_modified": "2025-11-26T12:00:00Z"
      }
    },
    {
      "id": "node_2",
      "type": "symbol",
      "name": "process_data",
      "path": "src/main.py",
      "line_start": 45,
      "line_end": 78,
      "metadata": {
        "kind": "function",
        "parameters": ["data", "options"],
        "returns": "dict"
      }
    },
    {
      "id": "node_3",
      "type": "cluster",
      "name": "data-processing",
      "description": "Data processing and transformation logic",
      "members": ["node_2", "node_5", "node_8"]
    }
  ],
  "edges": [
    {
      "from": "node_2",
      "to": "node_1",
      "type": "defined_in"
    },
    {
      "from": "node_2",
      "to": "node_5",
      "type": "calls"
    }
  ]
}
```

### `search.json` - Inverted index

```json
{
  "index": {
    "authentication": ["src/auth.py:12", "src/middleware.py:45"],
    "database": ["src/db.py:1", "src/models.py:23"],
    "api": ["src/routes.py:10", "src/handlers.py:5"]
  },
  "metadata": {
    "total_files": 50,
    "total_symbols": 250,
    "indexed_at": "2025-11-26T12:00:00Z"
  }
}
```

### `embeddings.bin` (Optional)

Binary file containing pre-computed embeddings for semantic search.
Format: Custom binary or numpy array saved with pickle/joblib.

## Layer 4: Tasks and Goals (`tasks.json`)

Defines what the agent should accomplish.

```json
{
  "mission": "Generate comprehensive documentation for this codebase",

  "tasks": [
    {
      "id": "task_1",
      "name": "Analyze project structure",
      "description": "Map out the high-level architecture and identify main components",
      "tools_allowed": ["list_files", "read_file", "query_graph"],
      "output": {
        "type": "markdown",
        "path": "output/architecture.md"
      }
    },
    {
      "id": "task_2",
      "name": "Document API endpoints",
      "description": "Create API documentation for all public endpoints",
      "depends_on": ["task_1"],
      "tools_allowed": ["read_file", "search_code", "semantic_search"],
      "output": {
        "type": "markdown",
        "path": "output/api-reference.md"
      }
    }
  ],

  "constraints": {
    "chain_of_thought_location": "/workspace/.reasoning",
    "forbidden_actions": ["modify_files", "execute_code"],
    "output_format": "markdown",
    "validation": {
      "required_sections": ["Overview", "Architecture", "API Reference"],
      "min_length": 1000
    }
  },

  "evaluation": {
    "success_criteria": [
      "All tasks completed without errors",
      "Output files exist at specified paths",
      "Validation rules pass"
    ]
  }
}
```

## Runtime Behavior

1. **Container starts** with the .docpack mounted at `/workspace`
2. **Orchestrator reads** `docpack.json` to understand available tools
3. **Orchestrator reads** `tasks.json` to understand goals
4. **Agent spawns** with access to configured tools
5. **Agent explores** the `files/` directory using tools
6. **Agent leverages** the `index/` for fast navigation
7. **Agent completes** tasks and writes to `output/`
8. **Container exits** with results in `output/`

## Tool APIs

Tools available to the agent (defined in `docpack.json`):

- **list_files(path)** - List files in directory
- **read_file(path)** - Read file contents
- **read_image(path)** - Read an image file (PNG, JPEG, WEBP, GIF) and return as base64 for vision/OCR analysis
- **read_pdf(path, page=1, dpi=200)** - Convert a PDF page to PNG and return as base64 for vision/OCR analysis (extracts text, diagrams, tables, handwriting)
- **search_code(query)** - Search using inverted index
- **query_graph(query_type, filters)** - Query the relationship graph
- **write_output(path, content)** - Write to output directory

### PDF and Image OCR

- The agent can call `read_image` or `read_pdf` to extract text and visual information from images and PDF files.
- `read_pdf` converts a specified page of a PDF to a PNG image, which is then analyzed using the vision model (OCR, diagram analysis, etc).
- Supported image formats: PNG, JPEG, WEBP, GIF. Supported PDF: any standard PDF (first N pages, configurable).
- This enables documentation of scanned documents, diagrams, screenshots, and multi-page PDFs.

## Benefits

1. **Portable** - Ship the entire documentation universe as one artifact
2. **Reproducible** - Same .docpack produces same results
3. **Secure** - Agent runs in isolated container
4. **Scalable** - Deploy to any container platform
5. **Domain-agnostic** - Works for code, PDFs, legal docs, game assets, etc.
