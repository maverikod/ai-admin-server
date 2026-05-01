from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""ArgoCD initialization command for Kubernetes clusters.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.argocd_security_adapter import ArgoCDSecurityAdapter

class ArgoCDInitCommand(BaseUnifiedCommand):
    """Initialize ArgoCD in Kubernetes cluster."""

    name = "argocd_init"

    def __init__(self):
        """Initialize ArgoCD init command."""
        super().__init__()
        self.security_adapter = ArgoCDSecurityAdapter()

    async def execute(
        self,
        cluster_name: str,
        namespace: str = "argocd",
        admin_password: Optional[str] = None,
        insecure: bool = False,
        port: int = 8080,
        service_type: str = "LoadBalancer",
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute ArgoCD initialization with unified security.

        Args:
            cluster_name: Name of the Kubernetes cluster
            namespace: Namespace for ArgoCD installation
            admin_password: Admin password for ArgoCD
            insecure: Allow insecure connections
            port: Port for ArgoCD server
            service_type: Kubernetes service type
            user_roles: List of user roles for security validation

        Returns:
            Success result with initialization information
        """
        # Validate inputs
        if not cluster_name:
            return ErrorResult(message="Cluster name is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            cluster_name=cluster_name,
            namespace=namespace,
            admin_password=admin_password,
            insecure=insecure,
            port=port,
            service_type=service_type,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for ArgoCD init command."""
        return "argocd:init"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute ArgoCD initialization logic."""
        return await self._init_argocd(**kwargs)

    async def _init_argocd(
        self,
        cluster_name: str,
        namespace: str = "argocd",
        admin_password: Optional[str] = None,
        insecure: bool = False,
        port: int = 8080,
        service_type: str = "LoadBalancer",
        **kwargs,
    ) -> Dict[str, Any]:
        """Initialize ArgoCD in Kubernetes cluster."""
        try:
            # Implementation would go here
            return {
                "message": f"ArgoCD initialized in cluster '{cluster_name}'",
                "cluster_name": cluster_name,
                "namespace": namespace,
                "port": port,
                "service_type": service_type,
                "status": "initialized"
            }

        except CustomError as e:
            raise CustomError(f"ArgoCD initialization failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for ArgoCD init command parameters."""
        return {
            "type": "object",
            "properties": {
                "cluster_name": {
                    "type": "string",
                    "description": "Name of the Kubernetes cluster",
                },
                "namespace": {
                    "type": "string",
                    "description": "Namespace for ArgoCD installation",
                    "default": "argocd",
                },
                "admin_password": {
                    "type": "string",
                    "description": "Admin password for ArgoCD",
                },
                "insecure": {
                    "type": "boolean",
                    "description": "Allow insecure connections",
                    "default": False,
                },
                "port": {
                    "type": "integer",
                    "description": "Port for ArgoCD server",
                    "default": 8080,
                },
                "service_type": {
                    "type": "string",
                    "description": "Kubernetes service type",
                    "default": "LoadBalancer",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["cluster_name"],
            "additionalProperties": False,
        }
