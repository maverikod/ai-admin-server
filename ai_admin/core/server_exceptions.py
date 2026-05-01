"""Server-related exceptions for AI Admin.

This module contains custom exceptions for server operations,
including startup errors, configuration errors, and SSL-related errors.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Optional, Dict, Any


class ServerError(Exception):
    """Base exception for server-related errors."""

    def __init__(
        self,
        message: str,
        server_type: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize server error.

        Args:
            message: Error message
            server_type: Type of server that failed
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.server_type = server_type
        self.error_code = error_code
        self.details = details or {}


class ServerStartupError(ServerError):
    """Exception raised when server startup fails."""

    def __init__(
        self,
        message: str,
        server_type: str,
        startup_config: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize server startup error.

        Args:
            message: Error message
            server_type: Type of server that failed to start
            startup_config: Server startup configuration
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, server_type, error_code, details)
        self.startup_config = startup_config or {}


class ServerConfigError(ServerError):
    """Exception raised when server configuration fails."""

    def __init__(
        self,
        message: str,
        config_type: str,
        config_data: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize server configuration error.

        Args:
            message: Error message
            config_type: Type of configuration that failed
            config_data: Configuration data that failed
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, "config", error_code, details)
        self.config_type = config_type
        self.config_data = config_data or {}


class SSLServerConfigError(ServerError):
    """Exception raised when SSL server configuration fails."""

    def __init__(
        self,
        message: str,
        ssl_setting: Optional[str] = None,
        ssl_config: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize SSL server configuration error.

        Args:
            message: Error message
            ssl_setting: SSL setting that failed
            ssl_config: SSL configuration that failed
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, "ssl", error_code, details)
        self.ssl_setting = ssl_setting
        self.ssl_config = ssl_config or {}
