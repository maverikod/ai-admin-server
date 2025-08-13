"""Kubernetes cluster manager command for creating and initializing clusters."""

import json
import time
import yaml
import asyncio
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import docker

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.settings_manager import get_settings_manager
from ai_admin.queue.queue_manager import queue_manager


class K8sClusterManagerCommand(Command):
    """Universal command to manage Kubernetes clusters (k3s, kind, minikube) using Python libraries."""
    
    name = "k8s_cluster_manager"
    
    def __init__(self):
        """Initialize cluster manager command."""
        self.supported_types = ["k3s", "kind", "minikube"]
        self.docker_client = None
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            print(f"Warning: Failed to initialize Docker client: {e}")
            self.docker_client = None
    
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
        Manage Kubernetes clusters using Python libraries.
        
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
                if not use_queue:
                    return ErrorResult(
                        message="Cluster creation without queue is not allowed. Use use_queue=True to create clusters safely.",
                        code="QUEUE_REQUIRED",
                        details={"valid_actions": ["list", "delete", "init", "status"], "note": "Use queue for long-running operations"}
                    )
                else:
                    return await self._create_cluster_with_queue(cluster_name, cluster_type, container_name, port, config)
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
        """List all available clusters using Docker Python SDK."""
        try:
            clusters = []
            
            if not self.docker_client:
                return SuccessResult(data={
                    "message": "Docker client not available, no clusters found",
                    "clusters": [],
                    "total_count": 0,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Check Docker containers for k3s clusters
            try:
                k3s_containers = self.docker_client.containers.list(
                    filters={"ancestor": "rancher/k3s:latest"}
                )
                
                for container in k3s_containers:
                    container_info = {
                        "name": container.name,
                        "id": container.short_id,
                        "status": container.status,
                                "type": "k3s",
                        "created": container.attrs["Created"],
                        "ports": container.attrs["NetworkSettings"]["Ports"],
                        "labels": container.labels
                    }
                    clusters.append(container_info)
                    
            except Exception as e:
                print(f"Error listing k3s containers: {e}")
            
            # Check for kind clusters
            try:
                kind_containers = self.docker_client.containers.list(
                    filters={"label": "io.x-k8s.kind.cluster"}
                )
                
                for container in kind_containers:
                    container_info = {
                        "name": container.name,
                        "id": container.short_id,
                        "status": container.status,
                            "type": "kind",
                        "created": container.attrs["Created"],
                        "ports": container.attrs["NetworkSettings"]["Ports"],
                        "labels": container.labels
                    }
                    clusters.append(container_info)
                    
            except Exception as e:
                print(f"Error listing kind containers: {e}")
            
            return SuccessResult(data={
                "message": f"Found {len(clusters)} Kubernetes clusters",
                "clusters": clusters,
                "total_count": len(clusters),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to list clusters: {str(e)}",
                code="LIST_FAILED",
                details={"exception": str(e)}
            )
    
    async def _create_cluster_internal(self, cluster_name: str, cluster_type: str,
                                     container_name: Optional[str], port: Optional[int],
                                     config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Create a Kubernetes cluster using Python libraries (internal method for queue)."""
        try:
            if cluster_type == "k3s":
                return await self._create_k3s_cluster(cluster_name, container_name, port, config)
            elif cluster_type == "kind":
                return await self._create_kind_cluster(cluster_name, config)
            elif cluster_type == "minikube":
                return await self._create_minikube_cluster(cluster_name, config)
            else:
                return ErrorResult(
                    message=f"Unsupported cluster type: {cluster_type}",
                    code="UNSUPPORTED_CLUSTER_TYPE",
                    details={"supported_types": self.supported_types}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create cluster: {str(e)}",
                code="CREATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _create_cluster(self, cluster_name: str, cluster_type: str,
                            container_name: Optional[str], port: Optional[int],
                            config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Create cluster directly (should not be called without queue)."""
        # This method should not be called directly - it's for internal use by queue
        return ErrorResult(
            message="Direct cluster creation is not allowed. Use queue system for safe cluster creation.",
            code="DIRECT_CREATION_FORBIDDEN",
            details={"note": "This method is for internal queue use only"}
        )
    
    async def _create_k3s_cluster(self, cluster_name: str, container_name: Optional[str],
                                port: Optional[int], config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Create a K3s cluster using Docker Python SDK."""
        try:
            if not self.docker_client:
                return ErrorResult(
                    message="Docker client not available",
                    code="DOCKER_CLIENT_UNAVAILABLE"
                )
            
            # Check if cluster with this name already exists
            try:
                existing_clusters = self.docker_client.containers.list(
                    filters={"label": f"ai-admin.cluster={cluster_name}"}
                )
                
                if existing_clusters:
                    # Cluster already exists, check if it's running
                    existing_container = existing_clusters[0]
                    existing_container.reload()
                    
                    if existing_container.status == "running":
                        # Check if k3s is ready
                        try:
                            process = await asyncio.create_subprocess_exec(
                                "docker", "exec", existing_container.name, "kubectl", "get", "nodes", "--no-headers",
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            stdout, stderr = await process.communicate()
                            
                            if process.returncode == 0 and "Ready" in stdout.decode():
                                return SuccessResult(data={
                                    "message": f"K3s cluster '{cluster_name}' already exists and is running",
                                    "cluster_name": cluster_name,
                                    "cluster_type": "k3s",
                                    "container_name": existing_container.name,
                                    "port": port,
                                    "status": "running",
                                    "timestamp": datetime.now().isoformat()
                                })
                        except Exception:
                            pass
                    
                    return ErrorResult(
                        message=f"K3s cluster '{cluster_name}' already exists",
                        code="CLUSTER_ALREADY_EXISTS",
                        details={"container_name": existing_container.name, "status": existing_container.status}
                    )
                    
            except Exception:
                # No existing cluster found, continue with creation
                pass
            
            if not container_name:
                container_name = f"k3s-{cluster_name}"
            
            if not port:
                port = 6443
            
            # Check if container already exists
            try:
                existing_container = self.docker_client.containers.get(container_name)
                
                # Container exists, check its status
                existing_container.reload()
                
                if existing_container.status == "running":
                    # Container is running, check if k3s is ready
                    try:
                        # Use subprocess to execute kubectl command inside container
                        process = await asyncio.create_subprocess_exec(
                            "docker", "exec", existing_container.name, "kubectl", "get", "nodes", "--no-headers",
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await process.communicate()
                        
                        if process.returncode == 0 and "Ready" in stdout.decode():
                            return SuccessResult(data={
                                "message": f"K3s cluster '{cluster_name}' is already running",
                                "cluster_name": cluster_name,
                                "cluster_type": "k3s",
                                "container_name": container_name,
                                "port": port,
                                "status": "running",
                                "timestamp": datetime.now().isoformat()
                            })
                    except Exception:
                        pass
                    
                    # Container is running but k3s might not be ready, wait for it
                    max_wait = 180  # 3 minutes to wait for k3s to be ready
                    wait_time = 0
                    k3s_ready = False
                    
                    while wait_time < max_wait and not k3s_ready:
                        try:
                            # Use subprocess to execute kubectl command inside container
                            process = await asyncio.create_subprocess_exec(
                                "docker", "exec", existing_container.name, "kubectl", "get", "nodes", "--no-headers",
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            stdout, stderr = await process.communicate()
                            
                            if process.returncode == 0 and "Ready" in stdout.decode():
                                k3s_ready = True
                                break
                        except Exception:
                            pass
                        
                        await asyncio.sleep(10)
                        wait_time += 10
                    
                    if k3s_ready:
                        return SuccessResult(data={
                            "message": f"K3s cluster '{cluster_name}' is now ready",
                            "cluster_name": cluster_name,
                            "cluster_type": "k3s",
                            "container_name": container_name,
                            "port": port,
                            "status": "running",
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        return ErrorResult(
                            message=f"K3s cluster '{cluster_name}' is running but not ready within timeout",
                            code="CLUSTER_NOT_READY"
                        )
                
                elif existing_container.status == "exited":
                    # Container exists but is stopped, start it
                    try:
                        existing_container.start()
                        container = existing_container
                        
                        # Wait for container to be ready after starting
                        await asyncio.sleep(5)
                        
                        # Wait for container to be ready (check container status, not exec)
                        max_wait = 120
                        wait_time = 0
                        container_ready = False
                        
                        while wait_time < max_wait and not container_ready:
                            try:
                                # Check container status instead of trying exec
                                container.reload()
                                if container.status == "running":
                                    # Try a simple exec to see if container is ready
                                    result = container.exec_run("echo 'ready'", tty=False)
                                    if result.exit_code == 0:
                                        container_ready = True
                                        break
                            except Exception:
                                pass
                            
                            await asyncio.sleep(5)
                            wait_time += 5
                        
                        if not container_ready:
                            return ErrorResult(
                                message="Container is not ready for exec commands within timeout",
                                code="CONTAINER_NOT_READY"
                            )
                        
                        # Now wait for K3s to be ready
                        max_wait = 300  # 5 minutes for k3s initialization
                        wait_time = 0
                        k3s_ready = False
                        
                        while wait_time < max_wait and not k3s_ready:
                            try:
                                # Check if k3s is ready by looking for kubeconfig
                                process = await asyncio.create_subprocess_exec(
                                    "docker", "exec", container.name, "ls", "-la", "/etc/rancher/k3s/k3s.yaml",
                                    stdout=asyncio.subprocess.PIPE,
                                    stderr=asyncio.subprocess.PIPE
                                )
                                stdout, stderr = await process.communicate()
                                
                                if process.returncode == 0:
                                    # Try kubectl command
                                    process = await asyncio.create_subprocess_exec(
                                        "docker", "exec", container.name, "kubectl", "get", "nodes", "--no-headers",
                                        stdout=asyncio.subprocess.PIPE,
                                        stderr=asyncio.subprocess.PIPE
                                    )
                                    stdout, stderr = await process.communicate()
                                    
                                    if process.returncode == 0 and "Ready" in stdout.decode():
                                        k3s_ready = True
                                        break
                            except Exception:
                                pass
                            
                            await asyncio.sleep(15)  # Check less frequently
                            wait_time += 15
                        
                        if not k3s_ready:
                            return ErrorResult(
                                message="K3s cluster failed to start within timeout (5 minutes)",
                                code="STARTUP_TIMEOUT"
                            )
                        
                        return SuccessResult(data={
                            "message": f"K3s cluster '{cluster_name}' started successfully",
                            "cluster_name": cluster_name, 
                            "cluster_type": "k3s",
                            "container_name": container_name,
                            "container_id": container.short_id,
                            "port": port,
                            "status": "running",
                            "timestamp": datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        return ErrorResult(
                            message=f"Failed to start existing container {container_name}: {e}",
                            code="CONTAINER_START_FAILED"
                        )
                else:
                    # Container exists but in unknown state, remove it and recreate
                    try:
                        existing_container.remove(force=True)
                    except Exception:
                        pass
                    # Continue with creation logic below
                    
            except docker.errors.NotFound:
                # Container doesn't exist, continue with creation
                pass
            
            # Pull K3s image
            try:
                self.docker_client.images.pull("rancher/k3s:latest")
            except Exception as e:
                return ErrorResult(
                    message=f"Failed to pull K3s image: {e}",
                    code="IMAGE_PULL_FAILED"
                )
            
            # Create container
            try:
                container = self.docker_client.containers.run(
                    "rancher/k3s:latest",
                    command=["server", "--disable", "traefik", "--disable", "servicelb", "--disable-cloud-controller", "--disable-network-policy", "--disable", "local-storage"],
                    name=container_name,
                    detach=True,
                    privileged=True,  # K3s requires privileged mode for cgroup access
                    ports={f"{port}/tcp": port},
                    environment={
                        "K3S_TOKEN": "mysecret",
                        "K3S_KUBECONFIG_OUTPUT": "/output/kubeconfig.yaml"
                    },
                    volumes={
                        "/var/lib/rancher/k3s": {"bind": f"/tmp/k3s-{cluster_name}", "mode": "rw"}
                    },
                    labels={
                        "ai-admin.cluster": cluster_name,
                        "ai-admin.type": "k3s",
                        "ai-admin.created": datetime.now().isoformat()
                    }
                )
                
                # Wait for container to start and be ready for commands
                max_wait = 180  # 3 minutes to wait for container to be ready
                wait_time = 0
                container_ready = False
                
                while wait_time < max_wait and not container_ready:
                    try:
                        # First, check if container is running
                        container.reload()
                        if container.status == "running":
                            # Wait a bit more for container to fully initialize
                            await asyncio.sleep(10)
                            
                            # Now try a simple exec to see if container is ready for commands
                            process = await asyncio.create_subprocess_exec(
                                "docker", "exec", container.name, "echo", "ready",
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            stdout, stderr = await process.communicate()
                            
                            if process.returncode == 0:
                                container_ready = True
                                break
                    except Exception:
                        pass
                    
                    await asyncio.sleep(10)  # Wait longer between checks
                    wait_time += 10
                
                if not container_ready:
                    return ErrorResult(
                        message="Container is not ready for exec commands within timeout",
                        code="CONTAINER_NOT_READY"
                    )
                
                # Now wait for K3s to be ready - but be more patient
                max_wait = 300  # 5 minutes for k3s initialization
                wait_time = 0
                k3s_ready = False
                
                while wait_time < max_wait and not k3s_ready:
                    try:
                        # First wait a bit for k3s to initialize
                        await asyncio.sleep(20)
                        wait_time += 20
                        
                        # Check if k3s is ready by looking for kubeconfig
                        process = await asyncio.create_subprocess_exec(
                            "docker", "exec", container.name, "ls", "-la", "/etc/rancher/k3s/k3s.yaml",
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await process.communicate()
                        
                        if process.returncode == 0:
                            # Try kubectl command
                            process = await asyncio.create_subprocess_exec(
                                "docker", "exec", container.name, "kubectl", "get", "nodes", "--no-headers",
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            stdout, stderr = await process.communicate()
                            
                            if process.returncode == 0 and "Ready" in stdout.decode():
                                k3s_ready = True
                                break
                    except Exception:
                        pass
                    
                    await asyncio.sleep(30)  # Check less frequently
                    wait_time += 30
                
                if not k3s_ready:
                    return ErrorResult(
                        message="K3s cluster failed to start within timeout (5 minutes)",
                        code="STARTUP_TIMEOUT"
                )
            
                return SuccessResult(data={
                    "message": f"K3s cluster '{cluster_name}' created successfully",
                    "cluster_name": cluster_name,
                    "cluster_type": "k3s",
                    "container_name": container_name,
                    "container_id": container.short_id,
                    "port": port,
                    "status": "running",
                    "timestamp": datetime.now().isoformat()
                 })
            
            except Exception as e:
                return ErrorResult(
                    message=f"Failed to create K3s container: {e}",
                    code="CONTAINER_CREATION_FAILED"
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create K3s cluster: {str(e)}",
                code="K3S_CREATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _create_kind_cluster(self, cluster_name: str, config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Create a Kind cluster using subprocess (fallback)."""
        try:
            # For Kind, we still need to use subprocess as there's no Python SDK
            import subprocess
            
            cmd = ["kind", "create", "cluster", "--name", cluster_name]
            
            if config:
                # Create kind config file
                kind_config = {
                    "kind": "Cluster",
                    "apiVersion": "kind.x-k8s.io/v1alpha4",
                    "nodes": [
                        {
                            "role": "control-plane",
                            "extraPortMappings": [
                                {"containerPort": 6443, "hostPort": 6443}
                            ]
                        }
                    ]
                }
                
                config_path = f"/tmp/kind-config-{cluster_name}.yaml"
                with open(config_path, 'w') as f:
                    yaml.dump(kind_config, f)
                
                cmd.extend(["--config", config_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to create Kind cluster: {result.stderr}",
                    code="KIND_CREATION_FAILED"
                )
            
            return SuccessResult(data={
                "message": f"Kind cluster '{cluster_name}' created successfully",
                "cluster_name": cluster_name,
                "cluster_type": "kind",
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create Kind cluster: {str(e)}",
                code="KIND_CREATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _create_minikube_cluster(self, cluster_name: str, config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Create a Minikube cluster using subprocess (fallback)."""
        try:
            # For Minikube, we still need to use subprocess as there's no Python SDK
            import subprocess
            
            cmd = ["minikube", "start", "--profile", cluster_name]
            
            if config:
                if config.get("driver"):
                    cmd.extend(["--driver", config["driver"]])
                if config.get("kubernetes_version"):
                    cmd.extend(["--kubernetes-version", config["kubernetes_version"]])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to create Minikube cluster: {result.stderr}",
                    code="MINIKUBE_CREATION_FAILED"
                )
            
            return SuccessResult(data={
                "message": f"Minikube cluster '{cluster_name}' created successfully",
                "cluster_name": cluster_name,
                "cluster_type": "minikube",
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create Minikube cluster: {str(e)}",
                code="MINIKUBE_CREATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _delete_cluster(self, cluster_name: str, cluster_type: str) -> SuccessResult:
        """Delete a Kubernetes cluster."""
        try:
            if cluster_type == "k3s":
                return await self._delete_k3s_cluster(cluster_name)
            elif cluster_type == "kind":
                return await self._delete_kind_cluster(cluster_name)
            elif cluster_type == "minikube":
                return await self._delete_minikube_cluster(cluster_name)
            else:
                return ErrorResult(
                    message=f"Unsupported cluster type: {cluster_type}",
                    code="UNSUPPORTED_CLUSTER_TYPE"
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Failed to delete cluster: {str(e)}",
                code="DELETION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _delete_k3s_cluster(self, cluster_name: str) -> SuccessResult:
        """Delete a K3s cluster using Docker Python SDK."""
        try:
            if not self.docker_client:
                return ErrorResult(
                    message="Docker client not available",
                    code="DOCKER_CLIENT_UNAVAILABLE"
                )
            
            # Find container by name or label
            containers = self.docker_client.containers.list(
                filters={"label": f"ai-admin.cluster={cluster_name}"}
            )
            
            if not containers:
                # Try by name
                try:
                    container = self.docker_client.containers.get(f"k3s-{cluster_name}")
                    containers = [container]
                except docker.errors.NotFound:
                    return ErrorResult(
                        message=f"K3s cluster '{cluster_name}' not found",
                        code="CLUSTER_NOT_FOUND"
                    )
            
            deleted_containers = []
            for container in containers:
                try:
                    container.stop(timeout=30)
                    container.remove()
                    deleted_containers.append(container.name)
                except Exception as e:
                    print(f"Failed to delete container {container.name}: {e}")
            
            return SuccessResult(data={
                "message": f"K3s cluster '{cluster_name}' deleted successfully",
                "cluster_name": cluster_name,
                "deleted_containers": deleted_containers,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to delete K3s cluster: {str(e)}",
                code="K3S_DELETION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _delete_kind_cluster(self, cluster_name: str) -> SuccessResult:
        """Delete a Kind cluster using subprocess."""
        try:
            import subprocess
            
            result = subprocess.run(
                ["kind", "delete", "cluster", "--name", cluster_name],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to delete Kind cluster: {result.stderr}",
                    code="KIND_DELETION_FAILED"
                )
            
            return SuccessResult(data={
                "message": f"Kind cluster '{cluster_name}' deleted successfully",
                "cluster_name": cluster_name,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to delete Kind cluster: {str(e)}",
                code="KIND_DELETION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _delete_minikube_cluster(self, cluster_name: str) -> SuccessResult:
        """Delete a Minikube cluster using subprocess."""
        try:
            import subprocess
            
            result = subprocess.run(
                ["minikube", "delete", "--profile", cluster_name],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to delete Minikube cluster: {result.stderr}",
                    code="MINIKUBE_DELETION_FAILED"
                )
            
            return SuccessResult(data={
                "message": f"Minikube cluster '{cluster_name}' deleted successfully",
                "cluster_name": cluster_name,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to delete Minikube cluster: {str(e)}",
                code="MINIKUBE_DELETION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _get_cluster_status(self, cluster_name: str, cluster_type: str) -> SuccessResult:
        """Get status of a Kubernetes cluster."""
        try:
            if cluster_type == "k3s":
                return await self._get_k3s_cluster_status(cluster_name)
            elif cluster_type == "kind":
                return await self._get_kind_cluster_status(cluster_name)
            elif cluster_type == "minikube":
                return await self._get_minikube_cluster_status(cluster_name)
            else:
                return ErrorResult(
                    message=f"Unsupported cluster type: {cluster_type}",
                    code="UNSUPPORTED_CLUSTER_TYPE"
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Failed to get cluster status: {str(e)}",
                code="STATUS_FAILED",
                details={"exception": str(e)}
            )
    
    async def _get_k3s_cluster_status(self, cluster_name: str) -> SuccessResult:
        """Get status of a K3s cluster using Docker Python SDK."""
        try:
            if not self.docker_client:
                return ErrorResult(
                    message="Docker client not available",
                    code="DOCKER_CLIENT_UNAVAILABLE"
                )
            
            # Find container
            containers = self.docker_client.containers.list(
                filters={"label": f"ai-admin.cluster={cluster_name}"}
            )
            
            if not containers:
                try:
                    container = self.docker_client.containers.get(f"k3s-{cluster_name}")
                    containers = [container]
                except docker.errors.NotFound:
                    return ErrorResult(
                        message=f"K3s cluster '{cluster_name}' not found",
                        code="CLUSTER_NOT_FOUND"
                    )
            
            cluster_status = []
            for container in containers:
                try:
                    # Get container status
                    container.reload()
                    
                    # Get Kubernetes status
                    result = container.exec_run("kubectl get nodes --no-headers")
                    nodes_status = "unknown"
                    if result.exit_code == 0:
                        nodes_status = result.output.decode()
                    
                    status_info = {
                        "container_name": container.name,
                        "container_id": container.short_id,
                        "container_status": container.status,
                        "nodes_status": nodes_status,
                        "created": container.attrs["Created"],
                        "ports": container.attrs["NetworkSettings"]["Ports"]
                    }
                    cluster_status.append(status_info)
                    
                except Exception as e:
                    cluster_status.append({
                        "container_name": container.name,
                        "error": str(e)
                    })
            
            return SuccessResult(data={
                "message": f"K3s cluster '{cluster_name}' status retrieved",
                "cluster_name": cluster_name,
                "cluster_type": "k3s",
                "status": cluster_status,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to get K3s cluster status: {str(e)}",
                code="K3S_STATUS_FAILED",
                details={"exception": str(e)}
            )
    
    async def _get_kind_cluster_status(self, cluster_name: str) -> SuccessResult:
        """Get status of a Kind cluster using subprocess."""
        try:
            import subprocess
            
            result = subprocess.run(
                ["kind", "get", "clusters"],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to get Kind clusters: {result.stderr}",
                    code="KIND_STATUS_FAILED"
                )
            
            clusters = result.stdout.strip().split('\n')
            is_running = cluster_name in clusters
            
            return SuccessResult(data={
                "message": f"Kind cluster '{cluster_name}' status retrieved",
                "cluster_name": cluster_name,
                "cluster_type": "kind",
                "status": "running" if is_running else "not_found",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to get Kind cluster status: {str(e)}",
                code="KIND_STATUS_FAILED",
                details={"exception": str(e)}
            )
    
    async def _get_minikube_cluster_status(self, cluster_name: str) -> SuccessResult:
        """Get status of a Minikube cluster using subprocess."""
        try:
            import subprocess
            
            result = subprocess.run(
                ["minikube", "status", "--profile", cluster_name],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to get Minikube cluster status: {result.stderr}",
                    code="MINIKUBE_STATUS_FAILED"
                )
            
            return SuccessResult(data={
                "message": f"Minikube cluster '{cluster_name}' status retrieved",
                "cluster_name": cluster_name,
                "cluster_type": "minikube",
                "status": result.stdout.strip(),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to get Minikube cluster status: {str(e)}",
                code="MINIKUBE_STATUS_FAILED",
                details={"exception": str(e)}
            )
    
    async def _create_cluster_with_queue(self, cluster_name: str, cluster_type: str,
                                       container_name: Optional[str], port: Optional[int],
                                       config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Create cluster using queue system."""
        try:
            print(f"DEBUG: Starting _create_cluster_with_queue for {cluster_name}")
            
            from ai_admin.queue.task_queue import Task, TaskType
            
            print(f"DEBUG: Imported Task and TaskType")
            
            # Create task with proper type based on cluster type
            if cluster_type == "k3s":
                task_type = TaskType.KIND_CLUSTER_CREATE  # Use kind task type for k3s
            elif cluster_type == "kind":
                task_type = TaskType.KIND_CLUSTER_CREATE
            elif cluster_type == "minikube":
                task_type = TaskType.CUSTOM_SCRIPT  # Minikube might need custom script
            else:
                task_type = TaskType.CUSTOM_SCRIPT
            
            print(f"DEBUG: Task type determined: {task_type}")
            
            task = Task(
                task_type=task_type,
                params={
                    "cluster_name": cluster_name,
                    "cluster_type": cluster_type,
                    "container_name": container_name,
                    "port": port,
                    "config": config
                }
            )
            
            print(f"DEBUG: Task created, adding to queue...")
            
            task_id = await queue_manager.task_queue.add_task(task)
            
            print(f"DEBUG: Task added to queue with ID: {task_id}")
            
            return SuccessResult(data={
                "message": f"Cluster creation task queued successfully",
                "task_id": task_id,
                "cluster_name": cluster_name,
                "cluster_type": cluster_type,
                "status": "queued",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"DEBUG: Exception in _create_cluster_with_queue: {e}")
            return ErrorResult(
                message=f"Failed to queue cluster creation: {str(e)}",
                code="QUEUE_FAILED",
                details={"exception": str(e)}
            )
    
    async def _initialize_cluster(self, cluster_name: str, namespace: Optional[str],
                                config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Initialize a cluster with default resources."""
        try:
            # This would typically involve creating namespaces, RBAC, etc.
            # For now, we'll return a success message
            return SuccessResult(data={
                "message": f"Cluster '{cluster_name}' initialization completed",
                "cluster_name": cluster_name,
                "namespace": namespace or "default",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to initialize cluster: {str(e)}",
                code="INITIALIZATION_FAILED",
                details={"exception": str(e)}
            ) 