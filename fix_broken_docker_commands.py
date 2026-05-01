#!/usr/bin/env python3
"""
Script to fix broken Docker commands after queue support addition.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import re
from typing import List, Dict, Any

def get_docker_commands() -> List[str]:
    """Get list of all Docker command files."""
    commands_dir = 'ai_admin/commands'
    docker_commands = []
    
    for file in os.listdir(commands_dir):
        if file.startswith('docker_') and file.endswith('_command.py'):
            docker_commands.append(file)
    
    return sorted(docker_commands)

def fix_broken_command(file_path: str) -> bool:
    """Fix broken Docker command file."""
    print(f"Checking {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check for common issues
    issues_found = []
    
    # Issue 1: Missing method signature
    if 'async def _execute_command_logic' in content and 'return await self._' in content:
        # Check if the method call is broken
        if 'return await self._' in content and '"""' in content:
            # Find the broken pattern
            pattern = r'return await self\._([^\(]+)\(\*\*kwargs\)\s*\n\s*"""([^"]*)"""\s*try:'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                method_name = match.group(1)
                docstring = match.group(2)
                issues_found.append(f"Broken method signature for {method_name}")
                
                # Fix the method signature
                fixed_method = f'''return await self._{method_name}(**kwargs)

    async def _{method_name}(
        self,
        use_queue: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """{docstring}"""
        try:'''
                
                content = content.replace(match.group(0), fixed_method)
    
    # Issue 2: Missing Task import
    if 'Task(' in content and 'from ai_admin.task_queue.task_queue import Task' not in content:
        issues_found.append("Missing Task import")
        # Add Task import
        if 'from ai_admin.task_queue.task_queue import TaskType' in content:
            content = content.replace(
                'from ai_admin.task_queue.task_queue import TaskType',
                'from ai_admin.task_queue.task_queue import TaskType, Task'
            )
        else:
            # Add import before the first usage
            task_usage = content.find('Task(')
            if task_usage != -1:
                # Find the line before Task usage
                lines = content[:task_usage].split('\n')
                for i in range(len(lines) - 1, -1, -1):
                    if 'from ai_admin.task_queue.queue_manager import queue_manager' in lines[i]:
                        lines.insert(i + 1, '                from ai_admin.task_queue.task_queue import Task')
                        break
                content = '\n'.join(lines) + content[task_usage:]
    
    # Issue 3: Missing use_queue in schema
    if 'use_queue' in content and '"use_queue"' not in content:
        issues_found.append("Missing use_queue in schema")
        # Add use_queue to schema
        schema_pattern = r'(\s+"user_roles":\s*{\s*"type":\s*"array",\s*"items":\s*{"type":\s*"string"},\s*"description":\s*"List of user roles for security validation",\s*},)'
        schema_match = re.search(schema_pattern, content, re.DOTALL)
        
        if schema_match:
            user_roles_schema = schema_match.group(1)
            use_queue_schema = '''                "use_queue": {
                    "type": "boolean",
                    "description": "Use background queue for long-running operations",
                    "default": True,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },'''
            
            content = content.replace(user_roles_schema, use_queue_schema)
    
    if issues_found:
        print(f"  🔧 Fixed issues: {', '.join(issues_found)}")
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    else:
        print(f"  ✅ No issues found")
        return False

def main():
    """Main function to fix all broken Docker commands."""
    print("🔧 Fixing broken Docker commands...")
    
    docker_commands = get_docker_commands()
    print(f"Found {len(docker_commands)} Docker commands:")
    
    fixed_count = 0
    for command in docker_commands:
        file_path = f'ai_admin/commands/{command}'
        if fix_broken_command(file_path):
            fixed_count += 1
    
    print(f"\n📊 Results:")
    print(f"  Total commands: {len(docker_commands)}")
    print(f"  Fixed: {fixed_count}")
    print(f"  No issues: {len(docker_commands) - fixed_count}")

if __name__ == "__main__":
    main()
