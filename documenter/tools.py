"""
Tool implementations for the agent.
These are the functions the agent can call to interact with the .docpack.
"""
import os
import json
import base64
import mimetypes
import io
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
from embeddings import EmbeddingSearcher
from parser import FunctionParser


class DocpackTools:
    """Collection of tools available to the agent."""

    def __init__(self, sandbox):
        self.sandbox = sandbox
        self._embedding_searcher = None
        self._function_parser = None

    def list_files(self, path="."):
        """List all files in a directory within the files/ area."""
        real = self.sandbox.resolve(path)
        if real is None:
            return {"error": "Path outside sandbox"}

        try:
            file_list = []
            for root, dirs, files in os.walk(real):
                for f in files:
                    full_path = Path(root) / f
                    rel = full_path.relative_to(self.sandbox.files_dir)
                    file_list.append(str(rel))
            return {"files": file_list}
        except Exception as e:
            return {"error": str(e)}

    def read_file(self, path):
        """Read a file from the files/ directory."""
        real = self.sandbox.resolve(path)
        if real is None:
            return {"error": "Path outside sandbox"}

        try:
            with open(real, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return {"content": content}
        except Exception as e:
            return {"error": str(e)}

    def sample_file(self, path, max_bytes=2048, mode="auto"):
        """
        Sample a file without loading the entire thing.
        The reconnaissance primitive for unknown files.

        This is how humans inspect files they don't understand:
        - head a CSV to see the schema
        - xxd a binary to check the magic bytes
        - peek a log file's first entries
        - check a PDF header
        - verify file encoding

        Perfect for:
        - Large files (datasets, logs, binaries)
        - Unknown file types
        - Quick inspection before deciding to read_file
        - Avoiding token explosions
        - Binary/noisy files you can't fully read

        Args:
            path: File to sample
            max_bytes: Maximum bytes to return (default: 2048)
            mode: "auto" (detect), "text" (force text), "binary" (hex dump)

        Returns:
            {
                "file": path,
                "sample": sample content,
                "total_size": file size in bytes,
                "sampled_bytes": actual bytes returned,
                "encoding": detected encoding,
                "is_truncated": whether file is larger than sample
            }
        """
        real = self.sandbox.resolve(path)
        if real is None:
            return {"error": "Path outside sandbox"}

        try:
            file_size = os.path.getsize(real)
            is_truncated = file_size > max_bytes

            # Read the sample
            with open(real, "rb") as f:
                sample_bytes = f.read(max_bytes)

            sampled_bytes = len(sample_bytes)

            # Detect if it's likely text or binary
            is_binary = b'\x00' in sample_bytes[:512]  # Null bytes suggest binary

            result = {
                "file": path,
                "total_size": file_size,
                "sampled_bytes": sampled_bytes,
                "is_truncated": is_truncated
            }

            # Auto-detect mode
            if mode == "auto":
                mode = "binary" if is_binary else "text"

            if mode == "text":
                # Try to decode as text
                try:
                    # Try common encodings
                    for encoding in ['utf-8', 'latin-1', 'cp1252']:
                        try:
                            sample_text = sample_bytes.decode(encoding)
                            result["sample"] = sample_text
                            result["encoding"] = encoding
                            result["mode"] = "text"
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # Fallback: decode with errors='replace'
                        sample_text = sample_bytes.decode('utf-8', errors='replace')
                        result["sample"] = sample_text
                        result["encoding"] = "utf-8 (lossy)"
                        result["mode"] = "text"
                except Exception as e:
                    return {"error": f"Failed to decode as text: {e}"}

            elif mode == "binary":
                # Return hex dump (similar to xxd)
                hex_lines = []
                for i in range(0, min(len(sample_bytes), 512), 16):  # Limit hex to first 512 bytes
                    chunk = sample_bytes[i:i+16]
                    hex_str = ' '.join(f'{b:02x}' for b in chunk)
                    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
                    hex_lines.append(f"{i:08x}  {hex_str:<48}  {ascii_str}")

                result["sample"] = '\n'.join(hex_lines)
                result["mode"] = "binary (hex dump)"
                result["encoding"] = "binary"

                # Try to detect file type from magic bytes
                if sample_bytes.startswith(b'\x89PNG'):
                    result["detected_type"] = "PNG image"
                elif sample_bytes.startswith(b'\xff\xd8\xff'):
                    result["detected_type"] = "JPEG image"
                elif sample_bytes.startswith(b'%PDF'):
                    result["detected_type"] = "PDF document"
                elif sample_bytes.startswith(b'PK\x03\x04'):
                    result["detected_type"] = "ZIP archive"
                elif sample_bytes.startswith(b'\x1f\x8b'):
                    result["detected_type"] = "GZIP compressed"
                elif sample_bytes.startswith(b'GIF8'):
                    result["detected_type"] = "GIF image"
                elif sample_bytes.startswith(b'\x7fELF'):
                    result["detected_type"] = "ELF executable"
                elif sample_bytes.startswith(b'MZ'):
                    result["detected_type"] = "PE executable (Windows)"

            return result

        except Exception as e:
            return {"error": str(e)}

    def read_image(self, path):
        """Read an image file and return it as base64 for vision analysis."""
        real = self.sandbox.resolve(path)
        if real is None:
            return {"error": "Path outside sandbox"}

        # Validate it's an image file
        mime_type, _ = mimetypes.guess_type(real)
        if not mime_type or not mime_type.startswith('image/'):
            return {"error": "File is not an image"}

        # Check supported formats
        supported = ['.png', '.jpg', '.jpeg', '.webp', '.gif']
        if not any(str(real).lower().endswith(ext) for ext in supported):
            return {"error": f"Unsupported image format. Supported: {', '.join(supported)}"}

        try:
            with open(real, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            return {
                "base64": image_data,
                "mime_type": mime_type,
                "path": path
            }
        except Exception as e:
            return {"error": str(e)}

    def read_pdf(self, path, page=1, dpi=200):
        """Read a PDF file, convert specified page to image, and return as base64 for OCR/vision analysis."""
        real = self.sandbox.resolve(path)
        if real is None:
            return {"error": "Path outside sandbox"}

        # Validate it's a PDF file
        if not str(real).lower().endswith('.pdf'):
            return {"error": "File is not a PDF"}

        try:
            # Convert PDF page to image
            images = convert_from_path(
                real, 
                dpi=dpi,
                first_page=page,
                last_page=page
            )
            
            if not images:
                return {"error": "Failed to convert PDF page"}
            
            # Convert PIL Image to base64
            img = images[0]
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return {
                "base64": image_data,
                "mime_type": "image/png",
                "path": path,
                "page": page,
                "format": "PDF converted to PNG"
            }
        except Exception as e:
            return {"error": str(e)}

    def search_code(self, query):
        """Search the code using the inverted index."""
        index = self.sandbox.load_search_index()
        if index is None:
            return {"error": "No search index available"}

        results = index.get("index", {}).get(query.lower(), [])
        return {"results": results}

    def query_graph(self, node_type=None, name=None):
        """Query the semantic graph for nodes."""
        graph = self.sandbox.load_graph()
        if graph is None:
            return {"error": "No graph available"}

        nodes = graph.get("nodes", [])

        # Filter by type if provided
        if node_type:
            nodes = [n for n in nodes if n.get("type") == node_type]

        # Filter by name if provided
        if name:
            nodes = [n for n in nodes if name.lower() in n.get("name", "").lower()]

        return {"nodes": nodes}

    def semantic_search(self, query, top_k=5):
        """
        Semantic search across the codebase using embeddings.
        Search by concepts, vibes, and intentions rather than exact keywords.

        Examples:
        - "error handling patterns"
        - "configuration loading"
        - "authentication flow"
        - "data validation logic"
        """
        # Lazy load the embedding searcher
        if self._embedding_searcher is None:
            self._embedding_searcher = EmbeddingSearcher(self.sandbox.index_dir)

        try:
            results = self._embedding_searcher.search(query, top_k=top_k)
            return {"results": results}
        except Exception as e:
            return {"error": str(e)}

    def semantic_search_and_read(self, query, max_results=5):
        """
        Semantic search + automatic file reading.
        One-shot tool to find and read relevant code.

        This combines semantic_search with read_file to provide
        full file contents for the most relevant matches, saving
        multiple round-trips. Perfect for quickly getting context
        on a topic.
        """
        search_results = self.semantic_search(query, top_k=max_results)

        if "error" in search_results:
            return search_results

        # Deduplicate by file
        files_to_read = {}
        for result in search_results["results"]:
            file = result["file"] # type: ignore
            if file not in files_to_read:
                files_to_read[file] = []
            files_to_read[file].append({
                "chunk": result["chunk"], # type: ignore
                "score": result["score"] # type: ignore
            })

        # Read each unique file
        outputs = []
        for file, chunks in files_to_read.items():
            content = self.read_file(file)
            outputs.append({
                "file": file,
                "content": content.get("content"),
                "relevant_chunks": chunks
            })

        return {
            "query": query,
            "files_found": len(outputs),
            "results": outputs
        }

    def semantic_outline(self, query, top_k=10, context_lines=5):
        """
        Give me a structured outline of the relevant sections across files.

        Performs semantic search and extracts code snippets around each match,
        producing a high-level outline that an LLM can quickly digest.

        Unlike semantic_search_and_read which returns full files, this returns
        targeted snippets, making it perfect for getting an overview across
        many locations without overwhelming context.

        Args:
            query: Natural language description of what you're looking for
            top_k: Number of results to return (default: 10)
            context_lines: Lines to show before/after the match (default: 5)
        """
        search_results = self.semantic_search(query, top_k=top_k)

        if "error" in search_results:
            return search_results

        # Group results by file
        files_map = {}
        for result in search_results["results"]:
            file = result["file"] # type: ignore
            if file not in files_map:
                files_map[file] = []
            files_map[file].append({
                "chunk": result["chunk"], # type: ignore
                "score": result["score"] # type: ignore
            })

        # Build outline by extracting snippets
        outline = []
        for file, chunks in files_map.items():
            # Read the file
            content = self.read_file(file)
            if "error" in content:
                continue

            file_content = content.get("content", "")
            lines = file_content.splitlines()

            sections = []
            for chunk_info in chunks:
                chunk_text = chunk_info["chunk"]
                score = chunk_info["score"]

                # Find the chunk in the file content
                line_num = self._find_chunk_line(lines, chunk_text)

                if line_num is not None:
                    # Extract snippet with context
                    start = max(0, line_num - context_lines)
                    end = min(len(lines), line_num + context_lines + 1)
                    snippet_lines = lines[start:end]
                    snippet = "\n".join(snippet_lines)

                    sections.append({
                        "line": line_num + 1,  # 1-indexed for user display
                        "snippet": snippet,
                        "score": score
                    })

            if sections:
                outline.append({
                    "file": file,
                    "sections": sections
                })

        return {
            "query": query,
            "outline": outline
        }

    def semantic_grep(self, query, top_k=10, context_lines=3):
        """
        Semantic ripgrep: returns only line-level snippets, not whole files.

        Think grep but semantic. Instead of returning entire files, this tool
        returns just the relevant code snippets with minimal context. Perfect
        for large repos where you need precision, not bulk.

        This cuts token usage by 100× compared to reading full files.

        Args:
            query: Natural language description of what to find
            top_k: Number of matches to return (default: 10)
            context_lines: Lines before/after each match (default: 3)

        Returns:
            List of snippets with file, line number, and code context
        """
        search_results = self.semantic_search(query, top_k=top_k)

        if "error" in search_results:
            return search_results

        snippets = []

        for result in search_results["results"]:
            file = result["file"] # type: ignore
            chunk_text = result["chunk"] # type: ignore
            score = result["score"] # type: ignore

            # Read the file
            content = self.read_file(file)
            if "error" in content:
                continue

            file_content = content.get("content", "")
            lines = file_content.splitlines()

            # Find where this chunk appears
            line_num = self._find_chunk_line(lines, chunk_text)

            if line_num is not None:
                # Extract snippet with context
                start = max(0, line_num - context_lines)
                end = min(len(lines), line_num + context_lines + 1)
                snippet_lines = lines[start:end]
                snippet = "\n".join(snippet_lines)

                snippets.append({
                    "file": file,
                    "line": line_num + 1,  # 1-indexed for display
                    "snippet": snippet,
                    "score": score
                })

        return {
            "query": query,
            "matches": len(snippets),
            "snippets": snippets
        }

    def semantic_neighbors(self, file, top_k=5):
        """
        Find files semantically similar to the given file.
        This is the inverse of semantic search.

        Instead of searching for a concept, you provide a file and get
        related files back. Perfect for multi-hop traversal and exploration:

        Examples:
        - "I'm reading universe.rs — what else relates to it?"
        - "What modules are similar to auth/session.rs?"
        - "Show me files related to renderer.py"

        The agent can explore code neighborhoods and discover related
        modules, dependencies, and architectural patterns.

        Args:
            file: Path to the file to find neighbors for
            top_k: Number of similar files to return (default: 5)

        Returns:
            List of similar files with similarity scores and representative chunks
        """
        # Lazy load the embedding searcher
        if self._embedding_searcher is None:
            self._embedding_searcher = EmbeddingSearcher(self.sandbox.index_dir)

        try:
            results = self._embedding_searcher.find_neighbors(file, top_k=top_k)
            return {"file": file, "neighbors": results}
        except Exception as e:
            return {"error": str(e)}

    def _find_chunk_line(self, lines, chunk_text):
        """
        Find the line number where a chunk appears in the file.
        Returns the first line of the chunk (0-indexed).
        """
        chunk_lines = chunk_text.strip().splitlines()
        if not chunk_lines:
            return None

        # Search for the first line of the chunk
        first_chunk_line = chunk_lines[0].strip()

        for i, line in enumerate(lines):
            if first_chunk_line in line.strip():
                # Found a potential match, verify by checking subsequent lines
                match = True
                for j, chunk_line in enumerate(chunk_lines):
                    if i + j >= len(lines):
                        match = False
                        break
                    if chunk_line.strip() not in lines[i + j].strip():
                        match = False
                        break

                if match:
                    return i

        # Fallback: just find first line
        for i, line in enumerate(lines):
            if first_chunk_line in line.strip():
                return i

        return None

    def search_text(self, query, path=".", case_sensitive=False, max_results=100):
        """
        Pure raw grep across files in the sandbox.

        Simple text search that stays within sandbox boundaries. No semantics,
        no embeddings - just good old grep. Fast and reliable for exact matches.

        Args:
            query: Text string to search for
            path: Directory to search in (default: ".", searches all files)
            case_sensitive: Whether to match case (default: False)
            max_results: Maximum number of matches to return (default: 100)

        Returns:
            {
                "query": "search term",
                "matches": 42,
                "results": [
                    {
                        "file": "path/to/file.py",
                        "line": 15,
                        "text": "    def search_text(query):",
                        "match": "search_text"
                    }
                ]
            }
        """
        real = self.sandbox.resolve(path)
        if real is None:
            return {"error": "Path outside sandbox"}

        try:
            results = []
            query_lower = query.lower() if not case_sensitive else query

            # Walk through all files
            for root, dirs, files in os.walk(real):
                for file in files:
                    file_path = Path(root) / file

                    # Skip binary files and common non-text files
                    skip_extensions = {'.pyc', '.pyo', '.so', '.dylib', '.dll',
                                     '.exe', '.bin', '.jpg', '.jpeg', '.png',
                                     '.gif', '.pdf', '.zip', '.tar', '.gz'}
                    if file_path.suffix.lower() in skip_extensions:
                        continue

                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                # Check if query matches
                                search_line = line if case_sensitive else line.lower()

                                if query_lower in search_line:
                                    # Get relative path from sandbox
                                    rel_path = file_path.relative_to(self.sandbox.files_dir)

                                    results.append({
                                        "file": str(rel_path),
                                        "line": line_num,
                                        "text": line.rstrip(),
                                        "match": query
                                    })

                                    if len(results) >= max_results:
                                        return {
                                            "query": query,
                                            "matches": len(results),
                                            "results": results,
                                            "truncated": True,
                                            "message": f"Stopped at {max_results} results. Increase max_results to see more."
                                        }
                    except (UnicodeDecodeError, PermissionError):
                        continue

            return {
                "query": query,
                "matches": len(results),
                "results": results
            }

        except Exception as e:
            return {"error": str(e)}

    def list_functions(self, path):
        """
        Parse a source file and extract all functions, methods, and classes.

        Uses tree-sitter for robust parsing (Python, Rust, JavaScript, TypeScript)
        with regex fallback. Returns symbolic information that makes LLMs 10×
        more reliable by providing precise locations and structure.

        Supported languages:
        - Python: functions, classes
        - Rust: functions, structs, impls, enums
        - JavaScript/TypeScript: functions, classes, methods

        Args:
            path: Relative path to source file

        Returns:
            {
                "file": "path/to/file.py",
                "language": "python",
                "symbols": [
                    {"name": "calculate_sum", "line": 10, "type": "function"},
                    {"name": "MyClass", "line": 42, "type": "class"}
                ]
            }
        """
        real = self.sandbox.resolve(path)
        if real is None:
            return {"error": "Path outside sandbox"}

        # Lazy load parser
        if self._function_parser is None:
            self._function_parser = FunctionParser()

        try:
            # Read file content
            with open(real, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Parse using tree-sitter
            result = self._function_parser.parse_file(Path(path), content)

            if result is None:
                return {
                    "error": f"Unsupported file type: {Path(path).suffix}",
                    "supported": [".py", ".rs", ".js", ".jsx", ".ts", ".tsx"]
                }

            return result

        except Exception as e:
            return {"error": str(e)}

    def docpack_metadata(self):
        """
        Expose all docpack metadata in one call.

        Returns comprehensive metadata about the docpack environment, including
        manifest info, available indexes, file statistics, and task definitions.
        This lets the agent write summaries without re-reading files.

        Perfect for:
        - Understanding the docpack structure at a glance
        - Writing documentation summaries
        - Analyzing scope and capabilities
        - Generating reports

        Returns:
            {
                "manifest": {...},          # Full docpack.json
                "statistics": {
                    "total_files": 42,
                    "file_types": {".py": 30, ".md": 12},
                    "total_size_bytes": 524288
                },
                "indexes": {
                    "has_graph": true,
                    "has_search_index": true,
                    "has_embeddings": true,
                    "graph_stats": {...},
                    "search_stats": {...}
                },
                "tasks": {...},             # tasks.json if available
                "environment": {...}        # Sandbox paths and constraints
            }
        """
        metadata = {
            "manifest": self.sandbox.manifest,
            "environment": {
                "workspace": str(self.sandbox.workspace),
                "files_dir": str(self.sandbox.files_dir),
                "index_dir": str(self.sandbox.index_dir),
                "output_dir": str(self.sandbox.output_dir)
            }
        }

        # Gather file statistics
        try:
            stats = {
                "total_files": 0,
                "file_types": {},
                "total_size_bytes": 0
            }

            for root, dirs, files in os.walk(self.sandbox.files_dir):
                for file in files:
                    file_path = Path(root) / file
                    stats["total_files"] += 1

                    # Track by extension
                    ext = file_path.suffix or "(no extension)"
                    stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1

                    # Track size
                    try:
                        stats["total_size_bytes"] += file_path.stat().st_size
                    except:
                        pass

            metadata["statistics"] = stats
        except Exception as e:
            metadata["statistics"] = {"error": str(e)}

        # Check available indexes
        indexes = {}

        # Graph
        graph = self.sandbox.load_graph()
        if graph:
            indexes["has_graph"] = True
            indexes["graph_stats"] = {
                "nodes": len(graph.get("nodes", [])),
                "edges": len(graph.get("edges", []))
            }
        else:
            indexes["has_graph"] = False

        # Search index
        search_index = self.sandbox.load_search_index()
        if search_index:
            indexes["has_search_index"] = True
            indexes["search_stats"] = search_index.get("metadata", {})
        else:
            indexes["has_search_index"] = False

        # Embeddings
        embeddings_path = self.sandbox.index_dir / "embeddings.json"
        if embeddings_path.exists():
            indexes["has_embeddings"] = True
            try:
                with open(embeddings_path, 'r') as f:
                    emb_data = json.load(f)
                indexes["embeddings_stats"] = emb_data.get("metadata", {})
            except:
                pass
        else:
            indexes["has_embeddings"] = False

        metadata["indexes"] = indexes

        # Load tasks if available
        tasks = self.sandbox.load_tasks()
        if tasks:
            metadata["tasks"] = tasks
        else:
            metadata["tasks"] = None

        return metadata

    def write_output(self, path, content):
        """Write content to the output/ directory."""
        real = self.sandbox.resolve_output(path)
        if real is None:
            return {"error": "Path outside output directory"}

        try:
            # Ensure parent directory exists
            Path(real).parent.mkdir(parents=True, exist_ok=True)

            with open(real, "w", encoding="utf-8") as f:
                f.write(content)

            return {"success": True, "path": path}
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self):
        """
        Return OpenAI-compatible tool definitions.
        By default, all tools are available. Manifests can optionally
        restrict to a subset via environment.tools array.
        """
        enabled_tools = self.sandbox.manifest.get("environment", {}).get("tools", None)

        all_tools = {
            "list_files": {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List all files in a directory within the project.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to list (default: '.')"
                            }
                        },
                        "required": []
                    }
                }
            },
            "read_file": {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a text file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to the file"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            "sample_file": {
                "type": "function",
                "function": {
                    "name": "sample_file",
                    "description": "Sample the first N bytes of a file without loading the entire thing. The reconnaissance primitive for unknown files - like 'head', 'xxd', or peeking at a file before committing to read it. Perfect for: large files (datasets, logs), unknown file types, binary files, checking encoding, avoiding token explosions, or quick inspection. Auto-detects text vs binary and provides appropriate output (text sample or hex dump with magic byte detection).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to the file to sample"
                            },
                            "max_bytes": {
                                "type": "integer",
                                "description": "Maximum bytes to return (default: 2048). For quick peek use 512, for CSV headers use 2048, for detailed inspection use 4096.",
                                "default": 2048
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["auto", "text", "binary"],
                                "description": "Sample mode: 'auto' (detect based on content), 'text' (force text decode), 'binary' (hex dump). Default: 'auto'",
                                "default": "auto"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            "search_code": {
                "type": "function",
                "function": {
                    "name": "search_code",
                    "description": "Search the codebase using the inverted index.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query term"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            "query_graph": {
                "type": "function",
                "function": {
                    "name": "query_graph",
                    "description": "Query the semantic graph for entities and relationships.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "node_type": {
                                "type": "string",
                                "description": "Filter by node type (file, symbol, cluster)"
                            },
                            "name": {
                                "type": "string",
                                "description": "Filter by name (partial match)"
                            }
                        },
                        "required": []
                    }
                }
            },
            "semantic_search": {
                "type": "function",
                "function": {
                    "name": "semantic_search",
                    "description": "Semantic search across the codebase using AI embeddings. Search by concepts, vibes, and intentions rather than exact keywords. Perfect for finding code related to abstract concepts like 'error handling', 'configuration', 'authentication', 'data validation', etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language description of what you're looking for (e.g., 'error handling patterns', 'authentication logic', 'database queries')"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results to return (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            "semantic_search_and_read": {
                "type": "function",
                "function": {
                    "name": "semantic_search_and_read",
                    "description": "One-shot semantic search that finds relevant code and automatically reads the full file contents. Combines semantic_search + read_file to save round-trips. Perfect for quickly gathering full context on a topic without multiple tool calls.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language description of what you're looking for (e.g., 'error handling patterns', 'authentication logic', 'database queries')"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of files to return (default: 3)",
                                "default": 3
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            "semantic_outline": {
                "type": "function",
                "function": {
                    "name": "semantic_outline",
                    "description": "Get a structured outline of relevant code sections across files. Performs semantic search and extracts targeted snippets (with surrounding context lines) instead of full files. Perfect for getting a high-level overview across many locations without overwhelming the context window.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language description of what you're looking for (e.g., 'GPU initialization', 'error handling patterns', 'authentication logic')"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results to return (default: 10)",
                                "default": 10
                            },
                            "context_lines": {
                                "type": "integer",
                                "description": "Number of lines to show before/after each match (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            "semantic_grep": {
                "type": "function",
                "function": {
                    "name": "semantic_grep",
                    "description": "Semantic ripgrep - returns only line-level snippets, not whole files. Like grep but semantic. Instead of returning entire files, gives you just the relevant code snippets with minimal context. Cuts token usage by 100× in large repos. Perfect when you need precision, not bulk.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language description of what to find (e.g., 'error handling', 'JWT validation', 'database connection pooling')"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of matches to return (default: 10)",
                                "default": 10
                            },
                            "context_lines": {
                                "type": "integer",
                                "description": "Lines of context before/after each match (default: 3)",
                                "default": 3
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            "semantic_neighbors": {
                "type": "function",
                "function": {
                    "name": "semantic_neighbors",
                    "description": "Find files semantically similar to a given file. This is the inverse of semantic search - instead of searching for concepts, you provide a file and discover related files. Perfect for multi-hop code exploration: 'I'm reading universe.rs — what else relates to it?' or 'What modules are similar to auth/session.rs?'. Enables the agent to explore code neighborhoods and discover related modules.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file": {
                                "type": "string",
                                "description": "Path to the file to find neighbors for (e.g., 'src/auth/session.rs', 'lib/renderer.py')"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of similar files to return (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["file"]
                    }
                }
            },
            "search_text": {
                "type": "function",
                "function": {
                    "name": "search_text",
                    "description": "Pure raw grep across files in the sandbox. Simple text search for exact matches - no semantics, no embeddings, just fast grep. Perfect for finding exact strings, identifiers, or error messages.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Text string to search for (e.g., 'TODO', 'import pandas', 'def calculate')"
                            },
                            "path": {
                                "type": "string",
                                "description": "Directory to search in (default: '.', searches all files)"
                            },
                            "case_sensitive": {
                                "type": "boolean",
                                "description": "Whether to match case exactly (default: False)"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of matches to return (default: 100)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            "list_functions": {
                "type": "function",
                "function": {
                    "name": "list_functions",
                    "description": "Parse a source file and extract all functions, methods, classes, and other symbols with their line numbers. Uses tree-sitter for robust parsing (Python/Rust/JS/TS) with regex fallback. Returns symbolic information that makes LLMs 10× more reliable by providing precise locations and code structure.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to source file (.py, .rs, .js, .jsx, .ts, .tsx)"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            "docpack_metadata": {
                "type": "function",
                "function": {
                    "name": "docpack_metadata",
                    "description": "Get comprehensive metadata about the entire docpack in one call. Returns manifest, file statistics, available indexes, and tasks. Perfect for understanding the docpack structure at a glance or writing summaries without re-reading files.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "write_output": {
                "type": "function",
                "function": {
                    "name": "write_output",
                    "description": "Write content to an output file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path for the output file"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write"
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            "read_image": {
                "type": "function",
                "function": {
                    "name": "read_image",
                    "description": "Read an image file (PNG, JPEG, WEBP, GIF) for vision/OCR analysis. Returns base64-encoded image data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to the image file"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            "read_pdf": {
                "type": "function",
                "function": {
                    "name": "read_pdf",
                    "description": "Read a PDF file, convert a page to image, and return for OCR/vision analysis. Useful for extracting text and analyzing diagrams from PDFs.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to the PDF file"
                            },
                            "page": {
                                "type": "integer",
                                "description": "Page number to read (default: 1)",
                                "default": 1
                            },
                            "dpi": {
                                "type": "integer",
                                "description": "DPI for image conversion (default: 200, higher = better quality but slower)",
                                "default": 200
                            }
                        },
                        "required": ["path"]
                    }
                }
            }
        }

        # If no tools specified in manifest, enable all tools
        if enabled_tools is None:
            return list(all_tools.values())
        
        # Otherwise, return only the specified tools
        return [all_tools[tool] for tool in enabled_tools if tool in all_tools]

    def execute(self, tool_name, args):
        """Execute a tool by name with given arguments."""
        method = getattr(self, tool_name, None)
        if method is None:
            return {"error": f"Unknown tool: {tool_name}"}

        return method(**args)
