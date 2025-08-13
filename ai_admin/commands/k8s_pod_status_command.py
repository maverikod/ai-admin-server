"""Kubernetes pod status command for MCP server."""

import re
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.k8s_utils import KubernetesConfigManager
from ai_admin.settings_manager import get_settings_manager


class K8sPodStatusCommand(Command):
    """Command to get status of Kubernetes pods using Python kubernetes library."""
    
    name = "k8s_pod_status"
    
    def __init__(self):
        """Initialize Kubernetes client."""
        self.config_manager = None
        self.core_v1 = None
    
    def _init_client(self, cluster_name: Optional[str] = None):
        """Initialize Kubernetes client for specific cluster."""
        try:
            # Get settings and create config manager
            settings_manager = get_settings_manager()
            config_data = settings_manager.get_all_settings()
            self.config_manager = KubernetesConfigManager(config_data)
            
            # Load kubeconfig for the cluster
            if self.config_manager.load_kubeconfig(cluster_name):
                self.core_v1 = client.CoreV1Api()
            else:
                # Fallback to default config
                try:
                    config.load_kube_config()
                    self.core_v1 = client.CoreV1Api()
                except config.ConfigException:
                    config.load_incluster_config()
                    self.core_v1 = client.CoreV1Api()
                    
        except Exception as e:
            print(f"Failed to initialize Kubernetes client: {e}")
            # Fallback to default config
            try:
                config.load_kube_config()
                self.core_v1 = client.CoreV1Api()
            except config.ConfigException:
                config.load_incluster_config()
                self.core_v1 = client.CoreV1Api()
    
    def get_project_name(self, project_path: str) -> str:
        """Extract and sanitize project name from path."""
        project_name = Path(project_path).name
        # Convert to kubernetes-compatible name (lowercase, no special chars)
        sanitized = re.sub(r'[^a-z0-9]', '-', project_name.lower())
        return sanitized.strip('-')
    
    def _extract_pod_info(self, pod) -> Dict[str, Any]:
        """Extract relevant pod information from Kubernetes API response."""
        metadata = pod.metadata
        status = pod.status
        
        return {
            "name": metadata.name,
            "namespace": metadata.namespace,
            "phase": status.phase,
            "ready": status.ready if status.ready else False,
            "restart_count": status.container_statuses[0].restart_count if status.container_statuses else 0,
            "image": status.container_statuses[0].image if status.container_statuses else None,
            "created": metadata.creation_timestamp.isoformat() if metadata.creation_timestamp else None,
            "labels": metadata.labels or {},
            "annotations": metadata.annotations or {}
        }
    
    async def execute(self, 
                     pod_name: Optional[str] = None,
                     project_path: Optional[str] = None,
                     namespace: str = "default",
                     all_ai_admin: bool = False,
                     cluster_name: Optional[str] = None,
                     **kwargs):
        """
        Get status of Kubernetes pods using Python kubernetes library.
        
        Args:
            pod_name: Name of specific pod to check (if not provided, derived from project_path)
            project_path: Path to project directory (used to derive pod name)
            namespace: Kubernetes namespace
            all_ai_admin: Get status of all ai-admin pods
        """
        try:
            # Initialize client for the specified cluster
            self._init_client(cluster_name)
            
            if all_ai_admin:
                # Get all ai-admin pods
                try:
                    pods = self.core_v1.list_namespaced_pod(
                        namespace=namespace,
                        label_selector="app=ai-admin"
                    )
                    
                    pods_info = []
                    for pod in pods.items:
                        pod_info = self._extract_pod_info(pod)
                        pods_info.append(pod_info)
                    
                    return SuccessResult(data={
                        "message": f"Found {len(pods_info)} ai-admin pods",
                        "namespace": namespace,
                        "pods": pods_info,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except ApiException as e:
                    return ErrorResult(
                        message=f"Failed to get pods: {e}",
                        code="K8S_API_ERROR",
                        details={"status": e.status, "reason": e.reason}
                    )
            
            else:
                # Get specific pod
                if not pod_name:
                    if not project_path:
                        import os
                        project_path = os.getcwd()
                    
                    project_name = self.get_project_name(project_path)
                    pod_name = f"ai-admin-{project_name}"
                
                try:
                    pod = self.core_v1.read_namespaced_pod(
                        name=pod_name,
                        namespace=namespace
                    )
                    
                    pod_info = self._extract_pod_info(pod)
                    
                    return SuccessResult(data={
                        "message": f"Pod {pod_name} status retrieved",
                        "namespace": namespace,
                        "pod": pod_info,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except ApiException as e:
                    if e.status == 404:
                        return ErrorResult(
                            message=f"Pod {pod_name} not found in namespace {namespace}",
                            code="POD_NOT_FOUND",
                            details={"status": e.status, "reason": e.reason}
                        )
                    else:
                        return ErrorResult(
                            message=f"Failed to get pod status: {e}",
                            code="K8S_API_ERROR",
                            details={"status": e.status, "reason": e.reason}
                        )
                        
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error getting pod status: {e}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            ) 