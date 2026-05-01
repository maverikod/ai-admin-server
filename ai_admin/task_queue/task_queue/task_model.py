"""Module task_model."""

from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, NetworkError
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

    def fail(
        self,
        error: str,
        error_code: TaskErrorCode = TaskErrorCode.UNKNOWN_ERROR,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> None:
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
        return self.retry_count < self.max_retries and self.status in [
            TaskStatus.FAILED,
            TaskStatus.TIMEOUT,
        ]

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
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
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
            "can_retry": self.can_retry(),
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
            TaskStatus.TIMEOUT: "Task execution timed out",
        }
        return status_descriptions.get(self.status, "Unknown status")



