from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import CustomError
"""Queue filter command for filtering tasks in queue.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.queue_security_adapter import QueueSecurityAdapter
from ai_admin.queue_management.queue_client import QueueClient, QueueFilter


class QueueFilterCommand(BaseUnifiedCommand):
    """Command to filter tasks in queue."""

    name = "queue_filter"
    
    def __init__(self):
        """Initialize queue filter command."""
        super().__init__()
        self.queue_security_adapter = QueueSecurityAdapter()

    async def execute(
        self,
        filter_status: str = "all",
        include_logs: bool = False,
        detailed: bool = True,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute queue filter command.
        
        Args:
            filter_status: Filter tasks by status (all, pending, running, completed, failed, cancelled, paused)
            include_logs: Include task logs in response
            detailed: Include detailed information
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with filtered tasks
        """
        # Use unified security approach
        return await super().execute(
            filter_status=filter_status,
            include_logs=include_logs,
            detailed=detailed,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for queue filter command."""
        return "queue:filter"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute queue filter command logic."""
        return await self._filter_tasks(**kwargs)

    async def _filter_tasks(
        self,
        filter_status: str = "all",
        include_logs: bool = False,
        detailed: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Filter tasks in queue."""
        try:
            # Convert filter status to enum
            filter_map = {
                "all": QueueFilter.ALL,
                "pending": QueueFilter.PENDING,
                "running": QueueFilter.RUNNING,
                "completed": QueueFilter.COMPLETED,
                "failed": QueueFilter.FAILED,
                "cancelled": QueueFilter.CANCELLED,
                "paused": QueueFilter.PAUSED,
            }
            
            queue_filter = filter_map.get(filter_status.lower())
            if not queue_filter:
                raise CustomError(f"Invalid filter status: {filter_status}")
            
            async with QueueClient() as client:
                result = await client.get_queue_status(
                    include_logs=include_logs,
                    detailed=detailed,
                    filter_status=queue_filter,
                )
                
                return {
                    "message": f"Tasks filtered by status: {filter_status}",
                    "filter_status": filter_status,
                    "include_logs": include_logs,
                    "detailed": detailed,
                    "result": result,
                    "status": "completed",
                }

        except Exception as e:
            raise CustomError(f"Queue filtering failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for queue filter command parameters."""
        return {
            "type": "object",
            "properties": {
                "filter_status": {
                    "type": "string",
                    "enum": ["all", "pending", "running", "completed", "failed", "cancelled", "paused"],
                    "description": "Filter tasks by status",
                    "default": "all",
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
