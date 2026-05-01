from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""FTP list command for listing files on FTP server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.ftp_security_adapter import FtpSecurityAdapter

class FtpListCommand(BaseUnifiedCommand):
    """List files on FTP server via queue with SSL/mTLS security."""

    name = "ftp_list"

    def __init__(self):
        """Initialize FTP list command."""
        super().__init__()
        self.security_adapter = FtpSecurityAdapter()

    async def execute(
        self,
        remote_path: str = "/",
        use_queue: bool = True,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute FTP list operation with SSL/mTLS security.

        Args:
            remote_path: Remote directory path to list (default: "/")
            use_queue: Use queue for operations
            user_roles: List of user roles for security validation

        Returns:
            Success result with list information
        """
        # Use unified security approach
        return await super().execute(
            remote_path=remote_path,
            use_queue=use_queue,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for FTP list command."""
        return "ftp:list"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute FTP list command logic."""
        return await self._list_files(**kwargs)

    async def _list_files(
        self,
        remote_path: str = "/",
        use_queue: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """List files on FTP server."""
        try:
            if use_queue:
                # Use queue for FTP operations
                import uuid
                from mcp_proxy_adapter.integrations.queuemgr_integration import (
                    get_global_queue_manager,
                )
                from mcp_proxy_adapter.commands.queue.jobs import CommandExecutionJob

                queue_manager = await get_global_queue_manager()
                if queue_manager is None:
                    raise CustomError("Queue manager is not available")

                job_id = str(uuid.uuid4())

                await queue_manager.add_job(
                    CommandExecutionJob,
                    job_id,
                    {
                        "command": "ftp_list",
                        "params": {
                            "remote_path": remote_path,
                            "use_queue": False,  # Prevent recursion
                        },
                        "auto_import_modules": ["commands.ftp_list_command"],
                    },
                )

                await queue_manager.start_job(job_id)

                return {
                    "message": f"FTP list task queued for '{remote_path}'",
                    "remote_path": remote_path,
                    "use_queue": use_queue,
                    "job_id": job_id,
                    "status": "queued",
                }
            else:
                # Direct FTP operation (placeholder)
                return {
                    "message": f"FTP list operation completed for '{remote_path}'",
                    "remote_path": remote_path,
                    "use_queue": use_queue,
                    "files": [],  # Placeholder for actual file list
                    "status": "completed",
                }

        except CustomError as e:
            raise CustomError(f"FTP list failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for FTP list command parameters."""
        return {
            "type": "object",
            "properties": {
                "remote_path": {
                    "type": "string",
                    "description": "Remote directory path to list",
                    "default": "/",
                },
                "use_queue": {
                    "type": "boolean",
                    "description": "Use queue for operations",
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
