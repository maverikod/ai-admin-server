#!/usr/bin/env python3
"""Script to fix undefined variable errors in command files - Version 3.

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


def extract_parameters_from_docstring(content: str) -> List[str]:
    """Extract parameter names from docstring."""
    params = []
    in_args_section = False
    
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('Args:'):
            in_args_section = True
            continue
        elif in_args_section:
            if line.startswith('Returns:') or line.startswith('Raises:'):
                break
            if ':' in line and not line.startswith(' '):
                param_name = line.split(':')[0].strip()
                if param_name and not param_name.startswith('**'):
                    params.append(param_name)
    
    return params


def fix_execute_method(content: str) -> str:
    """Fix the execute method to extract parameters from kwargs."""
    # Find the execute method
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Look for execute method
        if 'async def execute(self, **kwargs: Any) -> CommandResult:' in line:
            new_lines.append(line)
            i += 1
            
            # Add docstring and method body until we find the return statement
            while i < len(lines):
                current_line = lines[i]
                new_lines.append(current_line)
                
                # Look for the return statement with super().execute
                if 'return await super().execute(' in current_line:
                    # Extract parameters from docstring
                    method_content = '\n'.join(new_lines)
                    params = extract_parameters_from_docstring(method_content)
                    
                    # Add parameter extraction
                    if params:
                        new_lines.append('        # Extract parameters from kwargs')
                        for param in params:
                            new_lines.append(f'        {param} = kwargs.get("{param}")')
                        new_lines.append('')
                    
                    # Fix the return statement
                    if params:
                        param_args = [f'{param}={param}' for param in params]
                        new_lines.append(f'        return await super().execute(')
                        for param_arg in param_args:
                            new_lines.append(f'            {param_arg},')
                        new_lines.append('            **kwargs,')
                        new_lines.append('        )')
                    else:
                        new_lines.append('        return await super().execute(**kwargs)')
                    
                    i += 1
                    break
                i += 1
        else:
            new_lines.append(line)
            i += 1
    
    return '\n'.join(new_lines)


def fix_import_errors(content: str) -> str:
    """Fix common import errors."""
    # Add missing imports
    if 'datetime' in content and 'from datetime import datetime' not in content:
        content = content.replace(
            'import subprocess',
            'import subprocess\nfrom datetime import datetime'
        )
    
    if 'os' in content and 'import os' not in content:
        content = content.replace(
            'import subprocess',
            'import subprocess\nimport os'
        )
    
    if 'asyncio' in content and 'import asyncio' not in content:
        content = content.replace(
            'import subprocess',
            'import subprocess\nimport asyncio'
        )
    
    return content


def fix_command_file(file_path: str) -> bool:
    """Fix a single command file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix execute method
        content = fix_execute_method(content)
        
        # Fix import errors
        content = fix_import_errors(content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True
        else:
            print(f"No changes needed: {file_path}")
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
    
    print(f"Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
