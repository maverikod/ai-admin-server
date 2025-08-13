"""Kubernetes deployment creation command for MCP server."""

import os
import re
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class K8sDeploymentCreateCommand(Command):
    """Command to create Kubernetes deployments for projects using kubernetes Python library."""
    
    name = "k8s_deployment_create"
    
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
                     replicas: int = 1,
                     cpu_limit: str = "500m",
                     memory_limit: str = "512Mi",
                     cpu_request: str = "100m",
                     memory_request: str = "128Mi",
                     **kwargs):
        """
        Create Kubernetes deployment for project with mounted directory using kubernetes Python library.
        
        Args:
            project_path: Path to project directory (defaults to current working directory)
            image: Docker image to use
            port: Port to expose
            namespace: Kubernetes namespace
            replicas: Number of replicas
            cpu_limit: CPU limit for containers
            memory_limit: Memory limit for containers
            cpu_request: CPU request for containers
            memory_request: Memory request for containers
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
            deployment_name = f"ai-admin-{project_name}"
            
            # Create Kubernetes API client
            apps_v1 = client.AppsV1Api()
            
            # Create deployment object using kubernetes library
            deployment = client.V1Deployment(
                metadata=client.V1ObjectMeta(
                    name=deployment_name,
                    namespace=namespace,
                    labels={
                        "app": "ai-admin",
                        "project": project_name
                    }
                ),
                spec=client.V1DeploymentSpec(
                    replicas=replicas,
                    selector=client.V1LabelSelector(
                        match_labels={
                            "app": "ai-admin",
                            "project": project_name
                        }
                    ),
                    template=client.V1PodTemplateSpec(
                        metadata=client.V1ObjectMeta(
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
                                            "cpu": cpu_request,
                                            "memory": memory_request
                                        }
                                    ),
                                    env=[
                                        client.V1EnvVar(
                                            name="PROJECT_PATH",
                                            value="/app"
                                        )
                                    ],
                                    liveness_probe=client.V1Probe(
                                        http_get=client.V1HTTPGetAction(
                                            path="/health",
                                            port=port
                                        ),
                                        initial_delay_seconds=30,
                                        period_seconds=10
                                    ),
                                    readiness_probe=client.V1Probe(
                                        http_get=client.V1HTTPGetAction(
                                            path="/health",
                                            port=port
                                        ),
                                        initial_delay_seconds=5,
                                        period_seconds=5
                                    )
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
                )
            )
            
            # Check if deployment already exists
            try:
                existing_deployment = apps_v1.read_namespaced_deployment(
                    name=deployment_name,
                    namespace=namespace
                )
                return SuccessResult(data={
                    "message": f"Deployment {deployment_name} already exists in namespace {namespace}",
                    "deployment_name": deployment_name,
                    "namespace": namespace,
                    "project_path": project_path,
                    "project_name": project_name,
                    "status": "already_exists",
                    "available_replicas": existing_deployment.status.available_replicas,
                    "replicas": existing_deployment.status.replicas
                })
            except ApiException as e:
                if e.status != 404:  # Not found is expected
                    return ErrorResult(
                        message=f"Error checking deployment existence: {str(e)}",
                        code="DEPLOYMENT_CHECK_FAILED",
                        details={"api_exception": str(e)}
                    )
            
            # Create the deployment
            try:
                created_deployment = apps_v1.create_namespaced_deployment(
                    namespace=namespace,
                    body=deployment
                )
                
                # Get deployment status
                deployment_status = created_deployment.status
                available_replicas = deployment_status.available_replicas if deployment_status.available_replicas else 0
                
                return SuccessResult(data={
                    "message": f"Successfully created deployment {deployment_name}",
                    "deployment_name": deployment_name,
                    "namespace": namespace,
                    "project_path": project_path,
                    "project_name": project_name,
                    "replicas": replicas,
                    "available_replicas": available_replicas,
                    "port": port,
                    "uid": created_deployment.metadata.uid,
                    "creation_timestamp": created_deployment.metadata.creation_timestamp.isoformat() if created_deployment.metadata.creation_timestamp else None,
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                return ErrorResult(
                    message=f"Failed to create deployment: {str(e)}",
                    code="DEPLOYMENT_CREATE_FAILED",
                    details={
                        "api_exception": str(e),
                        "status_code": e.status,
                        "reason": e.reason
                    }
                )
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error creating deployment: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for k8s deployment create command parameters."""
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
                "replicas": {
                    "type": "integer",
                    "description": "Number of replicas",
                    "default": 1
                },
                "cpu_limit": {
                    "type": "string",
                    "description": "CPU limit for containers",
                    "default": "500m"
                },
                "memory_limit": {
                    "type": "string",
                    "description": "Memory limit for containers", 
                    "default": "512Mi"
                },
                "cpu_request": {
                    "type": "string",
                    "description": "CPU request for containers",
                    "default": "100m"
                },
                "memory_request": {
                    "type": "string",
                    "description": "Memory request for containers",
                    "default": "128Mi"
                }
            }
        } 