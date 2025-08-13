"""Kind cluster management command for MCP server."""

import subprocess
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class KindClusterCommand(Command):
    """Command to manage Kind Kubernetes clusters using Python library."""
    
    name = "kind_cluster"
    
    def __init__(self):
        """Initialize Kind command."""
        self.kind_path = "kind"  # Assume kind is in PATH
    
    async def execute(self, 
                     action: str = "list",
                     cluster_name: Optional[str] = None,
                     config_file: Optional[str] = None,
                     image: Optional[str] = None,
                     wait: int = 60,
                     **kwargs):
        """
        Manage Kind Kubernetes clusters.
        
        Args:
            action: Action to perform (create, delete, list, get-nodes, load-image)
            cluster_name: Name of the cluster
            config_file: Path to kind configuration file
            image: Docker image for cluster or to load
            wait: Time to wait for cluster operations (seconds)
        """
        try:
            if action == "list":
                return await self._list_clusters()
            elif action == "create":
                return await self._create_cluster(cluster_name, config_file, image, wait)
            elif action == "delete":
                return await self._delete_cluster(cluster_name)
            elif action == "get-nodes":
                return await self._get_nodes(cluster_name)
            elif action == "load-image":
                return await self._load_image(cluster_name, image)
            else:
                return ErrorResult(
                    message=f"Unknown action: {action}",
                    code="INVALID_ACTION",
                    details={"valid_actions": ["list", "create", "delete", "get-nodes", "load-image"]}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error in kind cluster operation: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )
    
    async def _list_clusters(self) -> SuccessResult:
        """List all kind clusters."""
        try:
            cmd = [self.kind_path, "get", "clusters", "--output", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to list clusters: {result.stderr}",
                    code="KIND_LIST_FAILED",
                    details={"stderr": result.stderr}
                )
            
            clusters = []
            if result.stdout.strip():
                try:
                    clusters_data = json.loads(result.stdout)
                    for cluster in clusters_data:
                        clusters.append({
                            "name": cluster.get("name"),
                            "status": cluster.get("status"),
                            "nodes": cluster.get("nodes", [])
                        })
                except json.JSONDecodeError:
                    # Fallback to simple parsing
                    cluster_names = result.stdout.strip().split('\n')
                    clusters = [{"name": name, "status": "unknown"} for name in cluster_names if name]
            
            return SuccessResult(data={
                "message": f"Found {len(clusters)} kind cluster(s)",
                "clusters": clusters,
                "count": len(clusters),
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Timeout while listing clusters",
                code="KIND_TIMEOUT",
                details={"timeout": 30}
            )
    
    async def _create_cluster(self, cluster_name: str, config_file: Optional[str], image: Optional[str], wait: int) -> SuccessResult:
        """Create a new kind cluster."""
        if not cluster_name:
            return ErrorResult(
                message="Cluster name is required for create action",
                code="MISSING_CLUSTER_NAME",
                details={}
            )
        
        try:
            cmd = [self.kind_path, "create", "cluster", "--name", cluster_name]
            
            if config_file:
                cmd.extend(["--config", config_file])
            
            if image:
                cmd.extend(["--image", image])
            
            if wait > 0:
                cmd.extend(["--wait", str(wait)])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=wait + 30)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to create cluster: {result.stderr}",
                    code="KIND_CREATE_FAILED",
                    details={
                        "stderr": result.stderr,
                        "stdout": result.stdout,
                        "command": " ".join(cmd)
                    }
                )
            
            return SuccessResult(data={
                "message": f"Successfully created kind cluster '{cluster_name}'",
                "cluster_name": cluster_name,
                "config_file": config_file,
                "image": image,
                "wait_time": wait,
                "stdout": result.stdout,
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message=f"Timeout while creating cluster '{cluster_name}'",
                code="KIND_TIMEOUT",
                details={"timeout": wait + 30, "cluster_name": cluster_name}
            )
    
    async def _delete_cluster(self, cluster_name: str) -> SuccessResult:
        """Delete a kind cluster."""
        if not cluster_name:
            return ErrorResult(
                message="Cluster name is required for delete action",
                code="MISSING_CLUSTER_NAME",
                details={}
            )
        
        try:
            cmd = [self.kind_path, "delete", "cluster", "--name", cluster_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to delete cluster: {result.stderr}",
                    code="KIND_DELETE_FAILED",
                    details={
                        "stderr": result.stderr,
                        "stdout": result.stdout,
                        "command": " ".join(cmd)
                    }
                )
            
            return SuccessResult(data={
                "message": f"Successfully deleted kind cluster '{cluster_name}'",
                "cluster_name": cluster_name,
                "stdout": result.stdout,
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message=f"Timeout while deleting cluster '{cluster_name}'",
                code="KIND_TIMEOUT",
                details={"timeout": 60, "cluster_name": cluster_name}
            )
    
    async def _get_nodes(self, cluster_name: str) -> SuccessResult:
        """Get nodes information for a cluster."""
        if not cluster_name:
            return ErrorResult(
                message="Cluster name is required for get-nodes action",
                code="MISSING_CLUSTER_NAME",
                details={}
            )
        
        try:
            cmd = [self.kind_path, "get", "nodes", "--name", cluster_name, "--output", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to get nodes: {result.stderr}",
                    code="KIND_GET_NODES_FAILED",
                    details={
                        "stderr": result.stderr,
                        "cluster_name": cluster_name
                    }
                )
            
            nodes = []
            if result.stdout.strip():
                try:
                    nodes_data = json.loads(result.stdout)
                    for node in nodes_data:
                        nodes.append({
                            "name": node.get("name"),
                            "role": node.get("role"),
                            "status": node.get("status"),
                            "internal_ip": node.get("internal_ip"),
                            "external_ip": node.get("external_ip")
                        })
                except json.JSONDecodeError:
                    # Fallback to simple parsing
                    node_names = result.stdout.strip().split('\n')
                    nodes = [{"name": name, "role": "unknown"} for name in node_names if name]
            
            return SuccessResult(data={
                "message": f"Found {len(nodes)} node(s) in cluster '{cluster_name}'",
                "cluster_name": cluster_name,
                "nodes": nodes,
                "count": len(nodes),
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message=f"Timeout while getting nodes for cluster '{cluster_name}'",
                code="KIND_TIMEOUT",
                details={"timeout": 30, "cluster_name": cluster_name}
            )
    
    async def _load_image(self, cluster_name: str, image: str) -> SuccessResult:
        """Load a Docker image into a kind cluster."""
        if not cluster_name:
            return ErrorResult(
                message="Cluster name is required for load-image action",
                code="MISSING_CLUSTER_NAME",
                details={}
            )
        
        if not image:
            return ErrorResult(
                message="Image name is required for load-image action",
                code="MISSING_IMAGE_NAME",
                details={}
            )
        
        try:
            cmd = [self.kind_path, "load", "docker-image", "--name", cluster_name, image]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minutes timeout
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to load image: {result.stderr}",
                    code="KIND_LOAD_IMAGE_FAILED",
                    details={
                        "stderr": result.stderr,
                        "stdout": result.stdout,
                        "command": " ".join(cmd)
                    }
                )
            
            return SuccessResult(data={
                "message": f"Successfully loaded image '{image}' into cluster '{cluster_name}'",
                "cluster_name": cluster_name,
                "image": image,
                "stdout": result.stdout,
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message=f"Timeout while loading image '{image}' into cluster '{cluster_name}'",
                code="KIND_TIMEOUT",
                details={"timeout": 300, "cluster_name": cluster_name, "image": image}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for kind cluster command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["list", "create", "delete", "get-nodes", "load-image"],
                    "default": "list"
                },
                "cluster_name": {
                    "type": "string",
                    "description": "Name of the cluster"
                },
                "config_file": {
                    "type": "string",
                    "description": "Path to kind configuration file"
                },
                "image": {
                    "type": "string",
                    "description": "Docker image for cluster or to load"
                },
                "wait": {
                    "type": "integer",
                    "description": "Time to wait for cluster operations (seconds)",
                    "default": 60
                }
            },
            "required": ["action"]
        } 