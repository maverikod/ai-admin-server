from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""FTP mkdir command for creating directories on FTP server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.ftp_security_adapter import FtpSecurityAdapter
from ai_admin.ftp.ftp_client import FTPClient


class FtpMkdirCommand(BaseUnifiedCommand):
    """Create directories on FTP server with SSL/mTLS security."""

    name = "ftp_mkdir"

    def __init__(self):
        """Initialize FTP mkdir command."""
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
        """Execute FTP mkdir operation with SSL/mTLS security.

        Args:
            remote_path: Remote directory path to create
            host: FTP server hostname
            port: FTP server port
            username: FTP username
            password: FTP password
            use_ftps: Use FTPS (FTP over SSL/TLS)
            passive_mode: Use passive mode
            use_queue: Use queue for operations
            user_roles: List of user roles for security validation

        Returns:
            Success result with mkdir information
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
        """Get default operation name for FTP mkdir command."""
        return "ftp:mkdir"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute FTP mkdir command logic."""
        return await self._create_directory(**kwargs)

    async def _create_directory(
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
        """Create directory on FTP server."""
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
                        "command": "ftp_mkdir",
                        "params": {
                            "remote_path": remote_path,
                            "host": host,
                            "port": port,
                            "username": username,
                            "password": password,
                            "use_ftps": use_ftps,
                            "passive_mode": passive_mode,
                            "use_queue": False,  # Prevent recursion
                        },
                        "auto_import_modules": ["commands.ftp_mkdir_command"],
                    },
                )

                await queue_manager.start_job(job_id)

                return {
                    "message": f"FTP mkdir task queued for '{remote_path}'",
                    "remote_path": remote_path,
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
                    result = ftp_client.create_directory(remote_path)

                return {
                    "message": f"FTP directory created: '{remote_path}'",
                    "remote_path": remote_path,
                    "use_queue": use_queue,
                    "status": "completed",
                    "result": result,
                }

        except CustomError as e:
            raise CustomError(f"FTP mkdir failed: {str(e)}")
        except Exception as e:
            raise CustomError(f"FTP mkdir failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for FTP mkdir command parameters."""
        return {
            "type": "object",
            "properties": {
                "remote_path": {
                    "type": "string",
                    "description": "Remote directory path to create",
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
