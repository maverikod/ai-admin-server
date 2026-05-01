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
from .core import QueueCore

class TaskQueue:
    """Universal task queue for managing any type of operations."""

    def __init__(self):
        self.queueCore = QueueCore()

    async def add_task(self, task):
        return self.queueCore.add_task(task)

    async def get_task(self, task_id):
        return self.queueCore.get_task(task_id)

    async def get_all_tasks(self):
        return self.queueCore.get_all_tasks()

    async def get_tasks_by_status(self, status):
        return self.queueCore.get_tasks_by_status(status)

    async def get_tasks_by_type(self, task_type):
        return self.queueCore.get_tasks_by_type(task_type)

    async def get_tasks_by_category(self, category):
        return self.queueCore.get_tasks_by_category(category)

    async def get_tasks_by_tag(self, tag):
        return self.queueCore.get_tasks_by_tag(tag)

    async def cancel_task(self, task_id, force):
        return self.queueCore.cancel_task(task_id, force)

    async def remove_task(self, task_id, force):
        return self.queueCore.remove_task(task_id, force)

    async def pause_task(self, task_id):
        return self.queueCore.pause_task(task_id)

    async def resume_task(self, task_id):
        return self.queueCore.resume_task(task_id)

    async def retry_task(self, task_id):
        return self.queueCore.retry_task(task_id)

    async def get_task_summary(self, task_id):
        return self.queueCore.get_task_summary(task_id)

    async def clear_completed(self):
        return self.queueCore.clear_completed()

    async def get_queue_stats(self):
        return self.queueCore.get_queue_stats()

    async def _try_start_next_task(self):
        return self.queueCore._try_start_next_task()

    async def _execute_task(self, task):
        return self.queueCore._execute_task(task)

    def _create_ftp_connection(self, ftp_config, task):
        return self.ftpExecutor._create_ftp_connection(ftp_config, task)

    async def _execute_ftp_upload_task(self, task):
        return self.ftpExecutor._execute_ftp_upload_task(task)

    async def _execute_ftp_download_task(self, task):
        return self.ftpExecutor._execute_ftp_download_task(task)

    async def _execute_ftp_list_task(self, task):
        return self.ftpExecutor._execute_ftp_list_task(task)

    async def _execute_ftp_delete_task(self, task):
        return self.ftpExecutor._execute_ftp_delete_task(task)

    async def _execute_docker_push_task(self, task):
        return self.dockerExecutor._execute_docker_push_task(task)

    async def _execute_docker_build_task(self, task):
        return self.dockerExecutor._execute_docker_build_task(task)

    async def _execute_docker_pull_task(self, task):
        return self.dockerExecutor._execute_docker_pull_task(task)

    async def _execute_docker_network_task(self, task):
        return self.dockerExecutor._execute_docker_network_task(task)

    async def _execute_docker_volume_task(self, task):
        return self.dockerExecutor._execute_docker_volume_task(task)

    async def _execute_docker_search_task(self, task):
        return self.dockerExecutor._execute_docker_search_task(task)

    async def _execute_docker_hub_task(self, task):
        return self.dockerExecutor._execute_docker_hub_task(task)

    async def _execute_docker_tag_task(self, task):
        return self.dockerExecutor._execute_docker_tag_task(task)

    async def _execute_k8s_deployment_create_task(self, task):
        return self.k8sExecutor._execute_k8s_deployment_create_task(task)

    async def _execute_k8s_pod_create_task(self, task):
        return self.k8sExecutor._execute_k8s_pod_create_task(task)

    async def _execute_k8s_pod_status_task(self, task):
        return self.k8sExecutor._execute_k8s_pod_status_task(task)

    async def _execute_k8s_pod_delete_task(self, task):
        return self.k8sExecutor._execute_k8s_pod_delete_task(task)

    async def _execute_kind_cluster_create_task(self, task):
        return self.kindExecutor._execute_kind_cluster_create_task(task)

    async def _execute_kind_cluster_delete_task(self, task):
        return self.kindExecutor._execute_kind_cluster_delete_task(task)

    async def _execute_kind_cluster_list_task(self, task):
        return self.kindExecutor._execute_kind_cluster_list_task(task)

    async def _execute_kind_cluster_get_nodes_task(self, task):
        return self.kindExecutor._execute_kind_cluster_get_nodes_task(task)

    async def _execute_kind_load_image_task(self, task):
        return self.kindExecutor._execute_kind_load_image_task(task)

    async def _execute_ollama_pull_task(self, task):
        return self.ollamaExecutor._execute_ollama_pull_task(task)

    async def _execute_ollama_run_task(self, task):
        return self.ollamaExecutor._execute_ollama_run_task(task)

    async def _execute_custom_script_task(self, task):
        return self.miscExecutor._execute_custom_script_task(task)

    async def _execute_custom_command_task(self, task):
        return self.miscExecutor._execute_custom_command_task(task)

    async def _execute_system_monitor_task(self, task):
        return self.miscExecutor._execute_system_monitor_task(task)

    async def _execute_generic_task(self, task):
        return self.miscExecutor._execute_generic_task(task)

    async def _execute_ssl_operation_task(self, task):
        return self.miscExecutor._execute_ssl_operation_task(task)

    async def _execute_vector_store_task(self, task):
        return self.miscExecutor._execute_vector_store_task(task)

    async def _execute_llm_task(self, task):
        return self.miscExecutor._execute_llm_task(task)

    async def _execute_test_task(self, task):
        return self.miscExecutor._execute_test_task(task)

    async def _execute_argocd_task(self, task):
        return self.miscExecutor._execute_argocd_task(task)

    async def _execute_ssh_task(self, task):
        return self.miscExecutor._execute_ssh_task(task)



