#!/usr/bin/env python3
"""Script to fix missing imports in command files.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any


def find_command_files(directory: str) -> List[str]:
    """Find all command files in the directory."""
    command_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('_command.py') and not file.startswith('base_'):
                command_files.append(os.path.join(root, file))
    return command_files


def fix_imports(content: str) -> str:
    """Fix missing imports in the file."""
    lines = content.split('\n')
    new_lines = []
    imports_added = set()
    
    # Find the last import line
    last_import_line = -1
    for i, line in enumerate(lines):
        if line.strip().startswith(('import ', 'from ')):
            last_import_line = i
    
    # Check what imports are needed
    content_lower = content.lower()
    needed_imports = []
    
    if 'commandresult' in content_lower and 'from mcp_proxy_adapter.commands.result import' in content_lower:
        if 'CommandResult' not in content:
            needed_imports.append('CommandResult')
    
    if 'os.' in content and 'import os' not in content:
        needed_imports.append('import os')
    
    if 'path(' in content and 'from pathlib import Path' not in content:
        needed_imports.append('from pathlib import Path')
    
    if 'datetime' in content and 'from datetime import datetime' not in content:
        needed_imports.append('from datetime import datetime')
    
    if 'asyncio.' in content and 'import asyncio' not in content:
        needed_imports.append('import asyncio')
    
    # Add needed imports
    if needed_imports:
        # Find the import section
        for i, line in enumerate(lines):
            new_lines.append(line)
            if i == last_import_line:
                # Add new imports
                for imp in needed_imports:
                    if imp not in imports_added:
                        new_lines.append(imp)
                        imports_added.add(imp)
                break
    else:
        new_lines = lines
    
    return '\n'.join(new_lines)


def fix_command_file(file_path: str) -> bool:
    """Fix a single command file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix imports
        content = fix_imports(content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed imports: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Main function to fix all command files."""
    commands_dir = "/home/vasilyvz/projects/vast_srv/ai_admin/commands"
    
    if not os.path.exists(commands_dir):
        print(f"Commands directory not found: {commands_dir}")
        return
    
    command_files = find_command_files(commands_dir)
    print(f"Found {len(command_files)} command files")
    
    fixed_count = 0
    for file_path in command_files:
        if fix_command_file(file_path):
            fixed_count += 1
    
    print(f"Fixed imports in {fixed_count} files")


if __name__ == "__main__":
    main()
