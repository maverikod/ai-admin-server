"""
Queue Cancel Task Command

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

This command allows canceling a specific task in the queue.
"""

import logging
from typing import Dict, Any, Optional, List

from base_unified_command import BaseUnifiedCommand
from security import DefaultSecurityAdapter
from mcp_proxy_adapter.core.errors import CommandError as CustomError, ValidationError
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    get_global_queue_manager,
    QueueJobError,
)

logger = logging.getLogger(__name__)


class QueueCancelTaskCommand(BaseUnifiedCommand):
    """Command to cancel a specific task in the queue."""

    def __init__(self):
        """Initialize QueueCancelTaskCommand."""
        super().__init__()
        self.security_adapter = DefaultSecurityAdapter()
        self.name = "queue_cancel_task"

    async def execute(
        self,
        task_id: str,
        force: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Cancel a specific task in the queue.

        Args:
            task_id: ID of the task to cancel
            force: Force cancel even if task is running
            user_roles: User roles for security validation
            **kwargs: Additional parameters

        Returns:
            Dict containing the result of the cancel operation
        """
        try:
            # Validate required parameters
            if not task_id:
                raise ValidationError("Task ID is required")

            # Security validation
            is_valid, error_msg = await self._validate_security(
                operation="queue_cancel_task",
                user_roles=user_roles,
                **kwargs
            )
            if not is_valid:
                raise CustomError(f"Security validation failed: {error_msg}")

            # Get queue manager
            queue_manager = await get_global_queue_manager()
            if queue_manager is None:
                raise CustomError("Queue manager is not available")

            # Get job status
            try:
                job_status = await queue_manager.get_job_status(task_id)
            except QueueJobError as e:
                if "not found" in str(e).lower():
                    raise CustomError(f"Task {task_id} not found")
                raise CustomError(f"Failed to get task status: {str(e)}")

            # Check if task can be cancelled
            if job_status.status in ["completed", "failed", "stopped", "deleted"]:
                raise CustomError(f"Task {task_id} is already {job_status.status} and cannot be cancelled")

            if job_status.status == "running" and not force:
                raise CustomError(f"Task {task_id} is currently running. Use force=True to cancel it")

            # Stop the job
            try:
                result = await queue_manager.stop_job(task_id)
                if result.status not in ["stopped", "deleted"]:
                    raise CustomError(f"Failed to cancel task {task_id}")
            except QueueJobError as e:
                raise CustomError(f"Failed to cancel task: {str(e)}")

            # Get updated job status
            try:
                updated_status = await queue_manager.get_job_status(task_id)
            except QueueJobError:
                updated_status = None
            
            return {
                "message": f"Task {task_id} cancelled successfully",
                "task_id": task_id,
                "previous_status": job_status.status,
                "current_status": updated_status.status if updated_status else "stopped",
                "force_cancelled": force and job_status.status == "running",
            }

        except ValidationError as e:
            logger.error(f"Validation error in queue_cancel_task: {e}")
            raise CustomError(f"Validation error: {str(e)}")
        except CustomError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in queue_cancel_task: {e}")
            raise CustomError(f"Failed to cancel task: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Get the command schema."""
        return {
            "name": self.name,
            "description": "Cancel a specific task in the queue",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "ID of the task to cancel",
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Force cancel even if task is running",
                        "default": False,
                    },
                },
                "required": ["task_id"],
            },
        }
