"""Kubernetes ConfigMap and Secret management commands for MCP server."""

import re
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class K8sConfigMapCreateCommand(Command):
    """Command to create Kubernetes ConfigMaps using Python kubernetes library."""
    
    name = "k8s_configmap_create"
    
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
                     configmap_name: str,
                     namespace: str = "default",
                     project_path: Optional[str] = None,
                     data: Optional[Dict[str, str]] = None,
                     labels: Optional[Dict[str, str]] = None,
                     **kwargs):
        """
        Create Kubernetes ConfigMap using Python kubernetes library.
        
        Args:
            configmap_name: Name of the ConfigMap
            namespace: Kubernetes namespace
            project_path: Path to project directory (used for default labels)
            data: Key-value pairs for ConfigMap data
            labels: Labels to apply to the ConfigMap
        """
        try:
            # Set default data if not provided
            if not data:
                data = {
                    "config.json": '{"default": "configuration"}',
                    "app.config": "default_configuration"
                }
            
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
            
            # Check if ConfigMap already exists
            try:
                existing_configmap = self.core_v1.read_namespaced_config_map(
                    name=configmap_name,
                    namespace=namespace
                )
                
                return SuccessResult(data={
                    "message": f"ConfigMap {configmap_name} already exists",
                    "namespace": namespace,
                    "configmap_name": configmap_name,
                    "configmap_info": {
                        "name": existing_configmap.metadata.name,
                        "namespace": existing_configmap.metadata.namespace,
                        "data": existing_configmap.data or {},
                        "labels": existing_configmap.metadata.labels or {}
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                if e.status != 404:
                    return ErrorResult(
                        message=f"Failed to check ConfigMap existence: {e}",
                        code="K8S_API_ERROR",
                        details={"status": e.status, "reason": e.reason}
                    )
            
            # Create ConfigMap
            try:
                # Create ConfigMap metadata
                configmap_metadata = client.V1ObjectMeta(
                    name=configmap_name,
                    namespace=namespace,
                    labels=labels
                )
                
                # Create ConfigMap object
                configmap = client.V1ConfigMap(
                    api_version="v1",
                    kind="ConfigMap",
                    metadata=configmap_metadata,
                    data=data
                )
                
                # Create the ConfigMap
                created_configmap = self.core_v1.create_namespaced_config_map(
                    namespace=namespace,
                    body=configmap
                )
                
                return SuccessResult(data={
                    "message": f"ConfigMap {configmap_name} created successfully",
                    "namespace": namespace,
                    "configmap_name": configmap_name,
                    "configmap_info": {
                        "name": created_configmap.metadata.name,
                        "namespace": created_configmap.metadata.namespace,
                        "data": created_configmap.data or {},
                        "labels": created_configmap.metadata.labels or {}
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                return ErrorResult(
                    message=f"Failed to create ConfigMap: {e}",
                    code="K8S_API_ERROR",
                    details={"status": e.status, "reason": e.reason}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error creating ConfigMap: {e}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )


class K8sSecretCreateCommand(Command):
    """Command to create Kubernetes Secrets using Python kubernetes library."""
    
    name = "k8s_secret_create"
    
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
                     secret_name: str,
                     namespace: str = "default",
                     project_path: Optional[str] = None,
                     data: Optional[Dict[str, str]] = None,
                     labels: Optional[Dict[str, str]] = None,
                     secret_type: str = "Opaque",
                     **kwargs):
        """
        Create Kubernetes Secret using Python kubernetes library.
        
        Args:
            secret_name: Name of the Secret
            namespace: Kubernetes namespace
            project_path: Path to project directory (used for default labels)
            data: Key-value pairs for Secret data (will be base64 encoded)
            labels: Labels to apply to the Secret
            secret_type: Type of Secret (Opaque, kubernetes.io/tls, etc.)
        """
        try:
            # Set default data if not provided
            if not data:
                data = {
                    "username": "admin",
                    "password": "secret123"
                }
            
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
            
            # Encode data to base64
            encoded_data = {}
            for key, value in data.items():
                encoded_data[key] = base64.b64encode(value.encode()).decode()
            
            # Check if Secret already exists
            try:
                existing_secret = self.core_v1.read_namespaced_secret(
                    name=secret_name,
                    namespace=namespace
                )
                
                return SuccessResult(data={
                    "message": f"Secret {secret_name} already exists",
                    "namespace": namespace,
                    "secret_name": secret_name,
                    "secret_info": {
                        "name": existing_secret.metadata.name,
                        "namespace": existing_secret.metadata.namespace,
                        "type": existing_secret.type,
                        "data_keys": list(existing_secret.data.keys()) if existing_secret.data else [],
                        "labels": existing_secret.metadata.labels or {}
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                if e.status != 404:
                    return ErrorResult(
                        message=f"Failed to check Secret existence: {e}",
                        code="K8S_API_ERROR",
                        details={"status": e.status, "reason": e.reason}
                    )
            
            # Create Secret
            try:
                # Create Secret metadata
                secret_metadata = client.V1ObjectMeta(
                    name=secret_name,
                    namespace=namespace,
                    labels=labels
                )
                
                # Create Secret object
                secret = client.V1Secret(
                    api_version="v1",
                    kind="Secret",
                    metadata=secret_metadata,
                    type=secret_type,
                    data=encoded_data
                )
                
                # Create the Secret
                created_secret = self.core_v1.create_namespaced_secret(
                    namespace=namespace,
                    body=secret
                )
                
                return SuccessResult(data={
                    "message": f"Secret {secret_name} created successfully",
                    "namespace": namespace,
                    "secret_name": secret_name,
                    "secret_info": {
                        "name": created_secret.metadata.name,
                        "namespace": created_secret.metadata.namespace,
                        "type": created_secret.type,
                        "data_keys": list(created_secret.data.keys()) if created_secret.data else [],
                        "labels": created_secret.metadata.labels or {}
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                return ErrorResult(
                    message=f"Failed to create Secret: {e}",
                    code="K8S_API_ERROR",
                    details={"status": e.status, "reason": e.reason}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error creating Secret: {e}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )


class K8sResourceDeleteCommand(Command):
    """Command to delete Kubernetes resources using Python kubernetes library."""
    
    name = "k8s_resource_delete"
    
    def __init__(self):
        """Initialize Kubernetes client."""
        try:
            config.load_kube_config()
        except config.ConfigException:
            # Try in-cluster config
            config.load_incluster_config()
        
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
    
    async def execute(self, 
                     resource_type: str,
                     resource_name: str,
                     namespace: str = "default",
                     force: bool = False,
                     **kwargs):
        """
        Delete Kubernetes resource using Python kubernetes library.
        
        Args:
            resource_type: Type of resource (pod, service, configmap, secret, deployment)
            resource_name: Name of the resource to delete
            namespace: Kubernetes namespace
            force: Force deletion even if resource is running
        """
        try:
            delete_options = client.V1DeleteOptions()
            if force:
                delete_options.grace_period_seconds = 0
            
            try:
                if resource_type.lower() == "pod":
                    self.core_v1.delete_namespaced_pod(
                        name=resource_name,
                        namespace=namespace,
                        body=delete_options
                    )
                elif resource_type.lower() == "service":
                    self.core_v1.delete_namespaced_service(
                        name=resource_name,
                        namespace=namespace,
                        body=delete_options
                    )
                elif resource_type.lower() == "configmap":
                    self.core_v1.delete_namespaced_config_map(
                        name=resource_name,
                        namespace=namespace,
                        body=delete_options
                    )
                elif resource_type.lower() == "secret":
                    self.core_v1.delete_namespaced_secret(
                        name=resource_name,
                        namespace=namespace,
                        body=delete_options
                    )
                elif resource_type.lower() == "deployment":
                    self.apps_v1.delete_namespaced_deployment(
                        name=resource_name,
                        namespace=namespace,
                        body=delete_options
                    )
                else:
                    return ErrorResult(
                        message=f"Unsupported resource type: {resource_type}",
                        code="UNSUPPORTED_RESOURCE_TYPE",
                        details={"supported_types": ["pod", "service", "configmap", "secret", "deployment"]}
                    )
                
                return SuccessResult(data={
                    "message": f"{resource_type.capitalize()} {resource_name} deleted successfully",
                    "resource_type": resource_type,
                    "resource_name": resource_name,
                    "namespace": namespace,
                    "force": force,
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                if e.status == 404:
                    return ErrorResult(
                        message=f"{resource_type.capitalize()} {resource_name} not found in namespace {namespace}",
                        code="RESOURCE_NOT_FOUND",
                        details={"status": e.status, "reason": e.reason}
                    )
                else:
                    return ErrorResult(
                        message=f"Failed to delete {resource_type}: {e}",
                        code="K8S_API_ERROR",
                        details={"status": e.status, "reason": e.reason}
                    )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error deleting resource: {e}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            ) 