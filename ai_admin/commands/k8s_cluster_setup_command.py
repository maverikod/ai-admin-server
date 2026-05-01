from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import CustomError
"""Kubernetes cluster setup command for setting up complete clusters.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.k8s_security_adapter import K8sSecurityAdapter

class K8sClusterSetupCommand(BaseUnifiedCommand):
    """Command to setup complete Kubernetes clusters with certificate management."""

    name = "k8s_cluster_setup"
    
    def __init__(self):
        """Initialize K8s cluster setup command."""
        super().__init__()
        self.certs_base_dir = "./certificates"
        self.kubeconfigs_dir = "./kubeconfigs"
        self.clusters_dir = "./clusters"
        self.security_adapter = K8sSecurityAdapter()

    async def execute(
        self,
        action: str = "create",
        cluster_name: str = "my-cluster",
        cluster_type: str = "kind",
        cluster_config: Optional[Dict[str, Any]] = None,
        cert_config: Optional[Dict[str, Any]] = None,
        admin_user: str = "admin",
        admin_organization: str = "system:masters",
        server_url: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute K8s cluster setup command with unified security.
        
        Args:
            action: Setup action (create, destroy, status)
            cluster_name: Name of the cluster
            cluster_type: Type of cluster (kind, minikube, k3s)
            cluster_config: Cluster configuration
            cert_config: Certificate configuration
            admin_user: Admin user name
            admin_organization: Admin organization
            server_url: Server URL
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with setup information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            cluster_name=cluster_name,
            cluster_type=cluster_type,
            cluster_config=cluster_config,
            cert_config=cert_config,
            admin_user=admin_user,
            admin_organization=admin_organization,
            server_url=server_url,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for K8s cluster setup command."""
        return "k8s:cluster_setup"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute K8s cluster setup command logic."""
        action = kwargs.get("action", "create")
        
        if action == "create":
            return await self._create_cluster(**kwargs)
        elif action == "destroy":
            return await self._destroy_cluster(**kwargs)
        elif action == "status":
            return await self._get_cluster_status(**kwargs)
        else:
            raise CustomError(f"Unknown setup action: {action}")

    async def _create_cluster(
        self,
        cluster_name: str = "my-cluster",
        cluster_type: str = "kind",
        cluster_config: Optional[Dict[str, Any]] = None,
        cert_config: Optional[Dict[str, Any]] = None,
        admin_user: str = "admin",
        admin_organization: str = "system:masters",
        server_url: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create Kubernetes cluster."""
        try:
            if cluster_type == "kind":
                # Create kind cluster
                cmd = ["kind", "create", "cluster", "--name", cluster_name]
                
                if cluster_config:
                    # Add configuration options
                    if cluster_config.get("nodes"):
                        cmd.extend(["--config", "-"])
                        # Create config file content
                        config_content = f"""
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
"""
                        for node in cluster_config["nodes"]:
                            config_content += f"- role: {node.get('role', 'worker')}\n"
                            if node.get("image"):
                                config_content += f"  image: {node['image']}\n"
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    raise CustomError(f"Kind cluster creation failed: {result.stderr}")
                
            elif cluster_type == "minikube":
                # Create minikube cluster
                cmd = ["minikube", "start", "--profile", cluster_name]
                
                if cluster_config:
                    if cluster_config.get("driver"):
                        cmd.extend(["--driver", cluster_config["driver"]])
                    if cluster_config.get("memory"):
                        cmd.extend(["--memory", str(cluster_config["memory"])])
                    if cluster_config.get("cpus"):
                        cmd.extend(["--cpus", str(cluster_config["cpus"])])
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    raise CustomError(f"Minikube cluster creation failed: {result.stderr}")
                
            else:
                raise CustomError(f"Unsupported cluster type: {cluster_type}")

            return {
                "message": f"Successfully created {cluster_type} cluster '{cluster_name}'",
                "action": "create",
                "cluster_name": cluster_name,
                "cluster_type": cluster_type,
                "cluster_config": cluster_config,
                "cert_config": cert_config,
                "admin_user": admin_user,
                "admin_organization": admin_organization,
                "server_url": server_url,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Cluster creation command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Cluster creation failed: {str(e)}")

    async def _destroy_cluster(
        self,
        cluster_name: str = "my-cluster",
        cluster_type: str = "kind",
        **kwargs,
    ) -> Dict[str, Any]:
        """Destroy Kubernetes cluster."""
        try:
            if cluster_type == "kind":
                cmd = ["kind", "delete", "cluster", "--name", cluster_name]
            elif cluster_type == "minikube":
                cmd = ["minikube", "delete", "--profile", cluster_name]
            else:
                raise CustomError(f"Unsupported cluster type: {cluster_type}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise CustomError(f"Cluster destruction failed: {result.stderr}")

            return {
                "message": f"Successfully destroyed {cluster_type} cluster '{cluster_name}'",
                "action": "destroy",
                "cluster_name": cluster_name,
                "cluster_type": cluster_type,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Cluster destruction command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Cluster destruction failed: {str(e)}")

    async def _get_cluster_status(
        self,
        cluster_name: str = "my-cluster",
        cluster_type: str = "kind",
        **kwargs,
    ) -> Dict[str, Any]:
        """Get cluster status."""
        try:
            if cluster_type == "kind":
                # Check if kind cluster exists
                result = subprocess.run(
                    ["kind", "get", "clusters"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                
                if result.returncode == 0:
                    clusters = result.stdout.strip().split("\n")
                    exists = cluster_name in clusters
                else:
                    exists = False
                    
            elif cluster_type == "minikube":
                # Check minikube status
                result = subprocess.run(
                    ["minikube", "status", "--profile", cluster_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                
                exists = result.returncode == 0
            else:
                raise CustomError(f"Unsupported cluster type: {cluster_type}")

            return {
                "message": f"Cluster status for {cluster_type} cluster '{cluster_name}'",
                "action": "status",
                "cluster_name": cluster_name,
                "cluster_type": cluster_type,
                "exists": exists,
                "status": "running" if exists else "not_found",
                "raw_output": result.stdout if result.returncode == 0 else result.stderr,
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Cluster status command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Failed to get cluster status: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for K8s cluster setup command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Setup action (create, destroy, status)",
                    "default": "create",
                    "enum": ["create", "destroy", "status"],
                },
                "cluster_name": {
                    "type": "string",
                    "description": "Name of the cluster",
                    "default": "my-cluster",
                },
                "cluster_type": {
                    "type": "string",
                    "description": "Type of cluster (kind, minikube, k3s)",
                    "default": "kind",
                    "enum": ["kind", "minikube", "k3s"],
                },
                "cluster_config": {
                    "type": "object",
                    "description": "Cluster configuration",
                },
                "cert_config": {
                    "type": "object",
                    "description": "Certificate configuration",
                },
                "admin_user": {
                    "type": "string",
                    "description": "Admin user name",
                    "default": "admin",
                },
                "admin_organization": {
                    "type": "string",
                    "description": "Admin organization",
                    "default": "system:masters",
                },
                "server_url": {
                    "type": "string",
                    "description": "Server URL",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }