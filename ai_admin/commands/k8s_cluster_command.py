"""Kubernetes cluster management command for MCP server."""

from typing import Optional, Dict, Any, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.k8s_utils import get_k8s_config_manager


class K8sClusterCommand(Command):
    """Command to manage Kubernetes clusters and test connections."""
    
    name = "k8s_cluster"
    
    async def execute(self, 
                     action: str = "list",
                     cluster_name: Optional[str] = None,
                     **kwargs):
        """
        Manage Kubernetes clusters.
        
        Args:
            action: Action to perform (list, test, info, switch)
            cluster_name: Name of the cluster to work with
        """
        try:
            config_manager = get_k8s_config_manager()
            
            if action == "list":
                return await self._list_clusters(config_manager)
            elif action == "test":
                return await self._test_cluster(config_manager, cluster_name)
            elif action == "info":
                return await self._get_cluster_info(config_manager, cluster_name)
            elif action == "switch":
                return await self._switch_cluster(config_manager, cluster_name)
            else:
                return ErrorResult(
                    message=f"Unknown action: {action}",
                    code="UNKNOWN_ACTION",
                    details={"supported_actions": ["list", "test", "info", "switch"]}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error in cluster operation: {e}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )
    
    async def _list_clusters(self, config_manager) -> SuccessResult:
        """List available clusters."""
        clusters = config_manager.get_available_clusters()
        default_cluster = config_manager.default_cluster
        
        cluster_list = []
        for cluster_name in clusters:
            cluster_config = config_manager.get_cluster_config(cluster_name)
            cluster_info = {
                "name": cluster_name,
                "type": cluster_config.get("type", "unknown"),
                "host": cluster_config.get("host", "unknown"),
                "port": cluster_config.get("port", "unknown"),
                "description": cluster_config.get("description", ""),
                "is_default": cluster_name == default_cluster
            }
            cluster_list.append(cluster_info)
        
        return SuccessResult(data={
            "message": f"Found {len(cluster_list)} clusters",
            "clusters": cluster_list,
            "default_cluster": default_cluster,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _test_cluster(self, config_manager, cluster_name: Optional[str] = None) -> SuccessResult:
        """Test connection to a cluster."""
        if not cluster_name:
            cluster_name = config_manager.default_cluster
        
        try:
            result = config_manager.test_connection(cluster_name)
            
            if result["success"]:
                return SuccessResult(data={
                    "message": f"Connection to cluster '{cluster_name}' successful",
                    "cluster": cluster_name,
                    "status": "connected",
                    "api_resources_count": result.get("api_resources_count", 0),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return ErrorResult(
                    message=f"Connection to cluster '{cluster_name}' failed",
                    code="CONNECTION_FAILED",
                    details={
                        "cluster": cluster_name,
                        "error": result.get("error", "Unknown error")
                    }
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Failed to test cluster '{cluster_name}': {e}",
                code="TEST_FAILED",
                details={"cluster": cluster_name, "error": str(e)}
            )
    
    async def _get_cluster_info(self, config_manager, cluster_name: Optional[str] = None) -> SuccessResult:
        """Get detailed information about a cluster."""
        if not cluster_name:
            cluster_name = config_manager.default_cluster
        
        try:
            cluster_config = config_manager.get_cluster_config(cluster_name)
            cluster_info = config_manager.get_cluster_info(cluster_name)
            
            return SuccessResult(data={
                "message": f"Cluster information for '{cluster_name}'",
                "cluster": cluster_name,
                "config": cluster_config,
                "info": cluster_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to get cluster info for '{cluster_name}': {e}",
                code="INFO_FAILED",
                details={"cluster": cluster_name, "error": str(e)}
            )
    
    async def _switch_cluster(self, config_manager, cluster_name: str) -> SuccessResult:
        """Switch to a different cluster."""
        if not cluster_name:
            return ErrorResult(
                message="Cluster name is required for switch action",
                code="MISSING_CLUSTER_NAME",
                details={}
            )
        
        try:
            # Test the connection first
            result = config_manager.test_connection(cluster_name)
            
            if result["success"]:
                # Update default cluster
                config_manager.default_cluster = cluster_name
                
                return SuccessResult(data={
                    "message": f"Successfully switched to cluster '{cluster_name}'",
                    "cluster": cluster_name,
                    "status": "switched",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return ErrorResult(
                    message=f"Cannot switch to cluster '{cluster_name}': connection failed",
                    code="SWITCH_FAILED",
                    details={
                        "cluster": cluster_name,
                        "error": result.get("error", "Unknown error")
                    }
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Failed to switch to cluster '{cluster_name}': {e}",
                code="SWITCH_FAILED",
                details={"cluster": cluster_name, "error": str(e)}
            ) 