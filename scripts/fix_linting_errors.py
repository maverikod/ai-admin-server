#!/usr/bin/env python3
"""Script to fix common linting errors in command files.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import re
from pathlib import Path


def fix_file_imports(file_path: Path) -> bool:
    """Fix common import issues in a file.
    
    Args:
        file_path: Path to file to fix
        
    Returns:
        True if file was modified
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove unused imports
        unused_imports = [
            'import asyncio',
            'import json',
            'import os',
            'import subprocess',
            'import yaml',
            'import base64',
            'import tempfile',
            'import pathlib',
            'from pathlib import Path',
            'from datetime import datetime',
            'from datetime import timedelta',
            'from typing import List',
            'from typing import Dict',
            'from typing import Any',
            'from typing import Optional',
            'from mcp_proxy_adapter.core.errors import CommandError',
            'from mcp_proxy_adapter.core.errors import ValidationError',
            'from mcp_proxy_adapter.commands.result import SuccessResult',
            'from mcp_proxy_adapter.commands.result import ErrorResult',
            'from ai_admin.dependency_injection import get_container',
            'from ai_admin.security.docker_security_adapter import DockerOperation',
            'from kubernetes.client import',
            'from kubernetes.config import',
            'from kubernetes.client.rest import ApiException',
            'from ai_admin.commands.k8s_utils import KubernetesConfigManager',
        ]
        
        for unused_import in unused_imports:
            # Remove import lines
            content = re.sub(f'^{unused_import}.*$', '', content, flags=re.MULTILINE)
            # Remove from import statements
            content = re.sub(f',\\s*{unused_import.split()[-1]}', '', content)
            content = re.sub(f'{unused_import.split()[-1]},\\s*', '', content)
        
        # Clean up empty lines
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Fix f-string placeholders
        content = re.sub(r'f"([^"]*)"', r'"\1"', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error fixing {file_path.name}: {str(e)}")
        return False


def main():
    """Main function to fix linting errors."""
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
    
    print(f"\nFixed {fixed_count} out of {total_count} files")


if __name__ == "__main__":
    main()
