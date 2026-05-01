from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import CustomError
"""Queue clear command for clearing tasks from queue.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from datetime import timedelta
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.queue_security_adapter import QueueSecurityAdapter
from ai_admin.queue_management.queue_client import QueueClient, QueueFilter


class QueueClearCommand(BaseUnifiedCommand):
    """Command to clear tasks from queue."""

    name = "queue_clear"
    
    def __init__(self):
        """Initialize queue clear command."""
        super().__init__()
        self.queue_security_adapter = QueueSecurityAdapter()

    async def execute(
        self,
        filter_status: Optional[str] = None,
        older_than_hours: Optional[int] = None,
        older_than_days: Optional[int] = None,
        confirm: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute queue clear command.
        
        Args:
            filter_status: Filter tasks by status (all, pending, running, completed, failed, cancelled, paused)
            older_than_hours: Remove tasks older than this many hours
            older_than_days: Remove tasks older than this many days
            confirm: Confirmation flag to prevent accidental clearing
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with clear operation information
        """
        # Use unified security approach
        return await super().execute(
            filter_status=filter_status,
            older_than_hours=older_than_hours,
            older_than_days=older_than_days,
            confirm=confirm,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for queue clear command."""
        return "queue:clear"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute queue clear command logic."""
        return await self._clear_queue(**kwargs)

    async def _clear_queue(
        self,
        filter_status: Optional[str] = None,
        older_than_hours: Optional[int] = None,
        older_than_days: Optional[int] = None,
        confirm: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Clear tasks from queue."""
        try:
            if not confirm:
                return {
                    "message": "Queue clear operation requires confirmation. Set confirm=true to proceed.",
                    "filter_status": filter_status,
                    "older_than_hours": older_than_hours,
                    "older_than_days": older_than_days,
                    "confirm": confirm,
                    "status": "requires_confirmation",
                }
            
            # Convert filter status to enum
            queue_filter = None
            if filter_status:
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
            
            # Calculate time range
            older_than = None
            if older_than_hours:
                older_than = timedelta(hours=older_than_hours)
            elif older_than_days:
                older_than = timedelta(days=older_than_days)
            
            async with QueueClient() as client:
                result = await client.clear_queue(
                    filter_status=queue_filter,
                    older_than=older_than,
                )
                
                return {
                    "message": f"Queue cleared successfully. Removed {result['removed_count']} tasks.",
                    "filter_status": filter_status,
                    "older_than_hours": older_than_hours,
                    "older_than_days": older_than_days,
                    "confirm": confirm,
                    "result": result,
                    "status": "completed",
                }

        except Exception as e:
            raise CustomError(f"Queue clear operation failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for queue clear command parameters."""
        return {
            "type": "object",
            "properties": {
                "filter_status": {
                    "type": "string",
                    "enum": ["all", "pending", "running", "completed", "failed", "cancelled", "paused"],
                    "description": "Filter tasks by status",
                },
                "older_than_hours": {
                    "type": "integer",
                    "description": "Remove tasks older than this many hours",
                    "minimum": 1,
                },
                "older_than_days": {
                    "type": "integer",
                    "description": "Remove tasks older than this many days",
                    "minimum": 1,
                },
                "confirm": {
                    "type": "boolean",
                    "description": "Confirmation flag to prevent accidental clearing",
                    "default": False,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
