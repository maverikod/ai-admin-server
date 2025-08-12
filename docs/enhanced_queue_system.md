# Enhanced Queue System Documentation

## Overview

The enhanced queue system provides comprehensive task management for Docker operations with detailed status tracking, error handling, and control capabilities.

## Key Features

### 1. Enhanced Task Statuses

#### Active States
- **PENDING**: Task is waiting in queue
- **RUNNING**: Task is currently executing
- **PAUSED**: Task execution is paused by user

#### Intermediate States
- **VALIDATING**: Validating task parameters
- **PREPARING**: Preparing task execution
- **UPLOADING**: Uploading data to registry
- **DOWNLOADING**: Downloading data from registry
- **BUILDING**: Building Docker image
- **PULLING**: Pulling Docker image

#### Completion States
- **COMPLETED**: Task completed successfully
- **FAILED**: Task failed with error
- **CANCELLED**: Task was cancelled
- **TIMEOUT**: Task execution timed out

### 2. Error Code System

#### Docker Errors
- `DOCKER_IMAGE_NOT_FOUND`: Docker image not found locally
- `DOCKER_AUTHENTICATION_FAILED`: Docker authentication failed
- `DOCKER_PERMISSION_DENIED`: Docker permission denied
- `DOCKER_NETWORK_ERROR`: Docker network connection error
- `DOCKER_REGISTRY_ERROR`: Docker registry error
- `DOCKER_BUILD_FAILED`: Docker build failed
- `DOCKER_PUSH_FAILED`: Docker push failed
- `DOCKER_PULL_FAILED`: Docker pull failed

#### System Errors
- `SYSTEM_TIMEOUT`: Task execution timed out
- `SYSTEM_RESOURCE_LIMIT`: System resource limit exceeded
- `SYSTEM_DISK_SPACE`: Insufficient disk space
- `SYSTEM_MEMORY_LIMIT`: Insufficient memory

#### Validation Errors
- `VALIDATION_INVALID_PARAMS`: Invalid task parameters
- `VALIDATION_MISSING_REQUIRED`: Missing required parameters
- `VALIDATION_INVALID_FORMAT`: Invalid parameter format

#### Queue Errors
- `QUEUE_FULL`: Task queue is full
- `QUEUE_TASK_NOT_FOUND`: Task not found in queue
- `QUEUE_TASK_ALREADY_RUNNING`: Task is already running

#### Ollama Errors
- `OLLAMA_MODEL_NOT_FOUND`: Ollama model not found
- `OLLAMA_SERVICE_UNAVAILABLE`: Ollama service unavailable
- `OLLAMA_INFERENCE_FAILED`: Ollama inference failed

#### Generic Errors
- `UNKNOWN_ERROR`: Unknown error occurred
- `INTERNAL_ERROR`: Internal system error

### 3. Task Management Commands

#### Queue Status (`queue_status`)
```json
{
  "action": "queue_status",
  "params": {
    "include_logs": false,
    "detailed": true
  }
}
```

#### Task Status (`queue_task_status`)
```json
{
  "action": "queue_task_status",
  "params": {
    "task_id": "123e4567-e89b-12d3-a456-426614174000",
    "include_logs": true,
    "detailed": true
  }
}
```

#### Task Management (`queue_manage`)
```json
{
  "action": "queue_manage",
  "params": {
    "action": "pause|resume|retry|cancel",
    "task_id": "123e4567-e89b-12d3-a456-426614174000"
  }
}
```

### 4. Enhanced Task Information

Each task now includes:

#### Basic Information
- `id`: Unique task identifier
- `task_type`: Type of task (docker_push, docker_build, etc.)
- `status`: Current status with description
- `progress`: Progress percentage (0-100)
- `current_step`: Current execution step

#### Timing Information
- `created_at`: Task creation timestamp
- `started_at`: Task start timestamp
- `completed_at`: Task completion timestamp
- `duration`: Task duration in seconds

#### Error Information
- `error`: Error message
- `error_code`: Specific error code
- `error_details`: Additional error details
- `error_info`: Human-readable error description and suggestions

#### Retry Information
- `retry_count`: Number of retry attempts
- `max_retries`: Maximum allowed retries
- `can_retry`: Whether task can be retried

### 5. Queue Statistics

The system provides comprehensive statistics:

#### Summary
- Total tasks
- Max concurrent tasks
- Current running tasks
- Queue size

#### Distributions
- Status distribution (count by status)
- Type distribution (count by task type)
- Error distribution (count by error code)

#### Performance Metrics
- Average task duration
- Success rate
- Completed/failed task counts

#### Retry Statistics
- Total retries across all tasks
- Tasks with retries
- Tasks that reached max retries

#### Recent Activity
- Tasks created in last 24 hours
- Tasks created in last hour

## Usage Examples

### 1. Push Docker Image
```python
from ai_admin.queue.task_queue import TaskQueue, DockerTask, TaskType

queue = TaskQueue()
task = DockerTask(
    task_type=TaskType.PUSH,
    params={
        "image_name": "username/myapp",
        "tag": "latest"
    }
)
task_id = await queue.add_task(task)
```

### 2. Monitor Task Status
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

### 3. Manage Tasks
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

### 4. Get Queue Statistics
```python
stats = await queue.get_queue_stats()
print(f"Success rate: {stats['performance']['success_rate']}%")
print(f"Average duration: {stats['performance']['average_duration_seconds']}s")
print(f"Recent tasks: {stats['recent_activity']['last_hour']}")
```

## Error Handling

### Automatic Error Detection
The system automatically detects and categorizes errors based on:
- Docker command exit codes
- Error message patterns
- System resource availability
- Network connectivity

### Error Recovery
- **Automatic retries**: Failed tasks can be automatically retried
- **Manual retries**: Users can manually retry failed tasks
- **Error suggestions**: System provides specific suggestions for fixing errors

### Error Reporting
Each error includes:
- Human-readable description
- Specific error code
- Detailed error context
- Suggested solutions

## Best Practices

### 1. Task Monitoring
- Always check task status after creation
- Monitor progress for long-running tasks
- Handle errors appropriately

### 2. Resource Management
- Set appropriate timeout values
- Configure retry limits
- Monitor queue statistics

### 3. Error Handling
- Check error codes for specific issues
- Follow suggested solutions
- Implement proper error recovery logic

### 4. Performance Optimization
- Use appropriate concurrent task limits
- Monitor success rates
- Clean up completed tasks regularly 