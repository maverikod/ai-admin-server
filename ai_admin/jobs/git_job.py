"""Git job scaffold for queuemgr.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from queuemgr.jobs.base_core import QueueJobBase  # type: ignore[import-untyped]


class GitJob(QueueJobBase):
    """Deferred until executor bridge completes later steps."""

    def execute(self) -> None:
        self.set_result(
            {
                "status": "deferred",
                "job": "Git",
                "detail": "Executor bridge pending Step 2.x–4",
            }
        )
