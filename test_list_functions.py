#!/usr/bin/env python3
"""
Test the list_functions tool to ensure it correctly extracts symbols.
"""
from pathlib import Path
from documenter.sandbox import Sandbox
from documenter.tools import DocpackTools
import json


def test_list_functions():
    # Use the current project as a test docpack
    test_docpack = Path("test.docpack")

    if not test_docpack.exists():
        print("Error: test.docpack not found. Please create a test docpack first.")
        print("Run: doctown ingest <source> -o test.docpack")
        return

    # Initialize sandbox and tools
    sandbox = Sandbox(test_docpack)
    tools = DocpackTools(sandbox)

    print("Testing list_functions...")
    print("=" * 70)

    # Test on different file types
    test_files = [
        "tools.py",           # Python
        "parser.py",          # Python
        "embeddings.py",      # Python
    ]

    for file_path in test_files:
        print(f"\n📄 Parsing: {file_path}")
        print("-" * 70)

        result = tools.list_functions(file_path)

        if "error" in result:
            print(f"❌ Error: {result['error']}")
            continue

        print(f"Language: {result['language']}")
        print(f"Total symbols: {len(result['symbols'])}\n")

        # Group by type
        by_type = {}
        for symbol in result['symbols']:
            sym_type = symbol['type']
            if sym_type not in by_type:
                by_type[sym_type] = []
            by_type[sym_type].append(symbol)

        # Display grouped results
        for sym_type, symbols in sorted(by_type.items()):
            print(f"{sym_type.upper()}S ({len(symbols)}):")
            for sym in symbols[:10]:  # Show first 10 of each type
                print(f"  • {sym['name']:40s} @ line {sym['line']:4d}")
            if len(symbols) > 10:
                print(f"  ... and {len(symbols) - 10} more")
            print()

    # Demonstrate symbolic navigation
    print("\n" + "=" * 70)
    print("Example: Symbolic Navigation")
    print("=" * 70)

    result = tools.list_functions("tools.py")
    if "symbols" in result:
        print("\nAgent can now ask: 'Read lines 145-165 of tools.py'")
        print("Instead of: 'Read the entire tools.py file'")
        print("\nSample function references:")
        for sym in result['symbols'][:5]:
            print(f"  {result['file']}:{sym['line']} - {sym['type']} {sym['name']}")

    print("\n✓ list_functions test completed!")


def test_parser_directly():
    """Test the parser module directly on this file."""
    from documenter.parser import FunctionParser

    print("\n" + "=" * 70)
    print("Direct Parser Test (on this test file)")
    print("=" * 70)

    parser = FunctionParser()
    with open(__file__, 'r') as f:
        content = f.read()

    result = parser.parse_file(Path(__file__), content)

    if result:
        print(f"\nFile: {result['file']}")
        print(f"Language: {result['language']}")
        print(f"Symbols found: {len(result['symbols'])}\n")

        for sym in result['symbols']:
            print(f"  {sym['type']:10s} {sym['name']:30s} @ line {sym['line']}")


if __name__ == "__main__":
    # Test with docpack
    test_list_functions()

    # Test parser directly
    test_parser_directly()
