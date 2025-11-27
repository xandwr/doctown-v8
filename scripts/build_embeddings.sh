#!/bin/bash
# Build semantic search embeddings for a .docpack

if [ $# -ne 1 ]; then
    echo "Usage: $0 <path-to-docpack>"
    exit 1
fi

DOCPACK_PATH="$1"

if [ ! -d "$DOCPACK_PATH" ]; then
    echo "Error: Directory $DOCPACK_PATH does not exist"
    exit 1
fi

cd "$(dirname "$0")/../documenter"

echo "Building embeddings for $DOCPACK_PATH..."
python3 embeddings.py "$DOCPACK_PATH"
