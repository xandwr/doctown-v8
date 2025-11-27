#!/bin/bash
# Build the Doctown Docker image

set -e

echo "Building Doctown agent image..."
docker build -t doctown:latest documenter/

echo "✓ Build complete!"
echo ""
echo "To run locally:"
echo "  docker-compose up"
echo ""
echo "To push to registry:"
echo "  docker tag doctown:latest YOUR_REGISTRY/doctown:latest"
echo "  docker push YOUR_REGISTRY/doctown:latest"
