from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Kubernetes deployment create command for creating deployments.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.k8s_security_adapter import K8sSecurityAdapter

class K8sDeploymentCreateCommand(BaseUnifiedCommand):
    """Command to create Kubernetes deployments for projects using kubernetes Python library."""

    name = "k8s_deployment_create"
    
    def __init__(self):
        """Initialize K8s deployment create command."""
        super().__init__()
        self.security_adapter = K8sSecurityAdapter()

    async def execute(
        self,
        action: str = "create",
        name: str = "my-deployment",
        namespace: str = "default",
        image: str = "nginx:latest",
        replicas: int = 1,
        port: Optional[int] = None,
        env_vars: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute K8s deployment create command with unified security.
        
        Args:
            action: Deployment action (create, get, delete, list, scale)
            name: Name of the deployment
            namespace: Kubernetes namespace
            image: Container image
            replicas: Number of replicas
            port: Container port
            env_vars: Environment variables
            labels: Labels for the deployment
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with deployment information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            name=name,
            namespace=namespace,
            image=image,
            replicas=replicas,
            port=port,
            env_vars=env_vars,
            labels=labels,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for K8s deployment create command."""
        return "k8s:deployment_create"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute K8s deployment create command logic."""
        action = kwargs.get("action", "create")
        
        if action == "create":
            return await self._create_deployment(**kwargs)
        elif action == "get":
            return await self._get_deployment(**kwargs)
        elif action == "delete":
            return await self._delete_deployment(**kwargs)
        elif action == "list":
            return await self._list_deployments(**kwargs)
        elif action == "scale":
            return await self._scale_deployment(**kwargs)
        else:
            raise CustomError(f"Unknown deployment action: {action}")

    async def _create_deployment(
        self,
        name: str = "my-deployment",
        namespace: str = "default",
        image: str = "nginx:latest",
        replicas: int = 1,
        port: Optional[int] = None,
        env_vars: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create Kubernetes deployment."""
        try:
            # Create deployment YAML
            deployment_yaml = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {namespace}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
"""
            
            if labels:
                for key, value in labels.items():
                    deployment_yaml += f"        {key}: {value}\n"
            
            deployment_yaml += """    spec:
      containers:
      - name: """
            deployment_yaml += f"{name}\n"
            deployment_yaml += f"        image: {image}\n"
            
            if port:
                deployment_yaml += f"        ports:\n"
                deployment_yaml += f"        - containerPort: {port}\n"
            
            if env_vars:
                deployment_yaml += "        env:\n"
                for key, value in env_vars.items():
                    deployment_yaml += f"        - name: {key}\n"
                    deployment_yaml += f"          value: {value}\n"

            # Apply deployment
            result = subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=deployment_yaml,
                text=True,
                capture_output=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise CustomError(f"Deployment creation failed: {result.stderr}")

            return {
                "message": f"Successfully created deployment '{name}' in namespace '{namespace}'",
                "action": "create",
                "name": name,
                "namespace": namespace,
                "image": image,
                "replicas": replicas,
                "port": port,
                "env_vars": env_vars,
                "labels": labels,
                "deployment_yaml": deployment_yaml,
                "raw_output": result.stdout,
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Deployment creation command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Deployment creation failed: {str(e)}")

    async def _get_deployment(
        self,
        name: str = "my-deployment",
        namespace: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """Get Kubernetes deployment."""
        try:
            cmd = ["kubectl", "get", "deployment", name, "-n", namespace, "-o", "yaml"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Deployment retrieval failed: {result.stderr}")

            return {
                "message": f"Retrieved deployment '{name}' from namespace '{namespace}'",
                "action": "get",
                "name": name,
                "namespace": namespace,
                "deployment_yaml": result.stdout,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Deployment retrieval command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Deployment retrieval failed: {str(e)}")

    async def _delete_deployment(
        self,
        name: str = "my-deployment",
        namespace: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """Delete Kubernetes deployment."""
        try:
            cmd = ["kubectl", "delete", "deployment", name, "-n", namespace]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Deployment deletion failed: {result.stderr}")

            return {
                "message": f"Successfully deleted deployment '{name}' from namespace '{namespace}'",
                "action": "delete",
                "name": name,
                "namespace": namespace,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Deployment deletion command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Deployment deletion failed: {str(e)}")

    async def _list_deployments(
        self,
        namespace: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """List Kubernetes deployments."""
        try:
            cmd = ["kubectl", "get", "deployments", "-n", namespace, "-o", "wide"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Deployment listing failed: {result.stderr}")

            deployments = []
            lines = result.stdout.strip().split("\n")
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 6:
                        deployments.append({
                            "name": parts[0],
                            "ready": parts[1],
                            "up_to_date": parts[2],
                            "available": parts[3],
                            "age": parts[4],
                        })

            return {
                "message": f"Found {len(deployments)} deployments in namespace '{namespace}'",
                "action": "list",
                "namespace": namespace,
                "deployments": deployments,
                "count": len(deployments),
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Deployment listing command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Deployment listing failed: {str(e)}")

    async def _scale_deployment(
        self,
        name: str = "my-deployment",
        namespace: str = "default",
        replicas: int = 1,
        **kwargs,
    ) -> Dict[str, Any]:
        """Scale Kubernetes deployment."""
        try:
            cmd = ["kubectl", "scale", "deployment", name, f"--replicas={replicas}", "-n", namespace]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Deployment scaling failed: {result.stderr}")

            return {
                "message": f"Successfully scaled deployment '{name}' to {replicas} replicas in namespace '{namespace}'",
                "action": "scale",
                "name": name,
                "namespace": namespace,
                "replicas": replicas,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Deployment scaling command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Deployment scaling failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for K8s deployment create command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Deployment action (create, get, delete, list, scale)",
                    "default": "create",
                    "enum": ["create", "get", "delete", "list", "scale"],
                },
                "name": {
                    "type": "string",
                    "description": "Name of the deployment",
                    "default": "my-deployment",
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
                "replicas": {
                    "type": "integer",
                    "description": "Number of replicas",
                    "default": 1,
                },
                "port": {
                    "type": "integer",
                    "description": "Container port",
                },
                "env_vars": {
                    "type": "object",
                    "description": "Environment variables",
                },
                "labels": {
                    "type": "object",
                    "description": "Labels for the deployment",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }