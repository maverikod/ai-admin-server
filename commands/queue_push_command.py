from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Queue push command for pushing tasks to the queue.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.queue_security_adapter import QueueSecurityAdapter

class QueuePushCommand(BaseUnifiedCommand):
    """Command to push tasks to the queue.

    This command adds Docker tasks to the queue for execution.
    """

    name = "queue_push"
    
    def __init__(self):
        """Initialize queue push command."""
        super().__init__()
        self.queue_security_adapter = QueueSecurityAdapter()

    async def execute(
        self,
        action: str = "push",
        image_name: Optional[str] = None,
        tag: str = "latest",
        all_tags: bool = False,
        command: Optional[str] = None,
        priority: int = 1,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute queue push command.
        
        Args:
            action: Push action (push, list, status)
            image_name: Docker image name
            tag: Docker image tag
            all_tags: Push all tags
            command: Command to execute
            priority: Task priority (1-10)
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with push status
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            image_name=image_name,
            tag=tag,
            all_tags=all_tags,
            command=command,
            priority=priority,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for queue push command."""
        return "queue:push"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute queue push command logic."""
        action = kwargs.get("action", "push")
        
        if action == "push":
            return await self._push_task(**kwargs)
        elif action == "list":
            return await self._list_tasks(**kwargs)
        elif action == "status":
            return await self._get_queue_status(**kwargs)
        else:
            raise CustomError(f"Unknown push action: {action}")

    async def _push_task(
        self,
        image_name: Optional[str] = None,
        tag: str = "latest",
        all_tags: bool = False,
        command: Optional[str] = None,
        priority: int = 1,
        **kwargs,
    ) -> Dict[str, Any]:
        """Push a task to the queue."""
        try:
            if not image_name and not command:
                raise CustomError("Either image_name or command is required for push action")

            # Generate task ID
            import uuid
            task_id = str(uuid.uuid4())[:8]

            # Mock task creation
            task = {
                "task_id": task_id,
                "image_name": image_name,
                "tag": tag,
                "all_tags": all_tags,
                "command": command,
                "priority": priority,
                "status": "queued",
                "created_at": "2024-01-01T00:00:00Z",
            }

            return {
                "message": f"Successfully pushed task '{task_id}' to queue",
                "action": "push",
                "task_id": task_id,
                "task": task,
            }

        except CustomError as e:
            raise CustomError(f"Task push failed: {str(e)}")

    async def _list_tasks(
        self,
        **kwargs,
    ) -> Dict[str, Any]:
        """List tasks in the queue."""
        try:
            # Mock task list
            tasks = [
                {
                    "task_id": "task_001",
                    "image_name": "nginx",
                    "tag": "latest",
                    "status": "queued",
                    "priority": 1,
                    "created_at": "2024-01-01T00:00:00Z",
                },
                {
                    "task_id": "task_002",
                    "command": "docker build .",
                    "status": "running",
                    "priority": 2,
                    "created_at": "2024-01-01T00:01:00Z",
                },
            ]

            return {
                "message": f"Found {len(tasks)} tasks in queue",
                "action": "list",
                "tasks": tasks,
                "count": len(tasks),
            }

        except CustomError as e:
            raise CustomError(f"Task listing failed: {str(e)}")

    async def _get_queue_status(
        self,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get queue status."""
        try:
            # Mock queue status
            queue_status = {
                "total_tasks": 5,
                "queued_tasks": 2,
                "running_tasks": 1,
                "completed_tasks": 2,
                "failed_tasks": 0,
                "queue_size": 10,
                "max_queue_size": 100,
            }

            return {
                "message": "Queue status retrieved",
                "action": "status",
                "queue_status": queue_status,
            }

        except CustomError as e:
            raise CustomError(f"Queue status retrieval failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for queue push command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Push action (push, list, status)",
                    "default": "push",
                    "enum": ["push", "list", "status"],
                },
                "image_name": {
                    "type": "string",
                    "description": "Docker image name",
                },
                "tag": {
                    "type": "string",
                    "description": "Docker image tag",
                    "default": "latest",
                },
                "all_tags": {
                    "type": "boolean",
                    "description": "Push all tags",
                    "default": False,
                },
                "command": {
                    "type": "string",
                    "description": "Command to execute",
                },
                "priority": {
                    "type": "integer",
                    "description": "Task priority (1-10)",
                    "default": 1,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }