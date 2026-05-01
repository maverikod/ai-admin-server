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

class OllamaError(AIAdminBaseException):
    """Base Ollama related error."""
    pass



class OllamaConnectionError(OllamaError):
    """Ollama connection error."""
    pass



class OllamaModelError(OllamaError):
    """Ollama model error."""
    pass



class OllamaInferenceError(OllamaError):
    """Ollama inference error."""
    pass


# GitHub Related Exceptions

