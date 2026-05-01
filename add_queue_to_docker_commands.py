#!/usr/bin/env python3
"""
Script to add queue support to all Docker commands.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import re
from typing import List, Dict, Any


def get_docker_commands() -> List[str]:
    """Get list of all Docker command files."""
    commands_dir = "ai_admin/commands"
    docker_commands = []

    for file in os.listdir(commands_dir):
        if file.startswith("docker_") and file.endswith("_command.py"):
            docker_commands.append(file)

    return sorted(docker_commands)


def has_queue_support(file_path: str) -> bool:
    """Check if command already has queue support."""
    with open(file_path, "r") as f:
        content = f.read()
        return "use_queue" in content


def add_queue_support_to_command(file_path: str) -> bool:
    """Add queue support to a Docker command."""
    print(f"Processing {file_path}...")

    with open(file_path, "r") as f:
        content = f.read()

    # Check if already has queue support
    if has_queue_support(file_path):
        print(f"  ✅ {file_path} already has queue support")
        return True

    # Find execute method signature
    execute_pattern = r"async def execute\(\s*self,([^)]*)\) -> SuccessResult:"
    execute_match = re.search(execute_pattern, content, re.DOTALL)

    if not execute_match:
        print(f"  ❌ {file_path} - Could not find execute method")
        return False

    # Extract parameters
    params_str = execute_match.group(1)

    # Add use_queue parameter if not present
    if "use_queue" not in params_str:
        # Find the last parameter before user_roles or **kwargs
        if "user_roles: Optional[List[str]] = None" in params_str:
            # Insert before user_roles
            new_params = params_str.replace(
                "user_roles: Optional[List[str]] = None",
                "use_queue: bool = True,\n        user_roles: Optional[List[str]] = None",
            )
        elif "**kwargs" in params_str:
            # Insert before **kwargs
            new_params = params_str.replace(
                "**kwargs", "use_queue: bool = True,\n        **kwargs"
            )
        else:
            # Add at the end
            new_params = params_str.rstrip() + ",\n        use_queue: bool = True"

        # Replace in content
        content = content.replace(params_str, new_params)

    # Add use_queue to docstring
    docstring_pattern = r'(\s+"""Execute.*?\n\s+Returns:\s+Success result.*?\n\s+""")'
    docstring_match = re.search(docstring_pattern, content, re.DOTALL)

    if docstring_match:
        docstring = docstring_match.group(1)
        if "use_queue" not in docstring:
            # Find the last parameter in docstring
            if "user_roles: List of user roles" in docstring:
                new_docstring = docstring.replace(
                    "user_roles: List of user roles for security validation",
                    "use_queue: Use background queue for long-running operations\n            user_roles: List of user roles for security validation",
                )
            else:
                # Add before Returns
                new_docstring = docstring.replace(
                    "Returns:",
                    "use_queue: Use background queue for long-running operations\n\n        Returns:",
                )

            content = content.replace(docstring, new_docstring)

    # Add use_queue to super().execute() call
    super_execute_pattern = r"return await super\(\)\.execute\(([^)]*)\)"
    super_execute_match = re.search(super_execute_pattern, content, re.DOTALL)

    if super_execute_match:
        super_params = super_execute_match.group(1)
        if "use_queue=use_queue" not in super_params:
            if "user_roles=user_roles" in super_params:
                new_super_params = super_params.replace(
                    "user_roles=user_roles",
                    "use_queue=use_queue,\n            user_roles=user_roles",
                )
            elif "**kwargs" in super_params:
                new_super_params = super_params.replace(
                    "**kwargs", "use_queue=use_queue,\n            **kwargs"
                )
            else:
                new_super_params = (
                    super_params.rstrip() + ",\n            use_queue=use_queue"
                )

            content = content.replace(super_params, new_super_params)

    # Add use_queue to schema
    schema_pattern = r'(\s+"user_roles":\s*{\s*"type":\s*"array",\s*"items":\s*{"type":\s*"string"},\s*"description":\s*"List of user roles for security validation",\s*},)'
    schema_match = re.search(schema_pattern, content, re.DOTALL)

    if schema_match:
        user_roles_schema = schema_match.group(1)
        use_queue_schema = """                "use_queue": {
                    "type": "boolean",
                    "description": "Use background queue for long-running operations",
                    "default": True,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },"""

        content = content.replace(user_roles_schema, use_queue_schema)

    # Write back to file
    with open(file_path, "w") as f:
        f.write(content)

    print(f"  ✅ {file_path} - Added queue support")
    return True


def main():
    """Main function to add queue support to all Docker commands."""
    print("🔧 Adding queue support to Docker commands...")

    docker_commands = get_docker_commands()
    print(f"Found {len(docker_commands)} Docker commands:")

    success_count = 0
    for command in docker_commands:
        file_path = f"ai_admin/commands/{command}"
        if add_queue_support_to_command(file_path):
            success_count += 1

    print(f"\n📊 Results:")
    print(f"  Total commands: {len(docker_commands)}")
    print(f"  Successfully updated: {success_count}")
    print(f"  Failed: {len(docker_commands) - success_count}")


if __name__ == "__main__":
    main()
