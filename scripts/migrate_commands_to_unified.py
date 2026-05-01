#!/usr/bin/env python3
"""Script to migrate all commands to unified security template.

This script automatically migrates existing commands to use the unified
security approach with BaseUnifiedCommand and CommandSecurityMixin.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set


class CommandMigrator:
    """Migrates commands to unified security template."""

    def __init__(self, commands_dir: str):
        """Initialize migrator.
        
        Args:
            commands_dir: Path to commands directory
        """
        self.commands_dir = Path(commands_dir)
        self.migrated_files: Set[str] = set()
        self.failed_files: Set[str] = set()
        
        # Commands that should be skipped
        self.skip_files = {
            "__init__.py",
            "base.py",
            "base_unified_command.py",
            "example_unified_security_command.py",
            "registry.py",
            "git_utils.py",
            "k8s_utils.py",
            "ollama_base.py",
        }

    def migrate_all_commands(self) -> Dict[str, List[str]]:
        """Migrate all commands to unified template.
        
        Returns:
            Dictionary with migration results
        """
        results = {
            "migrated": [],
            "failed": [],
            "skipped": []
        }
        
        for command_file in self.commands_dir.glob("*.py"):
            if command_file.name in self.skip_files:
                results["skipped"].append(command_file.name)
                continue
                
            try:
                if self._migrate_command_file(command_file):
                    results["migrated"].append(command_file.name)
                    self.migrated_files.add(command_file.name)
                else:
                    results["failed"].append(command_file.name)
                    self.failed_files.add(command_file.name)
            except Exception as e:
                print(f"Error migrating {command_file.name}: {str(e)}")
                results["failed"].append(command_file.name)
                self.failed_files.add(command_file.name)
        
        return results

    def _migrate_command_file(self, file_path: Path) -> bool:
        """Migrate a single command file.
        
        Args:
            file_path: Path to command file
            
        Returns:
            True if migration was successful
        """
        print(f"Migrating {file_path.name}...")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already migrated
        if "BaseUnifiedCommand" in content:
            print(f"  {file_path.name} already migrated, skipping")
            return True
        
        # Parse AST to understand structure
        try:
            tree = ast.parse(content)
        except SyntaxError:
            print(f"  {file_path.name} has syntax errors, skipping")
            return False
        
        # Find command class
        command_class = self._find_command_class(tree)
        if not command_class:
            print(f"  {file_path.name} no command class found, skipping")
            return False
        
        # Migrate the file
        migrated_content = self._migrate_content(content, command_class)
        
        # Write migrated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(migrated_content)
        
        print(f"  {file_path.name} migrated successfully")
        return True

    def _find_command_class(self, tree: ast.AST) -> ast.ClassDef:
        """Find the main command class in AST.
        
        Args:
            tree: AST tree
            
        Returns:
            Command class node or None
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it's a command class
                if any(base.id == 'Command' for base in node.bases 
                       if isinstance(base, ast.Name)):
                    return node
        return None

    def _migrate_content(self, content: str, command_class: ast.ClassDef) -> str:
        """Migrate file content to unified template.
        
        Args:
            content: Original file content
            command_class: Command class AST node
            
        Returns:
            Migrated content
        """
        lines = content.split('\n')
        migrated_lines = []
        
        # Add author header if missing
        if "Author: Vasiliy Zdanovskiy" not in content:
            migrated_lines.append('"""')
            migrated_lines.append('')
            migrated_lines.append('Author: Vasiliy Zdanovskiy')
            migrated_lines.append('email: vasilyvz@gmail.com')
            migrated_lines.append('"""')
            migrated_lines.append('')
        
        # Update imports
        migrated_lines.extend(self._update_imports(lines))
        
        # Update class definition
        migrated_lines.extend(self._update_class_definition(lines, command_class))
        
        # Update execute method
        migrated_lines.extend(self._update_execute_method(lines, command_class))
        
        return '\n'.join(migrated_lines)

    def _update_imports(self, lines: List[str]) -> List[str]:
        """Update imports for unified template.
        
        Args:
            lines: File lines
            
        Returns:
            Updated import lines
        """
        import_lines = []
        in_imports = True
        
        for line in lines:
            if in_imports and (line.startswith('import ') or line.startswith('from ')):
                # Update Command import
                if 'from mcp_proxy_adapter.commands.base import Command' in line:
                    import_lines.append('from ai_admin.commands.base_unified_command import BaseUnifiedCommand')
                else:
                    import_lines.append(line)
            elif in_imports and line.strip() == '':
                import_lines.append(line)
            elif in_imports and not line.startswith('#'):
                in_imports = False
                import_lines.append(line)
            else:
                import_lines.append(line)
        
        return import_lines

    def _update_class_definition(self, lines: List[str], command_class: ast.ClassDef) -> List[str]:
        """Update class definition to inherit from BaseUnifiedCommand.
        
        Args:
            lines: File lines
            command_class: Command class AST node
            
        Returns:
            Updated class definition lines
        """
        updated_lines = []
        in_class = False
        class_indent = 0
        
        for i, line in enumerate(lines):
            if f"class {command_class.name}" in line:
                in_class = True
                class_indent = len(line) - len(line.lstrip())
                
                # Update class definition
                if "BaseUnifiedCommand" not in line:
                    line = line.replace("Command", "BaseUnifiedCommand")
                
                updated_lines.append(line)
            elif in_class and line.strip() == '':
                updated_lines.append(line)
            elif in_class and not line.startswith(' ' * (class_indent + 1)):
                in_class = False
                updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        return updated_lines

    def _update_execute_method(self, lines: List[str], command_class: ast.ClassDef) -> List[str]:
        """Update execute method to use unified template.
        
        Args:
            lines: File lines
            command_class: Command class AST node
            
        Returns:
            Updated execute method lines
        """
        # This is a simplified version - in practice, you'd need more sophisticated
        # AST manipulation to properly migrate the execute method
        updated_lines = []
        
        for line in lines:
            # Add default operation method if missing
            if "def _get_default_operation" not in line:
                updated_lines.append(line)
            else:
                # Add the method if it doesn't exist
                updated_lines.append("    def _get_default_operation(self) -> str:")
                updated_lines.append(f'        """Get default operation name for {command_class.name}."""')
                updated_lines.append(f'        return "{command_class.name}:execute"')
                updated_lines.append("")
                updated_lines.append(line)
        
        return updated_lines


def main():
    """Main migration function."""
    commands_dir = "/home/vasilyvz/projects/vast_srv/ai_admin/commands"
    
    migrator = CommandMigrator(commands_dir)
    results = migrator.migrate_all_commands()
    
    print("\n=== Migration Results ===")
    print(f"Migrated: {len(results['migrated'])} files")
    print(f"Failed: {len(results['failed'])} files")
    print(f"Skipped: {len(results['skipped'])} files")
    
    if results['migrated']:
        print("\nMigrated files:")
        for file in results['migrated']:
            print(f"  ✓ {file}")
    
    if results['failed']:
        print("\nFailed files:")
        for file in results['failed']:
            print(f"  ✗ {file}")
    
    if results['skipped']:
        print("\nSkipped files:")
        for file in results['skipped']:
            print(f"  - {file}")


if __name__ == "__main__":
    main()
