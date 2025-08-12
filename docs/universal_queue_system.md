# Universal Queue System Documentation

## Overview

The universal queue system provides comprehensive task management for **any type of operations**, not just Docker. It supports Docker, Kubernetes, Vast.ai, GitHub, Ollama, system operations, custom scripts, and more.

## Key Features

### 1. Universal Task Types

#### Docker Operations
- `DOCKER_PUSH`, `DOCKER_BUILD`, `DOCKER_PULL`
- `DOCKER_RUN`, `DOCKER_STOP`, `DOCKER_REMOVE`, `DOCKER_TAG`

#### Kubernetes Operations
- `K8S_DEPLOY`, `K8S_SCALE`, `K8S_DELETE`
- `K8S_GET`, `K8S_LOGS`, `K8S_EXEC`

#### Vast.ai Operations
- `VAST_CREATE`, `VAST_DESTROY`, `VAST_LIST`, `VAST_SEARCH`

#### GitHub Operations
- `GITHUB_CREATE_REPO`, `GITHUB_LIST_REPOS`
- `GITHUB_CLONE`, `GITHUB_PUSH`

#### Ollama Operations
- `OLLAMA_PULL`, `OLLAMA_RUN`, `OLLAMA_LIST`, `OLLAMA_STATUS`

#### System Operations
- `SYSTEM_MONITOR`, `SYSTEM_BACKUP`, `SYSTEM_UPDATE`, `SYSTEM_CLEANUP`

#### Custom Operations
- `CUSTOM_SCRIPT`, `CUSTOM_COMMAND`, `CUSTOM_WEBHOOK`

#### Data Operations
- `DATA_PROCESS`, `DATA_ANALYZE`, `DATA_EXPORT`, `DATA_IMPORT`

#### Network Operations
- `NETWORK_TEST`, `NETWORK_SCAN`, `NETWORK_MONITOR`

### 2. Enhanced Task Features

#### Task Categorization
- **Category**: Groups tasks by purpose (docker, kubernetes, custom, etc.)
- **Tags**: Flexible tagging system for filtering and organization
- **Priority**: Task priority levels for scheduling

#### Advanced Status Tracking
- **Active States**: PENDING, RUNNING, PAUSED
- **Intermediate States**: VALIDATING, PREPARING, UPLOADING, DOWNLOADING, BUILDING, PULLING
- **Completion States**: COMPLETED, FAILED, CANCELLED, TIMEOUT

### 3. Universal Error Code System

#### Docker Errors
- `DOCKER_IMAGE_NOT_FOUND`, `DOCKER_AUTHENTICATION_FAILED`
- `DOCKER_PERMISSION_DENIED`, `DOCKER_NETWORK_ERROR`
- `DOCKER_REGISTRY_ERROR`, `DOCKER_BUILD_FAILED`
- `DOCKER_PUSH_FAILED`, `DOCKER_PULL_FAILED`
- `DOCKER_CONTAINER_NOT_FOUND`, `DOCKER_CONTAINER_ALREADY_RUNNING`

#### Kubernetes Errors
- `K8S_CLUSTER_UNAVAILABLE`, `K8S_AUTHENTICATION_FAILED`
- `K8S_RESOURCE_NOT_FOUND`, `K8S_RESOURCE_ALREADY_EXISTS`
- `K8S_NAMESPACE_NOT_FOUND`, `K8S_POD_FAILED`
- `K8S_DEPLOYMENT_FAILED`, `K8S_SERVICE_FAILED`

#### Vast.ai Errors
- `VAST_API_ERROR`, `VAST_AUTHENTICATION_FAILED`
- `VAST_INSTANCE_NOT_FOUND`, `VAST_INSTANCE_CREATION_FAILED`
- `VAST_INSTANCE_DESTRUCTION_FAILED`, `VAST_QUOTA_EXCEEDED`

#### GitHub Errors
- `GITHUB_API_ERROR`, `GITHUB_AUTHENTICATION_FAILED`
- `GITHUB_REPO_NOT_FOUND`, `GITHUB_REPO_ALREADY_EXISTS`
- `GITHUB_BRANCH_NOT_FOUND`, `GITHUB_MERGE_CONFLICT`

#### System Errors
- `SYSTEM_TIMEOUT`, `SYSTEM_RESOURCE_LIMIT`
- `SYSTEM_DISK_SPACE`, `SYSTEM_MEMORY_LIMIT`
- `SYSTEM_CPU_LIMIT`, `SYSTEM_PROCESS_KILLED`

#### Network Errors
- `NETWORK_CONNECTION_FAILED`, `NETWORK_TIMEOUT`
- `NETWORK_DNS_ERROR`, `NETWORK_PROXY_ERROR`
- `NETWORK_FIREWALL_BLOCKED`, `NETWORK_SSL_ERROR`

#### Data Errors
- `DATA_FILE_NOT_FOUND`, `DATA_FILE_CORRUPTED`
- `DATA_FORMAT_INVALID`, `DATA_SIZE_TOO_LARGE`
- `DATA_ENCODING_ERROR`, `DATA_PARSING_FAILED`

## Usage Examples

### 1. Docker Operations
```python
from ai_admin.queue.task_queue import TaskQueue, Task, TaskType

queue = TaskQueue()

# Docker push
docker_task = Task(
    task_type=TaskType.DOCKER_PUSH,
    params={"image_name": "username/myapp", "tag": "latest"},
    category="docker",
    tags=["docker", "push", "production"]
)
task_id = await queue.add_task(docker_task)
```

### 2. Custom Script Execution
```python
# Custom script
script_task = Task(
    task_type=TaskType.CUSTOM_SCRIPT,
    params={
        "script_path": "/path/to/script.sh",
        "script_args": ["arg1", "arg2"],
        "working_dir": "/tmp"
    },
    category="custom",
    tags=["script", "automation"]
)
task_id = await queue.add_task(script_task)
```

### 3. Custom Command Execution
```python
# Custom command
command_task = Task(
    task_type=TaskType.CUSTOM_COMMAND,
    params={
        "command": "python",
        "args": ["script.py", "--config", "config.json"],
        "shell": False
    },
    category="system",
    tags=["python", "automation"]
)
task_id = await queue.add_task(command_task)
```

### 4. System Monitoring
```python
# System monitoring
monitor_task = Task(
    task_type=TaskType.SYSTEM_MONITOR,
    params={"monitor_type": "general"},
    category="monitoring",
    tags=["system", "health"]
)
task_id = await queue.add_task(monitor_task)
```

### 5. Generic Tasks
```python
# Generic task for any operation
generic_task = Task(
    task_type=TaskType.DATA_PROCESS,
    params={
        "data_source": "database",
        "operation": "backup",
        "format": "json"
    },
    category="data",
    tags=["data", "backup", "database"]
)
task_id = await queue.add_task(generic_task)
```

## Task Management

### 1. Task Filtering
```python
# Filter by category
docker_tasks = await queue.get_tasks_by_category("docker")
kubernetes_tasks = await queue.get_tasks_by_category("kubernetes")

# Filter by tags
production_tasks = await queue.get_tasks_by_tag("production")
test_tasks = await queue.get_tasks_by_tag("test")

# Filter by type
push_tasks = await queue.get_tasks_by_type(TaskType.DOCKER_PUSH)
monitor_tasks = await queue.get_tasks_by_type(TaskType.SYSTEM_MONITOR)
```

### 2. Task Control
```python
# Pause running task
await queue.pause_task(task_id)

# Resume paused task
await queue.resume_task(task_id)

# Retry failed task
await queue.retry_task(task_id)

# Cancel task
await queue.cancel_task(task_id)
```

### 3. Task Monitoring
```python
# Get task status
task = await queue.get_task(task_id)
print(f"Status: {task.status.value}")
print(f"Progress: {task.progress}%")
print(f"Current step: {task.current_step}")

# Get detailed summary
summary = await queue.get_task_summary(task_id)
print(f"Error: {summary['error']}")
print(f"Can retry: {summary['retry']['can_retry']}")
```

## Queue Manager Integration

### 1. Using Queue Manager
```python
from ai_admin.queue.queue_manager import queue_manager

# Add Docker push task
task_id = await queue_manager.add_push_task(
    image_name="username/myapp",
    tag="latest"
)

# Add custom script task
task_id = await queue_manager.add_custom_script_task(
    script_path="/path/to/script.sh",
    script_args=["arg1", "arg2"]
)

# Add custom command task
task_id = await queue_manager.add_custom_command_task(
    command="python",
    args=["script.py"],
    shell=False
)

# Add system monitor task
task_id = await queue_manager.add_system_monitor_task(
    monitor_type="general"
)

# Add generic task
task_id = await queue_manager.add_generic_task(
    task_type=TaskType.DATA_PROCESS,
    params={"operation": "backup"}
)
```

### 2. Queue Statistics
```python
# Get comprehensive statistics
stats = await queue_manager.get_queue_status()

print(f"Total tasks: {stats['summary']['total_tasks']}")
print(f"Success rate: {stats['performance']['success_rate']}%")
print(f"Average duration: {stats['performance']['average_duration_seconds']}s")

# Status distribution
for status, count in stats['status_distribution'].items():
    if count > 0:
        print(f"{status}: {count}")

# Type distribution
for task_type, count in stats['type_distribution'].items():
    if count > 0:
        print(f"{task_type}: {count}")
```

## Error Handling

### 1. Automatic Error Detection
The system automatically detects and categorizes errors based on:
- Command exit codes
- Error message patterns
- System resource availability
- Network connectivity
- Service availability

### 2. Error Recovery
- **Automatic retries**: Failed tasks can be automatically retried
- **Manual retries**: Users can manually retry failed tasks
- **Error suggestions**: System provides specific suggestions for fixing errors

### 3. Error Reporting
Each error includes:
- Human-readable description
- Specific error code
- Detailed error context
- Suggested solutions

## Best Practices

### 1. Task Organization
- Use meaningful categories for grouping related tasks
- Apply relevant tags for easy filtering and search
- Set appropriate priorities for critical tasks

### 2. Error Handling
- Check error codes for specific issues
- Follow suggested solutions
- Implement proper error recovery logic

### 3. Performance Optimization
- Use appropriate concurrent task limits
- Monitor success rates and performance metrics
- Clean up completed tasks regularly

### 4. Monitoring
- Always check task status after creation
- Monitor progress for long-running tasks
- Handle errors appropriately

## Extensibility

The system is designed to be easily extensible:

### 1. Adding New Task Types
```python
# Add new task type to TaskType enum
class TaskType(Enum):
    # ... existing types ...
    NEW_OPERATION = "new_operation"

# Add corresponding error codes
class TaskErrorCode(Enum):
    # ... existing codes ...
    NEW_OPERATION_FAILED = "NEW_OPERATION_FAILED"

# Implement execution method
async def _execute_new_operation_task(self, task: Task) -> None:
    # Implementation here
    pass
```

### 2. Custom Executors
The system supports custom task executors for any operation type, making it truly universal for any automation needs.

## Conclusion

The universal queue system provides a comprehensive, extensible solution for managing any type of task or operation. It offers detailed status tracking, robust error handling, and flexible task organization, making it suitable for complex automation workflows across multiple domains. 