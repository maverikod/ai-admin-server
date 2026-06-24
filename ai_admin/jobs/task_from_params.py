"""Build Task instances for legacy executors used by queue jobs.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from ai_admin.task_queue.task_queue.enums import TaskStatus
from ai_admin.task_queue.task_queue.task import Task
from ai_admin.task_queue.task_queue.task_type import TaskType


def make_task(task_type: TaskType, params: dict) -> Task:
    """Instantiate Task with executor-ready defaults (explicit instance fields).

    The ``Task`` class in this codebase does not provide a usable ``__init__``,
    but executors rely on instance attributes ``params``, ``logs``, ``result``,
    etc. ``make_task`` sets those explicitly so helpers like ``add_log`` work.
    """
    task = Task()
    task.id = str(uuid4())
    task.task_type = task_type
    task.params = dict(params)
    task.status = TaskStatus.PENDING
    task.command = ""
    task.created_at = datetime.now()
    task.started_at = None
    task.completed_at = None
    task.progress = 0
    task.current_step = ""
    task.result = None
    task.error = None
    task.error_code = None
    task.error_details = None
    task.logs = []
    task.timeout_seconds = 3600
    task.retry_count = 0
    task.max_retries = 3
    task.priority = 0
    task.category = "general"
    task.tags = []
    return task
