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
from .task_queue import TaskQueue

class TaskQueueCore:
    """Universal task queue for managing any type of operations."""

    def __init__(self):
        self._pending_queue = None
        self._lock = None
        self._running_tasks = None
        self._tasks = None
        self.max_concurrent = None

    async def add_task(self, task: Task) -> str:
        """Add task to queue.

        Args:
            task: Task to add

        Returns:
            Task ID
        """
        import logging

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Adding task to queue ===")
        logger.info(f"Task ID: {task.id}")
        logger.info(f"Task type: {task.task_type.value}")
        logger.info(f"Task params: {task.params}")
        async with self._lock:
            logger.info("Acquired lock")
            self._tasks[task.id] = task
            logger.info(f"Task {task.id} added to tasks dict")
            self._pending_queue.append(task.id)
            logger.info(f"Task {task.id} added to pending queue")
            logger.info(f"Pending queue size: {len(self._pending_queue)}")
            task.add_log("Task added to queue")
            logger.info("Task log updated")
            logger.info("Trying to start next task")
            await self._try_start_next_task()
            logger.info(f"=== Task {task.id} added successfully ===")
            return task.id

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task or None if not found
        """
        return self._tasks.get(task_id)

    async def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return list(self._tasks.values())

    async def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks by status.

        Args:
            status: Task status to filter by

        Returns:
            List of tasks with specified status
        """
        return [task for task in self._tasks.values() if task.status == status]

    async def get_tasks_by_type(self, task_type: TaskType) -> List[Task]:
        """Get tasks by type.

        Args:
            task_type: Task type to filter by

        Returns:
            List of tasks with specified type
        """
        return [task for task in self._tasks.values() if task.task_type == task_type]

    async def get_tasks_by_category(self, category: str) -> List[Task]:
        """Get tasks by category.

        Args:
            category: Task category to filter by

        Returns:
            List of tasks with specified category
        """
        return [task for task in self._tasks.values() if task.category == category]

    async def get_tasks_by_tag(self, tag: str) -> List[Task]:
        """Get tasks by tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of tasks with specified tag
        """
        return [task for task in self._tasks.values() if tag in task.tags]

    async def cancel_task(self, task_id: str, force: bool = False) -> bool:
        """Cancel task.

        Args:
            task_id: Task identifier
            force: Force cancel even if task is running

        Returns:
            True if task was cancelled, False otherwise
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            if task.status == TaskStatus.PENDING:
                if task_id in self._pending_queue:
                    self._pending_queue.remove(task_id)
                task.cancel()
                return True
            elif task.status == TaskStatus.RUNNING:
                if task_id in self._running_tasks:
                    self._running_tasks[task_id].cancel()
                    del self._running_tasks[task_id]
                task.cancel()
                await self._try_start_next_task()
                return True
            return False

    async def remove_task(self, task_id: str, force: bool = False) -> bool:
        """Remove task completely from the queue.

        Args:
            task_id: Task identifier
            force: Force remove even if task is running

        Returns:
            True if task was removed, False otherwise
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            if task.status == TaskStatus.RUNNING and (not force):
                return False
            if task.status == TaskStatus.RUNNING:
                if task_id in self._running_tasks:
                    self._running_tasks[task_id].cancel()
                    del self._running_tasks[task_id]
                task.cancel()
                await self._try_start_next_task()
            if task_id in self._pending_queue:
                self._pending_queue.remove(task_id)
            del self._tasks[task_id]
            return True

    async def pause_task(self, task_id: str) -> bool:
        """Pause task execution.

        Args:
            task_id: Task identifier

        Returns:
            True if task was paused, False otherwise
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status != TaskStatus.RUNNING:
                return False
            task.pause()
            return True

    async def resume_task(self, task_id: str) -> bool:
        """Resume paused task.

        Args:
            task_id: Task identifier

        Returns:
            True if task was resumed, False otherwise
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status != TaskStatus.PAUSED:
                return False
            task.resume()
            return True

    async def retry_task(self, task_id: str) -> bool:
        """Retry failed task.

        Args:
            task_id: Task identifier

        Returns:
            True if task was retried, False otherwise
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task or not task.can_retry():
                return False
            task.increment_retry()
            self._pending_queue.append(task_id)
            await self._try_start_next_task()
            return True

    async def get_task_summary(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed task summary with status information.

        Args:
            task_id: Task identifier

        Returns:
            Task summary or None if not found
        """
        task = self._tasks.get(task_id)
        if not task:
            return None
        return {
            "id": task.id,
            "type": task.task_type.value,
            "status": {
                "current": task.status.value,
                "description": task._get_status_description(),
                "progress": task.progress,
                "current_step": task.current_step,
            },
            "timing": {
                "created": task.created_at.isoformat(),
                "started": task.started_at.isoformat() if task.started_at else None,
                "completed": (
                    task.completed_at.isoformat() if task.completed_at else None
                ),
                "duration": task.get_duration(),
            },
            "error": (
                {
                    "message": task.error,
                    "code": task.error_code.value if task.error_code else None,
                    "details": task.error_details,
                }
                if task.error
                else None
            ),
            "retry": {
                "count": task.retry_count,
                "max": task.max_retries,
                "can_retry": task.can_retry(),
            },
            "result": task.result,
        }

    async def clear_completed(self) -> int:
        """Clear completed and failed tasks.

        Returns:
            Number of tasks cleared
        """
        async with self._lock:
            to_remove = []
            for task_id, task in self._tasks.items():
                if task.status in [
                    TaskStatus.COMPLETED,
                    TaskStatus.FAILED,
                    TaskStatus.CANCELLED,
                ]:
                    to_remove.append(task_id)
            for task_id in to_remove:
                del self._tasks[task_id]
            return len(to_remove)

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get detailed queue statistics.

        Returns:
            Detailed queue statistics
        """
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = len(
                [t for t in self._tasks.values() if t.status == status]
            )
        type_counts = {}
        for task_type in TaskType:
            type_counts[task_type.value] = len(
                [t for t in self._tasks.values() if t.task_type == task_type]
            )
        error_counts = {}
        for error_code in TaskErrorCode:
            error_counts[error_code.value] = len(
                [t for t in self._tasks.values() if t.error_code == error_code]
            )
        completed_tasks = [
            t for t in self._tasks.values() if t.status == TaskStatus.COMPLETED
        ]
        avg_duration = (
            sum((t.get_duration() or 0 for t in completed_tasks)) / len(completed_tasks)
            if completed_tasks
            else 0
        )
        failed_tasks = [
            t for t in self._tasks.values() if t.status == TaskStatus.FAILED
        ]
        retry_stats = {
            "total_retries": sum((t.retry_count for t in self._tasks.values())),
            "tasks_with_retries": len(
                [t for t in self._tasks.values() if t.retry_count > 0]
            ),
            "max_retries_reached": len(
                [t for t in failed_tasks if t.retry_count >= t.max_retries]
            ),
        }
        return {
            "summary": {
                "total_tasks": len(self._tasks),
                "max_concurrent": self.max_concurrent,
                "current_running": len(self._running_tasks),
                "queue_size": len(self._pending_queue),
            },
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "error_distribution": error_counts,
            "performance": {
                "average_duration_seconds": round(avg_duration, 2),
                "completed_tasks": len(completed_tasks),
                "failed_tasks": len(failed_tasks),
                "success_rate": (
                    round(len(completed_tasks) / len(self._tasks) * 100, 2)
                    if self._tasks
                    else 0
                ),
            },
            "retry_statistics": retry_stats,
            "recent_activity": {
                "last_24h": len(
                    [
                        t
                        for t in self._tasks.values()
                        if (datetime.now() - t.created_at).total_seconds() < 86400
                    ]
                ),
                "last_hour": len(
                    [
                        t
                        for t in self._tasks.values()
                        if (datetime.now() - t.created_at).total_seconds() < 3600
                    ]
                ),
            },
        }

    async def _try_start_next_task(self) -> None:
        """Try to start next pending task if there's capacity."""
        import logging

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Trying to start next task ===")
        logger.info(f"Running tasks: {len(self._running_tasks)}")
        logger.info(f"Max concurrent: {self.max_concurrent}")
        logger.info(f"Pending queue size: {len(self._pending_queue)}")
        if len(self._running_tasks) >= self.max_concurrent:
            logger.info("Max concurrent tasks reached, skipping")
            return
        if not self._pending_queue:
            logger.info("No pending tasks, skipping")
            return
        task_id = self._pending_queue.pop(0)
        logger.info(f"Popped task ID: {task_id}")
        if task_id not in self._tasks:
            logger.error(f"Task {task_id} not found in tasks dict")
            return
        task = self._tasks[task_id]
        logger.info(f"Found task: {task.task_type.value} - {task.id}")
        logger.info(f"Creating asyncio task for {task_id}")
        async_task = asyncio.create_task(self._execute_task(task))
        self._running_tasks[task_id] = async_task
        logger.info(f"Task {task_id} added to running tasks")
        logger.info(f"=== Next task started successfully ===")

    async def _execute_task(self, task: Task) -> None:
        """Execute a task.

        Args:
            task: Task to execute
        """
        import logging

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting task execution {task.id} ===")
        logger.info(f"Task type: {task.task_type.value}")
        logger.info(f"Task params: {task.params}")
        try:
            task.start()
            logger.info(f"Task {task.id} started successfully")
            if task.task_type == TaskType.DOCKER_PUSH:
                logger.info(f"Executing DOCKER_PUSH task {task.id}")
                await self._execute_docker_push_task(task)
            elif task.task_type == TaskType.DOCKER_BUILD:
                logger.info(f"Executing DOCKER_BUILD task {task.id}")
                await self._execute_docker_build_task(task)
            elif task.task_type == TaskType.DOCKER_PULL:
                logger.info(f"Executing DOCKER_PULL task {task.id}")
                await self._execute_docker_pull_task(task)
            elif task.task_type == TaskType.OLLAMA_PULL:
                logger.info(f"Executing OLLAMA_PULL task {task.id}")
                await self._execute_ollama_pull_task(task)
            elif task.task_type == TaskType.OLLAMA_RUN:
                logger.info(f"Executing OLLAMA_RUN task {task.id}")
                await self._execute_ollama_run_task(task)
            elif task.task_type == TaskType.CUSTOM_SCRIPT:
                logger.info(f"Executing CUSTOM_SCRIPT task {task.id}")
                await self._execute_custom_script_task(task)
            elif task.task_type == TaskType.CUSTOM_COMMAND:
                logger.info(f"Executing CUSTOM_COMMAND task {task.id}")
                await self._execute_custom_command_task(task)
            elif task.task_type == TaskType.SYSTEM_MONITOR:
                logger.info(f"Executing SYSTEM_MONITOR task {task.id}")
                await self._execute_system_monitor_task(task)
            elif task.task_type == TaskType.FTP_UPLOAD:
                logger.info(f"Executing FTP_UPLOAD task {task.id}")
                await self._execute_ftp_upload_task(task)
            elif task.task_type == TaskType.FTP_DOWNLOAD:
                logger.info(f"Executing FTP_DOWNLOAD task {task.id}")
                await self._execute_ftp_download_task(task)
            elif task.task_type == TaskType.FTP_LIST:
                logger.info(f"Executing FTP_LIST task {task.id}")
                await self._execute_ftp_list_task(task)
            elif task.task_type == TaskType.FTP_DELETE:
                logger.info(f"Executing FTP_DELETE task {task.id}")
                await self._execute_ftp_delete_task(task)
            elif task.task_type == TaskType.K8S_DEPLOYMENT_CREATE:
                logger.info(f"Executing K8S_DEPLOYMENT_CREATE task {task.id}")
                await self._execute_k8s_deployment_create_task(task)
            elif task.task_type == TaskType.K8S_POD_CREATE:
                logger.info(f"Executing K8S_POD_CREATE task {task.id}")
                await self._execute_k8s_pod_create_task(task)
            elif task.task_type == TaskType.K8S_POD_STATUS:
                logger.info(f"Executing K8S_POD_STATUS task {task.id}")
                await self._execute_k8s_pod_status_task(task)
            elif task.task_type == TaskType.K8S_POD_DELETE:
                logger.info(f"Executing K8S_POD_DELETE task {task.id}")
                await self._execute_k8s_pod_delete_task(task)
            elif task.task_type == TaskType.KIND_CLUSTER_CREATE:
                logger.info(f"Executing KIND_CLUSTER_CREATE task {task.id}")
                await self._execute_kind_cluster_create_task(task)
            elif task.task_type == TaskType.KIND_CLUSTER_DELETE:
                logger.info(f"Executing KIND_CLUSTER_DELETE task {task.id}")
                await self._execute_kind_cluster_delete_task(task)
            elif task.task_type == TaskType.KIND_CLUSTER_LIST:
                logger.info(f"Executing KIND_CLUSTER_LIST task {task.id}")
                await self._execute_kind_cluster_list_task(task)
            elif task.task_type == TaskType.KIND_CLUSTER_GET_NODES:
                logger.info(f"Executing KIND_CLUSTER_GET_NODES task {task.id}")
                await self._execute_kind_cluster_get_nodes_task(task)
            elif task.task_type == TaskType.KIND_LOAD_IMAGE:
                logger.info(f"Executing KIND_LOAD_IMAGE task {task.id}")
                await self._execute_kind_load_image_task(task)
            elif task.task_type == TaskType.SSL_OPERATION:
                logger.info(f"Executing SSL_OPERATION task {task.id}")
                await self._execute_ssl_operation_task(task)
            elif task.task_type in [
                TaskType.VECTOR_STORE_DEPLOY,
                TaskType.VECTOR_STORE_CONFIGURE,
                TaskType.VECTOR_STORE_SCALE,
                TaskType.VECTOR_STORE_UPDATE,
                TaskType.VECTOR_STORE_DELETE,
                TaskType.VECTOR_STORE_STATUS,
                TaskType.VECTOR_STORE_LOGS,
                TaskType.VECTOR_STORE_BACKUP,
                TaskType.VECTOR_STORE_RESTORE,
                TaskType.VECTOR_STORE_MONITOR,
            ]:
                logger.info(f"Executing VECTOR_STORE task {task.id}")
                await self._execute_vector_store_task(task)
            elif task.task_type in [
                TaskType.LLM_INFERENCE,
                TaskType.LLM_TRAIN,
                TaskType.LLM_FINE_TUNE,
                TaskType.LLM_EVALUATE,
                TaskType.LLM_DEPLOY,
                TaskType.LLM_SCALE,
                TaskType.LLM_MONITOR,
                TaskType.LLM_LOGS,
                TaskType.LLM_BACKUP,
                TaskType.LLM_RESTORE,
                TaskType.LLM_CONFIGURE,
                TaskType.LLM_DELETE,
            ]:
                logger.info(f"Executing LLM task {task.id}")
                await self._execute_llm_task(task)
            elif task.task_type in [
                TaskType.TEST_DISCOVERY,
                TaskType.TEST_RUN,
                TaskType.TEST_DEBUG,
                TaskType.TEST_COVERAGE,
                TaskType.TEST_LINT,
                TaskType.TEST_SECURITY,
                TaskType.TEST_PERFORMANCE,
                TaskType.TEST_INTEGRATION,
                TaskType.TEST_UNIT,
                TaskType.TEST_E2E,
                TaskType.TEST_CONFIGURE,
                TaskType.TEST_REPORT,
            ]:
                logger.info(f"Executing TEST task {task.id}")
                await self._execute_test_task(task)
            elif task.task_type in [
                TaskType.ARGOCD_INIT,
                TaskType.ARGOCD_DEPLOY,
                TaskType.ARGOCD_SYNC,
                TaskType.ARGOCD_ROLLBACK,
                TaskType.ARGOCD_DELETE,
                TaskType.ARGOCD_STATUS,
                TaskType.ARGOCD_LOGS,
                TaskType.ARGOCD_CONFIGURE,
                TaskType.ARGOCD_UPDATE,
                TaskType.ARGOCD_SCALE,
                TaskType.ARGOCD_MONITOR,
                TaskType.ARGOCD_BACKUP,
                TaskType.ARGOCD_RESTORE,
            ]:
                logger.info(f"Executing ARGOCD task {task.id}")
                await self._execute_argocd_task(task)
            elif task.task_type in [
                TaskType.DOCKER_NETWORK_LS,
                TaskType.DOCKER_NETWORK_INSPECT,
                TaskType.DOCKER_NETWORK_CREATE,
                TaskType.DOCKER_NETWORK_CONNECT,
                TaskType.DOCKER_NETWORK_DISCONNECT,
                TaskType.DOCKER_NETWORK_RM,
            ]:
                logger.info(f"Executing DOCKER_NETWORK task {task.id}")
                await self._execute_docker_network_task(task)
            elif task.task_type in [
                TaskType.DOCKER_VOLUME_LS,
                TaskType.DOCKER_VOLUME_CREATE,
                TaskType.DOCKER_VOLUME_INSPECT,
                TaskType.DOCKER_VOLUME_RM,
                TaskType.DOCKER_VOLUME_PRUNE,
            ]:
                logger.info(f"Executing DOCKER_VOLUME task {task.id}")
                await self._execute_docker_volume_task(task)
            elif task.task_type == TaskType.DOCKER_SEARCH_CLI:
                logger.info(f"Executing DOCKER_SEARCH_CLI task {task.id}")
                await self._execute_docker_search_task(task)
            elif task.task_type in [
                TaskType.DOCKER_HUB_IMAGES,
                TaskType.DOCKER_HUB_IMAGE_INFO,
                TaskType.DOCKER_HUB_SEARCH,
            ]:
                logger.info(f"Executing DOCKER_HUB task {task.id}")
                await self._execute_docker_hub_task(task)
            elif task.task_type == TaskType.DOCKER_TAG:
                logger.info(f"Executing DOCKER_TAG task {task.id}")
                await self._execute_docker_tag_task(task)
            elif task.task_type in [TaskType.SSH_CONNECT, TaskType.SSH_EXEC]:
                logger.info(f"Executing SSH task {task.id}")
                await self._execute_ssh_task(task)
            else:
                logger.warning(
                    f"Task type {task.task_type} not implemented, using generic executor"
                )
                await self._execute_generic_task(task)
            logger.info(f"Task {task.id} execution completed")
        except asyncio.CancelledError:
            logger.warning(f"Task {task.id} was cancelled")
            task.cancel()
        except CustomError as e:
            logger.error(
                f"Task {task.id} failed with exception: {str(e)}", exc_info=True
            )
            task.fail(str(e), TaskErrorCode.UNKNOWN_ERROR)
        finally:
            logger.info(f"Cleaning up task {task.id}")
            if task.id in self._running_tasks:
                del self._running_tasks[task.id]
                logger.info(f"Removed task {task.id} from running tasks")
            logger.info("Trying to start next task")
            await self._try_start_next_task()
        logger.info(f"=== Completed task execution {task.id} ===")



