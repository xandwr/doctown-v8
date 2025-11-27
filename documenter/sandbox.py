import os
import json
from pathlib import Path

class Sandbox:
    """
    Sandbox for agent execution within a .docpack environment.
    In Docker, this points to /workspace where the .docpack is mounted.
    """
    def __init__(self, workspace_path=None):
        # Use env var or default to /workspace (Docker mount point)
        self.workspace = Path(workspace_path or os.getenv("WORKSPACE_PATH", "/workspace"))

        # Key directories within the .docpack
        self.files_dir = self.workspace / "files"
        self.index_dir = self.workspace / "index"
        self.output_dir = self.workspace / "output"

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load docpack manifest
        self.manifest = self._load_manifest()

    def _load_manifest(self):
        """Load the docpack.json manifest."""
        manifest_path = self.workspace / "docpack.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"No docpack.json found at {manifest_path}")

        with open(manifest_path, "r") as f:
            return json.load(f)

    def resolve(self, user_path):
        """
        Resolve agent-provided relative paths safely inside files/.
        Prevents traversal outside the sandbox.
        """
        # Resolve relative to files/ directory
        candidate = (self.files_dir / user_path).resolve()

        # Ensure it's within files/
        try:
            candidate.relative_to(self.files_dir)
            return str(candidate)
        except ValueError:
            return None

    def resolve_output(self, user_path):
        """
        Resolve output paths safely inside output/.
        """
        candidate = (self.output_dir / user_path).resolve()

        try:
            candidate.relative_to(self.output_dir)
            return str(candidate)
        except ValueError:
            return None

    def get_index_file(self, filename):
        """Get path to an index file (graph.json, search.json, etc.)."""
        path = self.index_dir / filename
        return str(path) if path.exists() else None

    def load_tasks(self):
        """Load the tasks.json file."""
        tasks_path = self.workspace / "tasks.json"
        if not tasks_path.exists():
            return None

        with open(tasks_path, "r") as f:
            return json.load(f)

    def load_graph(self):
        """Load the semantic graph."""
        graph_path = self.index_dir / "graph.json"
        if not graph_path.exists():
            return None

        with open(graph_path, "r") as f:
            return json.load(f)

    def load_search_index(self):
        """Load the search index."""
        search_path = self.index_dir / "search.json"
        if not search_path.exists():
            return None

        with open(search_path, "r") as f:
            return json.load(f)
