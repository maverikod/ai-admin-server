from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import CustomError
"""Kubernetes service create command for creating services.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.k8s_security_adapter import K8sSecurityAdapter

class K8sServiceCreateCommand(BaseUnifiedCommand):
    """Command to create Kubernetes services for projects using Python kubernetes library."""

    name = "k8s_service_create"
    
    def __init__(self):
        """Initialize K8s service create command."""
        super().__init__()
        self.security_adapter = K8sSecurityAdapter()

    async def execute(
        self,
        action: str = "create",
        name: str = "my-service",
        namespace: str = "default",
        service_type: str = "ClusterIP",
        port: int = 80,
        target_port: Optional[int] = None,
        selector: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute K8s service create command with unified security.
        
        Args:
            action: Service action (create, get, delete, list)
            name: Name of the service
            namespace: Kubernetes namespace
            service_type: Type of service (ClusterIP, NodePort, LoadBalancer)
            port: Service port
            target_port: Target port
            selector: Pod selector
            labels: Labels for the service
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with service information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            name=name,
            namespace=namespace,
            service_type=service_type,
            port=port,
            target_port=target_port,
            selector=selector,
            labels=labels,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for K8s service create command."""
        return "k8s:service_create"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute K8s service create command logic."""
        action = kwargs.get("action", "create")
        
        if action == "create":
            return await self._create_service(**kwargs)
        elif action == "get":
            return await self._get_service(**kwargs)
        elif action == "delete":
            return await self._delete_service(**kwargs)
        elif action == "list":
            return await self._list_services(**kwargs)
        else:
            raise CustomError(f"Unknown service action: {action}")

    async def _create_service(
        self,
        name: str = "my-service",
        namespace: str = "default",
        service_type: str = "ClusterIP",
        port: int = 80,
        target_port: Optional[int] = None,
        selector: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create Kubernetes service."""
        try:
            if target_port is None:
                target_port = port

            # Create service YAML
            service_yaml = f"""
apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: {namespace}
"""
            
            if labels:
                service_yaml += "  labels:\n"
                for key, value in labels.items():
                    service_yaml += f"    {key}: {value}\n"
            
            service_yaml += f"""spec:
  type: {service_type}
  ports:
  - port: {port}
    targetPort: {target_port}
"""
            
            if selector:
                service_yaml += "  selector:\n"
                for key, value in selector.items():
                    service_yaml += f"    {key}: {value}\n"

            # Apply service
            result = subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=service_yaml,
                text=True,
                capture_output=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise CustomError(f"Service creation failed: {result.stderr}")

            return {
                "message": f"Successfully created service '{name}' in namespace '{namespace}'",
                "action": "create",
                "name": name,
                "namespace": namespace,
                "service_type": service_type,
                "port": port,
                "target_port": target_port,
                "selector": selector,
                "labels": labels,
                "service_yaml": service_yaml,
                "raw_output": result.stdout,
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Service creation command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Service creation failed: {str(e)}")

    async def _get_service(
        self,
        name: str = "my-service",
        namespace: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """Get Kubernetes service."""
        try:
            cmd = ["kubectl", "get", "service", name, "-n", namespace, "-o", "yaml"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Service retrieval failed: {result.stderr}")

            return {
                "message": f"Retrieved service '{name}' from namespace '{namespace}'",
                "action": "get",
                "name": name,
                "namespace": namespace,
                "service_yaml": result.stdout,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Service retrieval command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Service retrieval failed: {str(e)}")

    async def _delete_service(
        self,
        name: str = "my-service",
        namespace: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """Delete Kubernetes service."""
        try:
            cmd = ["kubectl", "delete", "service", name, "-n", namespace]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Service deletion failed: {result.stderr}")

            return {
                "message": f"Successfully deleted service '{name}' from namespace '{namespace}'",
                "action": "delete",
                "name": name,
                "namespace": namespace,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Service deletion command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Service deletion failed: {str(e)}")

    async def _list_services(
        self,
        namespace: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """List Kubernetes services."""
        try:
            cmd = ["kubectl", "get", "services", "-n", namespace, "-o", "wide"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Service listing failed: {result.stderr}")

            services = []
            lines = result.stdout.strip().split("\n")
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 5:
                        services.append({
                            "name": parts[0],
                            "type": parts[1],
                            "cluster_ip": parts[2],
                            "external_ip": parts[3],
                            "port": parts[4],
                        })

            return {
                "message": f"Found {len(services)} services in namespace '{namespace}'",
                "action": "list",
                "namespace": namespace,
                "services": services,
                "count": len(services),
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Service listing command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Service listing failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for K8s service create command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Service action (create, get, delete, list)",
                    "default": "create",
                    "enum": ["create", "get", "delete", "list"],
                },
                "name": {
                    "type": "string",
                    "description": "Name of the service",
                    "default": "my-service",
                },
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace",
                    "default": "default",
                },
                "service_type": {
                    "type": "string",
                    "description": "Type of service (ClusterIP, NodePort, LoadBalancer)",
                    "default": "ClusterIP",
                    "enum": ["ClusterIP", "NodePort", "LoadBalancer"],
                },
                "port": {
                    "type": "integer",
                    "description": "Service port",
                    "default": 80,
                },
                "target_port": {
                    "type": "integer",
                    "description": "Target port",
                },
                "selector": {
                    "type": "object",
                    "description": "Pod selector",
                },
                "labels": {
                    "type": "object",
                    "description": "Labels for the service",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }