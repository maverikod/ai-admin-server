"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional
from .base import AIAdminBaseException

class AuthenticationError(AIAdminBaseException):
    """Authentication failure."""
    pass



class AuthorizationError(AIAdminBaseException):
    """Authorization failure."""
    pass



class TokenError(AuthenticationError):
    """Token validation or processing error."""
    pass



class PermissionError(AIAdminBaseException):
    """Permission denied error."""
    pass



class AccessDeniedError(PermissionError):
    """Access denied error."""
    pass


# Validation Exceptions

