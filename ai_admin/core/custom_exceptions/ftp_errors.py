"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional
from .base import AIAdminBaseException
from .auth_errors import AuthenticationError
from .network_errors import ConnectionError

class FTPError(AIAdminBaseException):
    """Base FTP related error."""
    pass



class FTPConnectionError(FTPError):
    """FTP connection error."""
    pass



class FTPAuthenticationError(FTPError):
    """FTP authentication error."""
    pass



class FTPTransferError(FTPError):
    """FTP transfer error."""
    pass


# Ollama Related Exceptions

