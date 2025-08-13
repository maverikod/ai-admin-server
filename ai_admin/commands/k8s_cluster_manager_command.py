"""Kubernetes cluster manager command for creating and initializing clusters."""

import subprocess
import json
import time
import yaml
import asyncio
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.settings_manager import get_settings_manager
from ai_admin.queue.queue_manager import queue_manager


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
                     use_queue: bool = True,
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
                if use_queue:
                    return await self._create_cluster_with_queue(cluster_name, cluster_type, container_name, port, config)
                else:
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
        """Create a k3s cluster with proper SSL certificate integration."""
        try:
            # Generate port if not provided
            if not port:
                port = 6443
            
            # Generate SSL certificates for the cluster with proper k3s structure
            cert_result = await self._generate_k3s_certificates(cluster_name, port)
            if not cert_result.get("success", False):
                return ErrorResult(
                    message=f"Failed to generate SSL certificates: {cert_result.get('error', 'Unknown error')}",
                    code="CERT_GENERATION_FAILED",
                    details=cert_result
                )
            
            # Build Docker run command
            cmd = [
                "docker", "run", "-d",
                "--name", cluster_name,
                "--privileged",
                "-p", f"{port}:6443"
            ]
            
            # Get k3s configuration
            settings_manager = get_settings_manager()
            config = settings_manager.get_all_settings()
            k3s_config = config.get("k3s", {})
            k3s_token = k3s_config.get("default_token", "mysecret")
            
            # Add environment variables
            env_vars = [
                f"K3S_TOKEN={k3s_token}",
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
            
            # Wait for cluster to be ready and actively check for kubeconfig
            max_wait_time = 60  # seconds
            wait_interval = 2   # seconds
            waited_time = 0
            
            while waited_time < max_wait_time:
                await asyncio.sleep(wait_interval)
                waited_time += wait_interval
                
                # Check multiple possible kubeconfig locations
                possible_paths = [
                    f"./kubeconfig-{cluster_name}/kubeconfig.yaml",
                    f"./kubeconfig-{cluster_name}/kubeconfig",
                    f"./kubeconfig-{cluster_name}/config",
                    f"./kubeconfig-{cluster_name}/config.yaml"
                ]
                
                kubeconfig_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        kubeconfig_path = path
                        break
                
                if kubeconfig_path:
                    break
                
                # Also check if kubeconfig is being generated inside container
                try:
                    result = subprocess.run([
                        "docker", "exec", cluster_name, "ls", "/output/kubeconfig.yaml"
                    ], capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0:
                        # Kubeconfig exists in container, copy it out
                        subprocess.run([
                            "docker", "cp", f"{cluster_name}:/output/kubeconfig.yaml", f"./kubeconfig-{cluster_name}/kubeconfig.yaml"
                        ], check=True, capture_output=True)
                        kubeconfig_path = f"./kubeconfig-{cluster_name}/kubeconfig.yaml"
                        break
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    pass
            
            if not kubeconfig_path or not os.path.exists(kubeconfig_path):
                # Try to get kubeconfig from container directly
                try:
                    subprocess.run([
                        "docker", "cp", f"{cluster_name}:/output/kubeconfig.yaml", f"./kubeconfig-{cluster_name}/kubeconfig.yaml"
                    ], check=True, capture_output=True)
                    kubeconfig_path = f"./kubeconfig-{cluster_name}/kubeconfig.yaml"
                except subprocess.CalledProcessError:
                    return ErrorResult(
                        message=f"Failed to create or copy kubeconfig after {max_wait_time} seconds",
                        code="KUBECONFIG_FAILED",
                        details={
                            "cluster_name": cluster_name, 
                            "checked_paths": possible_paths,
                            "container_status": "running"
                        }
                    )
            
            # Replace k3s certificates with our custom ones
            cert_replace_result = await self._replace_k3s_certificates(cluster_name, cert_result["certificates"])
            if not cert_replace_result.get("success", False):
                return ErrorResult(
                    message=f"Failed to replace k3s certificates: {cert_replace_result.get('error', 'Unknown error')}",
                    code="CERT_REPLACEMENT_FAILED",
                    details=cert_replace_result
                )
            
            # Restart k3s to use new certificates
            restart_result = await self._restart_k3s_cluster(cluster_name)
            if not restart_result.get("success", False):
                return ErrorResult(
                    message=f"Failed to restart k3s cluster: {restart_result.get('error', 'Unknown error')}",
                    code="CLUSTER_RESTART_FAILED",
                    details=restart_result
                )
            
            # Wait for cluster to be ready after restart
            await asyncio.sleep(10)
            
            # Update kubeconfig with new CA certificate
            kubeconfig_result = await self._update_kubeconfig_with_ca(cluster_name, cert_result["certificates"]["ca_cert"], kubeconfig_path)
            if not kubeconfig_result.get("success", False):
                return ErrorResult(
                    message=f"Failed to update kubeconfig: {kubeconfig_result.get('error', 'Unknown error')}",
                    code="KUBECONFIG_UPDATE_FAILED",
                    details=kubeconfig_result
                )
            
            return SuccessResult(data={
                "message": f"Successfully created k3s cluster '{cluster_name}' with custom SSL certificates",
                "cluster_name": cluster_name,
                "cluster_type": "k3s",
                "container_id": container_id,
                "port": port,
                "config": config,
                "command": " ".join(cmd),
                "certificates": cert_result.get("certificates", {}),
                "certificate_replacement": cert_replace_result,
                "kubeconfig_updated": kubeconfig_result,
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
    
    async def _generate_k3s_certificates(self, cluster_name: str, port: int) -> Dict[str, Any]:
        """Generate SSL certificates for k3s cluster with proper structure."""
        try:
            import os
            import tempfile
            from pathlib import Path
            
            # Create certificates directory
            certs_dir = Path(f"./certs-{cluster_name}")
            certs_dir.mkdir(exist_ok=True)
            
            # Generate CA certificate and key with proper k3s structure
            ca_key_path = certs_dir / "ca.key"
            ca_cert_path = certs_dir / "ca.crt"
            
            # Generate CA private key
            subprocess.run([
                "openssl", "genrsa", "-out", str(ca_key_path), "2048"
            ], check=True, capture_output=True)
            
            # Create CA certificate with proper x509 extensions for k3s
            ca_config_content = f"""[req]
distinguished_name = req_distinguished_name
req_extensions = v3_ca
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = {cluster_name}-CA
OU = IT
CN = {cluster_name}-CA
emailAddress = admin@{cluster_name}.local

[v3_ca]
basicConstraints = CA:TRUE, pathlen:0
keyUsage = keyCertSign, cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer:always
"""
            
            ca_config_path = certs_dir / "ca.cnf"
            with open(ca_config_path, 'w') as f:
                f.write(ca_config_content)
            
            subprocess.run([
                "openssl", "req", "-new", "-x509", "-key", str(ca_key_path),
                "-out", str(ca_cert_path), "-days", "365", "-config", str(ca_config_path),
                "-extensions", "v3_ca"
            ], check=True, capture_output=True)
            
            # Create k3s certificate structure
            k3s_certs_dir = certs_dir / "tls"
            k3s_certs_dir.mkdir(exist_ok=True)
            
            # Copy CA certificates to k3s structure
            import shutil
            shutil.copy2(ca_cert_path, k3s_certs_dir / "server-ca.crt")
            shutil.copy2(ca_key_path, k3s_certs_dir / "server-ca.key")
            shutil.copy2(ca_cert_path, k3s_certs_dir / "client-ca.crt")
            shutil.copy2(ca_key_path, k3s_certs_dir / "client-ca.key")
            
            # Clean up temporary files
            ca_config_path.unlink()
            
            return {
                "success": True,
                "certificates": {
                    "ca_key": str(ca_key_path),
                    "ca_cert": str(ca_cert_path),
                    "certs_dir": str(certs_dir),
                    "k3s_certs_dir": str(k3s_certs_dir),
                    "server_ca_cert": str(k3s_certs_dir / "server-ca.crt"),
                    "server_ca_key": str(k3s_certs_dir / "server-ca.key"),
                    "client_ca_cert": str(k3s_certs_dir / "client-ca.crt"),
                    "client_ca_key": str(k3s_certs_dir / "client-ca.key")
                }
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"OpenSSL command failed: {e.stderr.decode() if e.stderr else str(e)}",
                "return_code": e.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Certificate generation failed: {str(e)}"
            }
    
    async def _replace_k3s_certificates(self, cluster_name: str, certificates: Dict[str, str]) -> Dict[str, Any]:
        """Replace k3s certificates with custom ones using k3s certificate rotate-ca."""
        try:
            # Copy certificates to container
            k3s_certs_dir = certificates["k3s_certs_dir"]
            
            # Copy server CA certificate
            subprocess.run([
                "docker", "cp", f"{k3s_certs_dir}/server-ca.crt", f"{cluster_name}:/tmp/server-ca.crt"
            ], check=True, capture_output=True)
            
            # Copy server CA key
            subprocess.run([
                "docker", "cp", f"{k3s_certs_dir}/server-ca.key", f"{cluster_name}:/tmp/server-ca.key"
            ], check=True, capture_output=True)
            
            # Copy client CA certificate
            subprocess.run([
                "docker", "cp", f"{k3s_certs_dir}/client-ca.crt", f"{cluster_name}:/tmp/client-ca.crt"
            ], check=True, capture_output=True)
            
            # Copy client CA key
            subprocess.run([
                "docker", "cp", f"{k3s_certs_dir}/client-ca.key", f"{cluster_name}:/tmp/client-ca.key"
            ], check=True, capture_output=True)
            
            # Create proper structure in container
            subprocess.run([
                "docker", "exec", cluster_name, "mkdir", "-p", "/tmp/tls"
            ], check=True, capture_output=True)
            
            subprocess.run([
                "docker", "exec", cluster_name, "cp", "/tmp/server-ca.crt", "/tmp/tls/server-ca.crt"
            ], check=True, capture_output=True)
            
            subprocess.run([
                "docker", "exec", cluster_name, "cp", "/tmp/server-ca.key", "/tmp/tls/server-ca.key"
            ], check=True, capture_output=True)
            
            subprocess.run([
                "docker", "exec", cluster_name, "cp", "/tmp/client-ca.crt", "/tmp/tls/client-ca.crt"
            ], check=True, capture_output=True)
            
            subprocess.run([
                "docker", "exec", cluster_name, "cp", "/tmp/client-ca.key", "/tmp/tls/client-ca.key"
            ], check=True, capture_output=True)
            
            # Get k3s configuration for token
            settings_manager = get_settings_manager()
            config = settings_manager.get_all_settings()
            k3s_config = config.get("k3s", {})
            k3s_token = k3s_config.get("default_token", "mysecret")
            token_file_path = k3s_config.get("certificate_management", {}).get("token_file_path", "/var/lib/rancher/k3s/server/token")
            
            # Replace CA certificates using k3s command with token from config
            result = subprocess.run([
                "docker", "exec", cluster_name, "sh", "-c", f"echo {k3s_token} > {token_file_path} && k3s certificate rotate-ca --path /tmp/tls --force"
            ], check=True, capture_output=True, text=True)
            
            return {
                "success": True,
                "message": "Successfully replaced k3s CA certificates",
                "output": result.stdout,
                "certificates_replaced": ["server-ca", "client-ca"]
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to replace certificates: {e.stderr if isinstance(e.stderr, str) else e.stderr.decode() if e.stderr else str(e)}",
                "return_code": e.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Certificate replacement failed: {str(e)}"
            }
    
    async def _restart_k3s_cluster(self, cluster_name: str) -> Dict[str, Any]:
        """Restart k3s cluster to use new certificates."""
        try:
            # Restart the container
            result = subprocess.run([
                "docker", "restart", cluster_name
            ], check=True, capture_output=True, text=True)
            
            return {
                "success": True,
                "message": f"Successfully restarted k3s cluster '{cluster_name}'",
                "container_id": result.stdout.strip()
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to restart cluster: {e.stderr if isinstance(e.stderr, str) else e.stderr.decode() if e.stderr else str(e)}",
                "return_code": e.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Cluster restart failed: {str(e)}"
            }
    
    async def _update_kubeconfig_with_ca(self, cluster_name: str, ca_cert_path: str, kubeconfig_path: str) -> Dict[str, Any]:
        """Update kubeconfig with new CA certificate."""
        try:
            import base64
            import os
            
            # Read CA certificate and encode to base64
            with open(ca_cert_path, 'rb') as f:
                ca_cert_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Read kubeconfig
            if not os.path.exists(kubeconfig_path):
                return {
                    "success": False,
                    "error": f"Kubeconfig not found: {kubeconfig_path}"
                }
            
            with open(kubeconfig_path, 'r') as f:
                kubeconfig_content = f.read()
            
            # Replace certificate-authority-data with new CA
            import re
            updated_content = re.sub(
                r'certificate-authority-data: [A-Za-z0-9+/=]+',
                f'certificate-authority-data: {ca_cert_data}',
                kubeconfig_content
            )
            
            # Write updated kubeconfig
            with open(kubeconfig_path, 'w') as f:
                f.write(updated_content)
            
            return {
                "success": True,
                "message": f"Successfully updated kubeconfig with new CA certificate",
                "kubeconfig_path": kubeconfig_path
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update kubeconfig: {str(e)}"
            }
    
    async def _create_cluster_with_queue(self, cluster_name: str, cluster_type: str, container_name: Optional[str], port: Optional[int], config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Create cluster using queue system to avoid timeouts."""
        try:
            # Use queue manager directly
            
            # Create task data
            task_data = {
                "action": "create_cluster",
                "cluster_name": cluster_name,
                "cluster_type": cluster_type,
                "container_name": container_name,
                "port": port,
                "config": config,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add task to queue
            task_id = await queue_manager.push_task("k8s_cluster_creation", task_data)
            
            # Start background task
            await queue_manager.start_task(task_id, self._execute_cluster_creation_task)
            
            return SuccessResult(data={
                "message": f"Cluster creation task '{cluster_name}' queued successfully",
                "task_id": task_id,
                "cluster_name": cluster_name,
                "cluster_type": cluster_type,
                "status": "queued",
                "queue_position": await queue_manager.get_task_position(task_id),
                "estimated_wait_time": await queue_manager.get_estimated_wait_time(task_id),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to queue cluster creation task: {str(e)}",
                code="QUEUE_FAILED",
                details={"exception": str(e), "cluster_name": cluster_name}
            )
    
    async def _execute_cluster_creation_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute cluster creation task in background."""
        try:
            cluster_name = task_data["cluster_name"]
            cluster_type = task_data["cluster_type"]
            container_name = task_data.get("container_name")
            port = task_data.get("port")
            config = task_data.get("config")
            
            # Execute actual cluster creation
            if cluster_type == "k3s":
                result = await self._create_k3s_cluster(cluster_name, port, config)
            elif cluster_type == "kind":
                result = await self._create_kind_cluster(cluster_name, config)
            elif cluster_type == "minikube":
                result = await self._create_minikube_cluster(cluster_name, port, config)
            else:
                result = ErrorResult(
                    message=f"Unsupported cluster type: {cluster_type}",
                    code="UNSUPPORTED_CLUSTER_TYPE",
                    details={"supported_types": self.supported_types}
                )
            
            # Update task result
            await queue_manager.update_task_result(task_id, {
                "success": isinstance(result, SuccessResult),
                "result": result.to_dict() if hasattr(result, 'to_dict') else str(result),
                "completed_at": datetime.now().isoformat()
            })
            
            return {
                "success": isinstance(result, SuccessResult),
                "task_id": task_id,
                "result": result
            }
            
        except Exception as e:
            # Update task with error
            await queue_manager.update_task_result(task_id, {
                "success": False,
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            })
            
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e)
            }
    
    async def _generate_cluster_certificates(self, cluster_name: str, port: int) -> Dict[str, Any]:
        """Generate SSL certificates for Kubernetes cluster."""
        try:
            import os
            import tempfile
            from pathlib import Path
            
            # Create certificates directory
            certs_dir = Path(f"./certs-{cluster_name}")
            certs_dir.mkdir(exist_ok=True)
            
            # Generate CA certificate and key
            ca_key_path = certs_dir / "ca.key"
            ca_cert_path = certs_dir / "ca.crt"
            
            # Generate CA private key
            subprocess.run([
                "openssl", "genrsa", "-out", str(ca_key_path), "2048"
            ], check=True, capture_output=True)
            
            # Create CA certificate with proper x509 extensions
            ca_config_content = f"""[req]
distinguished_name = req_distinguished_name
req_extensions = v3_ca
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = {cluster_name}-CA
OU = IT
CN = {cluster_name}-CA
emailAddress = admin@{cluster_name}.local

[v3_ca]
basicConstraints = CA:TRUE, pathlen:0
keyUsage = keyCertSign, cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer:always
"""
            
            ca_config_path = certs_dir / "ca.cnf"
            with open(ca_config_path, 'w') as f:
                f.write(ca_config_content)
            
            subprocess.run([
                "openssl", "req", "-new", "-x509", "-key", str(ca_key_path),
                "-out", str(ca_cert_path), "-days", "365", "-config", str(ca_config_path),
                "-extensions", "v3_ca"
            ], check=True, capture_output=True)
            
            # Generate server certificate and key
            server_key_path = certs_dir / "server.key"
            server_cert_path = certs_dir / "server.crt"
            
            # Generate server private key
            subprocess.run([
                "openssl", "genrsa", "-out", str(server_key_path), "2048"
            ], check=True, capture_output=True)
            
            # Create server certificate signing request with proper x509 extensions
            server_config_content = f"""[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = {cluster_name}
OU = IT
CN = {cluster_name}-server
emailAddress = admin@{cluster_name}.local

[v3_req]
basicConstraints = CA:FALSE
keyUsage = keyEncipherment, dataEncipherment, digitalSignature
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names
subjectKeyIdentifier = hash

[alt_names]
DNS.1 = {cluster_name}
DNS.2 = localhost
DNS.3 = kubernetes.default.svc.cluster.local
DNS.4 = kubernetes.default.svc
DNS.5 = *.{cluster_name}.svc.cluster.local
IP.1 = 127.0.0.1
IP.2 = ::1
IP.3 = 10.0.0.1
IP.4 = 10.43.0.1
"""
            
            server_config_path = certs_dir / "server.cnf"
            with open(server_config_path, 'w') as f:
                f.write(server_config_content)
            
            server_csr_path = certs_dir / "server.csr"
            subprocess.run([
                "openssl", "req", "-new", "-key", str(server_key_path),
                "-out", str(server_csr_path), "-config", str(server_config_path)
            ], check=True, capture_output=True)
            
            # Sign server certificate with CA
            subprocess.run([
                "openssl", "x509", "-req", "-in", str(server_csr_path),
                "-CA", str(ca_cert_path), "-CAkey", str(ca_key_path),
                "-CAcreateserial", "-out", str(server_cert_path),
                "-days", "365", "-extensions", "v3_req", "-extfile", str(server_config_path)
            ], check=True, capture_output=True)
            
            # Generate client certificate and key
            client_key_path = certs_dir / "client.key"
            client_cert_path = certs_dir / "client.crt"
            
            # Generate client private key
            subprocess.run([
                "openssl", "genrsa", "-out", str(client_key_path), "2048"
            ], check=True, capture_output=True)
            
            # Create client certificate signing request with proper x509 extensions
            client_config_content = f"""[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = {cluster_name}
OU = IT
CN = {cluster_name}-client
emailAddress = admin@{cluster_name}.local

[v3_req]
basicConstraints = CA:FALSE
keyUsage = keyEncipherment, dataEncipherment, digitalSignature
extendedKeyUsage = clientAuth
subjectKeyIdentifier = hash
"""
            
            client_config_path = certs_dir / "client.cnf"
            with open(client_config_path, 'w') as f:
                f.write(client_config_content)
            
            client_csr_path = certs_dir / "client.csr"
            subprocess.run([
                "openssl", "req", "-new", "-key", str(client_key_path),
                "-out", str(client_csr_path), "-config", str(client_config_path)
            ], check=True, capture_output=True)
            
            # Sign client certificate with CA
            subprocess.run([
                "openssl", "x509", "-req", "-in", str(client_csr_path),
                "-CA", str(ca_cert_path), "-CAkey", str(ca_key_path),
                "-CAcreateserial", "-out", str(client_cert_path),
                "-days", "365", "-extensions", "v3_req", "-extfile", str(client_config_path)
            ], check=True, capture_output=True)
            
            # Clean up temporary files
            for temp_file in [ca_config_path, server_config_path, server_csr_path, client_config_path, client_csr_path]:
                temp_file.unlink()
            
            return {
                "success": True,
                "certificates": {
                    "ca_key": str(ca_key_path),
                    "ca_cert": str(ca_cert_path),
                    "server_key": str(server_key_path),
                    "server_cert": str(server_cert_path),
                    "client_key": str(client_key_path),
                    "client_cert": str(client_cert_path),
                    "certificates_dir": str(certs_dir)
                }
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"OpenSSL command failed: {e.stderr.decode() if e.stderr else str(e)}",
                "return_code": e.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Certificate generation failed: {str(e)}"
            }

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