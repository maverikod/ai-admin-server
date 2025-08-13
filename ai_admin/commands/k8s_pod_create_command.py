"""Kubernetes pod creation command for MCP server."""

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class K8sPodCreateCommand(Command):
    """Command to create Kubernetes pods for projects using kubernetes Python library."""
    
    name = "k8s_pod_create"
    
    def __init__(self):
        """Initialize Kubernetes client configuration."""
        try:
            # Try to load kubeconfig from default location
            config.load_kube_config()
        except Exception:
            # Fallback to in-cluster config
            try:
                config.load_incluster_config()
            except Exception:
                # Use default config
                pass
    
    def get_project_name(self, project_path: str) -> str:
        """Extract and sanitize project name from path."""
        project_name = Path(project_path).name
        # Convert to kubernetes-compatible name (lowercase, no special chars)
        sanitized = re.sub(r'[^a-z0-9]', '-', project_name.lower())
        return sanitized.strip('-')
    
    async def execute(self, 
                     project_path: Optional[str] = None,
                     image: str = "ai-admin-server:latest",
                     port: int = 8060,
                     namespace: str = "default",
                     cpu_limit: str = "500m",
                     memory_limit: str = "512Mi",
                     **kwargs):
        """
        Create Kubernetes pod for project with mounted directory using kubernetes Python library.
        
        Args:
            project_path: Path to project directory (defaults to current working directory)
            image: Docker image to use
            port: Port to expose
            namespace: Kubernetes namespace
            cpu_limit: CPU limit for pod
            memory_limit: Memory limit for pod
        """
        try:
            # Get current working directory if path not provided
            if not project_path:
                project_path = os.getcwd()
            
            # Ensure path exists
            if not os.path.exists(project_path):
                return ErrorResult(
                    message=f"Project path does not exist: {project_path}",
                    code="PATH_NOT_FOUND",
                    details={}
                )
            
            project_name = self.get_project_name(project_path)
            pod_name = f"ai-admin-{project_name}"
            
            # Create Kubernetes API client
            core_v1 = client.CoreV1Api()
            
            # Create pod object using kubernetes library
            pod = client.V1Pod(
                metadata=client.V1ObjectMeta(
                    name=pod_name,
                    namespace=namespace,
                    labels={
                        "app": "ai-admin",
                        "project": project_name
                    }
                ),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="mcp-server",
                            image=image,
                            ports=[
                                client.V1ContainerPort(
                                    container_port=port,
                                    name="http"
                                )
                            ],
                            volume_mounts=[
                                client.V1VolumeMount(
                                    name="project-volume",
                                    mount_path="/app"
                                )
                            ],
                            resources=client.V1ResourceRequirements(
                                limits={
                                    "cpu": cpu_limit,
                                    "memory": memory_limit
                                },
                                requests={
                                    "cpu": "100m",
                                    "memory": "128Mi"
                                }
                            ),
                            env=[
                                client.V1EnvVar(
                                    name="PROJECT_PATH",
                                    value="/app"
                                )
                            ]
                        )
                    ],
                    volumes=[
                        client.V1Volume(
                            name="project-volume",
                            host_path=client.V1HostPathVolumeSource(
                                path=project_path,
                                type="Directory"
                            )
                        )
                    ],
                    restart_policy="Always"
                )
            )
            
            # Check if pod already exists
            try:
                existing_pod = core_v1.read_namespaced_pod(
                    name=pod_name,
                    namespace=namespace
                )
                return SuccessResult(data={
                    "message": f"Pod {pod_name} already exists in namespace {namespace}",
                    "pod_name": pod_name,
                    "namespace": namespace,
                    "project_path": project_path,
                    "project_name": project_name,
                    "status": "already_exists",
                    "pod_phase": existing_pod.status.phase,
                    "pod_ip": existing_pod.status.pod_ip
                })
            except ApiException as e:
                if e.status != 404:  # Not found is expected
                    return ErrorResult(
                        message=f"Error checking pod existence: {str(e)}",
                        code="POD_CHECK_FAILED",
                        details={"api_exception": str(e)}
                    )
            
            # Create the pod
            try:
                created_pod = core_v1.create_namespaced_pod(
                    namespace=namespace,
                    body=pod
                )
                
                # Get pod status
                pod_status = created_pod.status
                pod_phase = pod_status.phase if pod_status.phase else "Unknown"
                pod_ip = pod_status.pod_ip if pod_status.pod_ip else None
                
                return SuccessResult(data={
                    "message": f"Successfully created pod {pod_name}",
                    "pod_name": pod_name,
                    "namespace": namespace,
                    "project_path": project_path,
                    "project_name": project_name,
                    "port": port,
                    "pod_phase": pod_phase,
                    "pod_ip": pod_ip,
                    "uid": created_pod.metadata.uid,
                    "creation_timestamp": created_pod.metadata.creation_timestamp.isoformat() if created_pod.metadata.creation_timestamp else None,
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                return ErrorResult(
                    message=f"Failed to create pod: {str(e)}",
                    code="POD_CREATE_FAILED",
                    details={
                        "api_exception": str(e),
                        "status_code": e.status,
                        "reason": e.reason
                    }
                )
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error creating pod: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for k8s pod create command parameters."""
        return {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to project directory (defaults to current working directory)"
                },
                "image": {
                    "type": "string",
                    "description": "Docker image to use",
                    "default": "ai-admin-server:latest"
                },
                "port": {
                    "type": "integer",
                    "description": "Port to expose",
                    "default": 8060
                },
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace",
                    "default": "default"
                },
                "cpu_limit": {
                    "type": "string",
                    "description": "CPU limit for pod",
                    "default": "500m"
                },
                "memory_limit": {
                    "type": "string",
                    "description": "Memory limit for pod",
                    "default": "512Mi"
                }
            }
        } 