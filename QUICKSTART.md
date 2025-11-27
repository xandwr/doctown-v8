# Doctown Quick Start Guide

## 1. Initial Setup (One Time)

```bash
# Navigate to project
cd /home/xander/Documents/doctown-v8

# Set up environment
cd documenter
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY

# Build the Docker image
cd ..
./scripts/build.sh
```

## 2. Test with Example Docpack

```bash
# Run the agent with the example docpack
./scripts/run-local.sh

# Or use docker-compose
docker-compose up doctown-agent

# Check the output
cat example.docpack/output/architecture.md
cat example.docpack/output/api-reference.md
```

## 3. Create Your Own Docpack

### Option A: From a Code Repository

```bash
# Create docpack structure
mkdir my-app.docpack
cd my-app.docpack
mkdir files index output

# Copy your project files
cp -r ~/path/to/your/project/* files/

# Create manifest
cat > docpack.json << 'EOF'
{
  "version": "1.0",
  "name": "my-app",
  "description": "My application documentation",
  "environment": {
    "tools": ["list_files", "read_file", "write_output"]
  }
}
EOF

# Create tasks
cat > tasks.json << 'EOF'
{
  "mission": "Generate comprehensive documentation",
  "tasks": [
    {
      "id": "overview",
      "name": "Create project overview",
      "description": "Analyze and document the project structure",
      "output": {"type": "markdown", "path": "overview.md"}
    }
  ]
}
EOF

# Optionally create index files (graph.json, search.json)
# See DOCPACK_SPEC.md for schemas

# Run the agent
cd ..
docker run --rm --env-file documenter/.env \
  -v $(pwd)/my-app.docpack:/workspace \
  doctown:latest
```

### Option B: From PDFs/Documents

```bash
mkdir legal-docs.docpack
cd legal-docs.docpack
mkdir files index output

# Copy your documents
cp ~/Documents/*.pdf files/

# Create manifest (same as above)
# Create tasks focused on document analysis
cat > tasks.json << 'EOF'
{
  "mission": "Summarize legal documents",
  "tasks": [
    {
      "id": "summary",
      "name": "Create document summary",
      "description": "Extract key points from all documents",
      "output": {"type": "markdown", "path": "summary.md"}
    }
  ]
}
EOF

# Run (PDF reading not yet implemented, but same pattern)
```

## 4. Deploy to Production (RunPod)

```bash
# Tag and push your image
docker tag doctown:latest your-dockerhub/doctown:latest
docker push your-dockerhub/doctown:latest

# On RunPod:
# 1. Create pod with your image
# 2. Set environment variable: OPENAI_API_KEY
# 3. Mount volume at /workspace with your .docpack
# 4. Run container
# 5. Retrieve results from /workspace/output
```

## 5. Development Workflow

```bash
# Make changes to documenter/*.py
nano documenter/main.py

# Rebuild
./scripts/build.sh

# Test
./scripts/run-local.sh

# Check results
ls -la example.docpack/output/

# Iterate
```

## Key Files Reference

- `docpack.json` - Environment configuration
- `tasks.json` - Agent goals and outputs
- `index/graph.json` - Semantic graph (optional)
- `index/search.json` - Search index (optional)
- `files/` - Your content
- `output/` - Agent-generated results

## Troubleshooting

**Agent not starting:**
- Check `OPENAI_API_KEY` is set in `documenter/.env`
- Ensure `.docpack/docpack.json` exists and is valid JSON

**No output generated:**
- Check `tasks.json` has valid task definitions
- Look at container logs: `docker logs doctown-agent`
- Verify tools are enabled in `docpack.json`

**Path traversal errors:**
- Ensure all file paths in the agent's view are relative
- Don't use absolute paths or `..` in file references

**Out of tokens/time:**
- Reduce `max_file_reads` in `docpack.json`
- Break tasks into smaller pieces
- Use semantic index to guide agent instead of blind exploration

## Next Steps

1. Read [DOCPACK_SPEC.md](DOCPACK_SPEC.md) for complete format details
2. Explore [example.docpack/](example.docpack/) to see structure
3. Build a docpack builder tool (future enhancement)
4. Add semantic indexing for your specific domain
