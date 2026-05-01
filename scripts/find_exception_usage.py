#!/usr/bin/env python3
"""
Script to find all direct usage of Exception class in Python files.

This script searches for all occurrences of Exception usage and categorizes them
for proper exception handling refactoring.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple


class ExceptionFinder(ast.NodeVisitor):
    """Find all Exception usage in AST."""
    
    def __init__(self):
        self.exception_usage: List[Dict] = []
        self.current_file = ""
    
    def set_file(self, file_path: str):
        """Set current file path."""
        self.current_file = file_path
    
    def visit_Raise(self, node):
        """Visit raise statements."""
        if node.exc:
            if isinstance(node.exc, ast.Call):
                # Exception() or SomeException()
                if isinstance(node.exc.func, ast.Name):
                    if node.exc.func.id == 'Exception':
                        self.exception_usage.append({
                            'type': 'raise_exception',
                            'line': node.lineno,
                            'content': ast.unparse(node),
                            'file': self.current_file,
                            'context': 'raise'
                        })
            elif isinstance(node.exc, ast.Name):
                # raise SomeException
                if node.exc.id == 'Exception':
                    self.exception_usage.append({
                        'type': 'raise_exception',
                        'line': node.lineno,
                        'content': ast.unparse(node),
                        'file': self.current_file,
                        'context': 'raise'
                    })
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node):
        """Visit except clauses."""
        if node.type:
            if isinstance(node.type, ast.Name):
                if node.type.id == 'Exception':
                    self.exception_usage.append({
                        'type': 'except_exception',
                        'line': node.lineno,
                        'content': ast.unparse(node),
                        'file': self.current_file,
                        'context': 'except'
                    })
        self.generic_visit(node)
    
    def visit_IsInstance(self, node):
        """Visit isinstance calls."""
        if isinstance(node.args[1], ast.Name):
            if node.args[1].id == 'Exception':
                self.exception_usage.append({
                    'type': 'isinstance_exception',
                    'line': node.lineno,
                    'content': ast.unparse(node),
                    'file': self.current_file,
                    'context': 'isinstance'
                })
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Visit function calls."""
        if isinstance(node.func, ast.Name):
            if node.func.id == 'Exception':
                self.exception_usage.append({
                    'type': 'call_exception',
                    'line': node.lineno,
                    'content': ast.unparse(node),
                    'file': self.current_file,
                    'context': 'call'
                })
        self.generic_visit(node)


def find_exceptions_in_file(file_path: Path) -> List[Dict]:
    """Find all Exception usage in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the file
        tree = ast.parse(content)
        
        # Find exceptions
        finder = ExceptionFinder()
        finder.set_file(str(file_path))
        finder.visit(tree)
        
        return finder.exception_usage
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []


def categorize_exceptions(exception_usage: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize exception usage by type and context."""
    categories = {
        'raise_exception': [],
        'except_exception': [],
        'isinstance_exception': [],
        'call_exception': [],
        'other': []
    }
    
    for usage in exception_usage:
        usage_type = usage.get('type', 'other')
        if usage_type in categories:
            categories[usage_type].append(usage)
        else:
            categories['other'].append(usage)
    
    return categories


def generate_exception_report(exception_usage: List[Dict], output_file: Path):
    """Generate a detailed report of exception usage."""
    categories = categorize_exceptions(exception_usage)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Exception Usage Report\n\n")
        f.write(f"Total Exception usages found: {len(exception_usage)}\n\n")
        
        for category, usages in categories.items():
            if not usages:
                continue
                
            f.write(f"## {category.replace('_', ' ').title()} ({len(usages)} occurrences)\n\n")
            
            # Sort by line number descending (largest to smallest) to avoid line number shifts
            usages_sorted = sorted(usages, key=lambda x: x['line'], reverse=True)
            
            for usage in usages_sorted:
                f.write(f"**File:** `{usage['file']}`\n")
                f.write(f"**Line:** {usage['line']}\n")
                f.write(f"**Context:** {usage['context']}\n")
                f.write(f"**Content:** `{usage['content']}`\n\n")
        
        # Summary by file
        f.write("## Summary by File\n\n")
        file_counts = {}
        for usage in exception_usage:
            file_path = usage['file']
            if file_path not in file_counts:
                file_counts[file_path] = 0
            file_counts[file_path] += 1
        
        for file_path, count in sorted(file_counts.items()):
            f.write(f"- `{file_path}`: {count} occurrences\n")


def suggest_specific_exceptions(exception_usage: List[Dict]) -> Dict[str, List[str]]:
    """Suggest specific exception types for generic Exception usage."""
    suggestions = {
        'ssl_errors': [],
        'validation_errors': [],
        'authentication_errors': [],
        'configuration_errors': [],
        'network_errors': [],
        'file_errors': [],
        'permission_errors': [],
        'other_errors': []
    }
    
    for usage in exception_usage:
        file_path = usage['file']
        content = usage['content'].lower()
        
        # Categorize based on context
        if 'ssl' in file_path.lower() or 'cert' in content or 'tls' in content:
            suggestions['ssl_errors'].append(f"{usage['file']}:{usage['line']}")
        elif 'valid' in content or 'invalid' in content:
            suggestions['validation_errors'].append(f"{usage['file']}:{usage['line']}")
        elif 'auth' in content or 'login' in content or 'token' in content:
            suggestions['authentication_errors'].append(f"{usage['file']}:{usage['line']}")
        elif 'config' in content or 'setting' in content:
            suggestions['configuration_errors'].append(f"{usage['file']}:{usage['line']}")
        elif 'network' in content or 'connection' in content or 'socket' in content:
            suggestions['network_errors'].append(f"{usage['file']}:{usage['line']}")
        elif 'file' in content or 'path' in content or 'directory' in content:
            suggestions['file_errors'].append(f"{usage['file']}:{usage['line']}")
        elif 'permission' in content or 'access' in content or 'denied' in content:
            suggestions['permission_errors'].append(f"{usage['file']}:{usage['line']}")
        else:
            suggestions['other_errors'].append(f"{usage['file']}:{usage['line']}")
    
    return suggestions


def generate_refactoring_script(exception_usage: List[Dict], output_file: Path):
    """Generate a Python script to refactor Exception usage from largest to smallest line numbers."""
    
    # Group by file and sort by line number descending
    file_exceptions = {}
    for usage in exception_usage:
        file_path = usage['file']
        if file_path not in file_exceptions:
            file_exceptions[file_path] = []
        file_exceptions[file_path].append(usage)
    
    # Sort each file's exceptions by line number descending
    for file_path in file_exceptions:
        file_exceptions[file_path].sort(key=lambda x: x['line'], reverse=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('"""\n')
        f.write('Script to refactor Exception usage to specific exception types.\n')
        f.write('Processes files from largest line numbers to smallest to avoid line number shifts.\n')
        f.write('\n')
        f.write('Author: Vasiliy Zdanovskiy\n')
        f.write('email: vasilyvz@gmail.com\n')
        f.write('"""\n\n')
        f.write('import re\n')
        f.write('from pathlib import Path\n')
        f.write('from typing import Dict, List\n\n')
        f.write('# Custom exception classes to be created\n')
        f.write('CUSTOM_EXCEPTIONS = {\n')
        f.write('    "ssl_errors": [\n')
        f.write('        "SSLError",\n')
        f.write('        "CertificateError",\n')
        f.write('        "TLSHandshakeError",\n')
        f.write('        "SSLConfigurationError"\n')
        f.write('    ],\n')
        f.write('    "validation_errors": [\n')
        f.write('        "ValidationError",\n')
        f.write('        "InvalidInputError",\n')
        f.write('        "DataValidationError"\n')
        f.write('    ],\n')
        f.write('    "authentication_errors": [\n')
        f.write('        "AuthenticationError",\n')
        f.write('        "AuthorizationError",\n')
        f.write('        "TokenError",\n')
        f.write('        "PermissionError"\n')
        f.write('    ],\n')
        f.write('    "configuration_errors": [\n')
        f.write('        "ConfigurationError",\n')
        f.write('        "ConfigValidationError"\n')
        f.write('    ],\n')
        f.write('    "network_errors": [\n')
        f.write('        "NetworkError",\n')
        f.write('        "ConnectionError",\n')
        f.write('        "TimeoutError"\n')
        f.write('    ],\n')
        f.write('    "file_errors": [\n')
        f.write('        "FileNotFoundError",\n')
        f.write('        "PermissionError",\n')
        f.write('        "IOError"\n')
        f.write('    ],\n')
        f.write('    "permission_errors": [\n')
        f.write('        "PermissionError",\n')
        f.write('        "AccessDeniedError"\n')
        f.write('    ],\n')
        f.write('    "other_errors": [\n')
        f.write('        "CustomError",\n')
        f.write('        "ApplicationError"\n')
        f.write('    ]\n')
        f.write('}\n\n')
        
        f.write('def categorize_exception(usage: Dict) -> str:\n')
        f.write('    """Categorize exception usage based on context."""\n')
        f.write('    file_path = usage["file"]\n')
        f.write('    content = usage["content"].lower()\n')
        f.write('    \n')
        f.write('    if "ssl" in file_path.lower() or "cert" in content or "tls" in content:\n')
        f.write('        return "ssl_errors"\n')
        f.write('    elif "valid" in content or "invalid" in content:\n')
        f.write('        return "validation_errors"\n')
        f.write('    elif "auth" in content or "login" in content or "token" in content:\n')
        f.write('        return "authentication_errors"\n')
        f.write('    elif "config" in content or "setting" in content:\n')
        f.write('        return "configuration_errors"\n')
        f.write('    elif "network" in content or "connection" in content or "socket" in content:\n')
        f.write('        return "network_errors"\n')
        f.write('    elif "file" in content or "path" in content or "directory" in content:\n')
        f.write('        return "file_errors"\n')
        f.write('    elif "permission" in content or "access" in content or "denied" in content:\n')
        f.write('        return "permission_errors"\n')
        f.write('    else:\n')
        f.write('        return "other_errors"\n\n')
        
        f.write('def refactor_file(file_path: str, usages: List[Dict]):\n')
        f.write('    """Refactor a single file, processing from largest to smallest line numbers."""\n')
        f.write('    print(f"Refactoring {{file_path}}...")\n')
        f.write('    \n')
        f.write('    try:\n')
        f.write('        with open(file_path, \'r\', encoding=\'utf-8\') as f:\n')
        f.write('            lines = f.readlines()\n')
        f.write('        \n')
        f.write('        # Process from largest line number to smallest\n')
        f.write('        for usage in usages:\n')
        f.write('            line_num = usage["line"] - 1  # Convert to 0-based index\n')
        f.write('            if line_num < len(lines):\n')
        f.write('                original_line = lines[line_num]\n')
        f.write('                category = categorize_exception(usage)\n')
        f.write('                \n')
        f.write('                # Choose appropriate exception type\n')
        f.write('                if category == "ssl_errors":\n')
        f.write('                    new_exception = "SSLError"\n')
        f.write('                elif category == "validation_errors":\n')
        f.write('                    new_exception = "ValidationError"\n')
        f.write('                elif category == "authentication_errors":\n')
        f.write('                    new_exception = "AuthenticationError"\n')
        f.write('                elif category == "configuration_errors":\n')
        f.write('                    new_exception = "ConfigurationError"\n')
        f.write('                elif category == "network_errors":\n')
        f.write('                    new_exception = "NetworkError"\n')
        f.write('                elif category == "file_errors":\n')
        f.write('                    new_exception = "FileNotFoundError"\n')
        f.write('                elif category == "permission_errors":\n')
        f.write('                    new_exception = "PermissionError"\n')
        f.write('                else:\n')
        f.write('                    new_exception = "CustomError"\n')
        f.write('                \n')
        f.write('                # Replace Exception with specific exception\n')
        f.write('                new_line = original_line.replace("Exception", new_exception)\n')
        f.write('                lines[line_num] = new_line\n')
        f.write('                print(f"  Line {{usage[\'line\']}}: {{original_line.strip()}} -> {{new_line.strip()}}")\n')
        f.write('        \n')
        f.write('        # Write back to file\n')
        f.write('        with open(file_path, \'w\', encoding=\'utf-8\') as f:\n')
        f.write('            f.writelines(lines)\n')
        f.write('            \n')
        f.write('    except Exception as e:\n')
        f.write('        print(f"Error refactoring {{file_path}}: {{e}}")\n\n')
        
        f.write('def main():\n')
        f.write('    """Main refactoring function."""\n')
        f.write('    print("Starting Exception refactoring...")\n')
        f.write('    \n')
        f.write('    # File exceptions data\n')
        f.write('    file_exceptions = {\n')
        
        for file_path, usages in file_exceptions.items():
            f.write(f'        "{file_path}": [\n')
            for usage in usages:
                f.write(f'            {{"line": {usage["line"]}, "content": {repr(usage["content"])}, "type": "{usage["type"]}", "context": "{usage["context"]}", "file": "{file_path}"}},\n')
            f.write('        ],\n')
        
        f.write('    }\n\n')
        f.write('    # Process each file\n')
        f.write('    for file_path, usages in file_exceptions.items():\n')
        f.write('        refactor_file(file_path, usages)\n')
        f.write('    \n')
        f.write('    print("Refactoring completed!")\n\n')
        f.write('if __name__ == "__main__":\n')
        f.write('    main()\n')


def main():
    """Main function."""
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
    else:
        target_path = Path('.')
    
    if not target_path.exists():
        print(f"Path {target_path} does not exist")
        return 1
    
    # Find all Python files
    python_files = []
    if target_path.is_file() and target_path.suffix == '.py':
        python_files = [target_path]
    else:
        python_files = list(target_path.rglob('*.py'))
    
    print(f"Found {len(python_files)} Python files")
    
    all_exceptions = []
    
    for file_path in python_files:
        # Skip __pycache__ and virtual environments
        if '__pycache__' in str(file_path) or '.venv' in str(file_path):
            continue
            
        print(f"Processing {file_path}...")
        exceptions = find_exceptions_in_file(file_path)
        all_exceptions.extend(exceptions)
        if exceptions:
            print(f"  Found {len(exceptions)} Exception usages")
    
    # Generate report
    output_file = Path('exception_usage_report.md')
    generate_exception_report(all_exceptions, output_file)
    print(f"\nReport saved to {output_file}")
    
    # Generate suggestions
    suggestions = suggest_specific_exceptions(all_exceptions)
    suggestions_file = Path('exception_suggestions.md')
    
    with open(suggestions_file, 'w', encoding='utf-8') as f:
        f.write("# Exception Refactoring Suggestions\n\n")
        
        for category, locations in suggestions.items():
            if not locations:
                continue
                
            f.write(f"## {category.replace('_', ' ').title()}\n\n")
            f.write(f"**Suggested Exception Types:**\n")
            
            if category == 'ssl_errors':
                f.write("- `SSLError`\n")
                f.write("- `CertificateError`\n")
                f.write("- `TLSHandshakeError`\n")
            elif category == 'validation_errors':
                f.write("- `ValidationError`\n")
                f.write("- `InvalidInputError`\n")
                f.write("- `DataValidationError`\n")
            elif category == 'authentication_errors':
                f.write("- `AuthenticationError`\n")
                f.write("- `AuthorizationError`\n")
                f.write("- `TokenError`\n")
            elif category == 'configuration_errors':
                f.write("- `ConfigurationError`\n")
                f.write("- `ConfigValidationError`\n")
            elif category == 'network_errors':
                f.write("- `NetworkError`\n")
                f.write("- `ConnectionError`\n")
                f.write("- `TimeoutError`\n")
            elif category == 'file_errors':
                f.write("- `FileNotFoundError`\n")
                f.write("- `PermissionError`\n")
                f.write("- `IOError`\n")
            elif category == 'permission_errors':
                f.write("- `PermissionError`\n")
                f.write("- `AccessDeniedError`\n")
            else:
                f.write("- `CustomError`\n")
                f.write("- `ApplicationError`\n")
            
            f.write(f"\n**Locations to refactor:**\n")
            for location in locations:
                f.write(f"- {location}\n")
            f.write("\n")
    
    print(f"Suggestions saved to {suggestions_file}")
    
    # Generate refactoring script
    refactoring_script = Path('refactor_exceptions.py')
    generate_refactoring_script(all_exceptions, refactoring_script)
    print(f"Refactoring script saved to {refactoring_script}")
    
    print(f"\nTotal Exception usages found: {len(all_exceptions)}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
