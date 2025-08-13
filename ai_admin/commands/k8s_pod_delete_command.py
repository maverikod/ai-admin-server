"""Kubernetes pod delete command for MCP server."""

import re
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class K8sPodDeleteCommand(Command):
    """Command to delete Kubernetes pods using Python kubernetes library."""
    
    name = "k8s_pod_delete"
    
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
                     pod_name: Optional[str] = None,
                     project_path: Optional[str] = None,
                     namespace: str = "default",
                     force: bool = False,
                     **kwargs):
        """
        Delete Kubernetes pod using Python kubernetes library.
        
        Args:
            pod_name: Name of pod to delete (if not provided, derived from project_path)
            project_path: Path to project directory (used to derive pod name)
            namespace: Kubernetes namespace
            force: Force deletion even if pod is running
        """
        try:
            if not pod_name:
                if not project_path:
                    import os
                    project_path = os.getcwd()
                
                project_name = self.get_project_name(project_path)
                pod_name = f"ai-admin-{project_name}"
            
            # Check if pod exists
            try:
                pod = self.core_v1.read_namespaced_pod(
                    name=pod_name,
                    namespace=namespace
                )
            except ApiException as e:
                if e.status == 404:
                    return ErrorResult(
                        message=f"Pod {pod_name} not found in namespace {namespace}",
                        code="POD_NOT_FOUND",
                        details={"status": e.status, "reason": e.reason}
                    )
                else:
                    return ErrorResult(
                        message=f"Failed to check pod existence: {e}",
                        code="K8S_API_ERROR",
                        details={"status": e.status, "reason": e.reason}
                    )
            
            # Delete the pod
            try:
                delete_options = client.V1DeleteOptions()
                if force:
                    delete_options.grace_period_seconds = 0
                
                self.core_v1.delete_namespaced_pod(
                    name=pod_name,
                    namespace=namespace,
                    body=delete_options
                )
                
                return SuccessResult(data={
                    "message": f"Pod {pod_name} deleted successfully",
                    "namespace": namespace,
                    "pod_name": pod_name,
                    "force": force,
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                return ErrorResult(
                    message=f"Failed to delete pod: {e}",
                    code="K8S_API_ERROR",
                    details={"status": e.status, "reason": e.reason}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error deleting pod: {e}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for k8s pod delete command parameters."""
        return {
            "type": "object",
            "properties": {
                "pod_name": {
                    "type": "string",
                    "description": "Name of pod to delete (if not provided, derived from project_path)"
                },
                "project_path": {
                    "type": "string",
                    "description": "Path to project directory (used to derive pod name)"
                },
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace",
                    "default": "default"
                },
                "force": {
                    "type": "boolean",
                    "description": "Force deletion even if pod is running",
                    "default": False
                }
            }
        } 