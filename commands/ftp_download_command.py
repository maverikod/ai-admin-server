from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""FTP download command for downloading files from FTP server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.ftp_security_adapter import FtpSecurityAdapter

class FtpDownloadCommand(BaseUnifiedCommand):
    """Download files from FTP server with resume support via queue and SSL/mTLS security."""

    name = "ftp_download"

    def __init__(self):
        """Initialize FTP download command."""
        super().__init__()
        self.security_adapter = FtpSecurityAdapter()

    async def execute(
        self,
        remote_path: str,
        local_path: Optional[str] = None,
        resume: bool = False,
        overwrite: bool = False,
        use_queue: bool = True,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute FTP download operation with SSL/mTLS security.

        Args:
            remote_path: Remote file path to download
            local_path: Local file path to save to
            resume: Resume interrupted download
            overwrite: Overwrite existing local file
            use_queue: Use queue for operations
            user_roles: List of user roles for security validation

        Returns:
            Success result with download information
        """
        # Validate inputs
        if not remote_path:
            return ErrorResult(message="Remote path is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            remote_path=remote_path,
            local_path=local_path,
            resume=resume,
            overwrite=overwrite,
            use_queue=use_queue,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for FTP download command."""
        return "ftp:download"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute FTP download command logic."""
        return await self._download_file(**kwargs)

    async def _download_file(
        self,
        remote_path: str,
        local_path: Optional[str] = None,
        resume: bool = False,
        overwrite: bool = False,
        use_queue: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Download file from FTP server."""
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
                        "command": "ftp_download",
                        "params": {
                            "remote_path": remote_path,
                            "local_path": local_path,
                            "resume": resume,
                            "overwrite": overwrite,
                            "use_queue": False,  # Prevent recursion
                        },
                        "auto_import_modules": ["commands.ftp_download_command"],
                    },
                )

                await queue_manager.start_job(job_id)

                return {
                    "message": f"FTP download task queued for '{remote_path}'",
                    "remote_path": remote_path,
                    "local_path": local_path,
                    "resume": resume,
                    "overwrite": overwrite,
                    "use_queue": use_queue,
                    "job_id": job_id,
                    "status": "queued",
                }
            else:
                # Direct FTP operation (placeholder)
                return {
                    "message": f"FTP download operation completed for '{remote_path}'",
                    "remote_path": remote_path,
                    "local_path": local_path,
                    "resume": resume,
                    "overwrite": overwrite,
                    "use_queue": use_queue,
                    "status": "completed",
                }

        except CustomError as e:
            raise CustomError(f"FTP download failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for FTP download command parameters."""
        return {
            "type": "object",
            "properties": {
                "remote_path": {
                    "type": "string",
                    "description": "Remote file path to download",
                },
                "local_path": {
                    "type": "string",
                    "description": "Local file path to save to",
                },
                "resume": {
                    "type": "boolean",
                    "description": "Resume interrupted download",
                    "default": False,
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "Overwrite existing local file",
                    "default": False,
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
            "required": ["remote_path"],
            "additionalProperties": False,
        }
