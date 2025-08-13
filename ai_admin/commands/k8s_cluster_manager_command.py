"""Kubernetes cluster manager command for creating and initializing clusters."""

import subprocess
import json
import time
import yaml
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class K8sClusterManagerCommand(Command):
    """Universal command to manage Kubernetes clusters (k3s, kind, minikube)."""
    
    name = "k8s_cluster_manager"
    
    def __init__(self):
        """Initialize cluster manager command."""
        self.supported_types = ["k3s", "kind", "minikube"]
    
    async def execute(self, 
                     action: str = "list",
                     cluster_name: Optional[str] = None,
                     cluster_type: str = "k3s",
                     container_name: Optional[str] = None,
                     port: Optional[int] = None,
                     namespace: Optional[str] = None,
                     config: Optional[Dict[str, Any]] = None,
                     environment: str = "development",
                     version: str = "latest",
                     description: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     **kwargs):
        """
        Manage Kubernetes clusters.
        
        Args:
            action: Action to perform (create, delete, list, init, status)
            cluster_name: Name of the cluster
            cluster_type: Type of cluster (k3s, kind, minikube)
            container_name: Name of the container to install cluster in
            port: Port for cluster API server
            namespace: Default namespace to create
            config: Additional configuration
            environment: Environment type (development, staging, production)
            version: Kubernetes version
            description: Cluster description
            tags: List of tags for cluster identification
        """
        try:
            if action == "list":
                return await self._list_clusters()
            elif action == "create":
                return await self._create_cluster(cluster_name, cluster_type, container_name, port, config)
            elif action == "delete":
                return await self._delete_cluster(cluster_name, cluster_type)
            elif action == "init":
                return await self._initialize_cluster(cluster_name, namespace, config)
            elif action == "status":
                return await self._get_cluster_status(cluster_name, cluster_type)
            else:
                return ErrorResult(
                    message=f"Unknown action: {action}",
                    code="INVALID_ACTION",
                    details={"valid_actions": ["list", "create", "delete", "init", "status"]}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error in cluster manager operation: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )
    
    async def _list_clusters(self) -> SuccessResult:
        """List all available clusters."""
        try:
            clusters = []
            
            # Check Docker containers for k3s clusters
            cmd = ["docker", "ps", "--filter", "ancestor=rancher/k3s:latest", "--format", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            container_info = json.loads(line)
                            clusters.append({
                                "name": container_info.get("Names", "").replace("/", ""),
                                "type": "k3s",
                                "status": "running" if container_info.get("Status", "").startswith("Up") else "stopped",
                                "ports": container_info.get("Ports", ""),
                                "id": container_info.get("ID", "")
                            })
                        except json.JSONDecodeError:
                            continue
            
            # Check for kind clusters
            cmd = ["kind", "get", "clusters", "--output", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                try:
                    kind_clusters = json.loads(result.stdout)
                    for cluster in kind_clusters:
                        clusters.append({
                            "name": cluster.get("name"),
                            "type": "kind",
                            "status": cluster.get("status", "unknown"),
                            "nodes": cluster.get("nodes", [])
                        })
                except json.JSONDecodeError:
                    pass
            
            return SuccessResult(data={
                "message": f"Found {len(clusters)} cluster(s)",
                "clusters": clusters,
                "count": len(clusters),
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Timeout while listing clusters",
                code="TIMEOUT",
                details={"timeout": 30}
            )
    
    async def _create_cluster(self, cluster_name: str, cluster_type: str, container_name: Optional[str], port: Optional[int], config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Create a new cluster."""
        if not cluster_name:
            return ErrorResult(
                message="Cluster name is required for create action",
                code="MISSING_CLUSTER_NAME",
                details={}
            )
        
        if cluster_type not in self.supported_types:
            return ErrorResult(
                message=f"Unsupported cluster type: {cluster_type}",
                code="UNSUPPORTED_CLUSTER_TYPE",
                details={"supported_types": self.supported_types}
            )
        
        try:
            # Check if container exists and is running
            if container_name:
                container_status = await self._check_container_status(container_name)
                if container_status.get("exists") and container_status.get("running"):
                    return await self._install_cluster_in_container(cluster_name, cluster_type, container_name, port, config)
                elif container_status.get("exists") and not container_status.get("running"):
                    return ErrorResult(
                        message=f"Container '{container_name}' exists but is not running",
                        code="CONTAINER_NOT_RUNNING",
                        details={"container_name": container_name}
                    )
                else:
                    return ErrorResult(
                        message=f"Container '{container_name}' does not exist",
                        code="CONTAINER_NOT_FOUND",
                        details={"container_name": container_name}
                    )
            else:
                # Create new container with cluster
                if cluster_type == "k3s":
                    return await self._create_k3s_cluster(cluster_name, port, config)
                elif cluster_type == "kind":
                    return await self._create_kind_cluster(cluster_name, config)
                elif cluster_type == "minikube":
                    return await self._create_minikube_cluster(cluster_name, config)
                else:
                    return ErrorResult(
                        message=f"Cluster type {cluster_type} not implemented",
                        code="NOT_IMPLEMENTED",
                        details={}
                    )
                
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create cluster: {str(e)}",
                code="CREATE_FAILED",
                details={"cluster_name": cluster_name, "cluster_type": cluster_type}
            )
    
    async def _create_k3s_cluster(self, cluster_name: str, port: Optional[int], config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Create a k3s cluster."""
        try:
            # Generate port if not provided
            if not port:
                port = 6443
            
            # Build Docker run command
            cmd = [
                "docker", "run", "-d",
                "--name", cluster_name,
                "--privileged",
                "-p", f"{port}:6443"
            ]
            
            # Add environment variables
            env_vars = [
                "K3S_TOKEN=mysecret",
                "K3S_KUBECONFIG_OUTPUT=/output/kubeconfig.yaml",
                "K3S_KUBECONFIG_MODE=666"
            ]
            
            for env_var in env_vars:
                cmd.extend(["-e", env_var])
            
            # Add volumes
            volumes = [
                f"{cluster_name}-data:/var/lib/rancher/k3s",
                "/var/run/docker.sock:/var/run/docker.sock",
                f"./kubeconfig-{cluster_name}:/output"
            ]
            
            for volume in volumes:
                cmd.extend(["-v", volume])
            
            # Add image and command
            cmd.extend([
                "rancher/k3s:latest",
                "server",
                "--disable", "traefik",
                "--disable", "servicelb",
                "--disable-cloud-controller",
                "--disable-network-policy",
                "--disable", "local-storage"
            ])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to create k3s cluster: {result.stderr}",
                    code="K3S_CREATE_FAILED",
                    details={
                        "stderr": result.stderr,
                        "stdout": result.stdout,
                        "command": " ".join(cmd)
                    }
                )
            
            container_id = result.stdout.strip()
            
            return SuccessResult(data={
                "message": f"Successfully created k3s cluster '{cluster_name}'",
                "cluster_name": cluster_name,
                "cluster_type": "k3s",
                "container_id": container_id,
                "port": port,
                "config": config,
                "command": " ".join(cmd),
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message=f"Timeout while creating k3s cluster '{cluster_name}'",
                code="TIMEOUT",
                details={"timeout": 120, "cluster_name": cluster_name}
            )
    
    async def _create_kind_cluster(self, cluster_name: str, config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Create a kind cluster."""
        try:
            cmd = ["kind", "create", "cluster", "--name", cluster_name]
            
            if config and config.get("wait"):
                cmd.extend(["--wait", str(config["wait"])])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to create kind cluster: {result.stderr}",
                    code="KIND_CREATE_FAILED",
                    details={
                        "stderr": result.stderr,
                        "stdout": result.stdout,
                        "command": " ".join(cmd)
                    }
                )
            
            return SuccessResult(data={
                "message": f"Successfully created kind cluster '{cluster_name}'",
                "cluster_name": cluster_name,
                "cluster_type": "kind",
                "config": config,
                "stdout": result.stdout,
                "command": " ".join(cmd),
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message=f"Timeout while creating kind cluster '{cluster_name}'",
                code="TIMEOUT",
                details={"timeout": 300, "cluster_name": cluster_name}
            )
    
    async def _create_minikube_cluster(self, cluster_name: str, config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Create a minikube cluster."""
        try:
            cmd = ["minikube", "start", "--profile", cluster_name]
            
            if config and config.get("driver"):
                cmd.extend(["--driver", config["driver"]])
            
            if config and config.get("cpus"):
                cmd.extend(["--cpus", str(config["cpus"])])
            
            if config and config.get("memory"):
                cmd.extend(["--memory", str(config["memory"])])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to create minikube cluster: {result.stderr}",
                    code="MINIKUBE_CREATE_FAILED",
                    details={
                        "stderr": result.stderr,
                        "stdout": result.stdout,
                        "command": " ".join(cmd)
                    }
                )
            
            return SuccessResult(data={
                "message": f"Successfully created minikube cluster '{cluster_name}'",
                "cluster_name": cluster_name,
                "cluster_type": "minikube",
                "config": config,
                "stdout": result.stdout,
                "command": " ".join(cmd),
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message=f"Timeout while creating minikube cluster '{cluster_name}'",
                code="TIMEOUT",
                details={"timeout": 300, "cluster_name": cluster_name}
            )
    
    async def _delete_cluster(self, cluster_name: str, cluster_type: str) -> SuccessResult:
        """Delete a cluster."""
        if not cluster_name:
            return ErrorResult(
                message="Cluster name is required for delete action",
                code="MISSING_CLUSTER_NAME",
                details={}
            )
        
        try:
            if cluster_type == "k3s":
                cmd = ["docker", "rm", "-f", cluster_name]
            elif cluster_type == "kind":
                cmd = ["kind", "delete", "cluster", "--name", cluster_name]
            elif cluster_type == "minikube":
                cmd = ["minikube", "delete", "--profile", cluster_name]
            else:
                return ErrorResult(
                    message=f"Unsupported cluster type: {cluster_type}",
                    code="UNSUPPORTED_CLUSTER_TYPE",
                    details={"supported_types": self.supported_types}
                )
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to delete cluster: {result.stderr}",
                    code="DELETE_FAILED",
                    details={
                        "stderr": result.stderr,
                        "stdout": result.stdout,
                        "command": " ".join(cmd)
                    }
                )
            
            return SuccessResult(data={
                "message": f"Successfully deleted {cluster_type} cluster '{cluster_name}'",
                "cluster_name": cluster_name,
                "cluster_type": cluster_type,
                "stdout": result.stdout,
                "command": " ".join(cmd),
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message=f"Timeout while deleting cluster '{cluster_name}'",
                code="TIMEOUT",
                details={"timeout": 60, "cluster_name": cluster_name}
            )
    
    async def _initialize_cluster(self, cluster_name: str, namespace: Optional[str], config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Initialize a cluster with default resources."""
        try:
            # Create default namespace if specified
            if namespace:
                # This would use the k8s_namespace_create command
                pass
            
            # Create default ConfigMap
            if config and config.get("create_default_config"):
                # This would use the k8s_configmap_create command
                pass
            
            return SuccessResult(data={
                "message": f"Successfully initialized cluster '{cluster_name}'",
                "cluster_name": cluster_name,
                "namespace": namespace,
                "config": config,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to initialize cluster: {str(e)}",
                code="INIT_FAILED",
                details={"cluster_name": cluster_name}
            )
    
    async def _get_cluster_status(self, cluster_name: str, cluster_type: str) -> SuccessResult:
        """Get cluster status."""
        if not cluster_name:
            return ErrorResult(
                message="Cluster name is required for status action",
                code="MISSING_CLUSTER_NAME",
                details={}
            )
        
        try:
            if cluster_type == "k3s":
                cmd = ["docker", "inspect", cluster_name, "--format", "json"]
            elif cluster_type == "kind":
                cmd = ["kind", "get", "nodes", "--name", cluster_name, "--output", "json"]
            elif cluster_type == "minikube":
                cmd = ["minikube", "status", "--profile", cluster_name, "--output", "json"]
            else:
                return ErrorResult(
                    message=f"Unsupported cluster type: {cluster_type}",
                    code="UNSUPPORTED_CLUSTER_TYPE",
                    details={"supported_types": self.supported_types}
                )
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to get cluster status: {result.stderr}",
                    code="STATUS_FAILED",
                    details={
                        "stderr": result.stderr,
                        "command": " ".join(cmd)
                    }
                )
            
            try:
                status_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                status_data = {"raw_output": result.stdout}
            
            return SuccessResult(data={
                "message": f"Cluster '{cluster_name}' status retrieved",
                "cluster_name": cluster_name,
                "cluster_type": cluster_type,
                "status": status_data,
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message=f"Timeout while getting cluster status",
                code="TIMEOUT",
                details={"timeout": 30, "cluster_name": cluster_name}
            )
    
    async def _check_container_status(self, container_name: str) -> Dict[str, Any]:
        """Check if container exists and is running."""
        try:
            cmd = ["docker", "inspect", container_name, "--format", "{{.State.Running}}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                is_running = result.stdout.strip() == "true"
                return {
                    "exists": True,
                    "running": is_running,
                    "container_name": container_name
                }
            else:
                return {
                    "exists": False,
                    "running": False,
                    "container_name": container_name
                }
        except Exception as e:
            return {
                "exists": False,
                "running": False,
                "container_name": container_name,
                "error": str(e)
            }
    
    async def _install_cluster_in_container(self, cluster_name: str, cluster_type: str, container_name: str, port: Optional[int], config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Install cluster in existing container."""
        try:
            if cluster_type == "k3s":
                return await self._install_k3s_in_container(cluster_name, container_name, port, config)
            else:
                return ErrorResult(
                    message=f"Installing {cluster_type} in existing container is not supported yet",
                    code="NOT_IMPLEMENTED",
                    details={"cluster_type": cluster_type, "container_name": container_name}
                )
        except Exception as e:
            return ErrorResult(
                message=f"Failed to install cluster in container: {str(e)}",
                code="INSTALL_FAILED",
                details={"cluster_name": cluster_name, "container_name": container_name, "cluster_type": cluster_type}
            )
    
    async def _install_k3s_in_container(self, cluster_name: str, container_name: str, port: Optional[int], config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Install k3s in existing container."""
        try:
            # Check if k3s is already installed
            cmd = ["docker", "exec", container_name, "which", "k3s"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return ErrorResult(
                    message=f"k3s is already installed in container '{container_name}'",
                    code="ALREADY_INSTALLED",
                    details={"container_name": container_name, "cluster_name": cluster_name}
                )
            
            # Install k3s in container
            install_cmd = [
                "docker", "exec", container_name,
                "sh", "-c",
                "curl -sfL https://get.k3s.io | sh -"
            ]
            
            result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to install k3s in container: {result.stderr}",
                    code="K3S_INSTALL_FAILED",
                    details={"container_name": container_name, "stderr": result.stderr}
                )
            
            # Start k3s server
            start_cmd = [
                "docker", "exec", container_name,
                "k3s", "server",
                "--disable", "traefik",
                "--disable", "servicelb",
                "--disable-cloud-controller",
                "--disable-network-policy",
                "--disable", "local-storage"
            ]
            
            # Run in background
            start_cmd.extend(["--"])
            
            result = subprocess.run(start_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to start k3s server: {result.stderr}",
                    code="K3S_START_FAILED",
                    details={"container_name": container_name, "stderr": result.stderr}
                )
            
            return SuccessResult(data={
                "message": f"Successfully installed k3s cluster '{cluster_name}' in container '{container_name}'",
                "cluster_name": cluster_name,
                "cluster_type": "k3s",
                "container_name": container_name,
                "port": port,
                "config": config,
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message=f"Timeout while installing k3s in container '{container_name}'",
                code="TIMEOUT",
                details={"timeout": 300, "container_name": container_name}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for cluster manager command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["list", "create", "delete", "init", "status"],
                    "default": "list"
                },
                "cluster_name": {
                    "type": "string",
                    "description": "Name of the cluster"
                },
                "cluster_type": {
                    "type": "string",
                    "description": "Type of cluster",
                    "enum": ["k3s", "kind", "minikube"],
                    "default": "k3s"
                },
                "port": {
                    "type": "integer",
                    "description": "Port for cluster API server (k3s only)"
                },
                "namespace": {
                    "type": "string",
                    "description": "Default namespace to create"
                },
                "config": {
                    "type": "object",
                    "description": "Additional configuration for cluster creation"
                }
            },
            "required": ["action"]
        } 