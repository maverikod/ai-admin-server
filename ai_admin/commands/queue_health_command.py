"""Queue health command."""

from mcp_proxy_adapter.commands.result import SuccessResult

from ai_admin.core.custom_exceptions import CustomError

"""Queue health command for checking queue health.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""


from typing import Dict, Any, Optional, List

from ai_admin.commands.base_unified_command import BaseUnifiedCommand

from ai_admin.security.queue_security_adapter import QueueSecurityAdapter

from ai_admin.queue_management.queue_client import QueueClient


class QueueHealthCommand:
    """Command to check queue health."""

    name = "queue_health"

    def __init__(self):
        """Initialize queue health command."""
        super().__init__()
        self.queue_security_adapter = QueueSecurityAdapter()

    async def execute(
        self,
        detailed: bool = True,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute queue health command.

        Args:
            detailed: Include detailed health information
            user_roles: List of user roles for security validation

        Returns:
            Success result with queue health information
        """
        # Use unified security approach
        return await super().execute(
            detailed=detailed,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for queue health command."""
        return "queue:health"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute queue health command logic."""
        return await self._get_health(**kwargs)

    async def _get_health(
        self,
        detailed: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get queue health information."""
        try:
            async with QueueClient() as client:
                result = await client.get_queue_health()

                return {
                    "message": "Queue health check completed",
                    "detailed": detailed,
                    "result": result,
                    "status": "completed",
                }

        except Exception as e:
            raise CustomError(f"Queue health check failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for queue health command parameters."""
        return {
            "type": "object",
            "properties": {
                "detailed": {
                    "type": "boolean",
                    "description": "Include detailed health information",
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
