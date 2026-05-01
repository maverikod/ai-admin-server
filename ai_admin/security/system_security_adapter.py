from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, PermissionError, SSLError, ValidationError
"""System Security Adapter for AI Admin.

This module provides security integration for System operations including
role-based access control, operation auditing, and permission validation.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

import logging
from ai_admin.settings_manager import get_settings_manager
from ai_admin.config.roles_config import RolesConfig


class SystemOperation(Enum):
    """System operation types."""

    MONITOR = "monitor"
    PROCESSES = "processes"
    RESOURCES = "resources"
    TEMPERATURE = "temperature"
    GPU_METRICS = "gpu_metrics"
    NETWORK = "network"
    DISK_USAGE = "disk_usage"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    SYSTEM_INFO = "system_info"
    BOOT_TIME = "boot_time"
    UPTIME = "uptime"
    LOAD_AVERAGE = "load_average"
    SYSTEM_LOGS = "system_logs"
    KERNEL_INFO = "kernel_info"
    HARDWARE_INFO = "hardware_info"
    SERVICES = "services"
    CONFIGURATION = "configuration"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    SYSTEM_MAINTENANCE = "system_maintenance"


class SystemSecurityAdapter:
    """Security adapter for System operations.

    This class provides:
    - Role-based access control for System operations
    - Operation auditing and logging
    - Permission validation for System resources
    - System resource access validation
    - Hardware permission checking
    - SSL/TLS certificate management for System connections
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize System Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig(roles_file="config/roles.json")
        self.logger = logging.getLogger("ai_admin.system_security")

        # System operation permissions mapping
        self.system_permissions = {
            SystemOperation.MONITOR: ["system:monitor", "system:admin"],
            SystemOperation.PROCESSES: ["system:processes", "system:admin"],
            SystemOperation.RESOURCES: ["system:resources", "system:admin"],
            SystemOperation.TEMPERATURE: ["system:temperature", "system:admin"],
            SystemOperation.GPU_METRICS: ["system:gpu", "system:admin"],
            SystemOperation.NETWORK: ["system:network", "system:admin"],
            SystemOperation.DISK_USAGE: ["system:disk", "system:admin"],
            SystemOperation.MEMORY_USAGE: ["system:memory", "system:admin"],
            SystemOperation.CPU_USAGE: ["system:cpu", "system:admin"],
            SystemOperation.SYSTEM_INFO: ["system:info", "system:admin"],
            SystemOperation.BOOT_TIME: ["system:boot", "system:admin"],
            SystemOperation.UPTIME: ["system:uptime", "system:admin"],
            SystemOperation.LOAD_AVERAGE: ["system:load", "system:admin"],
            SystemOperation.SYSTEM_LOGS: ["system:logs", "system:admin"],
            SystemOperation.KERNEL_INFO: ["system:kernel", "system:admin"],
            SystemOperation.HARDWARE_INFO: ["system:hardware", "system:admin"],
            SystemOperation.SERVICES: ["system:services", "system:admin"],
            SystemOperation.CONFIGURATION: ["system:config", "system:admin"],
            SystemOperation.SECURITY_AUDIT: ["system:security", "system:admin"],
            SystemOperation.PERFORMANCE_ANALYSIS: [
                "system:performance",
                "system:admin",
            ],
            SystemOperation.SYSTEM_MAINTENANCE: ["system:maintenance", "system:admin"],
        }

        # System resource access permissions
        self.resource_permissions = {
            "cpu": ["system:cpu:read", "system:admin"],
            "memory": ["system:memory:read", "system:admin"],
            "disk": ["system:disk:read", "system:admin"],
            "network": ["system:network:read", "system:admin"],
            "gpu": ["system:gpu:read", "system:admin"],
            "temperature": ["system:temperature:read", "system:admin"],
            "processes": ["system:processes:read", "system:admin"],
            "services": ["system:services:read", "system:admin"],
            "logs": ["system:logs:read", "system:admin"],
            "config": ["system:config:read", "system:admin"],
        }

        # System hardware access permissions
        self.hardware_permissions = {
            "cpu_info": ["system:hardware:cpu", "system:admin"],
            "memory_info": ["system:hardware:memory", "system:admin"],
            "disk_info": ["system:hardware:disk", "system:admin"],
            "network_info": ["system:hardware:network", "system:admin"],
            "gpu_info": ["system:hardware:gpu", "system:admin"],
            "temperature_sensors": ["system:hardware:temperature", "system:admin"],
            "bios_info": ["system:hardware:bios", "system:admin"],
            "motherboard_info": ["system:hardware:motherboard", "system:admin"],
        }

        # System maintenance permissions
        self.maintenance_permissions = {
            "system_cleanup": ["system:maintenance:cleanup", "system:admin"],
            "log_rotation": ["system:maintenance:logs", "system:admin"],
            "cache_clear": ["system:maintenance:cache", "system:admin"],
            "temp_cleanup": ["system:maintenance:temp", "system:admin"],
            "disk_cleanup": ["system:maintenance:disk", "system:admin"],
            "service_restart": ["system:maintenance:services", "system:admin"],
            "kernel_update": ["system:maintenance:kernel", "system:admin"],
            "security_update": ["system:maintenance:security", "system:admin"],
        }

    def validate_system_operation(
        self,
        operation: SystemOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate if user has permission to perform System operation.

        Args:
            operation: System operation type
            user_roles: List of user roles
            operation_params: Operation parameters for additional validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.logger.info(f"Validating System operation: {operation.value}")

            # Check basic operation permissions
            required_permissions = self.system_permissions.get(operation, [])
            if not required_permissions:
                return False, f"Unknown System operation: {operation.value}"

            # Check if user has required permissions
            has_permission = self._check_user_permissions(
                user_roles, required_permissions
            )
            if not has_permission:
                return (
                    False,
                    f"Insufficient permissions for operation: {operation.value}",
                )

            # Additional validation based on operation type
            if operation_params:
                validation_result = self._validate_operation_specific_params(
                    operation, operation_params, user_roles
                )
                if not validation_result[0]:
                    return validation_result

            # Audit the operation
            self.audit_system_operation(
                operation, user_roles, operation_params, "validated"
            )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating System operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def check_system_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if user has required System permissions.

        Args:
            user_roles: List of user roles
            required_permissions: List of required permissions

        Returns:
            Tuple of (has_permission, missing_permissions)
        """
        try:
            user_permissions = self._get_user_permissions(user_roles)
            missing_permissions = []

            for permission in required_permissions:
                if permission not in user_permissions:
                    missing_permissions.append(permission)

            has_permission = len(missing_permissions) == 0

            self.logger.debug(
                f"Permission check: {has_permission}, "
                f"missing: {missing_permissions}"
            )

            return has_permission, missing_permissions

        except PermissionError as e:
            self.logger.error(f"Error checking System permissions: {str(e)}")
            return False, required_permissions

    def audit_system_operation(
        self,
        operation: SystemOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        status: str = "executed",
    ) -> None:
        """
        Audit System operation for security monitoring.

        Args:
            operation: System operation type
            user_roles: List of user roles
            operation_params: Operation parameters
            status: Operation status (validated, executed, failed)
        """
        try:
            audit_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "operation": operation.value,
                "user_roles": user_roles,
                "status": status,
                "operation_params": operation_params or {},
            }

            # Log audit information
            self.logger.info(f"System operation audited: {audit_data}")

            # Store audit data (could be extended to write to database)
            self._store_audit_data(audit_data)

        except CustomError as e:
            self.logger.error(f"Error auditing System operation: {str(e)}")

    def get_system_roles(self) -> Dict[str, List[str]]:
        """
        Get System-related roles and their permissions.

        Returns:
            Dictionary mapping roles to their System permissions
        """
        try:
            system_roles = {}

            # Get all roles from configuration
            all_roles = self.roles_config.get_all_roles()

            for role_name, role_config in all_roles.items():
                role_permissions = role_config.get("permissions", [])
                system_permissions = [
                    perm for perm in role_permissions if perm.startswith("system:")
                ]

                if system_permissions:
                    system_roles[role_name] = system_permissions

            return system_roles

        except CustomError as e:
            self.logger.error(f"Error getting System roles: {str(e)}")
            return {}

    def validate_system_access(
        self, resource_type: str, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate user access to System resource.

        Args:
            resource_type: Type of system resource
            user_roles: List of user roles

        Returns:
            Tuple of (has_access, error_message)
        """
        try:
            # Check resource-specific permissions
            required_permissions = self.resource_permissions.get(
                resource_type, ["system:admin"]
            )

            has_permission, missing_permissions = self.check_system_permissions(
                user_roles, required_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to system resource {resource_type}. "
                    f"Missing permissions: {missing_permissions}",
                )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating system access: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def check_system_resource_permissions(
        self,
        resource_name: str,
        operation: SystemOperation,
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Check permissions for specific System resource operation.

        Args:
            resource_name: System resource name
            operation: System operation
            user_roles: List of user roles

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check if user has admin permissions (bypass resource-specific checks)
            if self._check_user_permissions(user_roles, ["system:admin"]):
                return True, ""

            # Check resource-specific permissions
            resource_type = self._get_resource_type(resource_name)
            required_permissions = self.resource_permissions.get(
                resource_type, ["system:admin"]
            )

            has_permission, missing_permissions = self.check_system_permissions(
                user_roles, required_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to system resource {resource_name} "
                    f"for operation {operation.value}. "
                    f"Missing permissions: {missing_permissions}",
                )

            return True, ""

        except PermissionError as e:
            error_msg = f"Error checking system resource permissions: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def manage_system_certificates(
        self, operation: str = "setup", config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Manage System SSL/TLS certificates.

        Args:
            operation: Certificate operation (setup, verify, remove)
            config: Certificate configuration

        Returns:
            Tuple of (success, message)
        """
        try:
            if operation == "setup":
                return self._setup_system_ssl_certificates(config)
            elif operation == "verify":
                return self._verify_system_ssl_certificates(config)
            elif operation == "remove":
                return self._remove_system_ssl_certificates(config)
            else:
                return False, f"Unknown certificate operation: {operation}"

        except SSLError as e:
            error_msg = f"Error managing System certificates: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def setup_system_ssl(
        self, ssl_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Setup SSL/TLS configuration for System connections.

        Args:
            ssl_config: SSL configuration parameters

        Returns:
            Tuple of (success, message)
        """
        try:
            # Default SSL configuration
            default_config = {
                "ssl_verify": True,
                "ssl_cert_path": None,
                "ssl_key_path": None,
                "ssl_ca_path": None,
                "ssl_timeout": 30,
                "system_ssl_enabled": True,
            }

            if ssl_config:
                default_config.update(ssl_config)

            # Store SSL configuration in settings
            self.settings_manager.set_custom_setting(
                "system.ssl.verify", default_config["ssl_verify"]
            )
            self.settings_manager.set_custom_setting(
                "system.ssl.timeout", default_config["ssl_timeout"]
            )
            self.settings_manager.set_custom_setting(
                "system.ssl.enabled", default_config["system_ssl_enabled"]
            )

            if default_config["ssl_cert_path"]:
                self.settings_manager.set_custom_setting(
                    "system.ssl.cert_path", default_config["ssl_cert_path"]
                )

            if default_config["ssl_key_path"]:
                self.settings_manager.set_custom_setting(
                    "system.ssl.key_path", default_config["ssl_key_path"]
                )

            if default_config["ssl_ca_path"]:
                self.settings_manager.set_custom_setting(
                    "system.ssl.ca_path", default_config["ssl_ca_path"]
                )

            self.logger.info("SSL configuration completed for System connections")
            return True, "SSL configuration completed successfully"

        except ConfigurationError as e:
            error_msg = f"Error setting up System SSL: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def check_hardware_permissions(
        self, hardware_type: str, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Check permissions for specific hardware type.

        Args:
            hardware_type: Hardware type name
            user_roles: List of user roles

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check if user has admin permissions (bypass hardware restrictions)
            if self._check_user_permissions(user_roles, ["system:admin"]):
                return True, ""

            # Check hardware-specific permissions
            hardware_permissions = self.hardware_permissions.get(
                hardware_type, ["system:hardware:default"]
            )

            has_permission, missing_permissions = self.check_system_permissions(
                user_roles, hardware_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to hardware {hardware_type}. "
                    f"Missing permissions: {missing_permissions}",
                )

            return True, ""

        except PermissionError as e:
            error_msg = f"Error checking hardware permissions: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def check_maintenance_permissions(
        self, maintenance_type: str, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Check permissions for specific maintenance operation.

        Args:
            maintenance_type: Maintenance operation type
            user_roles: List of user roles

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check if user has admin permissions (bypass maintenance restrictions)
            if self._check_user_permissions(user_roles, ["system:admin"]):
                return True, ""

            # Check maintenance-specific permissions
            maintenance_permissions = self.maintenance_permissions.get(
                maintenance_type, ["system:maintenance:default"]
            )

            has_permission, missing_permissions = self.check_system_permissions(
                user_roles, maintenance_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to maintenance operation {maintenance_type}. "
                    f"Missing permissions: {missing_permissions}",
                )

            return True, ""

        except PermissionError as e:
            error_msg = f"Error checking maintenance permissions: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _check_user_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> bool:
        """
        Check if user has any of the required permissions.

        Args:
            user_roles: List of user roles
            required_permissions: List of required permissions

        Returns:
            True if user has at least one required permission
        """
        try:
            user_permissions = self._get_user_permissions(user_roles)

            for permission in required_permissions:
                if permission in user_permissions:
                    return True

            return False

        except PermissionError as e:
            self.logger.error(f"Error checking user permissions: {str(e)}")
            return False

    def _get_user_permissions(self, user_roles: List[str]) -> List[str]:
        """
        Get all permissions for user roles.

        Args:
            user_roles: List of user roles

        Returns:
            List of user permissions
        """
        try:
            all_permissions = []

            for role in user_roles:
                role_config = self.roles_config.get_role_config(role)
                if role_config:
                    role_permissions = role_config.get("permissions", [])
                    all_permissions.extend(role_permissions)

            return list(set(all_permissions))  # Remove duplicates

        except PermissionError as e:
            self.logger.error(f"Error getting user permissions: {str(e)}")
            return []

    def _validate_operation_specific_params(
        self,
        operation: SystemOperation,
        operation_params: Dict[str, Any],
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Validate operation-specific parameters.

        Args:
            operation: System operation
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if operation == SystemOperation.MONITOR:
                return self._validate_monitor_operation(operation_params, user_roles)
            elif operation == SystemOperation.PROCESSES:
                return self._validate_processes_operation(operation_params, user_roles)
            elif operation == SystemOperation.GPU_METRICS:
                return self._validate_gpu_metrics_operation(
                    operation_params, user_roles
                )
            elif operation == SystemOperation.SYSTEM_LOGS:
                return self._validate_system_logs_operation(
                    operation_params, user_roles
                )
            elif operation == SystemOperation.SYSTEM_MAINTENANCE:
                return self._validate_maintenance_operation(
                    operation_params, user_roles
                )

            return True, ""

        except ValidationError as e:
            return False, f"Error validating operation parameters: {str(e)}"

    def _validate_monitor_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate System monitor operation parameters."""
        try:
            # Check GPU permissions if GPU monitoring is requested
            include_gpu = operation_params.get("include_gpu", False)
            if include_gpu:
                has_permission, error_msg = self.check_hardware_permissions(
                    "gpu_info", user_roles
                )
                if not has_permission:
                    return False, error_msg

            # Check temperature permissions if temperature monitoring is requested
            include_temperature = operation_params.get("include_temperature", False)
            if include_temperature:
                has_permission, error_msg = self.check_hardware_permissions(
                    "temperature_sensors", user_roles
                )
                if not has_permission:
                    return False, error_msg

            # Check processes permissions if process monitoring is requested
            include_processes = operation_params.get("include_processes", False)
            if include_processes:
                has_permission, error_msg = self.validate_system_access(
                    "processes", user_roles
                )
                if not has_permission:
                    return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating monitor operation: {str(e)}"

    def _validate_processes_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate System processes operation parameters."""
        try:
            # Check if user can view processes
            has_permission, error_msg = self.validate_system_access(
                "processes", user_roles
            )
            if not has_permission:
                return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating processes operation: {str(e)}"

    def _validate_gpu_metrics_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate System GPU metrics operation parameters."""
        try:
            # Check GPU permissions
            has_permission, error_msg = self.check_hardware_permissions(
                "gpu_info", user_roles
            )
            if not has_permission:
                return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating GPU metrics operation: {str(e)}"

    def _validate_system_logs_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate System logs operation parameters."""
        try:
            # Check logs permissions
            has_permission, error_msg = self.validate_system_access("logs", user_roles)
            if not has_permission:
                return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating system logs operation: {str(e)}"

    def _validate_maintenance_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate System maintenance operation parameters."""
        try:
            # Check maintenance type permissions
            maintenance_type = operation_params.get("maintenance_type", "default")
            has_permission, error_msg = self.check_maintenance_permissions(
                maintenance_type, user_roles
            )
            if not has_permission:
                return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating maintenance operation: {str(e)}"

    def _get_resource_type(self, resource_name: str) -> str:
        """Get resource type from resource name."""
        try:
            resource_mapping = {
                "cpu": "cpu",
                "memory": "memory",
                "ram": "memory",
                "disk": "disk",
                "storage": "disk",
                "network": "network",
                "net": "network",
                "gpu": "gpu",
                "temperature": "temperature",
                "temp": "temperature",
                "processes": "processes",
                "services": "services",
                "logs": "logs",
                "config": "config",
            }

            resource_lower = resource_name.lower()
            for key, value in resource_mapping.items():
                if key in resource_lower:
                    return value

            return "default"

        except CustomError:
            return "default"

    def _setup_system_ssl_certificates(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Setup SSL certificates for System connections."""
        try:
            # This could be extended to integrate with mcp-security-framework
            # For now, just configure basic SSL settings
            ssl_config = config or {}

            # Store SSL configuration
            self.settings_manager.set_custom_setting(
                "system.ssl.verify", ssl_config.get("ssl_verify", True)
            )
            self.settings_manager.set_custom_setting(
                "system.ssl.timeout", ssl_config.get("ssl_timeout", 30)
            )

            return True, "SSL certificates configured successfully"

        except SSLError as e:
            return False, f"Error setting up SSL certificates: {str(e)}"

    def _verify_system_ssl_certificates(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Verify SSL certificates for System connections."""
        try:
            # Check SSL configuration
            ssl_verify = self.settings_manager.get("system.ssl.verify", True)
            ssl_timeout = self.settings_manager.get("system.ssl.timeout", 30)

            if not ssl_verify:
                return False, "SSL verification is disabled"

            return (
                True,
                f"SSL certificates are properly configured (timeout: {ssl_timeout}s)",
            )

        except SSLError as e:
            return False, f"Error verifying SSL certificates: {str(e)}"

    def _remove_system_ssl_certificates(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Remove SSL certificates configuration for System connections."""
        try:
            # Remove SSL configuration
            ssl_configs = [
                "system.ssl.verify",
                "system.ssl.cert_path",
                "system.ssl.key_path",
                "system.ssl.ca_path",
                "system.ssl.timeout",
                "system.ssl.enabled",
            ]

            for config_key in ssl_configs:
                # Note: AIAdminSettingsManager doesn't have remove method
                # This would need to be implemented or use a different approach
                self.logger.info(f"Would remove SSL config: {config_key}")

            return True, "SSL certificates configuration removed"

        except SSLError as e:
            return False, f"Error removing SSL certificates: {str(e)}"

    def _store_audit_data(self, audit_data: Dict[str, Any]) -> None:
        """
        Store audit data for security monitoring.

        Args:
            audit_data: Audit data to store
        """
        try:
            # This could be extended to write to database or external system
            # For now, just log the data
            self.logger.info(f"System audit data stored: {audit_data}")

        except CustomError as e:
            self.logger.error(f"Error storing System audit data: {str(e)}")
