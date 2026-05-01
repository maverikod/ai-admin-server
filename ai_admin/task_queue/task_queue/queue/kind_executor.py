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

class KindExecutor:
    """Universal task queue for managing any type of operations."""

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



