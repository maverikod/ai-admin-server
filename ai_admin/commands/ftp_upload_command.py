"""FTP upload command for uploading files to FTP server with resume support."""

import os
import json
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError
from ai_admin.queue.task_queue import TaskQueue, Task, TaskType, TaskStatus


class FtpUploadCommand(Command):
    """Upload files to FTP server with resume support via queue."""
    
    name = "ftp_upload"
    
    async def execute(
        self,
        local_path: str,
        remote_path: Optional[str] = None,
        resume: bool = True,
        overwrite: bool = False,
        use_queue: bool = True,
        **kwargs
    ) -> SuccessResult:
        """Execute FTP upload operation with resume support.
        
        Args:
            local_path: Local file path to upload
            remote_path: Remote file path (optional, uses local filename if not provided)
            resume: Enable resume/append mode for interrupted uploads
            overwrite: Overwrite existing file (disables resume)
            use_queue: Use queue for long-running operations
            
        Returns:
            Success or error result
        """
        try:
            # Validate inputs
            if not local_path:
                raise ValidationError("Local file path is required")
            
            if not os.path.exists(local_path):
                return ErrorResult(
                    message=f"Local file not found: {local_path}",
                    code="FILE_NOT_FOUND",
                    details={"local_path": local_path}
                )
            
            # Use local filename if remote_path not provided
            if not remote_path:
                remote_path = os.path.basename(local_path)
            
            # Get file size for progress tracking
            file_size = os.path.getsize(local_path)
            
            # Use queue for long-running operations
            if use_queue:
                # Create task
                task = Task(
                    task_type=TaskType.FTP_UPLOAD,
                    params={
                        "local_path": local_path,
                        "remote_path": remote_path,
                        "resume": resume,
                        "overwrite": overwrite,
                        "file_size": file_size
                    },
                    category="ftp",
                    tags=["upload", "file_transfer"]
                )
                
                # Add to queue
                queue = TaskQueue()
                task_id = await queue.add_task(task)
                
                return SuccessResult(data={
                    "status": "queued",
                    "message": "FTP upload task added to queue",
                    "task_id": task_id,
                    "local_path": local_path,
                    "remote_path": remote_path,
                    "file_size": file_size,
                    "resume": resume,
                    "overwrite": overwrite,
                    "queue_position": len(await queue.get_tasks_by_status(TaskStatus.PENDING))
                })
            
            # Direct execution (for small files or testing)
            result = await self._execute_ftp_upload(local_path, remote_path, resume, overwrite)
            return SuccessResult(data=result)
            
        except ValidationError as e:
            return ErrorResult(
                message=str(e),
                code="VALIDATION_ERROR"
            )
        except Exception as e:
            return ErrorResult(
                message=f"FTP upload command failed: {str(e)}",
                code="FTP_UPLOAD_ERROR",
                details={"local_path": local_path, "remote_path": remote_path, "error": str(e)}
            )
    
    async def _execute_ftp_upload(self, local_path: str, remote_path: str, resume: bool, overwrite: bool) -> Dict[str, Any]:
        """Execute FTP upload directly."""
        # This will be implemented in the queue execution
        return {
            "status": "direct_execution_not_supported",
            "message": "Use queue for FTP upload operations"
        }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for FTP upload command parameters."""
        return {
            "type": "object",
            "properties": {
                "local_path": {
                    "type": "string",
                    "description": "Local file path to upload",
                    "examples": ["/path/to/file.txt", "./data.csv"]
                },
                "remote_path": {
                    "type": "string",
                    "description": "Remote file path (optional, uses local filename if not provided)",
                    "examples": ["uploads/file.txt", "data/backup.csv"]
                },
                "resume": {
                    "type": "boolean",
                    "description": "Enable resume/append mode for interrupted uploads",
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
            "required": ["local_path"],
            "additionalProperties": False
        } 