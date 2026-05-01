"""Queue manager for Docker operations."""

from typing import Dict, List, Any, Optional, Tuple
from ai_admin.task_queue.task_queue import TaskQueue, Task, TaskType, TaskStatus
from ai_admin.security.queue_security_adapter import QueueSecurityAdapter
from ai_admin.security.ssl_security_adapter import SSLSecurityAdapter

class QueueManager:
    """Manager for Docker task queues."""

    _instance: Optional["QueueManager"] = None

    def __new__(cls) -> "QueueManager":
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize queue manager."""
        if self._initialized:
            return

        self.task_queue = TaskQueue(max_concurrent=2)
        self.queue_security_adapter = QueueSecurityAdapter()
        self.ssl_security_adapter = SSLSecurityAdapter()
        self._initialized = True

    async def add_push_task(
        self, image_name: str, tag: str = "latest", **options: Any
    ) -> str:
        """Add Docker push task to queue.

        Args:
            image_name: Docker image name
            tag: Image tag
            **options: Additional push options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.DOCKER_PUSH,
            params={"image_name": image_name, "tag": tag, **options},
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_git_task(
        self,
        operation_type: str,
        current_directory: str,
        repository_url: Optional[str] = None,
        target_directory: Optional[str] = None,
        branch: Optional[str] = None,
        remote: str = "origin",
        force: bool = False,
        ssl_config: Optional[Dict[str, Any]] = None,
        user_roles: Optional[List[str]] = None,
        **options: Any,
    ) -> str:
        """Add Git operation task to queue.

        Args:
            operation_type: Type of Git operation (clone, push, pull)
            current_directory: Current working directory
            repository_url: Repository URL (for clone operations)
            target_directory: Target directory (for clone operations)
            branch: Branch name
            remote: Remote name
            force: Force operation
            ssl_config: SSL configuration
            user_roles: User roles for security
            **options: Additional options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.GIT_OPERATION,
            params={
                "operation_type": operation_type,
                "current_directory": current_directory,
                "repository_url": repository_url,
                "target_directory": target_directory,
                "branch": branch,
                "remote": remote,
                "force": force,
                "ssl_config": ssl_config,
                "user_roles": user_roles,
                **options,
            },
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_github_task(
        self,
        operation_type: str,
        repo_name: Optional[str] = None,
        description: Optional[str] = None,
        private: bool = False,
        initialize: bool = True,
        gitignore_template: Optional[str] = None,
        license_template: Optional[str] = None,
        username: Optional[str] = None,
        token: Optional[str] = None,
        ssl_config: Optional[Dict[str, Any]] = None,
        user_roles: Optional[List[str]] = None,
        **options: Any,
    ) -> str:
        """Add GitHub task to queue."""
        from ai_admin.queue.task_queue import Task, TaskType

        task = Task(
            task_type=TaskType.GITHUB_OPERATION,
            params={
                "operation_type": operation_type,
                "repo_name": repo_name,
                "description": description,
                "private": private,
                "initialize": initialize,
                "gitignore_template": gitignore_template,
                "license_template": license_template,
                "username": username,
                "token": token,
                "ssl_config": ssl_config,
                "user_roles": user_roles,
                **options,
            },
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_build_task(
        self,
        dockerfile_path: str = "Dockerfile",
        tag: Optional[str] = None,
        context_path: str = ".",
        **options: Any,
    ) -> str:
        """Add Docker build task to queue.

        Args:
            dockerfile_path: Path to Dockerfile
            tag: Tag for built image
            context_path: Build context path
            **options: Additional build options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.DOCKER_BUILD,
            params={
                "dockerfile_path": dockerfile_path,
                "tag": tag,
                "context_path": context_path,
                **options,
            },
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_pull_task(
        self, image_name: str, tag: str = "latest", **options: Any
    ) -> str:
        """Add Docker pull task to queue.

        Args:
            image_name: Docker image name
            tag: Image tag
            **options: Additional pull options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.DOCKER_PULL,
            params={"image_name": image_name, "tag": tag, **options},
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_ollama_pull_task(self, model_name: str, **options: Any) -> str:
        """Add Ollama model pull task to queue.

        Args:
            model_name: Ollama model name
            **options: Additional pull options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.OLLAMA_PULL,
            params={"model_name": model_name, **options},
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_ollama_run_task(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **options: Any,
    ) -> str:
        """Add Ollama model inference task to queue.

        Args:
            model_name: Ollama model name
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **options: Additional inference options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.OLLAMA_RUN,
            params={
                "model_name": model_name,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                **options,
            },
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_k8s_deployment_create_task(
        self,
        project_path: str,
        image: str = "ai-admin-server:latest",
        port: int = 8060,
        namespace: str = "default",
        replicas: int = 1,
        **options: Any,
    ) -> str:
        """Add Kubernetes deployment creation task to queue.

        Args:
            project_path: Path to project directory
            image: Docker image to use
            port: Port to expose
            namespace: Kubernetes namespace
            replicas: Number of replicas
            **options: Additional deployment options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.K8S_DEPLOYMENT_CREATE,
            params={
                "project_path": project_path,
                "image": image,
                "port": port,
                "namespace": namespace,
                "replicas": replicas,
                **options,
            },
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_k8s_pod_create_task(
        self,
        project_path: str,
        image: str = "ai-admin-server:latest",
        port: int = 8060,
        namespace: str = "default",
        **options: Any,
    ) -> str:
        """Add Kubernetes pod creation task to queue.

        Args:
            project_path: Path to project directory
            image: Docker image to use
            port: Port to expose
            namespace: Kubernetes namespace
            **options: Additional pod options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.K8S_POD_CREATE,
            params={
                "project_path": project_path,
                "image": image,
                "port": port,
                "namespace": namespace,
                **options,
            },
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_k8s_cluster_create_task(
        self,
        cluster_name: str,
        cluster_type: str = "k3s",
        container_name: Optional[str] = None,
        port: Optional[int] = None,
        **options: Any,
    ) -> str:
        """Add Kubernetes cluster creation task to queue.

        Args:
            cluster_name: Name of the cluster
            cluster_type: Type of cluster (k3s, kind, minikube)
            container_name: Name of the container
            port: Port for cluster API server
            **options: Additional cluster options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.K8S_CLUSTER_CREATE,
            params={
                "cluster_name": cluster_name,
                "cluster_type": cluster_type,
                "container_name": container_name,
                "port": port,
                **options,
            },
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_k8s_certificate_create_task(
        self,
        cluster_name: str,
        cert_type: str = "client",
        common_name: str = "kubernetes-admin",
        **options: Any,
    ) -> str:
        """Add Kubernetes certificate creation task to queue.

        Args:
            cluster_name: Name of the Kubernetes cluster
            cert_type: Type of certificate (client, server, ca, admin)
            common_name: Common Name for the certificate
            **options: Additional certificate options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.K8S_CERTIFICATE_CREATE,
            params={
                "cluster_name": cluster_name,
                "cert_type": cert_type,
                "common_name": common_name,
                **options,
            },
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_k8s_mtls_setup_task(self, cluster_name: str, **options: Any) -> str:
        """Add Kubernetes mTLS setup task to queue.

        Args:
            cluster_name: Name of the Kubernetes cluster
            **options: Additional mTLS setup options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.K8S_MTLS_SETUP,
            params={"cluster_name": cluster_name, **options},
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_vast_create_task(
        self,
        bundle_id: int,
        image: str = "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel",
        disk: float = 10,
        label: Optional[str] = None,
        onstart: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        user_roles: Optional[List[str]] = None,
        **options: Any,
    ) -> str:
        """Add Vast.ai instance creation task to queue.

        Args:
            bundle_id: ID of the bundle to rent
            image: Docker image to use
            disk: Disk space in GB
            label: Human-readable label for the instance
            onstart: Script to run on instance start
            env_vars: Environment variables to set
            user_roles: User roles for security validation
            **options: Additional creation options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.VAST_CREATE,
            params={
                "bundle_id": bundle_id,
                "image": image,
                "disk": disk,
                "label": label,
                "onstart": onstart,
                "env_vars": env_vars,
                "user_roles": user_roles,
                "security_validated": True,
                **options,
            },
            category="vast_ai",
            tags=["create", "instance", "gpu", "ssl_mtls"],
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_vast_destroy_task(
        self,
        instance_id: int,
        user_roles: Optional[List[str]] = None,
        **options: Any,
    ) -> str:
        """Add Vast.ai instance destruction task to queue.

        Args:
            instance_id: ID of the instance to destroy
            user_roles: User roles for security validation
            **options: Additional destruction options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.VAST_DESTROY,
            params={
                "instance_id": instance_id,
                "user_roles": user_roles,
                "security_validated": True,
                **options,
            },
            category="vast_ai",
            tags=["destroy", "instance", "gpu", "ssl_mtls"],
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_vast_search_task(
        self,
        gpu_name: Optional[str] = None,
        min_gpu_count: int = 1,
        max_gpu_count: Optional[int] = None,
        min_gpu_ram: Optional[float] = None,
        max_price_per_hour: Optional[float] = None,
        disk_space: Optional[float] = None,
        order: str = "score-",
        limit: int = 20,
        user_roles: Optional[List[str]] = None,
        **options: Any,
    ) -> str:
        """Add Vast.ai search task to queue.

        Args:
            gpu_name: GPU model name
            min_gpu_count: Minimum number of GPUs
            max_gpu_count: Maximum number of GPUs
            min_gpu_ram: Minimum GPU RAM in GB
            max_price_per_hour: Maximum price per hour in USD
            disk_space: Required disk space in GB
            order: Sort order
            limit: Maximum number of results
            user_roles: User roles for security validation
            **options: Additional search options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.VAST_SEARCH,
            params={
                "gpu_name": gpu_name,
                "min_gpu_count": min_gpu_count,
                "max_gpu_count": max_gpu_count,
                "min_gpu_ram": min_gpu_ram,
                "max_price_per_hour": max_price_per_hour,
                "disk_space": disk_space,
                "order": order,
                "limit": limit,
                "user_roles": user_roles,
                "security_validated": True,
                **options,
            },
            category="vast_ai",
            tags=["search", "instances", "gpu", "ssl_mtls"],
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_vast_instances_task(
        self,
        show_all: bool = False,
        user_roles: Optional[List[str]] = None,
        **options: Any,
    ) -> str:
        """Add Vast.ai instances listing task to queue.

        Args:
            show_all: Show all instances including terminated ones
            user_roles: User roles for security validation
            **options: Additional listing options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.VAST_INSTANCES,
            params={
                "show_all": show_all,
                "user_roles": user_roles,
                "security_validated": True,
                **options,
            },
            category="vast_ai",
            tags=["list", "instances", "gpu", "ssl_mtls"],
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_system_task(
        self,
        operation_type: str,
        include_gpu: bool = True,
        include_temperature: bool = True,
        include_processes: bool = False,
        ssl_config: Optional[Dict[str, Any]] = None,
        user_roles: Optional[List[str]] = None,
        **options: Any,
    ) -> str:
        """Add System operation task to queue.

        Args:
            operation_type: Type of System operation (system_monitor)
            include_gpu: Include GPU metrics
            include_temperature: Include temperature sensors
            include_processes: Include top processes
            ssl_config: SSL configuration
            user_roles: User roles for security validation
            **options: Additional System operation options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.SYSTEM_MONITOR,
            params={
                "operation_type": operation_type,
                "include_gpu": include_gpu,
                "include_temperature": include_temperature,
                "include_processes": include_processes,
                "ssl_config": ssl_config,
                "user_roles": user_roles,
                **options,
            },
            category="system",
            tags=["monitor", "system", "ssl_mtls"],
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_task(self, task: Task) -> str:
        """Add generic task to queue.

        Args:
            task: Task to add

        Returns:
            Task ID
        """
        task_id = await self.task_queue.add_task(task)
        return task_id

    async def add_ssl_task(
        self,
        operation_type: str,
        cert_type: str = "self_signed",
        common_name: str = "localhost",
        ssl_config: Optional[Dict[str, Any]] = None,
        user_roles: Optional[List[str]] = None,
        **options: Any,
    ) -> str:
        """Add SSL operation task to queue.

        Args:
            operation_type: Type of SSL operation (generate, view, verify, revoke)
            cert_type: Type of certificate (self_signed, ca_signed, server, client)
            common_name: Common Name for the certificate
            ssl_config: SSL configuration
            user_roles: User roles for security validation
            **options: Additional SSL operation options

        Returns:
            Task ID
        """
        task = Task(
            task_type=TaskType.SSL_OPERATION,
            params={
                "operation_type": operation_type,
                "cert_type": cert_type,
                "common_name": common_name,
                "ssl_config": ssl_config,
                "user_roles": user_roles,
                **options,
            },
            category="ssl",
            tags=["ssl", "certificate", "security"],
        )

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task object or None if not found
        """
        return await self.task_queue.get_task(task_id)

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task status dict or None if not found
        """
        task = await self.task_queue.get_task(task_id)
        return task.to_dict() if task else None

    async def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks.

        Returns:
            List of task dictionaries
        """
        tasks = await self.task_queue.get_all_tasks()
        return [task.to_dict() for task in tasks]

    async def get_tasks_by_status(self, status: TaskStatus) -> List[Dict[str, Any]]:
        """Get tasks by status.

        Args:
            status: Task status to filter by

        Returns:
            List of task dictionaries with specified status
        """
        tasks = await self.task_queue.get_all_tasks()
        filtered_tasks = [task for task in tasks if task.status == status]
        return [task.to_dict() for task in filtered_tasks]

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics.

        Returns:
            Queue statistics
        """
        return await self.task_queue.get_queue_stats()

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status and statistics.

        Returns:
            Queue status information
        """
        stats = await self.task_queue.get_queue_stats()

        # Add recent tasks info
        recent_tasks = await self.task_queue.get_all_tasks()
        recent_tasks.sort(key=lambda t: t.created_at, reverse=True)

        return {
            "statistics": stats,
            "recent_tasks": [task.to_dict() for task in recent_tasks[:10]],
            "running_tasks": [
                task.to_dict()
                for task in recent_tasks
                if task.status == TaskStatus.RUNNING
            ],
        }

    async def cancel_task(self, task_id: str, force: bool = False) -> bool:
        """Cancel task by ID.

        Args:
            task_id: Task identifier
            force: Force cancel even if task is running

        Returns:
            True if task was cancelled, False otherwise
        """
        return await self.task_queue.cancel_task(task_id)

    async def remove_task(self, task_id: str, force: bool = False) -> bool:
        """Remove task by ID.

        Args:
            task_id: Task identifier
            force: Force remove even if task is running

        Returns:
            True if task was removed, False otherwise
        """
        return await self.task_queue.remove_task(task_id, force=force)

    async def clear_completed_tasks(self) -> int:
        """Clear completed and failed tasks.

        Returns:
            Number of tasks cleared
        """
        return await self.task_queue.clear_completed()

    async def pause_queue(self) -> bool:
        """Pause task queue (stop processing new tasks).

        Returns:
            True if queue was paused
        """
        # Set max_concurrent to 0 to pause
        self.task_queue.max_concurrent = 0
        return True

    async def resume_queue(self, max_concurrent: int = 2) -> bool:
        """Resume task queue processing.

        Args:
            max_concurrent: Maximum concurrent tasks

        Returns:
            True if queue was resumed
        """
        self.task_queue.max_concurrent = max_concurrent
        # Try to start pending tasks
        await self.task_queue._try_start_next_task()
        return True

    async def get_task_logs(self, task_id: str) -> Optional[List[str]]:
        """Get task logs by ID.

        Args:
            task_id: Task identifier

        Returns:
            List of log messages or None if task not found
        """
        task = await self.task_queue.get_task(task_id)
        return task.logs if task else None

    async def push_task(self, queue_name: str, task_data: Dict[str, Any]) -> str:
        """Add generic task to queue.

        Args:
            queue_name: Name of the queue
            task_data: Task data dictionary

        Returns:
            Task ID
        """
        task = Task(task_type=TaskType.CUSTOM_SCRIPT, params=task_data)

        task_id = await self.task_queue.add_task(task)
        return task_id

    async def start_task(self, task_id: str, executor_func: Any) -> bool:
        """Start task execution.

        Args:
            task_id: Task identifier
            executor_func: Function to execute the task

        Returns:
            True if task started successfully
        """
        task = await self.task_queue.get_task(task_id)
        if task:
            task.status = TaskStatus.RUNNING
            # Execute task in background
            import asyncio

            asyncio.create_task(executor_func(task_id, task.params))
            return True
        return False

    async def get_task_position(self, task_id: str) -> int:
        """Get task position in queue.

        Args:
            task_id: Task identifier

        Returns:
            Position in queue (0 = currently running)
        """
        tasks = await self.task_queue.get_all_tasks()
        for i, task in enumerate(tasks):
            if task.id == task_id:
                return i
        return -1

    async def get_estimated_wait_time(self, task_id: str) -> int:
        """Get estimated wait time for task.

        Args:
            task_id: Task identifier

        Returns:
            Estimated wait time in seconds
        """
        position = await self.get_task_position(task_id)
        if position <= 0:
            return 0

        # Rough estimate: 30 seconds per task
        return position * 30

    async def update_task_result(self, task_id: str, result: Dict[str, Any]) -> bool:
        """Update task result.

        Args:
            task_id: Task identifier
            result: Task result data

        Returns:
            True if updated successfully
        """
        task = await self.task_queue.get_task(task_id)
        if task:
            task.result = result
            if result.get("success", False):
                task.status = TaskStatus.COMPLETED
            else:
                task.status = TaskStatus.FAILED
            return True
        return False

    async def setup_queue_ssl(
        self,
        user_roles: List[str],
        ssl_config: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Setup SSL/TLS for Queue connections.

        Args:
            user_roles: List of user roles
            ssl_config: SSL configuration parameters

        Returns:
            Tuple of (success, message)
        """
        return self.queue_security_adapter.setup_queue_ssl(user_roles, ssl_config)

    async def manage_queue_certificates(
        self,
        user_roles: List[str],
        operation: str,
        certificate_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Manage Queue SSL/TLS certificates.

        Args:
            user_roles: List of user roles
            operation: Certificate operation (create, update, delete, list)
            certificate_data: Certificate data for operations

        Returns:
            Tuple of (success, message)
        """
        return self.queue_security_adapter.manage_queue_certificates(
            user_roles, operation, certificate_data
        )

    async def validate_queue_access(
        self,
        user_roles: List[str],
        queue_name: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Validate user access to specific queue.

        Args:
            user_roles: List of user roles
            queue_name: Name of the queue to access

        Returns:
            Tuple of (has_access, error_message)
        """
        return self.queue_security_adapter.validate_queue_access(user_roles, queue_name)

