"""Docker job for queuemgr backed by legacy DockerExecutor.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import asyncio
from typing import List, Optional

from ai_admin.task_queue.task_queue.enums import TaskStatus
from ai_admin.task_queue.task_queue.queue.docker_executor import DockerExecutor
from ai_admin.task_queue.task_queue.task import Task
from ai_admin.task_queue.task_queue.task_type import TaskType
from queuemgr.jobs.base_core import QueueJobBase  # type: ignore[import-untyped]

from .task_from_params import make_task


class DockerJob(QueueJobBase):
    """Execute Docker ``push``, ``pull``, or ``build`` via DockerExecutor."""

    def execute(self) -> None:
        raw = dict(self.params)
        op = raw.get("op")
        if op not in ("push", "pull", "build"):
            self.set_result(
                {
                    "ok": False,
                    "success": False,
                    "error": (
                        'params must include string "op" one of '
                        '("push","pull","build"); '
                        f"got {op!r}"
                    ),
                }
            )
            return

        exec_params = {k: v for k, v in raw.items() if k != "op"}
        routing = {
            "push": (TaskType.DOCKER_PUSH, "_execute_docker_push_task"),
            "pull": (TaskType.DOCKER_PULL, "_execute_docker_pull_task"),
            "build": (TaskType.DOCKER_BUILD, "_execute_docker_build_task"),
        }
        task_type, method_name = routing[op]
        holder: List[Optional[Task]] = [None]

        async def _runner() -> None:
            exe = DockerExecutor()
            built = make_task(task_type, exec_params)
            await getattr(exe, method_name)(built)
            holder[0] = built

        try:
            asyncio.run(_runner())
        except Exception as exc:
            self.set_result({"ok": False, "success": False, "error": str(exc)})
            return

        qt = holder[0]
        if qt is None:
            self.set_result(
                {"ok": False, "success": False, "error": "executor did not expose task"}
            )
            return

        if qt.status == TaskStatus.COMPLETED:
            self.set_result({"ok": True, "result": qt.result})
            return

        if qt.status == TaskStatus.FAILED:
            self.set_result(
                {
                    "ok": False,
                    "success": False,
                    "error": qt.error or "Docker task failed",
                    "result": qt.result,
                    "details": qt.error_details,
                }
            )
            return

        self.set_result(
            {
                "ok": False,
                "success": False,
                "error": (
                    "unexpected_task_status_after_execute: "
                    f"{getattr(qt.status, 'value', qt.status)}"
                ),
            }
        )
