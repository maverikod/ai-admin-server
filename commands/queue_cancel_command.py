from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Queue cancel command for canceling tasks in the queue.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.queue_security_adapter import QueueSecurityAdapter

class QueueCancelCommand(BaseUnifiedCommand):
    """Command to cancel tasks in the queue.

    This command cancels a pending or running Docker task in the queue.
    """

    name = "queue_cancel"
    
    def __init__(self):
        """Initialize queue cancel command."""
        super().__init__()
        self.queue_security_adapter = QueueSecurityAdapter()

    async def execute(
        self,
        action: str = "cancel",
        task_id: str = "",
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute queue cancel command.
        
        Args:
            action: Cancel action (cancel, list, status)
            task_id: Task identifier to cancel
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with cancellation status
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            task_id=task_id,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for queue cancel command."""
        return "queue:cancel"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute queue cancel command logic."""
        action = kwargs.get("action", "cancel")
        
        if action == "cancel":
            return await self._cancel_task(**kwargs)
        elif action == "list":
            return await self._list_tasks(**kwargs)
        elif action == "status":
            return await self._get_task_status(**kwargs)
        else:
            raise CustomError(f"Unknown cancel action: {action}")

    async def _cancel_task(
        self,
        task_id: str = "",
        **kwargs,
    ) -> Dict[str, Any]:
        """Cancel a task in the queue."""
        try:
            if not task_id:
                raise CustomError("Task ID is required for cancel action")

            # Mock task cancellation logic
            # In a real implementation, this would interact with the actual queue system
            cancellation_result = {
                "task_id": task_id,
                "status": "cancelled",
                "cancelled_at": "2024-01-01T00:00:00Z",
                "reason": "User requested cancellation",
            }

            return {
                "message": f"Successfully cancelled task '{task_id}'",
                "action": "cancel",
                "task_id": task_id,
                "cancellation_result": cancellation_result,
            }

        except CustomError as e:
            raise CustomError(f"Task cancellation failed: {str(e)}")

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
                    "status": "pending",
                    "created_at": "2024-01-01T00:00:00Z",
                    "command": "docker run nginx",
                },
                {
                    "task_id": "task_002",
                    "status": "running",
                    "created_at": "2024-01-01T00:01:00Z",
                    "command": "docker build .",
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

    async def _get_task_status(
        self,
        task_id: str = "",
        **kwargs,
    ) -> Dict[str, Any]:
        """Get status of a specific task."""
        try:
            if not task_id:
                raise CustomError("Task ID is required for status action")

            # Mock task status
            task_status = {
                "task_id": task_id,
                "status": "running",
                "created_at": "2024-01-01T00:00:00Z",
                "started_at": "2024-01-01T00:00:30Z",
                "progress": 75,
                "command": "docker run nginx",
            }

            return {
                "message": f"Status for task '{task_id}'",
                "action": "status",
                "task_id": task_id,
                "task_status": task_status,
            }

        except CustomError as e:
            raise CustomError(f"Task status retrieval failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for queue cancel command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Cancel action (cancel, list, status)",
                    "default": "cancel",
                    "enum": ["cancel", "list", "status"],
                },
                "task_id": {
                    "type": "string",
                    "description": "Task identifier to cancel",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }