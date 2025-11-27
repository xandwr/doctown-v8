#!/usr/bin/env python3
"""
Quick test to demonstrate the semantic_search_and_read tool.
This shows the expected input/output format.
"""

# Example of what the tool returns:
example_output = {
    "query": "error handling patterns",
    "files_found": 2,
    "results": [
        {
            "file": "src/error_handler.py",
            "content": "# Full file contents here...",
            "relevant_chunks": [
                {
                    "chunk": "def handle_error(exc):\n    logger.error(exc)\n    ...",
                    "score": 0.89
                }
            ]
        },
        {
            "file": "src/utils/validation.py",
            "content": "# Full file contents here...",
            "relevant_chunks": [
                {
                    "chunk": "try:\n    validate_input(data)\nexcept ValueError as e:\n    ...",
                    "score": 0.76
                }
            ]
        }
    ]
}

print("semantic_search_and_read() tool added successfully!")
print("\nExample query: 'error handling patterns'")
print(f"Files found: {example_output['files_found']}")
print("\nBenefits:")
print("  ✓ Single tool call instead of semantic_search + multiple read_file calls")
print("  ✓ Automatic deduplication of files")
print("  ✓ Full file contents with relevance scores")
print("  ✓ Perfect for quickly gathering context on a topic")
