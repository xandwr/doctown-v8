#!/usr/bin/env python3
"""
Test the sample_file functionality.
"""
import os
import tempfile
from pathlib import Path
from documenter.tools import DocpackTools


class MockSandbox:
    """Mock sandbox for testing."""
    def __init__(self, test_dir):
        self.workspace = Path(test_dir)
        self.files_dir = self.workspace
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
        return None

    def load_graph(self):
        return None

    def load_search_index(self):
        return None

    def load_tasks(self):
        return None


def test_sample_file():
    """Test sample_file on various file types."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create test files

        # 1. Small text file (CSV)
        csv_file = tmpdir / "data.csv"
        csv_file.write_text("date,price,volume\n2020-12-01,133.1,1000000\n2020-12-02,135.2,1200000\n")

        # 2. Large text file
        large_file = tmpdir / "large.log"
        with open(large_file, "w") as f:
            for i in range(10000):
                f.write(f"[2024-01-{i%31+1:02d}] INFO: Processing item {i}\n")

        # 3. Binary file (fake PNG)
        binary_file = tmpdir / "image.png"
        binary_file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 1000)

        # 4. UTF-8 text with special chars
        utf8_file = tmpdir / "unicode.txt"
        utf8_file.write_text("Hello 世界! 🚀 Testing unicode...\n" * 10, encoding='utf-8')

        # Create tools
        sandbox = MockSandbox(tmpdir)
        tools = DocpackTools(sandbox)

        print("=" * 70)
        print("TEST 1: Small CSV file (should read completely)")
        print("=" * 70)
        result = tools.sample_file("data.csv", max_bytes=512)
        print(f"File: {result['file']}")
        print(f"Total size: {result['total_size']} bytes")
        print(f"Sampled: {result['sampled_bytes']} bytes")
        print(f"Truncated: {result['is_truncated']}")
        print(f"Mode: {result['mode']}")
        print(f"Encoding: {result['encoding']}")
        print(f"Sample:\n{result['sample']}")
        print()

        print("=" * 70)
        print("TEST 2: Large log file (should be truncated)")
        print("=" * 70)
        result = tools.sample_file("large.log", max_bytes=1024)
        print(f"File: {result['file']}")
        print(f"Total size: {result['total_size']:,} bytes")
        print(f"Sampled: {result['sampled_bytes']} bytes")
        print(f"Truncated: {result['is_truncated']}")
        print(f"Mode: {result['mode']}")
        print(f"Sample (first 200 chars):\n{result['sample'][:200]}...")
        print()

        print("=" * 70)
        print("TEST 3: Binary file (PNG) - hex dump with magic bytes")
        print("=" * 70)
        result = tools.sample_file("image.png", max_bytes=128)
        print(f"File: {result['file']}")
        print(f"Total size: {result['total_size']} bytes")
        print(f"Mode: {result['mode']}")
        print(f"Detected type: {result.get('detected_type', 'unknown')}")
        print(f"Sample (first 10 lines):")
        print('\n'.join(result['sample'].split('\n')[:10]))
        print()

        print("=" * 70)
        print("TEST 4: Unicode text file")
        print("=" * 70)
        result = tools.sample_file("unicode.txt", max_bytes=256)
        print(f"File: {result['file']}")
        print(f"Mode: {result['mode']}")
        print(f"Encoding: {result['encoding']}")
        print(f"Sample:\n{result['sample'][:150]}...")
        print()

        print("=" * 70)
        print("TEST 5: Force binary mode on text file")
        print("=" * 70)
        result = tools.sample_file("data.csv", max_bytes=64, mode="binary")
        print(f"File: {result['file']}")
        print(f"Mode: {result['mode']}")
        print(f"Sample:\n{result['sample']}")
        print()

        print("✓ All tests completed!")


if __name__ == "__main__":
    test_sample_file()
