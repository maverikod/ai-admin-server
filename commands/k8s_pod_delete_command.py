from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Kubernetes pod delete command for deleting pods.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.k8s_security_adapter import K8sSecurityAdapter

class K8sPodDeleteCommand(BaseUnifiedCommand):
    """Command to delete Kubernetes pods using Python kubernetes library."""

    name = "k8s_pod_delete"
    
    def __init__(self):
        """Initialize K8s pod delete command."""
        super().__init__()
        self.security_adapter = K8sSecurityAdapter()

    async def execute(
        self,
        action: str = "delete",
        pod_name: Optional[str] = None,
        namespace: str = "default",
        force: bool = False,
        grace_period: Optional[int] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute K8s pod delete command with unified security.
        
        Args:
            action: Pod action (delete, list)
            pod_name: Name of the pod to delete
            namespace: Kubernetes namespace
            force: Force deletion
            grace_period: Grace period for deletion
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with pod deletion information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            pod_name=pod_name,
            namespace=namespace,
            force=force,
            grace_period=grace_period,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for K8s pod delete command."""
        return "k8s:pod_delete"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute K8s pod delete command logic."""
        action = kwargs.get("action", "delete")
        
        if action == "delete":
            return await self._delete_pod(**kwargs)
        elif action == "list":
            return await self._list_pods(**kwargs)
        else:
            raise CustomError(f"Unknown pod action: {action}")

    async def _delete_pod(
        self,
        pod_name: Optional[str] = None,
        namespace: str = "default",
        force: bool = False,
        grace_period: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Delete Kubernetes pod."""
        try:
            if not pod_name:
                raise CustomError("Pod name is required for deletion")

            cmd = ["kubectl", "delete", "pod", pod_name, "-n", namespace]
            
            if force:
                cmd.append("--force")
            if grace_period:
                cmd.extend(["--grace-period", str(grace_period)])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Pod deletion failed: {result.stderr}")

            return {
                "message": f"Successfully deleted pod '{pod_name}' from namespace '{namespace}'",
                "action": "delete",
                "pod_name": pod_name,
                "namespace": namespace,
                "force": force,
                "grace_period": grace_period,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Pod deletion command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Pod deletion failed: {str(e)}")

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
        """Get JSON schema for K8s pod delete command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Pod action (delete, list)",
                    "default": "delete",
                    "enum": ["delete", "list"],
                },
                "pod_name": {
                    "type": "string",
                    "description": "Name of the pod to delete",
                },
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace",
                    "default": "default",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force deletion",
                    "default": False,
                },
                "grace_period": {
                    "type": "integer",
                    "description": "Grace period for deletion",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }