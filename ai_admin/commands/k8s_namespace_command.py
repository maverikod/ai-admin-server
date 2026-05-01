"""K8s namespace command."""

from mcp_proxy_adapter.commands.result import SuccessResult

from ai_admin.core.custom_exceptions import CustomError

"""Kubernetes namespace command for managing namespaces.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""


import subprocess

from typing import Dict, Any, Optional, List

from ai_admin.commands.base_unified_command import BaseUnifiedCommand

from ai_admin.security.k8s_security_adapter import K8sSecurityAdapter


class K8sNamespaceCommand:
    """Command to create Kubernetes namespaces using Python kubernetes library."""

    name = "k8s_namespace"

    def __init__(self):
        """Initialize K8s namespace command."""
        super().__init__()
        self.security_adapter = K8sSecurityAdapter()

    async def execute(
        self,
        action: str = "create",
        name: str = "my-namespace",
        labels: Optional[Dict[str, str]] = None,
        annotations: Optional[Dict[str, str]] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute K8s namespace command with unified security.

        Args:
            action: Namespace action (create, get, delete, list)
            name: Name of the namespace
            labels: Labels for the namespace
            annotations: Annotations for the namespace
            user_roles: List of user roles for security validation

        Returns:
            Success result with namespace information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            name=name,
            labels=labels,
            annotations=annotations,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for K8s namespace command."""
        return "k8s:namespace"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute K8s namespace command logic."""
        action = kwargs.get("action", "create")

        if action == "create":
            return await self._create_namespace(**kwargs)
        elif action == "get":
            return await self._get_namespace(**kwargs)
        elif action == "delete":
            return await self._delete_namespace(**kwargs)
        elif action == "list":
            return await self._list_namespaces(**kwargs)
        else:
            raise CustomError(f"Unknown namespace action: {action}")

    async def _create_namespace(
        self,
        name: str = "my-namespace",
        labels: Optional[Dict[str, str]] = None,
        annotations: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create Kubernetes namespace."""
        try:
            # Create namespace YAML
            namespace_yaml = f"""
    apiVersion: v1
    kind: Namespace
    metadata:
      name: {name}
    """

            if labels:
                namespace_yaml += "  labels:\n"
                for key, value in labels.items():
                    namespace_yaml += f"    {key}: {value}\n"

            if annotations:
                namespace_yaml += "  annotations:\n"
                for key, value in annotations.items():
                    namespace_yaml += f"    {key}: {value}\n"

            # Apply namespace
            result = subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=namespace_yaml,
                text=True,
                capture_output=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise CustomError(f"Namespace creation failed: {result.stderr}")

            return {
                "message": f"Successfully created namespace '{name}'",
                "action": "create",
                "name": name,
                "labels": labels,
                "annotations": annotations,
                "namespace_yaml": namespace_yaml,
                "raw_output": result.stdout,
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Namespace creation command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Namespace creation failed: {str(e)}")

    async def _get_namespace(
        self,
        name: str = "my-namespace",
        **kwargs,
    ) -> Dict[str, Any]:
        """Get Kubernetes namespace."""
        try:
            cmd = ["kubectl", "get", "namespace", name, "-o", "yaml"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Namespace retrieval failed: {result.stderr}")

            return {
                "message": f"Retrieved namespace '{name}'",
                "action": "get",
                "name": name,
                "namespace_yaml": result.stdout,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Namespace retrieval command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Namespace retrieval failed: {str(e)}")

    async def _delete_namespace(
        self,
        name: str = "my-namespace",
        **kwargs,
    ) -> Dict[str, Any]:
        """Delete Kubernetes namespace."""
        try:
            cmd = ["kubectl", "delete", "namespace", name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Namespace deletion failed: {result.stderr}")

            return {
                "message": f"Successfully deleted namespace '{name}'",
                "action": "delete",
                "name": name,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Namespace deletion command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Namespace deletion failed: {str(e)}")

    async def _list_namespaces(
        self,
        **kwargs,
    ) -> Dict[str, Any]:
        """List Kubernetes namespaces."""
        try:
            cmd = ["kubectl", "get", "namespaces", "-o", "wide"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Namespace listing failed: {result.stderr}")

            namespaces = []
            lines = result.stdout.strip().split("\n")
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        namespaces.append(
                            {
                                "name": parts[0],
                                "status": parts[1],
                                "age": parts[2],
                            }
                        )

            return {
                "message": f"Found {len(namespaces)} namespaces",
                "action": "list",
                "namespaces": namespaces,
                "count": len(namespaces),
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Namespace listing command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Namespace listing failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for K8s namespace command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Namespace action (create, get, delete, list)",
                    "default": "create",
                    "enum": ["create", "get", "delete", "list"],
                },
                "name": {
                    "type": "string",
                    "description": "Name of the namespace",
                    "default": "my-namespace",
                },
                "labels": {
                    "type": "object",
                    "description": "Labels for the namespace",
                },
                "annotations": {
                    "type": "object",
                    "description": "Annotations for the namespace",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
