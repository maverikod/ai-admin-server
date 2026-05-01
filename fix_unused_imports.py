#!/usr/bin/env python3
"""Script to fix unused imports in command files."""

import os
import re
from pathlib import Path

def fix_unused_imports(file_path):
    """Fix unused imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Common unused imports to remove
        unused_imports = [
            r'^import os\n',
            r'^from typing import List\n',
            r'^from typing import Optional\n',
            r'^from typing import Dict\n',
            r'^from typing import Any\n',
            r'^from mcp_proxy_adapter\.commands\.result import ErrorResult\n',
            r'^from mcp_proxy_adapter\.commands\.result import SuccessResult\n',
            r'^from abc import ABC\n',
            r'^from pathlib import Path\n',
            r'^import aiohttp\n',
        ]
        
        # Remove unused imports
        for pattern in unused_imports:
            content = re.sub(pattern, '', content, flags=re.MULTILINE)
        
        # Clean up multiple empty lines
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed unused imports in {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all command files."""
    commands_dir = Path("ai_admin/commands")
    
    if not commands_dir.exists():
        print("Commands directory not found!")
        return
    
    fixed_count = 0
    
    for file_path in commands_dir.rglob("*.py"):
        if file_path.name.startswith("__"):
            continue
            
        if fix_unused_imports(file_path):
            fixed_count += 1
    
    print(f"Fixed unused imports in {fixed_count} files")

if __name__ == "__main__":
    main()
