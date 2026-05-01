from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""FTP rename command for renaming files on FTP server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.ftp_security_adapter import FtpSecurityAdapter
from ai_admin.ftp.ftp_client import FTPClient


class FtpRenameCommand(BaseUnifiedCommand):
    """Rename files on FTP server with SSL/mTLS security."""

    name = "ftp_rename"

    def __init__(self):
        """Initialize FTP rename command."""
        super().__init__()
        self.security_adapter = FtpSecurityAdapter()

    async def execute(
        self,
        old_path: str,
        new_path: str,
        host: Optional[str] = None,
        port: int = 21,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ftps: bool = False,
        passive_mode: bool = True,
        use_queue: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute FTP rename operation with SSL/mTLS security.

        Args:
            old_path: Current file/directory path
            new_path: New file/directory path
            host: FTP server hostname
            port: FTP server port
            username: FTP username
            password: FTP password
            use_ftps: Use FTPS (FTP over SSL/TLS)
            passive_mode: Use passive mode
            use_queue: Use queue for operations
            user_roles: List of user roles for security validation

        Returns:
            Success result with rename information
        """
        # Validate inputs
        if not old_path:
            return ErrorResult(message="Old path is required", code="VALIDATION_ERROR")
        if not new_path:
            return ErrorResult(message="New path is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            old_path=old_path,
            new_path=new_path,
            host=host,
            port=port,
            username=username,
            password=password,
            use_ftps=use_ftps,
            passive_mode=passive_mode,
            use_queue=use_queue,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for FTP rename command."""
        return "ftp:rename"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute FTP rename command logic."""
        return await self._rename_file(**kwargs)

    async def _rename_file(
        self,
        old_path: str,
        new_path: str,
        host: Optional[str] = None,
        port: int = 21,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ftps: bool = False,
        passive_mode: bool = True,
        use_queue: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Rename file on FTP server."""
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
                        "command": "ftp_rename",
                        "params": {
                            "old_path": old_path,
                            "new_path": new_path,
                            "host": host,
                            "port": port,
                            "username": username,
                            "password": password,
                            "use_ftps": use_ftps,
                            "passive_mode": passive_mode,
                            "use_queue": False,  # Prevent recursion
                        },
                        "auto_import_modules": ["commands.ftp_rename_command"],
                    },
                )

                await queue_manager.start_job(job_id)

                return {
                    "message": f"FTP rename task queued for '{old_path}' to '{new_path}'",
                    "old_path": old_path,
                    "new_path": new_path,
                    "use_queue": use_queue,
                    "job_id": job_id,
                    "status": "queued",
                    "host": host,
                    "port": port,
                    "use_ftps": use_ftps,
                    "passive_mode": passive_mode,
                }
            else:
                # Direct FTP operation using FTP client
                if not host:
                    raise CustomError("FTP host is required for direct execution")

                with FTPClient(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    use_ftps=use_ftps,
                    passive_mode=passive_mode,
                ).connection() as ftp_client:
                    result = ftp_client.rename_file(old_path, new_path)

                return {
                    "message": f"FTP file renamed from '{old_path}' to '{new_path}'",
                    "old_path": old_path,
                    "new_path": new_path,
                    "use_queue": use_queue,
                    "status": "completed",
                    "result": result,
                }

        except CustomError as e:
            raise CustomError(f"FTP rename failed: {str(e)}")
        except Exception as e:
            raise CustomError(f"FTP rename failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for FTP rename command parameters."""
        return {
            "type": "object",
            "properties": {
                "old_path": {
                    "type": "string",
                    "description": "Current file/directory path",
                },
                "new_path": {
                    "type": "string",
                    "description": "New file/directory path",
                },
                "host": {
                    "type": "string",
                    "description": "FTP server hostname",
                },
                "port": {
                    "type": "integer",
                    "description": "FTP server port",
                    "default": 21,
                },
                "username": {
                    "type": "string",
                    "description": "FTP username",
                },
                "password": {
                    "type": "string",
                    "description": "FTP password",
                },
                "use_ftps": {
                    "type": "boolean",
                    "description": "Use FTPS (FTP over SSL/TLS)",
                    "default": False,
                },
                "passive_mode": {
                    "type": "boolean",
                    "description": "Use passive mode",
                    "default": True,
                },
                "use_queue": {
                    "type": "boolean",
                    "description": "Use queue for operations",
                    "default": False,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["old_path", "new_path"],
            "additionalProperties": False,
        }
