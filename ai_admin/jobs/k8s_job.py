"""Kubernetes job scaffold for queuemgr.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from queuemgr.jobs.base_core import QueueJobBase  # type: ignore[import-untyped]


class K8sJob(QueueJobBase):
    """Deferred until executor bridge completes later steps."""

    def execute(self) -> None:
        self.set_result(
            {
                "status": "deferred",
                "job": "K8s",
                "detail": "Executor bridge pending Step 2.x–4",
            }
        )
