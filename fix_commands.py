#!/usr/bin/env python3
"""Script to fix undefined variable errors in command files.

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
    execute_pattern = r'(async def execute\(self, \*\*kwargs: Any\) -> CommandResult:.*?)(return await super\(\)\.execute\()'
    
    def replace_execute(match):
        method_start = match.group(1)
        super_call_start = match.group(2)
        
        # Extract parameters from docstring
        params = extract_parameters_from_docstring(method_start)
        
        # Create parameter extraction code
        param_extractions = []
        for param in params:
            if param == 'user_roles':
                param_extractions.append(f'        {param} = kwargs.get("{param}")')
            else:
                param_extractions.append(f'        {param} = kwargs.get("{param}")')
        
        param_extraction_code = '\n'.join(param_extractions)
        if param_extraction_code:
            param_extraction_code = '\n        # Extract parameters from kwargs\n' + param_extraction_code + '\n'
        
        # Create the new super call with extracted parameters
        param_args = []
        for param in params:
            param_args.append(f'{param}={param}')
        
        if param_args:
            super_call = f'{super_call_start}\n            {",\n            ".join(param_args)},\n            **kwargs,\n        )'
        else:
            super_call = f'{super_call_start}**kwargs,\n        )'
        
        return method_start + param_extraction_code + super_call
    
    return re.sub(execute_pattern, replace_execute, content, flags=re.DOTALL)


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
