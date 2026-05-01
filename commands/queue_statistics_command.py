from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Queue statistics command for getting queue statistics.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from datetime import timedelta
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.queue_security_adapter import QueueSecurityAdapter
from ai_admin.queue_management.queue_client import QueueClient


class QueueStatisticsCommand(BaseUnifiedCommand):
    """Command to get queue statistics."""

    name = "queue_statistics"
    
    def __init__(self):
        """Initialize queue statistics command."""
        super().__init__()
        self.queue_security_adapter = QueueSecurityAdapter()

    async def execute(
        self,
        time_range_hours: Optional[int] = None,
        time_range_days: Optional[int] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute queue statistics command.
        
        Args:
            time_range_hours: Time range in hours
            time_range_days: Time range in days
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with queue statistics
        """
        # Use unified security approach
        return await super().execute(
            time_range_hours=time_range_hours,
            time_range_days=time_range_days,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for queue statistics command."""
        return "queue:statistics"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute queue statistics command logic."""
        return await self._get_statistics(**kwargs)

    async def _get_statistics(
        self,
        time_range_hours: Optional[int] = None,
        time_range_days: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get queue statistics."""
        try:
            # Calculate time range
            time_range = None
            if time_range_hours:
                time_range = timedelta(hours=time_range_hours)
            elif time_range_days:
                time_range = timedelta(days=time_range_days)
            
            async with QueueClient() as client:
                result = await client.get_queue_statistics(time_range=time_range)
                
                return {
                    "message": "Queue statistics retrieved successfully",
                    "time_range_hours": time_range_hours,
                    "time_range_days": time_range_days,
                    "result": result,
                    "status": "completed",
                }

        except Exception as e:
            raise CustomError(f"Queue statistics retrieval failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for queue statistics command parameters."""
        return {
            "type": "object",
            "properties": {
                "time_range_hours": {
                    "type": "integer",
                    "description": "Time range in hours for statistics",
                    "minimum": 1,
                },
                "time_range_days": {
                    "type": "integer",
                    "description": "Time range in days for statistics",
                    "minimum": 1,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
