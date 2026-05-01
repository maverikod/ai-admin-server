#!/usr/bin/env python3
"""
Script to move all imports to the beginning of Python files.

This script finds all import statements in Python files and moves them
to the beginning of the file, maintaining proper order and grouping.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Set


class ImportExtractor(ast.NodeVisitor):
    """Extract all import statements from AST."""
    
    def __init__(self):
        self.imports: List[Tuple[int, str, str]] = []  # (line, type, content)
        self.docstring_lines: Set[int] = set()
    
    def visit_Import(self, node):
        """Visit import statements."""
        content = ast.unparse(node)
        self.imports.append((node.lineno, "import", content))
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Visit from import statements."""
        content = ast.unparse(node)
        self.imports.append((node.lineno, "from", content))
        self.generic_visit(node)
    
    def visit_Expr(self, node):
        """Track docstring lines."""
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            # This is likely a docstring
            self.docstring_lines.add(node.lineno)
        self.generic_visit(node)


def extract_imports_from_file(file_path: Path) -> Tuple[List[str], List[str], int]:
    """
    Extract imports from a Python file.
    
    Returns:
        Tuple of (standard_imports, third_party_imports, local_imports, docstring_end_line)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the file
        tree = ast.parse(content)
        
        # Extract imports
        extractor = ImportExtractor()
        extractor.visit(tree)
        
        # Find docstring end
        docstring_end = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    docstring_end = node.body[0].end_lineno or node.body[0].lineno
        
        # Categorize imports
        standard_imports = []
        third_party_imports = []
        local_imports = []
        
        # Standard library modules (common ones)
        standard_modules = {
            'os', 'sys', 'json', 'time', 'datetime', 'pathlib', 'typing', 'collections',
            'itertools', 'functools', 'operator', 're', 'math', 'random', 'string',
            'io', 'tempfile', 'shutil', 'glob', 'fnmatch', 'linecache', 'pickle',
            'copy', 'deepcopy', 'hashlib', 'hmac', 'base64', 'urllib', 'http',
            'socket', 'ssl', 'threading', 'multiprocessing', 'asyncio', 'concurrent',
            'logging', 'warnings', 'traceback', 'inspect', 'importlib', 'pkgutil',
            'unittest', 'doctest', 'argparse', 'configparser', 'csv', 'xml',
            'html', 'email', 'mimetypes', 'platform', 'subprocess', 'signal',
            'atexit', 'contextlib', 'weakref', 'gc', 'ctypes', 'struct', 'array',
            'enum', 'dataclasses', 'abc', 'contextvars', 'asyncio', 'ssl'
        }
        
        for line_num, import_type, import_content in extractor.imports:
            if import_type == "from":
                # Extract module name from "from module import ..."
                match = re.match(r'from\s+([^\s]+)', import_content)
                if match:
                    module = match.group(1).split('.')[0]
                else:
                    module = ""
            else:
                # Extract module name from "import module"
                match = re.match(r'import\s+([^\s,]+)', import_content)
                if match:
                    module = match.group(1).split('.')[0]
                else:
                    module = ""
            
            # Categorize
            if module in standard_modules:
                standard_imports.append(import_content)
            elif module.startswith('.') or module.startswith('ai_admin'):
                local_imports.append(import_content)
            else:
                third_party_imports.append(import_content)
        
        return standard_imports, third_party_imports, local_imports, docstring_end
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return [], [], [], 0


def fix_imports_in_file(file_path: Path) -> bool:
    """
    Fix imports in a single file.
    
    Returns:
        True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extract imports
        standard_imports, third_party_imports, local_imports, docstring_end = extract_imports_from_file(file_path)
        
        if not (standard_imports or third_party_imports or local_imports):
            return False  # No imports to fix
        
        # Find existing imports to remove
        import_lines_to_remove = set()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (stripped.startswith('import ') or stripped.startswith('from ')) and not stripped.startswith('#'):
                import_lines_to_remove.add(i)
        
        # Remove existing imports
        new_lines = [line for i, line in enumerate(lines) if i not in import_lines_to_remove]
        
        # Find insertion point (after docstring)
        insertion_point = 0
        for i, line in enumerate(new_lines):
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                # Find end of docstring
                quote = stripped[:3]
                if stripped.count(quote) >= 2:
                    insertion_point = i + 1
                    break
                else:
                    # Multi-line docstring
                    for j in range(i + 1, len(new_lines)):
                        if quote in new_lines[j]:
                            insertion_point = j + 1
                            break
                    break
            elif stripped and not stripped.startswith('#'):
                insertion_point = i
                break
        
        # Prepare new imports
        new_imports = []
        
        # Add standard library imports
        if standard_imports:
            new_imports.extend(sorted(set(standard_imports)))
            new_imports.append('')  # Empty line
        
        # Add third-party imports
        if third_party_imports:
            new_imports.extend(sorted(set(third_party_imports)))
            new_imports.append('')  # Empty line
        
        # Add local imports
        if local_imports:
            new_imports.extend(sorted(set(local_imports)))
            new_imports.append('')  # Empty line
        
        # Insert imports
        for i, import_line in enumerate(new_imports):
            new_lines.insert(insertion_point + i, import_line + '\n')
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        return True
        
    except Exception as e:
        print(f"Error fixing imports in {file_path}: {e}")
        return False


def main():
    """Main function."""
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
    else:
        target_path = Path('.')
    
    if not target_path.exists():
        print(f"Path {target_path} does not exist")
        return 1
    
    modified_files = []
    
    # Find all Python files
    python_files = []
    if target_path.is_file() and target_path.suffix == '.py':
        python_files = [target_path]
    else:
        python_files = list(target_path.rglob('*.py'))
    
    print(f"Found {len(python_files)} Python files")
    
    for file_path in python_files:
        # Skip __pycache__ and test files for now
        if '__pycache__' in str(file_path) or 'test_' in file_path.name:
            continue
            
        print(f"Processing {file_path}...")
        if fix_imports_in_file(file_path):
            modified_files.append(file_path)
            print(f"  ✓ Modified")
        else:
            print(f"  - No changes needed")
    
    print(f"\nModified {len(modified_files)} files:")
    for file_path in modified_files:
        print(f"  {file_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
