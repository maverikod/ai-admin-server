from ai_admin.core.custom_exceptions import CustomError

"""Vast.ai create instance command for renting GPU instances.

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


class VastCreateCommand(BaseUnifiedCommand):
    """Create (rent) a GPU instance on Vast.ai."""

    name = "vast_create"

    def _get_default_operation(self) -> str:
        """Get default operation name for VastCreateCommand."""
        return "vastcreate:execute"

    def __init__(self):
        """Initialize Vast.ai create command with security adapter."""
        super().__init__()
        self.security_adapter = VastAiSecurityAdapter()

    async def execute(
        self,
        bundle_id: int,
        image: str = "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel",
        disk: float = 10,
        label: Optional[str] = None,
        onstart: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        use_queue: bool = True,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Create a new GPU instance.

        Args:
            bundle_id: ID of the bundle to rent (from vast_search)
            image: Docker image to use
            disk: Disk space in GB
            label: Human-readable label for the instance
            onstart: Script to run on instance start
            env_vars: Environment variables to set
            use_queue: Whether to use queue system for instance creation
            user_roles: List of user roles for security validation

        Returns:
            SuccessResult with instance creation details
        """
        try:
            # Security validation
            user_roles = user_roles or []
            operation_params = {
                "bundle_id": bundle_id,
                "image": image,
                "disk": disk,
                "label": label,
                "onstart": onstart,
                "env_vars": env_vars,
            }

            is_valid, error_msg = self.security_adapter.validate_vast_ai_operation(
                VastAiOperation.CREATE, user_roles, operation_params
            )

            if not is_valid:
                return ErrorResult(
                    message="Security validation failed: {error_msg}",
                    code="SECURITY_ERROR",
                )

            # Get Vast API configuration
            api_key = config.get("vast.api_key")
            api_url = config.get("vast.api_url", "https://console.vast.ai/api/v0")

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
                    task_type=TaskType.VAST_CREATE,
                    params={
                        "bundle_id": bundle_id,
                        "image": image,
                        "disk": disk,
                        "label": label,
                        "onstart": onstart,
                        "env_vars": env_vars,
                        "user_roles": user_roles,
                        "security_validated": True,
                    },
                    category="vast_ai",
                    tags=["create", "instance", "gpu", "ssl_mtls"],
                )

                # Add to queue
                task_id = await queue_manager.add_task(task)

                # Audit successful operation
                self.security_adapter.audit_vast_ai_operation(
                    VastAiOperation.CREATE,
                    user_roles,
                    operation_params,
                    "queued",
                )

                return SuccessResult(
                    data={
                        "status": "queued",
                        "message": (
                            "Vast.ai instance creation task added to queue "
                            "with SSL/mTLS security"
                        ),
                        "task_id": task_id,
                        "bundle_id": bundle_id,
                        "image": image,
                        "disk": disk,
                        "label": label,
                        "security_validated": True,
                        "queue_position": len(
                            await queue_manager.get_tasks_by_status(TaskStatus.PENDING)
                        ),
                    }
                )

            # Build request payload
            payload = {
                "client_id": "me",
                "image": image,
                "disk": disk,
                "label": label or "Instance-{bundle_id}",
                "onstart": onstart or "",
                "env": env_vars or {},
            }

            # Execute curl request to create instance
            curl_cmd = [
                "curl",
                "-s",
                "-X",
                "PUT",
                "-H",
                "Authorization: Bearer {api_key}",
                "-H",
                "Content-Type: application/json",
                "-d",
                payload,
                f"{api_url}/asks/{bundle_id}/",
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
                    message="Failed to create Vast instance: {error_msg}",
                    code="API_REQUEST_FAILED",
                    details={
                        "stderr": error_msg,
                        "exit_code": process.returncode,
                        "bundle_id": bundle_id,
                        "payload": payload,
                    },
                )

            # Parse response
            try:
                response_data = json.loads(stdout.decode("utf-8"))
            except json.JSONDecodeError:
                return ErrorResult(
                    message="Failed to parse API response: {str(e)}",
                    code="INVALID_JSON_RESPONSE",
                    details={"raw_response": stdout.decode("utf-8")[:500]},
                )

            # Check for API errors
            if "error" in response_data:
                return ErrorResult(
                    message="Vast API error: {response_data['error']}",
                    code="API_ERROR",
                    details={"api_response": response_data},
                )

            # Extract instance information
            if "new_contract" in response_data:
                contract_id = response_data["new_contract"]

                # Get detailed instance information
                instance_info = {
                    "status": "success",
                    "contract_id": contract_id,
                    "bundle_id": bundle_id,
                    "instance_label": payload["label"],
                    "image": image,
                    "disk_space": disk,
                    "creation_time": response_data.get("timestamp"),
                    "machine_id": response_data.get("machine_id"),
                    "actual_status": response_data.get("actual_status", "creating"),
                }

                # Add environment variables if any
                if env_vars:
                    instance_info["environment_variables"] = env_vars

                # Add onstart script if any
                if onstart:
                    instance_info["onstart_script"] = onstart

                # Audit successful direct execution
                self.security_adapter.audit_vast_ai_operation(
                    VastAiOperation.CREATE,
                    user_roles,
                    operation_params,
                    "executed",
                )

                return SuccessResult(
                    data={
                        "status": "success",
                        "message": (
                            "Successfully created instance with contract ID: "
                            "{contract_id}"
                        ),
                        "instance": instance_info,
                        "raw_response": response_data,
                        "security_validated": True,
                        "next_steps": [
                            "Wait for instance to be ready "
                            "(status: loading -> running)",
                            "Use 'vast_instances' to check status",
                            "Use 'vast_ssh' to get SSH connection info",
                            "Access your instance via SSH or Jupyter",
                        ],
                    }
                )
            else:
                return ErrorResult(
                    message="Unexpected response format - no contract ID returned",
                    code="UNEXPECTED_RESPONSE",
                    details={"response": response_data},
                )

        except CustomError as e:
            # Audit failed operation
            self.security_adapter.audit_vast_ai_operation(
                VastAiOperation.CREATE,
                user_roles or [],
                operation_params,
                "failed",
            )

            return ErrorResult(
                message="Unexpected error creating Vast instance: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error_type": type(e).__name__},
            )

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get the JSON schema for this command."""
        return {
            "type": "object",
            "properties": {
                "bundle_id": {
                    "type": "integer",
                    "description": (
                        "ID of the bundle to rent (get from vast_search command)"
                    ),
                },
                "image": {
                    "type": "string",
                    "description": "Docker image to use",
                    "default": "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel",
                    "examples": [
                        "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel",
                        "tensorflow/tensorflow:2.13.0-gpu",
                        "nvidia/cuda:12.1-devel-ubuntu20.04",
                        "jupyter/tensorflow-notebook",
                    ],
                },
                "disk": {
                    "type": "number",
                    "description": "Disk space in GB",
                    "default": 10,
                    "minimum": 1,
                },
                "label": {
                    "type": "string",
                    "description": "Human-readable label for the instance",
                },
                "onstart": {
                    "type": "string",
                    "description": "Script to run on instance start (bash script)",
                },
                "env_vars": {
                    "type": "object",
                    "description": "Environment variables to set",
                    "additionalProperties": {"type": "string"},
                    "examples": [
                        {
                            "WANDB_API_KEY": "your-wandb-key",
                            "HF_TOKEN": "your-hf-token",
                        }
                    ],
                },
                "use_queue": {
                    "type": "boolean",
                    "description": "Whether to use queue system for instance creation",
                    "default": True,
                },
                "user_roles": {
                    "type": "array",
                    "description": "List of user roles for security validation",
                    "items": {"type": "string"},
                    "examples": [["vast:create", "vast:admin"]],
                },
            },
            "required": ["bundle_id"],
            "additionalProperties": False,
        }
