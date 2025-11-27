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


class DocpackTools:
    """Collection of tools available to the agent."""

    def __init__(self, sandbox):
        self.sandbox = sandbox
        self._embedding_searcher = None

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
