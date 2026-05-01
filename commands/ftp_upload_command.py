from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""FTP upload command for uploading files to FTP server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.ftp_security_adapter import FtpSecurityAdapter
from ai_admin.ftp.ftp_client import FTPClient

class FtpUploadCommand(BaseUnifiedCommand):
    """Upload files to FTP server with resume support via queue and SSL/mTLS security."""

    name = "ftp_upload"

    def __init__(self):
        """Initialize FTP upload command."""
        super().__init__()
        self.security_adapter = FtpSecurityAdapter()

    async def execute(
        self,
        local_path: str,
        remote_path: Optional[str] = None,
        resume: bool = False,
        overwrite: bool = False,
        use_queue: bool = True,
        host: Optional[str] = None,
        port: int = 21,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ftps: bool = False,
        passive_mode: bool = True,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute FTP upload operation with SSL/mTLS security.

        Args:
            local_path: Local file path to upload
            remote_path: Remote file path to save to
            resume: Resume interrupted upload
            overwrite: Overwrite existing remote file
            use_queue: Use queue for operations (ALWAYS True for upload)
            host: FTP server hostname
            port: FTP server port
            username: FTP username
            password: FTP password
            use_ftps: Use FTPS (FTP over SSL/TLS)
            passive_mode: Use passive mode
            user_roles: List of user roles for security validation

        Returns:
            Success result with upload information
        """
        # Validate inputs
        if not local_path:
            return ErrorResult(message="Local path is required", code="VALIDATION_ERROR")
        
        if not os.path.exists(local_path):
            return ErrorResult(message=f"Local file not found: {local_path}", code="FILE_NOT_FOUND")

        # Upload/download operations MUST use queue
        use_queue = True

        # Use unified security approach
        return await super().execute(
            local_path=local_path,
            remote_path=remote_path,
            resume=resume,
            overwrite=overwrite,
            use_queue=use_queue,
            host=host,
            port=port,
            username=username,
            password=password,
            use_ftps=use_ftps,
            passive_mode=passive_mode,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for FTP upload command."""
        return "ftp:upload"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute FTP upload command logic."""
        return await self._upload_file(**kwargs)

    async def _upload_file(
        self,
        local_path: str,
        remote_path: Optional[str] = None,
        resume: bool = False,
        overwrite: bool = False,
        use_queue: bool = True,
        host: Optional[str] = None,
        port: int = 21,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ftps: bool = False,
        passive_mode: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Upload file to FTP server."""
        try:
            # Upload operations MUST use queue
            if not use_queue:
                use_queue = True

            if use_queue:
                # Use queue for FTP operations
                import uuid
                from mcp_proxy_adapter.integrations.queuemgr_integration import (
                    get_global_queue_manager,
                )
                from mcp_proxy_adapter.commands.queue.jobs import CommandExecutionJob

                # Get queue manager
                queue_manager = await get_global_queue_manager()
                if queue_manager is None:
                    return ErrorResult(
                        message="Queue manager is not available",
                        code="QUEUE_UNAVAILABLE",
                    )

                # Set default remote path if not provided
                if not remote_path:
                    remote_path = f"/{os.path.basename(local_path)}"

                # Create job ID
                job_id = str(uuid.uuid4())

                # Add job to queue using CommandExecutionJob
                await queue_manager.add_job(
                    CommandExecutionJob,
                    job_id,
                    {
                        "command": "ftp_upload",
                        "params": {
                            "local_path": local_path,
                            "remote_path": remote_path,
                            "resume": resume,
                            "overwrite": overwrite,
                            "host": host,
                            "port": port,
                            "username": username,
                            "password": password,
                            "use_ftps": use_ftps,
                            "passive_mode": passive_mode,
                            "operation": "upload",
                            "use_queue": False,  # Prevent recursion
                        },
                        "auto_import_modules": ["commands.ftp_upload_command"],
                    },
                )

                # Start the job
                await queue_manager.start_job(job_id)

                return {
                    "message": f"FTP upload task queued for '{local_path}'",
                    "local_path": local_path,
                    "remote_path": remote_path,
                    "resume": resume,
                    "overwrite": overwrite,
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

                # Set default remote path if not provided
                if not remote_path:
                    remote_path = f"/{os.path.basename(local_path)}"

                with FTPClient(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    use_ftps=use_ftps,
                    passive_mode=passive_mode,
                ).connection() as ftp_client:
                    result = ftp_client.upload_file(
                        local_path=local_path,
                        remote_path=remote_path,
                        resume=resume,
                        overwrite=overwrite,
                    )

                return {
                    "message": f"FTP upload completed for '{local_path}'",
                    "local_path": local_path,
                    "remote_path": remote_path,
                    "resume": resume,
                    "overwrite": overwrite,
                    "use_queue": use_queue,
                    "status": "completed",
                    "result": result,
                }

        except CustomError as e:
            raise CustomError(f"FTP upload failed: {str(e)}")
        except Exception as e:
            raise CustomError(f"FTP upload failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for FTP upload command parameters."""
        return {
            "type": "object",
            "properties": {
                "local_path": {
                    "type": "string",
                    "description": "Local file path to upload",
                },
                "remote_path": {
                    "type": "string",
                    "description": "Remote file path to save to",
                },
                "resume": {
                    "type": "boolean",
                    "description": "Resume interrupted upload",
                    "default": False,
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "Overwrite existing remote file",
                    "default": False,
                },
                "use_queue": {
                    "type": "boolean",
                    "description": "Use queue for operations (ALWAYS True for upload)",
                    "default": True,
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
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["local_path"],
            "additionalProperties": False,
        }
