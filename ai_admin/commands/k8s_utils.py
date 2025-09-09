"""Kubernetes utilities for managing cluster configurations."""

import os
import yaml
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from kubernetes import client, config
from kubernetes.client.rest import ApiException
import docker

from ai_admin.settings_manager import get_settings_manager


class KubernetesConfigManager:
    """Manager for Kubernetes cluster configurations."""
    
    def __init__(self, config_data: Dict[str, Any]):
        """Initialize config manager with settings."""
        self.config_data = config_data
        self.clusters = config_data.get("kubernetes_clusters", {})
        self.default_cluster = config_data.get("default_kubernetes_cluster", "default")
        self.current_cluster = None
        self.current_client = None
        self.docker_client = None
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            print(f"Warning: Failed to initialize Docker client: {e}")
            self.docker_client = None
    
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
            # First check if this is a cluster created by our cluster manager
            if self._is_managed_cluster(cluster_name):
                return self._load_managed_cluster_config(cluster_name)
            
            # Otherwise use standard configuration
            cluster_config = self.get_cluster_config(cluster_name)
            cluster_type = cluster_config.get("type", "k3s")
            
            if cluster_type == "docker_k3s":
                return self._load_docker_k3s_config(cluster_config)
            else:
                return self._load_standard_kubeconfig(cluster_config)
                
        except Exception as e:
            print(f"Failed to load kubeconfig for cluster {cluster_name}: {e}")
            return False
    
    def _is_managed_cluster(self, cluster_name: str) -> bool:
        """Check if cluster was created by our cluster manager."""
        clusters_dir = self.config_data.get("clusters_dir", "./kubeconfigs")
        kubeconfig_path = os.path.join(clusters_dir, cluster_name, "kubeconfig.yaml")
        return os.path.exists(kubeconfig_path)
    
    def _load_managed_cluster_config(self, cluster_name: str) -> bool:
        """Load kubeconfig for a cluster created by our cluster manager."""
        try:
            clusters_dir = self.config_data.get("clusters_dir", "./kubeconfigs")
            kubeconfig_path = os.path.join(clusters_dir, cluster_name, "kubeconfig.yaml")
            
            if not os.path.exists(kubeconfig_path):
                print(f"Kubeconfig not found for managed cluster: {kubeconfig_path}")
                return False
            
            # Load configuration from our managed cluster
            config.load_kube_config(config_file=kubeconfig_path)
            
            # Configure client certificates for authentication
            self._configure_client_certificates(cluster_name)
            
            self.current_cluster = cluster_name
            return True
            
        except Exception as e:
            print(f"Failed to load managed cluster config: {e}")
            return False
    
    def _configure_client_certificates(self, cluster_name: str):
        """Configure client certificates for Kubernetes API authentication."""
        try:
            # Get certificates directory from config
            certs_base_dir = self.config_data.get("certificates_dir", "./certificates")
            certs_dir = os.path.join(certs_base_dir, cluster_name)
            
            # Check if client certificates exist
            client_cert_path = os.path.join(certs_dir, "tls", "client-ca.crt")
            client_key_path = os.path.join(certs_dir, "tls", "client-ca.key")
            
            if not os.path.exists(client_cert_path) or not os.path.exists(client_key_path):
                print(f"Client certificates not found for cluster {cluster_name}")
                return
            
            # Configure Kubernetes client with client certificates
            configuration = client.Configuration()
            configuration.cert_file = client_cert_path
            configuration.key_file = client_key_path
            configuration.verify_ssl = True
            
            # Set the configuration for the client
            client.Configuration.set_default(configuration)
            
            print(f"Configured client certificates for cluster {cluster_name}")
            
        except Exception as e:
            print(f"Failed to configure client certificates: {e}")
    
    def _load_docker_k3s_config(self, cluster_config: Dict[str, Any]) -> bool:
        """Load kubeconfig from Docker K3s container using Docker Python SDK."""
        try:
            if not self.docker_client:
                print("Docker client not available, falling back to subprocess")
                return self._load_docker_k3s_config_subprocess(cluster_config)
            
            container_name = cluster_config.get("container_name", "k3s-server")
            
            # Get container using Docker Python SDK
            try:
                container = self.docker_client.containers.get(container_name)
            except docker.errors.NotFound:
                print(f"Container {container_name} not found")
                return False
            
            # Get kubeconfig from container
            try:
                result = container.exec_run("cat /etc/rancher/k3s/k3s.yaml")
                if result.exit_code != 0:
                    print(f"Failed to get kubeconfig from container {container_name}")
                    return False
                
                kubeconfig_content = result.output.decode('utf-8')
            except Exception as e:
                print(f"Failed to execute command in container: {e}")
                return False
            
            # Parse kubeconfig
            kubeconfig = yaml.safe_load(kubeconfig_content)
            
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
            
            # The kubeconfig already contains the CA certificate and client certificates
            # So SSL verification should work correctly with self-signed certificates
            
            # Clean up
            os.unlink(temp_config_path)
            
            self.current_cluster = cluster_config["name"]
            return True
            
        except Exception as e:
            print(f"Failed to load Docker K3s config: {e}")
            return False
    
    def _load_docker_k3s_config_subprocess(self, cluster_config: Dict[str, Any]) -> bool:
        """Fallback method using subprocess for Docker operations."""
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
            
            # The kubeconfig already contains the CA certificate and client certificates
            # So SSL verification should work correctly with self-signed certificates
            
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
        
        # Create client with current configuration
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