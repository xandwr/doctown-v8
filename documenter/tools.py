"""
Tool implementations for the agent.
These are the functions the agent can call to interact with the .docpack.
"""
import os
import json
from pathlib import Path


class DocpackTools:
    """Collection of tools available to the agent."""

    def __init__(self, sandbox):
        self.sandbox = sandbox

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
        Return OpenAI-compatible tool definitions based on what's
        enabled in the docpack manifest.
        """
        enabled_tools = self.sandbox.manifest.get("environment", {}).get("tools", [])

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
            }
        }

        # Return only enabled tools
        return [all_tools[tool] for tool in enabled_tools if tool in all_tools]

    def execute(self, tool_name, args):
        """Execute a tool by name with given arguments."""
        method = getattr(self, tool_name, None)
        if method is None:
            return {"error": f"Unknown tool: {tool_name}"}

        return method(**args)
