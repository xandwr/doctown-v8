#!/bin/bash
# Run Doctown locally with the example docpack

set -e

# Check if .env exists
if [ ! -f "documenter/.env" ]; then
    echo "Error: documenter/.env not found"
    echo "Please copy documenter/.env.example to documenter/.env and add your API key"
    exit 1
fi

echo "Running Doctown agent with example.docpack..."
docker run --rm \
    --env-file documenter/.env \
    -v "$(pwd)/example.docpack:/workspace" \
    doctown:latest

echo ""
echo "✓ Agent finished!"
echo ""
echo "Check output:"
echo "  ls -la example.docpack/output/"
echo "  cat example.docpack/output/architecture.md"
