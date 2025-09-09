"""Vector Store deployment command for Kubernetes clusters."""

import json
import yaml
import asyncio
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.settings_manager import get_settings_manager
from ai_admin.commands.k8s_utils import KubernetesConfigManager


class VectorStoreDeployCommand(Command):
    """Deploy Vector Store with Redis and FAISS to Kubernetes cluster."""
    
    name = "vector_store_deploy"
    
    def __init__(self):
        """Initialize vector store deployment command."""
        self.settings_manager = get_settings_manager()
        self.config_manager = None
        self.core_v1 = None
    
    def _init_client(self, cluster_name: Optional[str] = None):
        """Initialize Kubernetes client for specific cluster."""
        self.cluster_name = cluster_name or "k3s-test-vector-store"
        
        try:
            from kubernetes import client, config
            from kubernetes.client.rest import ApiException
            import docker
            import yaml
            import tempfile
            import os
            
            # Initialize Docker client
            self.docker_client = docker.from_env()
            
            # Get kubeconfig from Docker container
            try:
                container = self.docker_client.containers.get(self.cluster_name)
                result = container.exec_run("cat /etc/rancher/k3s/k3s.yaml")
                
                if result.exit_code != 0:
                    raise Exception(f"Failed to get kubeconfig from container {self.cluster_name}")
                
                kubeconfig_content = result.output.decode('utf-8')
                kubeconfig = yaml.safe_load(kubeconfig_content)
                
                # Update server URL to point to host
                kubeconfig["clusters"][0]["cluster"]["server"] = "https://localhost:6443"
                
                # Write to temporary file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
                    yaml.dump(kubeconfig, f)
                    temp_config_path = f.name
                
                # Load configuration
                config.load_kube_config(config_file=temp_config_path)
                
                # Clean up
                os.unlink(temp_config_path)
                
                # Create Kubernetes client
                self.core_v1 = client.CoreV1Api()
                self.apps_v1 = client.AppsV1Api()
                
                print(f"Successfully initialized Kubernetes client for cluster {self.cluster_name}")
                
            except docker.errors.NotFound:
                raise Exception(f"Container {self.cluster_name} not found")
            except Exception as e:
                raise Exception(f"Failed to initialize Kubernetes client: {e}")
                    
        except Exception as e:
            print(f"Failed to initialize client: {e}")
            raise
    
    async def execute(self,
                     action: str = "deploy",
                     namespace: str = "default",
                     vector_store_image: str = "vector-store:latest",
                     redis_image: str = "redis:7-alpine",
                     config_path: Optional[str] = None,
                     storage_class: str = "local-path",
                     storage_size: str = "10Gi",
                     mtls_enabled: bool = False,
                     ca_cert: Optional[str] = None,
                     server_cert: Optional[str] = None,
                     server_key: Optional[str] = None,
                     client_cert: Optional[str] = None,
                     client_key: Optional[str] = None,
                     **kwargs):
        """
        Deploy Vector Store with Redis and FAISS to Kubernetes cluster.
        
        Args:
            action: Action to perform (deploy, delete, status, logs)
            namespace: Kubernetes namespace
            vector_store_image: Vector Store Docker image
            redis_image: Redis Docker image
            config_path: Path to config file (optional, uses default if not provided)
            storage_class: Storage class for persistent volumes
            storage_size: Size of persistent volume for FAISS
            mtls_enabled: Enable mTLS authentication
            ca_cert: Path to CA certificate
            server_cert: Path to server certificate
            server_key: Path to server private key
            client_cert: Path to client certificate
            client_key: Path to client private key
        """
        try:
            if action == "deploy":
                return await self._deploy_vector_store(namespace, vector_store_image, redis_image, 
                                                     config_path, storage_class, storage_size,
                                                     mtls_enabled, ca_cert, server_cert, server_key,
                                                     client_cert, client_key)
            elif action == "delete":
                return await self._delete_vector_store(namespace)
            elif action == "status":
                return await self._get_deployment_status(namespace)
            elif action == "logs":
                return await self._get_logs(namespace, kwargs.get("pod_name"))
            else:
                return ErrorResult(
                    message=f"Unknown action: {action}",
                    code="INVALID_ACTION",
                    details={"valid_actions": ["deploy", "delete", "status", "logs"]}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error in vector store deployment: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )
    
    async def _deploy_vector_store(self, namespace: str, vector_store_image: str, 
                                 redis_image: str, config_path: Optional[str],
                                 storage_class: str, storage_size: str,
                                 mtls_enabled: bool = False, ca_cert: Optional[str] = None,
                                 server_cert: Optional[str] = None, server_key: Optional[str] = None,
                                 client_cert: Optional[str] = None, client_key: Optional[str] = None) -> SuccessResult:
        """Deploy Vector Store with Redis and FAISS in a single pod."""
        try:
            # Configure mTLS if enabled
            if mtls_enabled:
                await self._configure_mtls(ca_cert, server_cert, server_key, client_cert, client_key)
            
            # Load configuration
            config = await self._load_config(config_path)
            
            # Create namespace if it doesn't exist
            await self._create_namespace(namespace)
            
            # Create Persistent Volume for FAISS
            pv_result = await self._create_persistent_volume(namespace, storage_class, storage_size)
            if isinstance(pv_result, ErrorResult):
                return pv_result
            
            # Create Persistent Volume Claim
            pvc_result = await self._create_persistent_volume_claim(namespace, storage_size)
            if isinstance(pvc_result, ErrorResult):
                return pvc_result
            
            # Create ConfigMap with configuration
            configmap_result = await self._create_configmap(namespace, config)
            if isinstance(configmap_result, ErrorResult):
                return configmap_result
            
            # Create single pod with Vector Store and Redis
            pod_result = await self._create_vector_store_pod(
                namespace, vector_store_image, redis_image, config
            )
            if isinstance(pod_result, ErrorResult):
                return pod_result
            
            return SuccessResult(data={
                "message": "Vector Store deployment completed successfully",
                "namespace": namespace,
                "components": {
                    "persistent_volume": pv_result.data,
                    "persistent_volume_claim": pvc_result.data,
                    "configmap": configmap_result.data,
                    "vector_store_pod": pod_result.data
                },
                "access_info": {
                    "vector_store_service": f"vector-store-service.{namespace}.svc.cluster.local:8007",
                    "redis_internal": "redis-instance1:6379"  # Redis доступен внутри пода как redis-instance1
                },
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to deploy Vector Store: {str(e)}",
                code="DEPLOYMENT_FAILED",
                details={"exception": str(e)}
            )
    
    async def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use default."""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Update Redis URL to use the correct container name inside the pod
                if "vector_store" in config and "redis_url" in config["vector_store"]:
                    config["vector_store"]["redis_url"] = "redis://redis-instance1:6379"
                return config
        else:
            # Default configuration based on config1.json
            return {
                "vector_store": {
                    "vector_size": 384,
                    "faiss_index_path": "/app/data/faiss.index",
                    "counter_path": "/app/data/id_counter.txt",
                    "redis_url": "redis://redis-instance1:6379",  # Correct Redis URL for pod internal communication
                    "limits": {
                        "max_query_limit": 1000,
                        "default_search_limit": 5,
                        "default_filter_limit": 100
                    }
                },
                "api": {
                    "host": "0.0.0.0",
                    "port": 8007,
                    "log_level": "DEBUG",
                    "auto_register_routes": True
                },
                "embedding": {
                    "embedding_url": "http://embedding-service:8001/cmd",
                    "model": "all-MiniLM-L6-v2"
                },
                "vector_store_database": {
                    "name": "Vector Store Database",
                    "version": "1.0.0",
                    "description": "High-performance service for storing, retrieving, and searching vector embeddings",
                    "features": [
                        "semantic_search",
                        "metadata_filtering",
                        "efficient_vector_operations"
                    ],
                    "standardize_api": True
                }
            }
    
    async def _create_namespace(self, namespace: str) -> None:
        """Create namespace if it doesn't exist."""
        try:
            from kubernetes import client
            from kubernetes.client.rest import ApiException
            
            # Setup Kubernetes client
            self._init_client("k3s-test-vector-store")
            
            # Check if namespace exists
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
                    
        except Exception as e:
            print(f"Warning: Failed to create namespace {namespace}: {e}")
    
    async def _create_persistent_volume(self, namespace: str, storage_class: str, 
                                      storage_size: str) -> SuccessResult:
        """Create Persistent Volume for FAISS storage."""
        # With local-path StorageClass, PV will be created automatically by the provisioner
        # when PVC is created, so we don't need to create PV manually
                return SuccessResult(data={
            "message": f"Persistent Volume will be created automatically by {storage_class} StorageClass",
            "storage_class": storage_class,
                "storage_size": storage_size
            })
    
    async def _create_persistent_volume_claim(self, namespace: str, storage_size: str) -> SuccessResult:
        """Create Persistent Volume Claim for FAISS storage."""
        try:
            from kubernetes import client
            from kubernetes.client.rest import ApiException
            
            # Setup Kubernetes client
            self._init_client("k3s-test-vector-store")
            
            pvc_name = "faiss-storage-claim"
            
            # Check if PVC already exists
            try:
                self.core_v1.read_namespaced_persistent_volume_claim(pvc_name, namespace)
                return SuccessResult(data={
                    "message": f"Persistent Volume Claim {pvc_name} already exists",
                    "name": pvc_name
                })
            except ApiException as e:
                if e.status != 404:
                    raise
            
            # Create Persistent Volume Claim
            pvc = client.V1PersistentVolumeClaim(
                metadata=client.V1ObjectMeta(name=pvc_name),
                spec=client.V1PersistentVolumeClaimSpec(
                    access_modes=["ReadWriteOnce"],
                    storage_class_name="local-path",
                    resources=client.V1ResourceRequirements(
                        requests={"storage": storage_size}
                    )
                )
            )
            
            self.core_v1.create_namespaced_persistent_volume_claim(namespace, pvc)
            
            return SuccessResult(data={
                "message": f"Persistent Volume Claim {pvc_name} created successfully",
                "name": pvc_name,
                "storage_size": storage_size
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create Persistent Volume Claim: {str(e)}",
                code="PVC_CREATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _create_configmap(self, namespace: str, config: Dict[str, Any]) -> SuccessResult:
        """Create ConfigMap with Vector Store configuration."""
        try:
            from kubernetes import client
            from kubernetes.client.rest import ApiException
            
            # Setup Kubernetes client
            self._init_client("k3s-test-vector-store")
            
            configmap_name = "vector-store-config"
            
            # Check if ConfigMap already exists
            try:
                self.core_v1.read_namespaced_config_map(configmap_name, namespace)
                return SuccessResult(data={
                    "message": f"ConfigMap {configmap_name} already exists",
                    "name": configmap_name
                })
            except ApiException as e:
                if e.status != 404:
                    raise
            
            # Create ConfigMap with proper configuration
            configmap = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(name=configmap_name),
                data={
                    "config.json": json.dumps(config, indent=2)
                }
            )
            
            self.core_v1.create_namespaced_config_map(namespace, configmap)
            
            return SuccessResult(data={
                "message": f"ConfigMap {configmap_name} created successfully",
                "name": configmap_name
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create ConfigMap: {str(e)}",
                code="CONFIGMAP_CREATION_FAILED",
                details={"exception": str(e)}
            )
    

    
    async def _create_vector_store_pod(self, namespace: str, vector_store_image: str,
                                     redis_image: str, config: Dict[str, Any]) -> SuccessResult:
        """Create a single pod with Vector Store and Redis containers."""
        try:
            from kubernetes import client
            from kubernetes.client.rest import ApiException
            
            # Setup Kubernetes client
            self._init_client("k3s-test-vector-store")
            
            pod_name = "vector-store-pod"
            
            # Check if pod already exists
            try:
                self.core_v1.read_namespaced_pod(pod_name, namespace)
                return SuccessResult(data={
                    "message": f"Vector Store pod {pod_name} already exists",
                    "name": pod_name
                })
            except ApiException as e:
                if e.status != 404:
                    raise
            
            # Create pod with two containers: Vector Store and Redis
            pod = client.V1Pod(
                metadata=client.V1ObjectMeta(
                    name=pod_name,
                    labels={"app": "vector-store"}
                ),
                spec=client.V1PodSpec(
                    containers=[
                        # Vector Store container
                        client.V1Container(
                            name="vector-store",
                            image=vector_store_image,
                            ports=[client.V1ContainerPort(container_port=8007)],
                            resources=client.V1ResourceRequirements(
                                requests={"memory": "512Mi", "cpu": "250m"},
                                limits={"memory": "1Gi", "cpu": "500m"}
                            ),
                            volume_mounts=[
                                client.V1VolumeMount(
                                    name="faiss-storage",
                                    mount_path="/app/data"
                                ),
                                client.V1VolumeMount(
                                    name="config-volume",
                                    mount_path="/app/config"
                                ),
                                client.V1VolumeMount(
                                    name="cache-volume",
                                    mount_path="/app/cache"
                                ),
                                client.V1VolumeMount(
                                    name="logs-volume",
                                    mount_path="/app/logs"
                                )
                            ],
                            env=[
                                client.V1EnvVar(
                                    name="CONFIG_PATH",
                                    value="/app/config/config.json"
                                ),
                                client.V1EnvVar(
                                    name="REDIS_URL",
                                    value="redis://redis-instance1:6379"  # Redis доступен внутри пода как redis-instance1
                                )
                            ]
                        ),
                        # Redis container (sidecar)
                        client.V1Container(
                            name="redis-instance1",
                            image=redis_image,
                            ports=[client.V1ContainerPort(container_port=6379)],
                            resources=client.V1ResourceRequirements(
                                requests={"memory": "128Mi", "cpu": "100m"},
                                limits={"memory": "256Mi", "cpu": "200m"}
                            ),
                            command=["redis-server", "--appendonly", "yes"],
                            volume_mounts=[
                                client.V1VolumeMount(
                                    name="redis-data",
                                    mount_path="/data"
                                )
                            ]
                        )
                    ],
                    volumes=[
                        # FAISS storage volume
                        client.V1Volume(
                            name="faiss-storage",
                            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                                claim_name="faiss-storage-claim"
                            )
                        ),
                        # Config volume
                        client.V1Volume(
                            name="config-volume",
                            config_map=client.V1ConfigMapVolumeSource(
                                name="vector-store-config"
                            )
                        ),
                        # Redis data volume (emptyDir for simplicity)
                        client.V1Volume(
                            name="redis-data",
                            empty_dir=client.V1EmptyDirVolumeSource()
                        ),
                        # Cache volume
                        client.V1Volume(
                            name="cache-volume",
                            empty_dir=client.V1EmptyDirVolumeSource()
                        ),
                        # Logs volume
                        client.V1Volume(
                            name="logs-volume",
                            empty_dir=client.V1EmptyDirVolumeSource()
                        )
                    ],
                    restart_policy="Always"
                )
            )
            
            self.core_v1.create_namespaced_pod(namespace, pod)
            
            # Create service for Vector Store
            service = client.V1Service(
                metadata=client.V1ObjectMeta(name="vector-store-service"),
                spec=client.V1ServiceSpec(
                    selector={"app": "vector-store"},
                    ports=[client.V1ServicePort(port=8007, target_port=8007)],
                    type="ClusterIP"
                )
            )
            
            self.core_v1.create_namespaced_service(namespace, service)
            
            return SuccessResult(data={
                "message": f"Vector Store pod with Redis created successfully",
                "pod": pod_name,
                "service": "vector-store-service",
                "containers": ["vector-store", "redis-instance1"]
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create Vector Store pod: {str(e)}",
                code="POD_CREATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _delete_vector_store(self, namespace: str) -> SuccessResult:
        """Delete Vector Store pod and all related resources."""
        try:
            from kubernetes import client
            from kubernetes.client.rest import ApiException
            
            # Setup Kubernetes client
            self._init_client("k3s-test-vector-store")
            
            deleted_resources = []
            
            # Delete pod
            try:
                self.core_v1.delete_namespaced_pod("vector-store-pod", namespace)
                deleted_resources.append("pod/vector-store-pod")
            except ApiException as e:
                if e.status != 404:
                    raise
            
            # Delete service
            try:
                self.core_v1.delete_namespaced_service("vector-store-service", namespace)
                deleted_resources.append("service/vector-store-service")
            except ApiException as e:
                if e.status != 404:
                    raise
            
            # Delete ConfigMap
            try:
                self.core_v1.delete_namespaced_config_map("vector-store-config", namespace)
                deleted_resources.append("configmap/vector-store-config")
            except ApiException as e:
                if e.status != 404:
                    raise
            
            # Delete PVC
            try:
                self.core_v1.delete_namespaced_persistent_volume_claim("faiss-storage-claim", namespace)
                deleted_resources.append("pvc/faiss-storage-claim")
            except ApiException as e:
                if e.status != 404:
                    raise
            
            return SuccessResult(data={
                "message": "Vector Store pod deleted successfully",
                "deleted_resources": deleted_resources,
                "namespace": namespace
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to delete Vector Store pod: {str(e)}",
                code="DELETION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _get_deployment_status(self, namespace: str) -> SuccessResult:
        """Get pod status."""
        try:
            from kubernetes import client
            from kubernetes.client.rest import ApiException
            
            # Setup Kubernetes client
            self._init_client("k3s-test-vector-store")
            
            # Get pod status
            try:
                pod = self.core_v1.read_namespaced_pod("vector-store-pod", namespace)
                pod_status = {
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "ready": all(cont.ready for cont in pod.status.container_statuses) if pod.status.container_statuses else False,
                    "containers": []
                }
                
                # Get container statuses
                for container in pod.status.container_statuses:
                    pod_status["containers"].append({
                        "name": container.name,
                        "ready": container.ready,
                        "restart_count": container.restart_count,
                        "state": container.state.running.start_time.isoformat() if container.state.running else "not_running"
                    })
                
            except ApiException as e:
                if e.status == 404:
                    pod_status = "not_found"
                else:
                    raise
            
            # Get service status
            try:
                service = self.core_v1.read_namespaced_service("vector-store-service", namespace)
                service_status = {
                    "name": service.metadata.name,
                    "type": service.spec.type,
                    "ports": [f"{port.port}:{port.target_port}" for port in service.spec.ports]
                }
            except ApiException as e:
                if e.status == 404:
                    service_status = "not_found"
                else:
                    raise
            
            return SuccessResult(data={
                "message": "Pod status retrieved successfully",
                "namespace": namespace,
                "pod": pod_status,
                "service": service_status
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to get pod status: {str(e)}",
                code="STATUS_FAILED",
                details={"exception": str(e)}
            )
    
    async def _get_logs(self, namespace: str, pod_name: Optional[str] = None, container: Optional[str] = None) -> SuccessResult:
        """Get logs from Vector Store pod containers."""
        try:
            from kubernetes import client
            from kubernetes.client.rest import ApiException
            
            # Setup Kubernetes client
            self._init_client("k3s-test-vector-store")
            
            logs = {}
            target_pod = pod_name or "vector-store-pod"
            
            if container:
                # Get logs from specific container
                try:
                    container_logs = self.core_v1.read_namespaced_pod_log(target_pod, namespace, container=container)
                    logs[f"{target_pod}:{container}"] = container_logs
                except ApiException as e:
                    return ErrorResult(
                        message=f"Failed to get logs for container {container} in pod {target_pod}: {str(e)}",
                        code="LOGS_FAILED"
                    )
            else:
                # Get logs from both containers
                for container_name in ["vector-store", "redis-instance1"]:
                    try:
                        container_logs = self.core_v1.read_namespaced_pod_log(target_pod, namespace, container=container_name)
                        logs[f"{target_pod}:{container_name}"] = container_logs
                    except ApiException:
                        logs[f"{target_pod}:{container_name}"] = "Failed to retrieve logs"
            
            return SuccessResult(data={
                "message": "Logs retrieved successfully",
                "namespace": namespace,
                "pod": target_pod,
                "logs": logs
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to get logs: {str(e)}",
                code="LOGS_FAILED",
                details={"exception": str(e)}
            ) 
    
    async def _configure_mtls(self, ca_cert: Optional[str], server_cert: Optional[str], 
                             server_key: Optional[str], client_cert: Optional[str], 
                             client_key: Optional[str]) -> None:
        """Configure mTLS certificates for Kubernetes client."""
        try:
            from kubernetes import client
            
            # Validate certificate files exist
            cert_files = []
            if ca_cert:
                cert_files.append(("CA certificate", ca_cert))
            if client_cert:
                cert_files.append(("Client certificate", client_cert))
            if client_key:
                cert_files.append(("Client key", client_key))
            
            for cert_name, cert_path in cert_files:
                if not os.path.exists(cert_path):
                    raise FileNotFoundError(f"{cert_name} not found: {cert_path}")
            
            # Configure Kubernetes client with certificates
            configuration = client.Configuration()
            
            if client_cert and client_key:
                configuration.cert_file = client_cert
                configuration.key_file = client_key
            
            if ca_cert:
                configuration.ssl_ca_cert = ca_cert
            
            # Disable SSL verification for self-signed certificates
            configuration.verify_ssl = False
            
            # Set the configuration for the client
            client.Configuration.set_default(configuration)
            
            print(f"mTLS configuration applied successfully")
            
        except Exception as e:
            print(f"Failed to configure mTLS: {e}")
            raise