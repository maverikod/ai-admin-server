#!/usr/bin/env python3
"""
Script to fix test endpoints in all test files.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import re
from pathlib import Path

def fix_test_file(file_path: str):
    """Fix endpoints in a test file."""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match old endpoint format
    old_pattern = r'f"{self\.base_url}/cmd/([^"]+)"'
    
    def replace_endpoint(match):
        command_name = match.group(1)
        return 'f"{self.base_url}/cmd"'
    
    # Replace endpoint URLs
    content = re.sub(old_pattern, replace_endpoint, content)
    
    # Pattern to match old JSON format
    old_json_pattern = r'json=\{\s*"([^"]+)":\s*([^}]+)\s*\}'
    
    def replace_json(match):
        param_name = match.group(1)
        param_value = match.group(2)
        return f'json={{\n                        "command": "{param_name}",\n                        "params": {param_value}\n                    }}'
    
    # Replace JSON format
    content = re.sub(old_json_pattern, replace_json, content, flags=re.MULTILINE | re.DOTALL)
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def main():
    """Main function."""
    test_files = [
        "test_ollama.py",
        "test_github.py", 
        "test_queue.py",
        "test_system.py"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            fix_test_file(test_file)
        else:
            print(f"❌ File not found: {test_file}")

if __name__ == "__main__":
    main()
