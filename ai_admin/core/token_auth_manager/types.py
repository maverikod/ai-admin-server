"""Module types."""

from ai_admin.core.custom_exceptions import AuthenticationError, CustomError, SSLError, TokenError, ValidationError
import os
import json
import jwt
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from ..config.token_config import TokenManager, TokenStatus
from ..config.roles_config import RolesConfig
from .ssl_error_handler import SSLErrorHandler

class TokenAuthError(Exception):
    """Base exception for token authentication errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "TOKEN_AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}



class TokenValidationError(TokenAuthError):
    """Exception raised when token validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "TOKEN_VALIDATION_ERROR", details)



class TokenExpiredError(TokenAuthError):
    """Exception raised when token has expired."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "TOKEN_EXPIRED_ERROR", details)



class TokenInvalidError(TokenAuthError):
    """Exception raised when token is invalid."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "TOKEN_INVALID_ERROR", details)



class PermissionCheckError(TokenAuthError):
    """Exception raised when permission check fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "PERMISSION_CHECK_ERROR", details)



class TokenAuthResult:
    """Result of token authentication operation."""

    authenticated: bool
    user_id: Optional[str] = None
    roles: List[str] = None
    permissions: List[str] = None
    token_info: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.roles is None:
            self.roles = []
        if self.permissions is None:
            self.permissions = []



