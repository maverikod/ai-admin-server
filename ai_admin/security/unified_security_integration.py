from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, PermissionError, ValidationError
"""Unified Security Integration for AI Admin.

This module provides a unified approach to integrating security components
with all commands, ensuring consistent security implementation across the system.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

import logging
from ai_admin.settings_manager import get_settings_manager
from ai_admin.config.roles_config import RolesConfig

from .base_security_adapter import SecurityAdapter
from .roles_manager import RolesManager
from .security_monitor import SecurityMonitor
from .security_metrics import SecurityMetrics


class UnifiedSecurityIntegration:
    """Unified security integration for all commands.

    This class provides:
    - Centralized security configuration management
    - Automatic security adapter selection
    - Unified security validation and auditing
    - Consistent error handling and reporting
    - Security monitoring and metrics collection
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize Unified Security Integration.

        Args:
            config_path: Path to unified security configuration
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig()
        self.logger = logging.getLogger("ai_admin.unified_security")

        # Load unified security configuration
        self.config = self._load_security_config(config_path)

        # Initialize security components
        self.roles_manager = RolesManager(self.config, self.roles_config)
        self.security_monitor = SecurityMonitor(self.settings_manager)
        self.security_metrics = SecurityMetrics(self.settings_manager)

        # Security adapter registry
        self.security_adapters = {}
        self._initialize_security_adapters()

    def _load_security_config(
        self, config_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load unified security configuration.

        Args:
            config_path: Path to configuration file

        Returns:
            Security configuration dictionary
        """
        try:
            if not config_path:
                config_path = "config/unified_security_config.json"

            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                self.logger.info(
                    f"Loaded unified security configuration from {config_path}"
                )
                return config.get("security", {})
            else:
                self.logger.warning(
                    f"Security configuration file {config_path} not found, using defaults"
                )
                return self._get_default_config()

        except ConfigurationError as e:
            self.logger.error(f"Error loading security configuration: {str(e)}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default security configuration.

        Returns:
            Default security configuration
        """
        return {
            "enabled": True,
            "framework": "mcp-security-framework",
            "global_settings": {
                "audit_enabled": True,
                "monitoring_enabled": True,
                "metrics_enabled": True,
                "rate_limiting_enabled": True,
                "ssl_verification_enabled": True,
                "certificate_validation_enabled": True,
                "role_hierarchy_enabled": True,
                "anomaly_detection_enabled": True,
            },
            "adapters": {},
            "role_hierarchy": {},
            "monitoring": {
                "enabled": True,
                "thresholds": {
                    "failed_auth_per_minute": 10,
                    "failed_operations_per_minute": 20,
                    "permission_denied_per_minute": 15,
                    "rate_limit_per_minute": 100,
                },
            },
            "metrics": {
                "enabled": True,
                "collection_interval": 60,
                "retention_days": 90,
            },
        }

    def _initialize_security_adapters(self) -> None:
        """Initialize security adapters for all components."""
        try:
            # Import all security adapters
            from .docker_security_adapter import DockerSecurityAdapter
            from .k8s_security_adapter import K8sSecurityAdapter
            from .ftp_security_adapter import FtpSecurityAdapter
            from .git_security_adapter import GitSecurityAdapter
            from .vast_ai_security_adapter import VastAiSecurityAdapter
            from .github_security_adapter import GitHubSecurityAdapter
            from .system_security_adapter import SystemSecurityAdapter
            from .queue_security_adapter import QueueSecurityAdapter
            from .ssl_security_adapter import SSLSecurityAdapter
            from .vector_store_security_adapter import VectorStoreSecurityAdapter
            from .llm_security_adapter import LLMSecurityAdapter
            from .test_security_adapter import TestSecurityAdapter
            from .kind_security_adapter import KindSecurityAdapter
            from .argocd_security_adapter import ArgoCDSecurityAdapter

            # Register security adapters
            adapter_mapping = {
                "docker": DockerSecurityAdapter,
                "k8s": K8sSecurityAdapter,
                "kubernetes": K8sSecurityAdapter,
                "ftp": FtpSecurityAdapter,
                "git": GitSecurityAdapter,
                "github": GitHubSecurityAdapter,
                "vast": VastAiSecurityAdapter,
                "vast_ai": VastAiSecurityAdapter,
                "system": SystemSecurityAdapter,
                "queue": QueueSecurityAdapter,
                "ssl": SSLSecurityAdapter,
                "vector_store": VectorStoreSecurityAdapter,
                "llm": LLMSecurityAdapter,
                "test": TestSecurityAdapter,
                "kind": KindSecurityAdapter,
                "argocd": ArgoCDSecurityAdapter,
            }

            for component, adapter_class in adapter_mapping.items():
                if self._is_component_enabled(component):
                    self.security_adapters[component] = adapter_class(
                        self.settings_manager, self.roles_config
                    )
                    self.logger.info(f"Initialized security adapter for {component}")

        except CustomError as e:
            self.logger.error(f"Error initializing security adapters: {str(e)}")

    def _is_component_enabled(self, component: str) -> bool:
        """
        Check if component is enabled in configuration.

        Args:
            component: Component name

        Returns:
            True if component is enabled
        """
        try:
            adapters_config = self.config.get("adapters", {})
            component_config = adapters_config.get(component, {})
            return component_config.get("enabled", True)

        except CustomError as e:
            self.logger.error(
                f"Error checking if component {component} is enabled: {str(e)}"
            )
            return True

    def get_security_adapter(self, component: str) -> Optional[SecurityAdapter]:
        """
        Get security adapter for component.

        Args:
            component: Component name

        Returns:
            Security adapter instance or None
        """
        try:
            return self.security_adapters.get(component)

        except CustomError as e:
            self.logger.error(
                f"Error getting security adapter for {component}: {str(e)}"
            )
            return None

    def validate_operation(
        self,
        component: str,
        operation: str,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Validate operation with unified security.

        Args:
            component: Component name
            operation: Operation name
            user_roles: List of user roles
            operation_params: Operation parameters
            user_id: User identifier
            source_ip: Source IP address

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.logger.info(f"Validating operation: {component}.{operation}")

            # Get security adapter for component
            security_adapter = self.get_security_adapter(component)
            if not security_adapter:
                return False, f"No security adapter found for component: {component}"

            # Validate operation using component-specific adapter
            if hasattr(security_adapter, f"validate_{component}_operation"):
                validation_method = getattr(
                    security_adapter, f"validate_{component}_operation"
                )
                is_valid, error_msg = validation_method(
                    operation, user_roles, operation_params
                )
            else:
                # Fallback to base validation
                is_valid, error_msg = security_adapter.validate_operation(
                    operation, operation_params or {}
                )

            # Monitor the validation
            self.security_monitor.monitor_operation(
                component,
                operation,
                user_roles,
                {"valid": is_valid, "error": error_msg},
                user_id,
                source_ip,
                operation_params,
            )

            # Record metrics
            self.security_metrics.record_operation(
                component, operation, user_roles, is_valid
            )

            if is_valid:
                self.logger.info(
                    f"Operation validated successfully: {component}.{operation}"
                )
            else:
                self.logger.warning(
                    f"Operation validation failed: {component}.{operation} - {error_msg}"
                )

            return is_valid, error_msg

        except ValidationError as e:
            error_msg = f"Error validating operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    async def audit_operation(
        self,
        component: str,
        operation: str,
        user_roles: List[str],
        result: Any,
        operation_params: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
    ) -> None:
        """
        Audit operation with unified security.

        Args:
            component: Component name
            operation: Operation name
            user_roles: List of user roles
            result: Operation result
            operation_params: Operation parameters
            user_id: User identifier
            source_ip: Source IP address
        """
        try:
            self.logger.info(f"Auditing operation: {component}.{operation}")

            # Get security adapter for component
            security_adapter = self.get_security_adapter(component)
            if security_adapter:
                # Audit using component-specific adapter
                if hasattr(security_adapter, f"audit_{component}_operation"):
                    audit_method = getattr(
                        security_adapter, f"audit_{component}_operation"
                    )
                    audit_method(operation, user_roles, operation_params, "executed")
                else:
                    # Fallback to base auditing
                    await security_adapter.audit_operation(
                        operation, operation_params or {}, result
                    )

            # Monitor the operation
            await self.security_monitor.monitor_operation(
                component,
                operation,
                user_roles,
                result,
                user_id,
                source_ip,
                operation_params,
            )

            # Record metrics
            self.security_metrics.record_operation(
                component, operation, user_roles, result is not None
            )

            self.logger.info(f"Operation audited successfully: {component}.{operation}")

        except CustomError as e:
            self.logger.error(f"Error auditing operation: {str(e)}", exc_info=True)

    def check_permissions(
        self, component: str, user_roles: List[str], required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check permissions with unified security.

        Args:
            component: Component name
            user_roles: List of user roles
            required_permissions: List of required permissions

        Returns:
            Tuple of (has_permission, missing_permissions)
        """
        try:
            # Use roles manager for unified permission checking
            has_permission = True
            missing_permissions = []

            for permission in required_permissions:
                if not self.roles_manager.has_role_permission(
                    user_roles, permission, component
                ):
                    has_permission = False
                    missing_permissions.append(permission)

            return has_permission, missing_permissions

        except PermissionError as e:
            self.logger.error(f"Error checking permissions: {str(e)}")
            return False, required_permissions

    def get_user_permissions(
        self, user_roles: List[str], component: str = None
    ) -> List[str]:
        """
        Get user permissions with unified security.

        Args:
            user_roles: List of user roles
            component: Component name (optional)

        Returns:
            List of user permissions
        """
        try:
            return self.roles_manager.get_user_permissions(user_roles, component)

        except PermissionError as e:
            self.logger.error(f"Error getting user permissions: {str(e)}")
            return []

    def get_security_report(self) -> Dict[str, Any]:
        """
        Get unified security report.

        Returns:
            Security report data
        """
        try:
            # Get security monitor report
            monitor_report = self.security_monitor.generate_security_report()

            # Get security metrics
            metrics_data = self.security_metrics.get_metrics()

            # Get roles information
            roles_info = {
                "total_roles": len(self.roles_manager.get_all_roles()),
                "components": list(self.security_adapters.keys()),
                "enabled_components": [
                    comp
                    for comp in self.security_adapters.keys()
                    if self._is_component_enabled(comp)
                ],
            }

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "configuration": {
                    "enabled": self.config.get("enabled", True),
                    "framework": self.config.get("framework", "unknown"),
                    "global_settings": self.config.get("global_settings", {}),
                },
                "roles": roles_info,
                "monitoring": monitor_report,
                "metrics": metrics_data,
                "adapters": {
                    comp: {
                        "enabled": self._is_component_enabled(comp),
                        "available_roles": self.roles_manager.get_roles_for_component(
                            comp
                        ),
                    }
                    for comp in self.security_adapters.keys()
                },
            }

        except CustomError as e:
            self.logger.error(f"Error generating security report: {str(e)}")
            return {"error": str(e)}

    def get_component_status(self) -> Dict[str, Any]:
        """
        Get status of all security components.

        Returns:
            Component status information
        """
        try:
            status = {
                "timestamp": datetime.utcnow().isoformat(),
                "components": {},
                "overall_status": "healthy",
            }

            # Check each component
            for component, adapter in self.security_adapters.items():
                component_status = {
                    "enabled": self._is_component_enabled(component),
                    "adapter_available": adapter is not None,
                    "roles_available": len(
                        self.roles_manager.get_roles_for_component(component)
                    )
                    > 0,
                    "status": "healthy",
                }

                # Determine overall component status
                if not component_status["enabled"]:
                    component_status["status"] = "disabled"
                elif not component_status["adapter_available"]:
                    component_status["status"] = "error"
                elif not component_status["roles_available"]:
                    component_status["status"] = "warning"

                status["components"][component] = component_status

            # Determine overall system status
            error_components = [
                comp
                for comp, info in status["components"].items()
                if info["status"] == "error"
            ]
            warning_components = [
                comp
                for comp, info in status["components"].items()
                if info["status"] == "warning"
            ]

            if error_components:
                status["overall_status"] = "error"
            elif warning_components:
                status["overall_status"] = "warning"

            return status

        except CustomError as e:
            self.logger.error(f"Error getting component status: {str(e)}")
            return {"error": str(e)}

    def reload_configuration(self, config_path: Optional[str] = None) -> bool:
        """
        Reload security configuration.

        Args:
            config_path: Path to new configuration file

        Returns:
            True if configuration was reloaded successfully
        """
        try:
            # Load new configuration
            new_config = self._load_security_config(config_path)

            # Update configuration
            self.config = new_config

            # Reinitialize components
            self.roles_manager = RolesManager(self.config, self.roles_config)
            self._initialize_security_adapters()

            self.logger.info("Security configuration reloaded successfully")
            return True

        except ConfigurationError as e:
            self.logger.error(f"Error reloading configuration: {str(e)}")
            return False

    def export_configuration(self, file_path: str) -> bool:
        """
        Export current security configuration.

        Args:
            file_path: Path to export configuration

        Returns:
            True if configuration was exported successfully
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Export configuration
            export_data = {
                "security": self.config,
                "export_timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
            }

            with open(file_path, "w") as f:
                json.dump(export_data, f, indent=2)

            self.logger.info(f"Security configuration exported to {file_path}")
            return True

        except ConfigurationError as e:
            self.logger.error(f"Error exporting configuration: {str(e)}")
            return False


# Global instance for easy access
_unified_security = None


def get_unified_security() -> UnifiedSecurityIntegration:
    """
    Get global unified security integration instance.

    Returns:
        Unified security integration instance
    """
    global _unified_security
    if _unified_security is None:
        _unified_security = UnifiedSecurityIntegration()
    return _unified_security


def initialize_unified_security(
    config_path: Optional[str] = None,
    settings_manager: Optional[Any] = None,
    roles_config: Optional[RolesConfig] = None,
) -> UnifiedSecurityIntegration:
    """
    Initialize global unified security integration.

    Args:
        config_path: Path to security configuration
        settings_manager: Settings manager instance
        roles_config: Roles configuration instance

    Returns:
        Initialized unified security integration instance
    """
    global _unified_security
    _unified_security = UnifiedSecurityIntegration(
        config_path, settings_manager, roles_config
    )
    return _unified_security
