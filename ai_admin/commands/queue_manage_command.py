"""Queue management command for controlling Docker tasks."""

from typing import Dict, Any, List
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import ValidationError
from ai_admin.queue.queue_manager import queue_manager


class QueueManageCommand(Command):
    """Manage Docker tasks in queue (pause, resume, retry, cancel).
    
    This command provides control over individual tasks in the queue,
    allowing users to pause, resume, retry, or cancel tasks.
    """
    
    name = "queue_manage"
    
    async def execute(
        self,
        action: str,
        task_id: str,
        **kwargs
    ) -> SuccessResult:
        """Execute queue management command.
        
        Args:
            action: Action to perform (pause, resume, retry, cancel)
            task_id: Task identifier
            
        Returns:
            Success result with action result
        """
        try:
            # Validate inputs
            if not action:
                raise ValidationError("Action is required")
            
            if not task_id:
                raise ValidationError("Task ID is required")
            
            # Validate action
            valid_actions = ["pause", "resume", "retry", "cancel"]
            if action not in valid_actions:
                raise ValidationError(f"Invalid action. Must be one of: {', '.join(valid_actions)}")
            
            # Get task first to check if it exists
            task = await queue_manager.get_task_status(task_id)
            if not task:
                return ErrorResult(
                    message=f"Task with ID '{task_id}' not found",
                    code="TASK_NOT_FOUND",
                    details={"task_id": task_id}
                )
            
            # Perform action
            success = False
            message = ""
            
            if action == "pause":
                success = await queue_manager.task_queue.pause_task(task_id)
                message = "Task paused successfully" if success else "Failed to pause task"
                
            elif action == "resume":
                success = await queue_manager.task_queue.resume_task(task_id)
                message = "Task resumed successfully" if success else "Failed to resume task"
                
            elif action == "retry":
                success = await queue_manager.task_queue.retry_task(task_id)
                message = "Task retry initiated successfully" if success else "Failed to retry task"
                
            elif action == "cancel":
                success = await queue_manager.task_queue.cancel_task(task_id)
                message = "Task cancelled successfully" if success else "Failed to cancel task"
            
            if not success:
                return ErrorResult(
                    message=message,
                    code="ACTION_FAILED",
                    details={
                        "action": action,
                        "task_id": task_id,
                        "current_status": task.get("status"),
                        "reason": self._get_action_failure_reason(action, task.get("status"))
                    }
                )
            
            # Get updated task status
            updated_task = await queue_manager.get_task_status(task_id)
            
            return SuccessResult(data={
                "status": "success",
                "message": message,
                "action": action,
                "task_id": task_id,
                "task_status": updated_task,
                "timestamp": datetime.now().isoformat()
            })
            
        except ValidationError as e:
            return ErrorResult(
                message=str(e),
                code="VALIDATION_ERROR",
                details={"error_type": "validation"}
            )
        except Exception as e:
            return ErrorResult(
                message=f"Error managing task: {str(e)}",
                code="MANAGEMENT_ERROR",
                details={"error_type": "unexpected", "error": str(e)}
            )
    
    def _get_action_failure_reason(self, action: str, current_status: str) -> str:
        """Get reason why action failed based on current task status."""
        failure_reasons = {
            "pause": {
                "pending": "Cannot pause task that is not running",
                "completed": "Cannot pause completed task",
                "failed": "Cannot pause failed task",
                "cancelled": "Cannot pause cancelled task",
                "timeout": "Cannot pause timed out task"
            },
            "resume": {
                "pending": "Cannot resume task that is not paused",
                "running": "Cannot resume task that is already running",
                "completed": "Cannot resume completed task",
                "failed": "Cannot resume failed task",
                "cancelled": "Cannot resume cancelled task",
                "timeout": "Cannot resume timed out task"
            },
            "retry": {
                "pending": "Cannot retry task that is not failed or timed out",
                "running": "Cannot retry task that is currently running",
                "completed": "Cannot retry completed task",
                "cancelled": "Cannot retry cancelled task"
            },
            "cancel": {
                "completed": "Cannot cancel completed task",
                "failed": "Cannot cancel failed task",
                "cancelled": "Task is already cancelled",
                "timeout": "Cannot cancel timed out task"
            }
        }
        
        return failure_reasons.get(action, {}).get(current_status, "Action not allowed for current task status")
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for queue management command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform on the task",
                    "enum": ["pause", "resume", "retry", "cancel"],
                    "examples": ["pause", "resume", "retry", "cancel"]
                },
                "task_id": {
                    "type": "string",
                    "description": "Task identifier (UUID)",
                    "minLength": 1,
                    "examples": ["123e4567-e89b-12d3-a456-426614174000"]
                }
            },
            "required": ["action", "task_id"],
            "additionalProperties": False
        } 