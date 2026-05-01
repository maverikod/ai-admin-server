from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import CustomError
"""Queue logs command for getting task logs.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.queue_security_adapter import QueueSecurityAdapter
from ai_admin.queue_management.queue_client import QueueClient


class QueueLogsCommand(BaseUnifiedCommand):
    """Command to get task logs."""

    name = "queue_logs"
    
    def __init__(self):
        """Initialize queue logs command."""
        super().__init__()
        self.queue_security_adapter = QueueSecurityAdapter()

    async def execute(
        self,
        task_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute queue logs command.
        
        Args:
            task_id: Task identifier
            limit: Maximum number of log entries
            offset: Offset for pagination
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with task logs
        """
        # Use unified security approach
        return await super().execute(
            task_id=task_id,
            limit=limit,
            offset=offset,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for queue logs command."""
        return "queue:logs"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute queue logs command logic."""
        return await self._get_logs(**kwargs)

    async def _get_logs(
        self,
        task_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get task logs."""
        try:
            async with QueueClient() as client:
                result = await client.get_task_logs(
                    task_id=task_id,
                    limit=limit,
                    offset=offset,
                )
                
                return {
                    "message": f"Task logs retrieved for {task_id}",
                    "task_id": task_id,
                    "limit": limit,
                    "offset": offset,
                    "result": result,
                    "status": "completed",
                }

        except Exception as e:
            raise CustomError(f"Task logs retrieval failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for queue logs command parameters."""
        return {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Task identifier",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of log entries",
                    "minimum": 1,
                },
                "offset": {
                    "type": "integer",
                    "description": "Offset for pagination",
                    "minimum": 0,
                    "default": 0,
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
