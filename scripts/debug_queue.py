#!/usr/bin/env python3
"""
Debug queue script
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_admin.queue.task_queue import TaskQueue, Task, TaskType, TaskStatus

async def debug_queue():
    """Debug queue functionality"""
    print("=== Debugging Queue ===")
    
    # Create queue
    queue = TaskQueue()
    print(f"Queue created: {queue}")
    
    # Create a test task
    task = Task(
        task_type=TaskType.DOCKER_PUSH,
        params={
            "image_name": "vasilyvz/gpu-test",
            "tag": "latest"
        }
    )
    print(f"Task created: {task.id}")
    print(f"Task type: {task.task_type.value}")
    print(f"Task params: {task.params}")
    
    # Add task to queue
    try:
        task_id = await queue.add_task(task)
        print(f"Task added to queue: {task_id}")
        
        # Check queue status
        stats = await queue.get_queue_stats()
        print(f"Queue stats: {stats}")
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Check task status
        task_status = await queue.get_task(task_id)
        if task_status:
            print(f"Task status: {task_status.status.value}")
            print(f"Task error: {task_status.error}")
            print(f"Task logs: {task_status.logs}")
        else:
            print("Task not found in queue")
            
    except Exception as e:
        print(f"Error adding task: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_queue()) 