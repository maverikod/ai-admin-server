"""Kubernetes service creation command for MCP server."""

import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class K8sServiceCreateCommand(Command):
    """Command to create Kubernetes services for projects using Python kubernetes library."""
    
    name = "k8s_service_create"
    
    def __init__(self):
        """Initialize Kubernetes client."""
        try:
            config.load_kube_config()
        except config.ConfigException:
            # Try in-cluster config
            config.load_incluster_config()
        
        self.core_v1 = client.CoreV1Api()
    
    def get_project_name(self, project_path: str) -> str:
        """Extract and sanitize project name from path."""
        project_name = Path(project_path).name
        # Convert to kubernetes-compatible name (lowercase, no special chars)
        sanitized = re.sub(r'[^a-z0-9]', '-', project_name.lower())
        return sanitized.strip('-')
    
    async def execute(self, 
                     service_name: Optional[str] = None,
                     project_path: Optional[str] = None,
                     namespace: str = "default",
                     port: int = 80,
                     target_port: int = 80,
                     service_type: str = "ClusterIP",
                     **kwargs):
        """
        Create Kubernetes service using Python kubernetes library.
        
        Args:
            service_name: Name of the service (if not provided, derived from project_path)
            project_path: Path to project directory (used to derive service name)
            namespace: Kubernetes namespace
            port: Service port
            target_port: Target port on pods
            service_type: Type of service (ClusterIP, NodePort, LoadBalancer)
        """
        try:
            if not service_name:
                if not project_path:
                    import os
                    project_path = os.getcwd()
                
                project_name = self.get_project_name(project_path)
                service_name = f"ai-admin-{project_name}-service"
            
            # Check if service already exists
            try:
                existing_service = self.core_v1.read_namespaced_service(
                    name=service_name,
                    namespace=namespace
                )
                
                return SuccessResult(data={
                    "message": f"Service {service_name} already exists",
                    "namespace": namespace,
                    "service_name": service_name,
                    "service_info": {
                        "name": existing_service.metadata.name,
                        "namespace": existing_service.metadata.namespace,
                        "type": existing_service.spec.type,
                        "cluster_ip": existing_service.spec.cluster_ip,
                        "ports": [
                            {
                                "port": port.port,
                                "target_port": port.target_port,
                                "protocol": port.protocol
                            } for port in existing_service.spec.ports
                        ] if existing_service.spec.ports else []
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                if e.status != 404:
                    return ErrorResult(
                        message=f"Failed to check service existence: {e}",
                        code="K8S_API_ERROR",
                        details={"status": e.status, "reason": e.reason}
                    )
            
            # Create service
            try:
                # Create service spec
                service_port = client.V1ServicePort(
                    port=port,
                    target_port=target_port,
                    protocol="TCP"
                )
                
                service_spec = client.V1ServiceSpec(
                    type=service_type,
                    ports=[service_port],
                    selector={"app": f"ai-admin-{self.get_project_name(project_path or '.')}"}
                )
                
                # Create service metadata
                service_metadata = client.V1ObjectMeta(
                    name=service_name,
                    namespace=namespace,
                    labels={
                        "app": f"ai-admin-{self.get_project_name(project_path or '.')}",
                        "service": "ai-admin"
                    }
                )
                
                # Create service object
                service = client.V1Service(
                    api_version="v1",
                    kind="Service",
                    metadata=service_metadata,
                    spec=service_spec
                )
                
                # Create the service
                created_service = self.core_v1.create_namespaced_service(
                    namespace=namespace,
                    body=service
                )
                
                return SuccessResult(data={
                    "message": f"Service {service_name} created successfully",
                    "namespace": namespace,
                    "service_name": service_name,
                    "service_info": {
                        "name": created_service.metadata.name,
                        "namespace": created_service.metadata.namespace,
                        "type": created_service.spec.type,
                        "cluster_ip": created_service.spec.cluster_ip,
                        "ports": [
                            {
                                "port": port.port,
                                "target_port": port.target_port,
                                "protocol": port.protocol
                            } for port in created_service.spec.ports
                        ] if created_service.spec.ports else []
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                return ErrorResult(
                    message=f"Failed to create service: {e}",
                    code="K8S_API_ERROR",
                    details={"status": e.status, "reason": e.reason}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error creating service: {e}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for k8s service create command parameters."""
        return {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to project directory (defaults to current working directory)"
                },
                "service_type": {
                    "type": "string",
                    "description": "Type of service",
                    "enum": ["ClusterIP", "NodePort", "LoadBalancer"],
                    "default": "ClusterIP"
                },
                "port": {
                    "type": "integer",
                    "description": "Service port",
                    "default": 8060
                },
                "target_port": {
                    "type": "integer", 
                    "description": "Target port on pods",
                    "default": 8060
                },
                "node_port": {
                    "type": "integer",
                    "description": "NodePort (only for NodePort service type)",
                    "minimum": 30000,
                    "maximum": 32767
                },
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace",
                    "default": "default"
                }
            }
        } 