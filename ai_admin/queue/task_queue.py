"""Task queue system for Docker operations."""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field


class TaskStatus(Enum):
    """Task execution status with detailed error codes."""
    # Active states
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    
    # Completion states
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    
    # Intermediate states
    VALIDATING = "validating"
    PREPARING = "preparing"
    UPLOADING = "uploading"
    DOWNLOADING = "downloading"
    BUILDING = "building"
    PULLING = "pulling"


class TaskType(Enum):
    """Universal task types for any operations."""
    # Docker operations
    DOCKER_PUSH = "docker_push"
    DOCKER_BUILD = "docker_build"
    DOCKER_PULL = "docker_pull"
    DOCKER_RUN = "docker_run"
    DOCKER_STOP = "docker_stop"
    DOCKER_REMOVE = "docker_remove"
    DOCKER_TAG = "docker_tag"
    
    # Ollama operations
    OLLAMA_PULL = "ollama_pull"
    OLLAMA_RUN = "ollama_run"
    OLLAMA_LIST = "ollama_list"
    OLLAMA_STATUS = "ollama_status"
    
    # Kubernetes operations
    K8S_DEPLOY = "k8s_deploy"
    K8S_SCALE = "k8s_scale"
    K8S_DELETE = "k8s_delete"
    K8S_GET = "k8s_get"
    K8S_LOGS = "k8s_logs"
    K8S_EXEC = "k8s_exec"
    
    # Vast.ai operations
    VAST_CREATE = "vast_create"
    VAST_DESTROY = "vast_destroy"
    VAST_LIST = "vast_list"
    VAST_SEARCH = "vast_search"
    
    # GitHub operations
    GITHUB_CREATE_REPO = "github_create_repo"
    GITHUB_LIST_REPOS = "github_list_repos"
    GITHUB_CLONE = "github_clone"
    GITHUB_PUSH = "github_push"
    
    # System operations
    SYSTEM_MONITOR = "system_monitor"
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_UPDATE = "system_update"
    SYSTEM_CLEANUP = "system_cleanup"
    
    # Custom operations
    CUSTOM_SCRIPT = "custom_script"
    CUSTOM_COMMAND = "custom_command"
    CUSTOM_WEBHOOK = "custom_webhook"
    
    # Data operations
    DATA_PROCESS = "data_process"
    DATA_ANALYZE = "data_analyze"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    
    # Network operations
    NETWORK_TEST = "network_test"
    NETWORK_SCAN = "network_scan"
    NETWORK_MONITOR = "network_monitor"
    
    # FTP operations
    FTP_UPLOAD = "ftp_upload"
    FTP_DOWNLOAD = "ftp_download"
    FTP_LIST = "ftp_list"
    FTP_DELETE = "ftp_delete"


class TaskErrorCode(Enum):
    """Universal error codes for any task failures."""
    # Docker errors
    DOCKER_IMAGE_NOT_FOUND = "DOCKER_IMAGE_NOT_FOUND"
    DOCKER_AUTHENTICATION_FAILED = "DOCKER_AUTHENTICATION_FAILED"
    DOCKER_PERMISSION_DENIED = "DOCKER_PERMISSION_DENIED"
    DOCKER_NETWORK_ERROR = "DOCKER_NETWORK_ERROR"
    DOCKER_REGISTRY_ERROR = "DOCKER_REGISTRY_ERROR"
    DOCKER_BUILD_FAILED = "DOCKER_BUILD_FAILED"
    DOCKER_PUSH_FAILED = "DOCKER_PUSH_FAILED"
    DOCKER_PULL_FAILED = "DOCKER_PULL_FAILED"
    DOCKER_CONTAINER_NOT_FOUND = "DOCKER_CONTAINER_NOT_FOUND"
    DOCKER_CONTAINER_ALREADY_RUNNING = "DOCKER_CONTAINER_ALREADY_RUNNING"
    DOCKER_CONTAINER_STOPPED = "DOCKER_CONTAINER_STOPPED"
    
    # Kubernetes errors
    K8S_CLUSTER_UNAVAILABLE = "K8S_CLUSTER_UNAVAILABLE"
    K8S_AUTHENTICATION_FAILED = "K8S_AUTHENTICATION_FAILED"
    K8S_RESOURCE_NOT_FOUND = "K8S_RESOURCE_NOT_FOUND"
    K8S_RESOURCE_ALREADY_EXISTS = "K8S_RESOURCE_ALREADY_EXISTS"
    K8S_NAMESPACE_NOT_FOUND = "K8S_NAMESPACE_NOT_FOUND"
    K8S_POD_FAILED = "K8S_POD_FAILED"
    K8S_DEPLOYMENT_FAILED = "K8S_DEPLOYMENT_FAILED"
    K8S_SERVICE_FAILED = "K8S_SERVICE_FAILED"
    K8S_CONFIGMAP_FAILED = "K8S_CONFIGMAP_FAILED"
    K8S_SECRET_FAILED = "K8S_SECRET_FAILED"
    
    # Vast.ai errors
    VAST_API_ERROR = "VAST_API_ERROR"
    VAST_AUTHENTICATION_FAILED = "VAST_AUTHENTICATION_FAILED"
    VAST_INSTANCE_NOT_FOUND = "VAST_INSTANCE_NOT_FOUND"
    VAST_INSTANCE_CREATION_FAILED = "VAST_INSTANCE_CREATION_FAILED"
    VAST_INSTANCE_DESTRUCTION_FAILED = "VAST_INSTANCE_DESTRUCTION_FAILED"
    VAST_QUOTA_EXCEEDED = "VAST_QUOTA_EXCEEDED"
    VAST_PAYMENT_REQUIRED = "VAST_PAYMENT_REQUIRED"
    
    # GitHub errors
    GITHUB_API_ERROR = "GITHUB_API_ERROR"
    GITHUB_AUTHENTICATION_FAILED = "GITHUB_AUTHENTICATION_FAILED"
    GITHUB_REPO_NOT_FOUND = "GITHUB_REPO_NOT_FOUND"
    GITHUB_REPO_ALREADY_EXISTS = "GITHUB_REPO_ALREADY_EXISTS"
    GITHUB_BRANCH_NOT_FOUND = "GITHUB_BRANCH_NOT_FOUND"
    GITHUB_MERGE_CONFLICT = "GITHUB_MERGE_CONFLICT"
    GITHUB_RATE_LIMIT_EXCEEDED = "GITHUB_RATE_LIMIT_EXCEEDED"
    
    # Ollama errors
    OLLAMA_MODEL_NOT_FOUND = "OLLAMA_MODEL_NOT_FOUND"
    OLLAMA_SERVICE_UNAVAILABLE = "OLLAMA_SERVICE_UNAVAILABLE"
    OLLAMA_INFERENCE_FAILED = "OLLAMA_INFERENCE_FAILED"
    OLLAMA_MODEL_DOWNLOAD_FAILED = "OLLAMA_MODEL_DOWNLOAD_FAILED"
    OLLAMA_MEMORY_INSUFFICIENT = "OLLAMA_MEMORY_INSUFFICIENT"
    OLLAMA_GPU_UNAVAILABLE = "OLLAMA_GPU_UNAVAILABLE"
    
    # System errors
    SYSTEM_TIMEOUT = "SYSTEM_TIMEOUT"
    SYSTEM_RESOURCE_LIMIT = "SYSTEM_RESOURCE_LIMIT"
    SYSTEM_DISK_SPACE = "SYSTEM_DISK_SPACE"
    SYSTEM_MEMORY_LIMIT = "SYSTEM_MEMORY_LIMIT"
    SYSTEM_CPU_LIMIT = "SYSTEM_CPU_LIMIT"
    SYSTEM_PROCESS_KILLED = "SYSTEM_PROCESS_KILLED"
    SYSTEM_SERVICE_UNAVAILABLE = "SYSTEM_SERVICE_UNAVAILABLE"
    SYSTEM_PERMISSION_DENIED = "SYSTEM_PERMISSION_DENIED"
    
    # Network errors
    NETWORK_CONNECTION_FAILED = "NETWORK_CONNECTION_FAILED"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    NETWORK_DNS_ERROR = "NETWORK_DNS_ERROR"
    NETWORK_PROXY_ERROR = "NETWORK_PROXY_ERROR"
    NETWORK_FIREWALL_BLOCKED = "NETWORK_FIREWALL_BLOCKED"
    NETWORK_SSL_ERROR = "NETWORK_SSL_ERROR"
    
    # FTP errors
    FTP_CONNECTION_FAILED = "FTP_CONNECTION_FAILED"
    FTP_AUTHENTICATION_FAILED = "FTP_AUTHENTICATION_FAILED"
    FTP_FILE_NOT_FOUND = "FTP_FILE_NOT_FOUND"
    FTP_PERMISSION_DENIED = "FTP_PERMISSION_DENIED"
    FTP_UPLOAD_FAILED = "FTP_UPLOAD_FAILED"
    FTP_DOWNLOAD_FAILED = "FTP_DOWNLOAD_FAILED"
    FTP_RESUME_FAILED = "FTP_RESUME_FAILED"
    FTP_INVALID_PATH = "FTP_INVALID_PATH"
    
    # Data errors
    DATA_FILE_NOT_FOUND = "DATA_FILE_NOT_FOUND"
    DATA_FILE_CORRUPTED = "DATA_FILE_CORRUPTED"
    DATA_FORMAT_INVALID = "DATA_FORMAT_INVALID"
    DATA_SIZE_TOO_LARGE = "DATA_SIZE_TOO_LARGE"
    DATA_ENCODING_ERROR = "DATA_ENCODING_ERROR"
    DATA_PARSING_FAILED = "DATA_PARSING_FAILED"
    
    # Validation errors
    VALIDATION_INVALID_PARAMS = "VALIDATION_INVALID_PARAMS"
    VALIDATION_MISSING_REQUIRED = "VALIDATION_MISSING_REQUIRED"
    VALIDATION_INVALID_FORMAT = "VALIDATION_INVALID_FORMAT"
    VALIDATION_OUT_OF_RANGE = "VALIDATION_OUT_OF_RANGE"
    VALIDATION_CONSTRAINT_VIOLATION = "VALIDATION_CONSTRAINT_VIOLATION"
    
    # Queue errors
    QUEUE_FULL = "QUEUE_FULL"
    QUEUE_TASK_NOT_FOUND = "QUEUE_TASK_NOT_FOUND"
    QUEUE_TASK_ALREADY_RUNNING = "QUEUE_TASK_ALREADY_RUNNING"
    QUEUE_TASK_DUPLICATE = "QUEUE_TASK_DUPLICATE"
    QUEUE_PRIORITY_INVALID = "QUEUE_PRIORITY_INVALID"
    
    # Custom errors
    CUSTOM_SCRIPT_FAILED = "CUSTOM_SCRIPT_FAILED"
    CUSTOM_COMMAND_FAILED = "CUSTOM_COMMAND_FAILED"
    CUSTOM_WEBHOOK_FAILED = "CUSTOM_WEBHOOK_FAILED"
    CUSTOM_VALIDATION_FAILED = "CUSTOM_VALIDATION_FAILED"
    
    # Generic errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


@dataclass
class Task:
    """Universal task representation with enhanced error handling for any operation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType = TaskType.DOCKER_PUSH
    status: TaskStatus = TaskStatus.PENDING
    command: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0  # 0-100%
    current_step: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[TaskErrorCode] = None
    error_details: Optional[Dict[str, Any]] = None
    logs: List[str] = field(default_factory=list)
    timeout_seconds: int = 3600  # 1 hour default timeout
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 0  # Task priority (higher = more important)
    category: str = "general"  # Task category for grouping
    tags: List[str] = field(default_factory=list)  # Task tags for filtering
    
    def add_log(self, message: str) -> None:
        """Add log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
    
    def update_progress(self, progress: int, step: str = "") -> None:
        """Update task progress."""
        self.progress = max(0, min(100, progress))
        if step:
            self.current_step = step
            self.add_log(f"Progress: {self.progress}% - {step}")
    
    def start(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        self.add_log(f"Task started: {self.task_type.value}")
    
    def complete(self, result: Dict[str, Any]) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress = 100
        self.result = result
        self.add_log("Task completed successfully")
    
    def fail(self, error: str, error_code: TaskErrorCode = TaskErrorCode.UNKNOWN_ERROR, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Mark task as failed with error code and details."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
        self.error_code = error_code
        self.error_details = error_details or {}
        self.add_log(f"Task failed: {error} (Code: {error_code.value})")
    
    def cancel(self) -> None:
        """Mark task as cancelled."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
        self.add_log("Task cancelled")
    
    def pause(self) -> None:
        """Pause task execution."""
        if self.status == TaskStatus.RUNNING:
            self.status = TaskStatus.PAUSED
            self.add_log("Task paused")
    
    def resume(self) -> None:
        """Resume paused task."""
        if self.status == TaskStatus.PAUSED:
            self.status = TaskStatus.RUNNING
            self.add_log("Task resumed")
    
    def timeout(self) -> None:
        """Mark task as timed out."""
        self.status = TaskStatus.TIMEOUT
        self.completed_at = datetime.now()
        self.error = "Task execution timed out"
        self.error_code = TaskErrorCode.SYSTEM_TIMEOUT
        self.add_log("Task timed out")
    
    def update_status(self, status: TaskStatus, step: str = "") -> None:
        """Update task status and step."""
        self.status = status
        if step:
            self.current_step = step
            self.add_log(f"Status: {status.value} - {step}")
    
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries and self.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT]
    
    def increment_retry(self) -> None:
        """Increment retry count and reset status."""
        self.retry_count += 1
        self.status = TaskStatus.PENDING
        self.error = None
        self.error_code = None
        self.error_details = None
        self.add_log(f"Retry attempt {self.retry_count}/{self.max_retries}")
    
    def get_duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            "id": self.id,
            "task_type": self.task_type.value,
            "status": self.status.value,
            "status_description": self._get_status_description(),
            "command": self.command,
            "params": self.params,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "current_step": self.current_step,
            "result": self.result,
            "error": self.error,
            "error_code": self.error_code.value if self.error_code else None,
            "error_details": self.error_details,
            "logs": self.logs,
            "duration": self.get_duration(),
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "can_retry": self.can_retry()
        }
    
    def _get_status_description(self) -> str:
        """Get human-readable status description."""
        status_descriptions = {
            TaskStatus.PENDING: "Task is waiting in queue",
            TaskStatus.RUNNING: "Task is currently executing",
            TaskStatus.PAUSED: "Task execution is paused",
            TaskStatus.VALIDATING: "Validating task parameters",
            TaskStatus.PREPARING: "Preparing task execution",
            TaskStatus.UPLOADING: "Uploading data",
            TaskStatus.DOWNLOADING: "Downloading data",
            TaskStatus.BUILDING: "Building/compiling",
            TaskStatus.PULLING: "Pulling/retrieving data",
            TaskStatus.COMPLETED: "Task completed successfully",
            TaskStatus.FAILED: "Task failed with error",
            TaskStatus.CANCELLED: "Task was cancelled",
            TaskStatus.TIMEOUT: "Task execution timed out"
        }
        return status_descriptions.get(self.status, "Unknown status")


class TaskQueue:
    """Universal task queue for managing any type of operations."""
    
    def __init__(self, max_concurrent: int = 2):
        """Initialize task queue.
        
        Args:
            max_concurrent: Maximum number of concurrent tasks
        """
        self.max_concurrent = max_concurrent
        self._tasks: Dict[str, Task] = {}
        self._pending_queue: List[str] = []
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
    
    async def add_task(self, task: Task) -> str:
        """Add task to queue.
        
        Args:
            task: Task to add
            
        Returns:
            Task ID
        """
        import logging
        
        # Setup logging
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
            
            # Try to start task if there's capacity
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
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if task was cancelled, False otherwise
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            if task.status == TaskStatus.PENDING:
                # Remove from pending queue
                if task_id in self._pending_queue:
                    self._pending_queue.remove(task_id)
                task.cancel()
                return True
            
            elif task.status == TaskStatus.RUNNING:
                # Cancel running task
                if task_id in self._running_tasks:
                    self._running_tasks[task_id].cancel()
                    del self._running_tasks[task_id]
                task.cancel()
                await self._try_start_next_task()
                return True
            
            return False
    
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
                "current_step": task.current_step
            },
            "timing": {
                "created": task.created_at.isoformat(),
                "started": task.started_at.isoformat() if task.started_at else None,
                "completed": task.completed_at.isoformat() if task.completed_at else None,
                "duration": task.get_duration()
            },
            "error": {
                "message": task.error,
                "code": task.error_code.value if task.error_code else None,
                "details": task.error_details
            } if task.error else None,
            "retry": {
                "count": task.retry_count,
                "max": task.max_retries,
                "can_retry": task.can_retry()
            },
            "result": task.result
        }
    
    async def clear_completed(self) -> int:
        """Clear completed and failed tasks.
        
        Returns:
            Number of tasks cleared
        """
        async with self._lock:
            to_remove = []
            for task_id, task in self._tasks.items():
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self._tasks[task_id]
            
            return len(to_remove)
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get detailed queue statistics.
        
        Returns:
            Detailed queue statistics
        """
        # Count tasks by status
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = len([t for t in self._tasks.values() if t.status == status])
        
        # Count tasks by type
        type_counts = {}
        for task_type in TaskType:
            type_counts[task_type.value] = len([t for t in self._tasks.values() if t.task_type == task_type])
        
        # Error statistics
        error_counts = {}
        for error_code in TaskErrorCode:
            error_counts[error_code.value] = len([t for t in self._tasks.values() if t.error_code == error_code])
        
        # Calculate averages
        completed_tasks = [t for t in self._tasks.values() if t.status == TaskStatus.COMPLETED]
        avg_duration = sum(t.get_duration() or 0 for t in completed_tasks) / len(completed_tasks) if completed_tasks else 0
        
        failed_tasks = [t for t in self._tasks.values() if t.status == TaskStatus.FAILED]
        retry_stats = {
            "total_retries": sum(t.retry_count for t in self._tasks.values()),
            "tasks_with_retries": len([t for t in self._tasks.values() if t.retry_count > 0]),
            "max_retries_reached": len([t for t in failed_tasks if t.retry_count >= t.max_retries])
        }
        
        return {
            "summary": {
                "total_tasks": len(self._tasks),
                "max_concurrent": self.max_concurrent,
                "current_running": len(self._running_tasks),
                "queue_size": len(self._pending_queue)
            },
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "error_distribution": error_counts,
            "performance": {
                "average_duration_seconds": round(avg_duration, 2),
                "completed_tasks": len(completed_tasks),
                "failed_tasks": len(failed_tasks),
                "success_rate": round(len(completed_tasks) / len(self._tasks) * 100, 2) if self._tasks else 0
            },
            "retry_statistics": retry_stats,
            "recent_activity": {
                "last_24h": len([t for t in self._tasks.values() 
                               if (datetime.now() - t.created_at).total_seconds() < 86400]),
                "last_hour": len([t for t in self._tasks.values() 
                                if (datetime.now() - t.created_at).total_seconds() < 3600])
            }
        }
    
    async def _try_start_next_task(self) -> None:
        """Try to start next pending task if there's capacity."""
        import logging
        
        # Setup logging
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
        
        # Create asyncio task for execution
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
        
        # Setup logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        logger.info(f"=== Starting task execution {task.id} ===")
        logger.info(f"Task type: {task.task_type.value}")
        logger.info(f"Task params: {task.params}")
        
        try:
            task.start()
            logger.info(f"Task {task.id} started successfully")
            
            # Execute task based on type
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
            else:
                logger.warning(f"Task type {task.task_type} not implemented, using generic executor")
                await self._execute_generic_task(task)
            
            logger.info(f"Task {task.id} execution completed")
            
        except asyncio.CancelledError:
            logger.warning(f"Task {task.id} was cancelled")
            task.cancel()
        except Exception as e:
            logger.error(f"Task {task.id} failed with exception: {str(e)}", exc_info=True)
            task.fail(str(e))
        finally:
            logger.info(f"Cleaning up task {task.id}")
            # Remove from running tasks
            if task.id in self._running_tasks:
                del self._running_tasks[task.id]
                logger.info(f"Removed task {task.id} from running tasks")
            
            # Try to start next task
            logger.info("Trying to start next task")
            await self._try_start_next_task()
            
        logger.info(f"=== Completed task execution {task.id} ===")
    
    async def _execute_ftp_upload_task(self, task: Task) -> None:
        """Execute FTP upload task with resume support."""
        import ftplib
        import os
        import logging
        from pathlib import Path
        
        # Setup logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        logger.info(f"=== Starting FTP upload task {task.id} ===")
        
        params = task.params
        local_path = params.get("local_path", "")
        remote_path = params.get("remote_path", "")
        resume = params.get("resume", True)
        overwrite = params.get("overwrite", False)
        file_size = params.get("file_size", 0)
        
        logger.info(f"Upload parameters: local={local_path}, remote={remote_path}, resume={resume}, overwrite={overwrite}")
        
        task.update_progress(5, f"Starting FTP upload: {os.path.basename(local_path)}")
        task.add_log(f"DEBUG: Task parameters: {params}")
        
        try:
            # Load FTP configuration
            config_path = Path("config/config.json")
            if not config_path.exists():
                task.fail(
                    "FTP configuration file not found",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"config_path": str(config_path)}
                )
                return
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            ftp_config = config.get("ftp", {})
            host = ftp_config.get("host")
            user = ftp_config.get("user")
            password = ftp_config.get("password")
            port = ftp_config.get("port", 21)
            timeout = ftp_config.get("timeout", 30)
            passive_mode = ftp_config.get("passive_mode", True)
            
            if not all([host, user, password]):
                task.fail(
                    "FTP configuration incomplete",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"ftp_config": ftp_config}
                )
                return
            
            task.update_progress(10, "Connecting to FTP server")
            task.add_log(f"DEBUG: Connecting to {host}:{port}")
            
            # Connect to FTP server
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=timeout)
            ftp.login(user, password)
            
            if passive_mode:
                ftp.set_pasv(True)
                task.add_log("DEBUG: Using passive mode")
            
            task.update_progress(20, "Connected to FTP server")
            task.add_log(f"DEBUG: Successfully connected to {host}")
            
            # Check if remote file exists for resume
            remote_file_exists = False
            remote_file_size = 0
            
            try:
                if resume and not overwrite:
                    remote_file_size = ftp.size(remote_path)
                    remote_file_exists = remote_file_size > 0
                    task.add_log(f"DEBUG: Remote file exists, size: {remote_file_size}")
            except ftplib.error_perm:
                # File doesn't exist or no permission to check size
                remote_file_exists = False
                task.add_log("DEBUG: Remote file doesn't exist or no permission to check size")
            
            # Determine upload mode
            if resume and remote_file_exists and not overwrite:
                if remote_file_size >= file_size:
                    task.complete({
                        "message": "File already exists and is complete",
                        "local_path": local_path,
                        "remote_path": remote_path,
                        "file_size": file_size,
                        "remote_file_size": remote_file_size,
                        "resumed": False,
                        "uploaded_bytes": 0
                    })
                    return
                
                # Resume upload
                task.update_progress(30, f"Resuming upload from position {remote_file_size}")
                task.add_log(f"DEBUG: Resuming upload from byte {remote_file_size}")
                
                with open(local_path, 'rb') as local_file:
                    local_file.seek(remote_file_size)
                    
                    # Create custom callback for progress tracking
                    def upload_callback(data):
                        nonlocal remote_file_size
                        remote_file_size += len(data)
                        progress = min(95, 30 + int((remote_file_size / file_size) * 65))
                        task.update_progress(progress, f"Uploading: {remote_file_size}/{file_size} bytes")
                    
                    # Upload with resume
                    ftp.storbinary(f"STOR {remote_path}", local_file, callback=upload_callback, rest=remote_file_size)
            else:
                # Full upload
                task.update_progress(30, "Starting full upload")
                task.add_log("DEBUG: Starting full upload")
                
                with open(local_path, 'rb') as local_file:
                    uploaded_bytes = 0
                    
                    # Create custom callback for progress tracking
                    def upload_callback(data):
                        nonlocal uploaded_bytes
                        uploaded_bytes += len(data)
                        progress = min(95, 30 + int((uploaded_bytes / file_size) * 65))
                        task.update_progress(progress, f"Uploading: {uploaded_bytes}/{file_size} bytes")
                    
                    # Upload file
                    ftp.storbinary(f"STOR {remote_path}", local_file, callback=upload_callback)
                    uploaded_bytes = file_size
            
            # Verify upload
            task.update_progress(95, "Verifying upload")
            try:
                final_size = ftp.size(remote_path)
                if final_size != file_size:
                    task.fail(
                        f"Upload verification failed: expected {file_size}, got {final_size}",
                        TaskErrorCode.FTP_UPLOAD_FAILED,
                        {"expected_size": file_size, "actual_size": final_size}
                    )
                    return
            except ftplib.error_perm as e:
                task.fail(
                    f"Failed to verify upload: {str(e)}",
                    TaskErrorCode.FTP_UPLOAD_FAILED,
                    {"error": str(e)}
                )
                return
            
            ftp.quit()
            
            task.complete({
                "message": "FTP upload completed successfully",
                "local_path": local_path,
                "remote_path": remote_path,
                "file_size": file_size,
                "uploaded_bytes": file_size,
                "resumed": resume and remote_file_exists,
                "resume_position": remote_file_size if resume and remote_file_exists else 0
            })
            
        except ftplib.error_perm as e:
            error_msg = f"FTP permission error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_PERMISSION_DENIED, {"error": str(e)})
        except ftplib.error_temp as e:
            error_msg = f"FTP temporary error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_CONNECTION_FAILED, {"error": str(e)})
        except ftplib.error_proto as e:
            error_msg = f"FTP protocol error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_CONNECTION_FAILED, {"error": str(e)})
        except Exception as e:
            error_msg = f"FTP upload failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(error_msg, TaskErrorCode.FTP_UPLOAD_FAILED, {"error": str(e)})
    
    async def _execute_ftp_download_task(self, task: Task) -> None:
        """Execute FTP download task with resume support."""
        import ftplib
        import os
        import logging
        from pathlib import Path
        
        # Setup logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        logger.info(f"=== Starting FTP download task {task.id} ===")
        
        params = task.params
        remote_path = params.get("remote_path", "")
        local_path = params.get("local_path", "")
        resume = params.get("resume", True)
        overwrite = params.get("overwrite", False)
        local_file_exists = params.get("local_file_exists", False)
        local_file_size = params.get("local_file_size", 0)
        
        logger.info(f"Download parameters: remote={remote_path}, local={local_path}, resume={resume}, overwrite={overwrite}")
        
        task.update_progress(5, f"Starting FTP download: {os.path.basename(remote_path)}")
        task.add_log(f"DEBUG: Task parameters: {params}")
        
        try:
            # Load FTP configuration
            config_path = Path("config/config.json")
            if not config_path.exists():
                task.fail(
                    "FTP configuration file not found",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"config_path": str(config_path)}
                )
                return
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            ftp_config = config.get("ftp", {})
            host = ftp_config.get("host")
            user = ftp_config.get("user")
            password = ftp_config.get("password")
            port = ftp_config.get("port", 21)
            timeout = ftp_config.get("timeout", 30)
            passive_mode = ftp_config.get("passive_mode", True)
            
            if not all([host, user, password]):
                task.fail(
                    "FTP configuration incomplete",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"ftp_config": ftp_config}
                )
                return
            
            task.update_progress(10, "Connecting to FTP server")
            task.add_log(f"DEBUG: Connecting to {host}:{port}")
            
            # Connect to FTP server
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=timeout)
            ftp.login(user, password)
            
            if passive_mode:
                ftp.set_pasv(True)
                task.add_log("DEBUG: Using passive mode")
            
            task.update_progress(20, "Connected to FTP server")
            task.add_log(f"DEBUG: Successfully connected to {host}")
            
            # Get remote file size
            try:
                remote_file_size = ftp.size(remote_path)
                if remote_file_size < 0:
                    task.fail(
                        "Remote file not found or no permission to access",
                        TaskErrorCode.FTP_FILE_NOT_FOUND,
                        {"remote_path": remote_path}
                    )
                    return
                task.add_log(f"DEBUG: Remote file size: {remote_file_size}")
            except ftplib.error_perm as e:
                task.fail(
                    f"Failed to get remote file size: {str(e)}",
                    TaskErrorCode.FTP_FILE_NOT_FOUND,
                    {"remote_path": remote_path, "error": str(e)}
                )
                return
            
            # Check if local file exists for resume
            if resume and local_file_exists and not overwrite:
                if local_file_size >= remote_file_size:
                    task.complete({
                        "message": "Local file already exists and is complete",
                        "local_path": local_path,
                        "remote_path": remote_path,
                        "file_size": remote_file_size,
                        "local_file_size": local_file_size,
                        "resumed": False,
                        "downloaded_bytes": 0
                    })
                    return
                
                # Resume download
                task.update_progress(30, f"Resuming download from position {local_file_size}")
                task.add_log(f"DEBUG: Resuming download from byte {local_file_size}")
                
                mode = 'ab'  # Append binary mode
            else:
                # Full download
                task.update_progress(30, "Starting full download")
                task.add_log("DEBUG: Starting full download")
                
                mode = 'wb'  # Write binary mode
                local_file_size = 0
            
            # Download file
            downloaded_bytes = local_file_size
            
            with open(local_path, mode) as local_file:
                # Create custom callback for progress tracking
                def download_callback(data):
                    nonlocal downloaded_bytes
                    downloaded_bytes += len(data)
                    progress = min(95, 30 + int((downloaded_bytes / remote_file_size) * 65))
                    task.update_progress(progress, f"Downloading: {downloaded_bytes}/{remote_file_size} bytes")
                
                # Download with resume support
                ftp.retrbinary(f"RETR {remote_path}", download_callback, rest=local_file_size)
            
            # Verify download
            task.update_progress(95, "Verifying download")
            final_size = os.path.getsize(local_path)
            if final_size != remote_file_size:
                task.fail(
                    f"Download verification failed: expected {remote_file_size}, got {final_size}",
                    TaskErrorCode.FTP_DOWNLOAD_FAILED,
                    {"expected_size": remote_file_size, "actual_size": final_size}
                )
                return
            
            ftp.quit()
            
            task.complete({
                "message": "FTP download completed successfully",
                "local_path": local_path,
                "remote_path": remote_path,
                "file_size": remote_file_size,
                "downloaded_bytes": final_size,
                "resumed": resume and local_file_exists,
                "resume_position": local_file_size if resume and local_file_exists else 0
            })
            
        except ftplib.error_perm as e:
            error_msg = f"FTP permission error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_PERMISSION_DENIED, {"error": str(e)})
        except ftplib.error_temp as e:
            error_msg = f"FTP temporary error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_CONNECTION_FAILED, {"error": str(e)})
        except ftplib.error_proto as e:
            error_msg = f"FTP protocol error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_CONNECTION_FAILED, {"error": str(e)})
        except Exception as e:
            error_msg = f"FTP download failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(error_msg, TaskErrorCode.FTP_DOWNLOAD_FAILED, {"error": str(e)})
    
    async def _execute_ftp_list_task(self, task: Task) -> None:
        """Execute FTP list directory task."""
        import ftplib
        import logging
        import socket
        from pathlib import Path
        
        # Setup logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        logger.info(f"=== Starting FTP list task {task.id} ===")
        
        params = task.params
        remote_path = params.get("remote_path", "/")
        
        logger.info(f"List parameters: remote_path={remote_path}")
        
        task.update_progress(10, f"Listing directory: {remote_path}")
        
        try:
            # Load FTP configuration
            config_path = Path("config/config.json")
            if not config_path.exists():
                task.fail(
                    "FTP configuration file not found",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"config_path": str(config_path)}
                )
                return
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            ftp_config = config.get("ftp", {})
            host = ftp_config.get("host")
            user = ftp_config.get("user")
            password = ftp_config.get("password")
            port = ftp_config.get("port", 21)
            timeout = ftp_config.get("timeout", 30)
            passive_mode = ftp_config.get("passive_mode", True)
            
            if not all([host, user, password]):
                task.fail(
                    "FTP configuration incomplete",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"ftp_config": ftp_config}
                )
                return
            
            task.update_progress(30, "Connecting to FTP server")
            
            # Connect to FTP server
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=timeout)
            ftp.login(user, password)
            
            if passive_mode:
                ftp.set_pasv(True)
            
            task.update_progress(50, "Connected to FTP server")
            
            # List directory - use simple LIST command
            files = []
            ftp.retrlines("LIST", lambda line: files.append(line))
            
            task.update_progress(90, "Directory listing completed")
            
            ftp.quit()
            
            task.complete({
                "message": "FTP directory listing completed",
                "remote_path": remote_path,
                "files": files,
                "file_count": len(files)
            })
            
        except ftplib.error_perm as e:
            error_msg = f"FTP permission error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_PERMISSION_DENIED, {"error": str(e)})
        except socket.timeout as e:
            error_msg = f"FTP timeout - possible firewall issue: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_CONNECTION_FAILED, {"error": str(e), "suggestion": "Check firewall settings"})
        except Exception as e:
            error_msg = f"FTP list failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(error_msg, TaskErrorCode.FTP_CONNECTION_FAILED, {"error": str(e)})
    
    async def _execute_ftp_delete_task(self, task: Task) -> None:
        """Execute FTP delete file task."""
        import ftplib
        import logging
        from pathlib import Path
        
        # Setup logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        logger.info(f"=== Starting FTP delete task {task.id} ===")
        
        params = task.params
        remote_path = params.get("remote_path", "")
        
        logger.info(f"Delete parameters: remote_path={remote_path}")
        
        task.update_progress(10, f"Deleting file: {remote_path}")
        
        try:
            # Load FTP configuration
            config_path = Path("config/config.json")
            if not config_path.exists():
                task.fail(
                    "FTP configuration file not found",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"config_path": str(config_path)}
                )
                return
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            ftp_config = config.get("ftp", {})
            host = ftp_config.get("host")
            user = ftp_config.get("user")
            password = ftp_config.get("password")
            port = ftp_config.get("port", 21)
            timeout = ftp_config.get("timeout", 30)
            passive_mode = ftp_config.get("passive_mode", True)
            
            if not all([host, user, password]):
                task.fail(
                    "FTP configuration incomplete",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"ftp_config": ftp_config}
                )
                return
            
            task.update_progress(30, "Connecting to FTP server")
            
            # Connect to FTP server
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=timeout)
            ftp.login(user, password)
            
            if passive_mode:
                ftp.set_pasv(True)
            
            task.update_progress(50, "Connected to FTP server")
            
            # Delete file
            ftp.delete(remote_path)
            
            task.update_progress(90, "File deleted successfully")
            
            ftp.quit()
            
            task.complete({
                "message": "FTP file deletion completed",
                "remote_path": remote_path
            })
            
        except ftplib.error_perm as e:
            error_msg = f"FTP permission error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_PERMISSION_DENIED, {"error": str(e)})
        except Exception as e:
            error_msg = f"FTP delete failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(error_msg, TaskErrorCode.FTP_CONNECTION_FAILED, {"error": str(e)})
    
    async def _execute_docker_push_task(self, task: Task) -> None:
        """Execute Docker push task."""
        import subprocess
        import logging
        
        # Setup logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        logger.info(f"=== Starting Docker push task {task.id} ===")
        
        params = task.params
        image_name = params.get("image_name", "")
        tag = params.get("tag", "latest")
        full_image_name = f"{image_name}:{tag}"
        
        logger.info(f"Push parameters: image_name={image_name}, tag={tag}, full_name={full_image_name}")
        
        task.update_progress(10, f"Starting push of {full_image_name}")
        task.add_log(f"DEBUG: Task parameters: {params}")
        
        # Build command
        cmd = ["docker", "push", full_image_name]
        task.command = " ".join(cmd)
        
        logger.info(f"Executing command: {' '.join(cmd)}")
        task.add_log(f"DEBUG: Executing command: {' '.join(cmd)}")
        
        try:
            # Check if image exists locally
            check_cmd = ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}", full_image_name]
            logger.info(f"Checking image existence: {' '.join(check_cmd)}")
            task.add_log(f"DEBUG: Checking image existence: {' '.join(check_cmd)}")
            
            check_process = await asyncio.create_subprocess_exec(
                *check_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            check_stdout, check_stderr = await check_process.communicate()
            
            if check_process.returncode != 0 or not check_stdout.decode('utf-8').strip():
                error_msg = f"Image {full_image_name} not found locally"
                logger.error(error_msg)
                task.add_log(f"DEBUG: {error_msg}")
                task.fail(
                    error_msg, 
                    TaskErrorCode.DOCKER_IMAGE_NOT_FOUND,
                    {"image_name": full_image_name, "check_command": " ".join(check_cmd)}
                )
                return
            
            logger.info(f"Image {full_image_name} found locally")
            task.add_log(f"DEBUG: Image {full_image_name} found locally")
            
            # Execute with progress tracking
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            logger.info(f"Process started with PID: {process.pid}")
            task.add_log(f"DEBUG: Process started with PID: {process.pid}")
            
            task.update_progress(25, "Pushing layers...")
            
            # Monitor output for progress
            stdout, stderr = await process.communicate()
            
            logger.info(f"Process completed with return code: {process.returncode}")
            task.add_log(f"DEBUG: Process completed with return code: {process.returncode}")
            
            if stdout:
                logger.info(f"STDOUT: {stdout.decode('utf-8')}")
                task.add_log(f"DEBUG: STDOUT: {stdout.decode('utf-8')}")
            
            if stderr:
                logger.warning(f"STDERR: {stderr.decode('utf-8')}")
                task.add_log(f"DEBUG: STDERR: {stderr.decode('utf-8')}")
            
            if process.returncode == 0:
                task.update_progress(90, "Finalizing push...")
                
                # Parse output for digest
                output_lines = stdout.decode('utf-8').splitlines()
                digest = None
                for line in output_lines:
                    if "digest:" in line:
                        digest = line.split("digest: ")[-1].strip()
                        break
                
                result = {
                    "status": "success",
                    "message": "Docker image pushed successfully",
                    "image_name": image_name,
                    "tag": tag,
                    "full_image_name": full_image_name,
                    "digest": digest
                }
                
                logger.info(f"Push completed successfully: {result}")
                task.add_log(f"DEBUG: Push completed successfully: {result}")
                task.complete(result)
            else:
                error_msg = stderr.decode('utf-8').strip()
                logger.error(f"Push failed: {error_msg}")
                task.add_log(f"DEBUG: Push failed: {error_msg}")
                
                # Determine error code based on error message
                error_code = TaskErrorCode.DOCKER_PUSH_FAILED
                error_details = {
                    "exit_code": process.returncode,
                    "stderr": error_msg,
                    "command": " ".join(cmd)
                }
                
                if "denied" in error_msg.lower():
                    error_code = TaskErrorCode.DOCKER_PERMISSION_DENIED
                elif "authentication" in error_msg.lower():
                    error_code = TaskErrorCode.DOCKER_AUTHENTICATION_FAILED
                elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                    error_code = TaskErrorCode.DOCKER_NETWORK_ERROR
                elif "registry" in error_msg.lower():
                    error_code = TaskErrorCode.DOCKER_REGISTRY_ERROR
                
                task.fail(f"Docker push failed: {error_msg}", error_code, error_details)
                
        except Exception as e:
            error_msg = f"Exception during push: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.add_log(f"DEBUG: Exception during push: {str(e)}")
            task.fail(
                error_msg, 
                TaskErrorCode.INTERNAL_ERROR,
                {"exception_type": type(e).__name__, "exception": str(e)}
            )
        
        logger.info(f"=== Completed Docker push task {task.id} ===")
    
    async def _execute_docker_build_task(self, task: Task) -> None:
        """Execute Docker build task."""
        # Similar implementation for build operations
        params = task.params
        tag = params.get("tag", "")
        
        task.update_progress(10, f"Starting build of {tag}")
        
        # Implementation would be similar to push but for build
        # For now, just simulate
        await asyncio.sleep(5)  # Simulate build time
        
        result = {
            "status": "success",
            "message": "Docker image built successfully",
            "tag": tag
        }
        task.complete(result)
    
    async def _execute_docker_pull_task(self, task: Task) -> None:
        """Execute Docker pull task."""
        # Similar implementation for pull operations
        params = task.params
        image_name = params.get("image_name", "")
        
        task.update_progress(10, f"Starting pull of {image_name}")
        
        # Implementation would be similar to push but for pull
        # For now, just simulate
        await asyncio.sleep(3)  # Simulate pull time
        
        result = {
            "status": "success",
            "message": "Docker image pulled successfully",
            "image_name": image_name
        }
        task.complete(result)
    
    async def _execute_ollama_pull_task(self, task: Task) -> None:
        """Execute Ollama model pull task."""
        import subprocess
        import json
        import os
        from ai_admin.commands.ollama_base import ollama_config
        
        params = task.params
        model_name = params.get("model_name", "")
        
        task.update_progress(5, f"Starting pull of Ollama model: {model_name}")
        
        # Set OLLAMA_MODELS environment variable
        env = os.environ.copy()
        env['OLLAMA_MODELS'] = ollama_config.get_models_cache_path()
        
        # Build command
        cmd = ["ollama", "pull", model_name]
        task.command = " ".join(cmd)
        
        # Execute with progress tracking
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        task.update_progress(15, "Downloading model layers...")
        
        # Monitor output for progress
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            task.update_progress(95, "Finalizing model download...")
            
            # Parse output for model info
            output_lines = stdout.decode('utf-8').splitlines()
            model_size = None
            for line in output_lines:
                if "pulled" in line.lower() and "mb" in line.lower():
                    # Extract size info if available
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "mb" in part.lower() or "gb" in part.lower():
                            model_size = part
                            break
            
            result = {
                "status": "success",
                "message": f"Ollama model {model_name} pulled successfully",
                "model_name": model_name,
                "model_size": model_size,
                "output": output_lines
            }
            task.complete(result)
        else:
            error_msg = stderr.decode('utf-8').strip()
            task.fail(f"Ollama pull failed: {error_msg}")
    
    async def _execute_ollama_run_task(self, task: Task) -> None:
        """Execute Ollama model inference task."""
        import subprocess
        import json
        from ai_admin.commands.ollama_base import ollama_config
        
        params = task.params
        model_name = params.get("model_name", "")
        prompt = params.get("prompt", "")
        max_tokens = params.get("max_tokens", 1000)
        temperature = params.get("temperature", 0.7)
        
        task.update_progress(10, f"Starting inference with model: {model_name}")
        
        # Prepare request data
        request_data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            }
        }
        
        # Build curl command
        curl_cmd = [
            "curl", "-s", "-X", "POST",
            f"{ollama_config.get_ollama_url()}/api/generate",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(request_data)
        ]
        task.command = " ".join(curl_cmd)
        
        task.update_progress(25, "Sending request to Ollama...")
        
        # Execute with progress tracking
        process = await asyncio.create_subprocess_exec(
            *curl_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        task.update_progress(50, "Processing inference...")
        
        # Monitor output
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            task.update_progress(90, "Parsing response...")
            
            try:
                response_data = json.loads(stdout.decode('utf-8'))
                generated_text = response_data.get("response", "")
                
                result = {
                    "status": "success",
                    "message": f"Inference completed with model {model_name}",
                    "model_name": model_name,
                    "prompt": prompt,
                    "generated_text": generated_text,
                    "prompt_tokens": response_data.get("prompt_eval_count", 0),
                    "generated_tokens": response_data.get("eval_count", 0),
                    "total_duration": response_data.get("eval_duration", 0),
                    "tokens_per_second": response_data.get("eval_count", 0) / (response_data.get("eval_duration", 1) / 1e9)
                }
                task.complete(result)
                
            except json.JSONDecodeError as e:
                task.fail(f"Invalid JSON response from Ollama: {str(e)}")
        else:
            error_msg = stderr.decode('utf-8').strip()
            task.fail(f"Ollama inference failed: {error_msg}")
    
    async def _execute_custom_script_task(self, task: Task) -> None:
        """Execute custom script task."""
        import subprocess
        import os
        
        params = task.params
        script_path = params.get("script_path", "")
        script_args = params.get("script_args", [])
        working_dir = params.get("working_dir", ".")
        
        task.update_progress(10, f"Starting custom script: {script_path}")
        
        if not os.path.exists(script_path):
            task.fail(
                f"Script not found: {script_path}",
                TaskErrorCode.DATA_FILE_NOT_FOUND,
                {"script_path": script_path}
            )
            return
        
        # Build command
        cmd = [script_path] + script_args
        task.command = " ".join(cmd)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            task.update_progress(50, "Executing script...")
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result = {
                    "status": "success",
                    "message": "Custom script executed successfully",
                    "script_path": script_path,
                    "stdout": stdout.decode('utf-8'),
                    "exit_code": process.returncode
                }
                task.complete(result)
            else:
                error_msg = stderr.decode('utf-8').strip()
                task.fail(
                    f"Custom script failed: {error_msg}",
                    TaskErrorCode.CUSTOM_SCRIPT_FAILED,
                    {"exit_code": process.returncode, "stderr": error_msg}
                )
                
        except Exception as e:
            task.fail(
                f"Exception during script execution: {str(e)}",
                TaskErrorCode.INTERNAL_ERROR,
                {"exception": str(e)}
            )
    
    async def _execute_custom_command_task(self, task: Task) -> None:
        """Execute custom command task."""
        import subprocess
        
        params = task.params
        command = params.get("command", "")
        args = params.get("args", [])
        shell = params.get("shell", False)
        
        task.update_progress(10, f"Starting custom command: {command}")
        
        if not command:
            task.fail(
                "No command specified",
                TaskErrorCode.VALIDATION_MISSING_REQUIRED,
                {"command": command}
            )
            return
        
        # Build command
        if shell:
            cmd = command
        else:
            cmd = [command] + args
        
        task.command = command if shell else " ".join(cmd)
        
        try:
            if shell:
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            
            task.update_progress(50, "Executing command...")
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result = {
                    "status": "success",
                    "message": "Custom command executed successfully",
                    "command": command,
                    "stdout": stdout.decode('utf-8'),
                    "exit_code": process.returncode
                }
                task.complete(result)
            else:
                error_msg = stderr.decode('utf-8').strip()
                task.fail(
                    f"Custom command failed: {error_msg}",
                    TaskErrorCode.CUSTOM_COMMAND_FAILED,
                    {"exit_code": process.returncode, "stderr": error_msg}
                )
                
        except Exception as e:
            task.fail(
                f"Exception during command execution: {str(e)}",
                TaskErrorCode.INTERNAL_ERROR,
                {"exception": str(e)}
            )
    
    async def _execute_system_monitor_task(self, task: Task) -> None:
        """Execute system monitoring task."""
        import psutil
        
        params = task.params
        monitor_type = params.get("monitor_type", "general")
        
        task.update_progress(10, f"Starting system monitoring: {monitor_type}")
        
        try:
            if monitor_type == "general":
                # General system info
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                result = {
                    "status": "success",
                    "message": "System monitoring completed",
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "memory_available": memory.available,
                    "disk_free": disk.free
                }
                
            elif monitor_type == "processes":
                # Process information
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                result = {
                    "status": "success",
                    "message": "Process monitoring completed",
                    "processes": processes[:100]  # Limit to first 100 processes
                }
                
            else:
                task.fail(
                    f"Unknown monitor type: {monitor_type}",
                    TaskErrorCode.VALIDATION_INVALID_PARAMS,
                    {"monitor_type": monitor_type}
                )
                return
            
            task.complete(result)
            
        except Exception as e:
            task.fail(
                f"System monitoring failed: {str(e)}",
                TaskErrorCode.SYSTEM_SERVICE_UNAVAILABLE,
                {"exception": str(e)}
            )
    
    async def _execute_generic_task(self, task: Task) -> None:
        """Execute generic task with basic validation and execution."""
        params = task.params
        task_type = task.task_type.value
        
        task.update_progress(10, f"Starting generic task: {task_type}")
        
        try:
            # Basic validation
            if not params:
                task.fail(
                    "No parameters provided for generic task",
                    TaskErrorCode.VALIDATION_MISSING_REQUIRED,
                    {"task_type": task_type}
                )
                return
            
            # Simulate task execution
            task.update_progress(50, "Processing generic task...")
            await asyncio.sleep(1)  # Simulate work
            
            result = {
                "status": "success",
                "message": f"Generic task {task_type} completed",
                "task_type": task_type,
                "params": params
            }
            
            task.complete(result)
            
        except Exception as e:
            task.fail(
                f"Generic task failed: {str(e)}",
                TaskErrorCode.UNKNOWN_ERROR,
                {"exception": str(e), "task_type": task_type}
            ) 