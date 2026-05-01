"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional
from .base import AIAdminBaseException
from .auth_errors import PermissionError

class FileNotFoundError(AIAdminBaseException):
    """File not found error."""
    pass



class IOError(AIAdminBaseException):
    """I/O operation error."""
    pass



class FilePermissionError(IOError):
    """File permission error."""
    pass



class DirectoryNotFoundError(IOError):
    """Directory not found error."""
    pass


# Docker Related Exceptions

