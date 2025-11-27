# localdoc CLI - Quick Start

Get started with the Doctown CLI in 5 minutes.

## Installation

```bash
cd cli
cargo build --release
```

The binary is now at `cli/target/release/localdoc`.

## Your First Docpack

### Option 1: From Existing Code

```bash
# Navigate to CLI directory
cd cli

# Create a docpack from your project
./target/release/localdoc ingest ~/my-project \
  -o my-project.docpack \
  --all-tools \
  --build-index

# Inspect what was created
./target/release/localdoc inspect my-project.docpack

# Validate it's correct
./target/release/localdoc validate my-project.docpack
```

### Option 2: Start from Scratch

```bash
# Create empty docpack with template
./target/release/localdoc init my-docs.docpack --with-tasks

# Add your files
cp -r ~/my-files/* my-docs.docpack/files/

# Validate structure
./target/release/localdoc validate my-docs.docpack
```

## Run the Documenter

### Prerequisites

1. **Build the Docker image** (one-time setup):
   ```bash
   cd ../documenter
   docker build -t doctown:latest .
   ```

2. **Create .env file** with your OpenAI API key:
   ```bash
   echo "OPENAI_API_KEY=sk-your-key-here" > .env
   ```

### Execute

```bash
# Run the documenter
./target/release/localdoc run my-project.docpack -f

# View generated documentation
ls -la my-project.docpack/output/
cat my-project.docpack/output/*.md
```

## Common Commands

```bash
# Get help
./target/release/localdoc --help
./target/release/localdoc ingest --help

# Create docpack from directory
./target/release/localdoc ingest ./source -o output.docpack

# Inspect docpack details
./target/release/localdoc inspect output.docpack -v

# Validate docpack format
./target/release/localdoc validate output.docpack

# Run documenter
./target/release/localdoc run output.docpack

# Initialize empty docpack
./target/release/localdoc init new.docpack --with-tasks
```

## Customization

### Edit Tasks

After creating a docpack, customize `tasks.json` to define specific documentation goals:

```bash
nano my-project.docpack/tasks.json
```

Example tasks.json:
```json
{
  "mission": "Create comprehensive API documentation",
  "tasks": [
    {
      "id": "task_1",
      "name": "Document REST API",
      "description": "Create detailed documentation for all REST endpoints",
      "output": {
        "type": "markdown",
        "path": "output/api-docs.md"
      }
    }
  ]
}
```

### Enable Additional Tools

Edit `docpack.json` to add more tools:

```bash
nano my-project.docpack/docpack.json
```

Add to the `tools` array:
- `read_image` - For analyzing image files
- `read_pdf` - For extracting content from PDFs
- `search_code` - For using the search index
- `query_graph` - For querying the semantic graph

## Next Steps

1. **Read the examples**: [EXAMPLES.md](EXAMPLES.md)
2. **Understand the integration**: [../CLI_INTEGRATION.md](../CLI_INTEGRATION.md)
3. **Review the spec**: [../DOCPACK_SPEC.md](../DOCPACK_SPEC.md)
4. **Full CLI reference**: [README.md](README.md)

## Troubleshooting

**Problem**: Binary not found
```bash
# Build again
cargo build --release
# Use full path
./target/release/localdoc --help
```

**Problem**: Docker errors
```bash
# Check Docker is running
docker ps
# Build the image
cd ../documenter && docker build -t doctown:latest .
```

**Problem**: OpenAI API errors
```bash
# Check .env file exists
cat .env
# Should contain: OPENAI_API_KEY=sk-...
```

**Problem**: Validation fails
```bash
# See detailed errors
./target/release/localdoc validate my.docpack
```

## Help

```bash
# General help
./target/release/localdoc --help

# Command-specific help
./target/release/localdoc ingest --help
./target/release/localdoc run --help
./target/release/localdoc inspect --help
```
