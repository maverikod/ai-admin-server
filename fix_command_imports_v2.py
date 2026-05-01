#!/usr/bin/env python3
"""
Script to fix imports in command files for the commands directory.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import re
from pathlib import Path

def fix_command_imports(file_path: Path) -> bool:
    """Fix imports in a command file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix imports
        content = re.sub(
            r'from ai_admin\.commands\.base_unified_command import BaseUnifiedCommand',
            'from base_unified_command import BaseUnifiedCommand',
            content
        )
        
        content = re.sub(
            r'from ai_admin\.core\.custom_exceptions import CustomError, NetworkError, PermissionError',
            'from mcp_proxy_adapter.core.errors import CommandError as CustomError, NetworkError, PermissionError',
            content
        )
        
        content = re.sub(
            r'from ai_admin\.core\.custom_exceptions import CustomError',
            'from mcp_proxy_adapter.core.errors import CommandError as CustomError',
            content
        )
        
        content = re.sub(
            r'from ai_admin\.security\.system_security_adapter import',
            'from mcp_proxy_adapter.security import',
            content
        )
        
        content = re.sub(
            r'from ai_admin\.security\.command_security_mixin import',
            'from mcp_proxy_adapter.security import',
            content
        )
        
        content = re.sub(
            r'from ai_admin\.security\.default_security_adapter import',
            'from mcp_proxy_adapter.security import',
            content
        )
        
        content = re.sub(
            r'from ai_admin\.task_queue\.queue_manager import',
            'from mcp_proxy_adapter.queue import',
            content
        )
        
        content = re.sub(
            r'from ai_admin\.task_queue\.task_queue import',
            'from mcp_proxy_adapter.queue import',
            content
        )
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed imports in {file_path.name}")
            return True
        else:
            print(f"No changes needed in {file_path.name}")
            return False
            
    except Exception as e:
        print(f"Error fixing {file_path.name}: {e}")
        return False

def main():
    """Fix imports in all command files."""
    commands_dir = Path("commands")
    
    if not commands_dir.exists():
        print("Commands directory not found")
        return
    
    fixed_count = 0
    for file_path in commands_dir.glob("*_command.py"):
        if fix_command_imports(file_path):
            fixed_count += 1
    
    print(f"Fixed imports in {fixed_count} files")

if __name__ == "__main__":
    main()
