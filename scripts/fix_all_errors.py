#!/usr/bin/env python3
"""Script to fix all linting errors in command files.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import re
from pathlib import Path


def fix_file_errors(file_path: Path) -> bool:
    """Fix all errors in a file.
    
    Args:
        file_path: Path to file to fix
        
    Returns:
        True if file was modified
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix f-string issues
        content = re.sub(r'f"([^"]*)"', r'"\1"', content)
        content = re.sub(r'f\'([^\']*)\'', r'"\1"', content)
        
        # Fix missing imports - add common imports at the top
        imports_to_add = []
        
        if 'Optional' in content and 'from typing import' not in content:
            imports_to_add.append('from typing import Optional, List, Dict, Any')
        elif 'Optional' in content and 'Optional' not in content.split('from typing import')[1].split('\n')[0]:
            content = re.sub(
                r'from typing import ([^\n]+)',
                r'from typing import \1, Optional, List, Dict, Any',
                content
            )
        
        if 'ErrorResult' in content and 'from mcp_proxy_adapter.commands.result import' not in content:
            imports_to_add.append('from mcp_proxy_adapter.commands.result import ErrorResult, SuccessResult')
        elif 'ErrorResult' in content and 'ErrorResult' not in content.split('from mcp_proxy_adapter.commands.result import')[1].split('\n')[0]:
            content = re.sub(
                r'from mcp_proxy_adapter.commands.result import ([^\n]+)',
                r'from mcp_proxy_adapter.commands.result import \1, ErrorResult, SuccessResult',
                content
            )
        
        if 'datetime' in content and 'from datetime import' not in content:
            imports_to_add.append('from datetime import datetime')
        
        if 'subprocess' in content and 'import subprocess' not in content:
            imports_to_add.append('import subprocess')
        
        if 'json' in content and 'import json' not in content:
            imports_to_add.append('import json')
        
        if 'os.' in content and 'import os' not in content:
            imports_to_add.append('import os')
        
        # Add imports at the top
        if imports_to_add:
            # Find the first import line
            lines = content.split('\n')
            import_index = -1
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_index = i
                    break
            
            if import_index >= 0:
                # Insert new imports before existing imports
                for import_line in reversed(imports_to_add):
                    lines.insert(import_index, import_line)
                content = '\n'.join(lines)
            else:
                # Add imports after docstring
                docstring_end = content.find('"""', content.find('"""') + 3) + 3
                if docstring_end > 2:
                    content = content[:docstring_end] + '\n\n' + '\n'.join(imports_to_add) + '\n' + content[docstring_end:]
        
        # Fix syntax errors in f-strings
        content = re.sub(r'f"([^"]*)"', r'"\1"', content)
        content = re.sub(r'f\'([^\']*)\'', r'"\1"', content)
        
        # Fix walrus operator syntax errors
        content = re.sub(r'(\w+)\s*=\s*([^=]+)\s*=\s*([^,)]+)', r'\1 = \2 == \3', content)
        
        # Fix bare except statements
        content = re.sub(r'except:', r'except Exception:', content)
        
        # Remove unused variable assignments
        content = re.sub(r'(\w+)\s*=\s*[^=]+$', r'# \1 = ...', content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error fixing {file_path.name}: {str(e)}")
        return False


def main():
    """Main function to fix all errors."""
    commands_dir = Path("/home/vasilyvz/projects/vast_srv/ai_admin/commands")
    
    if not commands_dir.exists():
        print(f"Commands directory not found: {commands_dir}")
        return
    
    fixed_count = 0
    total_count = 0
    
    for command_file in commands_dir.glob("*.py"):
        if command_file.name in ['__init__.py', 'base.py', 'registry.py']:
            continue
            
        total_count += 1
        if fix_file_errors(command_file):
            fixed_count += 1
            print(f"Fixed: {command_file.name}")
    
    print(f"\nFixed {fixed_count} out of {total_count} files")


if __name__ == "__main__":
    main()
