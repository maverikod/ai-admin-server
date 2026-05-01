from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Vast.ai search command for finding available GPU instances.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
from typing import Optional, List, Dict, Any
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand

from mcp_proxy_adapter.config import config

from ai_admin.security.vast_ai_security_adapter import (
    VastAiSecurityAdapter,
    VastAiOperation,
)

class VastSearchCommand(BaseUnifiedCommand):
    """Search for available GPU instances on Vast.ai."""

    name = "vast_search"

    def _get_default_operation(self) -> str:
        """Get default operation name for VastSearchCommand."""
        return "vastsearch:execute"

    def __init__(self):
        """Initialize Vast.ai search command with security adapter."""
        super().__init__()
        self.security_adapter = VastAiSecurityAdapter()

    async def execute(
        self,
        gpu_name: Optional[str] = None,
        min_gpu_count: int = 1,
        max_gpu_count: Optional[int] = None,
        min_gpu_ram: Optional[float] = None,
        max_price_per_hour: Optional[float] = None,
        disk_space: Optional[float] = None,
        order: str = "score-",
        limit: int = 20,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Search for available GPU instances.

        Args:
            gpu_name: GPU model name (e.g., 'RTX_4090', 'A100')
            min_gpu_count: Minimum number of GPUs
            max_gpu_count: Maximum number of GPUs
            min_gpu_ram: Minimum GPU RAM in GB
            max_price_per_hour: Maximum price per hour in USD
            disk_space: Required disk space in GB
            order: Sort order (score-, dph+, dph-, etc.)
            limit: Maximum number of results
            user_roles: List of user roles for security validation

        Returns:
            SuccessResult with available instances
        """
        try:
            # Security validation
            user_roles = user_roles or []
            operation_params = {
                "gpu_name": gpu_name,
                "min_gpu_count": min_gpu_count,
                "max_gpu_count": max_gpu_count,
                "min_gpu_ram": min_gpu_ram,
                "max_price_per_hour": max_price_per_hour,
                "disk_space": disk_space,
                "order": order,
                "limit": limit,
            }

            is_valid, error_msg = self.security_adapter.validate_vast_ai_operation(
                VastAiOperation.SEARCH, user_roles, operation_params
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

            # Build search parameters
            search_params = {
                "verified": "true",
                "rentable": "true",
                "order": order,
                "limit": str(limit),
            }

            if gpu_name:
                search_params["gpu_name"] = gpu_name

            if min_gpu_count:
                search_params["num_gpus"] = ">={min_gpu_count}"

            if max_gpu_count:
                if min_gpu_count == max_gpu_count:
                    search_params["num_gpus"] = str(min_gpu_count)
                else:
                    search_params["num_gpus"] = ">={min_gpu_count}&num_gpus=<={max_gpu_count}"

            if min_gpu_ram:
                search_params["gpu_ram"] = ">={min_gpu_ram}"

            if max_price_per_hour:
                search_params["dph"] = "<={max_price_per_hour}"

            if disk_space:
                search_params["disk_space"] = ">={disk_space}"

            # Build curl command
            params_str = "&".join(["{k}={v}" for k, v in search_params.items()])
            search_url = "{api_url}/bundles/?{params_str}"

            # Execute curl request
            curl_cmd = [
                "curl",
                "-s",
                "-H",
                "Authorization: Bearer {api_key}",
                search_url,
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
                    message="Failed to search Vast instances: {error_msg}",
                    code="API_REQUEST_FAILED",
                    details={
                        "stderr": error_msg,
                        "exit_code": process.returncode,
                        "url": search_url,
                    },
                )

            # Parse response
            try:
                response_data = json.loads(stdout.decode("utf-8"))
            except json.JSONDecodeError as e:
                return ErrorResult(
                    message="Failed to parse API response: {str(e)}",
                    code="INVALID_JSON_RESPONSE",
                    details={"raw_response": stdout.decode("utf-8")[:500]},
                )

            # Process and format results
            if not isinstance(response_data, dict):
                return ErrorResult(
                    message="Unexpected API response format",
                    code="UNEXPECTED_RESPONSE",
                    details={"response": response_data},
                )

            # Handle both 'bundles' and 'offers' response formats
            bundles = response_data.get("bundles", [])
            if not bundles:
                bundles = response_data.get("offers", [])

            if not bundles:
                return ErrorResult(
                    message="No instances found in API response",
                    code="NO_INSTANCES_FOUND",
                    details={"response": response_data},
                )

            # Format instances for better readability
            formatted_instances = []
            for bundle in bundles:
                # Handle both bundle and offer formats
                instance = {
                    "id": bundle.get("id") or bundle.get("ask_contract_id"),
                    "machine_id": bundle.get("machine_id"),
                    "gpu_name": bundle.get("gpu_name"),
                    "gpu_count": bundle.get("num_gpus", 0),
                    "gpu_ram": bundle.get("gpu_ram", 0),
                    "cpu_cores": bundle.get("cpu_cores", 0),
                    "cpu_ram": bundle.get("cpu_ram", 0),
                    "disk_space": bundle.get("disk_space", 0),
                    "price_per_hour": bundle.get("dph_total", 0),
                    "price_per_gpu_hour": bundle.get("dph_base", 0),
                    "location": bundle.get("geolocation"),
                    "inet_up": bundle.get("inet_up", 0),
                    "inet_down": bundle.get("inet_down", 0),
                    "reliability": bundle.get("reliability2", 0) or bundle.get("reliability", 0),
                    "score": bundle.get("score", 0),
                    "verified": bundle.get("verified", False),
                    "cuda_max_good": bundle.get("cuda_max_good"),
                    "driver_version": bundle.get("driver_version"),
                    "direct_port_count": bundle.get("direct_port_count", 0),
                    "rentable": bundle.get("rentable", False),
                    "rented": bundle.get("rented", False),
                }
                formatted_instances.append(instance)

            # Calculate statistics
            stats = {
                "total_found": len(formatted_instances),
                "price_range": {},
                "gpu_types": {},
                "locations": {},
            }

            if formatted_instances:
                prices = [inst["price_per_hour"] for inst in formatted_instances if inst["price_per_hour"]]
                if prices:
                    stats["price_range"] = {
                        "min": min(prices),
                        "max": max(prices),
                        "avg": sum(prices) / len(prices),
                    }

                # Count GPU types
                for inst in formatted_instances:
                    gpu = inst["gpu_name"]
                    if gpu:
                        stats["gpu_types"][gpu] = stats["gpu_types"].get(gpu, 0) + 1

                # Count locations
                for inst in formatted_instances:
                    loc = inst["location"]
                    if loc:
                        stats["locations"][loc] = stats["locations"].get(loc, 0) + 1

            # Audit successful operation
            self.security_adapter.audit_vast_ai_operation(
                VastAiOperation.SEARCH,
                user_roles,
                operation_params,
                "executed",
            )

            return SuccessResult(
                data={
                    "status": "success",
                    "message": "Found {len(formatted_instances)} available instances",
                    "instances": formatted_instances,
                    "statistics": stats,
                    "search_parameters": search_params,
                    "security_validated": True,
                    "api_info": {
                        "url": search_url,
                        "limit": limit,
                        "order": order,
                    },
                }
            )

        except CustomError as e:
            # Audit failed operation
            self.security_adapter.audit_vast_ai_operation(
                VastAiOperation.SEARCH,
                user_roles or [],
                operation_params,
                "failed",
            )

            return ErrorResult(
                message="Unexpected error searching Vast instances: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error_type": type(e).__name__},
            )

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get the JSON schema for this command."""
        return {
            "type": "object",
            "properties": {
                "gpu_name": {
                    "type": "string",
                    "description": "GPU model name (e.g., 'RTX_4090', 'A100', 'RTX_3090')",
                },
                "min_gpu_count": {
                    "type": "integer",
                    "description": "Minimum number of GPUs",
                    "default": 1,
                    "minimum": 1,
                },
                "max_gpu_count": {
                    "type": "integer",
                    "description": "Maximum number of GPUs",
                    "minimum": 1,
                },
                "min_gpu_ram": {
                    "type": "number",
                    "description": "Minimum GPU RAM in GB",
                    "minimum": 0,
                },
                "max_price_per_hour": {
                    "type": "number",
                    "description": "Maximum price per hour in USD",
                    "minimum": 0,
                },
                "disk_space": {
                    "type": "number",
                    "description": "Required disk space in GB",
                    "minimum": 0,
                },
                "order": {
                    "type": "string",
                    "description": "Sort order",
                    "enum": [
                        "score-",
                        "dph+",
                        "dph-",
                        "gpu_ram+",
                        "gpu_ram-",
                        "num_gpus+",
                        "num_gpus-",
                    ],
                    "default": "score-",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                },
                "user_roles": {
                    "type": "array",
                    "description": "List of user roles for security validation",
                    "items": {"type": "string"},
                    "examples": [["vast:search", "vast:admin"]],
                },
            },
            "required": [],
            "additionalProperties": False,
        }
