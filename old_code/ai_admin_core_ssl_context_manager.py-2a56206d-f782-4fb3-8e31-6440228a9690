"""SSL Context Manager for AI Admin Server.

This module provides SSL context management functionality for the AI Admin server,
including creation, configuration, and validation of SSL contexts for different
authentication modes (HTTPS, mTLS, Token Auth, Mixed).

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import ssl
import os
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass
from ai_admin.core.custom_exceptions import SSLError

import logging

from ..config.ssl_config import SSLConfig, SecurityParams, CertificatePaths
from .ssl_error_handler import SSLErrorHandler


class SSLContextType(Enum):
    """Types of SSL contexts supported by the manager."""

    HTTPS = "https"
    MTLS = "mtls"
    TOKEN_AUTH = "token_auth"
    MIXED = "mixed"


@dataclass
class SSLContextInfo:
    """Information about an SSL context."""

    context_type: SSLContextType
    ssl_context: ssl.SSLContext
    certificate_paths: CertificatePaths
    security_params: SecurityParams
    created_at: str
    is_valid: bool
    validation_errors: List[str]


class SSLContextManager:
    """
    Manager for SSL contexts in AI Admin server.

    This class provides comprehensive SSL context management including:
    - Creation of SSL contexts for different authentication modes
    - Configuration of security parameters
    - Integration with certificates
    - Validation of SSL contexts
    - Support for various server types (Hypercorn, Uvicorn)
    """

    def __init__(
        self,
        ssl_config: Optional[SSLConfig] = None,
        error_handler: Optional[SSLErrorHandler] = None,
    ):
        """
        Initialize SSL context manager.

        Args:
            ssl_config: SSL configuration instance. If None, creates default config.
            error_handler: SSL error handler for comprehensive error management
        """
        self.logger = logging.getLogger("ai_admin.ssl_context_manager")
        self.ssl_config = ssl_config or SSLConfig()
        self.error_handler = error_handler or SSLErrorHandler()
        self._contexts: Dict[SSLContextType, SSLContextInfo] = {}
        self._default_context_type: Optional[SSLContextType] = None

        self.logger.info("SSL context manager initialized")

    async def create_ssl_context(
        self, context_type: SSLContextType, force_recreate: bool = False
    ) -> Optional[ssl.SSLContext]:
        """
        Create SSL context for specified type.

        Args:
            context_type: Type of SSL context to create
            force_recreate: Whether to force recreation of existing context

        Returns:
            SSL context if created successfully, None otherwise

        Raises:
            ValueError: If SSL configuration is invalid
            FileNotFoundError: If certificate files are not found
            ssl.SSLError: If SSL context creation fails
        """
        try:
            # Check if context already exists
            if context_type in self._contexts and not force_recreate:
                self.logger.info(f"SSL context {context_type.value} already exists")
                return self._contexts[context_type].ssl_context

            self.logger.info(f"Creating SSL context for {context_type.value}")

            # Get certificate paths and security parameters
            cert_paths = self.ssl_config.get_certificate_paths()
            security_params = self.ssl_config.get_security_params()

            # Create SSL context based on type
            if context_type == SSLContextType.HTTPS:
                ssl_context = await self._create_https_context(
                    cert_paths, security_params
                )
            elif context_type == SSLContextType.MTLS:
                ssl_context = await self._create_mtls_context(
                    cert_paths, security_params
                )
            elif context_type == SSLContextType.TOKEN_AUTH:
                ssl_context = await self._create_token_auth_context(
                    cert_paths, security_params
                )
            elif context_type == SSLContextType.MIXED:
                ssl_context = await self._create_mixed_context(
                    cert_paths, security_params
                )
            else:
                raise ValueError(f"Unsupported SSL context type: {context_type}")

            # Validate the created context
            is_valid, validation_errors = await self._validate_ssl_context(
                ssl_context, context_type
            )

            # Store context information
            from datetime import datetime

            context_info = SSLContextInfo(
                context_type=context_type,
                ssl_context=ssl_context,
                certificate_paths=cert_paths,
                security_params=security_params,
                created_at=datetime.utcnow().isoformat(),
                is_valid=is_valid,
                validation_errors=validation_errors,
            )

            self._contexts[context_type] = context_info

            if is_valid:
                self.logger.info(
                    f"SSL context {context_type.value} created successfully"
                )
                return ssl_context
            else:
                self.logger.warning(
                    f"SSL context {context_type.value} created with validation errors: "
                    f"{', '.join(validation_errors)}"
                )
            return ssl_context

        except SSLError as e:
            self.logger.error(f"Failed to create SSL context {context_type.value}: {e}")

            # Handle error through error handler
            await self.error_handler.handle_ssl_error(
                error=e,
                component="ssl_context",
                operation=f"create_{context_type.value}",
                user_roles=[],
                context={"context_type": context_type.value},
            )
            raise

    async def _create_https_context(
        self, cert_paths: CertificatePaths, security_params: SecurityParams
    ) -> ssl.SSLContext:
        """
        Create HTTPS SSL context.

        Args:
            cert_paths: Certificate paths configuration
            security_params: Security parameters configuration

        Returns:
            Configured SSL context for HTTPS

        Raises:
            FileNotFoundError: If certificate files are not found
            ssl.SSLError: If SSL context creation fails
        """
        try:
            # Create SSL context with proper settings
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            
            # Set verify_mode before check_hostname to avoid conflicts
            if security_params.verify_mode == "CERT_NONE":
                ssl_context.verify_mode = ssl.CERT_NONE
                ssl_context.check_hostname = False
            elif security_params.verify_mode == "CERT_OPTIONAL":
                ssl_context.verify_mode = ssl.CERT_OPTIONAL
                ssl_context.check_hostname = security_params.check_hostname
            elif security_params.verify_mode == "CERT_REQUIRED":
                ssl_context.verify_mode = ssl.CERT_REQUIRED
                ssl_context.check_hostname = security_params.check_hostname
            else:
                ssl_context.check_hostname = security_params.check_hostname

            # Configure security parameters
            await self._configure_security_params(ssl_context, security_params)

            # Load server certificate and key
            if cert_paths.server_cert and cert_paths.server_key:
                if not os.path.exists(cert_paths.server_cert):
                    raise FileNotFoundError(
                        f"Server certificate not found: {cert_paths.server_cert}"
                    )
                if not os.path.exists(cert_paths.server_key):
                    raise FileNotFoundError(
                        f"Server key not found: {cert_paths.server_key}"
                    )

                ssl_context.load_cert_chain(
                    cert_paths.server_cert, cert_paths.server_key
                )
                self.logger.info("Server certificate and key loaded for HTTPS context")

            # Configure for server use
            ssl_context.verify_mode = ssl.CERT_NONE
            ssl_context.check_hostname = False

            return ssl_context

        except SSLError as e:
            self.logger.error(f"Failed to create HTTPS context: {e}")

            # Handle error through error handler
            await self.error_handler.handle_ssl_error(
                error=e,
                component="ssl_context",
                operation="create_https",
                user_roles=[],
                context={"cert_paths": cert_paths.__dict__ if cert_paths else None},
            )
            raise

    async def _create_mtls_context(
        self, cert_paths: CertificatePaths, security_params: SecurityParams
    ) -> ssl.SSLContext:
        """
        Create mTLS SSL context.

        Args:
            cert_paths: Certificate paths configuration
            security_params: Security parameters configuration

        Returns:
            Configured SSL context for mTLS

        Raises:
            FileNotFoundError: If certificate files are not found
            ssl.SSLError: If SSL context creation fails
        """
        try:
            # Create SSL context with proper settings
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            
            # Set check_hostname first to avoid conflicts with verify_mode
            ssl_context.check_hostname = security_params.check_hostname
            
            # Set verify_mode after check_hostname
            if security_params.verify_mode == "CERT_NONE":
                ssl_context.verify_mode = ssl.CERT_NONE
            elif security_params.verify_mode == "CERT_OPTIONAL":
                ssl_context.verify_mode = ssl.CERT_OPTIONAL
            elif security_params.verify_mode == "CERT_REQUIRED":
                ssl_context.verify_mode = ssl.CERT_REQUIRED

            # Configure security parameters
            await self._configure_security_params(ssl_context, security_params)

            # Load server certificate and key
            if cert_paths.server_cert and cert_paths.server_key:
                if not os.path.exists(cert_paths.server_cert):
                    raise FileNotFoundError(
                        f"Server certificate not found: {cert_paths.server_cert}"
                    )
                if not os.path.exists(cert_paths.server_key):
                    raise FileNotFoundError(
                        f"Server key not found: {cert_paths.server_key}"
                    )

                ssl_context.load_cert_chain(
                    cert_paths.server_cert, cert_paths.server_key
                )
                self.logger.info("Server certificate and key loaded for mTLS context")

            # Load CA certificate for client verification
            if cert_paths.ca_cert:
                if not os.path.exists(cert_paths.ca_cert):
                    raise FileNotFoundError(
                        f"CA certificate not found: {cert_paths.ca_cert}"
                    )

                ssl_context.load_verify_locations(cert_paths.ca_cert)
                self.logger.info("CA certificate loaded for mTLS context")

            # Configure for mutual TLS
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.check_hostname = security_params.check_hostname

            return ssl_context

        except SSLError as e:
            self.logger.error(f"Failed to create mTLS context: {e}")

            # Handle error through error handler
            await self.error_handler.handle_ssl_error(
                error=e,
                component="ssl_context",
                operation="create_mtls",
                user_roles=[],
                context={"cert_paths": cert_paths.__dict__ if cert_paths else None},
            )
            raise

    async def _create_token_auth_context(
        self, cert_paths: CertificatePaths, security_params: SecurityParams
    ) -> ssl.SSLContext:
        """
        Create token authentication SSL context.

        Args:
            cert_paths: Certificate paths configuration
            security_params: Security parameters configuration

        Returns:
            Configured SSL context for token authentication

        Raises:
            FileNotFoundError: If certificate files are not found
            ssl.SSLError: If SSL context creation fails
        """
        try:
            # Create SSL context (similar to HTTPS but with token auth considerations)
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            
            # Set check_hostname first to avoid conflicts with verify_mode
            ssl_context.check_hostname = security_params.check_hostname
            
            # Set verify_mode after check_hostname
            if security_params.verify_mode == "CERT_NONE":
                ssl_context.verify_mode = ssl.CERT_NONE
            elif security_params.verify_mode == "CERT_OPTIONAL":
                ssl_context.verify_mode = ssl.CERT_OPTIONAL
            elif security_params.verify_mode == "CERT_REQUIRED":
                ssl_context.verify_mode = ssl.CERT_REQUIRED

            # Configure security parameters
            await self._configure_security_params(ssl_context, security_params)

            # Load server certificate and key
            if cert_paths.server_cert and cert_paths.server_key:
                if not os.path.exists(cert_paths.server_cert):
                    raise FileNotFoundError(
                        f"Server certificate not found: {cert_paths.server_cert}"
                    )
                if not os.path.exists(cert_paths.server_key):
                    raise FileNotFoundError(
                        f"Server key not found: {cert_paths.server_key}"
                    )

                ssl_context.load_cert_chain(
                    cert_paths.server_cert, cert_paths.server_key
                )
                self.logger.info(
                    "Server certificate and key loaded for token auth context"
                )

            # Configure for server use with token authentication
            ssl_context.verify_mode = ssl.CERT_NONE
            ssl_context.check_hostname = False

            return ssl_context

        except SSLError as e:
            self.logger.error(f"Failed to create token auth context: {e}")

            # Handle error through error handler
            await self.error_handler.handle_ssl_error(
                error=e,
                component="ssl_context",
                operation="create_token_auth",
                user_roles=[],
                context={"cert_paths": cert_paths.__dict__ if cert_paths else None},
            )
            raise

    async def _create_mixed_context(
        self, cert_paths: CertificatePaths, security_params: SecurityParams
    ) -> ssl.SSLContext:
        """
        Create mixed authentication SSL context.

        Args:
            cert_paths: Certificate paths configuration
            security_params: Security parameters configuration

        Returns:
            Configured SSL context for mixed authentication

        Raises:
            FileNotFoundError: If certificate files are not found
            ssl.SSLError: If SSL context creation fails
        """
        try:
            # Create SSL context (supports both mTLS and token auth)
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            
            # Set check_hostname first to avoid conflicts with verify_mode
            ssl_context.check_hostname = security_params.check_hostname
            
            # Set verify_mode after check_hostname
            if security_params.verify_mode == "CERT_NONE":
                ssl_context.verify_mode = ssl.CERT_NONE
            elif security_params.verify_mode == "CERT_OPTIONAL":
                ssl_context.verify_mode = ssl.CERT_OPTIONAL
            elif security_params.verify_mode == "CERT_REQUIRED":
                ssl_context.verify_mode = ssl.CERT_REQUIRED

            # Configure security parameters
            await self._configure_security_params(ssl_context, security_params)

            # Load server certificate and key
            if cert_paths.server_cert and cert_paths.server_key:
                if not os.path.exists(cert_paths.server_cert):
                    raise FileNotFoundError(
                        f"Server certificate not found: {cert_paths.server_cert}"
                    )
                if not os.path.exists(cert_paths.server_key):
                    raise FileNotFoundError(
                        f"Server key not found: {cert_paths.server_key}"
                    )

                ssl_context.load_cert_chain(
                    cert_paths.server_cert, cert_paths.server_key
                )
                self.logger.info("Server certificate and key loaded for mixed context")

            # Load CA certificate for client verification (optional for mixed mode)
            if cert_paths.ca_cert:
                if not os.path.exists(cert_paths.ca_cert):
                    raise FileNotFoundError(
                        f"CA certificate not found: {cert_paths.ca_cert}"
                    )

                ssl_context.load_verify_locations(cert_paths.ca_cert)
                self.logger.info("CA certificate loaded for mixed context")

            # Configure for mixed authentication (flexible verification)
            ssl_context.verify_mode = ssl.CERT_OPTIONAL
            ssl_context.check_hostname = security_params.check_hostname

            return ssl_context

        except SSLError as e:
            self.logger.error(f"Failed to create mixed context: {e}")

            # Handle error through error handler
            await self.error_handler.handle_ssl_error(
                error=e,
                component="ssl_context",
                operation="create_mixed",
                user_roles=[],
                context={"cert_paths": cert_paths.__dict__ if cert_paths else None},
            )
            raise

    async def _configure_security_params(
        self, ssl_context: ssl.SSLContext, security_params: SecurityParams
    ) -> None:
        """
        Configure security parameters for SSL context.

        Args:
            ssl_context: SSL context to configure
            security_params: Security parameters to apply
        """
        try:
            # Set minimum TLS version
            if security_params.min_tls_version == "TLSv1.2":
                ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            elif security_params.min_tls_version == "TLSv1.3":
                ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
            else:
                ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

            # Set maximum TLS version if specified
            if security_params.max_tls_version:
                if security_params.max_tls_version == "TLSv1.2":
                    ssl_context.maximum_version = ssl.TLSVersion.TLSv1_2
                elif security_params.max_tls_version == "TLSv1.3":
                    ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3

            # Configure cipher suites if specified
            if security_params.cipher_suite:
                # Note: cipher suite configuration is complex and depends on the
                # specific suite. For now, we'll use the default cipher suites
                self.logger.info(
                    f"Cipher suite specified: {security_params.cipher_suite}"
                )

            # Verification mode already set in context creation

            self.logger.info("Security parameters configured for SSL context")

        except SSLError as e:
            self.logger.error(f"Failed to configure security parameters: {e}")

            # Handle error through error handler
            await self.error_handler.handle_ssl_error(
                error=e,
                component="ssl_context",
                operation="configure_security_params",
                user_roles=[],
                context={
                    "security_params": (
                        security_params.__dict__ if security_params else None
                    )
                },
            )
            raise

    async def _validate_ssl_context(
        self, ssl_context: ssl.SSLContext, context_type: SSLContextType
    ) -> Tuple[bool, List[str]]:
        """
        Validate SSL context.

        Args:
            ssl_context: SSL context to validate
            context_type: Type of SSL context

        Returns:
            Tuple of (is_valid, validation_errors)
        """
        validation_errors = []

        try:
            # Basic validation checks
            if ssl_context is None:
                validation_errors.append("SSL context is None")
                return False, validation_errors

            # Check if context has required attributes
            required_attrs = ["minimum_version", "verify_mode", "check_hostname"]
            for attr in required_attrs:
                if not hasattr(ssl_context, attr):
                    validation_errors.append(
                        f"SSL context missing required attribute: {attr}"
                    )

            # Validate certificate files if they should be loaded
            cert_paths = self.ssl_config.get_certificate_paths()
            if cert_paths.server_cert and not os.path.exists(cert_paths.server_cert):
                validation_errors.append(
                    f"Server certificate file not found: {cert_paths.server_cert}"
                )

            if cert_paths.server_key and not os.path.exists(cert_paths.server_key):
                validation_errors.append(
                    f"Server key file not found: {cert_paths.server_key}"
                )

            # Context-specific validation
            if context_type == SSLContextType.MTLS:
                if cert_paths.ca_cert and not os.path.exists(cert_paths.ca_cert):
                    validation_errors.append(
                        f"CA certificate file not found: {cert_paths.ca_cert}"
                    )

            # Check TLS version compatibility
            try:
                min_version = ssl_context.minimum_version
                if min_version and min_version < ssl.TLSVersion.TLSv1_2:
                    validation_errors.append(
                        "TLS version below 1.2 is not recommended for security"
                    )
            except SSLError as e:
                validation_errors.append(f"Failed to validate TLS version: {e}")

            is_valid = len(validation_errors) == 0
            return is_valid, validation_errors

        except SSLError as e:
            validation_errors.append(f"SSL context validation failed: {e}")

            # Handle error through error handler
            await self.error_handler.handle_ssl_error(
                error=e,
                component="ssl_context",
                operation="validate_ssl_context",
                user_roles=[],
                context={"context_type": context_type.value},
            )
            return False, validation_errors

    async def get_ssl_context(
        self, context_type: SSLContextType
    ) -> Optional[ssl.SSLContext]:
        """
        Get SSL context for specified type.

        Args:
            context_type: Type of SSL context to retrieve

        Returns:
            SSL context if available, None otherwise
        """
        if context_type in self._contexts:
            context_info = self._contexts[context_type]
            if context_info.is_valid:
                return context_info.ssl_context
            else:
                self.logger.warning(
                    f"SSL context {context_type.value} has validation errors: "
                    f"{', '.join(context_info.validation_errors)}"
                )
                return context_info.ssl_context
        else:
            self.logger.warning(f"SSL context {context_type.value} not found")
            return None

    async def get_context_summary(self) -> Dict[str, Any]:
        """
        Get summary of all SSL contexts.

        Returns:
            Dictionary containing context summary information
        """
        summary = {
            "total_contexts": len(self._contexts),
            "contexts": {},
            "default_context_type": (
                self._default_context_type.value if self._default_context_type else None
            ),
        }

        for context_type, context_info in self._contexts.items():
            summary["contexts"][context_type.value] = {
                "created_at": context_info.created_at,
                "is_valid": context_info.is_valid,
                "validation_errors": context_info.validation_errors,
                "certificate_paths": {
                    "server_cert": context_info.certificate_paths.server_cert,
                    "server_key": context_info.certificate_paths.server_key,
                    "ca_cert": context_info.certificate_paths.ca_cert,
                },
                "security_params": {
                    "min_tls_version": context_info.security_params.min_tls_version,
                    "max_tls_version": context_info.security_params.max_tls_version,
                    "verify_mode": context_info.security_params.verify_mode,
                    "check_hostname": context_info.security_params.check_hostname,
                },
            }

        return summary

    async def clear_context(self, context_type: SSLContextType) -> None:
        """
        Clear SSL context for specified type.

        Args:
            context_type: Type of SSL context to clear
        """
        if context_type in self._contexts:
            del self._contexts[context_type]
            self.logger.info(f"SSL context {context_type.value} cleared")
        else:
            self.logger.warning(
                f"SSL context {context_type.value} not found for clearing"
            )

    async def clear_all_contexts(self) -> None:
        """Clear all SSL contexts."""
        self._contexts.clear()
        self._default_context_type = None
        self.logger.info("All SSL contexts cleared")

    async def recreate_context(
        self, context_type: SSLContextType
    ) -> Optional[ssl.SSLContext]:
        """
        Recreate SSL context for specified type.

        Args:
            context_type: Type of SSL context to recreate

        Returns:
            New SSL context if created successfully, None otherwise
        """
        try:
            # Clear existing context
            await self.clear_context(context_type)

            # Create new context
            return await self.create_ssl_context(context_type, force_recreate=True)

        except SSLError as e:
            self.logger.error(
                f"Failed to recreate SSL context {context_type.value}: {e}"
            )

            # Handle error through error handler
            await self.error_handler.handle_ssl_error(
                error=e,
                component="ssl_context",
                operation="recreate_context",
                user_roles=[],
                context={"context_type": context_type.value},
            )
            return None

    async def validate_all_contexts(self) -> Dict[str, Any]:
        """
        Validate all existing SSL contexts.

        Returns:
            Dictionary containing validation results for all contexts
        """
        validation_results = {
            "total_contexts": len(self._contexts),
            "valid_contexts": 0,
            "invalid_contexts": 0,
            "contexts": {},
        }

        for context_type, context_info in self._contexts.items():
            is_valid, validation_errors = await self._validate_ssl_context(
                context_info.ssl_context, context_type
            )

            validation_results["contexts"][context_type.value] = {
                "is_valid": is_valid,
                "validation_errors": validation_errors,
            }

            if is_valid:
                validation_results["valid_contexts"] += 1
            else:
                validation_results["invalid_contexts"] += 1

        return validation_results

    def get_available_context_types(self) -> List[SSLContextType]:
        """
        Get list of available SSL context types.

        Returns:
            List of available SSL context types
        """
        return list(self._contexts.keys())

    def is_context_available(self, context_type: SSLContextType) -> bool:
        """
        Check if SSL context is available for specified type.

        Args:
            context_type: Type of SSL context to check

        Returns:
            True if context is available and valid, False otherwise
        """
        if context_type not in self._contexts:
            return False

        context_info = self._contexts[context_type]
        return context_info.is_valid

    async def get_server_ssl_config(
        self, context_type: SSLContextType
    ) -> Dict[str, Any]:
        """
        Get server SSL configuration for specified context type.

        Args:
            context_type: Type of SSL context

        Returns:
            Dictionary containing server SSL configuration
        """
        if context_type not in self._contexts:
            return {}

        context_info = self._contexts[context_type]
        cert_paths = context_info.certificate_paths

        config = {
            "ssl_context": context_info.ssl_context,
            "cert_file": cert_paths.server_cert,
            "key_file": cert_paths.server_key,
            "ca_cert": cert_paths.ca_cert,
            "verify_mode": context_info.security_params.verify_mode,
            "check_hostname": context_info.security_params.check_hostname,
            "min_tls_version": context_info.security_params.min_tls_version,
            "max_tls_version": context_info.security_params.max_tls_version,
        }

        return config
