"""Queue status command for monitoring Docker task queue."""

from typing import Dict, Any
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.queue.queue_manager import queue_manager


class QueueStatusCommand(Command):
    """Get status and statistics of Docker task queue.
    
    This command provides information about running, pending, completed,
    and failed Docker tasks in the queue.
    """
    
    name = "queue_status"
    
    async def execute(
        self,
        include_logs: bool = False,
        detailed: bool = True,
        **kwargs
    ) -> SuccessResult:
        """Execute queue status command.
        
        Args:
            include_logs: Include task logs in response
            detailed: Include detailed statistics
            
        Returns:
            Success result with queue status
        """
        try:
            # Get queue statistics
            queue_stats = await queue_manager.get_queue_stats()
            
            # Get all tasks
            all_tasks = await queue_manager.get_all_tasks()
            
            # Get running tasks
            running_tasks = [task for task in all_tasks if task.status.value == "running"]
            
            # Build queue status
            queue_status = {
                "statistics": queue_stats,
                "recent_tasks": [task.to_dict() for task in all_tasks[:10]],
                "running_tasks": [task.to_dict() for task in running_tasks]
            }
            
            # Add all tasks with logs if requested
            if include_logs:
                queue_status["all_tasks_with_logs"] = [task.to_dict() for task in all_tasks]
            
            # Add status descriptions
            if detailed:
                queue_status["status_descriptions"] = {
                    "pending": "Tasks waiting in queue",
                    "running": "Tasks currently executing",
                    "paused": "Tasks paused by user",
                    "validating": "Tasks validating parameters",
                    "preparing": "Tasks preparing for execution",
                    "uploading": "Tasks uploading data",
                    "downloading": "Tasks downloading data",
                    "building": "Tasks building Docker images",
                    "pulling": "Tasks pulling Docker images",
                    "completed": "Tasks completed successfully",
                    "failed": "Tasks failed with errors",
                    "cancelled": "Tasks cancelled by user",
                    "timeout": "Tasks timed out"
                }
            
            return SuccessResult(data={
                "status": "success",
                "message": "Queue status retrieved successfully",
                "queue_status": queue_status,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Error getting queue status: {str(e)}",
                code="QUEUE_STATUS_ERROR",
                details={"error_type": "unexpected", "error": str(e)}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for queue status command parameters."""
        return {
            "type": "object",
            "properties": {
                "include_logs": {
                    "type": "boolean",
                    "description": "Include task logs in response",
                    "default": False
                }
            },
            "required": [],
            "additionalProperties": False
        } 