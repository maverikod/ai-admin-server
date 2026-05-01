#!/usr/bin/env python3
"""
Script to copy all AI Admin commands to the commands directory for auto-discovery.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import shutil
from pathlib import Path

def copy_all_commands():
    """Copy all AI Admin commands to the commands directory."""
    source_dir = Path("ai_admin/commands")
    target_dir = Path("commands")
    
    if not source_dir.exists():
        print(f"Source directory {source_dir} does not exist")
        return
    
    if not target_dir.exists():
        target_dir.mkdir()
        print(f"Created target directory {target_dir}")
    
    # Get all command files
    command_files = list(source_dir.glob("*_command.py"))
    print(f"Found {len(command_files)} command files")
    
    copied_count = 0
    for source_file in command_files:
        target_file = target_dir / source_file.name
        
        try:
            # Copy the file
            shutil.copy2(source_file, target_file)
            print(f"Copied: {source_file.name}")
            copied_count += 1
        except Exception as e:
            print(f"Failed to copy {source_file.name}: {e}")
    
    print(f"\nCopied {copied_count} command files to {target_dir}")
    
    # Also copy base_unified_command.py if it exists
    base_file = source_dir / "base_unified_command.py"
    if base_file.exists():
        target_base = target_dir / "base_unified_command.py"
        try:
            shutil.copy2(base_file, target_base)
            print(f"Copied: base_unified_command.py")
        except Exception as e:
            print(f"Failed to copy base_unified_command.py: {e}")

if __name__ == "__main__":
    copy_all_commands()
