"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional
from .base import AIAdminBaseException
from .network_errors import ConnectionError, TimeoutError

class QueueError(AIAdminBaseException):
    """Base queue related error."""
    pass



class QueueConnectionError(QueueError):
    """Queue connection error."""
    pass



class QueueTaskError(QueueError):
    """Queue task error."""
    pass



class QueueTimeoutError(QueueError):
    """Queue operation timeout error."""
    pass


# Security Related Exceptions

