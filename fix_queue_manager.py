#!/usr/bin/env python3
"""
Script to fix queue_manager.py type annotations.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import re
from pathlib import Path


def fix_queue_manager():
    """Fix type annotations in queue_manager.py."""
    file_path = Path("ai_admin/task_queue/queue_manager.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix method signatures
    content = re.sub(
        r'async def add_[a-zA-Z_]+\(self, [^)]+\) -> str:',
        lambda m: re.sub(r'\(self, ([^)]+)\)', r'(self, \1) -> str:', m.group(0)),
        content
    )
    
    # Fix **options parameters
    content = re.sub(
        r'(\*\*options)(?!\s*:)',
        r'\1: Any',
        content
    )
    
    # Fix return statements
    content = re.sub(
        r'return await self\.task_queue\.add_task\(task\)',
        'task_id = await self.task_queue.add_task(task)\n        return task_id',
        content
    )
    
    # Fix other method signatures
    content = re.sub(
        r'async def [a-zA-Z_]+\(self, [^)]*\) -> [^:]+:',
        lambda m: re.sub(r'\(self, ([^)]*)\)', r'(self, \1) -> str:', m.group(0)) if '-> str:' not in m.group(0) else m.group(0),
        content
    )
    
    # Add Any import if needed
    if ': Any' in content and 'from typing import' in content:
        if 'Any' not in content.split('from typing import')[1].split('\n')[0]:
            content = re.sub(
                r'from typing import ([^\\n]+)',
                lambda m: f'from typing import {m.group(1)}, Any' if 'Any' not in m.group(1) else m.group(0),
                content
            )
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {file_path}")
    else:
        print(f"No changes needed for {file_path}")


if __name__ == "__main__":
    fix_queue_manager()
