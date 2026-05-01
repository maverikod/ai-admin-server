#!/usr/bin/env python3
"""Script to properly fix import issues in command files.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import re
from pathlib import Path


def fix_file_imports(file_path: Path) -> bool:
    """Fix import issues in a file properly.
    
    Args:
        file_path: Path to file to fix
        
    Returns:
        True if file was modified
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Add missing imports that are commonly used
        if 'from typing import' in content and 'Optional' not in content:
            content = re.sub(
                r'from typing import ([^\\n]+)',
                r'from typing import \1, Optional, List, Dict, Any',
                content
            )
        
        # Add missing imports for common classes
        if 'ErrorResult' in content and 'from mcp_proxy_adapter.commands.result import' not in content:
            content = re.sub(
                r'from mcp_proxy_adapter.commands.result import ([^\\n]+)',
                r'from mcp_proxy_adapter.commands.result import \1, ErrorResult',
                content
            )
        
        if 'SuccessResult' in content and 'SuccessResult' not in content.split('from mcp_proxy_adapter.commands.result import')[1].split('\\n')[0]:
            content = re.sub(
                r'from mcp_proxy_adapter.commands.result import ([^\\n]+)',
                r'from mcp_proxy_adapter.commands.result import \1, SuccessResult',
                content
            )
        
        # Add missing datetime import
        if 'datetime' in content and 'from datetime import' not in content:
            content = re.sub(
                r'import subprocess',
                r'import subprocess\\nfrom datetime import datetime',
                content
            )
        
        # Add missing subprocess import
        if 'subprocess' in content and 'import subprocess' not in content:
            content = re.sub(
                r'from datetime import datetime',
                r'from datetime import datetime\\nimport subprocess',
                content
            )
        
        # Add missing json import
        if 'json' in content and 'import json' not in content:
            content = re.sub(
                r'import subprocess',
                r'import subprocess\\nimport json',
                content
            )
        
        # Add missing os import
        if 'os.' in content and 'import os' not in content:
            content = re.sub(
                r'import json',
                r'import json\\nimport os',
                content
            )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error fixing {file_path.name}: {str(e)}")
        return False


def main():
    """Main function to fix import issues."""
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
        if fix_file_imports(command_file):
            fixed_count += 1
            print(f"Fixed: {command_file.name}")
    
    print(f"\\nFixed {fixed_count} out of {total_count} files")


if __name__ == "__main__":
    main()
