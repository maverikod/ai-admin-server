"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional
from .base import AIAdminBaseException
from .config_errors import ConfigurationError
from .network_errors import ConnectionError

class LLMError(AIAdminBaseException):
    """Base LLM related error."""
    pass



class LLMConnectionError(LLMError):
    """LLM connection error."""
    pass



class LLMInferenceError(LLMError):
    """LLM inference error."""
    pass



class LLMConfigurationError(LLMError):
    """LLM configuration error."""
    pass


# System and Monitoring Exceptions

