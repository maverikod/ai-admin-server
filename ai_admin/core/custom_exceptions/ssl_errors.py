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

class SSLError(AIAdminBaseException):
    """Base SSL/TLS related error."""
    pass



class CertificateError(SSLError):
    """Certificate validation or processing error."""
    pass



class TLSHandshakeError(SSLError):
    """TLS handshake failure."""
    pass



class SSLConfigurationError(SSLError):
    """SSL configuration error."""
    pass



class MTLSConfigurationError(SSLError):
    """mTLS configuration error."""
    pass


# Authentication and Authorization Exceptions

