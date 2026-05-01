"""Module queue."""

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
from dataclasses import dataclass, field

class K8sExecutor:
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



