"""Kubernetes mTLS setup command for secure cluster authentication."""

import os
import yaml
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.settings_manager import get_settings_manager
from ai_admin.commands.k8s_utils import KubernetesConfigManager


class K8sMtlsSetupCommand(Command):
    """Command to setup mTLS certificates for Kubernetes clusters."""
    
    name = "k8s_mtls_setup"
    
    def __init__(self):
        """Initialize mTLS setup command."""
        self.settings_manager = get_settings_manager()
        self.config_manager = None
        self.core_v1 = None
    
    def _init_client(self, cluster_name: Optional[str] = None):
        """Initialize Kubernetes client for specific cluster."""
        try:
            # Get settings and create config manager
            config_data = self.settings_manager.get_all_settings()
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
    
    async def execute(self,
                     action: str = "setup",
                     cluster_name: str = "default",
                     namespace: str = "default",
                     cert_dir: Optional[str] = None,
                     ca_cert_path: Optional[str] = None,
                     client_cert_path: Optional[str] = None,
                     client_key_path: Optional[str] = None,
                     **kwargs):
        """
        Setup mTLS certificates for Kubernetes cluster.
        
        Args:
            action: Action to perform (setup, verify, remove)
            cluster_name: Name of the Kubernetes cluster
            namespace: Kubernetes namespace for certificates
            cert_dir: Directory containing certificates
            ca_cert_path: Path to CA certificate
            client_cert_path: Path to client certificate
            client_key_path: Path to client private key
        """
        try:
            if action == "setup":
                return await self._setup_mtls(cluster_name, namespace, cert_dir, 
                                             ca_cert_path, client_cert_path, client_key_path)
            elif action == "verify":
                return await self._verify_mtls(cluster_name, namespace)
            elif action == "remove":
                return await self._remove_mtls(cluster_name, namespace)
            else:
                return ErrorResult(
                    message=f"Unknown action: {action}",
                    code="INVALID_ACTION",
                    details={"valid_actions": ["setup", "verify", "remove"]}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error in mTLS setup: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )
    
    async def _setup_mtls(self, cluster_name: str, namespace: str, 
                         cert_dir: Optional[str], ca_cert_path: Optional[str],
                         client_cert_path: Optional[str], client_key_path: Optional[str]) -> SuccessResult:
        """Setup mTLS certificates for the cluster."""
        try:
            # Initialize client
            self._init_client(cluster_name)
            
            # Determine certificate paths
            if cert_dir:
                ca_cert_path = ca_cert_path or os.path.join(cert_dir, "ca.crt")
                client_cert_path = client_cert_path or os.path.join(cert_dir, "client.crt")
                client_key_path = client_key_path or os.path.join(cert_dir, "client.key")
            
            # Validate certificate files exist
            if not all(os.path.exists(path) for path in [ca_cert_path, client_cert_path, client_key_path]):
                return ErrorResult(
                    message="Certificate files not found",
                    code="CERTIFICATES_NOT_FOUND",
                    details={"ca_cert": ca_cert_path, "client_cert": client_cert_path, "client_key": client_key_path}
                )
            
            # Create namespace if it doesn't exist
            await self._create_namespace(namespace)
            
            # Create ConfigMap with CA certificate
            ca_configmap_result = await self._create_ca_configmap(namespace, ca_cert_path)
            if isinstance(ca_configmap_result, ErrorResult):
                return ca_configmap_result
            
            # Create Secret with client certificates
            client_secret_result = await self._create_client_secret(namespace, client_cert_path, client_key_path)
            if isinstance(client_secret_result, ErrorResult):
                return client_secret_result
            
            # Create RBAC resources for mTLS
            rbac_result = await self._create_mtls_rbac(namespace)
            if isinstance(rbac_result, ErrorResult):
                return rbac_result
            
            return SuccessResult(data={
                "message": f"mTLS setup completed successfully for cluster '{cluster_name}'",
                "cluster_name": cluster_name,
                "namespace": namespace,
                "ca_configmap": "mtls-ca-cert",
                "client_secret": "mtls-client-cert",
                "rbac_resources": ["mtls-role", "mtls-rolebinding"],
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to setup mTLS: {str(e)}",
                code="SETUP_FAILED",
                details={"exception": str(e)}
            )
    
    async def _create_namespace(self, namespace: str) -> None:
        """Create namespace if it doesn't exist."""
        try:
            self.core_v1.read_namespace(namespace)
            return  # Namespace already exists
        except ApiException as e:
            if e.status == 404:
                # Create namespace
                ns = client.V1Namespace(
                    metadata=client.V1ObjectMeta(name=namespace)
                )
                self.core_v1.create_namespace(ns)
            else:
                raise
    
    async def _create_ca_configmap(self, namespace: str, ca_cert_path: str) -> SuccessResult:
        """Create ConfigMap with CA certificate."""
        try:
            # Read CA certificate
            with open(ca_cert_path, 'r') as f:
                ca_cert_content = f.read()
            
            # Create ConfigMap
            configmap = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(name="mtls-ca-cert"),
                data={"ca.crt": ca_cert_content}
            )
            
            self.core_v1.create_namespaced_config_map(namespace, configmap)
            
            return SuccessResult(data={
                "message": "CA certificate ConfigMap created successfully",
                "name": "mtls-ca-cert"
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create CA ConfigMap: {str(e)}",
                code="CONFIGMAP_CREATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _create_client_secret(self, namespace: str, client_cert_path: str, client_key_path: str) -> SuccessResult:
        """Create Secret with client certificates."""
        try:
            # Read client certificate and key
            with open(client_cert_path, 'r') as f:
                client_cert_content = f.read()
            with open(client_key_path, 'r') as f:
                client_key_content = f.read()
            
            # Create Secret
            secret = client.V1Secret(
                metadata=client.V1ObjectMeta(name="mtls-client-cert"),
                type="kubernetes.io/tls",
                data={
                    "tls.crt": client_cert_content.encode('base64'),
                    "tls.key": client_key_content.encode('base64')
                }
            )
            
            self.core_v1.create_namespaced_secret(namespace, secret)
            
            return SuccessResult(data={
                "message": "Client certificate Secret created successfully",
                "name": "mtls-client-cert"
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create client Secret: {str(e)}",
                code="SECRET_CREATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _create_mtls_rbac(self, namespace: str) -> SuccessResult:
        """Create RBAC resources for mTLS authentication."""
        try:
            # Create Role
            role = client.V1Role(
                metadata=client.V1ObjectMeta(name="mtls-role"),
                rules=[
                    client.V1PolicyRule(
                        api_groups=[""],
                        resources=["pods", "services", "configmaps", "secrets"],
                        verbs=["get", "list", "watch", "create", "update", "patch", "delete"]
                    )
                ]
            )
            
            # Create RoleBinding
            role_binding = client.V1RoleBinding(
                metadata=client.V1ObjectMeta(name="mtls-rolebinding"),
                role_ref=client.V1RoleRef(
                    api_group="rbac.authorization.k8s.io",
                    kind="Role",
                    name="mtls-role"
                ),
                subjects=[
                    client.V1Subject(
                        kind="ServiceAccount",
                        name="mtls-service-account",
                        namespace=namespace
                    )
                ]
            )
            
            # Create ServiceAccount
            service_account = client.V1ServiceAccount(
                metadata=client.V1ObjectMeta(name="mtls-service-account")
            )
            
            # Apply RBAC resources
            self.core_v1.create_namespaced_role(namespace, role)
            self.core_v1.create_namespaced_role_binding(namespace, role_binding)
            self.core_v1.create_namespaced_service_account(namespace, service_account)
            
            return SuccessResult(data={
                "message": "RBAC resources created successfully",
                "resources": ["mtls-role", "mtls-rolebinding", "mtls-service-account"]
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create RBAC resources: {str(e)}",
                code="RBAC_CREATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _verify_mtls(self, cluster_name: str, namespace: str) -> SuccessResult:
        """Verify mTLS setup."""
        try:
            # Initialize client
            self._init_client(cluster_name)
            
            # Check if resources exist
            resources_status = {}
            
            try:
                self.core_v1.read_namespaced_config_map("mtls-ca-cert", namespace)
                resources_status["ca_configmap"] = "exists"
            except ApiException as e:
                if e.status == 404:
                    resources_status["ca_configmap"] = "not_found"
                else:
                    raise
            
            try:
                self.core_v1.read_namespaced_secret("mtls-client-cert", namespace)
                resources_status["client_secret"] = "exists"
            except ApiException as e:
                if e.status == 404:
                    resources_status["client_secret"] = "not_found"
                else:
                    raise
            
            try:
                self.core_v1.read_namespaced_role("mtls-role", namespace)
                resources_status["role"] = "exists"
            except ApiException as e:
                if e.status == 404:
                    resources_status["role"] = "not_found"
                else:
                    raise
            
            return SuccessResult(data={
                "message": "mTLS verification completed",
                "cluster_name": cluster_name,
                "namespace": namespace,
                "resources_status": resources_status,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to verify mTLS: {str(e)}",
                code="VERIFICATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _remove_mtls(self, cluster_name: str, namespace: str) -> SuccessResult:
        """Remove mTLS setup."""
        try:
            # Initialize client
            self._init_client(cluster_name)
            
            deleted_resources = []
            
            # Delete resources
            resources_to_delete = [
                ("configmap", "mtls-ca-cert"),
                ("secret", "mtls-client-cert"),
                ("role", "mtls-role"),
                ("rolebinding", "mtls-rolebinding"),
                ("serviceaccount", "mtls-service-account")
            ]
            
            for resource_type, resource_name in resources_to_delete:
                try:
                    if resource_type == "configmap":
                        self.core_v1.delete_namespaced_config_map(resource_name, namespace)
                    elif resource_type == "secret":
                        self.core_v1.delete_namespaced_secret(resource_name, namespace)
                    elif resource_type == "role":
                        self.core_v1.delete_namespaced_role(resource_name, namespace)
                    elif resource_type == "rolebinding":
                        self.core_v1.delete_namespaced_role_binding(resource_name, namespace)
                    elif resource_type == "serviceaccount":
                        self.core_v1.delete_namespaced_service_account(resource_name, namespace)
                    
                    deleted_resources.append(f"{resource_type}/{resource_name}")
                except ApiException as e:
                    if e.status != 404:
                        raise
            
            return SuccessResult(data={
                "message": "mTLS setup removed successfully",
                "cluster_name": cluster_name,
                "namespace": namespace,
                "deleted_resources": deleted_resources,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to remove mTLS: {str(e)}",
                code="REMOVAL_FAILED",
                details={"exception": str(e)}
            ) 