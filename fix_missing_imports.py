#!/usr/bin/env python3
"""Script to fix missing imports in command files."""

import os
import re
from pathlib import Path

def fix_missing_imports(file_path):
    """Fix missing imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check what imports are needed based on usage
        needs_os = 'os.' in content or 'os.path' in content
        needs_success_result = 'SuccessResult(' in content
        needs_aiohttp = 'aiohttp.' in content or 'ClientSession' in content
        needs_path = 'Path(' in content
        
        # Add missing imports
        imports_to_add = []
        
        if needs_os and 'import os' not in content:
            imports_to_add.append('import os')
        
        if needs_success_result and 'SuccessResult' not in content:
            imports_to_add.append('from mcp_proxy_adapter.commands.result import SuccessResult')
        
        if needs_aiohttp and 'import aiohttp' not in content:
            imports_to_add.append('import aiohttp')
        
        if needs_path and 'from pathlib import Path' not in content:
            imports_to_add.append('from pathlib import Path')
        
        if imports_to_add:
            # Find the right place to add imports (after docstring)
            lines = content.split('\n')
            insert_index = 0
            
            # Skip docstring
            in_docstring = False
            for i, line in enumerate(lines):
                if line.strip().startswith('"""') and not in_docstring:
                    in_docstring = True
                elif line.strip().endswith('"""') and in_docstring:
                    insert_index = i + 1
                    break
                elif not in_docstring and line.strip() and not line.strip().startswith('#'):
                    insert_index = i
                    break
            
            # Insert imports
            for import_line in imports_to_add:
                lines.insert(insert_index, import_line)
                insert_index += 1
            
            content = '\n'.join(lines)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed missing imports in {file_path}")
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
            
        if fix_missing_imports(file_path):
            fixed_count += 1
    
    print(f"Fixed missing imports in {fixed_count} files")

if __name__ == "__main__":
    main()
