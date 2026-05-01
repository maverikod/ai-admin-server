"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional
from .base import AIAdminBaseException
from .validation_errors import ValidationError
from .network_errors import TimeoutError

class CommandError(AIAdminBaseException):
    """Base command related error."""
    pass



class CommandExecutionError(CommandError):
    """Command execution error."""
    pass



class CommandTimeoutError(CommandError):
    """Command timeout error."""
    pass



class CommandValidationError(CommandError):
    """Command validation error."""
    pass


# Application Level Exceptions

