"""Exceptions for SSL test environment.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Optional


class TestEnvironmentError(Exception):
    """Base exception for test environment errors.

    This is the base exception class for all test environment related errors.
    It provides a common interface for error handling in the test environment.

    Args:
        message: Error message describing what went wrong
        details: Optional additional details about the error
        error_code: Optional error code for programmatic error handling
    """

    def __init__(
        self,
        message: str,
        details: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        """Initialize TestEnvironmentError.

        Args:
            message: Error message describing what went wrong
            details: Optional additional details about the error
            error_code: Optional error code for programmatic error handling
        """
        super().__init__(message)
        self.message = message
        self.details = details
        self.error_code = error_code

    def __str__(self) -> str:
        """Return string representation of the error.

        Returns:
            Formatted error message with details if available
        """
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class CertificateGenerationError(TestEnvironmentError):
    """Exception raised when certificate generation fails.

    This exception is raised when there are issues generating test certificates,
    such as OpenSSL command failures, invalid parameters, or file system errors.

    Args:
        message: Error message describing the certificate generation failure
        certificate_type: Type of certificate that failed to generate
        details: Optional additional details about the error
        error_code: Optional error code for programmatic error handling
    """

    def __init__(
        self,
        message: str,
        certificate_type: Optional[str] = None,
        details: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        """Initialize CertificateGenerationError.

        Args:
            message: Error message describing the certificate generation failure
            certificate_type: Type of certificate that failed to generate
            details: Optional additional details about the error
            error_code: Optional error code for programmatic error handling
        """
        super().__init__(message, details, error_code)
        self.certificate_type = certificate_type

    def __str__(self) -> str:
        """Return string representation of the error.

        Returns:
            Formatted error message with certificate type and details
        """
        base_msg = self.message
        if self.certificate_type:
            base_msg = (
                f"Certificate generation failed for {self.certificate_type}: {base_msg}"
            )
        if self.details:
            base_msg += f" Details: {self.details}"
        return base_msg


class ConfigGenerationError(TestEnvironmentError):
    """Exception raised when configuration generation fails.

    This exception is raised when there are issues generating test configurations,
    such as JSON serialization errors, invalid configuration parameters, or
    file system errors.

    Args:
        message: Error message describing the configuration generation failure
        config_type: Type of configuration that failed to generate
        details: Optional additional details about the error
        error_code: Optional error code for programmatic error handling
    """

    def __init__(
        self,
        message: str,
        config_type: Optional[str] = None,
        details: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        """Initialize ConfigGenerationError.

        Args:
            message: Error message describing the configuration generation failure
            config_type: Type of configuration that failed to generate
            details: Optional additional details about the error
            error_code: Optional error code for programmatic error handling
        """
        super().__init__(message, details, error_code)
        self.config_type = config_type

    def __str__(self) -> str:
        """Return string representation of the error.

        Returns:
            Formatted error message with config type and details
        """
        base_msg = self.message
        if self.config_type:
            base_msg = (
                f"Configuration generation failed for {self.config_type}: "
                f"{base_msg}"
            )
        if self.details:
            base_msg += f" Details: {self.details}"
        return base_msg


class EnvironmentSetupError(TestEnvironmentError):
    """Exception raised when test environment setup fails.

    This exception is raised when there are issues setting up the test environment,
    such as directory creation failures, permission issues, or dependency problems.

    Args:
        message: Error message describing the environment setup failure
        component: Component that failed to setup
        details: Optional additional details about the error
        error_code: Optional error code for programmatic error handling
    """

    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        details: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        """Initialize EnvironmentSetupError.

        Args:
            message: Error message describing the environment setup failure
            component: Component that failed to setup
            details: Optional additional details about the error
            error_code: Optional error code for programmatic error handling
        """
        super().__init__(message, details, error_code)
        self.component = component

    def __str__(self) -> str:
        """Return string representation of the error.

        Returns:
            Formatted error message with component and details
        """
        base_msg = self.message
        if self.component:
            base_msg = f"Environment setup failed for {self.component}: {base_msg}"
        if self.details:
            base_msg += f" Details: {self.details}"
        return base_msg


class EnvironmentValidationError(TestEnvironmentError):
    """Exception raised when test environment validation fails.

    This exception is raised when the test environment fails validation checks,
    such as missing files, invalid configurations, or incorrect permissions.

    Args:
        message: Error message describing the validation failure
        validation_type: Type of validation that failed
        details: Optional additional details about the error
        error_code: Optional error code for programmatic error handling
    """

    def __init__(
        self,
        message: str,
        validation_type: Optional[str] = None,
        details: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        """Initialize EnvironmentValidationError.

        Args:
            message: Error message describing the validation failure
            validation_type: Type of validation that failed
            details: Optional additional details about the error
            error_code: Optional error code for programmatic error handling
        """
        super().__init__(message, details, error_code)
        self.validation_type = validation_type

    def __str__(self) -> str:
        """Return string representation of the error.

        Returns:
            Formatted error message with validation type and details
        """
        base_msg = self.message
        if self.validation_type:
            base_msg = f"Validation failed for {self.validation_type}: {base_msg}"
        if self.details:
            base_msg += f" Details: {self.details}"
        return base_msg
