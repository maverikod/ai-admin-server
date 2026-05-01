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
from .command_errors import CommandError

class GitError(AIAdminBaseException):
    """Base Git related error."""
    pass



class GitRepositoryError(GitError):
    """Git repository error."""
    pass



class GitCommandError(GitError):
    """Git command execution error."""
    pass



class GitAuthenticationError(GitError):
    """Git authentication error."""
    pass


# Queue Related Exceptions

