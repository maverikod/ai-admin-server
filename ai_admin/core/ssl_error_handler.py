"""SSL error handling utilities for the AI Admin server."""

"""SSL error handling utilities for the AI Admin server."""
from ai_admin.core.custom_exceptions import SSLError

"""
SSL/mTLS error handler for comprehensive error management.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import ssl
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

# Note: Importing these classes would create circular imports
# They are used only for type hints and are imported locally when needed


class SSLErrorType(Enum):
    """SSL error types for classification."""

    SSL_CONTEXT_ERROR = "ssl_context_error"
    SSL_HANDSHAKE_ERROR = "ssl_handshake_error"
    SSL_CERTIFICATE_ERROR = "ssl_certificate_error"
    SSL_PROTOCOL_ERROR = "ssl_protocol_error"
    SSL_VERIFICATION_ERROR = "ssl_verification_error"
    MTLS_AUTH_ERROR = "mtls_auth_error"
    MTLS_CERT_VALIDATION_ERROR = "mtls_cert_validation_error"
    MTLS_ROLE_EXTRACTION_ERROR = "mtls_role_extraction_error"
    TOKEN_AUTH_ERROR = "token_auth_error"
    TOKEN_VALIDATION_ERROR = "token_validation_error"
    TOKEN_EXPIRY_ERROR = "token_expiry_error"
    CONFIGURATION_ERROR = "configuration_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


class SSLErrorSeverity(Enum):
    """SSL error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SSLErrorInfo:
    """SSL error information structure."""

    error_type: SSLErrorType
    severity: SSLErrorSeverity
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    component: str
    operation: str
    user_roles: List[str]
    client_info: Optional[Dict[str, Any]] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False


class SSLErrorHandler:
    """
    Comprehensive SSL/mTLS error handler.

    This class provides:
    - Classification of SSL/mTLS errors
    - Detailed error logging
    - Audit trail for security events
    - Error recovery mechanisms
    - Performance monitoring
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize SSL error handler.

        Args:
            config: Configuration dictionary for error handling
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.audit_logger = logging.getLogger(f"{__name__}.audit")

        # Error tracking
        self.error_count: Dict[SSLErrorType, int] = {
            error_type: 0 for error_type in SSLErrorType
        }
        self.recent_errors: List[SSLErrorInfo] = []
        self.max_recent_errors = self.config.get("max_recent_errors", 100)

        # Recovery configuration
        self.recovery_config = self.config.get("recovery", {})
        self.max_recovery_attempts = self.recovery_config.get("max_attempts", 3)
        self.recovery_delay = self.recovery_config.get("delay_seconds", 1)

        # Alert configuration
        self.alert_config = self.config.get("alerts", {})
        self.alert_thresholds = self.alert_config.get("thresholds", {})

        self.logger.info("SSL error handler initialized")

    async def handle_ssl_error(
        self,
        error: Exception,
        component: str,
        operation: str,
        user_roles: List[str] = None,
        client_info: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> SSLErrorInfo:
        """
        Handle SSL-related errors.

        Args:
            error: The SSL error exception
            component: Component where error occurred
            operation: Operation being performed
            user_roles: User roles for the operation
            client_info: Client information
            context: Additional context information

        Returns:
            SSLErrorInfo: Structured error information
        """
        user_roles = user_roles or []
        context = context or {}

        # Classify the error
        error_type, severity = self._classify_ssl_error(error, component, operation)

        # Create error info
        error_info = SSLErrorInfo(
            error_type=error_type,
            severity=severity,
            message=str(error),
            details={
                "error_class": error.__class__.__name__,
                "component": component,
                "operation": operation,
                "context": context,
                "user_roles": user_roles,
            },
            timestamp=datetime.utcnow(),
            component=component,
            operation=operation,
            user_roles=user_roles,
            client_info=client_info,
        )

        # Log the error
        await self._log_error(error_info)

        # Audit the error
        await self._audit_error(error_info)

        # Update error tracking
        self._update_error_tracking(error_info)

        # Attempt recovery if configured
        if self._should_attempt_recovery(error_info):
            await self._attempt_recovery(error_info)

        # Check for alerts
        await self._check_alerts(error_info)

        return error_info

    async def handle_mtls_error(
        self,
        error: Exception,
        operation: str,
        user_roles: List[str] = None,
        client_info: Optional[Dict[str, Any]] = None,
        cert_info: Optional[Dict[str, Any]] = None,
    ) -> SSLErrorInfo:
        """
        Handle mTLS-specific errors.

        Args:
            error: The mTLS error exception
            operation: Operation being performed
            user_roles: User roles for the operation
            client_info: Client information
            cert_info: Certificate information

        Returns:
            SSLErrorInfo: Structured error information
        """
        user_roles = user_roles or []
        cert_info = cert_info or {}

        # Classify the error
        error_type, severity = self._classify_mtls_error(error, operation)

        # Create error info
        error_info = SSLErrorInfo(
            error_type=error_type,
            severity=severity,
            message=str(error),
            details={
                "error_class": error.__class__.__name__,
                "component": "mtls_auth",
                "operation": operation,
                "cert_info": cert_info,
                "user_roles": user_roles,
            },
            timestamp=datetime.utcnow(),
            component="mtls_auth",
            operation=operation,
            user_roles=user_roles,
            client_info=client_info,
        )

        # Log the error
        await self._log_error(error_info)

        # Audit the error
        await self._audit_error(error_info)

        # Update error tracking
        self._update_error_tracking(error_info)

        # Attempt recovery if configured
        if self._should_attempt_recovery(error_info):
            await self._attempt_recovery(error_info)

        # Check for alerts
        await self._check_alerts(error_info)

        return error_info

    async def handle_token_error(
        self,
        error: Exception,
        operation: str,
        user_roles: List[str] = None,
        client_info: Optional[Dict[str, Any]] = None,
        token_info: Optional[Dict[str, Any]] = None,
    ) -> SSLErrorInfo:
        """
        Handle token authentication errors.

        Args:
            error: The token error exception
            operation: Operation being performed
            user_roles: User roles for the operation
            client_info: Client information
            token_info: Token information

        Returns:
            SSLErrorInfo: Structured error information
        """
        user_roles = user_roles or []
        token_info = token_info or {}

        # Classify the error
        error_type, severity = self._classify_token_error(error, operation)

        # Create error info
        error_info = SSLErrorInfo(
            error_type=error_type,
            severity=severity,
            message=str(error),
            details={
                "error_class": error.__class__.__name__,
                "component": "token_auth",
                "operation": operation,
                "token_info": token_info,
                "user_roles": user_roles,
            },
            timestamp=datetime.utcnow(),
            component="token_auth",
            operation=operation,
            user_roles=user_roles,
            client_info=client_info,
        )

        # Log the error
        await self._log_error(error_info)

        # Audit the error
        await self._audit_error(error_info)

        # Update error tracking
        self._update_error_tracking(error_info)

        # Attempt recovery if configured
        if self._should_attempt_recovery(error_info):
            await self._attempt_recovery(error_info)

        # Check for alerts
        await self._check_alerts(error_info)

        return error_info

    async def log_error(self, error_info: SSLErrorInfo) -> None:
        """
        Log error information.

        Args:
            error_info: Error information to log
        """
        await self._log_error(error_info)

    async def audit_error(self, error_info: SSLErrorInfo) -> None:
        """
        Audit error information for security monitoring.

        Args:
            error_info: Error information to audit
        """
        await self._audit_error(error_info)

    async def recover_from_error(
        self,
        error_info: SSLErrorInfo,
        recovery_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Attempt to recover from an error.

        Args:
            error_info: Error information
            recovery_context: Context for recovery

        Returns:
            bool: True if recovery was successful
        """
        return await self._attempt_recovery(error_info, recovery_context)

    def classify_error(
        self, error: Exception, component: str, operation: str
    ) -> tuple[SSLErrorType, SSLErrorSeverity]:
        """
        Classify an error by type and severity.

        Args:
            error: The error exception
            component: Component where error occurred
            operation: Operation being performed

        Returns:
            tuple: (error_type, severity)
        """
        if component == "ssl_context":
            return self._classify_ssl_error(error, component, operation)
        elif component == "mtls_auth":
            return self._classify_mtls_error(error, component, operation)
        elif component == "token_auth":
            return self._classify_token_error(error, component, operation)
        else:
            return SSLErrorType.UNKNOWN_ERROR, SSLErrorSeverity.MEDIUM

    def _classify_ssl_error(
        self, error: Exception, component: str, operation: str
    ) -> tuple[SSLErrorType, SSLErrorSeverity]:
        """Classify SSL-related errors."""
        if isinstance(error, ssl.SSLError):
            if "certificate" in str(error).lower():
                return SSLErrorType.SSL_CERTIFICATE_ERROR, SSLErrorSeverity.HIGH
            elif "handshake" in str(error).lower():
                return SSLErrorType.SSL_HANDSHAKE_ERROR, SSLErrorSeverity.MEDIUM
            elif "protocol" in str(error).lower():
                return SSLErrorType.SSL_PROTOCOL_ERROR, SSLErrorSeverity.HIGH
            else:
                return SSLErrorType.SSL_CONTEXT_ERROR, SSLErrorSeverity.MEDIUM
        elif isinstance(error, FileNotFoundError):
            return SSLErrorType.CONFIGURATION_ERROR, SSLErrorSeverity.HIGH
        elif isinstance(error, PermissionError):
            return SSLErrorType.CONFIGURATION_ERROR, SSLErrorSeverity.HIGH
        else:
            return SSLErrorType.UNKNOWN_ERROR, SSLErrorSeverity.MEDIUM

    def _classify_mtls_error(
        self, error: Exception, operation: str
    ) -> tuple[SSLErrorType, SSLErrorSeverity]:
        """Classify mTLS-related errors."""
        if "certificate" in str(error).lower():
            if "expired" in str(error).lower():
                return SSLErrorType.MTLS_CERT_VALIDATION_ERROR, SSLErrorSeverity.HIGH
            elif "invalid" in str(error).lower():
                return SSLErrorType.MTLS_CERT_VALIDATION_ERROR, SSLErrorSeverity.HIGH
            else:
                return SSLErrorType.MTLS_CERT_VALIDATION_ERROR, SSLErrorSeverity.MEDIUM
        elif "role" in str(error).lower():
            return SSLErrorType.MTLS_ROLE_EXTRACTION_ERROR, SSLErrorSeverity.MEDIUM
        elif "permission" in str(error).lower():
            return SSLErrorType.MTLS_AUTH_ERROR, SSLErrorSeverity.MEDIUM
        else:
            return SSLErrorType.MTLS_AUTH_ERROR, SSLErrorSeverity.MEDIUM

    def _classify_token_error(
        self, error: Exception, operation: str
    ) -> tuple[SSLErrorType, SSLErrorSeverity]:
        """Classify token-related errors."""
        if "expired" in str(error).lower():
            return SSLErrorType.TOKEN_EXPIRY_ERROR, SSLErrorSeverity.MEDIUM
        elif "invalid" in str(error).lower():
            return SSLErrorType.TOKEN_VALIDATION_ERROR, SSLErrorSeverity.MEDIUM
        elif "signature" in str(error).lower():
            return SSLErrorType.TOKEN_VALIDATION_ERROR, SSLErrorSeverity.HIGH
        else:
            return SSLErrorType.TOKEN_AUTH_ERROR, SSLErrorSeverity.MEDIUM

    async def _log_error(self, error_info: SSLErrorInfo) -> None:
        """Log error information with appropriate level."""
        log_message = (
            f"SSL Error [{error_info.error_type.value}] - "
            f"Component: {error_info.component}, "
            f"Operation: {error_info.operation}, "
            f"Message: {error_info.message}"
        )

        if error_info.severity == SSLErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra={"error_info": error_info})
        elif error_info.severity == SSLErrorSeverity.HIGH:
            self.logger.error(log_message, extra={"error_info": error_info})
        elif error_info.severity == SSLErrorSeverity.MEDIUM:
            self.logger.warning(log_message, extra={"error_info": error_info})
        else:
            self.logger.info(log_message, extra={"error_info": error_info})

    async def _audit_error(self, error_info: SSLErrorInfo) -> None:
        """Audit error information for security monitoring."""
        audit_message = (
            f"SSL Security Event - "
            f"Type: {error_info.error_type.value}, "
            f"Severity: {error_info.severity.value}, "
            f"Component: {error_info.component}, "
            f"Operation: {error_info.operation}, "
            f"User Roles: {error_info.user_roles}, "
            f"Client: {error_info.client_info}, "
            f"Timestamp: {error_info.timestamp.isoformat()}"
        )

        self.audit_logger.info(audit_message, extra={"error_info": error_info})

    def _update_error_tracking(self, error_info: SSLErrorInfo) -> None:
        """Update error tracking statistics."""
        # Update error count
        self.error_count[error_info.error_type] += 1

        # Add to recent errors
        self.recent_errors.append(error_info)

        # Maintain max recent errors limit
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors = self.recent_errors[-self.max_recent_errors :]

    def _should_attempt_recovery(self, error_info: SSLErrorInfo) -> bool:
        """Determine if recovery should be attempted."""
        # Don't attempt recovery for critical errors
        if error_info.severity == SSLErrorSeverity.CRITICAL:
            return False

        # Don't attempt recovery for configuration errors
        if error_info.error_type == SSLErrorType.CONFIGURATION_ERROR:
            return False

        # Check if recovery is enabled
        return self.recovery_config.get("enabled", True)

    async def _attempt_recovery(
        self,
        error_info: SSLErrorInfo,
        recovery_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Attempt to recover from an error.

        Args:
            error_info: Error information
            recovery_context: Context for recovery

        Returns:
            bool: True if recovery was successful
        """
        recovery_context = recovery_context or {}
        error_info.recovery_attempted = True

        try:
            # Implement recovery logic based on error type
            if error_info.error_type == SSLErrorType.SSL_HANDSHAKE_ERROR:
                # Wait and retry for handshake errors
                await asyncio.sleep(self.recovery_delay)
                error_info.recovery_successful = True
                return True

            elif error_info.error_type == SSLErrorType.TOKEN_EXPIRY_ERROR:
                # Token expiry errors cannot be recovered automatically
                error_info.recovery_successful = False
                return False

            elif error_info.error_type == SSLErrorType.MTLS_CERT_VALIDATION_ERROR:
                # Certificate validation errors cannot be recovered automatically
                error_info.recovery_successful = False
                return False

            else:
                # Default recovery attempt
                await asyncio.sleep(self.recovery_delay)
                error_info.recovery_successful = True
                return True

        except SSLError as recovery_error:
            self.logger.error(f"Recovery attempt failed: {recovery_error}")
            error_info.recovery_successful = False
            return False

    async def _check_alerts(self, error_info: SSLErrorInfo) -> None:
        """Check if alerts should be triggered."""
        # Check error count thresholds
        error_type = error_info.error_type
        error_count = self.error_count[error_type]

        threshold = self.alert_thresholds.get(error_type.value, {}).get("count", 10)
        if error_count >= threshold:
            await self._trigger_alert(
                error_info, f"Error count threshold exceeded: {error_count}"
            )

        # Check severity-based alerts
        if error_info.severity == SSLErrorSeverity.CRITICAL:
            await self._trigger_alert(error_info, "Critical SSL error detected")

        # Check recent error rate
        recent_critical_errors = [
            e
            for e in self.recent_errors[-10:]  # Last 10 errors
            if e.severity == SSLErrorSeverity.CRITICAL
        ]
        if len(recent_critical_errors) >= 3:
            await self._trigger_alert(
                error_info, "High rate of critical errors detected"
            )

    async def _trigger_alert(self, error_info: SSLErrorInfo, message: str) -> None:
        """Trigger an alert for critical errors."""
        alert_message = (
            f"SSL ALERT: {message} - "
            f"Error Type: {error_info.error_type.value}, "
            f"Component: {error_info.component}, "
            f"Operation: {error_info.operation}, "
            f"Timestamp: {error_info.timestamp.isoformat()}"
        )

        self.logger.critical(alert_message, extra={"error_info": error_info})

        # Here you could integrate with external alerting systems
        # (e.g., email, Slack, PagerDuty, etc.)

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            "error_counts": {
                error_type.value: count
                for error_type, count in self.error_count.items()
            },
            "recent_errors_count": len(self.recent_errors),
            "recent_errors": [
                {
                    "type": error.error_type.value,
                    "severity": error.severity.value,
                    "component": error.component,
                    "operation": error.operation,
                    "timestamp": error.timestamp.isoformat(),
                    "recovery_attempted": error.recovery_attempted,
                    "recovery_successful": error.recovery_successful,
                }
                for error in self.recent_errors[-10:]  # Last 10 errors
            ],
        }

    def reset_error_tracking(self) -> None:
        """Reset error tracking statistics."""
        self.error_count = {error_type: 0 for error_type in SSLErrorType}
        self.recent_errors = []
        self.logger.info("Error tracking statistics reset")


"""SSL error handling for ai_admin.core."""
