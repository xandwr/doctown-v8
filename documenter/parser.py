"""
Function/class extraction using tree-sitter for multiple languages.
Provides symbolic information to make LLMs 10× more reliable.
"""
from pathlib import Path
from typing import List, Dict, Optional
import re


class FunctionParser:
    """Parse functions, methods, and classes from source files."""

    def __init__(self):
        self._parsers = {}
        self._queries = {}

    def _get_language_parser(self, language: str):
        """Lazy load tree-sitter parser for a language."""
        if language not in self._parsers:
            try:
                from tree_sitter import Language, Parser

                # Import language bindings
                if language == "python":
                    import tree_sitter_python as tspython
                    ts_language = Language(tspython.language())
                elif language == "rust":
                    import tree_sitter_rust as tsrust
                    ts_language = Language(tsrust.language())
                elif language == "javascript":
                    import tree_sitter_javascript as tsjs
                    ts_language = Language(tsjs.language())
                elif language == "typescript":
                    import tree_sitter_typescript as tsts
                    ts_language = Language(tsts.language_typescript())
                else:
                    return None

                parser = Parser(ts_language)
                self._parsers[language] = (parser, ts_language)
            except ImportError:
                return None

        return self._parsers.get(language)

    def _get_query(self, language: str, ts_language):
        """Get tree-sitter query for extracting functions/classes."""
        if language in self._queries:
            return self._queries[language]

        # Define queries for each language
        queries = {
            "python": """
                (function_definition
                    name: (identifier) @function.name) @function.def
                (class_definition
                    name: (identifier) @class.name) @class.def
            """,
            "rust": """
                (function_item
                    name: (identifier) @function.name) @function.def
                (impl_item
                    type: (type_identifier) @impl.name) @impl.def
                (struct_item
                    name: (type_identifier) @struct.name) @struct.def
                (enum_item
                    name: (type_identifier) @enum.name) @enum.def
            """,
            "javascript": """
                (function_declaration
                    name: (identifier) @function.name) @function.def
                (method_definition
                    name: (property_identifier) @method.name) @method.def
                (class_declaration
                    name: (identifier) @class.name) @class.def
            """,
            "typescript": """
                (function_declaration
                    name: (identifier) @function.name) @function.def
                (method_definition
                    name: (property_identifier) @method.name) @method.def
                (class_declaration
                    name: (type_identifier) @class.name) @class.def
                (interface_declaration
                    name: (type_identifier) @interface.name) @interface.def
            """
        }

        query_text = queries.get(language)
        if query_text:
            query = ts_language.query(query_text)
            self._queries[language] = query
            return query

        return None

    def parse_file(self, file_path: Path, content: str) -> Optional[Dict]:
        """
        Parse a file and extract functions, methods, and classes.

        Args:
            file_path: Path to the file (used to determine language)
            content: File content as string

        Returns:
            Dict with file info and list of symbols, or None if parsing fails
        """
        # Detect language from extension
        ext = file_path.suffix.lower()
        language_map = {
            '.py': 'python',
            '.rs': 'rust',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
        }

        language = language_map.get(ext)
        if not language:
            return None

        # Try tree-sitter parsing first
        parser_info = self._get_language_parser(language)
        if parser_info:
            parser, ts_language = parser_info
            query = self._get_query(language, ts_language)

            if query:
                try:
                    tree = parser.parse(bytes(content, "utf8"))
                    captures = query.captures(tree.root_node)

                    symbols = []
                    seen = set()  # Deduplicate by (name, line)

                    for node, capture_name in captures:
                        if ".name" in capture_name:
                            name = node.text.decode('utf8')
                            line = node.start_point[0] + 1  # 1-indexed

                            # Determine symbol type
                            symbol_type = capture_name.split('.')[0]

                            key = (name, line, symbol_type)
                            if key not in seen:
                                symbols.append({
                                    "name": name,
                                    "line": line,
                                    "type": symbol_type
                                })
                                seen.add(key)

                    return {
                        "file": str(file_path),
                        "language": language,
                        "symbols": sorted(symbols, key=lambda x: x["line"])
                    }
                except Exception:
                    pass

        # Fallback to regex parsing if tree-sitter fails
        return self._regex_parse(file_path, content, language)

    def _regex_parse(self, file_path: Path, content: str, language: str) -> Dict:
        """Fallback regex-based parsing when tree-sitter is unavailable."""
        symbols = []
        lines = content.split('\n')

        if language == 'python':
            # Match: def function_name( or class ClassName:
            for i, line in enumerate(lines, 1):
                # Functions
                match = re.match(r'^\s*def\s+(\w+)\s*\(', line)
                if match:
                    symbols.append({
                        "name": match.group(1),
                        "line": i,
                        "type": "function"
                    })
                # Classes
                match = re.match(r'^\s*class\s+(\w+)', line)
                if match:
                    symbols.append({
                        "name": match.group(1),
                        "line": i,
                        "type": "class"
                    })

        elif language == 'rust':
            # Match: fn function_name, struct Name, impl Name, enum Name
            for i, line in enumerate(lines, 1):
                # Functions
                match = re.match(r'^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)', line)
                if match:
                    symbols.append({
                        "name": match.group(1),
                        "line": i,
                        "type": "function"
                    })
                # Structs
                match = re.match(r'^\s*(?:pub\s+)?struct\s+(\w+)', line)
                if match:
                    symbols.append({
                        "name": match.group(1),
                        "line": i,
                        "type": "struct"
                    })
                # Impls
                match = re.match(r'^\s*impl\s+(\w+)', line)
                if match:
                    symbols.append({
                        "name": match.group(1),
                        "line": i,
                        "type": "impl"
                    })
                # Enums
                match = re.match(r'^\s*(?:pub\s+)?enum\s+(\w+)', line)
                if match:
                    symbols.append({
                        "name": match.group(1),
                        "line": i,
                        "type": "enum"
                    })

        elif language in ('javascript', 'typescript'):
            # Match: function name, class Name, async function name
            for i, line in enumerate(lines, 1):
                # Functions
                match = re.match(r'^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)', line)
                if match:
                    symbols.append({
                        "name": match.group(1),
                        "line": i,
                        "type": "function"
                    })
                # Classes
                match = re.match(r'^\s*(?:export\s+)?class\s+(\w+)', line)
                if match:
                    symbols.append({
                        "name": match.group(1),
                        "line": i,
                        "type": "class"
                    })
                # Arrow functions (const name = )
                match = re.match(r'^\s*(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(', line)
                if match:
                    symbols.append({
                        "name": match.group(1),
                        "line": i,
                        "type": "function"
                    })

        return {
            "file": str(file_path),
            "language": language,
            "symbols": symbols
        }
