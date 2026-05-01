"""Factory-related exceptions for AI Admin.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Optional, Dict, Any


class FactoryError(Exception):
    """Base exception for factory-related errors."""

    def __init__(
        self,
        message: str,
        factory_component: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize factory error.

        Args:
            message: Error message
            factory_component: Factory component that failed
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.factory_component = factory_component
        self.error_code = error_code
        self.details = details or {}


class AppCreationError(FactoryError):
    """Exception raised when application creation fails."""

    def __init__(
        self,
        message: str,
        app_config: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize application creation error.

        Args:
            message: Error message
            app_config: Application configuration that failed
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, "app_creation", error_code, details)
        self.app_config = app_config or {}


class MiddlewareSetupError(FactoryError):
    """Exception raised when middleware setup fails."""

    def __init__(
        self,
        message: str,
        middleware_type: Optional[str] = None,
        middleware_config: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize middleware setup error.

        Args:
            message: Error message
            middleware_type: Type of middleware that failed
            middleware_config: Middleware configuration
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, "middleware_setup", error_code, details)
        self.middleware_type = middleware_type
        self.middleware_config = middleware_config or {}


class CommandRegistrationError(FactoryError):
    """Exception raised when command registration fails."""

    def __init__(
        self,
        message: str,
        command_name: Optional[str] = None,
        command_class: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize command registration error.

        Args:
            message: Error message
            command_name: Name of command that failed to register
            command_class: Command class that failed
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, "command_registration", error_code, details)
        self.command_name = command_name
        self.command_class = command_class
