"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional
from .base import AIAdminBaseException
from .auth_errors import AuthenticationError
from .network_errors import ConnectionError

class GitHubError(AIAdminBaseException):
    """Base GitHub related error."""
    pass



class GitHubConnectionError(GitHubError):
    """GitHub connection error."""
    pass



class GitHubAuthenticationError(GitHubError):
    """GitHub authentication error."""
    pass



class GitHubRepositoryError(GitHubError):
    """GitHub repository error."""
    pass


# Vector Store Related Exceptions

