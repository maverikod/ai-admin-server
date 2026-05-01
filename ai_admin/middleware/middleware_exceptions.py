from ai_admin.core.custom_exceptions import AccessDeniedError, ValidationError
"""Custom exceptions for middleware components.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional


class MiddlewareError(Exception):
    """Base exception for middleware errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize middleware error.

        Args:
            message: Error message
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class CertificateValidationError(MiddlewareError):
    """Exception raised when certificate validation fails."""

    def __init__(
        self,
        message: str,
        certificate_info: Optional[Dict[str, Any]] = None,
        validation_details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize certificate validation error.

        Args:
            message: Error message
            certificate_info: Information about the certificate
            validation_details: Details about validation failure
        """
        super().__init__(
            message,
            error_code="CERT_VALIDATION_ERROR",
            details={
                "certificate_info": certificate_info or {},
                "validation_details": validation_details or {},
            },
        )
        self.certificate_info = certificate_info or {}
        self.validation_details = validation_details or {}


class RoleValidationError(MiddlewareError):
    """Exception raised when role validation fails."""

    def __init__(
        self,
        message: str,
        client_roles: Optional[list] = None,
        required_roles: Optional[list] = None,
        endpoint: Optional[str] = None,
    ):
        """
        Initialize role validation error.

        Args:
            message: Error message
            client_roles: Roles found in client certificate
            required_roles: Roles required for access
            endpoint: Endpoint that was accessed
        """
        super().__init__(
            message,
            error_code="ROLE_VALIDATION_ERROR",
            details={
                "client_roles": client_roles or [],
                "required_roles": required_roles or [],
                "endpoint": endpoint or "unknown",
            },
        )
        self.client_roles = client_roles or []
        self.required_roles = required_roles or []
        self.endpoint = endpoint or "unknown"


class AccessDeniedError(MiddlewareError):
    """Exception raised when access is denied."""

    def __init__(
        self,
        message: str,
        client_identity: Optional[str] = None,
        requested_resource: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        """
        Initialize access denied error.

        Args:
            message: Error message
            client_identity: Client identity information
            requested_resource: Resource that was requested
            reason: Reason for access denial
        """
        super().__init__(
            message,
            error_code="ACCESS_DENIED",
            details={
                "client_identity": client_identity or "unknown",
                "requested_resource": requested_resource or "unknown",
                "reason": reason or "insufficient_permissions",
            },
        )
        self.client_identity = client_identity or "unknown"
        self.requested_resource = requested_resource or "unknown"
        self.reason = reason or "insufficient_permissions"


class TokenValidationError(MiddlewareError):
    """Exception raised when token validation fails."""

    def __init__(
        self,
        message: str,
        token_info: Optional[Dict[str, Any]] = None,
        validation_details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize token validation error.

        Args:
            message: Error message
            token_info: Information about the token
            validation_details: Details about validation failure
        """
        super().__init__(
            message,
            error_code="TOKEN_VALIDATION_ERROR",
            details={
                "token_info": token_info or {},
                "validation_details": validation_details or {},
            },
        )
        self.token_info = token_info or {}
        self.validation_details = validation_details or {}


class TokenExpiredError(TokenValidationError):
    """Exception raised when token has expired."""

    def __init__(
        self,
        message: str = "Token has expired",
        token_info: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize token expired error.

        Args:
            message: Error message
            token_info: Information about the expired token
        """
        super().__init__(
            message,
            token_info=token_info,
            validation_details={"error_type": "expired"},
        )


class TokenInvalidError(TokenValidationError):
    """Exception raised when token is invalid."""

    def __init__(
        self,
        message: str = "Token is invalid",
        token_info: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize token invalid error.

        Args:
            message: Error message
            token_info: Information about the invalid token
        """
        super().__init__(
            message,
            token_info=token_info,
            validation_details={"error_type": "invalid"},
        )


class PermissionDeniedError(MiddlewareError):
    """Exception raised when permission is denied."""

    def __init__(
        self,
        message: str,
        user_roles: Optional[list] = None,
        required_permissions: Optional[list] = None,
        resource: Optional[str] = None,
    ):
        """
        Initialize permission denied error.

        Args:
            message: Error message
            user_roles: User roles that were checked
            required_permissions: Permissions required for access
            resource: Resource that was requested
        """
        super().__init__(
            message,
            error_code="PERMISSION_DENIED",
            details={
                "user_roles": user_roles or [],
                "required_permissions": required_permissions or [],
                "resource": resource or "unknown",
            },
        )
        self.user_roles = user_roles or []
        self.required_permissions = required_permissions or []
        self.resource = resource or "unknown"
