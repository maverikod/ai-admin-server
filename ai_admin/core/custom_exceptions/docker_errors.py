"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional
from .base import AIAdminBaseException
from .network_errors import ConnectionError, NetworkError

class DockerError(AIAdminBaseException):
    """Base Docker related error."""
    pass



class DockerConnectionError(DockerError):
    """Docker connection error."""
    pass



class DockerImageError(DockerError):
    """Docker image related error."""
    pass



class DockerContainerError(DockerError):
    """Docker container related error."""
    pass



class DockerNetworkError(DockerError):
    """Docker network related error."""
    pass


# Kubernetes Related Exceptions

