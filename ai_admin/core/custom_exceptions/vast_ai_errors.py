"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional
from .base import AIAdminBaseException
from .network_errors import ConnectionError

class VastAIError(AIAdminBaseException):
    """Base Vast.ai related error."""
    pass



class VastAIConnectionError(VastAIError):
    """Vast.ai connection error."""
    pass



class VastAIInstanceError(VastAIError):
    """Vast.ai instance error."""
    pass


# FTP Related Exceptions

