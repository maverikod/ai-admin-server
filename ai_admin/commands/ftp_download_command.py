"""FTP download command for downloading files from FTP server with resume support."""

import os
import json
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError
from ai_admin.queue.task_queue import TaskQueue, Task, TaskType, TaskStatus


class FtpDownloadCommand(Command):
    """Download files from FTP server with resume support via queue."""
    
    name = "ftp_download"
    
    async def execute(
        self,
        remote_path: str,
        local_path: Optional[str] = None,
        resume: bool = True,
        overwrite: bool = False,
        use_queue: bool = True,
        **kwargs
    ) -> SuccessResult:
        """Execute FTP download operation with resume support.
        
        Args:
            remote_path: Remote file path to download
            local_path: Local file path (optional, uses remote filename if not provided)
            resume: Enable resume mode for interrupted downloads
            overwrite: Overwrite existing file (disables resume)
            use_queue: Use queue for long-running operations
            
        Returns:
            Success or error result
        """
        try:
            # Validate inputs
            if not remote_path:
                raise ValidationError("Remote file path is required")
            
            # Use remote filename if local_path not provided
            if not local_path:
                local_path = os.path.basename(remote_path)
            
            # Check if local file exists for resume
            local_file_exists = os.path.exists(local_path)
            local_file_size = os.path.getsize(local_path) if local_file_exists else 0
            
            # Use queue for long-running operations
            if use_queue:
                # Create task
                task = Task(
                    task_type=TaskType.FTP_DOWNLOAD,
                    params={
                        "remote_path": remote_path,
                        "local_path": local_path,
                        "resume": resume,
                        "overwrite": overwrite,
                        "local_file_exists": local_file_exists,
                        "local_file_size": local_file_size
                    },
                    category="ftp",
                    tags=["download", "file_transfer"]
                )
                
                # Add to queue
                queue = TaskQueue()
                task_id = await queue.add_task(task)
                
                return SuccessResult(data={
                    "status": "queued",
                    "message": "FTP download task added to queue",
                    "task_id": task_id,
                    "remote_path": remote_path,
                    "local_path": local_path,
                    "resume": resume,
                    "overwrite": overwrite,
                    "local_file_exists": local_file_exists,
                    "local_file_size": local_file_size,
                    "queue_position": len(await queue.get_tasks_by_status(TaskStatus.PENDING))
                })
            
            # Direct execution (for small files or testing)
            result = await self._execute_ftp_download(remote_path, local_path, resume, overwrite)
            return SuccessResult(data=result)
            
        except ValidationError as e:
            return ErrorResult(
                message=str(e),
                code="VALIDATION_ERROR"
            )
        except Exception as e:
            return ErrorResult(
                message=f"FTP download command failed: {str(e)}",
                code="FTP_DOWNLOAD_ERROR",
                details={"remote_path": remote_path, "local_path": local_path, "error": str(e)}
            )
    
    async def _execute_ftp_download(self, remote_path: str, local_path: str, resume: bool, overwrite: bool) -> Dict[str, Any]:
        """Execute FTP download directly."""
        # This will be implemented in the queue execution
        return {
            "status": "direct_execution_not_supported",
            "message": "Use queue for FTP download operations"
        }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for FTP download command parameters."""
        return {
            "type": "object",
            "properties": {
                "remote_path": {
                    "type": "string",
                    "description": "Remote file path to download",
                    "examples": ["uploads/file.txt", "data/backup.csv"]
                },
                "local_path": {
                    "type": "string",
                    "description": "Local file path (optional, uses remote filename if not provided)",
                    "examples": ["/path/to/file.txt", "./data.csv"]
                },
                "resume": {
                    "type": "boolean",
                    "description": "Enable resume mode for interrupted downloads",
                    "default": True
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "Overwrite existing file (disables resume)",
                    "default": False
                },
                "use_queue": {
                    "type": "boolean",
                    "description": "Use queue for long-running operations",
                    "default": True
                }
            },
            "required": ["remote_path"],
            "additionalProperties": False
        } 