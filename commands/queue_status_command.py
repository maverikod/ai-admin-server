from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Queue status command for checking queue status.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.queue_security_adapter import QueueSecurityAdapter

class QueueStatusCommand(BaseUnifiedCommand):
    """Command to check queue status.

    This command provides detailed information about the current state of the task queue.
    """

    name = "queue_status"
    
    def __init__(self):
        """Initialize queue status command."""
        super().__init__()
        self.queue_security_adapter = QueueSecurityAdapter()

    async def execute(
        self,
        action: str = "status",
        include_logs: bool = False,
        detailed: bool = True,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute queue status command.
        
        Args:
            action: Status action (status, health, metrics)
            include_logs: Include task logs in response
            detailed: Include detailed information
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with queue status
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            include_logs=include_logs,
            detailed=detailed,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for queue status command."""
        return "queue:status"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute queue status command logic."""
        action = kwargs.get("action", "status")
        
        if action == "status":
            return await self._get_queue_status(**kwargs)
        elif action == "health":
            return await self._get_queue_health(**kwargs)
        elif action == "metrics":
            return await self._get_queue_metrics(**kwargs)
        else:
            raise CustomError(f"Unknown status action: {action}")

    async def _get_queue_status(
        self,
        include_logs: bool = False,
        detailed: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get queue status."""
        try:
            # Mock queue status
            queue_status = {
                "queue_name": "default",
                "total_tasks": 10,
                "queued_tasks": 3,
                "running_tasks": 2,
                "completed_tasks": 4,
                "failed_tasks": 1,
                "queue_size": 10,
                "max_queue_size": 100,
                "status": "healthy",
                "last_updated": "2024-01-01T00:00:00Z",
            }

            if detailed:
                queue_status["detailed_info"] = {
                    "average_task_duration": "2m 30s",
                    "success_rate": 0.8,
                    "active_workers": 2,
                    "max_workers": 5,
                }

            if include_logs:
                queue_status["recent_logs"] = [
                    "Task task_001 completed successfully",
                    "Task task_002 started execution",
                    "Task task_003 failed with error: timeout",
                ]

            return {
                "message": "Queue status retrieved successfully",
                "action": "status",
                "include_logs": include_logs,
                "detailed": detailed,
                "queue_status": queue_status,
            }

        except CustomError as e:
            raise CustomError(f"Queue status retrieval failed: {str(e)}")

    async def _get_queue_health(
        self,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get queue health status."""
        try:
            # Mock queue health
            health_status = {
                "status": "healthy",
                "checks": {
                    "queue_accessible": True,
                    "workers_running": True,
                    "storage_available": True,
                    "memory_usage": "45%",
                    "cpu_usage": "30%",
                },
                "last_check": "2024-01-01T00:00:00Z",
            }

            return {
                "message": "Queue health check completed",
                "action": "health",
                "health_status": health_status,
            }

        except CustomError as e:
            raise CustomError(f"Queue health check failed: {str(e)}")

    async def _get_queue_metrics(
        self,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get queue metrics."""
        try:
            # Mock queue metrics
            metrics = {
                "throughput": {
                    "tasks_per_minute": 5.2,
                    "tasks_per_hour": 312,
                    "tasks_per_day": 7488,
                },
                "performance": {
                    "average_task_duration": "2m 30s",
                    "success_rate": 0.8,
                    "failure_rate": 0.2,
                },
                "resources": {
                    "memory_usage": "45%",
                    "cpu_usage": "30%",
                    "disk_usage": "60%",
                },
                "timestamps": {
                    "collected_at": "2024-01-01T00:00:00Z",
                    "period": "last_24_hours",
                },
            }

            return {
                "message": "Queue metrics retrieved successfully",
                "action": "metrics",
                "metrics": metrics,
            }

        except CustomError as e:
            raise CustomError(f"Queue metrics retrieval failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for queue status command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Status action (status, health, metrics)",
                    "default": "status",
                    "enum": ["status", "health", "metrics"],
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
            "additionalProperties": False,
        }