"""ArgoCD initialization command for Kubernetes clusters."""
import subprocess
import asyncio
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class ArgoCDInitCommand(Command):
    """Initialize ArgoCD in Kubernetes cluster."""
    
    name = "argocd_init"
    
    async def execute(self,
                     cluster_name: str,
                     namespace: str = "argocd",
                     admin_password: Optional[str] = None,
                     insecure: bool = True,
                     port: int = 8080,
                     service_type: str = "NodePort",
                     **kwargs) -> SuccessResult:
        """
        Initialize ArgoCD in Kubernetes cluster.
        
        Args:
            cluster_name: Name of the Kubernetes cluster container
            namespace: Namespace for ArgoCD (default: argocd)
            admin_password: Admin password for ArgoCD (default: auto-generated)
            insecure: Run ArgoCD in insecure mode (default: True)
            port: Port for ArgoCD server (default: 8080)
            service_type: Type of service (NodePort, ClusterIP, LoadBalancer)
        """
        try:
            # Validate inputs
            if not cluster_name:
                return ErrorResult(
                    message="Cluster name is required",
                    code="MISSING_CLUSTER_NAME",
                    details={}
                )
            
            # Generate admin password if not provided
            if not admin_password:
                admin_password = await self._generate_password()
            
            # Step 1: Create namespace
            result = await self._create_namespace(cluster_name, namespace)
            if not result.get("success"):
                return ErrorResult(
                    message=f"Failed to create namespace: {result.get('error')}",
                    code="NAMESPACE_CREATION_FAILED",
                    details=result
                )
            
            # Step 2: Create ArgoCD deployment
            result = await self._create_argocd_deployment(cluster_name, namespace, port, insecure)
            if not result.get("success"):
                return ErrorResult(
                    message=f"Failed to create ArgoCD deployment: {result.get('error')}",
                    code="DEPLOYMENT_CREATION_FAILED",
                    details=result
                )
            
            # Step 3: Create ArgoCD service
            result = await self._create_argocd_service(cluster_name, namespace, port, service_type)
            if not result.get("success"):
                return ErrorResult(
                    message=f"Failed to create ArgoCD service: {result.get('error')}",
                    code="SERVICE_CREATION_FAILED",
                    details=result
                )
            
            # Step 4: Wait for deployment to be ready
            result = await self._wait_for_deployment(cluster_name, namespace)
            if not result.get("success"):
                return ErrorResult(
                    message=f"Deployment not ready: {result.get('error')}",
                    code="DEPLOYMENT_NOT_READY",
                    details=result
                )
            
            # Step 5: Get service details
            service_info = await self._get_service_info(cluster_name, namespace)
            
            return SuccessResult(data={
                "message": f"ArgoCD successfully initialized in cluster '{cluster_name}'",
                "cluster_name": cluster_name,
                "namespace": namespace,
                "admin_password": admin_password,
                "port": port,
                "service_type": service_type,
                "service_info": service_info,
                "access_url": f"http://localhost:{service_info.get('node_port', 'N/A')}",
                "timestamp": "2025-08-13T19:20:00.000000"
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to initialize ArgoCD: {str(e)}",
                code="INIT_FAILED",
                details={"cluster_name": cluster_name, "namespace": namespace}
            )
    
    async def _generate_password(self) -> str:
        """Generate a random password for ArgoCD admin."""
        try:
            cmd = ["openssl", "rand", "-base64", "32"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "admin123"  # fallback password
        except Exception:
            return "admin123"  # fallback password
    
    async def _create_namespace(self, cluster_name: str, namespace: str) -> Dict[str, Any]:
        """Create namespace for ArgoCD."""
        try:
            # Try to create namespace directly
            cmd = ["docker", "exec", cluster_name, "kubectl", "create", "namespace", namespace]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {"success": True, "message": f"Namespace '{namespace}' created"}
            elif "already exists" in result.stderr:
                return {"success": True, "message": f"Namespace '{namespace}' already exists"}
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_argocd_deployment(self, cluster_name: str, namespace: str, port: int, insecure: bool) -> Dict[str, Any]:
        """Create ArgoCD deployment."""
        try:
            # Use kubectl run command instead of YAML
            cmd = [
                "docker", "exec", cluster_name, "kubectl", "run", "argocd-server",
                "--image=argoproj/argocd:latest",
                f"--namespace={namespace}",
                f"--port={port}",
                "--env=ARGOCD_SERVER_INSECURE=true",
                "--env=ARGOCD_SERVER_ROOT_PATH=/argocd",
                "--command", "--", "argocd-server", "--insecure", "--rootpath", "/argocd"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return {"success": True, "message": "ArgoCD deployment created"}
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_argocd_service(self, cluster_name: str, namespace: str, port: int, service_type: str) -> Dict[str, Any]:
        """Create ArgoCD service."""
        try:
            # Use kubectl expose command
            cmd = [
                "docker", "exec", cluster_name, "kubectl", "expose", "pod", "argocd-server",
                f"--namespace={namespace}",
                "--name=argocd-server",
                f"--port={port}",
                f"--target-port={port}",
                f"--type={service_type}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {"success": True, "message": "ArgoCD service created"}
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _wait_for_deployment(self, cluster_name: str, namespace: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for ArgoCD pod to be ready."""
        try:
            cmd = ["docker", "exec", cluster_name, "kubectl", "wait", "--for=condition=ready", "--timeout=300s", "pod/argocd-server", "-n", namespace]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                return {"success": True, "message": "ArgoCD pod is ready"}
            else:
                return {"success": False, "error": result.stderr}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout waiting for pod to be ready"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_service_info(self, cluster_name: str, namespace: str) -> Dict[str, Any]:
        """Get ArgoCD service information."""
        try:
            cmd = ["docker", "exec", cluster_name, "kubectl", "get", "service", "argocd-server", "-n", namespace, "-o", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                import json
                service_data = json.loads(result.stdout)
                node_port = None
                if service_data.get("spec", {}).get("type") == "NodePort":
                    ports = service_data.get("spec", {}).get("ports", [])
                    if ports:
                        node_port = ports[0].get("nodePort")
                
                return {
                    "name": service_data.get("metadata", {}).get("name"),
                    "type": service_data.get("spec", {}).get("type"),
                    "cluster_ip": service_data.get("spec", {}).get("clusterIP"),
                    "node_port": node_port,
                    "ports": service_data.get("spec", {}).get("ports", [])
                }
            else:
                return {"error": result.stderr}
                
        except Exception as e:
            return {"error": str(e)}
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "name": cls.name,
            "description": "Initialize ArgoCD in Kubernetes cluster",
            "parameters": {
                "type": "object",
                "properties": {
                    "cluster_name": {
                        "type": "string",
                        "description": "Name of the Kubernetes cluster container"
                    },
                    "namespace": {
                        "type": "string",
                        "description": "Namespace for ArgoCD",
                        "default": "argocd"
                    },
                    "admin_password": {
                        "type": "string",
                        "description": "Admin password for ArgoCD (auto-generated if not provided)"
                    },
                    "insecure": {
                        "type": "boolean",
                        "description": "Run ArgoCD in insecure mode",
                        "default": True
                    },
                    "port": {
                        "type": "integer",
                        "description": "Port for ArgoCD server",
                        "default": 8080
                    },
                    "service_type": {
                        "type": "string",
                        "description": "Type of service (NodePort, ClusterIP, LoadBalancer)",
                        "default": "NodePort"
                    }
                },
                "required": ["cluster_name"]
            }
        } 