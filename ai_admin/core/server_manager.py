"""Server manager for AI Admin.

Handles server lifecycle and process management.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
from ai_admin.core.custom_exceptions import AuthenticationError, ConfigurationError, CustomError
"""Server manager for AI Admin with SSL/mTLS support.

This module provides the ServerManager class for managing the AI Admin server
with support for various authentication modes and SSL/mTLS configuration.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import ssl
import atexit
import signal
import asyncio
from typing import Dict, Any, Optional

import hypercorn.asyncio
import hypercorn.config
from fastapi import FastAPI

from mcp_proxy_adapter.core.logging import setup_logging, get_logger
from mcp_proxy_adapter.config import config

from ai_admin.core.app_factory import AppFactory
from ai_admin.core.server_adapter import ServerAdapter
from ai_admin.config.ssl_config import SSLConfig
from ai_admin.config.roles_config import RolesConfig
from ai_admin.config.token_config import TokenConfig
from ai_admin.security_integration import initialize_security


class ServerManager:
    """Server manager for AI Admin with SSL/mTLS support."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize server manager.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.logger = logging.getLogger("ai_admin.server")
        self.app_factory: Optional[AppFactory] = None
        self.ssl_config: Optional[SSLConfig] = None
        self.roles_config: Optional[RolesConfig] = None
        self.token_config: Optional[TokenConfig] = None
        self.app: Optional[FastAPI] = None
        self.server_config: Dict[str, Any] = {}
        self.server_adapter: Optional[ServerAdapter] = None

    async def initialize(self) -> None:
        """Initialize server components."""
        self.logger.info("Initializing AI Admin server...")

        # Load configuration
        await self._load_configuration()

        # Initialize security components
        await self._initialize_security_components()

        # Setup hooks and dependency injection
        await self._setup_components()

        # Initialize commands
        await self._initialize_commands()

        # Create application using AppFactory
        await self._create_application()

        # Initialize server adapter
        await self._initialize_server_adapter()

        self.logger.info("Server initialization completed")

    async def _load_configuration(self) -> None:
        """Load configuration from file or environment."""
        try:
            if self.config_path and os.path.exists(self.config_path):
                config.load_from_file(self.config_path)
                self.logger.info(f"✅ Loaded configuration from: {self.config_path}")
            else:
                config_path = os.environ.get("CONFIG_PATH", "config/config.json")
                if os.path.exists(config_path):
                    config.load_from_file(config_path)
                    self.logger.info(f"✅ Loaded configuration from: {config_path}")
                else:
                    self.logger.warning(
                        f"⚠️ Configuration file not found: {config_path}"
                    )
                    self.logger.info("Using default configuration")

            # Setup logging
            setup_logging()
            self.logger.info("Logging configured")

        except ConfigurationError as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise

    async def _initialize_security_components(self) -> None:
        """Initialize security components."""
        try:
            # Initialize SSL configuration only if enabled
            ssl_config_data = config.get("ssl", {})
            if ssl_config_data and ssl_config_data.get("enabled", False):
                self.ssl_config = SSLConfig(ssl_config_data)
                self.logger.info("SSL configuration initialized")
            else:
                self.logger.info("SSL configuration disabled")

            # Initialize roles configuration
            roles_config_data = config.get("roles", {})
            if roles_config_data:
                self.roles_config = RolesConfig(roles_config_data)
                self.logger.info("Roles configuration initialized")

            # Initialize token configuration
            token_config_data = config.get("token", {})
            if token_config_data:
                self.token_config = TokenConfig(token_config_data)
                self.logger.info("Token configuration initialized")

            # Initialize security integration only if enabled
            security_config = config.get("security", {})
            if security_config and security_config.get("enabled", False):
                try:
                    initialize_security("config/security.json")
                    self.logger.info("Security integration initialized successfully")
                except CustomError as e:
                    self.logger.warning(
                        f"Failed to initialize security integration: {e}"
                    )
            else:
                self.logger.info("Security integration disabled")

        except CustomError as e:
            self.logger.error(f"Failed to initialize security components: {e}")
            raise

    async def _setup_components(self) -> None:
        """Setup hooks and dependency injection."""
        try:
            # Import here to avoid circular imports
            from ai_admin.core.server_setup import (
                setup_hooks,
                setup_proxy_registration,
                setup_dependency_injection,
            )

            # Setup hooks for command processing
            setup_hooks()

            # Setup proxy registration
            setup_proxy_registration()

            # Initialize dependency injection
            setup_dependency_injection()

            self.logger.info("Components setup completed")

        except CustomError as e:
            self.logger.error(f"Failed to setup components: {e}")
            raise

    async def _initialize_commands(self) -> None:
        """Initialize commands."""
        try:
            # Import here to avoid circular imports
            from ai_admin.core.server_setup import initialize_commands

            command_count = await initialize_commands()
            self.logger.info(f"Initialized {command_count} commands")

        except CustomError as e:
            self.logger.error(f"Failed to initialize commands: {e}")
            raise

    async def _create_application(self) -> None:
        """Create FastAPI application using AppFactory."""
        try:
            # Create AppFactory instance
            self.app_factory = AppFactory(
                config_path=self.config_path, settings_manager=None
            )

            # Determine authentication mode
            auth_mode = self._determine_auth_mode()
            
            # Create application with appropriate middleware based on auth mode
            self.app = await self.app_factory.create_app(
                app_name="AI Admin - Enhanced MCP Server",
                app_version="1.0.0",
                description=(
                    "AI Admin server with SSL/mTLS support and command autodiscovery"
                ),
                enable_ssl=(auth_mode in ["https_only", "mtls"]),
                enable_mtls=(auth_mode == "mtls"),
                enable_cors=True,
                enable_token_auth=(auth_mode == "token"),
            )

            self.logger.info("FastAPI application created successfully")

        except CustomError as e:
            self.logger.error(f"Failed to create application: {e}")
            raise

    async def _initialize_server_adapter(self) -> None:
        """Initialize server adapter for automatic server selection."""
        try:
            if self.app is None:
                raise RuntimeError("FastAPI application not initialized")
            
            # Prepare SSL configuration for adapter
            ssl_config = self._prepare_ssl_config_for_adapter()
            
            # Create server adapter
            self.server_adapter = ServerAdapter(
                app=self.app,
                ssl_config=ssl_config,
                prefer_hypercorn=True
            )
            
            self.logger.info("Server adapter initialized successfully")
            
        except CustomError as e:
            self.logger.error(f"Failed to initialize server adapter: {e}")
            raise

    def _prepare_ssl_config_for_adapter(self) -> Dict[str, Any]:
        """
        Prepare SSL configuration for server adapter.
        
        Returns:
            SSL configuration dictionary for adapter
        """
        try:
            ssl_config = {}
            
            # Get SSL configuration from multiple sources
            ssl_config_data = config.get("ssl", {})
            security_ssl_config = config.get("security.ssl", {})
            
            # Use security framework SSL config if available, otherwise use legacy
            if security_ssl_config.get("enabled", False):
                ssl_config = security_ssl_config
            else:
                ssl_config = ssl_config_data
            
            # Determine authentication mode
            auth_mode = self._determine_auth_mode()
            
            # Add mode-specific configuration
            if auth_mode == "mtls":
                ssl_config.update({
                    "verify_client": True,
                    "client_cert_required": True
                })
            elif auth_mode == "https_only":
                ssl_config.update({
                    "verify_client": False,
                    "client_cert_required": False
                })
            
            return ssl_config
            
        except ConfigurationError as e:
            self.logger.error(f"Failed to prepare SSL config for adapter: {e}")
            return {}

    def _determine_auth_mode(self) -> str:
        """
        Determine authentication mode based on configuration.

        Returns:
            Authentication mode: 'https_only', 'mtls', 'token', or 'none'
        """
        try:
            # Check SSL configuration
            ssl_enabled = config.get("ssl.enabled", False)
            security_ssl_enabled = config.get("security.ssl.enabled", False)

            if ssl_enabled or security_ssl_enabled:
                # Check for mTLS configuration
                verify_client = config.get("ssl.verify_client", False)
                security_verify_client = config.get("security.ssl.verify_client", False)

                if verify_client or security_verify_client:
                    # Check for roles configuration
                    roles_enabled = config.get("roles.enabled", False)
                    security_roles_enabled = config.get(
                        "security.permissions.enabled", False
                    )

                    if roles_enabled or security_roles_enabled:
                        return "mtls"
                    else:
                        return "https_only"
                else:
                    return "https_only"

            # Check token authentication
            token_enabled = config.get("token.enabled", False)
            security_token_enabled = config.get("security.auth.enabled", False)

            if token_enabled or security_token_enabled:
                return "token"

            return "none"

        except AuthenticationError as e:
            self.logger.warning(f"Failed to determine auth mode: {e}")
            return "none"

    def _prepare_server_config(self) -> Dict[str, Any]:
        """
        Prepare server configuration for hypercorn.

        Returns:
            Server configuration dictionary
        """
        try:
            # Get basic server settings
            host = config.get("server.host", "0.0.0.0")
            port = config.get("server.port", 8000)
            log_level = config.get("server.log_level", "info")
            debug = config.get("server.debug", False)

            server_config = {
                "host": host,
                "port": port,
                "log_level": log_level.lower(),
                "reload": debug,
            }

            # Determine authentication mode
            auth_mode = self._determine_auth_mode()
            self.logger.info(f"Authentication mode: {auth_mode}")

            # Add SSL configuration based on mode
            if auth_mode in ["https_only", "mtls"]:
                self._add_ssl_config(server_config, auth_mode)

            return server_config

        except ConfigurationError as e:
            self.logger.error(f"Failed to prepare server config: {e}")
            raise

    def _add_ssl_config(self, server_config: Dict[str, Any], auth_mode: str) -> None:
        """
        Add SSL configuration to server config.

        Args:
            server_config: Server configuration dictionary
            auth_mode: Authentication mode
        """
        try:
            # Get SSL configuration from multiple sources
            ssl_config_data = config.get("ssl", {})
            security_ssl_config = config.get("security.ssl", {})

            # Use security framework SSL config if available, otherwise use legacy
            if security_ssl_config.get("enabled", False):
                ssl_config = security_ssl_config
            else:
                ssl_config = ssl_config_data

            if ssl_config.get("enabled", False):
                cert_file = ssl_config.get("cert_file")
                key_file = ssl_config.get("key_file")
                ca_cert = ssl_config.get("ca_cert") or ssl_config.get("ca_cert_file")

                if cert_file and key_file:
                    server_config.update(
                        {
                            "ssl_enabled": True,
                            "ssl_cert_file": cert_file,
                            "ssl_key_file": key_file,
                            "ssl_ca_cert": ca_cert,
                            "ssl_verify_mode": (
                                "CERT_REQUIRED" if auth_mode == "mtls" else "CERT_NONE"
                            ),
                        }
                    )

                    self.logger.info(f"SSL configuration added for mode: {auth_mode}")
                    self.logger.info(f"Certificate: {cert_file}")
                    self.logger.info(f"Key: {key_file}")
                    if ca_cert:
                        self.logger.info(f"CA Certificate: {ca_cert}")

        except ConfigurationError as e:
            self.logger.error(f"Failed to add SSL config: {e}")
            raise

    async def run_server(self) -> None:
        """Run the server using server adapter for automatic server selection."""
        try:
            # Prepare server configuration
            self.server_config = self._prepare_server_config()

            # Print server information
            self._print_server_info()

            # Setup shutdown handlers
            self._setup_shutdown_handlers()

            # Use server adapter for automatic server selection
            if self.server_adapter is None:
                raise RuntimeError("Server adapter not initialized")
            
            # Run server using adapter
            await self.server_adapter.run_server(
                host=self.server_config['host'],
                port=self.server_config['port'],
                workers=1,  # Single worker for now
                reload=self.server_config.get('reload', False),
                log_level=self.server_config.get('log_level', 'info'),
                ssl_keyfile=self.server_config.get('ssl_key_file'),
                ssl_certfile=self.server_config.get('ssl_cert_file'),
                ssl_ca_certs=self.server_config.get('ssl_ca_cert'),
                ssl_verify_mode=self.server_config.get('ssl_verify_mode')
            )

        except KeyboardInterrupt:
            self.logger.info("🛑 Server stopped by user")
        except CustomError as e:
            self.logger.error(f"❌ Failed to start server: {e}")
            raise

    def _print_server_info(self) -> None:
        """Print server information."""
        print("=" * 80)
        print("🚀 AI ADMIN - ENHANCED MCP SERVER WITH SSL/mTLS")
        print("=" * 80)
        print(
            "📋 Description: AI Admin server with SSL/mTLS support and "
            "command autodiscovery"
        )
        print("🔧 Version: 1.0.0")
        print("⚙️  Configuration:")
        print(f"   • Server: {self.server_config['host']}:{self.server_config['port']}")
        print(f"   • Log Level: {self.server_config.get('log_level', 'info')}")
        print(f"   • Debug: {self.server_config.get('reload', False)}")

        # Print authentication mode
        auth_mode = self._determine_auth_mode()
        print(f"🔒 Authentication Mode: {auth_mode.upper()}")

        if auth_mode == "https_only":
            print("   • HTTPS only mode enabled")
        elif auth_mode == "mtls":
            print("   • mTLS with role-based authentication enabled")
        elif auth_mode == "token":
            print("   • Token authentication enabled")
        else:
            print("   • No authentication (HTTP mode)")

        # Print SSL information
        if self.server_config.get("ssl_enabled", False):
            print("🔐 SSL Configuration:")
            print(f"   • Certificate: {self.server_config.get('ssl_cert_file', 'N/A')}")
            print(f"   • Key: {self.server_config.get('ssl_key_file', 'N/A')}")
            if self.server_config.get("ssl_ca_cert"):
                print(f"   • CA Certificate: {self.server_config.get('ssl_ca_cert')}")
            print(
                f"   • Verification: "
                f"{self.server_config.get('ssl_verify_mode', 'CERT_NONE')}"
            )

        print("🎯 Enhanced Features:")
        print("   • Advanced JSON-RPC API")
        print("   • Automatic command discovery")
        print("   • SSL/mTLS support")
        print("   • Role-based authentication")
        print("   • Token authentication")
        print("   • Configuration validation")
        print("   • Automatic mode detection")
        print("   • Hypercorn server engine")
        print("=" * 80)

    def _setup_shutdown_handlers(self) -> None:
        """Setup shutdown handlers."""

        def shutdown_handler():
            """Handle server shutdown and cleanup."""
            logger = logging.getLogger("ai_admin.server")
            logger.info("Shutting down AI Admin server...")

            # Unregister from proxy if enabled
            try:
                proxy_config = config.get("proxy_registration", {})
                if proxy_config.get("enabled", False) and proxy_config.get(
                    "auto_unregister_on_shutdown", False
                ):
                    asyncio.run(unregister_from_proxy(proxy_config))
            except CustomError as e:
                logger.warning(f"Error during proxy unregistration on shutdown: {e}")

            logger.info("AI Admin server shutdown complete")

        # Register shutdown handlers
        atexit.register(shutdown_handler)

        def signal_handler(sig, frame):
            """Handle system signals."""
            shutdown_handler()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def unregister_from_proxy(proxy_config):
    """Unregister AI Admin server from proxy server."""
    logger = logging.getLogger("ai_admin")

    try:
        # Import here to avoid circular imports
        from ai_admin.core.server_setup import ProxyRegistrationCommand

        # Create proxy registration command instance
        proxy_cmd = ProxyRegistrationCommand()

        # Prepare unregistration data
        unregistration_data = {
            "action": "unregister",
            "server_url": proxy_config.get("server_url", "http://127.0.0.1:3004/proxy"),
            "auth_method": proxy_config.get("auth_method", "token"),
            "token": proxy_config.get("token", "ai_admin_proxy_token_123"),
            "proxy_info": proxy_config.get("proxy_info", {}),
        }

        # Execute unregistration
        result = await proxy_cmd.execute(**unregistration_data)

        if hasattr(result, "success") and result.success:
            logger.info("Successfully unregistered from proxy server")
        else:
            logger.warning(f"Failed to unregister from proxy server: {result}")

    except CustomError as e:
        logger.error(f"Error during proxy unregistration: {e}")
