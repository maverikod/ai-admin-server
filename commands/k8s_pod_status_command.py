from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Kubernetes pod status command for getting pod status.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.k8s_security_adapter import K8sSecurityAdapter

class K8sPodStatusCommand(BaseUnifiedCommand):
    """Command to get status of Kubernetes pods using Python kubernetes library."""

    name = "k8s_pod_status"
    
    def __init__(self):
        """Initialize K8s pod status command."""
        super().__init__()
        self.security_adapter = K8sSecurityAdapter()

    async def execute(
        self,
        action: str = "get",
        pod_name: Optional[str] = None,
        namespace: str = "default",
        watch: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute K8s pod status command with unified security.
        
        Args:
            action: Pod action (get, list, watch)
            pod_name: Name of the pod
            namespace: Kubernetes namespace
            watch: Watch pod status changes
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with pod status information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            pod_name=pod_name,
            namespace=namespace,
            watch=watch,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for K8s pod status command."""
        return "k8s:pod_status"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute K8s pod status command logic."""
        action = kwargs.get("action", "get")
        
        if action == "get":
            return await self._get_pod_status(**kwargs)
        elif action == "list":
            return await self._list_pods(**kwargs)
        elif action == "watch":
            return await self._watch_pods(**kwargs)
        else:
            raise CustomError(f"Unknown pod action: {action}")

    async def _get_pod_status(
        self,
        pod_name: Optional[str] = None,
        namespace: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """Get Kubernetes pod status."""
        try:
            if not pod_name:
                raise CustomError("Pod name is required for getting status")

            cmd = ["kubectl", "get", "pod", pod_name, "-n", namespace, "-o", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Pod status retrieval failed: {result.stderr}")

            import json
            pod_data = json.loads(result.stdout)
            
            status = {
                "name": pod_data.get("metadata", {}).get("name"),
                "namespace": pod_data.get("metadata", {}).get("namespace"),
                "phase": pod_data.get("status", {}).get("phase"),
                "ready": pod_data.get("status", {}).get("conditions", []),
                "containers": pod_data.get("status", {}).get("containerStatuses", []),
                "restart_count": sum(container.get("restartCount", 0) for container in pod_data.get("status", {}).get("containerStatuses", [])),
            }

            return {
                "message": f"Retrieved status for pod '{pod_name}' in namespace '{namespace}'",
                "action": "get",
                "pod_name": pod_name,
                "namespace": namespace,
                "status": status,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Pod status retrieval command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Pod status retrieval failed: {str(e)}")

    async def _list_pods(
        self,
        namespace: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """List Kubernetes pods with status."""
        try:
            cmd = ["kubectl", "get", "pods", "-n", namespace, "-o", "wide"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Pod listing failed: {result.stderr}")

            pods = []
            lines = result.stdout.strip().split("\n")
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 6:
                        pods.append({
                            "name": parts[0],
                            "ready": parts[1],
                            "status": parts[2],
                            "restarts": parts[3],
                            "age": parts[4],
                        })

            return {
                "message": f"Found {len(pods)} pods in namespace '{namespace}'",
                "action": "list",
                "namespace": namespace,
                "pods": pods,
                "count": len(pods),
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Pod listing command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Pod listing failed: {str(e)}")

    async def _watch_pods(
        self,
        namespace: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """Watch Kubernetes pods for status changes."""
        try:
            cmd = ["kubectl", "get", "pods", "-n", namespace, "-w", "--no-headers"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                raise CustomError(f"Pod watching failed: {result.stderr}")

            return {
                "message": f"Watching pods in namespace '{namespace}'",
                "action": "watch",
                "namespace": namespace,
                "watch_output": result.stdout,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Pod watching command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Pod watching failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for K8s pod status command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Pod action (get, list, watch)",
                    "default": "get",
                    "enum": ["get", "list", "watch"],
                },
                "pod_name": {
                    "type": "string",
                    "description": "Name of the pod",
                },
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace",
                    "default": "default",
                },
                "watch": {
                    "type": "boolean",
                    "description": "Watch pod status changes",
                    "default": False,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }