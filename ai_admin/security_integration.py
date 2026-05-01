from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, SSLError, ValidationError
"""
AI Admin Security Integration

This module provides integration with mcp_security_framework for comprehensive
security management including authentication, authorization, rate limiting,
and certificate management.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from mcp_security_framework import (
    SecurityManager,
    AuthManager,
    CertificateManager,
    PermissionManager,
    RateLimiter,
    SecurityConfig,
    AuthConfig,
    SSLConfig,
    PermissionConfig,
    RateLimitConfig
)
import logging
from ai_admin.settings_manager import get_settings_manager


class AISecurityIntegration:
    """
    AI Admin Security Integration class.
    
    This class provides integration with mcp_security_framework for:
    - Multi-method authentication (API keys, JWT, X.509 certificates)
    - Role-based authorization with permission management
    - Rate limiting for request throttling
    - SSL/TLS certificate management
    - Security event logging and monitoring
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize AI Security Integration.
        
        Args:
            config_path: Path to security configuration file
        """
        self.logger = logging.getLogger("ai_admin.security")
        self.settings_manager = get_settings_manager()
        self.config_path = config_path or "config/security.json"
        
        # Security components
        self.security_manager: Optional[SecurityManager] = None
        self.auth_manager: Optional[AuthManager] = None
        self.certificate_manager: Optional[CertificateManager] = None
        self.permission_manager: Optional[PermissionManager] = None
        self.rate_limiter: Optional[RateLimiter] = None
        
        # Initialize security components
        self._initialize_security()
    
    def _initialize_security(self) -> None:
        """Initialize security components with configuration."""
        try:
            # Load security configuration
            security_config = self._load_security_config()
            
            # Initialize SecurityManager
            self.security_manager = SecurityManager(security_config)
            self.logger.info("SecurityManager initialized successfully")
            
            # Initialize individual components
            self.auth_manager = self.security_manager.auth_manager
            self.certificate_manager = self.security_manager.certificate_manager
            self.permission_manager = self.security_manager.permission_manager
            self.rate_limiter = self.security_manager.rate_limiter
            
            self.logger.info("All security components initialized successfully")
            
        except CustomError as e:
            self.logger.error(f"Failed to initialize security components: {e}")
            raise
    
    def _load_security_config(self) -> SecurityConfig:
        """
        Load security configuration from file and settings.
        
        Returns:
            SecurityConfig object with loaded configuration
        """
        # Get settings from AI Admin settings manager
        settings = self.settings_manager.get_all_settings()
        
        # Load security configuration from file if exists
        if os.path.exists(self.config_path):
            import json
            with open(self.config_path, 'r') as f:
                file_config = json.load(f)
        else:
            file_config = {}
        
        # Merge settings and file configuration
        security_settings = settings.get("security", {})
        merged_config = {**security_settings, **file_config}
        
        # Create SecurityConfig with defaults
        auth_config = AuthConfig(
            enabled=merged_config.get("auth", {}).get("enabled", True),
            methods=merged_config.get("auth", {}).get("methods", ["api_key"]),
            api_keys=merged_config.get("auth", {}).get("api_keys", {}),
            jwt_secret=merged_config.get("auth", {}).get("jwt_secret", "default_secret"),
            jwt_algorithm=merged_config.get("auth", {}).get("jwt_algorithm", "HS256"),
            jwt_expiry_hours=merged_config.get("auth", {}).get("jwt_expiry_hours", 24)
        )
        
        # SSL configuration - only enable if certificates are provided
        ssl_enabled = merged_config.get("ssl", {}).get("enabled", False)
        ssl_cert_path = merged_config.get("ssl", {}).get("cert_path")
        ssl_key_path = merged_config.get("ssl", {}).get("key_path")
        
        # Disable SSL if certificates are not provided
        if ssl_enabled and (not ssl_cert_path or not ssl_key_path):
            ssl_enabled = False
        
        ssl_config = SSLConfig(
            enabled=ssl_enabled,
            cert_path=ssl_cert_path,
            key_path=ssl_key_path,
            ca_cert_path=merged_config.get("ssl", {}).get("ca_cert_path"),
            verify_peer=merged_config.get("ssl", {}).get("verify_peer", True),
            require_client_cert=merged_config.get("ssl", {}).get("require_client_cert", False)
        )
        
        permission_config = PermissionConfig(
            enabled=merged_config.get("permissions", {}).get("enabled", True),
            roles=merged_config.get("permissions", {}).get("roles", {}),
            default_role=merged_config.get("permissions", {}).get("default_role", "user")
        )
        
        rate_limit_config = RateLimitConfig(
            enabled=merged_config.get("rate_limit", {}).get("enabled", True),
            requests_per_minute=merged_config.get("rate_limit", {}).get("requests_per_minute", 60),
            burst_limit=merged_config.get("rate_limit", {}).get("burst_limit", 10)
        )
        
        return SecurityConfig(
            auth=auth_config,
            ssl=ssl_config,
            permissions=permission_config,
            rate_limit=rate_limit_config
        )
    
    def validate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate incoming request for authentication and authorization.
        
        Args:
            request_data: Request data containing authentication info and required permissions
            
        Returns:
            Validation result with access decision and user info
        """
        if not self.security_manager:
            return {
                "is_valid": False,
                "error": "Security manager not initialized",
                "user": None,
                "permissions": []
            }
        
        try:
            result = self.security_manager.validate_request(request_data)
            return {
                "is_valid": result.is_valid,
                "error": result.error_message if not result.is_valid else None,
                "user": result.user_info if hasattr(result, 'user_info') else None,
                "permissions": result.permissions if hasattr(result, 'permissions') else []
            }
        except ValidationError as e:
            self.logger.error(f"Request validation failed: {e}")
            return {
                "is_valid": False,
                "error": f"Validation error: {str(e)}",
                "user": None,
                "permissions": []
            }
    
    def check_rate_limit(self, client_id: str) -> Dict[str, Any]:
        """
        Check if client has exceeded rate limits.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            Rate limit check result
        """
        if not self.rate_limiter:
            return {
                "allowed": True,
                "remaining": 0,
                "reset_time": None
            }
        
        try:
            result = self.rate_limiter.check_limit(client_id)
            return {
                "allowed": result.allowed,
                "remaining": result.remaining,
                "reset_time": result.reset_time
            }
        except CustomError as e:
            self.logger.error(f"Rate limit check failed: {e}")
            return {
                "allowed": True,  # Allow on error
                "remaining": 0,
                "reset_time": None
            }
    
    def get_certificate_info(self, cert_path: str) -> Dict[str, Any]:
        """
        Get information about a certificate.
        
        Args:
            cert_path: Path to certificate file
            
        Returns:
            Certificate information
        """
        if not self.certificate_manager:
            return {
                "error": "Certificate manager not initialized"
            }
        
        try:
            cert_info = self.certificate_manager.get_certificate_info(cert_path)
            return {
                "subject": cert_info.subject,
                "issuer": cert_info.issuer,
                "valid_from": cert_info.valid_from,
                "valid_to": cert_info.valid_to,
                "serial_number": cert_info.serial_number,
                "fingerprint": cert_info.fingerprint
            }
        except SSLError as e:
            self.logger.error(f"Failed to get certificate info: {e}")
            return {
                "error": f"Certificate info error: {str(e)}"
            }
    
    def create_certificate(self, cert_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new certificate.
        
        Args:
            cert_config: Certificate configuration
            
        Returns:
            Certificate creation result
        """
        if not self.certificate_manager:
            return {
                "success": False,
                "error": "Certificate manager not initialized"
            }
        
        try:
            result = self.certificate_manager.create_certificate(cert_config)
            return {
                "success": True,
                "cert_path": result.cert_path,
                "key_path": result.key_path,
                "message": "Certificate created successfully"
            }
        except SSLError as e:
            self.logger.error(f"Failed to create certificate: {e}")
            return {
                "success": False,
                "error": f"Certificate creation error: {str(e)}"
            }
    
    def reload_configuration(self) -> bool:
        """
        Reload security configuration.
        
        Returns:
            True if reload was successful, False otherwise
        """
        try:
            self._initialize_security()
            self.logger.info("Security configuration reloaded successfully")
            return True
        except ConfigurationError as e:
            self.logger.error(f"Failed to reload security configuration: {e}")
            return False


# Global security integration instance
_security_integration: Optional[AISecurityIntegration] = None


def get_security_integration() -> AISecurityIntegration:
    """
    Get the global security integration instance.
    
    Returns:
        AISecurityIntegration instance
    """
    global _security_integration
    if _security_integration is None:
        _security_integration = AISecurityIntegration()
    return _security_integration


def initialize_security(config_path: Optional[str] = None) -> AISecurityIntegration:
    """
    Initialize security integration.
    
    Args:
        config_path: Path to security configuration file
        
    Returns:
        Initialized AISecurityIntegration instance
    """
    global _security_integration
    _security_integration = AISecurityIntegration(config_path)
    return _security_integration
