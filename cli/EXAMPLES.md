# localdoc CLI Examples

Real-world examples of using the Doctown CLI.

## Example 1: Document a Python Project

```bash
# 1. Create a docpack from your Python project
localdoc ingest ~/projects/my-python-app \
  -o my-python-app.docpack \
  -n "My Python Application" \
  -d "A web application built with Flask" \
  -l "python" \
  --all-tools \
  --build-index

# 2. Inspect what was created
localdoc inspect my-python-app.docpack

# 3. Validate the structure
localdoc validate my-python-app.docpack

# 4. Run the documenter
localdoc run my-python-app.docpack -f

# 5. View the generated documentation
ls -la my-python-app.docpack/output/
cat my-python-app.docpack/output/overview.md
```

## Example 2: Quick Start with Init

```bash
# 1. Initialize a new docpack
localdoc init my-docs.docpack --with-tasks

# 2. Add your files
cp -r ~/my-files/* my-docs.docpack/files/

# 3. Edit the manifest to enable vision tools for images/PDFs
nano my-docs.docpack/docpack.json
# Add "read_image" and "read_pdf" to tools array

# 4. Customize tasks
nano my-docs.docpack/tasks.json

# 5. Run
localdoc run my-docs.docpack
```

## Example 3: Documenting a Multi-Language Project

```bash
# Create docpack with all tools
localdoc ingest ~/projects/full-stack-app \
  -o full-stack.docpack \
  -n "Full Stack Application" \
  -d "React frontend + Node.js backend" \
  --all-tools \
  --build-index \
  --build-graph

# Edit tasks.json to document both frontend and backend
cat > full-stack.docpack/tasks.json << 'EOF'
{
  "mission": "Document the full-stack application architecture",
  "tasks": [
    {
      "id": "task_1",
      "name": "Document React Frontend",
      "description": "Document component structure, state management, and routing",
      "output": {"type": "markdown", "path": "output/frontend.md"}
    },
    {
      "id": "task_2",
      "name": "Document Node.js Backend",
      "description": "Document API endpoints, database models, and middleware",
      "output": {"type": "markdown", "path": "output/backend.md"}
    },
    {
      "id": "task_3",
      "name": "Create Architecture Diagram",
      "description": "High-level overview of system architecture",
      "output": {"type": "markdown", "path": "output/architecture.md"}
    }
  ]
}
EOF

# Run the documenter
localdoc run full-stack.docpack -f
```

## Example 4: Processing PDFs and Images

```bash
# Create docpack with vision tools
localdoc ingest ~/documents/research-papers \
  -o research.docpack \
  -n "Research Papers Collection" \
  --all-tools

# Verify vision tools are enabled
localdoc inspect research.docpack | grep -A5 "Tools enabled"

# Custom tasks for PDF extraction
cat > research.docpack/tasks.json << 'EOF'
{
  "mission": "Extract and summarize content from research PDFs",
  "tasks": [
    {
      "id": "task_1",
      "name": "Index all PDFs",
      "description": "List all PDF files and extract metadata",
      "tools_allowed": ["list_files", "read_pdf", "write_output"],
      "output": {"type": "markdown", "path": "output/pdf-index.md"}
    },
    {
      "id": "task_2",
      "name": "Extract key findings",
      "description": "Read each PDF and extract key findings, methodology, and conclusions",
      "tools_allowed": ["list_files", "read_pdf", "write_output"],
      "output": {"type": "markdown", "path": "output/summaries.md"}
    }
  ]
}
EOF

# Run
localdoc run research.docpack -f
```

## Example 5: Batch Processing Multiple Projects

```bash
# Create a script to process multiple projects
cat > batch_document.sh << 'EOF'
#!/bin/bash

PROJECTS=(
  "~/repos/project-a"
  "~/repos/project-b"
  "~/repos/project-c"
)

for project in "${PROJECTS[@]}"; do
  name=$(basename "$project")
  echo "Processing $name..."

  # Create docpack
  localdoc ingest "$project" \
    -o "${name}.docpack" \
    --all-tools \
    --build-index

  # Run documenter
  localdoc run "${name}.docpack"

  # Show results
  echo "Generated documentation for $name:"
  ls -lh "${name}.docpack/output/"
  echo "---"
done
EOF

chmod +x batch_document.sh
./batch_document.sh
```

## Example 6: Validation and Quality Checks

```bash
# Create docpack
localdoc ingest ~/my-project -o my-project.docpack

# Validate before running
if localdoc validate my-project.docpack; then
  echo "✓ Docpack is valid, proceeding..."
  localdoc run my-project.docpack
else
  echo "✗ Validation failed, please fix errors"
  exit 1
fi

# Inspect results
localdoc inspect my-project.docpack -v

# Check if output was generated
if [ -d "my-project.docpack/output" ]; then
  file_count=$(ls my-project.docpack/output/*.md 2>/dev/null | wc -l)
  echo "Generated $file_count documentation files"
fi
```

## Example 7: Custom Docker Image

```bash
# Build custom documenter image with additional tools
cat > Dockerfile.custom << 'EOF'
FROM doctown:latest

# Install additional Python packages
RUN pip install --no-cache-dir \
    matplotlib \
    pandas \
    numpy

# Add custom analysis scripts
COPY custom_tools.py /app/
EOF

docker build -f Dockerfile.custom -t doctown:custom .

# Use custom image
localdoc run my-data-project.docpack -i doctown:custom
```

## Example 8: Debugging and Troubleshooting

```bash
# Create docpack
localdoc ingest ~/test-project -o test.docpack

# Inspect without running
localdoc inspect test.docpack -v

# Validate structure
localdoc validate test.docpack

# Run with log following to see what's happening
localdoc run test.docpack -f

# If issues occur, check the .env file
cat .env | grep OPENAI_API_KEY

# Check Docker is running
docker ps

# Manually run Docker container for debugging
docker run --rm -it \
  --env-file .env \
  -v $(pwd)/test.docpack:/workspace \
  doctown:latest \
  /bin/bash
```

## Example 9: Creating Reusable Task Templates

```bash
# Create a template directory
mkdir -p ~/.doctown/templates

# Create a comprehensive documentation template
cat > ~/.doctown/templates/comprehensive-docs.json << 'EOF'
{
  "mission": "Generate comprehensive technical documentation",
  "tasks": [
    {
      "id": "overview",
      "name": "Project Overview",
      "description": "High-level project summary, purpose, and architecture",
      "output": {"type": "markdown", "path": "output/01-overview.md"}
    },
    {
      "id": "setup",
      "name": "Setup Instructions",
      "description": "Installation, configuration, and getting started guide",
      "output": {"type": "markdown", "path": "output/02-setup.md"}
    },
    {
      "id": "api",
      "name": "API Reference",
      "description": "Complete API documentation with examples",
      "output": {"type": "markdown", "path": "output/03-api-reference.md"}
    },
    {
      "id": "examples",
      "name": "Usage Examples",
      "description": "Common use cases and code examples",
      "output": {"type": "markdown", "path": "output/04-examples.md"}
    }
  ]
}
EOF

# Use the template
localdoc init my-project.docpack
cp ~/.doctown/templates/comprehensive-docs.json my-project.docpack/tasks.json
```

## Example 10: CI/CD Integration

```yaml
# .github/workflows/generate-docs.yml
name: Generate Documentation

on:
  push:
    branches: [main]

jobs:
  document:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable

      - name: Build localdoc CLI
        run: |
          cd cli
          cargo build --release

      - name: Create docpack
        run: |
          ./cli/target/release/localdoc ingest . \
            -o project.docpack \
            --all-tools \
            --build-index

      - name: Build Docker image
        run: docker build -t doctown:latest documenter/

      - name: Generate documentation
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          echo "OPENAI_API_KEY=$OPENAI_API_KEY" > .env
          ./cli/target/release/localdoc run project.docpack

      - name: Upload documentation
        uses: actions/upload-artifact@v3
        with:
          name: documentation
          path: project.docpack/output/
```

## Tips and Best Practices

### 1. Always validate before running
```bash
localdoc validate my.docpack && localdoc run my.docpack
```

### 2. Use inspect to check what was created
```bash
localdoc inspect my.docpack -v | less
```

### 3. Enable only needed tools for faster processing
```bash
# Minimal tools for simple text analysis
localdoc ingest ./code -o code.docpack
# (uses default: list_files, read_file, write_output)

# Full tools for complex documents with images/PDFs
localdoc ingest ./docs -o docs.docpack --all-tools
```

### 4. Build indexes for large codebases
```bash
localdoc ingest ./large-project \
  -o large.docpack \
  --build-index \
  --build-graph
```

### 5. Customize tasks for specific outputs
Always edit `tasks.json` after ingesting to get targeted documentation instead of generic exploration.
