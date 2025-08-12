"""Queue task status command for monitoring individual tasks."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import ValidationError
from ai_admin.queue.queue_manager import queue_manager


class QueueTaskStatusCommand(Command):
    """Get status of individual Docker task in queue.
    
    This command provides detailed information about a specific task
    including progress, logs, and current status.
    """
    
    name = "queue_task_status"
    
    async def execute(
        self,
        task_id: str,
        include_logs: bool = True,
        detailed: bool = True,
        **kwargs
    ) -> SuccessResult:
        """Execute queue task status command.
        
        Args:
            task_id: Task identifier
            include_logs: Include task logs in response
            detailed: Include detailed task information
            
        Returns:
            Success result with task status
        """
        try:
            # Validate inputs
            if not task_id:
                raise ValidationError("Task ID is required")
            
            # Get task from global queue
            task = await queue_manager.get_task(task_id)
            
            if not task:
                return ErrorResult(
                    message=f"Task with ID '{task_id}' not found",
                    code="TASK_NOT_FOUND",
                    details={"task_id": task_id}
                )
            
            # Convert task to dict
            task_status = task.to_dict()
            
            # Get detailed task summary if requested
            task_summary = None
            if detailed:
                task_summary = task_status  # Use task status as summary
            
            # Get task logs if requested
            logs = task.logs if include_logs else None
            
            # Add error code descriptions
            error_info = None
            if task_status.get("error_code"):
                error_info = {
                    "code": task_status["error_code"],
                    "description": self._get_error_description(task_status["error_code"]),
                    "suggestions": self._get_error_suggestions(task_status["error_code"])
                }
            
            return SuccessResult(data={
                "status": "success",
                "message": "Task status retrieved successfully",
                "task": task_status,
                "task_summary": task_summary,
                "error_info": error_info,
                "logs": logs if include_logs else None,
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
                message=f"Error getting task status: {str(e)}",
                code="TASK_STATUS_ERROR",
                details={"error_type": "unexpected", "error": str(e)}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for queue task status command parameters."""
        return {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Task identifier (UUID)",
                    "minLength": 1,
                    "examples": ["123e4567-e89b-12d3-a456-426614174000"]
                },
                "include_logs": {
                    "type": "boolean",
                    "description": "Include task logs in response",
                    "default": True
                },
                "detailed": {
                    "type": "boolean",
                    "description": "Include detailed task information",
                    "default": True
                }
            },
            "required": ["task_id"],
            "additionalProperties": False
        }
    
    def _get_error_description(self, error_code: str) -> str:
        """Get human-readable error description."""
        error_descriptions = {
            "DOCKER_IMAGE_NOT_FOUND": "Docker image not found locally",
            "DOCKER_AUTHENTICATION_FAILED": "Docker authentication failed",
            "DOCKER_PERMISSION_DENIED": "Docker permission denied",
            "DOCKER_NETWORK_ERROR": "Docker network connection error",
            "DOCKER_REGISTRY_ERROR": "Docker registry error",
            "DOCKER_BUILD_FAILED": "Docker build failed",
            "DOCKER_PUSH_FAILED": "Docker push failed",
            "DOCKER_PULL_FAILED": "Docker pull failed",
            "SYSTEM_TIMEOUT": "Task execution timed out",
            "SYSTEM_RESOURCE_LIMIT": "System resource limit exceeded",
            "SYSTEM_DISK_SPACE": "Insufficient disk space",
            "SYSTEM_MEMORY_LIMIT": "Insufficient memory",
            "VALIDATION_INVALID_PARAMS": "Invalid task parameters",
            "VALIDATION_MISSING_REQUIRED": "Missing required parameters",
            "VALIDATION_INVALID_FORMAT": "Invalid parameter format",
            "QUEUE_FULL": "Task queue is full",
            "QUEUE_TASK_NOT_FOUND": "Task not found in queue",
            "QUEUE_TASK_ALREADY_RUNNING": "Task is already running",
            "OLLAMA_MODEL_NOT_FOUND": "Ollama model not found",
            "OLLAMA_SERVICE_UNAVAILABLE": "Ollama service unavailable",
            "OLLAMA_INFERENCE_FAILED": "Ollama inference failed",
            "UNKNOWN_ERROR": "Unknown error occurred",
            "INTERNAL_ERROR": "Internal system error"
        }
        return error_descriptions.get(error_code, "Unknown error code")
    
    def _get_error_suggestions(self, error_code: str) -> List[str]:
        """Get suggestions for fixing the error."""
        error_suggestions = {
            "DOCKER_IMAGE_NOT_FOUND": [
                "Check if the image exists locally with 'docker images'",
                "Build the image first with 'docker build'",
                "Pull the image from registry with 'docker pull'"
            ],
            "DOCKER_AUTHENTICATION_FAILED": [
                "Login to Docker registry with 'docker login'",
                "Check your Docker credentials",
                "Verify your access token is valid"
            ],
            "DOCKER_PERMISSION_DENIED": [
                "Check Docker daemon permissions",
                "Ensure you have write access to the registry",
                "Verify your user has Docker group membership"
            ],
            "DOCKER_NETWORK_ERROR": [
                "Check your internet connection",
                "Verify registry URL is accessible",
                "Check firewall settings"
            ],
            "SYSTEM_TIMEOUT": [
                "Increase task timeout settings",
                "Check system resources",
                "Consider breaking task into smaller parts"
            ],
            "SYSTEM_RESOURCE_LIMIT": [
                "Free up system resources",
                "Reduce concurrent task limit",
                "Check system memory and CPU usage"
            ],
            "VALIDATION_INVALID_PARAMS": [
                "Review task parameters",
                "Check parameter format and values",
                "Refer to command documentation"
            ]
        }
        return error_suggestions.get(error_code, ["Check system logs for more details"]) 