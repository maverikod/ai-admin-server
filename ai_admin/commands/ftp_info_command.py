from ai_admin.core.custom_exceptions import CustomError
"""FTP info command for getting file information from FTP server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.ftp_security_adapter import FtpSecurityAdapter
from ai_admin.ftp.ftp_client import FTPClient


class FtpInfoCommand(BaseUnifiedCommand):
    """Get file information from FTP server with SSL/mTLS security."""

    name = "ftp_info"

    def __init__(self):
        """Initialize FTP info command."""
        super().__init__()
        self.security_adapter = FtpSecurityAdapter()

    async def execute(
        self,
        remote_path: str,
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
        """Execute FTP info operation with SSL/mTLS security.

        Args:
            remote_path: Remote file/directory path
            host: FTP server hostname
            port: FTP server port
            username: FTP username
            password: FTP password
            use_ftps: Use FTPS (FTP over SSL/TLS)
            passive_mode: Use passive mode
            use_queue: Use queue for operations
            user_roles: List of user roles for security validation

        Returns:
            Success result with file information
        """
        # Validate inputs
        if not remote_path:
            return ErrorResult(message="Remote path is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            remote_path=remote_path,
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
        """Get default operation name for FTP info command."""
        return "ftp:info"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute FTP info command logic."""
        return await self._get_file_info(**kwargs)

    async def _get_file_info(
        self,
        remote_path: str,
        host: Optional[str] = None,
        port: int = 21,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ftps: bool = False,
        passive_mode: bool = True,
        use_queue: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get file information from FTP server."""
        try:
            if use_queue:
                # Use queue for FTP operations
                from ai_admin.task_queue.queue_manager import queue_manager
                from ai_admin.task_queue.task_queue import Task, TaskType

                task = Task(
                    task_type=TaskType.FTP_INFO,
                    params={
                        "remote_path": remote_path,
                        "host": host,
                        "port": port,
                        "username": username,
                        "password": password,
                        "use_ftps": use_ftps,
                        "passive_mode": passive_mode,
                        "operation": "info",
                    },
                    priority=1,
                )

                task_id = await queue_manager.add_task(task)

                return {
                    "message": f"FTP info task queued for '{remote_path}'",
                    "remote_path": remote_path,
                    "use_queue": use_queue,
                    "task_id": task_id,
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
                    result = ftp_client.get_file_info(remote_path)

                return {
                    "message": f"FTP file info retrieved for '{remote_path}'",
                    "remote_path": remote_path,
                    "use_queue": use_queue,
                    "status": "completed",
                    "result": result,
                }

        except CustomError as e:
            raise CustomError(f"FTP info failed: {str(e)}")
        except Exception as e:
            raise CustomError(f"FTP info failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for FTP info command parameters."""
        return {
            "type": "object",
            "properties": {
                "remote_path": {
                    "type": "string",
                    "description": "Remote file/directory path",
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
            "required": ["remote_path"],
            "additionalProperties": False,
        }
