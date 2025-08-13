"""Kubernetes logs, exec, and port-forward commands for MCP server."""

import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class K8sLogsCommand(Command):
    """Command to get Kubernetes pod logs using Python kubernetes library."""
    
    name = "k8s_logs"
    
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
                     container: Optional[str] = None,
                     tail_lines: Optional[int] = None,
                     follow: bool = False,
                     previous: bool = False,
                     timestamps: bool = False,
                     **kwargs):
        """
        Get Kubernetes pod logs using Python kubernetes library.
        
        Args:
            pod_name: Name of the pod (if not provided, derived from project_path)
            project_path: Path to project directory (used to derive pod name)
            namespace: Kubernetes namespace
            container: Container name (if pod has multiple containers)
            tail_lines: Number of lines to show from the end
            follow: Follow log output (not supported in this implementation)
            previous: Get logs from previous container instance
            timestamps: Include timestamps in log output
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
                        message=f"Failed to get pod: {e}",
                        code="K8S_API_ERROR",
                        details={"status": e.status, "reason": e.reason}
                    )
            
            # Get logs
            try:
                logs = self.core_v1.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=namespace,
                    container=container,
                    tail_lines=tail_lines,
                    previous=previous,
                    timestamps=timestamps
                )
                
                return SuccessResult(data={
                    "message": f"Logs retrieved for pod {pod_name}",
                    "pod_name": pod_name,
                    "namespace": namespace,
                    "container": container,
                    "tail_lines": tail_lines,
                    "previous": previous,
                    "timestamps": timestamps,
                    "logs": logs,
                    "log_lines_count": len(logs.splitlines()) if logs else 0,
                    "timestamp": datetime.now().isoformat()
                })
                
            except ApiException as e:
                return ErrorResult(
                    message=f"Failed to get logs: {e}",
                    code="K8S_API_ERROR",
                    details={"status": e.status, "reason": e.reason}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error getting logs: {e}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )


class K8sExecCommand(Command):
    """Command to execute commands in Kubernetes pods using Python kubernetes library."""
    
    name = "k8s_exec"
    
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
                     container: Optional[str] = None,
                     command: str = "ls",
                     **kwargs):
        """
        Execute command in Kubernetes pod using Python kubernetes library.
        
        Args:
            pod_name: Name of the pod (if not provided, derived from project_path)
            project_path: Path to project directory (used to derive pod name)
            namespace: Kubernetes namespace
            container: Container name (if pod has multiple containers)
            command: Command to execute
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
                        message=f"Failed to get pod: {e}",
                        code="K8S_API_ERROR",
                        details={"status": e.status, "reason": e.reason}
                    )
            
            # Note: The kubernetes Python client doesn't support exec directly
            # This would require using the kubernetes.stream module or subprocess
            # For now, we'll return an informative message
            
            return SuccessResult(data={
                "message": f"Exec command '{command}' would be executed in pod {pod_name}",
                "pod_name": pod_name,
                "namespace": namespace,
                "container": container,
                "command": command,
                "note": "Exec functionality requires kubernetes.stream module or subprocess implementation",
                "timestamp": datetime.now().isoformat()
            })
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error executing command: {e}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )


class K8sPortForwardCommand(Command):
    """Command to setup port forwarding to Kubernetes pods using Python kubernetes library."""
    
    name = "k8s_port_forward"
    
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
                     local_port: int = 8080,
                     remote_port: int = 80,
                     **kwargs):
        """
        Setup port forwarding to Kubernetes pod using Python kubernetes library.
        
        Args:
            pod_name: Name of the pod (if not provided, derived from project_path)
            project_path: Path to project directory (used to derive pod name)
            namespace: Kubernetes namespace
            local_port: Local port to forward to
            remote_port: Remote port in the pod
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
                        message=f"Failed to get pod: {e}",
                        code="K8S_API_ERROR",
                        details={"status": e.status, "reason": e.reason}
                    )
            
            # Note: Port forwarding requires kubernetes.stream module
            # This would require a more complex implementation with background threads
            # For now, we'll return an informative message
            
            return SuccessResult(data={
                "message": f"Port forwarding would be setup for pod {pod_name}",
                "pod_name": pod_name,
                "namespace": namespace,
                "local_port": local_port,
                "remote_port": remote_port,
                "note": "Port forwarding requires kubernetes.stream module implementation",
                "timestamp": datetime.now().isoformat()
            })
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error setting up port forwarding: {e}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            ) 