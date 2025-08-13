"""Queue manager for Docker operations."""

from typing import Dict, List, Any, Optional
from ai_admin.queue.task_queue import TaskQueue, Task, TaskType, TaskStatus


class QueueManager:
    """Manager for Docker task queues."""
    
    _instance: Optional['QueueManager'] = None
    
    def __new__(cls) -> 'QueueManager':
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize queue manager."""
        if self._initialized:
            return
        
        self.task_queue = TaskQueue(max_concurrent=2)
        self._initialized = True
    
    async def add_push_task(
        self,
        image_name: str,
        tag: str = "latest",
        **options
    ) -> str:
        """Add Docker push task to queue.
        
        Args:
            image_name: Docker image name
            tag: Image tag
            **options: Additional push options
            
        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.DOCKER_PUSH,
            params={
                "image_name": image_name,
                "tag": tag,
                **options
            }
        )
        
        return await self.task_queue.add_task(task)
    
    async def add_build_task(
        self,
        dockerfile_path: str = "Dockerfile",
        tag: Optional[str] = None,
        context_path: str = ".",
        **options
    ) -> str:
        """Add Docker build task to queue.
        
        Args:
            dockerfile_path: Path to Dockerfile
            tag: Tag for built image
            context_path: Build context path
            **options: Additional build options
            
        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.DOCKER_BUILD,
            params={
                "dockerfile_path": dockerfile_path,
                "tag": tag,
                "context_path": context_path,
                **options
            }
        )
        
        return await self.task_queue.add_task(task)
    
    async def add_pull_task(
        self,
        image_name: str,
        tag: str = "latest",
        **options
    ) -> str:
        """Add Docker pull task to queue.
        
        Args:
            image_name: Docker image name
            tag: Image tag
            **options: Additional pull options
            
        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.DOCKER_PULL,
            params={
                "image_name": image_name,
                "tag": tag,
                **options
            }
        )
        
        return await self.task_queue.add_task(task)
    
    async def add_ollama_pull_task(
        self,
        model_name: str,
        **options
    ) -> str:
        """Add Ollama model pull task to queue.
        
        Args:
            model_name: Ollama model name
            **options: Additional pull options
            
        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.OLLAMA_PULL,
            params={
                "model_name": model_name,
                **options
            }
        )
        
        return await self.task_queue.add_task(task)
    
    async def add_ollama_run_task(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **options
    ) -> str:
        """Add Ollama model inference task to queue.
        
        Args:
            model_name: Ollama model name
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **options: Additional inference options
            
        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.OLLAMA_RUN,
            params={
                "model_name": model_name,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                **options
            }
        )
        
        return await self.task_queue.add_task(task)
    
    async def add_task(self, task: Task) -> str:
        """Add generic task to queue.
        
        Args:
            task: Task to add
            
        Returns:
            Task ID
        """
        return await self.task_queue.add_task(task)
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task object or None if not found
        """
        return await self.task_queue.get_task(task_id)
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status dict or None if not found
        """
        task = await self.task_queue.get_task(task_id)
        return task.to_dict() if task else None
    
    async def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks.
        
        Returns:
            List of task dictionaries
        """
        tasks = await self.task_queue.get_all_tasks()
        return [task.to_dict() for task in tasks]
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics.
        
        Returns:
            Queue statistics
        """
        return await self.task_queue.get_queue_stats()
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status and statistics.
        
        Returns:
            Queue status information
        """
        stats = await self.task_queue.get_queue_stats()
        
        # Add recent tasks info
        recent_tasks = await self.task_queue.get_all_tasks()
        recent_tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return {
            "statistics": stats,
            "recent_tasks": [task.to_dict() for task in recent_tasks[:10]],
            "running_tasks": [
                task.to_dict() 
                for task in recent_tasks 
                if task.status == TaskStatus.RUNNING
            ]
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if task was cancelled, False otherwise
        """
        return await self.task_queue.cancel_task(task_id)
    
    async def clear_completed_tasks(self) -> int:
        """Clear completed and failed tasks.
        
        Returns:
            Number of tasks cleared
        """
        return await self.task_queue.clear_completed()
    
    async def pause_queue(self) -> bool:
        """Pause task queue (stop processing new tasks).
        
        Returns:
            True if queue was paused
        """
        # Set max_concurrent to 0 to pause
        self.task_queue.max_concurrent = 0
        return True
    
    async def resume_queue(self, max_concurrent: int = 2) -> bool:
        """Resume task queue processing.
        
        Args:
            max_concurrent: Maximum concurrent tasks
            
        Returns:
            True if queue was resumed
        """
        self.task_queue.max_concurrent = max_concurrent
        # Try to start pending tasks
        await self.task_queue._try_start_next_task()
        return True
    
    async def get_task_logs(self, task_id: str) -> Optional[List[str]]:
        """Get task logs by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of log messages or None if task not found
        """
        task = await self.task_queue.get_task(task_id)
        return task.logs if task else None
    
    async def push_task(self, queue_name: str, task_data: Dict[str, Any]) -> str:
        """Add generic task to queue.
        
        Args:
            queue_name: Name of the queue
            task_data: Task data dictionary
            
        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.CUSTOM_SCRIPT,
            params=task_data
        )
        
        return await self.task_queue.add_task(task)
    
    async def start_task(self, task_id: str, executor_func) -> bool:
        """Start task execution.
        
        Args:
            task_id: Task identifier
            executor_func: Function to execute the task
            
        Returns:
            True if task started successfully
        """
        task = await self.task_queue.get_task(task_id)
        if task:
            task.status = TaskStatus.RUNNING
            # Execute task in background
            import asyncio
            asyncio.create_task(executor_func(task_id, task.params))
            return True
        return False
    
    async def get_task_position(self, task_id: str) -> int:
        """Get task position in queue.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Position in queue (0 = currently running)
        """
        tasks = await self.task_queue.get_all_tasks()
        for i, task in enumerate(tasks):
            if task.id == task_id:
                return i
        return -1
    
    async def get_estimated_wait_time(self, task_id: str) -> int:
        """Get estimated wait time for task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Estimated wait time in seconds
        """
        position = await self.get_task_position(task_id)
        if position <= 0:
            return 0
        
        # Rough estimate: 30 seconds per task
        return position * 30
    
    async def update_task_result(self, task_id: str, result: Dict[str, Any]) -> bool:
        """Update task result.
        
        Args:
            task_id: Task identifier
            result: Task result data
            
        Returns:
            True if updated successfully
        """
        task = await self.task_queue.get_task(task_id)
        if task:
            task.result = result
            if result.get("success", False):
                task.status = TaskStatus.COMPLETED
            else:
                task.status = TaskStatus.FAILED
            return True
        return False


# Global queue manager instance
queue_manager = QueueManager() 