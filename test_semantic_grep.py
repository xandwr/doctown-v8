#!/usr/bin/env python3
"""
Test the semantic_grep tool to ensure it returns line-level snippets.
"""
from pathlib import Path
from documenter.sandbox import Sandbox
from documenter.tools import DocpackTools


def test_semantic_grep():
    # Use the current project as a test docpack
    test_docpack = Path("test.docpack")

    if not test_docpack.exists():
        print("Error: test.docpack not found. Please create a test docpack first.")
        print("Run: doctown ingest <source> -o test.docpack")
        return

    # Initialize sandbox and tools
    sandbox = Sandbox(test_docpack)
    tools = DocpackTools(sandbox)

    # Test semantic_grep
    print("Testing semantic_grep...")
    print("=" * 60)

    query = "semantic search implementation"
    result = tools.semantic_grep(query, top_k=5, context_lines=3)

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print(f"Query: {query}")
    print(f"Matches found: {result['matches']}")
    print()

    for i, snippet in enumerate(result["snippets"], 1):
        print(f"Match {i}:")
        print(f"  File: {snippet['file']}")
        print(f"  Line: {snippet['line']}")
        print(f"  Score: {snippet['score']:.4f}")
        print(f"  Snippet:")
        print("  " + "-" * 58)
        for line in snippet['snippet'].split('\n'):
            print(f"  {line}")
        print("  " + "-" * 58)
        print()

    # Compare token usage
    print("\n" + "=" * 60)
    print("Token usage comparison:")
    print("=" * 60)

    snippet_chars = sum(len(s['snippet']) for s in result['snippets'])
    print(f"semantic_grep output: ~{snippet_chars} characters")

    # Estimate full file read
    files_mentioned = set(s['file'] for s in result['snippets'])
    total_file_chars = 0
    for file in files_mentioned:
        content = tools.read_file(file)
        if 'content' in content:
            total_file_chars += len(content['content'])

    print(f"Full file read would be: ~{total_file_chars} characters")

    if total_file_chars > 0:
        reduction = (1 - snippet_chars / total_file_chars) * 100
        print(f"Token reduction: ~{reduction:.1f}%")

    print("\n✓ semantic_grep test completed!")


if __name__ == "__main__":
    test_semantic_grep()
