from ai_admin.core.custom_exceptions import CustomError, NetworkError
"""Kubernetes utilities for managing clusters and configurations.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List

class KubernetesConfigManager:
    """Manager for Kubernetes cluster configurations."""

    def __init__(self, config_data: Dict[str]):
        """Initialize config manager with settings."""
        self.config_data = config_data
        self.clusters = config_data.get("kubernetes_clusters", {})
        self.default_cluster = config_data.get("default_kubernetes_cluster", "default")
        self.current_cluster = None
        self.current_client = None
        self.docker_client = None

    def list_clusters(self) -> List[str]:
        """List available cluster names."""
        return list(self.clusters.keys())

    def get_cluster_config(self, cluster_name: str) -> Dict[str, Any]:
        """Get configuration for a specific cluster."""
        return self.clusters.get(cluster_name, {})

    def set_default_cluster(self, cluster_name: str) -> bool:
        """Set the default cluster."""
        if cluster_name in self.clusters:
            self.default_cluster = cluster_name
            return True
        return False

    def test_connection(self, cluster_name: Optional[str] = None) -> Dict[str, Any]:
        """Test connection to a cluster."""
        try:
            if not cluster_name:
                cluster_name = self.default_cluster

            # Test kubectl connection
            result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "cluster": cluster_name,
                    "info": result.stdout,
                }
            else:
                return {
                    "success": False,
                    "cluster": cluster_name,
                    "error": result.stderr,
                }

        except subprocess.TimeoutExpired as e:
            return {
                "success": False,
                "cluster": cluster_name,
                "error": f"Connection timeout: {str(e)}",
            }
        except NetworkError as e:
            return {
                "success": False,
                "cluster": cluster_name,
                "error": f"Connection failed: {str(e)}",
            }

    def get_cluster_info(self, cluster_name: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed information about a cluster."""
        try:
            if not cluster_name:
                cluster_name = self.default_cluster

            # Get cluster info
            result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise CustomError(f"Failed to get cluster info: {result.stderr}")

            # Get nodes info
            nodes_result = subprocess.run(
                ["kubectl", "get", "nodes", "-o", "wide"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            return {
                "cluster_name": cluster_name,
                "cluster_info": result.stdout,
                "nodes_info": nodes_result.stdout if nodes_result.returncode == 0 else "Failed to get nodes info",
                "config": self.get_cluster_config(cluster_name),
            }

        except CustomError as e:
            raise CustomError(f"Failed to get cluster info: {str(e)}")

    def switch_cluster(self, cluster_name: str) -> bool:
        """Switch to a different cluster."""
        try:
            if cluster_name not in self.clusters:
                return False

            # Test connection first
            test_result = self.test_connection(cluster_name)
            if not test_result.get("success", False):
                return False

            # Switch context
            result = subprocess.run(
                ["kubectl", "config", "use-context", cluster_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.current_cluster = cluster_name
                return True
            return False

        except CustomError as e:
            print(f"Failed to switch cluster: {str(e)}")
            return False

def get_k8s_config_manager() -> KubernetesConfigManager:
    """Get Kubernetes config manager instance."""
    # Default configuration
    default_config = {
        "kubernetes_clusters": {
            "default": {
                "context": "default",
                "namespace": "default",
            }
        },
        "default_kubernetes_cluster": "default",
    }
    
    return KubernetesConfigManager(default_config)

def validate_k8s_connection() -> bool:
    """Validate Kubernetes connection."""
    try:
        result = subprocess.run(
            ["kubectl", "version", "--client"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except CustomError:
        return False

def get_k8s_contexts() -> List[str]:
    """Get available Kubernetes contexts."""
    try:
        result = subprocess.run(
            ["kubectl", "config", "get-contexts", "-o", "name"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            return [ctx.strip() for ctx in result.stdout.strip().split("\n") if ctx.strip()]
        return []
    except CustomError:
        return []

def get_current_k8s_context() -> Optional[str]:
    """Get current Kubernetes context."""
    try:
        result = subprocess.run(
            ["kubectl", "config", "current-context"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except CustomError:
        return None