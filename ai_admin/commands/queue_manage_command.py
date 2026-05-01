from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import CustomError

"""Queue manage command for managing tasks in the queue.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.queue_security_adapter import QueueSecurityAdapter


class QueueManageCommand(BaseUnifiedCommand):
    """Command to manage tasks in the queue.

    This command provides functionality for pausing, resuming, retrying, and cancelling tasks.
    """

    name = "queue_manage"

    def __init__(self):
        """Initialize queue manage command."""
        super().__init__()
        self.queue_security_adapter = QueueSecurityAdapter()

    async def execute(
        self,
        action: str,
        task_id: str,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute queue management command.

        Args:
            action: Action to perform (pause, resume, retry, cancel)
            task_id: Task identifier to manage
            user_roles: List of user roles for security validation

        Returns:
            Success result with management status
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            task_id=task_id,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for queue manage command."""
        return "queue:manage"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute queue manage command logic."""
        action = kwargs.get("action")
        task_id = kwargs.get("task_id")

        if action == "pause":
            return await self._pause_task(task_id, **kwargs)
        elif action == "resume":
            return await self._resume_task(task_id, **kwargs)
        elif action == "retry":
            return await self._retry_task(task_id, **kwargs)
        elif action == "cancel":
            return await self._cancel_task(task_id, **kwargs)
        else:
            raise CustomError(f"Unknown management action: {action}")

    async def _pause_task(
        self,
        task_id: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Pause a task in the queue."""
        try:
            if not task_id:
                raise CustomError("Task ID is required for pause action")

            # Mock task pause logic
            pause_result = {
                "task_id": task_id,
                "status": "paused",
                "paused_at": "2024-01-01T00:00:00Z",
                "reason": "User requested pause",
            }

            return {
                "message": f"Successfully paused task '{task_id}'",
                "action": "pause",
                "task_id": task_id,
                "pause_result": pause_result,
            }

        except CustomError as e:
            raise CustomError(f"Task pause failed: {str(e)}")

    async def _resume_task(
        self,
        task_id: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Resume a paused task in the queue."""
        try:
            if not task_id:
                raise CustomError("Task ID is required for resume action")

            # Mock task resume logic
            resume_result = {
                "task_id": task_id,
                "status": "resumed",
                "resumed_at": "2024-01-01T00:00:00Z",
                "reason": "User requested resume",
            }

            return {
                "message": f"Successfully resumed task '{task_id}'",
                "action": "resume",
                "task_id": task_id,
                "resume_result": resume_result,
            }

        except CustomError as e:
            raise CustomError(f"Task resume failed: {str(e)}")

    async def _retry_task(
        self,
        task_id: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Retry a failed task in the queue."""
        try:
            if not task_id:
                raise CustomError("Task ID is required for retry action")

            # Mock task retry logic
            retry_result = {
                "task_id": task_id,
                "status": "retrying",
                "retried_at": "2024-01-01T00:00:00Z",
                "retry_count": 1,
                "reason": "User requested retry",
            }

            return {
                "message": f"Successfully retried task '{task_id}'",
                "action": "retry",
                "task_id": task_id,
                "retry_result": retry_result,
            }

        except CustomError as e:
            raise CustomError(f"Task retry failed: {str(e)}")

    async def _cancel_task(
        self,
        task_id: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Cancel a task in the queue."""
        try:
            if not task_id:
                raise CustomError("Task ID is required for cancel action")

            # Mock task cancellation logic
            cancel_result = {
                "task_id": task_id,
                "status": "cancelled",
                "cancelled_at": "2024-01-01T00:00:00Z",
                "reason": "User requested cancellation",
            }

            return {
                "message": f"Successfully cancelled task '{task_id}'",
                "action": "cancel",
                "task_id": task_id,
                "cancel_result": cancel_result,
            }

        except CustomError as e:
            raise CustomError(f"Task cancellation failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for queue manage command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform (pause, resume, retry, cancel)",
                    "enum": ["pause", "resume", "retry", "cancel"],
                },
                "task_id": {
                    "type": "string",
                    "description": "Task identifier to manage",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["action", "task_id"],
            "additionalProperties": False,
        }
