"""
Queue Client with comprehensive task management capabilities

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import json

from ai_admin.task_queue.queue_manager import QueueManager
from ai_admin.task_queue.task_queue import Task, TaskType, TaskStatus

logger = logging.getLogger(__name__)


class QueueAction(Enum):
    """Queue action enumeration."""
    PAUSE = "pause"
    RESUME = "resume"
    RETRY = "retry"
    CANCEL = "cancel"
    PRIORITIZE = "prioritize"
    MOVE = "move"


class QueueFilter(Enum):
    """Queue filter enumeration."""
    ALL = "all"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class QueueMetrics:
    """Queue metrics information."""
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    cancelled_tasks: int
    paused_tasks: int
    average_execution_time: float
    success_rate: float
    throughput_per_hour: float
    queue_size: int
    max_concurrent: int
    active_workers: int


@dataclass
class TaskInfo:
    """Task information."""
    task_id: str
    task_type: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: float
    priority: int
    retry_count: int
    max_retries: int
    error_message: Optional[str]
    result: Optional[Dict[str, Any]]
    logs: List[str]
    params: Dict[str, Any]


class QueueClient:
    """Enhanced queue client with comprehensive task management capabilities."""

    def __init__(self):
        """Initialize queue client."""
        self.queue_manager = QueueManager()
        self.logger = logging.getLogger(__name__)

    async def get_queue_status(
        self,
        include_logs: bool = False,
        detailed: bool = True,
        filter_status: Optional[QueueFilter] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive queue status.

        Args:
            include_logs: Include task logs in response
            detailed: Include detailed information
            filter_status: Filter tasks by status

        Returns:
            Queue status information
        """
        try:
            # Get basic queue information
            queue_info = await self.queue_manager.get_queue_status()
            
            # Get task list
            tasks = await self.queue_manager.list_tasks()
            
            # Apply filter if specified
            if filter_status and filter_status != QueueFilter.ALL:
                status_map = {
                    QueueFilter.PENDING: TaskStatus.PENDING,
                    QueueFilter.RUNNING: TaskStatus.RUNNING,
                    QueueFilter.COMPLETED: TaskStatus.COMPLETED,
                    QueueFilter.FAILED: TaskStatus.FAILED,
                    QueueFilter.CANCELLED: TaskStatus.CANCELLED,
                    QueueFilter.PAUSED: TaskStatus.PAUSED,
                }
                target_status = status_map.get(filter_status)
                if target_status:
                    tasks = [task for task in tasks if task.status == target_status]
            
            # Convert tasks to info objects
            task_infos = []
            for task in tasks:
                task_info = TaskInfo(
                    task_id=task.id,
                    task_type=task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
                    status=task.status.value if hasattr(task.status, 'value') else str(task.status),
                    created_at=task.created_at,
                    started_at=task.started_at,
                    completed_at=task.completed_at,
                    progress=task.progress,
                    priority=task.priority,
                    retry_count=task.retry_count,
                    max_retries=task.max_retries,
                    error_message=task.error_message,
                    result=task.result,
                    logs=task.logs if include_logs else [],
                    params=task.params,
                )
                task_infos.append(asdict(task_info))
            
            # Calculate metrics
            metrics = await self._calculate_metrics(tasks)
            
            return {
                "status": "success",
                "queue_info": queue_info,
                "tasks": task_infos,
                "task_count": len(task_infos),
                "metrics": asdict(metrics),
                "filter_applied": filter_status.value if filter_status else None,
                "detailed": detailed,
                "include_logs": include_logs,
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get queue status: {e}")
            raise

    async def get_task_status(
        self,
        task_id: str,
        include_logs: bool = True,
        include_result: bool = True,
    ) -> Dict[str, Any]:
        """
        Get detailed status of a specific task.

        Args:
            task_id: Task identifier
            include_logs: Include task logs
            include_result: Include task result

        Returns:
            Task status information
        """
        try:
            task = await self.queue_manager.get_task(task_id)
            if not task:
                return {
                    "status": "error",
                    "message": f"Task {task_id} not found",
                    "task_id": task_id,
                }
            
            task_info = TaskInfo(
                task_id=task.id,
                task_type=task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
                status=task.status.value if hasattr(task.status, 'value') else str(task.status),
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                progress=task.progress,
                priority=task.priority,
                retry_count=task.retry_count,
                max_retries=task.max_retries,
                error_message=task.error_message,
                result=task.result if include_result else None,
                logs=task.logs if include_logs else [],
                params=task.params,
            )
            
            return {
                "status": "success",
                "task": asdict(task_info),
                "include_logs": include_logs,
                "include_result": include_result,
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get task status: {e}")
            raise

    async def get_task_logs(
        self,
        task_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get logs for a specific task.

        Args:
            task_id: Task identifier
            limit: Maximum number of log entries
            offset: Offset for pagination

        Returns:
            Task logs
        """
        try:
            logs = await self.queue_manager.get_task_logs(task_id)
            
            # Apply pagination
            if offset > 0:
                logs = logs[offset:]
            if limit:
                logs = logs[:limit]
            
            return {
                "status": "success",
                "task_id": task_id,
                "logs": logs,
                "total_logs": len(logs),
                "limit": limit,
                "offset": offset,
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get task logs: {e}")
            raise

    async def manage_task(
        self,
        action: QueueAction,
        task_id: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Manage a task (pause, resume, retry, cancel, etc.).

        Args:
            action: Action to perform
            task_id: Task identifier
            **kwargs: Additional parameters

        Returns:
            Management result
        """
        try:
            if action == QueueAction.PAUSE:
                result = await self.queue_manager.pause_task(task_id)
            elif action == QueueAction.RESUME:
                result = await self.queue_manager.resume_task(task_id)
            elif action == QueueAction.RETRY:
                result = await self.queue_manager.retry_task(task_id)
            elif action == QueueAction.CANCEL:
                result = await self.queue_manager.cancel_task(task_id)
            elif action == QueueAction.PRIORITIZE:
                priority = kwargs.get('priority', 1)
                result = await self.queue_manager.set_task_priority(task_id, priority)
            elif action == QueueAction.MOVE:
                position = kwargs.get('position', 0)
                result = await self.queue_manager.move_task(task_id, position)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            return {
                "status": "success",
                "action": action.value,
                "task_id": task_id,
                "result": result,
            }
            
        except Exception as e:
            self.logger.error(f"Failed to manage task {task_id}: {e}")
            raise

    async def clear_queue(
        self,
        filter_status: Optional[QueueFilter] = None,
        older_than: Optional[timedelta] = None,
    ) -> Dict[str, Any]:
        """
        Clear tasks from queue.

        Args:
            filter_status: Filter tasks by status
            older_than: Remove tasks older than this duration

        Returns:
            Clear result
        """
        try:
            tasks = await self.queue_manager.list_tasks()
            removed_count = 0
            
            for task in tasks:
                should_remove = False
                
                # Apply status filter
                if filter_status and filter_status != QueueFilter.ALL:
                    status_map = {
                        QueueFilter.PENDING: TaskStatus.PENDING,
                        QueueFilter.RUNNING: TaskStatus.RUNNING,
                        QueueFilter.COMPLETED: TaskStatus.COMPLETED,
                        QueueFilter.FAILED: TaskStatus.FAILED,
                        QueueFilter.CANCELLED: TaskStatus.CANCELLED,
                        QueueFilter.PAUSED: TaskStatus.PAUSED,
                    }
                    target_status = status_map.get(filter_status)
                    if target_status and task.status == target_status:
                        should_remove = True
                else:
                    should_remove = True
                
                # Apply time filter
                if older_than and should_remove:
                    if task.created_at < datetime.now() - older_than:
                        should_remove = True
                    else:
                        should_remove = False
                
                if should_remove:
                    await self.queue_manager.remove_task(task.id)
                    removed_count += 1
            
            return {
                "status": "success",
                "removed_count": removed_count,
                "filter_status": filter_status.value if filter_status else None,
                "older_than": str(older_than) if older_than else None,
            }
            
        except Exception as e:
            self.logger.error(f"Failed to clear queue: {e}")
            raise

    async def get_queue_health(self) -> Dict[str, Any]:
        """
        Get queue health information.

        Returns:
            Queue health status
        """
        try:
            metrics = await self._calculate_metrics(await self.queue_manager.list_tasks())
            
            # Determine health status
            health_status = "healthy"
            issues = []
            
            if metrics.failed_tasks > metrics.completed_tasks * 0.1:  # More than 10% failure rate
                health_status = "warning"
                issues.append("High failure rate")
            
            if metrics.queue_size > metrics.max_concurrent * 10:  # Queue too long
                health_status = "warning"
                issues.append("Queue backlog")
            
            if metrics.average_execution_time > 3600:  # Average execution > 1 hour
                health_status = "warning"
                issues.append("Slow task execution")
            
            return {
                "status": "success",
                "health_status": health_status,
                "issues": issues,
                "metrics": asdict(metrics),
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get queue health: {e}")
            raise

    async def get_queue_statistics(
        self,
        time_range: Optional[timedelta] = None,
    ) -> Dict[str, Any]:
        """
        Get queue statistics for a time range.

        Args:
            time_range: Time range for statistics

        Returns:
            Queue statistics
        """
        try:
            tasks = await self.queue_manager.list_tasks()
            
            # Filter by time range if specified
            if time_range:
                cutoff_time = datetime.now() - time_range
                tasks = [task for task in tasks if task.created_at >= cutoff_time]
            
            # Calculate statistics
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
            failed_tasks = len([t for t in tasks if t.status == TaskStatus.FAILED])
            
            # Calculate execution times
            execution_times = []
            for task in tasks:
                if task.started_at and task.completed_at:
                    exec_time = (task.completed_at - task.started_at).total_seconds()
                    execution_times.append(exec_time)
            
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            
            # Task type distribution
            task_types = {}
            for task in tasks:
                task_type = task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type)
                task_types[task_type] = task_types.get(task_type, 0) + 1
            
            return {
                "status": "success",
                "time_range": str(time_range) if time_range else "all",
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "average_execution_time": avg_execution_time,
                "task_type_distribution": task_types,
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get queue statistics: {e}")
            raise

    async def _calculate_metrics(self, tasks: List[Task]) -> QueueMetrics:
        """Calculate queue metrics from task list."""
        total_tasks = len(tasks)
        pending_tasks = len([t for t in tasks if t.status == TaskStatus.PENDING])
        running_tasks = len([t for t in tasks if t.status == TaskStatus.RUNNING])
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in tasks if t.status == TaskStatus.FAILED])
        cancelled_tasks = len([t for t in tasks if t.status == TaskStatus.CANCELLED])
        paused_tasks = len([t for t in tasks if t.status == TaskStatus.PAUSED])
        
        # Calculate average execution time
        execution_times = []
        for task in tasks:
            if task.started_at and task.completed_at:
                exec_time = (task.completed_at - task.started_at).total_seconds()
                execution_times.append(exec_time)
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # Calculate success rate
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate throughput (tasks per hour)
        if tasks:
            oldest_task = min(tasks, key=lambda t: t.created_at)
            newest_task = max(tasks, key=lambda t: t.created_at)
            time_span = (newest_task.created_at - oldest_task.created_at).total_seconds() / 3600
            throughput_per_hour = total_tasks / time_span if time_span > 0 else 0
        else:
            throughput_per_hour = 0
        
        return QueueMetrics(
            total_tasks=total_tasks,
            pending_tasks=pending_tasks,
            running_tasks=running_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            cancelled_tasks=cancelled_tasks,
            paused_tasks=paused_tasks,
            average_execution_time=avg_execution_time,
            success_rate=success_rate,
            throughput_per_hour=throughput_per_hour,
            queue_size=pending_tasks + running_tasks,
            max_concurrent=self.queue_manager.task_queue.max_concurrent,
            active_workers=running_tasks,
        )
