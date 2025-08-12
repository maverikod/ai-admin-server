"""FTP delete command for deleting files on FTP server."""

import json
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError
from ai_admin.queue.task_queue import TaskQueue, Task, TaskType, TaskStatus


class FtpDeleteCommand(Command):
    """Delete files on FTP server via queue."""
    
    name = "ftp_delete"
    
    async def execute(
        self,
        remote_path: str,
        use_queue: bool = True,
        **kwargs
    ) -> SuccessResult:
        """Execute FTP delete operation.
        
        Args:
            remote_path: Remote file path to delete
            use_queue: Use queue for operations
            
        Returns:
            Success or error result
        """
        try:
            # Validate inputs
            if not remote_path:
                raise ValidationError("Remote file path is required")
            
            # Use queue for operations
            if use_queue:
                # Create task
                task = Task(
                    task_type=TaskType.FTP_DELETE,
                    params={
                        "remote_path": remote_path
                    },
                    category="ftp",
                    tags=["delete", "file_transfer"]
                )
                
                # Add to queue
                queue = TaskQueue()
                task_id = await queue.add_task(task)
                
                return SuccessResult(data={
                    "status": "queued",
                    "message": "FTP delete task added to queue",
                    "task_id": task_id,
                    "remote_path": remote_path,
                    "queue_position": len(await queue.get_tasks_by_status(TaskStatus.PENDING))
                })
            
            # Direct execution (for testing)
            result = await self._execute_ftp_delete(remote_path)
            return SuccessResult(data=result)
            
        except ValidationError as e:
            return ErrorResult(
                message=str(e),
                code="VALIDATION_ERROR"
            )
        except Exception as e:
            return ErrorResult(
                message=f"FTP delete command failed: {str(e)}",
                code="FTP_DELETE_ERROR",
                details={"remote_path": remote_path, "error": str(e)}
            )
    
    async def _execute_ftp_delete(self, remote_path: str) -> Dict[str, Any]:
        """Execute FTP delete directly."""
        # This will be implemented in the queue execution
        return {
            "status": "direct_execution_not_supported",
            "message": "Use queue for FTP delete operations"
        }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for FTP delete command parameters."""
        return {
            "type": "object",
            "properties": {
                "remote_path": {
                    "type": "string",
                    "description": "Remote file path to delete",
                    "examples": ["/uploads/file.txt", "/data/backup.csv"]
                },
                "use_queue": {
                    "type": "boolean",
                    "description": "Use queue for operations",
                    "default": True
                }
            },
            "required": ["remote_path"],
            "additionalProperties": False
        } 