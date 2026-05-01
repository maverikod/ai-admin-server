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
from .config_errors import ConfigurationError

class SecurityError(AIAdminBaseException):
    """Base security related error."""
    pass



class SecurityValidationError(SecurityError):
    """Security validation error."""
    pass



class SecurityConfigurationError(SecurityError):
    """Security configuration error."""
    pass



class SecurityAuditError(SecurityError):
    """Security audit error."""
    pass


# Vast.ai Related Exceptions

