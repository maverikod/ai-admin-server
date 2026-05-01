"""Module queue_impl."""

from ai_admin.core.custom_exceptions import (
    ConfigurationError,
    CustomError,
    NetworkError,
)
import asyncio
import json
import uuid
import ssl
import socket
import ftplib
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from .enums import TaskErrorCode, TaskStatus, TaskType
from .task import Task

class K8sKindExecutor:
    """Universal task queue for managing any type of operations."""

    async def _execute_k8s_deployment_create_task(self, task: Task) -> None:
        """Execute Kubernetes deployment creation task using kubernetes Python library."""
        import logging
        from ai_admin.commands.k8s_deployment_create_command import (
            K8sDeploymentCreateCommand,
        )

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting K8S deployment create task {task.id} ===")
        params = task.params
        project_path = params.get("project_path")
        image = params.get("image", "ai-admin-server:latest")
        port = params.get("port", 8060)
        namespace = params.get("namespace", "default")
        replicas = params.get("replicas", 1)
        cpu_limit = params.get("cpu_limit", "500m")
        memory_limit = params.get("memory_limit", "512Mi")
        cpu_request = params.get("cpu_request", "100m")
        memory_request = params.get("memory_request", "128Mi")
        logger.info(
            f"Deployment parameters: project_path={project_path}, image={image}, namespace={namespace}"
        )
        task.update_progress(10, f"Creating Kubernetes deployment")
        task.add_log(f"DEBUG: Task parameters: {params}")
        try:
            command = K8sDeploymentCreateCommand()
            result = await command.execute(
                project_path=project_path,
                image=image,
                port=port,
                namespace=namespace,
                replicas=replicas,
                cpu_limit=cpu_limit,
                memory_limit=memory_limit,
                cpu_request=cpu_request,
                memory_request=memory_request,
            )
            if result.success:
                task.update_progress(90, "Deployment created successfully")
                task.complete(
                    {
                        "message": "Kubernetes deployment created successfully",
                        "deployment_name": result.data.get("deployment_name"),
                        "namespace": result.data.get("namespace"),
                        "available_replicas": result.data.get("available_replicas"),
                        "replicas": result.data.get("replicas"),
                        "uid": result.data.get("uid"),
                        "creation_timestamp": result.data.get("creation_timestamp"),
                    }
                )
            else:
                task.fail(
                    result.message, TaskErrorCode.K8S_DEPLOYMENT_FAILED, result.details
                )
        except CustomError as e:
            error_msg = f"K8S deployment creation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(
                error_msg, TaskErrorCode.K8S_DEPLOYMENT_FAILED, {"exception": str(e)}
            )

    async def _execute_k8s_pod_create_task(self, task: Task) -> None:
        """Execute Kubernetes pod creation task using kubernetes Python library."""
        import logging
        from ai_admin.commands.k8s_pod_create_command import K8sPodCreateCommand

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting K8S pod create task {task.id} ===")
        params = task.params
        project_path = params.get("project_path")
        image = params.get("image", "ai-admin-server:latest")
        port = params.get("port", 8060)
        namespace = params.get("namespace", "default")
        cpu_limit = params.get("cpu_limit", "500m")
        memory_limit = params.get("memory_limit", "512Mi")
        logger.info(
            f"Pod parameters: project_path={project_path}, image={image}, namespace={namespace}"
        )
        task.update_progress(10, f"Creating Kubernetes pod")
        task.add_log(f"DEBUG: Task parameters: {params}")
        try:
            command = K8sPodCreateCommand()
            result = await command.execute(
                project_path=project_path,
                image=image,
                port=port,
                namespace=namespace,
                cpu_limit=cpu_limit,
                memory_limit=memory_limit,
            )
            if result.success:
                task.update_progress(90, "Pod created successfully")
                task.complete(
                    {
                        "message": "Kubernetes pod created successfully",
                        "pod_name": result.data.get("pod_name"),
                        "namespace": result.data.get("namespace"),
                        "pod_phase": result.data.get("pod_phase"),
                        "pod_ip": result.data.get("pod_ip"),
                        "uid": result.data.get("uid"),
                        "creation_timestamp": result.data.get("creation_timestamp"),
                    }
                )
            else:
                task.fail(result.message, TaskErrorCode.K8S_POD_FAILED, result.details)
        except CustomError as e:
            error_msg = f"K8S pod creation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(error_msg, TaskErrorCode.K8S_POD_FAILED, {"exception": str(e)})

    async def _execute_k8s_pod_status_task(self, task: Task) -> None:
        """Execute Kubernetes pod status task using kubernetes Python library."""
        import logging
        from kubernetes import client, config
        from kubernetes.client.rest import ApiException

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting K8S pod status task {task.id} ===")
        params = task.params
        pod_name = params.get("pod_name")
        namespace = params.get("namespace", "default")
        logger.info(
            f"Pod status parameters: pod_name={pod_name}, namespace={namespace}"
        )
        task.update_progress(10, f"Getting pod status")
        task.add_log(f"DEBUG: Task parameters: {params}")
        try:
            try:
                config.load_kube_config()
            except ConfigurationError:
                config.load_incluster_config()
            core_v1 = client.CoreV1Api()
            pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            task.update_progress(90, "Pod status retrieved successfully")
            task.complete(
                {
                    "message": "Kubernetes pod status retrieved successfully",
                    "pod_name": pod_name,
                    "namespace": namespace,
                    "phase": pod.status.phase,
                    "pod_ip": pod.status.pod_ip,
                    "host_ip": pod.status.host_ip,
                    "start_time": (
                        pod.status.start_time.isoformat()
                        if pod.status.start_time
                        else None
                    ),
                    "container_statuses": [
                        {
                            "name": container.name,
                            "ready": container.ready,
                            "restart_count": container.restart_count,
                            "state": str(container.state),
                        }
                        for container in pod.status.container_statuses or []
                    ],
                }
            )
        except ApiException as e:
            if e.status == 404:
                task.fail(
                    f"Pod {pod_name} not found in namespace {namespace}",
                    TaskErrorCode.K8S_RESOURCE_NOT_FOUND,
                    {"pod_name": pod_name, "namespace": namespace},
                )
            else:
                task.fail(
                    f"Failed to get pod status: {str(e)}",
                    TaskErrorCode.K8S_API_ERROR,
                    {"api_exception": str(e), "status_code": e.status},
                )
        except CustomError as e:
            error_msg = f"K8S pod status failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(error_msg, TaskErrorCode.K8S_API_ERROR, {"exception": str(e)})

    async def _execute_k8s_pod_delete_task(self, task: Task) -> None:
        """Execute Kubernetes pod deletion task using kubernetes Python library."""
        import logging
        from kubernetes import client, config
        from kubernetes.client.rest import ApiException

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting K8S pod delete task {task.id} ===")
        params = task.params
        pod_name = params.get("pod_name")
        namespace = params.get("namespace", "default")
        logger.info(
            f"Pod delete parameters: pod_name={pod_name}, namespace={namespace}"
        )
        task.update_progress(10, f"Deleting pod")
        task.add_log(f"DEBUG: Task parameters: {params}")
        try:
            try:
                config.load_kube_config()
            except ConfigurationError:
                config.load_incluster_config()
            core_v1 = client.CoreV1Api()
            core_v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
            task.update_progress(90, "Pod deleted successfully")
            task.complete(
                {
                    "message": "Kubernetes pod deleted successfully",
                    "pod_name": pod_name,
                    "namespace": namespace,
                }
            )
        except ApiException as e:
            if e.status == 404:
                task.fail(
                    f"Pod {pod_name} not found in namespace {namespace}",
                    TaskErrorCode.K8S_RESOURCE_NOT_FOUND,
                    {"pod_name": pod_name, "namespace": namespace},
                )
            else:
                task.fail(
                    f"Failed to delete pod: {str(e)}",
                    TaskErrorCode.K8S_API_ERROR,
                    {"api_exception": str(e), "status_code": e.status},
                )
        except CustomError as e:
            error_msg = f"K8S pod deletion failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(error_msg, TaskErrorCode.K8S_API_ERROR, {"exception": str(e)})

    async def _execute_kind_cluster_create_task(self, task: Task) -> None:
        """Execute Kind cluster creation task."""
        import logging
        from ai_admin.commands.kind_cluster_command import KindClusterCommand
        from ai_admin.commands.k8s_cluster_manager_command import (
            K8sClusterManagerCommand,
        )
        from mcp_proxy_adapter.commands.result import SuccessResult

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting cluster create task {task.id} ===")
        params = task.params
        cluster_name = params.get("cluster_name")
        cluster_type = params.get("cluster_type", "kind")
        container_name = params.get("container_name")
        port = params.get("port")
        config = params.get("config")
        logger.info(
            f"Cluster create parameters: cluster_name={cluster_name}, cluster_type={cluster_type}"
        )
        task.update_progress(10, f"Creating {cluster_type} cluster: {cluster_name}")
        task.add_log(f"DEBUG: Task parameters: {params}")
        try:
            if cluster_type in ["k3s", "kind"]:
                command = K8sClusterManagerCommand()
                result = await command._create_cluster_internal(
                    cluster_name=cluster_name,
                    cluster_type=cluster_type,
                    container_name=container_name,
                    port=port,
                    config=config,
                )
            else:
                command = KindClusterCommand()
                result = await command.execute(
                    action="create",
                    cluster_name=cluster_name,
                    config_file=params.get("config_file"),
                    image=params.get("image"),
                    wait=params.get("wait", 60),
                )
            if isinstance(result, SuccessResult):
                task.update_progress(90, f"{cluster_type} cluster created successfully")
                task.complete(
                    {
                        "message": f"{cluster_type} cluster created successfully",
                        "cluster_name": cluster_name,
                        "cluster_type": cluster_type,
                        "container_name": container_name,
                        "port": port,
                        "config": config,
                        "data": result.data,
                    }
                )
            else:
                task.fail(
                    result.message,
                    TaskErrorCode.KIND_CLUSTER_CREATE_FAILED,
                    result.details,
                )
        except CustomError as e:
            error_msg = f"{cluster_type} cluster creation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(
                error_msg,
                TaskErrorCode.KIND_CLUSTER_CREATE_FAILED,
                {"exception": str(e)},
            )

    async def _execute_kind_cluster_delete_task(self, task: Task) -> None:
        """Execute Kind cluster deletion task."""
        import logging
        from ai_admin.commands.kind_cluster_command import KindClusterCommand

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting Kind cluster delete task {task.id} ===")
        params = task.params
        cluster_name = params.get("cluster_name")
        logger.info(f"Kind cluster delete parameters: cluster_name={cluster_name}")
        task.update_progress(10, f"Deleting Kind cluster: {cluster_name}")
        task.add_log(f"DEBUG: Task parameters: {params}")
        try:
            command = KindClusterCommand()
            result = await command.execute(action="delete", cluster_name=cluster_name)
            if result.success:
                task.update_progress(90, "Kind cluster deleted successfully")
                task.complete(
                    {
                        "message": "Kind cluster deleted successfully",
                        "cluster_name": cluster_name,
                        "stdout": result.data.get("stdout"),
                    }
                )
            else:
                task.fail(
                    result.message,
                    TaskErrorCode.KIND_CLUSTER_DELETE_FAILED,
                    result.details,
                )
        except CustomError as e:
            error_msg = f"Kind cluster deletion failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(
                error_msg,
                TaskErrorCode.KIND_CLUSTER_DELETE_FAILED,
                {"exception": str(e)},
            )

    async def _execute_kind_cluster_list_task(self, task: Task) -> None:
        """Execute Kind cluster list task."""
        import logging
        from ai_admin.commands.kind_cluster_command import KindClusterCommand

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting Kind cluster list task {task.id} ===")
        task.update_progress(10, "Listing Kind clusters")
        try:
            command = KindClusterCommand()
            result = await command.execute(action="list")
            if result.success:
                task.update_progress(90, "Kind clusters listed successfully")
                task.complete(
                    {
                        "message": "Kind clusters listed successfully",
                        "clusters": result.data.get("clusters", []),
                        "count": result.data.get("count", 0),
                    }
                )
            else:
                task.fail(
                    result.message, TaskErrorCode.KIND_CLUSTER_NOT_FOUND, result.details
                )
        except CustomError as e:
            error_msg = f"Kind cluster listing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(
                error_msg, TaskErrorCode.KIND_CLUSTER_NOT_FOUND, {"exception": str(e)}
            )

    async def _execute_kind_cluster_get_nodes_task(self, task: Task) -> None:
        """Execute Kind cluster get nodes task."""
        import logging
        from ai_admin.commands.kind_cluster_command import KindClusterCommand

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting Kind cluster get nodes task {task.id} ===")
        params = task.params
        cluster_name = params.get("cluster_name")
        logger.info(f"Kind cluster get nodes parameters: cluster_name={cluster_name}")
        task.update_progress(10, f"Getting nodes for Kind cluster: {cluster_name}")
        task.add_log(f"DEBUG: Task parameters: {params}")
        try:
            command = KindClusterCommand()
            result = await command.execute(
                action="get-nodes", cluster_name=cluster_name
            )
            if result.success:
                task.update_progress(90, "Kind cluster nodes retrieved successfully")
                task.complete(
                    {
                        "message": "Kind cluster nodes retrieved successfully",
                        "cluster_name": cluster_name,
                        "nodes": result.data.get("nodes", []),
                        "count": result.data.get("count", 0),
                    }
                )
            else:
                task.fail(
                    result.message, TaskErrorCode.KIND_CLUSTER_NOT_FOUND, result.details
                )
        except CustomError as e:
            error_msg = f"Kind cluster get nodes failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(
                error_msg, TaskErrorCode.KIND_CLUSTER_NOT_FOUND, {"exception": str(e)}
            )

    async def _execute_kind_load_image_task(self, task: Task) -> None:
        """Execute Kind load image task."""
        import logging
        from ai_admin.commands.kind_cluster_command import KindClusterCommand

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting Kind load image task {task.id} ===")
        params = task.params
        cluster_name = params.get("cluster_name")
        image = params.get("image")
        logger.info(
            f"Kind load image parameters: cluster_name={cluster_name}, image={image}"
        )
        task.update_progress(10, f"Loading image into Kind cluster: {cluster_name}")
        task.add_log(f"DEBUG: Task parameters: {params}")
        try:
            command = KindClusterCommand()
            result = await command.execute(
                action="load-image", cluster_name=cluster_name, image=image
            )
            if result.success:
                task.update_progress(90, "Image loaded into Kind cluster successfully")
                task.complete(
                    {
                        "message": "Image loaded into Kind cluster successfully",
                        "cluster_name": cluster_name,
                        "image": image,
                        "stdout": result.data.get("stdout"),
                    }
                )
            else:
                task.fail(
                    result.message, TaskErrorCode.KIND_LOAD_IMAGE_FAILED, result.details
                )
        except CustomError as e:
            error_msg = f"Kind load image failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(
                error_msg, TaskErrorCode.KIND_LOAD_IMAGE_FAILED, {"exception": str(e)}
            )



