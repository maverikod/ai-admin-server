from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Queue task status command for checking individual task status.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.queue_security_adapter import QueueSecurityAdapter

class QueueTaskStatusCommand(BaseUnifiedCommand):
    """Command to check individual task status in the queue.

    This command provides detailed information about a specific task in the queue.
    """

    name = "queue_task_status"
    
    def __init__(self):
        """Initialize queue task status command."""
        super().__init__()
        self.queue_security_adapter = QueueSecurityAdapter()

    async def execute(
        self,
        action: str = "status",
        task_id: str = "",
        include_logs: bool = False,
        detailed: bool = True,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute queue task status command.
        
        Args:
            action: Status action (status, logs, history)
            task_id: Task identifier to check
            include_logs: Include task logs in response
            detailed: Include detailed information
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with task status
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            task_id=task_id,
            include_logs=include_logs,
            detailed=detailed,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for queue task status command."""
        return "queue:task_status"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute queue task status command logic."""
        action = kwargs.get("action", "status")
        
        if action == "status":
            return await self._get_task_status(**kwargs)
        elif action == "logs":
            return await self._get_task_logs(**kwargs)
        elif action == "history":
            return await self._get_task_history(**kwargs)
        else:
            raise CustomError(f"Unknown task status action: {action}")

    async def _get_task_status(
        self,
        task_id: str = "",
        include_logs: bool = False,
        detailed: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get task status."""
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
                "priority": 1,
                "worker_id": "worker_001",
            }

            if detailed:
                task_status["detailed_info"] = {
                    "estimated_completion": "2024-01-01T00:02:00Z",
                    "memory_usage": "512MB",
                    "cpu_usage": "25%",
                    "retry_count": 0,
                    "max_retries": 3,
                }

            if include_logs:
                task_status["logs"] = [
                    "Task started successfully",
                    "Pulling image nginx:latest",
                    "Container started with ID abc123",
                    "Task is running normally",
                ]

            return {
                "message": f"Task status for '{task_id}' retrieved successfully",
                "action": "status",
                "task_id": task_id,
                "include_logs": include_logs,
                "detailed": detailed,
                "task_status": task_status,
            }

        except CustomError as e:
            raise CustomError(f"Task status retrieval failed: {str(e)}")

    async def _get_task_logs(
        self,
        task_id: str = "",
        **kwargs,
    ) -> Dict[str, Any]:
        """Get task logs."""
        try:
            if not task_id:
                raise CustomError("Task ID is required for logs action")

            # Mock task logs
            logs = [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "level": "INFO",
                    "message": "Task started successfully",
                },
                {
                    "timestamp": "2024-01-01T00:00:05Z",
                    "level": "INFO",
                    "message": "Pulling image nginx:latest",
                },
                {
                    "timestamp": "2024-01-01T00:00:10Z",
                    "level": "INFO",
                    "message": "Container started with ID abc123",
                },
                {
                    "timestamp": "2024-01-01T00:00:15Z",
                    "level": "INFO",
                    "message": "Task is running normally",
                },
            ]

            return {
                "message": f"Task logs for '{task_id}' retrieved successfully",
                "action": "logs",
                "task_id": task_id,
                "logs": logs,
                "log_count": len(logs),
            }

        except CustomError as e:
            raise CustomError(f"Task logs retrieval failed: {str(e)}")

    async def _get_task_history(
        self,
        task_id: str = "",
        **kwargs,
    ) -> Dict[str, Any]:
        """Get task history."""
        try:
            if not task_id:
                raise CustomError("Task ID is required for history action")

            # Mock task history
            history = [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "status": "queued",
                    "message": "Task added to queue",
                },
                {
                    "timestamp": "2024-01-01T00:00:30Z",
                    "status": "running",
                    "message": "Task started execution",
                },
                {
                    "timestamp": "2024-01-01T00:01:00Z",
                    "status": "running",
                    "message": "Task progress: 50%",
                },
                {
                    "timestamp": "2024-01-01T00:01:30Z",
                    "status": "running",
                    "message": "Task progress: 75%",
                },
            ]

            return {
                "message": f"Task history for '{task_id}' retrieved successfully",
                "action": "history",
                "task_id": task_id,
                "history": history,
                "history_count": len(history),
            }

        except CustomError as e:
            raise CustomError(f"Task history retrieval failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for queue task status command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Status action (status, logs, history)",
                    "default": "status",
                    "enum": ["status", "logs", "history"],
                },
                "task_id": {
                    "type": "string",
                    "description": "Task identifier to check",
                },
                "include_logs": {
                    "type": "boolean",
                    "description": "Include task logs in response",
                    "default": False,
                },
                "detailed": {
                    "type": "boolean",
                    "description": "Include detailed information",
                    "default": True,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["task_id"],
            "additionalProperties": False,
        }