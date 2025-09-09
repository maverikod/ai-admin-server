"""Kubernetes namespace management commands for MCP server."""

import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class K8sNamespaceCreateCommand(Command):
    """Command to create Kubernetes namespaces using Python kubernetes library."""
    
    name = "k8s_namespace_create"
    
    def __init__(self):
        """Initialize Kubernetes client."""
        try:
            config.load_kube_config()
            
            # Configure client with SSL verification disabled for self-signed certs
            configuration = client.Configuration()
            configuration.verify_ssl = False
            client.Configuration.set_default(configuration)
            
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
                     namespace: str,
                     project_path: Optional[str] = None,
                     labels: Optional[Dict[str, str]] = None,
                     **kwargs):
        """
        Create Kubernetes namespace using Python kubernetes library.
        
        Args:
            namespace: Name of the namespace to create
            project_path: Path to project directory (used for default labels)
            labels: Labels to apply to the namespace
        """
        try:
            # Set default labels if not provided
            if not labels:
                if project_path:
                    project_name = self.get_project_name(project_path)
                    labels = {
                        "app": "ai-admin",
                        "project": project_name,
                        "managed-by": "ai-admin"
                    }
                else:
                    labels = {
                        "app": "ai-admin",
                        "managed-by": "ai-admin"
                    }
            
            # Check if namespace already exists
            try:
                existing_namespace = self.core_v1.read_namespace(name=namespace)
                
                return SuccessResult(data={
                    "message": f"Namespace {namespace} already exists",
                    "namespace": namespace,
                    "namespace_info": {
                        "name": existing_namespace.metadata.name,
                        "status": existing_namespace.status.phase,
                        "labels": existing_namespace.metadata.labels or {},
                        "annotations": existing_namespace.metadata.annotations or {}
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                if e.status != 404:
                    return ErrorResult(
                        message=f"Failed to check namespace existence: {e}",
                        code="K8S_API_ERROR",
                        details={"status": e.status, "reason": e.reason}
                    )
            
            # Create namespace
            try:
                # Create namespace metadata
                namespace_metadata = client.V1ObjectMeta(
                    name=namespace,
                    labels=labels
                )
                
                # Create namespace object
                namespace_obj = client.V1Namespace(
                    api_version="v1",
                    kind="Namespace",
                    metadata=namespace_metadata
                )
                
                # Create the namespace
                created_namespace = self.core_v1.create_namespace(body=namespace_obj)
                
                return SuccessResult(data={
                    "message": f"Namespace {namespace} created successfully",
                    "namespace": namespace,
                    "namespace_info": {
                        "name": created_namespace.metadata.name,
                        "status": created_namespace.status.phase,
                        "labels": created_namespace.metadata.labels or {},
                        "annotations": created_namespace.metadata.annotations or {}
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                return ErrorResult(
                    message=f"Failed to create namespace: {e}",
                    code="K8S_API_ERROR",
                    details={"status": e.status, "reason": e.reason}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error creating namespace: {e}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )


class K8sNamespaceListCommand(Command):
    """Command to list Kubernetes namespaces using Python kubernetes library."""
    
    name = "k8s_namespace_list"
    
    def __init__(self):
        """Initialize Kubernetes client."""
        try:
            config.load_kube_config()
        except config.ConfigException:
            # Try in-cluster config
            config.load_incluster_config()
        
        self.core_v1 = client.CoreV1Api()
    
    async def execute(self, **kwargs):
        """
        List Kubernetes namespaces using Python kubernetes library.
        """
        try:
            try:
                namespaces = self.core_v1.list_namespace()
                
                namespace_list = []
                for namespace in namespaces.items:
                    namespace_info = {
                        "name": namespace.metadata.name,
                        "status": namespace.status.phase,
                        "labels": namespace.metadata.labels or {},
                        "annotations": namespace.metadata.annotations or {},
                        "created": namespace.metadata.creation_timestamp.isoformat() if namespace.metadata.creation_timestamp else None
                    }
                    namespace_list.append(namespace_info)
                
                return SuccessResult(data={
                    "message": f"Found {len(namespace_list)} namespaces",
                    "namespaces": namespace_list,
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                return ErrorResult(
                    message=f"Failed to list namespaces: {e}",
                    code="K8S_API_ERROR",
                    details={"status": e.status, "reason": e.reason}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error listing namespaces: {e}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )


class K8sNamespaceDeleteCommand(Command):
    """Command to delete Kubernetes namespaces using Python kubernetes library."""
    
    name = "k8s_namespace_delete"
    
    def __init__(self):
        """Initialize Kubernetes client."""
        try:
            config.load_kube_config()
        except config.ConfigException:
            # Try in-cluster config
            config.load_incluster_config()
        
        self.core_v1 = client.CoreV1Api()
    
    async def execute(self, 
                     namespace: str,
                     force: bool = False,
                     **kwargs):
        """
        Delete Kubernetes namespace using Python kubernetes library.
        
        Args:
            namespace: Name of the namespace to delete
            force: Force deletion even if namespace contains resources
        """
        try:
            # Check if namespace exists
            try:
                existing_namespace = self.core_v1.read_namespace(name=namespace)
            except ApiException as e:
                if e.status == 404:
                    return ErrorResult(
                        message=f"Namespace {namespace} not found",
                        code="NAMESPACE_NOT_FOUND",
                        details={"status": e.status, "reason": e.reason}
                    )
                else:
                    return ErrorResult(
                        message=f"Failed to check namespace existence: {e}",
                        code="K8S_API_ERROR",
                        details={"status": e.status, "reason": e.reason}
                    )
            
            # Delete namespace
            try:
                delete_options = client.V1DeleteOptions()
                if force:
                    delete_options.grace_period_seconds = 0
                
                self.core_v1.delete_namespace(
                    name=namespace,
                    body=delete_options
                )
                
                return SuccessResult(data={
                    "message": f"Namespace {namespace} deleted successfully",
                    "namespace": namespace,
                    "force": force,
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                return ErrorResult(
                    message=f"Failed to delete namespace: {e}",
                    code="K8S_API_ERROR",
                    details={"status": e.status, "reason": e.reason}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error deleting namespace: {e}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            ) 