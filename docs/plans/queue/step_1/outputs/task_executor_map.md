# Task executor map — QueueManager `add_*` → TaskQueueCore._execute_task

Source files: `ai_admin/task_queue/queue_manager/queue_manager_impl.py` (enqueue), `ai_admin/task_queue/task_queue/task_queue.py` (`TaskQueueCore._execute_task`, lines 563–764).

Every `QueueManager` `add_*` method builds a `Task` and calls `await self.task_queue.add_task(task)`. Execution is dispatched in `TaskQueueCore._execute_task`, which awaits `self._execute_*` helpers. Implementations of those helpers live in classes later in the same module (`FTPExecutor`, `DockerExecutor`, `K8sKindExecutor`, `OllamaExecutor`, `MiscExecutor`).

## Mapping table

| add_method | TaskType (value) | TaskQueueCore._execute_task dispatch | Implementing class (task_queue.py) | executor_method | params_passed (keys in Task.params) |
|------------|------------------|--------------------------------------|-------------------------------------|-----------------|-------------------------------------|
| add_push_task | DOCKER_PUSH (`docker_push`) | `_execute_docker_push_task` | DockerExecutor | `_execute_docker_push_task` | image_name, tag, + **options |
| add_git_task | GIT_OPERATION (`git_operation`) | `else` → `_execute_generic_task` | MiscExecutor | `_execute_generic_task` | operation_type, current_directory, repository_url, target_directory, branch, remote, force, ssl_config, user_roles, + **options |
| add_github_task | GITHUB_OPERATION (`github_operation`) | `else` → `_execute_generic_task` | MiscExecutor | `_execute_generic_task` | operation_type, repo_name, description, private, initialize, gitignore_template, license_template, username, token, ssl_config, user_roles, + **options |
| add_build_task | DOCKER_BUILD (`docker_build`) | `_execute_docker_build_task` | DockerExecutor | `_execute_docker_build_task` | dockerfile_path, tag, context_path, + **options |
| add_pull_task | DOCKER_PULL (`docker_pull`) | `_execute_docker_pull_task` | DockerExecutor | `_execute_docker_pull_task` | image_name, tag, + **options |
| add_ollama_pull_task | OLLAMA_PULL (`ollama_pull`) | `_execute_ollama_pull_task` | OllamaExecutor | `_execute_ollama_pull_task` | model_name, + **options |
| add_ollama_run_task | OLLAMA_RUN (`ollama_run`) | `_execute_ollama_run_task` | OllamaExecutor | `_execute_ollama_run_task` | model_name, prompt, max_tokens, temperature, + **options |
| add_k8s_deployment_create_task | K8S_DEPLOYMENT_CREATE (`k8s_deployment_create`) | `_execute_k8s_deployment_create_task` | K8sKindExecutor | `_execute_k8s_deployment_create_task` | project_path, image, port, namespace, replicas, + **options |
| add_k8s_pod_create_task | K8S_POD_CREATE (`k8s_pod_create`) | `_execute_k8s_pod_create_task` | K8sKindExecutor | `_execute_k8s_pod_create_task` | project_path, image, port, namespace, + **options |
| add_k8s_cluster_create_task | K8S_CLUSTER_CREATE (`k8s_cluster_create`) | `else` → `_execute_generic_task` | MiscExecutor | `_execute_generic_task` | cluster_name, cluster_type, container_name, port, + **options |
| add_k8s_certificate_create_task | K8S_CERTIFICATE_CREATE (`k8s_certificate_create`) | `else` → `_execute_generic_task` | MiscExecutor | `_execute_generic_task` | cluster_name, cert_type, common_name, + **options |
| add_k8s_mtls_setup_task | K8S_MTLS_SETUP (`k8s_mtls_setup`) | `else` → `_execute_generic_task` | MiscExecutor | `_execute_generic_task` | cluster_name, + **options |
| add_vast_create_task | VAST_CREATE (`vast_create`) | `else` → `_execute_generic_task` | MiscExecutor | `_execute_generic_task` | bundle_id, image, disk, label, onstart, env_vars, user_roles, security_validated, + **options |
| add_vast_destroy_task | VAST_DESTROY (`vast_destroy`) | `else` → `_execute_generic_task` | MiscExecutor | `_execute_generic_task` | instance_id, user_roles, security_validated, + **options |
| add_vast_search_task | VAST_SEARCH (`vast_search`) | `else` → `_execute_generic_task` | MiscExecutor | `_execute_generic_task` | gpu_name, min_gpu_count, max_gpu_count, min_gpu_ram, max_price_per_hour, disk_space, order, limit, user_roles, security_validated, + **options |
| add_vast_instances_task | VAST_INSTANCES (`vast_instances`) | `else` → `_execute_generic_task` | MiscExecutor | `_execute_generic_task` | show_all, user_roles, security_validated, + **options |
| add_system_task | SYSTEM_MONITOR (`system_monitor`) | `_execute_system_monitor_task` | MiscExecutor | `_execute_system_monitor_task` | operation_type, include_gpu, include_temperature, include_processes, ssl_config, user_roles, + **options |
| add_task | (caller `task.task_type`) | Per `task.task_type` in `_execute_task` | (same as branch for that type) | (same as branch) | Whatever the caller put in `task.params` |
| add_ssl_task | SSL_OPERATION (`ssl_operation`) | `_execute_ssl_operation_task` | MiscExecutor | `_execute_ssl_operation_task` | operation_type, cert_type, common_name, ssl_config, user_roles, + **options |
| push_task | CUSTOM_SCRIPT (`custom_script`) | `_execute_custom_script_task` | MiscExecutor | `_execute_custom_script_task` | task_data (entire dict becomes `params`) |

### Notes

- **QueueManager** does not instantiate executor classes; all rows are “enqueue `Task` then core dispatches”. There is no separate `INLINE` row for logic inside `QueueManager` beyond task construction and `add_task`.
- Rows that use `else` → `_execute_generic_task` are types **not** named on any `elif` branch in `TaskQueueCore._execute_task` (lines 579–742); see Blockers for runtime behavior of `MiscExecutor._execute_generic_task`.

## Blockers (facts from `queue_manager_impl.py` and `task_queue.py` only)

### 1. MiscExecutor generic path vs `else` branch in `_execute_task`

`TaskQueueCore._execute_task` sends unhandled types to the generic path:

```743:747:ai_admin/task_queue/task_queue/task_queue.py
            else:
                logger.warning(
                    f"Task type {task.task_type} not implemented, using generic executor"
                )
                await self._execute_generic_task(task)
```

`MiscExecutor._execute_generic_task` only treats `task_type` values `"custom_script"` and `"custom_command"` as success paths; anything else hits “Unknown task type” and fails:

```2598:2634:ai_admin/task_queue/task_queue/task_queue.py
            if task_type == "custom_script":
                script_path = params.get("script_path", "")
                if not script_path:
                    task.fail(
                        "Script path not provided",
                        TaskErrorCode.VALIDATION_MISSING_REQUIRED,
                    )
                    return
                result = {
                    "status": "success",
                    "message": f"Custom script task completed",
                    "task_type": task_type,
                    "script_path": script_path,
                    "note": "Script execution handled by _execute_custom_script_task",
                }
            elif task_type == "custom_command":
                command = params.get("command", "")
                if not command:
                    task.fail(
                        "Command not provided",
                        TaskErrorCode.VALIDATION_MISSING_REQUIRED,
                    )
                    return
                result = {
                    "status": "success",
                    "message": f"Custom command task completed",
                    "task_type": task_type,
                    "command": command,
                    "note": "Command execution handled by _execute_custom_command_task",
                }
            else:
                task.fail(
                    f"Unknown task type: {task_type}",
                    TaskErrorCode.VALIDATION_INVALID_PARAMS,
                    {"task_type": task_type},
                )
                return
```

So `GIT_OPERATION`, `GITHUB_OPERATION`, `K8S_CLUSTER_CREATE`, `K8S_CERTIFICATE_CREATE`, `K8S_MTLS_SETUP`, and all `VAST_*` types enqueued by `QueueManager` are dispatched to generic code that does not implement those `task.task_type.value` strings.

### 2. `add_github_task` import path

`add_github_task` imports `Task` and `TaskType` from a different module than the rest of the file:

```116:117:ai_admin/task_queue/queue_manager/queue_manager_impl.py
        from ai_admin.queue.task_queue import Task, TaskType

```

Elsewhere the file uses:

```4:4:ai_admin/task_queue/queue_manager/queue_manager_impl.py
from ai_admin.task_queue.task_queue import TaskQueue, Task, TaskType, TaskStatus
```

### 3. `max_concurrent`: facade vs core

`QueueManager.__init__` constructs the queue with a `max_concurrent` argument:

```25:25:ai_admin/task_queue/queue_manager/queue_manager_impl.py
        self.task_queue = TaskQueue(max_concurrent=2)
```

`TaskQueue.__init__` accepts only `self` and does not define `max_concurrent`:

```27:28:ai_admin/task_queue/task_queue/task_queue.py
    def __init__(self):
        self.taskQueueCore = TaskQueueCore()
```

`TaskQueueCore.__init__` sets:

```187:192:ai_admin/task_queue/task_queue/task_queue.py
    def __init__(self):
        self._pending_queue = None
        self.max_concurrent = None
        self._tasks = None
        self._lock = None
        self._running_tasks = None
```

Pause/resume mutate `self.task_queue.max_concurrent` on the `TaskQueue` instance:

```764:776:ai_admin/task_queue/queue_manager/queue_manager_impl.py
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
```

`_try_start_next_task` compares against `self.max_concurrent` on the **core** object (`TaskQueueCore`), not the facade:

```542:545:ai_admin/task_queue/task_queue/task_queue.py
        logger.info(f"Max concurrent: {self.max_concurrent}")
        logger.info(f"Pending queue size: {len(self._pending_queue)}")
        if len(self._running_tasks) >= self.max_concurrent:
            logger.info("Max concurrent tasks reached, skipping")
```

So the integer intended for concurrency is attached to `TaskQueue` in `queue_manager_impl.py` while scheduling logic reads `TaskQueueCore.max_concurrent` (still `None` in `__init__`).
