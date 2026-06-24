"""QueueManagerIntegration lifecycle and module singleton accessors.

Wire lifespan in Step 3.4 when server exposes hook.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Optional

from mcp_proxy_adapter.integrations.queuemgr_integration import (
    QueueManagerIntegration,
)

_integration: Optional[QueueManagerIntegration] = None


def get_queue_integration() -> QueueManagerIntegration:
    """Return the started integration singleton."""
    if _integration is None:
        raise RuntimeError("Queue integration has not been started")
    return _integration


def set_queue_integration(obj: QueueManagerIntegration) -> None:
    """Store the QueueManagerIntegration instance (typically already started)."""
    global _integration
    _integration = obj


async def start_queue_integration(**kwargs: Any) -> None:
    """Start `QueueManagerIntegration` with sane defaults unless overridden."""
    global _integration
    if _integration is not None:
        return

    registry_path = kwargs.pop("registry_path", None)
    in_memory = kwargs.pop("in_memory", True)
    max_concurrent_jobs = kwargs.pop("max_concurrent_jobs", 10)

    instance = QueueManagerIntegration(
        registry_path=registry_path,
        in_memory=in_memory,
        max_concurrent_jobs=max_concurrent_jobs,
        **kwargs,
    )
    await instance.start()
    _integration = instance


async def stop_queue_integration() -> None:
    """Stop and clear the module singleton."""
    global _integration
    if _integration is None:
        return
    await _integration.stop()
    _integration = None
