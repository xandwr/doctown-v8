#!/usr/bin/env python3
"""
Test the docpack_metadata tool to see all metadata at once.
"""
from pathlib import Path
from documenter.sandbox import Sandbox
from documenter.tools import DocpackTools
import json


def test_docpack_metadata():
    # Use the current project as a test docpack
    test_docpack = Path("test.docpack")

    if not test_docpack.exists():
        print("Error: test.docpack not found. Please create a test docpack first.")
        print("Run: doctown ingest <source> -o test.docpack")
        return

    # Initialize sandbox and tools
    sandbox = Sandbox(test_docpack)
    tools = DocpackTools(sandbox)

    print("Testing docpack_metadata...")
    print("=" * 70)

    result = tools.docpack_metadata()

    # Display formatted metadata
    print("\n📦 DOCPACK OVERVIEW")
    print("=" * 70)

    # Manifest
    if "manifest" in result:
        manifest = result["manifest"]
        print(f"\nName: {manifest.get('name', 'N/A')}")
        print(f"Description: {manifest.get('description', 'N/A')}")
        print(f"Version: {manifest.get('version', 'N/A')}")

    # Statistics
    if "statistics" in result:
        stats = result["statistics"]
        print(f"\n📊 STATISTICS")
        print(f"  Total files: {stats.get('total_files', 0)}")
        print(f"  Total size: {stats.get('total_size_bytes', 0):,} bytes")
        print(f"\n  File types:")
        for ext, count in sorted(stats.get('file_types', {}).items()):
            print(f"    {ext:20s} {count:4d} files")

    # Indexes
    if "indexes" in result:
        indexes = result["indexes"]
        print(f"\n🔍 INDEXES")
        print(f"  Graph index: {'✓' if indexes.get('has_graph') else '✗'}")
        if indexes.get('has_graph'):
            graph_stats = indexes.get('graph_stats', {})
            print(f"    - Nodes: {graph_stats.get('nodes', 0)}")
            print(f"    - Edges: {graph_stats.get('edges', 0)}")

        print(f"  Search index: {'✓' if indexes.get('has_search_index') else '✗'}")
        if indexes.get('has_search_index'):
            search_stats = indexes.get('search_stats', {})
            print(f"    - Total files: {search_stats.get('total_files', 0)}")
            print(f"    - Total symbols: {search_stats.get('total_symbols', 0)}")

        print(f"  Embeddings: {'✓' if indexes.get('has_embeddings') else '✗'}")
        if indexes.get('has_embeddings'):
            emb_stats = indexes.get('embeddings_stats', {})
            print(f"    - Chunks: {emb_stats.get('chunk_count', 0)}")
            print(f"    - Model: {emb_stats.get('model', 'N/A')}")

    # Tasks
    if "tasks" in result and result["tasks"]:
        tasks = result["tasks"]
        print(f"\n📋 TASKS")
        print(f"  Goal: {tasks.get('goal', 'N/A')}")
        print(f"  Deliverables: {len(tasks.get('deliverables', []))}")

    # Environment
    if "environment" in result:
        env = result["environment"]
        print(f"\n🔧 ENVIRONMENT")
        print(f"  Workspace: {env.get('workspace')}")
        print(f"  Files dir: {env.get('files_dir')}")
        print(f"  Index dir: {env.get('index_dir')}")
        print(f"  Output dir: {env.get('output_dir')}")

    print("\n" + "=" * 70)
    print("✓ docpack_metadata test completed!")

    # Show why this is useful
    print("\n" + "=" * 70)
    print("💡 WHY THIS IS USEFUL")
    print("=" * 70)
    print("""
Agent workflow WITHOUT docpack_metadata:
  1. Call list_files() to see what's there
  2. Call read_file() on manifest
  3. Manually check each index file
  4. Count files manually
  5. Read tasks.json separately
  → Many tool calls, lots of tokens

Agent workflow WITH docpack_metadata:
  1. Call docpack_metadata()
  → Everything in one shot!

Perfect for:
  - Writing summaries
  - Understanding scope
  - Generating reports
  - Quick overview before deep dive
""")


if __name__ == "__main__":
    test_docpack_metadata()
