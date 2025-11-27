#!/bin/bash

echo "🚀 Starting Doctown Web Interface"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Create a .env file with your OPENAI_API_KEY"
    echo ""
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "⚠️  Warning: Docker is not running!"
    echo "Start Docker to enable document generation"
    echo ""
fi

# Build Docker image if it doesn't exist
if ! docker images | grep -q "doctown.*latest"; then
    echo "📦 Building Docker image (first time only)..."
    docker build -t doctown:latest ./documenter
    echo ""
fi

# Create output directory
mkdir -p ~/.localdoc/outputs
mkdir -p ~/.localdoc/temp

echo "📁 Storage locations:"
echo "   Temp:    ~/.localdoc/temp"
echo "   Outputs: ~/.localdoc/outputs"
echo ""

# Start the dev server
echo "🌐 Starting web interface..."
echo "   URL: http://localhost:5173"
echo ""

cd website && npm run dev
