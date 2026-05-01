"""Hypercorn ASGI server configuration for AI Admin.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
from ai_admin.core.custom_exceptions import ConfigurationError, SSLError
"""Hypercorn configuration for AI Admin.

This module provides configuration management for Hypercorn ASGI server,
including SSL/mTLS setup, worker configuration, and logging setup.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import ssl
from typing import Dict, Any, Optional, List
from hypercorn.config import Config
from .server_exceptions import SSLServerConfigError


class HypercornConfig:
    """Hypercorn configuration manager for AI Admin."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        ssl_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Hypercorn configuration.

        Args:
            host: Server host
            port: Server port
            ssl_config: SSL configuration dictionary
        """
        self.host = host
        self.port = port
        self.ssl_config = ssl_config or {}

    def create_config(
        self,
        app_name: str = "AI Admin",
        workers: int = 1,
        worker_class: str = "asyncio",
        keep_alive_timeout: int = 5,
        max_incomplete_size: int = 16384,
        ssl_enabled: bool = False,
    ) -> Config:
        """
        Create Hypercorn configuration.

        Args:
            app_name: Application name
            workers: Number of worker processes
            worker_class: Worker class type
            keep_alive_timeout: Keep alive timeout
            max_incomplete_size: Maximum incomplete request size
            ssl_enabled: Whether SSL is enabled

        Returns:
            Hypercorn Config object

        Raises:
            SSLServerConfigError: If SSL configuration fails
        """
        config = Config()

        # Basic configuration
        config.bind = [f"{self.host}:{self.port}"]
        config.workers = workers
        config.worker_class = worker_class
        config.keep_alive_timeout = keep_alive_timeout
        config.max_incomplete_size = max_incomplete_size

        # Configure SSL if enabled
        if ssl_enabled and self.ssl_config:
            self.configure_ssl(config, self.ssl_config)

        # Configure workers
        self.configure_workers(config, workers, worker_class)

        # Configure logging
        self.configure_logging(config)

        return config

    def configure_ssl(self, config: Config, ssl_config: Dict[str, Any]) -> None:
        """
        Configure SSL settings for Hypercorn.

        Args:
            config: Hypercorn Config object
            ssl_config: SSL configuration dictionary

        Raises:
            SSLServerConfigError: If SSL configuration fails
        """
        try:
            # Validate SSL configuration
            validation_errors = self._validate_ssl_config(ssl_config)
            if validation_errors:
                raise SSLServerConfigError(
                    f"SSL configuration validation failed: "
                    f"{', '.join(validation_errors)}",
                    ssl_config=ssl_config,
                )

            # Create SSL context
            ssl_context = self.configure_ssl_context(ssl_config)
            config.ssl_context = ssl_context

            # Configure mTLS if enabled
            if ssl_config.get("verify_client", False) or ssl_config.get(
                "client_cert_required", False
            ):
                self.configure_mtls(config, ssl_config)

        except ConfigurationError as e:
            raise SSLServerConfigError(
                f"Failed to configure SSL: {e}", ssl_config=ssl_config
            ) from e

    def configure_ssl_context(self, ssl_config: Dict[str, Any]) -> ssl.SSLContext:
        """
        Create SSL context for Hypercorn.

        Args:
            ssl_config: SSL configuration dictionary

        Returns:
            SSL context object

        Raises:
            SSLServerConfigError: If SSL context creation fails
        """
        try:
            # Create SSL context
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

            # Load certificate and key
            cert_file = ssl_config.get("cert_file")
            key_file = ssl_config.get("key_file")

            if cert_file and key_file:
                ssl_context.load_cert_chain(cert_file, key_file)
            else:
                raise SSLServerConfigError(
                    "Certificate file and key file are required for SSL",
                    ssl_setting="cert_file/key_file",
                    ssl_config=ssl_config,
                )

            # Load CA certificate if provided
            ca_cert = ssl_config.get("ca_cert")
            if ca_cert:
                ssl_context.load_verify_locations(ca_cert)

            # Configure verification mode
            verify_mode = self._get_ssl_verify_mode(
                ssl_config.get("verify_client", False),
                ssl_config.get("client_cert_required", False),
            )
            ssl_context.verify_mode = verify_mode

            # Configure cipher suites
            cipher_suites = ssl_config.get("cipher_suites")
            if cipher_suites:
                self._configure_ssl_ciphers(ssl_context, cipher_suites)

            # Configure protocols
            min_tls_version = ssl_config.get("min_tls_version", "1.2")
            max_tls_version = ssl_config.get("max_tls_version", "1.3")
            self._configure_ssl_protocols(ssl_context, min_tls_version, max_tls_version)

            return ssl_context

        except ConfigurationError as e:
            raise SSLServerConfigError(
                f"Failed to create SSL context: {e}", ssl_config=ssl_config
            ) from e

    def configure_mtls(self, config: Config, ssl_config: Dict[str, Any]) -> None:
        """
        Configure mTLS settings for Hypercorn.

        Args:
            config: Hypercorn Config object
            ssl_config: SSL configuration dictionary

        Raises:
            SSLServerConfigError: If mTLS configuration fails
        """
        try:
            # Set client certificate verification
            if ssl_config.get("client_cert_required", False):
                config.ssl_context.verify_mode = ssl.CERT_REQUIRED
            elif ssl_config.get("verify_client", False):
                config.ssl_context.verify_mode = ssl.CERT_OPTIONAL

            # Set CA certificate for client verification
            ca_cert = ssl_config.get("ca_cert")
            if ca_cert and config.ssl_context:
                config.ssl_context.load_verify_locations(ca_cert)

        except SSLError as e:
            raise SSLServerConfigError(
                f"Failed to configure mTLS: {e}",
                ssl_setting="mtls",
                ssl_config=ssl_config,
            ) from e

    def configure_workers(
        self, config: Config, workers: int, worker_class: str
    ) -> None:
        """
        Configure worker settings for Hypercorn.

        Args:
            config: Hypercorn Config object
            workers: Number of workers
            worker_class: Worker class type
        """
        config.workers = workers
        config.worker_class = worker_class

        # Set worker-specific settings
        if worker_class == "asyncio":
            config.worker_connections = 1000
        elif worker_class == "uvloop":
            config.worker_connections = 1000
        elif worker_class == "trio":
            config.worker_connections = 100

    def configure_logging(
        self,
        config: Config,
        log_level: str = "info",
        access_log_format: str = '%(h)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"',
    ) -> None:
        """
        Configure logging for Hypercorn.

        Args:
            config: Hypercorn Config object
            log_level: Logging level
            access_log_format: Access log format
        """
        config.loglevel = log_level.upper()
        config.access_log_format = access_log_format
        config.accesslog = "-"  # Log to stdout
        config.errorlog = "-"  # Log to stderr

    def configure_cors(
        self, config: Config, cors_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Configure CORS settings for Hypercorn.

        Args:
            config: Hypercorn Config object
            cors_config: CORS configuration dictionary
        """
        if cors_config:
            # Note: Hypercorn doesn't have built-in CORS support
            # This would typically be handled by middleware
            pass

    def _validate_ssl_config(self, ssl_config: Dict[str, Any]) -> List[str]:
        """
        Validate SSL configuration.

        Args:
            ssl_config: SSL configuration dictionary

        Returns:
            List of validation error messages
        """
        errors = []

        # Check required fields
        if not ssl_config.get("cert_file"):
            errors.append("cert_file is required")

        if not ssl_config.get("key_file"):
            errors.append("key_file is required")

        # Validate certificate files
        cert_file = ssl_config.get("cert_file")
        key_file = ssl_config.get("key_file")
        ca_cert = ssl_config.get("ca_cert")

        if cert_file or key_file or ca_cert:
            file_errors = self._validate_certificate_files(cert_file, key_file, ca_cert)
            errors.extend(file_errors)

        # Validate TLS versions
        min_tls = ssl_config.get("min_tls_version", "1.2")
        max_tls = ssl_config.get("max_tls_version", "1.3")

        valid_versions = ["1.0", "1.1", "1.2", "1.3"]
        if min_tls not in valid_versions:
            errors.append(f"Invalid min_tls_version: {min_tls}")

        if max_tls not in valid_versions:
            errors.append(f"Invalid max_tls_version: {max_tls}")

        return errors

    def _validate_certificate_files(
        self,
        cert_file: Optional[str],
        key_file: Optional[str],
        ca_cert: Optional[str] = None,
    ) -> List[str]:
        """
        Validate certificate files.

        Args:
            cert_file: Certificate file path
            key_file: Private key file path
            ca_cert: CA certificate file path

        Returns:
            List of validation error messages
        """
        errors = []

        if cert_file and not os.path.exists(cert_file):
            errors.append(f"Certificate file not found: {cert_file}")

        if key_file and not os.path.exists(key_file):
            errors.append(f"Key file not found: {key_file}")

        if ca_cert and not os.path.exists(ca_cert):
            errors.append(f"CA certificate file not found: {ca_cert}")

        return errors

    def _get_ssl_verify_mode(
        self, verify_client: bool, client_cert_required: bool
    ) -> ssl.VerifyMode:
        """
        Get SSL verification mode.

        Args:
            verify_client: Whether to verify client certificates
            client_cert_required: Whether client certificates are required

        Returns:
            SSL verification mode
        """
        if client_cert_required:
            return ssl.CERT_REQUIRED
        elif verify_client:
            return ssl.CERT_OPTIONAL
        else:
            return ssl.CERT_NONE

    def _configure_ssl_ciphers(
        self, ssl_context: ssl.SSLContext, cipher_suites: Optional[List[str]] = None
    ) -> None:
        """
        Configure SSL cipher suites.

        Args:
            ssl_context: SSL context object
            cipher_suites: List of cipher suites
        """
        if cipher_suites:
            # Set cipher suites (this is a simplified implementation)
            # In practice, you would need to map cipher suite names to OpenSSL constants
            pass

    def _configure_ssl_protocols(
        self,
        ssl_context: ssl.SSLContext,
        min_tls_version: str = "1.2",
        max_tls_version: str = "1.3",
    ) -> None:
        """
        Configure SSL protocol versions.

        Args:
            ssl_context: SSL context object
            min_tls_version: Minimum TLS version
            max_tls_version: Maximum TLS version
        """
        # Configure minimum protocol version
        if min_tls_version == "1.2":
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        elif min_tls_version == "1.3":
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3

        # Configure maximum protocol version
        if max_tls_version == "1.2":
            ssl_context.maximum_version = ssl.TLSVersion.TLSv1_2
        elif max_tls_version == "1.3":
            ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3

    def _get_default_ssl_config(self) -> Dict[str, Any]:
        """
        Get default SSL configuration.

        Returns:
            Default SSL configuration dictionary
        """
        return {
            "enabled": False,
            "mode": "https_only",
            "cert_file": None,
            "key_file": None,
            "ca_cert": None,
            "verify_client": False,
            "client_cert_required": False,
            "min_tls_version": "1.2",
            "max_tls_version": "1.3",
            "cipher_suites": None,
        }

    def _merge_ssl_config(
        self, base_config: Dict[str, Any], override_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge SSL configurations.

        Args:
            base_config: Base SSL configuration
            override_config: Override SSL configuration

        Returns:
            Merged SSL configuration
        """
        merged = base_config.copy()
        merged.update(override_config)
        return merged
