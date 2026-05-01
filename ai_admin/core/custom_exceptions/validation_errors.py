"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional
from .base import AIAdminBaseException

class ValidationError(AIAdminBaseException):
    """Data validation error."""
    pass



class InvalidInputError(ValidationError):
    """Invalid input data error."""
    pass



class DataValidationError(ValidationError):
    """Data validation error."""
    pass



class ConfigValidationError(ValidationError):
    """Configuration validation error."""
    pass


# Configuration Exceptions

