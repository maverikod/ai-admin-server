from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError, AuthorizationError
"""Kubernetes cluster management command for MCP server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Optional, List, Dict, Any
from datetime import datetime
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.k8s_security_adapter import K8sSecurityAdapter

class K8sClusterCommand(BaseUnifiedCommand):
    """Command to manage Kubernetes clusters and test connections."""

    name = "k8s_cluster"
    
    def __init__(self):
        """Initialize K8s cluster command."""
        super().__init__()
        self.security_adapter = K8sSecurityAdapter()

    async def execute(
        self,
        action: str = "list",
        cluster_name: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """
        Manage Kubernetes clusters.

        Args:
            action: Action to perform (list, test, info, switch)
            cluster_name: Name of the cluster to work with
            user_roles: List of user roles for security validation
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            cluster_name=cluster_name,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for K8s cluster command."""
        return "k8s:cluster"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute K8s cluster command logic."""
        action = kwargs.get("action", "list")
        cluster_name = kwargs.get("cluster_name")
        
        if action == "list":
            return await self._list_clusters(**kwargs)
        elif action == "test":
            return await self._test_cluster(cluster_name, **kwargs)
        elif action == "info":
            return await self._get_cluster_info(cluster_name, **kwargs)
        elif action == "switch":
            return await self._switch_cluster(cluster_name, **kwargs)
        else:
            raise CustomError(f"Unknown action: {action}")

    async def _list_clusters(self, **kwargs) -> Dict[str, Any]:
        """List available clusters."""
        try:
            # Get current context
            result = subprocess.run(
                ["kubectl", "config", "current-context"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            current_context = result.stdout.strip() if result.returncode == 0 else "unknown"

            # Get all contexts
            result = subprocess.run(
                ["kubectl", "config", "get-contexts", "-o", "name"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise CustomError(f"Failed to get contexts: {result.stderr}")

            contexts = [ctx.strip() for ctx in result.stdout.strip().split("\n") if ctx.strip()]

            cluster_list = []
            for context in contexts:
                cluster_list.append({
                    "name": context,
                    "current": context == current_context,
                })

            return {
                "message": f"Found {len(cluster_list)} clusters",
                "action": "list",
                "clusters": cluster_list,
                "current_context": current_context,
                "count": len(cluster_list),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Cluster list command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Failed to list clusters: {str(e)}")

    async def _test_cluster(self, cluster_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Test connection to a cluster."""
        try:
            if not cluster_name:
                # Test current cluster
                cmd = ["kubectl", "cluster-info"]
            else:
                # Test specific cluster
                cmd = ["kubectl", "cluster-info", "--context", cluster_name]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {
                    "message": f"Connection to cluster '{cluster_name or 'current'}' successful",
                    "action": "test",
                    "cluster_name": cluster_name,
                    "success": True,
                    "cluster_info": result.stdout,
                    "raw_output": result.stdout,
                    "command": " ".join(cmd),
                }
            else:
                return {
                    "message": f"Connection to cluster '{cluster_name or 'current'}' failed",
                    "action": "test",
                    "cluster_name": cluster_name,
                    "success": False,
                    "error": result.stderr,
                    "raw_output": result.stderr,
                    "command": " ".join(cmd),
                }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Cluster test command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Failed to test cluster: {str(e)}")

    async def _get_cluster_info(self, cluster_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Get detailed information about a cluster."""
        try:
            if not cluster_name:
                cluster_name = "current"

            # Get cluster info
            cmd = ["kubectl", "cluster-info"]
            if cluster_name != "current":
                cmd.extend(["--context", cluster_name])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Failed to get cluster info: {result.stderr}")

            # Get nodes info
            nodes_cmd = ["kubectl", "get", "nodes", "-o", "wide"]
            if cluster_name != "current":
                nodes_cmd.extend(["--context", cluster_name])

            nodes_result = subprocess.run(nodes_cmd, capture_output=True, text=True, timeout=30)

            cluster_info = {
                "cluster_info": result.stdout,
                "nodes_info": nodes_result.stdout if nodes_result.returncode == 0 else "Failed to get nodes info",
            }

            return {
                "message": f"Cluster information for '{cluster_name}'",
                "action": "info",
                "cluster_name": cluster_name,
                "cluster_info": cluster_info,
                "timestamp": datetime.now().isoformat(),
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Cluster info command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Failed to get cluster info: {str(e)}")

    async def _switch_cluster(self, cluster_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Switch to a different cluster."""
        try:
            if not cluster_name:
                raise CustomError("Cluster name is required for switch action")

            # Test the connection first
            test_result = await self._test_cluster(cluster_name)
            if not test_result.get("success", False):
                raise AuthorizationError(f"Cluster '{cluster_name}' is not accessible")

            # Switch context
            result = subprocess.run(
                ["kubectl", "config", "use-context", cluster_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise CustomError(f"Failed to switch context: {result.stderr}")

            return {
                "message": f"Successfully switched to cluster '{cluster_name}'",
                "action": "switch",
                "cluster_name": cluster_name,
                "success": True,
                "raw_output": result.stdout,
                "command": f"kubectl config use-context {cluster_name}",
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Cluster switch command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Failed to switch to cluster '{cluster_name}': {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for K8s cluster command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform (list, test, info, switch)",
                    "default": "list",
                    "enum": ["list", "test", "info", "switch"],
                },
                "cluster_name": {
                    "type": "string",
                    "description": "Name of the cluster to work with",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }