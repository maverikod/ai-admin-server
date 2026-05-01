"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional
from .base import AIAdminBaseException

class ConfigurationError(AIAdminBaseException):
    """Configuration error."""
    pass



class ConfigNotFoundError(ConfigurationError):
    """Configuration file not found."""
    pass



class ConfigParseError(ConfigurationError):
    """Configuration parsing error."""
    pass


# Network and Connection Exceptions

