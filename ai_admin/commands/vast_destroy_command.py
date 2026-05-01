from ai_admin.core.custom_exceptions import CustomError

"""Vast.ai destroy instance command for stopping/deleting GPU instances.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
from typing import Optional, List, Dict, Any
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand

from mcp_proxy_adapter.config import config

from ai_admin.security.vast_ai_security_adapter import (
    VastAiSecurityAdapter,
    VastAiOperation,
)
from ai_admin.task_queue.task_queue import Task, TaskType, TaskStatus
from ai_admin.task_queue.queue_manager import QueueManager


class VastDestroyCommand(BaseUnifiedCommand):
    """Destroy (stop/delete) a GPU instance on Vast.ai."""

    name = "vast_destroy"

    def _get_default_operation(self) -> str:
        """Get default operation name for VastDestroyCommand."""
        return "vastdestroy:execute"

    def __init__(self):
        """Initialize Vast.ai destroy command with security adapter."""
        super().__init__()
        self.security_adapter = VastAiSecurityAdapter()

    async def execute(
        self,
        instance_id: int,
        use_queue: bool = True,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Destroy a GPU instance.

        Args:
            instance_id: ID of the instance to destroy
            use_queue: Whether to use queue system for instance destruction
            user_roles: List of user roles for security validation

        Returns:
            SuccessResult with destruction details
        """
        try:
            # Security validation
            user_roles = user_roles or []
            operation_params = {
                "instance_id": instance_id,
            }

            is_valid, error_msg = self.security_adapter.validate_vast_ai_operation(
                VastAiOperation.DESTROY, user_roles, operation_params
            )

            if not is_valid:
                return ErrorResult(
                    message="Security validation failed: {error_msg}",
                    code="SECURITY_ERROR",
                )

            # Get Vast API configuration
            api_key = config.get("vast.api_key")
            api_url = config.get(  # noqa: F841
                "vast.api_url", "https://console.vast.ai/api/v0"
            )

            if not api_key or api_key == "your-vast-api-key-here":
                return ErrorResult(
                    message="Vast API key not configured",
                    code="MISSING_API_KEY",
                    details={"config_path": "vast.api_key"},
                )

            # Use queue for long-running operations
            if use_queue:
                queue_manager = QueueManager()
                # Create task with security context
                task = Task(
                    task_type=TaskType.VAST_DESTROY,
                    params={
                        "instance_id": instance_id,
                        "user_roles": user_roles,
                        "security_validated": True,
                    },
                    category="vast_ai",
                    tags=["destroy", "instance", "gpu", "ssl_mtls"],
                )

                # Add to queue
                task_id = await queue_manager.add_task(task)

                # Audit successful operation
                self.security_adapter.audit_vast_ai_operation(
                    VastAiOperation.DESTROY,
                    user_roles,
                    operation_params,
                    "queued",
                )

                return SuccessResult(
                    data={
                        "status": "queued",
                        "message": (
                            "Vast.ai instance destruction task added to queue "
                            "with SSL/mTLS security"
                        ),
                        "task_id": task_id,
                        "instance_id": instance_id,
                        "security_validated": True,
                        "queue_position": len(
                            await queue_manager.get_tasks_by_status(TaskStatus.PENDING)
                        ),
                    }
                )

            # Execute curl request to destroy instance
            curl_cmd = [
                "curl",
                "-s",
                "-X",
                "DELETE",
                "-H",
                "Authorization: Bearer {api_key}",
                "{api_url}/instances/{instance_id}/",
            ]

            process = await asyncio.create_subprocess_exec(
                *curl_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8").strip()
                return ErrorResult(
                    message="Failed to destroy Vast instance: {error_msg}",
                    code="API_REQUEST_FAILED",
                    details={
                        "stderr": error_msg,
                        "exit_code": process.returncode,
                        "instance_id": instance_id,
                    },
                )

            # Parse response
            response_text = stdout.decode("utf-8").strip()

            # Try to parse as JSON, but handle simple text responses too
            try:
                response_data = json.loads(response_text) if response_text else {}
            except json.JSONDecodeError:
                # Sometimes API returns simple text responses
                response_data = {"message": response_text}

            # Check for API errors
            if "error" in response_data:
                return ErrorResult(
                    message="Vast API error: {response_data['error']}",
                    code="API_ERROR",
                    details={"api_response": response_data},
                )

            # Audit successful direct execution
            self.security_adapter.audit_vast_ai_operation(
                VastAiOperation.DESTROY,
                user_roles,
                operation_params,
                "executed",
            )

            # Successful destruction
            return SuccessResult(
                data={
                    "status": "success",
                    "message": "Successfully destroyed instance {instance_id}",
                    "instance_id": instance_id,
                    "api_response": response_data,
                    "security_validated": True,
                    "info": [
                        "Instance has been marked for destruction",
                        "It may take a few moments to fully terminate",
                        "Billing for this instance will stop shortly",
                        "Use 'vast_instances' to verify termination status",
                    ],
                }
            )

        except CustomError as e:
            # Audit failed operation
            self.security_adapter.audit_vast_ai_operation(
                VastAiOperation.DESTROY,
                user_roles or [],
                operation_params,
                "failed",
            )

            return ErrorResult(
                message="Unexpected error destroying Vast instance: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error_type": type(e).__name__},
            )

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get the JSON schema for this command."""
        return {
            "type": "object",
            "properties": {
                "instance_id": {
                    "type": "integer",
                    "description": (
                        "ID of the instance to destroy "
                        "(get from vast_instances command)"
                    ),
                },
                "use_queue": {
                    "type": "boolean",
                    "description": (
                        "Whether to use queue system for instance destruction"
                    ),
                    "default": True,
                },
                "user_roles": {
                    "type": "array",
                    "description": "List of user roles for security validation",
                    "items": {"type": "string"},
                    "examples": [["vast:destroy", "vast:admin"]],
                },
            },
            "required": ["instance_id"],
            "additionalProperties": False,
        }
