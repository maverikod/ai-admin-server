#!/usr/bin/env python3
"""
Quick fix for test endpoints.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os

def fix_file(file_path):
    """Fix a test file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace old endpoints with new format
    replacements = [
        (f'f"{{self.base_url}}/cmd/{{command_name}}"', 'f"{self.base_url}/cmd"'),
        ('async with session.get(', 'async with session.post('),
        ('json={', 'json={\n                        "command": "COMMAND_NAME",\n                        "params": {'),
    ]
    
    # Simple replacements
    content = content.replace('f"{self.base_url}/cmd/github_list_repos"', 'f"{self.base_url}/cmd"')
    content = content.replace('f"{self.base_url}/cmd/github_create_repo"', 'f"{self.base_url}/cmd"')
    content = content.replace('f"{self.base_url}/cmd/queue_status"', 'f"{self.base_url}/cmd"')
    content = content.replace('f"{self.base_url}/cmd/queue_push"', 'f"{self.base_url}/cmd"')
    content = content.replace('f"{self.base_url}/cmd/queue_manage"', 'f"{self.base_url}/cmd"')
    content = content.replace('f"{self.base_url}/cmd/system_monitor"', 'f"{self.base_url}/cmd"')
    
    # Fix JSON format for specific commands
    content = content.replace(
        'json={\n                        "name": "test-repo",\n                        "description": "Test repository",\n                        "user_roles": ["admin"]\n                    }',
        'json={\n                        "command": "github_create_repo",\n                        "params": {\n                            "name": "test-repo",\n                            "description": "Test repository",\n                            "user_roles": ["admin"]\n                        }\n                    }'
    )
    
    content = content.replace(
        'json={\n                        "action": "push",\n                        "image_name": "nginx",\n                        "tag": "latest",\n                        "user_roles": ["admin"]\n                    }',
        'json={\n                        "command": "queue_push",\n                        "params": {\n                            "action": "push",\n                            "image_name": "nginx",\n                            "tag": "latest",\n                            "user_roles": ["admin"]\n                        }\n                    }'
    )
    
    # Fix GET requests to POST
    content = content.replace(
        'async with session.get(\n                    f"{self.base_url}/cmd/github_list_repos",\n                    headers=self.headers\n                ) as response:',
        'async with session.post(\n                    f"{self.base_url}/cmd",\n                    json={\n                        "command": "github_list_repos",\n                        "params": {}\n                    },\n                    headers=self.headers\n                ) as response:'
    )
    
    content = content.replace(
        'async with session.get(\n                    f"{self.base_url}/cmd/queue_status",\n                    headers=self.headers\n                ) as response:',
        'async with session.post(\n                    f"{self.base_url}/cmd",\n                    json={\n                        "command": "queue_status",\n                        "params": {}\n                    },\n                    headers=self.headers\n                ) as response:'
    )
    
    content = content.replace(
        'async with session.get(\n                    f"{self.base_url}/cmd/system_monitor",\n                    headers=self.headers\n                ) as response:',
        'async with session.post(\n                    f"{self.base_url}/cmd",\n                    json={\n                        "command": "system_monitor",\n                        "params": {}\n                    },\n                    headers=self.headers\n                ) as response:'
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def main():
    """Main function."""
    files_to_fix = [
        "test_github.py",
        "test_queue.py", 
        "test_system.py"
    ]
    
    for file_path in files_to_fix:
        fix_file(file_path)

if __name__ == "__main__":
    main()
