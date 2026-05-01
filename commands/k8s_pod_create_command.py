from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Kubernetes pod create command for creating pods.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.k8s_security_adapter import K8sSecurityAdapter

class K8sPodCreateCommand(BaseUnifiedCommand):
    """Command to create Kubernetes pods for projects using kubernetes Python library."""

    name = "k8s_pod_create"
    
    def __init__(self):
        """Initialize K8s pod create command."""
        super().__init__()
        self.security_adapter = K8sSecurityAdapter()

    async def execute(
        self,
        action: str = "create",
        name: str = "my-pod",
        namespace: str = "default",
        image: str = "nginx:latest",
        command: Optional[List[str]] = None,
        args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute K8s pod create command with unified security.
        
        Args:
            action: Pod action (create, get, delete, list)
            name: Name of the pod
            namespace: Kubernetes namespace
            image: Container image
            command: Container command
            args: Container arguments
            env_vars: Environment variables
            labels: Labels for the pod
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with pod information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            name=name,
            namespace=namespace,
            image=image,
            command=command,
            args=args,
            env_vars=env_vars,
            labels=labels,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for K8s pod create command."""
        return "k8s:pod_create"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute K8s pod create command logic."""
        action = kwargs.get("action", "create")
        
        if action == "create":
            return await self._create_pod(**kwargs)
        elif action == "get":
            return await self._get_pod(**kwargs)
        elif action == "delete":
            return await self._delete_pod(**kwargs)
        elif action == "list":
            return await self._list_pods(**kwargs)
        else:
            raise CustomError(f"Unknown pod action: {action}")

    async def _create_pod(
        self,
        name: str = "my-pod",
        namespace: str = "default",
        image: str = "nginx:latest",
        command: Optional[List[str]] = None,
        args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create Kubernetes pod."""
        try:
            # Create pod YAML
            pod_yaml = f"""
apiVersion: v1
kind: Pod
metadata:
  name: {name}
  namespace: {namespace}
"""
            
            if labels:
                pod_yaml += "  labels:\n"
                for key, value in labels.items():
                    pod_yaml += f"    {key}: {value}\n"
            
            pod_yaml += """spec:
  containers:
  - name: """
            pod_yaml += f"{name}\n"
            pod_yaml += f"    image: {image}\n"
            
            if command:
                pod_yaml += "    command:\n"
                for cmd in command:
                    pod_yaml += f"    - {cmd}\n"
            
            if args:
                pod_yaml += "    args:\n"
                for arg in args:
                    pod_yaml += f"    - {arg}\n"
            
            if env_vars:
                pod_yaml += "    env:\n"
                for key, value in env_vars.items():
                    pod_yaml += f"    - name: {key}\n"
                    pod_yaml += f"      value: {value}\n"

            # Apply pod
            result = subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=pod_yaml,
                text=True,
                capture_output=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise CustomError(f"Pod creation failed: {result.stderr}")

            return {
                "message": f"Successfully created pod '{name}' in namespace '{namespace}'",
                "action": "create",
                "name": name,
                "namespace": namespace,
                "image": image,
                "command": command,
                "args": args,
                "env_vars": env_vars,
                "labels": labels,
                "pod_yaml": pod_yaml,
                "raw_output": result.stdout,
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Pod creation command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Pod creation failed: {str(e)}")

    async def _get_pod(
        self,
        name: str = "my-pod",
        namespace: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """Get Kubernetes pod."""
        try:
            cmd = ["kubectl", "get", "pod", name, "-n", namespace, "-o", "yaml"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Pod retrieval failed: {result.stderr}")

            return {
                "message": f"Retrieved pod '{name}' from namespace '{namespace}'",
                "action": "get",
                "name": name,
                "namespace": namespace,
                "pod_yaml": result.stdout,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Pod retrieval command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Pod retrieval failed: {str(e)}")

    async def _delete_pod(
        self,
        name: str = "my-pod",
        namespace: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """Delete Kubernetes pod."""
        try:
            cmd = ["kubectl", "delete", "pod", name, "-n", namespace]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Pod deletion failed: {result.stderr}")

            return {
                "message": f"Successfully deleted pod '{name}' from namespace '{namespace}'",
                "action": "delete",
                "name": name,
                "namespace": namespace,
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
        """Get JSON schema for K8s pod create command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Pod action (create, get, delete, list)",
                    "default": "create",
                    "enum": ["create", "get", "delete", "list"],
                },
                "name": {
                    "type": "string",
                    "description": "Name of the pod",
                    "default": "my-pod",
                },
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace",
                    "default": "default",
                },
                "image": {
                    "type": "string",
                    "description": "Container image",
                    "default": "nginx:latest",
                },
                "command": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Container command",
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Container arguments",
                },
                "env_vars": {
                    "type": "object",
                    "description": "Environment variables",
                },
                "labels": {
                    "type": "object",
                    "description": "Labels for the pod",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }