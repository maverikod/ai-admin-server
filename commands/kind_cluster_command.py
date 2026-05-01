from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Kind cluster command for managing Kind Kubernetes clusters.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.k8s_security_adapter import K8sSecurityAdapter

class KindClusterCommand(BaseUnifiedCommand):
    """Command to manage Kind Kubernetes clusters using Python library."""

    name = "kind_cluster"
    
    def __init__(self):
        """Initialize Kind cluster command."""
        super().__init__()
        self.kind_path = "kind"  # Assume kind is in PATH
        self.security_adapter = K8sSecurityAdapter()

    async def execute(
        self,
        action: str = "create",
        cluster_name: Optional[str] = None,
        config_file: Optional[str] = None,
        image: Optional[str] = None,
        wait: int = 60,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Kind cluster command with unified security.
        
        Args:
            action: Kind action (create, delete, list, get)
            cluster_name: Name of the cluster
            config_file: Path to Kind config file
            image: Kind node image
            wait: Wait time for cluster creation
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with Kind cluster information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            cluster_name=cluster_name,
            config_file=config_file,
            image=image,
            wait=wait,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Kind cluster command."""
        return "kind:cluster"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Kind cluster command logic."""
        action = kwargs.get("action", "create")
        
        if action == "create":
            return await self._create_cluster(**kwargs)
        elif action == "delete":
            return await self._delete_cluster(**kwargs)
        elif action == "list":
            return await self._list_clusters(**kwargs)
        elif action == "get":
            return await self._get_cluster(**kwargs)
        else:
            raise CustomError(f"Unknown Kind action: {action}")

    async def _create_cluster(
        self,
        cluster_name: Optional[str] = None,
        config_file: Optional[str] = None,
        image: Optional[str] = None,
        wait: int = 60,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create Kind cluster."""
        try:
            if not cluster_name:
                cluster_name = "kind"

            cmd = ["kind", "create", "cluster", "--name", cluster_name]
            
            if config_file:
                cmd.extend(["--config", config_file])
            if image:
                cmd.extend(["--image", image])
            if wait:
                cmd.extend(["--wait", f"{wait}s"])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                raise CustomError(f"Kind cluster creation failed: {result.stderr}")

            return {
                "message": f"Successfully created Kind cluster '{cluster_name}'",
                "action": "create",
                "cluster_name": cluster_name,
                "config_file": config_file,
                "image": image,
                "wait": wait,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Kind cluster creation command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Kind cluster creation failed: {str(e)}")

    async def _delete_cluster(
        self,
        cluster_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Delete Kind cluster."""
        try:
            if not cluster_name:
                cluster_name = "kind"

            cmd = ["kind", "delete", "cluster", "--name", cluster_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise CustomError(f"Kind cluster deletion failed: {result.stderr}")

            return {
                "message": f"Successfully deleted Kind cluster '{cluster_name}'",
                "action": "delete",
                "cluster_name": cluster_name,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Kind cluster deletion command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Kind cluster deletion failed: {str(e)}")

    async def _list_clusters(
        self,
        **kwargs,
    ) -> Dict[str, Any]:
        """List Kind clusters."""
        try:
            cmd = ["kind", "get", "clusters"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Kind cluster listing failed: {result.stderr}")

            clusters = [cluster.strip() for cluster in result.stdout.strip().split("\n") if cluster.strip()]

            return {
                "message": f"Found {len(clusters)} Kind clusters",
                "action": "list",
                "clusters": clusters,
                "count": len(clusters),
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Kind cluster listing command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Kind cluster listing failed: {str(e)}")

    async def _get_cluster(
        self,
        cluster_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get Kind cluster information."""
        try:
            if not cluster_name:
                cluster_name = "kind"

            # Check if cluster exists
            list_result = await self._list_clusters()
            clusters = list_result.get("clusters", [])
            
            if cluster_name not in clusters:
                raise CustomError(f"Kind cluster '{cluster_name}' not found")

            # Get cluster info
            cmd = ["kubectl", "cluster-info", "--context", f"kind-{cluster_name}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Failed to get cluster info: {result.stderr}")

            return {
                "message": f"Retrieved information for Kind cluster '{cluster_name}'",
                "action": "get",
                "cluster_name": cluster_name,
                "cluster_info": result.stdout,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Kind cluster info command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Kind cluster info retrieval failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Kind cluster command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Kind action (create, delete, list, get)",
                    "default": "create",
                    "enum": ["create", "delete", "list", "get"],
                },
                "cluster_name": {
                    "type": "string",
                    "description": "Name of the cluster",
                },
                "config_file": {
                    "type": "string",
                    "description": "Path to Kind config file",
                },
                "image": {
                    "type": "string",
                    "description": "Kind node image",
                },
                "wait": {
                    "type": "integer",
                    "description": "Wait time for cluster creation",
                    "default": 60,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }