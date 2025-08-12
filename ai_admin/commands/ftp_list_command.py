"""FTP list command for listing files on FTP server."""

import json
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError
from ai_admin.queue.task_queue import TaskQueue, Task, TaskType, TaskStatus


class FtpListCommand(Command):
    """List files on FTP server via queue."""
    
    name = "ftp_list"
    
    async def execute(
        self,
        remote_path: str = "/",
        use_queue: bool = True,
        **kwargs
    ) -> SuccessResult:
        """Execute FTP list operation.
        
        Args:
            remote_path: Remote directory path to list (default: "/")
            use_queue: Use queue for operations
            
        Returns:
            Success or error result
        """
        try:
            # Validate inputs
            if not remote_path:
                raise ValidationError("Remote path is required")
            
            # Use queue for operations
            if use_queue:
                # Create task
                task = Task(
                    task_type=TaskType.FTP_LIST,
                    params={
                        "remote_path": remote_path
                    },
                    category="ftp",
                    tags=["list", "file_transfer"]
                )
                
                # Add to queue
                queue = TaskQueue()
                task_id = await queue.add_task(task)
                
                return SuccessResult(data={
                    "status": "queued",
                    "message": "FTP list task added to queue",
                    "task_id": task_id,
                    "remote_path": remote_path,
                    "queue_position": len(await queue.get_tasks_by_status(TaskStatus.PENDING))
                })
            
            # Direct execution (for small directories or testing)
            result = await self._execute_ftp_list(remote_path)
            return SuccessResult(data=result)
            
        except ValidationError as e:
            return ErrorResult(
                message=str(e),
                code="VALIDATION_ERROR"
            )
        except Exception as e:
            return ErrorResult(
                message=f"FTP list command failed: {str(e)}",
                code="FTP_LIST_ERROR",
                details={"remote_path": remote_path, "error": str(e)}
            )
    
    async def _execute_ftp_list(self, remote_path: str) -> Dict[str, Any]:
        """Execute FTP list directly."""
        # This will be implemented in the queue execution
        return {
            "status": "direct_execution_not_supported",
            "message": "Use queue for FTP list operations"
        }
    
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
                    "examples": ["/", "/uploads", "/data/backup"]
                },
                "use_queue": {
                    "type": "boolean",
                    "description": "Use queue for operations",
                    "default": True
                }
            },
            "additionalProperties": False
        } 