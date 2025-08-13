"""Kubernetes cluster setup command with certificate management for MCP server."""

import os
import subprocess
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import tempfile

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class K8sClusterSetupCommand(Command):
    """Command to setup complete Kubernetes clusters with certificate management."""
    
    name = "k8s_cluster_setup"
    
    def __init__(self):
        """Initialize cluster setup command."""
        self.certs_base_dir = "./certificates"
        self.kubeconfigs_dir = "./kubeconfigs"
        self.clusters_dir = "./clusters"
    
    async def execute(self,
                     action: str = "create",
                     cluster_name: str = "my-cluster",
                     cluster_type: str = "kind",
                     cluster_config: Optional[Dict[str, Any]] = None,
                     cert_config: Optional[Dict[str, Any]] = None,
                     admin_user: str = "kubernetes-admin",
                     admin_organization: str = "system:masters",
                     server_url: Optional[str] = None,
                     namespace: str = "default",
                     wait_timeout: int = 300,
                     **kwargs):
        """
        Setup complete Kubernetes clusters with certificate management.
        
        Args:
            action: Action to perform (create, delete, status, test, upgrade)
            cluster_name: Name of the Kubernetes cluster
            cluster_type: Type of cluster (kind, k3s, minikube, docker)
            cluster_config: Additional cluster configuration
            cert_config: Certificate configuration
            admin_user: Admin user name for RBAC
            admin_organization: Admin organization for RBAC
            server_url: Kubernetes API server URL
            namespace: Default namespace
            wait_timeout: Timeout for cluster operations (seconds)
        """
        try:
            if action == "create":
                return await self._create_complete_cluster(
                    cluster_name, cluster_type, cluster_config, cert_config,
                    admin_user, admin_organization, server_url, namespace, wait_timeout
                )
            elif action == "delete":
                return await self._delete_cluster(cluster_name, cluster_type)
            elif action == "status":
                return await self._get_cluster_status(cluster_name, cluster_type)
            elif action == "test":
                return await self._test_cluster_connection(cluster_name)
            elif action == "upgrade":
                return await self._upgrade_cluster(cluster_name, cluster_type, cluster_config)
            else:
                return ErrorResult(
                    message=f"Unknown action: {action}",
                    code="INVALID_ACTION",
                    details={"valid_actions": ["create", "delete", "status", "test", "upgrade"]}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Failed to setup cluster: {str(e)}",
                code="CLUSTER_SETUP_FAILED",
                details={"exception": str(e)}
            )
    
    async def _create_complete_cluster(self, cluster_name: str, cluster_type: str,
                                     cluster_config: Optional[Dict[str, Any]],
                                     cert_config: Optional[Dict[str, Any]],
                                     admin_user: str, admin_organization: str,
                                     server_url: Optional[str], namespace: str,
                                     wait_timeout: int) -> SuccessResult:
        """Create a complete Kubernetes cluster with certificates."""
        try:
            # Step 1: Create cluster
            cluster_result = await self._create_cluster(cluster_name, cluster_type, cluster_config, wait_timeout)
            if not cluster_result.success:
                return cluster_result
            
            # Step 2: Setup certificates
            cert_result = await self._setup_cluster_certificates(
                cluster_name, admin_user, admin_organization, cert_config
            )
            if not cert_result.success:
                return cert_result
            
            # Step 3: Create client configuration
            config_result = await self._create_client_configuration(
                cluster_name, admin_user, server_url
            )
            if not config_result.success:
                return config_result
            
            # Step 4: Test cluster connection
            test_result = await self._test_cluster_connection(cluster_name)
            if not test_result.success:
                return test_result
            
            # Step 5: Setup initial resources
            resources_result = await self._setup_initial_resources(cluster_name, namespace)
            
            return SuccessResult(data={
                "message": f"Complete Kubernetes cluster '{cluster_name}' created successfully",
                "cluster_name": cluster_name,
                "cluster_type": cluster_type,
                "admin_user": admin_user,
                "server_url": server_url or f"https://localhost:6443",
                "namespace": namespace,
                "certificates_created": cert_result.data.get("certificates_created", []),
                "kubeconfig_path": config_result.data.get("kubeconfig_path"),
                "connection_test": test_result.data,
                "initial_resources": resources_result.data if resources_result.success else None,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create complete cluster: {str(e)}",
                code="COMPLETE_CLUSTER_CREATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _create_cluster(self, cluster_name: str, cluster_type: str,
                            cluster_config: Optional[Dict[str, Any]], wait_timeout: int) -> SuccessResult:
        """Create the base Kubernetes cluster."""
        try:
            if cluster_type == "kind":
                return await self._create_kind_cluster(cluster_name, cluster_config, wait_timeout)
            elif cluster_type == "k3s":
                return await self._create_k3s_cluster(cluster_name, cluster_config, wait_timeout)
            elif cluster_type == "minikube":
                return await self._create_minikube_cluster(cluster_name, cluster_config, wait_timeout)
            else:
                return ErrorResult(
                    message=f"Unsupported cluster type: {cluster_type}",
                    code="UNSUPPORTED_CLUSTER_TYPE",
                    details={"supported_types": ["kind", "k3s", "minikube"]}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create cluster: {str(e)}",
                code="CLUSTER_CREATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _create_kind_cluster(self, cluster_name: str, cluster_config: Optional[Dict[str, Any]], wait_timeout: int) -> SuccessResult:
        """Create a Kind Kubernetes cluster."""
        try:
            # Create kind configuration
            kind_config = self._create_kind_config(cluster_name, cluster_config)
            config_path = os.path.join(self.clusters_dir, cluster_name, "kind-config.yaml")
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                yaml.dump(kind_config, f, default_flow_style=False)
            
            # Create cluster
            cmd = ["kind", "create", "cluster", "--name", cluster_name, "--config", config_path, "--wait", str(wait_timeout)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=wait_timeout + 60)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to create Kind cluster: {result.stderr}",
                    code="KIND_CREATION_FAILED",
                    details={"stderr": result.stderr, "stdout": result.stdout}
                )
            
            return SuccessResult(data={
                "message": f"Kind cluster '{cluster_name}' created successfully",
                "cluster_name": cluster_name,
                "cluster_type": "kind",
                "config_path": config_path,
                "stdout": result.stdout
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message=f"Timeout creating Kind cluster '{cluster_name}'",
                code="KIND_TIMEOUT",
                details={"timeout": wait_timeout + 60}
            )
    
    async def _create_k3s_cluster(self, cluster_name: str, cluster_config: Optional[Dict[str, Any]], wait_timeout: int) -> SuccessResult:
        """Create a K3s Kubernetes cluster."""
        try:
            # Create Docker container for K3s
            container_name = f"k3s-{cluster_name}"
            port = cluster_config.get("port", 6443) if cluster_config else 6443
            
            # Create K3s server container
            cmd = [
                "docker", "run", "-d", "--name", container_name,
                "-p", f"{port}:6443",
                "-e", "K3S_TOKEN=mysecret",
                "--privileged",
                "rancher/k3s:latest", "server", "--disable", "traefik"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to create K3s container: {result.stderr}",
                    code="K3S_CREATION_FAILED",
                    details={"stderr": result.stderr}
                )
            
            # Wait for K3s to be ready
            await self._wait_for_k3s_ready(container_name, wait_timeout)
            
            return SuccessResult(data={
                "message": f"K3s cluster '{cluster_name}' created successfully",
                "cluster_name": cluster_name,
                "cluster_type": "k3s",
                "container_name": container_name,
                "port": port
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create K3s cluster: {str(e)}",
                code="K3S_CREATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _create_minikube_cluster(self, cluster_name: str, cluster_config: Optional[Dict[str, Any]], wait_timeout: int) -> SuccessResult:
        """Create a Minikube Kubernetes cluster."""
        try:
            # Create minikube cluster
            cmd = ["minikube", "start", "--profile", cluster_name, "--wait", "all", "--timeout", str(wait_timeout)]
            
            if cluster_config:
                if cluster_config.get("driver"):
                    cmd.extend(["--driver", cluster_config["driver"]])
                if cluster_config.get("cpus"):
                    cmd.extend(["--cpus", str(cluster_config["cpus"])])
                if cluster_config.get("memory"):
                    cmd.extend(["--memory", cluster_config["memory"]])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=wait_timeout + 60)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to create Minikube cluster: {result.stderr}",
                    code="MINIKUBE_CREATION_FAILED",
                    details={"stderr": result.stderr, "stdout": result.stdout}
                )
            
            return SuccessResult(data={
                "message": f"Minikube cluster '{cluster_name}' created successfully",
                "cluster_name": cluster_name,
                "cluster_type": "minikube",
                "stdout": result.stdout
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message=f"Timeout creating Minikube cluster '{cluster_name}'",
                code="MINIKUBE_TIMEOUT",
                details={"timeout": wait_timeout + 60}
            )
    
    async def _setup_cluster_certificates(self, cluster_name: str, admin_user: str,
                                        admin_organization: str, cert_config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Setup certificates for the cluster."""
        try:
            # Import certificates command
            from ai_admin.commands.k8s_certificates_command import K8sCertificatesCommand
            cert_cmd = K8sCertificatesCommand()
            
            # Setup cluster certificates
            result = await cert_cmd.execute(
                action="setup_cluster",
                cluster_name=cluster_name,
                common_name=admin_user,
                organization=admin_organization,
                **cert_config or {}
            )
            
            return result
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to setup cluster certificates: {str(e)}",
                code="CERT_SETUP_FAILED",
                details={"exception": str(e)}
            )
    
    async def _create_client_configuration(self, cluster_name: str, admin_user: str,
                                         server_url: Optional[str]) -> SuccessResult:
        """Create client configuration (kubeconfig) for the cluster."""
        try:
            # Import certificates command
            from ai_admin.commands.k8s_certificates_command import K8sCertificatesCommand
            cert_cmd = K8sCertificatesCommand()
            
            # Create client config
            result = await cert_cmd.execute(
                action="create_client_config",
                cluster_name=cluster_name,
                common_name=admin_user,
                organization="system:masters",
                server_url=server_url
            )
            
            return result
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create client configuration: {str(e)}",
                code="CLIENT_CONFIG_FAILED",
                details={"exception": str(e)}
            )
    
    async def _test_cluster_connection(self, cluster_name: str) -> SuccessResult:
        """Test connection to the cluster using Python kubernetes API."""
        try:
            # Get kubeconfig path
            kubeconfig_path = os.path.join(self.kubeconfigs_dir, cluster_name, "kubeconfig.yaml")
            
            if not os.path.exists(kubeconfig_path):
                return ErrorResult(
                    message=f"Kubeconfig not found: {kubeconfig_path}",
                    code="KUBECONFIG_NOT_FOUND",
                    details={"kubeconfig_path": kubeconfig_path}
                )
            
            # Load kubernetes configuration
            from kubernetes import client, config
            config.load_kube_config(config_file=kubeconfig_path)
            
            # Test cluster connection using Python API
            core_v1 = client.CoreV1Api()
            
            try:
                # Get API resources to test connection
                api_resources = core_v1.get_api_resources()
                
                # Get cluster nodes
                nodes = core_v1.list_node()
                nodes_info = []
                
                for node in nodes.items:
                    # Get node status
                    status = "Unknown"
                    if node.status.conditions:
                        for condition in node.status.conditions:
                            if condition.type == "Ready":
                                status = condition.status
                                break
                    
                    nodes_info.append({
                        "name": node.metadata.name,
                        "status": status,
                        "version": node.status.node_info.kubelet_version if node.status.node_info else "Unknown"
                    })
                
                return SuccessResult(data={
                    "message": f"Successfully connected to cluster '{cluster_name}'",
                    "cluster_name": cluster_name,
                    "api_resources_count": len(api_resources.resources) if api_resources.resources else 0,
                    "nodes": nodes_info,
                    "node_count": len(nodes_info)
                })
                
            except Exception as api_error:
                return ErrorResult(
                    message=f"Failed to connect to cluster API: {str(api_error)}",
                    code="CLUSTER_API_CONNECTION_FAILED",
                    details={"exception": str(api_error)}
                )
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to test cluster connection: {str(e)}",
                code="CONNECTION_TEST_FAILED",
                details={"exception": str(e)}
            )
    
    async def _setup_initial_resources(self, cluster_name: str, namespace: str) -> SuccessResult:
        """Setup initial resources in the cluster using Python kubernetes API."""
        try:
            kubeconfig_path = os.path.join(self.kubeconfigs_dir, cluster_name, "kubeconfig.yaml")
            
            # Load kubernetes configuration
            from kubernetes import client, config
            config.load_kube_config(config_file=kubeconfig_path)
            
            core_v1 = client.CoreV1Api()
            rbac_v1 = client.RbacAuthorizationV1Api()
            
            resources_created = []
            
            # Create namespace if not default
            if namespace != "default":
                try:
                    namespace_obj = client.V1Namespace(
                        metadata=client.V1ObjectMeta(name=namespace)
                    )
                    core_v1.create_namespace(namespace_obj)
                    resources_created.append(f"namespace:{namespace}")
                except Exception as e:
                    # Namespace might already exist
                    pass
            
            # Create basic RBAC resources
            rbac_resources = self._create_basic_rbac_resources(namespace)
            
            for resource_name, resource_yaml in rbac_resources.items():
                try:
                    if resource_name == "cluster-admin":
                        # Create ClusterRoleBinding
                        role_binding = client.V1ClusterRoleBinding(
                            metadata=client.V1ObjectMeta(name="cluster-admin-binding"),
                            role_ref=client.V1RoleRef(
                                api_group="rbac.authorization.k8s.io",
                                kind="ClusterRole",
                                name="cluster-admin"
                            ),
                            subjects=[
                                client.V1Subject(
                                    kind="User",
                                    name="kubernetes-admin",
                                    api_group="rbac.authorization.k8s.io"
                                )
                            ]
                        )
                        rbac_v1.create_cluster_role_binding(role_binding)
                        resources_created.append(resource_name)
                        
                    elif resource_name == "namespace-admin":
                        # Create RoleBinding
                        role_binding = client.V1RoleBinding(
                            metadata=client.V1ObjectMeta(
                                name="namespace-admin-binding",
                                namespace=namespace
                            ),
                            role_ref=client.V1RoleRef(
                                api_group="rbac.authorization.k8s.io",
                                kind="ClusterRole",
                                name="admin"
                            ),
                            subjects=[
                                client.V1Subject(
                                    kind="User",
                                    name="kubernetes-admin",
                                    api_group="rbac.authorization.k8s.io"
                                )
                            ]
                        )
                        rbac_v1.create_namespaced_role_binding(namespace, role_binding)
                        resources_created.append(resource_name)
                        
                except Exception as e:
                    # Resource might already exist
                    pass
            
            return SuccessResult(data={
                "message": f"Initial resources created for cluster '{cluster_name}'",
                "cluster_name": cluster_name,
                "namespace": namespace,
                "resources_created": resources_created
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to setup initial resources: {str(e)}",
                code="RESOURCES_SETUP_FAILED",
                details={"exception": str(e)}
            )
    
    async def _delete_cluster(self, cluster_name: str, cluster_type: str) -> SuccessResult:
        """Delete a Kubernetes cluster."""
        try:
            if cluster_type == "kind":
                cmd = ["kind", "delete", "cluster", "--name", cluster_name]
            elif cluster_type == "k3s":
                container_name = f"k3s-{cluster_name}"
                cmd = ["docker", "rm", "-f", container_name]
            elif cluster_type == "minikube":
                cmd = ["minikube", "delete", "--profile", cluster_name]
            else:
                return ErrorResult(
                    message=f"Unsupported cluster type for deletion: {cluster_type}",
                    code="UNSUPPORTED_CLUSTER_TYPE",
                    details={"supported_types": ["kind", "k3s", "minikube"]}
                )
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to delete cluster: {result.stderr}",
                    code="CLUSTER_DELETION_FAILED",
                    details={"stderr": result.stderr}
                )
            
            # Clean up certificates and configs
            self._cleanup_cluster_resources(cluster_name)
            
            return SuccessResult(data={
                "message": f"Cluster '{cluster_name}' deleted successfully",
                "cluster_name": cluster_name,
                "cluster_type": cluster_type
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to delete cluster: {str(e)}",
                code="CLUSTER_DELETION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _get_cluster_status(self, cluster_name: str, cluster_type: str) -> SuccessResult:
        """Get status of a Kubernetes cluster."""
        try:
            if cluster_type == "kind":
                cmd = ["kind", "get", "clusters"]
            elif cluster_type == "k3s":
                container_name = f"k3s-{cluster_name}"
                cmd = ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"]
            elif cluster_type == "minikube":
                cmd = ["minikube", "profile", "list"]
            else:
                return ErrorResult(
                    message=f"Unsupported cluster type: {cluster_type}",
                    code="UNSUPPORTED_CLUSTER_TYPE",
                    details={"supported_types": ["kind", "k3s", "minikube"]}
                )
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to get cluster status: {result.stderr}",
                    code="STATUS_CHECK_FAILED",
                    details={"stderr": result.stderr}
                )
            
            # Check if cluster exists
            cluster_exists = cluster_name in result.stdout
            
            status_info = {
                "cluster_name": cluster_name,
                "cluster_type": cluster_type,
                "exists": cluster_exists,
                "status": "running" if cluster_exists else "not_found"
            }
            
            if cluster_exists:
                # Test connection if cluster exists
                connection_test = await self._test_cluster_connection(cluster_name)
                if connection_test.success:
                    status_info.update(connection_test.data)
            
            return SuccessResult(data=status_info)
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to get cluster status: {str(e)}",
                code="STATUS_CHECK_FAILED",
                details={"exception": str(e)}
            )
    
    async def _upgrade_cluster(self, cluster_name: str, cluster_type: str,
                             cluster_config: Optional[Dict[str, Any]]) -> SuccessResult:
        """Upgrade a Kubernetes cluster."""
        try:
            if cluster_type == "kind":
                # Kind doesn't support direct upgrades, need to recreate
                return ErrorResult(
                    message="Kind clusters require recreation for upgrades",
                    code="UPGRADE_NOT_SUPPORTED",
                    details={"cluster_type": "kind"}
                )
            elif cluster_type == "k3s":
                container_name = f"k3s-{cluster_name}"
                # Pull latest image and restart container
                subprocess.run(["docker", "pull", "rancher/k3s:latest"], check=True)
                subprocess.run(["docker", "restart", container_name], check=True)
            elif cluster_type == "minikube":
                cmd = ["minikube", "start", "--profile", cluster_name, "--kubernetes-version", "latest"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    return ErrorResult(
                        message=f"Failed to upgrade Minikube cluster: {result.stderr}",
                        code="UPGRADE_FAILED",
                        details={"stderr": result.stderr}
                    )
            else:
                return ErrorResult(
                    message=f"Unsupported cluster type for upgrade: {cluster_type}",
                    code="UNSUPPORTED_CLUSTER_TYPE",
                    details={"supported_types": ["k3s", "minikube"]}
                )
            
            return SuccessResult(data={
                "message": f"Cluster '{cluster_name}' upgraded successfully",
                "cluster_name": cluster_name,
                "cluster_type": cluster_type
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to upgrade cluster: {str(e)}",
                code="UPGRADE_FAILED",
                details={"exception": str(e)}
            )
    
    def _create_kind_config(self, cluster_name: str, cluster_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create Kind cluster configuration."""
        config = {
            "kind": "Cluster",
            "apiVersion": "kind.x-k8s.io/v1alpha4",
            "name": cluster_name,
            "nodes": [
                {
                    "role": "control-plane",
                    "extraPortMappings": [
                        {"containerPort": 6443, "hostPort": 6443, "protocol": "TCP"}
                    ]
                }
            ]
        }
        
        if cluster_config:
            if cluster_config.get("workers"):
                for i in range(cluster_config["workers"]):
                    config["nodes"].append({"role": "worker"})
            
            if cluster_config.get("kubernetes_version"):
                config["nodes"][0]["image"] = f"kindest/node:v{cluster_config['kubernetes_version']}"
        
        return config
    
    async def _wait_for_k3s_ready(self, container_name: str, timeout: int):
        """Wait for K3s container to be ready."""
        import asyncio
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            try:
                cmd = ["docker", "exec", container_name, "kubectl", "get", "nodes"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and "Ready" in result.stdout:
                    return
                    
            except subprocess.TimeoutExpired:
                pass
            
            await asyncio.sleep(5)
        
        raise TimeoutError(f"K3s container {container_name} not ready within {timeout} seconds")
    
    def _create_basic_rbac_resources(self, namespace: str) -> Dict[str, Any]:
        """Create basic RBAC resources for the cluster."""
        return {
            "cluster-admin": {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "ClusterRoleBinding",
                "metadata": {"name": "cluster-admin-binding"},
                "roleRef": {
                    "apiGroup": "rbac.authorization.k8s.io",
                    "kind": "ClusterRole",
                    "name": "cluster-admin"
                },
                "subjects": [
                    {
                        "kind": "User",
                        "name": "kubernetes-admin",
                        "apiGroup": "rbac.authorization.k8s.io"
                    }
                ]
            },
            "namespace-admin": {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "RoleBinding",
                "metadata": {
                    "name": "namespace-admin-binding",
                    "namespace": namespace
                },
                "roleRef": {
                    "apiGroup": "rbac.authorization.k8s.io",
                    "kind": "ClusterRole",
                    "name": "admin"
                },
                "subjects": [
                    {
                        "kind": "User",
                        "name": "kubernetes-admin",
                        "apiGroup": "rbac.authorization.k8s.io"
                    }
                ]
            }
        }
    
    def _cleanup_cluster_resources(self, cluster_name: str):
        """Clean up cluster resources (certificates, configs, etc.)."""
        try:
            # Remove certificates
            certs_dir = os.path.join(self.certs_base_dir, cluster_name)
            if os.path.exists(certs_dir):
                import shutil
                shutil.rmtree(certs_dir)
            
            # Remove kubeconfig
            kubeconfig_dir = os.path.join(self.kubeconfigs_dir, cluster_name)
            if os.path.exists(kubeconfig_dir):
                import shutil
                shutil.rmtree(kubeconfig_dir)
            
            # Remove cluster config
            cluster_dir = os.path.join(self.clusters_dir, cluster_name)
            if os.path.exists(cluster_dir):
                import shutil
                shutil.rmtree(cluster_dir)
                
        except Exception as e:
            print(f"Warning: Failed to cleanup cluster resources: {e}")
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for k8s cluster setup command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["create", "delete", "status", "test", "upgrade"],
                    "default": "create"
                },
                "cluster_name": {
                    "type": "string",
                    "description": "Name of the Kubernetes cluster",
                    "default": "my-cluster"
                },
                "cluster_type": {
                    "type": "string",
                    "description": "Type of cluster",
                    "enum": ["kind", "k3s", "minikube"],
                    "default": "kind"
                },
                "admin_user": {
                    "type": "string",
                    "description": "Admin user name for RBAC",
                    "default": "kubernetes-admin"
                },
                "admin_organization": {
                    "type": "string",
                    "description": "Admin organization for RBAC",
                    "default": "system:masters"
                },
                "namespace": {
                    "type": "string",
                    "description": "Default namespace",
                    "default": "default"
                },
                "wait_timeout": {
                    "type": "integer",
                    "description": "Timeout for cluster operations (seconds)",
                    "default": 300
                }
            },
            "required": ["action", "cluster_name"]
        } 