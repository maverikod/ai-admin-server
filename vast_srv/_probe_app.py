"""Probe application for testing CST workflow.

Demonstrates a small task queue with workers and a simple registry.
Used as a sandbox for MCP server command exploration.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Lifecycle states of a task."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Task:
    """A single unit of work managed by the queue.

    Attributes:
        task_id: Unique identifier assigned at creation.
        name: Human-readable label for logging and debugging.
        payload: Arbitrary data passed to the worker function.
        status: Current lifecycle state.
        result: Output produced by the worker, if completed.
        error: Exception message if the task failed.
    """

    name: str
    payload: dict
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[dict] = None
    error: Optional[str] = None

    def mark_running(self) -> None:
        """Transition task to RUNNING state."""
        self.status = TaskStatus.RUNNING
        logger.debug("Task %s → RUNNING", self.task_id)

    def mark_done(self, result: dict) -> None:
        """Transition task to DONE and store the result.

        Args:
            result: Output produced by the worker function.
        """
        self.status = TaskStatus.DONE
        self.result = result
        logger.debug("Task %s → DONE", self.task_id)

    def mark_failed(self, error: str) -> None:
        """Transition task to FAILED and store the error message.

        Args:
            error: String representation of the exception.
        """
        self.status = TaskStatus.FAILED
        self.error = error
        logger.warning("Task %s → FAILED: %s", self.task_id, error)


class WorkerRegistry:
    """Registry that maps task names to worker callables.

    Workers are plain functions with signature
    ``(payload: dict) -> dict``.
    """

    def __init__(self) -> None:
        """Initialise an empty registry."""
        self._handlers: dict[str, Callable[[dict], dict]] = {}

    def register(self, name: str, handler: Callable[[dict], dict]) -> None:
        """Register a worker function under a task name.

        Args:
            name: Task name used when submitting tasks to the queue.
            handler: Callable that processes the task payload.

        Raises:
            ValueError: If a handler for *name* is already registered.
        """
        if name in self._handlers:
            raise ValueError(f"Handler already registered for task '{name}'")
        self._handlers[name] = handler
        logger.info("Registered handler for '%s'", name)

    def get(self, name: str) -> Optional[Callable[[dict], dict]]:
        """Return the handler for *name*, or None if not registered.

        Args:
            name: Task name to look up.

        Returns:
            The registered callable, or None.
        """
        return self._handlers.get(name)

    def list_names(self) -> list[str]:
        """Return a sorted list of all registered task names.

        Returns:
            Sorted list of task name strings.
        """
        return sorted(self._handlers)


class TaskQueue:
    """In-memory FIFO queue that dispatches tasks to registered workers.

    Attributes:
        registry: Worker registry used to resolve handlers.
    """

    def __init__(self, registry: WorkerRegistry) -> None:
        """Initialise the queue with a worker registry.

        Args:
            registry: Registry instance to resolve task handlers from.
        """
        self.registry = registry
        self._queue: list[Task] = []

    def submit(self, name: str, payload: dict) -> Task:
        """Create and enqueue a new task.

        Args:
            name: Task name; must have a registered handler.
            payload: Data forwarded to the worker function.

        Returns:
            The newly created Task object.

        Raises:
            KeyError: If no handler is registered for *name*.
        """
        if self.registry.get(name) is None:
            raise KeyError(f"No handler registered for task '{name}'")
        task = Task(name=name, payload=payload)
        self._queue.append(task)
        logger.info("Submitted task %s (name=%s)", task.task_id, name)
        return task

    def run_next(self) -> Optional[Task]:
        """Dequeue and execute the next pending task.

        Returns:
            The executed Task, or None if the queue is empty.
        """
        if not self._queue:
            return None
        task = self._queue.pop(0)
        handler = self.registry.get(task.name)
        task.mark_running()
        try:
            result = handler(task.payload)
            task.mark_done(result)
        except Exception as exc:  # noqa: BLE001
            task.mark_failed(str(exc))
        return task

    def run_all(self) -> list[Task]:
        """Execute all pending tasks in order.

        Returns:
            List of executed Task objects in execution order.
        """
        executed: list[Task] = []
        while self._queue:
            executed.append(self.run_next())
        return executed

    def pending_count(self) -> int:
        """Return the number of tasks currently waiting in the queue.

        Returns:
            Integer count of pending tasks.
        """
        return len(self._queue)
