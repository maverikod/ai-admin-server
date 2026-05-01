from ai_admin.core.custom_exceptions import CertificateError, ValidationError
"""
Certificate exception classes for SSL/TLS certificate management.

This module defines custom exception classes for handling certificate-related
errors in the AI Admin server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List


class CertificateError(Exception):
    """Base exception class for certificate-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize certificate error.
        
        Args:
            message: Error message
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class CertificateValidationError(CertificateError):
    """Exception raised when certificate validation fails."""
    
    def __init__(
        self,
        message: str,
        certificate_path: Optional[str] = None,
        validation_type: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize certificate validation error.
        
        Args:
            message: Error message
            certificate_path: Path to certificate that failed validation
            validation_type: Type of validation that failed
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, error_code, details)
        self.certificate_path = certificate_path
        self.validation_type = validation_type


class CertificateCreationError(CertificateError):
    """Exception raised when certificate creation fails."""
    
    def __init__(
        self,
        message: str,
        certificate_type: str,
        output_path: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize certificate creation error.
        
        Args:
            message: Error message
            certificate_type: Type of certificate being created
            output_path: Path where certificate was being created
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, error_code, details)
        self.certificate_type = certificate_type
        self.output_path = output_path


class CertificateRoleError(CertificateError):
    """Exception raised when certificate role operations fail."""
    
    def __init__(
        self,
        message: str,
        operation: str,
        roles: Optional[List[str]] = None,
        certificate_path: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize certificate role error.
        
        Args:
            message: Error message
            operation: Role operation that failed
            roles: List of roles involved in the operation
            certificate_path: Path to certificate
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, error_code, details)
        self.operation = operation
        self.roles = roles or []
        self.certificate_path = certificate_path
