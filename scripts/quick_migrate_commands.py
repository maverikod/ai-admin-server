#!/usr/bin/env python3
"""Quick migration script for commands to unified template.

This script performs basic migration of commands to use BaseUnifiedCommand.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import re
from pathlib import Path


def migrate_command_file(file_path: Path) -> bool:
    """Migrate a single command file to unified template.
    
    Args:
        file_path: Path to command file
        
    Returns:
        True if migration was successful
    """
    print(f"Migrating {file_path.name}...")
    
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already migrated
        if "BaseUnifiedCommand" in content:
            print(f"  {file_path.name} already migrated, skipping")
            return True
        
        # Skip utility files
        skip_files = {
            "__init__.py", "base.py", "base_unified_command.py", 
            "example_unified_security_command.py", "registry.py",
            "git_utils.py", "k8s_utils.py", "ollama_base.py"
        }
        
        if file_path.name in skip_files:
            print(f"  {file_path.name} skipped (utility file)")
            return True
        
        # Basic migration patterns
        migrated_content = content
        
        # 1. Add author header if missing
        if "Author: Vasiliy Zdanovskiy" not in content:
            # Find the first docstring and add author info
            docstring_pattern = r'("""[^"]*""")'
            match = re.search(docstring_pattern, content)
            if match:
                docstring = match.group(1)
                if "Author:" not in docstring:
                    new_docstring = docstring.rstrip('"""') + '\n\nAuthor: Vasiliy Zdanovskiy\nemail: vasilyvz@gmail.com\n"""'
                    migrated_content = migrated_content.replace(docstring, new_docstring)
        
        # 2. Update imports
        migrated_content = re.sub(
            r'from mcp_proxy_adapter\.commands\.base import Command',
            'from ai_admin.commands.base_unified_command import BaseUnifiedCommand',
            migrated_content
        )
        
        # 3. Update class inheritance
        migrated_content = re.sub(
            r'class (\w+)\(Command\):',
            r'class \1(BaseUnifiedCommand):',
            migrated_content
        )
        
        # 4. Add default operation method if missing
        if "_get_default_operation" not in migrated_content:
            # Find the class definition and add the method
            class_pattern = r'(class \w+\(BaseUnifiedCommand\):.*?)(    def __init__)'
            match = re.search(class_pattern, migrated_content, re.DOTALL)
            if match:
                class_def = match.group(1)
                init_def = match.group(2)
                
                # Extract command name from class name
                class_name_match = re.search(r'class (\w+)\(', class_def)
                if class_name_match:
                    class_name = class_name_match.group(1)
                    command_name = class_name.lower().replace('command', '')
                    
                    # Add the method
                    method_to_add = f'''    def _get_default_operation(self) -> str:
        """Get default operation name for {class_name}."""
        return "{command_name}:execute"

'''
                    
                    migrated_content = migrated_content.replace(
                        class_def + init_def,
                        class_def + method_to_add + init_def
                    )
        
        # Write migrated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(migrated_content)
        
        print(f"  {file_path.name} migrated successfully")
        return True
        
    except Exception as e:
        print(f"  Error migrating {file_path.name}: {str(e)}")
        return False


def main():
    """Main migration function."""
    commands_dir = Path("/home/vasilyvz/projects/vast_srv/ai_admin/commands")
    
    if not commands_dir.exists():
        print(f"Commands directory not found: {commands_dir}")
        return
    
    migrated_count = 0
    failed_count = 0
    skipped_count = 0
    
    # Get all Python files in commands directory
    command_files = list(commands_dir.glob("*.py"))
    
    print(f"Found {len(command_files)} command files to migrate")
    print("=" * 50)
    
    for command_file in command_files:
        try:
            if migrate_command_file(command_file):
                migrated_count += 1
            else:
                failed_count += 1
        except Exception as e:
            print(f"Error processing {command_file.name}: {str(e)}")
            failed_count += 1
    
    print("=" * 50)
    print(f"Migration completed:")
    print(f"  Migrated: {migrated_count} files")
    print(f"  Failed: {failed_count} files")
    print(f"  Total processed: {migrated_count + failed_count} files")


if __name__ == "__main__":
    main()
