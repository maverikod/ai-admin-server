from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Kubernetes logs command for getting pod logs.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.k8s_security_adapter import K8sSecurityAdapter

class K8sLogsCommand(BaseUnifiedCommand):
    """Command to get Kubernetes pod logs using Python kubernetes library."""

    name = "k8s_logs"
    
    def __init__(self):
        """Initialize K8s logs command."""
        super().__init__()
        self.security_adapter = K8sSecurityAdapter()

    async def execute(
        self,
        action: str = "get",
        pod_name: Optional[str] = None,
        namespace: str = "default",
        container: Optional[str] = None,
        lines: Optional[int] = None,
        follow: bool = False,
        previous: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute K8s logs command with unified security.
        
        Args:
            action: Logs action (get, list)
            pod_name: Name of the pod
            namespace: Kubernetes namespace
            container: Container name
            lines: Number of lines to show
            follow: Follow log output
            previous: Show previous container logs
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with logs information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            pod_name=pod_name,
            namespace=namespace,
            container=container,
            lines=lines,
            follow=follow,
            previous=previous,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for K8s logs command."""
        return "k8s:logs"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute K8s logs command logic."""
        action = kwargs.get("action", "get")
        
        if action == "get":
            return await self._get_logs(**kwargs)
        elif action == "list":
            return await self._list_pods(**kwargs)
        else:
            raise CustomError(f"Unknown logs action: {action}")

    async def _get_logs(
        self,
        pod_name: Optional[str] = None,
        namespace: str = "default",
        container: Optional[str] = None,
        lines: Optional[int] = None,
        follow: bool = False,
        previous: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get Kubernetes pod logs."""
        try:
            if not pod_name:
                raise CustomError("Pod name is required for getting logs")

            cmd = ["kubectl", "logs", pod_name, "-n", namespace]
            
            if container:
                cmd.extend(["-c", container])
            if lines:
                cmd.extend(["--tail", str(lines)])
            if follow:
                cmd.append("-f")
            if previous:
                cmd.append("--previous")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Logs retrieval failed: {result.stderr}")

            return {
                "message": f"Retrieved logs for pod '{pod_name}' in namespace '{namespace}'",
                "action": "get",
                "pod_name": pod_name,
                "namespace": namespace,
                "container": container,
                "lines": lines,
                "follow": follow,
                "previous": previous,
                "logs": result.stdout,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Logs retrieval command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Logs retrieval failed: {str(e)}")

    async def _list_pods(
        self,
        namespace: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """List Kubernetes pods."""
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

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for K8s logs command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Logs action (get, list)",
                    "default": "get",
                    "enum": ["get", "list"],
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
                "container": {
                    "type": "string",
                    "description": "Container name",
                },
                "lines": {
                    "type": "integer",
                    "description": "Number of lines to show",
                },
                "follow": {
                    "type": "boolean",
                    "description": "Follow log output",
                    "default": False,
                },
                "previous": {
                    "type": "boolean",
                    "description": "Show previous container logs",
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