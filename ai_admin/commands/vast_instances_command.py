from ai_admin.core.custom_exceptions import CustomError
"""Vast.ai instances command for listing active GPU instances.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult, CommandResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand

from mcp_proxy_adapter.config import config

from ai_admin.security.vast_ai_security_adapter import (
    VastAiSecurityAdapter,
    VastAiOperation,
)

class VastInstancesCommand(BaseUnifiedCommand):
    """Command to list and manage Vast.ai GPU instances."""

    name = "vast_instances"

    def _get_default_operation(self) -> str:
        """Get default operation name for VastInstancesCommand."""
        return "vast:instances"

    def __init__(self) -> None:
        """Initialize Vast instances command with security adapter."""
        super().__init__()
        self.vast_security_adapter = VastAiSecurityAdapter()

    async def execute(
        self,
        action: str = "list",
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ):
        """
        List and manage Vast.ai GPU instances.

        Args:
            action: Action to perform (list, status, details)
            user_roles: List of user roles for security validation
        """
        try:
            # Security validation
            user_roles = user_roles or []

            # Validate Vast.ai operation
            operation_params = {
                "action": action,
            }

            is_valid, error_msg = self.vast_security_adapter.validate_vast_ai_operation(
                VastAiOperation.LIST_INSTANCES, user_roles, operation_params
            )

            if not is_valid:
                return ErrorResult(
                    message=f"Security validation failed: {error_msg}",
                    code="SECURITY_VALIDATION_FAILED",
                    details={"error": error_msg, "user_roles": user_roles},
                )

            if action == "list":
                return await self._list_instances()
            elif action == "status":
                return await self._get_instances_status()
            elif action == "details":
                return await self._get_instances_details()
            else:
                return ErrorResult(
                    message=f"Unknown action: {action}",
                    code="UNKNOWN_ACTION",
                    details={
                        "supported_actions": ["list", "status", "details"]
                    },
                )

        except CustomError as e:
            return ErrorResult(
                message=f"Vast instances operation failed: {str(e)}",
                code="VAST_INSTANCES_FAILED",
                details={"exception": str(e)},
            )

    async def _list_instances(self) -> CommandResult:
        """List all Vast.ai instances."""
        try:
            # Get Vast.ai API configuration
            vast_config = config.get("vast_ai", {})
            api_key = vast_config.get("api_key")
            
            if not api_key:
                return ErrorResult(
                    message="Vast.ai API key not configured",
                    code="VAST_API_KEY_MISSING",
                    details={"config_section": "vast_ai.api_key"}
                )
            
            # Make API request to list instances
            import aiohttp
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://console.vast.ai/api/v0/instances/",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        instances_data = await response.json()
                        
                        return SuccessResult(
                            data={
                                "message": "Vast.ai instances retrieved successfully",
                                "instances": instances_data.get("instances", []),
                                "total_count": len(instances_data.get("instances", [])),
                            }
                        )
                    else:
                        error_text = await response.text()
                        return ErrorResult(
                            message=f"Failed to retrieve instances: {error_text}",
                            code="VAST_API_ERROR",
                            details={"status_code": response.status, "error": error_text}
                        )
                        
        except CustomError as e:
            return ErrorResult(
                message=f"Failed to list instances: {str(e)}",
                code="INSTANCES_LIST_FAILED",
                details={"exception": str(e)}
            )

    async def _get_instances_status(self) -> CommandResult:
        """Get status of all instances."""
        try:
            # Get instances list first
            instances_result = await self._list_instances()
            
            if not instances_result.success:
                return instances_result
            
            instances = instances_result.data.get("instances", [])
            
            # Process status information
            status_summary = {
                "total": len(instances),
                "running": 0,
                "stopped": 0,
                "error": 0,
                "unknown": 0,
            }
            
            for instance in instances:
                status = instance.get("status", "unknown").lower()
                if status in ["running", "active"]:
                    status_summary["running"] += 1
                elif status in ["stopped", "inactive"]:
                    status_summary["stopped"] += 1
                elif status in ["error", "failed"]:
                    status_summary["error"] += 1
                else:
                    status_summary["unknown"] += 1
            
            return SuccessResult(
                data={
                    "message": "Instance status retrieved",
                    "status_summary": status_summary,
                    "instances": instances,
                }
            )
            
        except CustomError as e:
            return ErrorResult(
                message=f"Failed to get instances status: {str(e)}",
                code="INSTANCES_STATUS_FAILED",
                details={"exception": str(e)}
            )

    async def _get_instances_details(self) -> CommandResult:
        """Get detailed information about instances."""
        try:
            # Get instances list first
            instances_result = await self._list_instances()
            
            if not instances_result.success:
                return instances_result
            
            instances = instances_result.data.get("instances", [])
            
            # Process detailed information
            detailed_instances = []
            
            for instance in instances:
                details = {
                    "id": instance.get("id"),
                    "status": instance.get("status"),
                    "gpu_name": instance.get("gpu_name"),
                    "gpu_memory": instance.get("gpu_memory"),
                    "gpu_count": instance.get("gpu_count"),
                    "price": instance.get("price"),
                    "location": instance.get("location"),
                    "created_at": instance.get("created_at"),
                    "last_seen": instance.get("last_seen"),
                    "ssh_host": instance.get("ssh_host"),
                    "ssh_port": instance.get("ssh_port"),
                }
                detailed_instances.append(details)
            
            return SuccessResult(
                data={
                    "message": "Instance details retrieved",
                    "detailed_instances": detailed_instances,
                    "total_count": len(detailed_instances),
                }
            )
            
        except CustomError as e:
            return ErrorResult(
                message=f"Failed to get instances details: {str(e)}",
                code="INSTANCES_DETAILS_FAILED",
                details={"exception": str(e)}
            )