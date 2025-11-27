# Doctown Web Interface

Dead simple localhost interface for generating and browsing .docpack documentation.

## What It Does

1. **Upload** - Drag & drop a .zip file containing your codebase (or whatever)
2. **Process** - AI agent pipeline automatically generates documentation
3. **Browse** - Explore generated .docpack files with a clean interface
4. **View** - Read through source files and AI-generated documentation

## Quick Start

### Prerequisites

1. Docker running (for the documenter agent)
2. Rust/Cargo installed (for the CLI)
3. Node.js installed (for the web interface)
4. `.env` file in project root with `OPENAI_API_KEY=your-key-here`

### Build the Docker Image

```bash
# From project root
docker build -t doctown:latest ./documenter
```

### Run the Web Interface

```bash
# Install dependencies
npm install

# Start dev server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## How It Works

### Upload Flow

1. User uploads a .zip file
2. File is extracted to `~/.localdoc/temp/{id}/`
3. `localdoc ingest` creates a .docpack structure
4. `localdoc run` executes the AI agent in Docker
5. Generated .docpack saved to `~/.localdoc/outputs/`

### File Structure

```
~/.localdoc/
├── temp/           # Temporary upload/extraction
└── docpacks/        # Generated .docpack files
    └── myproject-abc123.docpack/
        ├── docpack.json    # Manifest
        ├── tasks.json      # AI agent tasks
        ├── files/          # Source files
        ├── index/          # Search index
        └── output/         # Generated docs
```

## Pages

- `/` - Upload interface
- `/browse` - List all docpacks
- `/docpack/[id]` - View specific docpack

## API Routes

- `POST /api/upload` - Handle zip upload & processing
- `GET /api/docpacks` - List all docpacks
- `GET /api/docpack/[id]` - Get docpack metadata
- `GET /api/docpack/[id]/file?path=...` - Read file content

## Development

```bash
# Type checking
npm run check

# Build for production
npm run build

# Preview production build
npm run preview
```

## Notes

- All processing happens locally on your machine
- No cloud storage (for now)
- Docker container runs in isolated sandbox
- .docpack files are deterministic and portable

## Future Ideas

- WebSocket progress updates during processing
- Real-time log streaming
- Markdown rendering for output files
- Syntax highlighting for source files
- Download .docpack as archive
- Share docpacks via links
- R2 storage integration
