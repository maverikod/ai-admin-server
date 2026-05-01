"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional
from .base import AIAdminBaseException

class NetworkError(AIAdminBaseException):
    """Network related error."""
    pass



class ConnectionError(NetworkError):
    """Connection error."""
    pass



class TimeoutError(NetworkError):
    """Operation timeout error."""
    pass



class ConnectionTimeoutError(TimeoutError):
    """Connection timeout error."""
    pass


# File and I/O Exceptions

