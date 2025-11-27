#!/usr/bin/env python3
"""
Quick test for semantic_neighbors functionality.
"""
from pathlib import Path
from documenter.tools import DocpackTools


class MockSandbox:
    """Mock sandbox for testing."""
    def __init__(self, workspace_path):
        self.workspace = Path(workspace_path)
        self.files_dir = self.workspace / "files"
        self.index_dir = self.workspace / "index"
        self.output_dir = self.workspace / "output"
        self.manifest = {}

    def resolve(self, path):
        """Resolve a path within the sandbox."""
        target = (self.files_dir / path).resolve()
        if target.is_relative_to(self.files_dir):
            return target
        return None

    def resolve_output(self, path):
        """Resolve an output path."""
        target = (self.output_dir / path).resolve()
        if target.is_relative_to(self.output_dir):
            return target
        return None

    def load_graph(self):
        return None

    def load_search_index(self):
        return None

    def load_tasks(self):
        return None


def test_semantic_neighbors():
    """Test the semantic_neighbors tool."""
    # You'll need a real docpack with embeddings to test this
    docpack_path = input("Enter path to a docpack with embeddings: ")

    if not Path(docpack_path).exists():
        print(f"Error: {docpack_path} does not exist")
        return

    # Create tools
    sandbox = MockSandbox(docpack_path)
    tools = DocpackTools(sandbox)

    # Get a file from the user
    file_path = input("Enter a file path to find neighbors for: ")

    print(f"\nFinding neighbors for {file_path}...\n")

    result = tools.semantic_neighbors(file=file_path, top_k=5)

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print(f"File: {result['file']}")
    print(f"\nTop {len(result['neighbors'])} similar files:\n")

    for i, neighbor in enumerate(result['neighbors'], 1):
        print(f"{i}. {neighbor['file']} (score: {neighbor['score']:.4f})")
        print(f"   Representative chunk: {neighbor['representative_chunk'][:100]}...")
        print()


if __name__ == "__main__":
    test_semantic_neighbors()
