"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional
from .base import AIAdminBaseException

class SystemError(AIAdminBaseException):
    """Base system related error."""
    pass



class SystemMonitoringError(SystemError):
    """System monitoring error."""
    pass



class SystemResourceError(SystemError):
    """System resource error."""
    pass


# Command Related Exceptions

