"""Kubernetes utilities for managing multiple clusters."""

import os
import tempfile
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from kubernetes import client, config
from kubernetes.client.rest import ApiException


class KubernetesConfigManager:
    """Manager for Kubernetes cluster configurations."""
    
    def __init__(self, config_data: Dict[str, Any]):
        """Initialize with configuration data."""
        self.config = config_data.get("kubernetes", {})
        self.clusters = self.config.get("clusters", {})
        self.default_cluster = self.config.get("default_cluster", "local")
        self.current_cluster = None
        self.current_client = None
    
    def get_cluster_config(self, cluster_name: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for a specific cluster."""
        if not cluster_name:
            cluster_name = self.default_cluster
        
        if cluster_name not in self.clusters:
            raise ValueError(f"Cluster '{cluster_name}' not found in configuration")
        
        return self.clusters[cluster_name]
    
    def get_available_clusters(self) -> List[str]:
        """Get list of available cluster names."""
        return list(self.clusters.keys())
    
    def load_kubeconfig(self, cluster_name: Optional[str] = None) -> bool:
        """Load kubeconfig for a specific cluster."""
        try:
            cluster_config = self.get_cluster_config(cluster_name)
            cluster_type = cluster_config.get("type", "k3s")
            
            if cluster_type == "docker_k3s":
                return self._load_docker_k3s_config(cluster_config)
            else:
                return self._load_standard_kubeconfig(cluster_config)
                
        except Exception as e:
            print(f"Failed to load kubeconfig for cluster {cluster_name}: {e}")
            return False
    
    def _load_docker_k3s_config(self, cluster_config: Dict[str, Any]) -> bool:
        """Load kubeconfig from Docker K3s container."""
        try:
            container_name = cluster_config.get("container_name", "k3s-server")
            
            # Get kubeconfig from container
            import subprocess
            result = subprocess.run([
                "docker", "exec", container_name, "cat", "/etc/rancher/k3s/k3s.yaml"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Failed to get kubeconfig from container {container_name}")
                return False
            
            # Parse kubeconfig
            kubeconfig = yaml.safe_load(result.stdout)
            
            # Update server URL to point to host
            host = cluster_config.get("host", "localhost")
            port = cluster_config.get("port", 6443)
            kubeconfig["clusters"][0]["cluster"]["server"] = f"https://{host}:{port}"
            
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
                yaml.dump(kubeconfig, f)
                temp_config_path = f.name
            
            # Load configuration
            config.load_kube_config(config_file=temp_config_path)
            
            # Clean up
            os.unlink(temp_config_path)
            
            self.current_cluster = cluster_config["name"]
            return True
            
        except Exception as e:
            print(f"Failed to load Docker K3s config: {e}")
            return False
    
    def _load_standard_kubeconfig(self, cluster_config: Dict[str, Any]) -> bool:
        """Load standard kubeconfig file."""
        try:
            kubeconfig_path = os.path.expanduser(cluster_config.get("kubeconfig_path", "~/.kube/config"))
            context = cluster_config.get("context")
            
            if context:
                config.load_kube_config(config_file=kubeconfig_path, context=context)
            else:
                config.load_kube_config(config_file=kubeconfig_path)
            
            self.current_cluster = cluster_config["name"]
            return True
            
        except Exception as e:
            print(f"Failed to load standard kubeconfig: {e}")
            return False
    
    def get_client(self, cluster_name: Optional[str] = None) -> client.CoreV1Api:
        """Get Kubernetes client for a specific cluster."""
        if not cluster_name:
            cluster_name = self.default_cluster
        
        if self.current_cluster != cluster_name:
            if not self.load_kubeconfig(cluster_name):
                raise Exception(f"Failed to load configuration for cluster {cluster_name}")
        
        return client.CoreV1Api()
    
    def get_apps_client(self, cluster_name: Optional[str] = None) -> client.AppsV1Api:
        """Get Kubernetes Apps client for a specific cluster."""
        if not cluster_name:
            cluster_name = self.default_cluster
        
        if self.current_cluster != cluster_name:
            if not self.load_kubeconfig(cluster_name):
                raise Exception(f"Failed to load configuration for cluster {cluster_name}")
        
        return client.AppsV1Api()
    
    def test_connection(self, cluster_name: Optional[str] = None) -> Dict[str, Any]:
        """Test connection to a Kubernetes cluster."""
        try:
            core_v1 = self.get_client(cluster_name)
            version = core_v1.get_api_resources()
            
            return {
                "success": True,
                "cluster": cluster_name or self.default_cluster,
                "message": "Connection successful",
                "api_resources_count": len(version.resources) if version.resources else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "cluster": cluster_name or self.default_cluster,
                "message": f"Connection failed: {str(e)}",
                "error": str(e)
            }
    
    def get_cluster_info(self, cluster_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a cluster."""
        try:
            core_v1 = self.get_client(cluster_name)
            
            # Get nodes
            nodes = core_v1.list_node()
            node_count = len(nodes.items) if nodes.items else 0
            
            # Get namespaces
            namespaces = core_v1.list_namespace()
            namespace_count = len(namespaces.items) if namespaces.items else 0
            
            # Get pods
            pods = core_v1.list_pod_for_all_namespaces()
            pod_count = len(pods.items) if pods.items else 0
            
            return {
                "cluster": cluster_name or self.default_cluster,
                "nodes": node_count,
                "namespaces": namespace_count,
                "pods": pod_count,
                "status": "connected"
            }
            
        except Exception as e:
            return {
                "cluster": cluster_name or self.default_cluster,
                "status": "error",
                "error": str(e)
            }


def get_k8s_config_manager() -> KubernetesConfigManager:
    """Get Kubernetes configuration manager instance."""
    from ai_admin.settings_manager import get_settings_manager
    settings_manager = get_settings_manager()
    config_data = settings_manager.get_all_settings()
    return KubernetesConfigManager(config_data)


def load_k8s_config(cluster_name: Optional[str] = None) -> bool:
    """Load Kubernetes configuration for a specific cluster."""
    config_manager = get_k8s_config_manager()
    return config_manager.load_kubeconfig(cluster_name)


def get_k8s_client(cluster_name: Optional[str] = None) -> client.CoreV1Api:
    """Get Kubernetes client for a specific cluster."""
    config_manager = get_k8s_config_manager()
    return config_manager.get_client(cluster_name)


def get_k8s_apps_client(cluster_name: Optional[str] = None) -> client.AppsV1Api:
    """Get Kubernetes Apps client for a specific cluster."""
    config_manager = get_k8s_config_manager()
    return config_manager.get_apps_client(cluster_name) 