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

class VectorStoreError(AIAdminBaseException):
    """Base vector store related error."""
    pass



class VectorStoreConnectionError(VectorStoreError):
    """Vector store connection error."""
    pass



class VectorStoreConfigurationError(VectorStoreError):
    """Vector store configuration error."""
    pass


# LLM Related Exceptions

