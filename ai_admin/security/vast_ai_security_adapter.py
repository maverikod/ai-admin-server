from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, PermissionError, SSLError, ValidationError
"""Vast.ai Security Adapter for AI Admin.

This module provides security integration for Vast.ai operations including
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


class VastAiOperation(Enum):
    """Vast.ai operation types."""

    SEARCH = "search"
    CREATE = "create"
    DESTROY = "destroy"
    INSTANCES = "instances"
    SSH = "ssh"
    LOGS = "logs"
    STOP = "stop"
    START = "start"
    RESTART = "restart"
    INSPECT = "inspect"
    CONFIG = "config"
    BILLING = "billing"
    API_ACCESS = "api_access"


class VastAiSecurityAdapter:
    """Security adapter for Vast.ai operations.

    This class provides:
    - Role-based access control for Vast.ai operations
    - Operation auditing and logging
    - Permission validation for Vast.ai resources
    - API access validation
    - Instance permission checking
    - SSL/TLS certificate management for Vast.ai connections
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize Vast.ai Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig()
        self.logger = logging.getLogger("ai_admin.vast_ai_security")

        # Vast.ai operation permissions mapping
        self.vast_ai_permissions = {
            VastAiOperation.SEARCH: ["vast:search", "vast:admin"],
            VastAiOperation.CREATE: ["vast:create", "vast:admin"],
            VastAiOperation.DESTROY: ["vast:destroy", "vast:admin"],
            VastAiOperation.INSTANCES: ["vast:instances", "vast:admin"],
            VastAiOperation.SSH: ["vast:ssh", "vast:admin"],
            VastAiOperation.LOGS: ["vast:logs", "vast:admin"],
            VastAiOperation.STOP: ["vast:stop", "vast:admin"],
            VastAiOperation.START: ["vast:start", "vast:admin"],
            VastAiOperation.RESTART: ["vast:restart", "vast:admin"],
            VastAiOperation.INSPECT: ["vast:inspect", "vast:admin"],
            VastAiOperation.CONFIG: ["vast:config", "vast:admin"],
            VastAiOperation.BILLING: ["vast:billing", "vast:admin"],
            VastAiOperation.API_ACCESS: ["vast:api", "vast:admin"],
        }

        # Vast.ai API access permissions
        self.api_permissions = {
            "console.vast.ai": ["vast:api:console"],
            "api.vast.ai": ["vast:api:api"],
            "default": ["vast:api:default"],
        }

        # Instance access permissions
        self.instance_permissions = {
            "own_instances": ["vast:instances:own"],
            "all_instances": ["vast:instances:all", "vast:admin"],
            "shared_instances": ["vast:instances:shared"],
        }

        # GPU type restrictions
        self.gpu_restrictions = {
            "RTX_4090": ["vast:gpu:rtx4090", "vast:gpu:premium"],
            "A100": ["vast:gpu:a100", "vast:gpu:premium"],
            "H100": ["vast:gpu:h100", "vast:gpu:premium"],
            "RTX_3090": ["vast:gpu:rtx3090", "vast:gpu:standard"],
            "RTX_3080": ["vast:gpu:rtx3080", "vast:gpu:standard"],
            "default": ["vast:gpu:default"],
        }

    def validate_vast_ai_operation(
        self,
        operation: VastAiOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate if user has permission to perform Vast.ai operation.

        Args:
            operation: Vast.ai operation type
            user_roles: List of user roles
            operation_params: Operation parameters for additional validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.logger.info(f"Validating Vast.ai operation: {operation.value}")

            # Check basic operation permissions
            required_permissions = self.vast_ai_permissions.get(operation, [])
            if not required_permissions:
                return False, f"Unknown Vast.ai operation: {operation.value}"

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
            self.audit_vast_ai_operation(
                operation, user_roles, operation_params, "validated"
            )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating Vast.ai operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def check_vast_ai_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if user has required Vast.ai permissions.

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
            self.logger.error(f"Error checking Vast.ai permissions: {str(e)}")
            return False, required_permissions

    def audit_vast_ai_operation(
        self,
        operation: VastAiOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        status: str = "executed",
    ) -> None:
        """
        Audit Vast.ai operation for security monitoring.

        Args:
            operation: Vast.ai operation type
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
            self.logger.info(f"Vast.ai operation audited: {audit_data}")

            # Store audit data (could be extended to write to database)
            self._store_audit_data(audit_data)

        except CustomError as e:
            self.logger.error(f"Error auditing Vast.ai operation: {str(e)}")

    def get_vast_ai_roles(self) -> Dict[str, List[str]]:
        """
        Get Vast.ai-related roles and their permissions.

        Returns:
            Dictionary mapping roles to their Vast.ai permissions
        """
        try:
            vast_ai_roles = {}

            # Get all roles from configuration
            all_roles = self.roles_config.get_all_roles()

            for role_name, role_config in all_roles.items():
                role_permissions = role_config.get("permissions", [])
                vast_ai_permissions = [
                    perm for perm in role_permissions if perm.startswith("vast:")
                ]

                if vast_ai_permissions:
                    vast_ai_roles[role_name] = vast_ai_permissions

            return vast_ai_roles

        except CustomError as e:
            self.logger.error(f"Error getting Vast.ai roles: {str(e)}")
            return {}

    def validate_vast_ai_api_access(
        self, api_url: str, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate user access to Vast.ai API.

        Args:
            api_url: Vast.ai API URL
            user_roles: List of user roles

        Returns:
            Tuple of (has_access, error_message)
        """
        try:
            # Extract API hostname
            api_host = self._extract_api_host(api_url)

            # Check API-specific permissions
            required_permissions = self.api_permissions.get(
                api_host, self.api_permissions["default"]
            )

            has_permission, missing_permissions = self.check_vast_ai_permissions(
                user_roles, required_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to API {api_host}. Missing permissions: {missing_permissions}",
                )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating API access: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def check_vast_ai_instance_permissions(
        self,
        instance_id: Optional[int],
        operation: VastAiOperation,
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Check permissions for specific Vast.ai instance operation.

        Args:
            instance_id: Vast.ai instance ID
            operation: Vast.ai operation
            user_roles: List of user roles

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check if user has admin permissions (bypass instance-specific checks)
            if self._check_user_permissions(user_roles, ["vast:admin"]):
                return True, ""

            # Check instance access permissions
            if instance_id:
                # For specific instance operations, check if user owns the instance
                # This would require integration with Vast.ai API to check ownership
                has_permission = self._check_user_permissions(
                    user_roles, ["vast:instances:own", "vast:instances:all"]
                )
                if not has_permission:
                    return (
                        False,
                        f"Access denied to instance {instance_id}. Missing instance permissions",
                    )

            return True, ""

        except PermissionError as e:
            error_msg = f"Error checking instance permissions: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def manage_vast_ai_certificates(
        self, operation: str = "setup", config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Manage Vast.ai SSL/TLS certificates.

        Args:
            operation: Certificate operation (setup, verify, remove)
            config: Certificate configuration

        Returns:
            Tuple of (success, message)
        """
        try:
            if operation == "setup":
                return self._setup_vast_ai_ssl_certificates(config)
            elif operation == "verify":
                return self._verify_vast_ai_ssl_certificates(config)
            elif operation == "remove":
                return self._remove_vast_ai_ssl_certificates(config)
            else:
                return False, f"Unknown certificate operation: {operation}"

        except SSLError as e:
            error_msg = f"Error managing Vast.ai certificates: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def setup_vast_ai_ssl(
        self, ssl_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Setup SSL/TLS configuration for Vast.ai connections.

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
            }

            if ssl_config:
                default_config.update(ssl_config)

            # Store SSL configuration in settings
            self.settings_manager.set("vast.ssl.verify", default_config["ssl_verify"])
            self.settings_manager.set("vast.ssl.timeout", default_config["ssl_timeout"])

            if default_config["ssl_cert_path"]:
                self.settings_manager.set(
                    "vast.ssl.cert_path", default_config["ssl_cert_path"]
                )

            if default_config["ssl_key_path"]:
                self.settings_manager.set(
                    "vast.ssl.key_path", default_config["ssl_key_path"]
                )

            if default_config["ssl_ca_path"]:
                self.settings_manager.set(
                    "vast.ssl.ca_path", default_config["ssl_ca_path"]
                )

            self.logger.info("SSL configuration completed for Vast.ai connections")
            return True, "SSL configuration completed successfully"

        except ConfigurationError as e:
            error_msg = f"Error setting up Vast.ai SSL: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def check_gpu_permissions(
        self, gpu_name: str, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Check permissions for specific GPU type.

        Args:
            gpu_name: GPU model name
            user_roles: List of user roles

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check if user has admin permissions (bypass GPU restrictions)
            if self._check_user_permissions(user_roles, ["vast:admin"]):
                return True, ""

            # Check GPU-specific permissions
            gpu_permissions = self.gpu_restrictions.get(
                gpu_name, self.gpu_restrictions["default"]
            )

            has_permission, missing_permissions = self.check_vast_ai_permissions(
                user_roles, gpu_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to GPU {gpu_name}. Missing permissions: {missing_permissions}",
                )

            return True, ""

        except PermissionError as e:
            error_msg = f"Error checking GPU permissions: {str(e)}"
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
        operation: VastAiOperation,
        operation_params: Dict[str, Any],
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Validate operation-specific parameters.

        Args:
            operation: Vast.ai operation
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if operation == VastAiOperation.CREATE:
                return self._validate_create_operation(operation_params, user_roles)
            elif operation == VastAiOperation.DESTROY:
                return self._validate_destroy_operation(operation_params, user_roles)
            elif operation == VastAiOperation.SEARCH:
                return self._validate_search_operation(operation_params, user_roles)
            elif operation == VastAiOperation.INSTANCES:
                return self._validate_instances_operation(operation_params, user_roles)

            return True, ""

        except ValidationError as e:
            return False, f"Error validating operation parameters: {str(e)}"

    def _validate_create_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Vast.ai create operation parameters."""
        try:
            # Check GPU permissions
            gpu_name = operation_params.get("gpu_name")
            if gpu_name:
                has_permission, error_msg = self.check_gpu_permissions(
                    gpu_name, user_roles
                )
                if not has_permission:
                    return False, error_msg

            # Check instance permissions
            instance_id = operation_params.get("bundle_id")
            if instance_id:
                has_permission, error_msg = self.check_vast_ai_instance_permissions(
                    instance_id, VastAiOperation.CREATE, user_roles
                )
                if not has_permission:
                    return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating create operation: {str(e)}"

    def _validate_destroy_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Vast.ai destroy operation parameters."""
        try:
            # Check instance permissions
            instance_id = operation_params.get("instance_id")
            if instance_id:
                has_permission, error_msg = self.check_vast_ai_instance_permissions(
                    instance_id, VastAiOperation.DESTROY, user_roles
                )
                if not has_permission:
                    return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating destroy operation: {str(e)}"

    def _validate_search_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Vast.ai search operation parameters."""
        try:
            # Check GPU permissions
            gpu_name = operation_params.get("gpu_name")
            if gpu_name:
                has_permission, error_msg = self.check_gpu_permissions(
                    gpu_name, user_roles
                )
                if not has_permission:
                    return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating search operation: {str(e)}"

    def _validate_instances_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Vast.ai instances operation parameters."""
        try:
            # Check if user can view all instances
            show_all = operation_params.get("show_all", False)
            if show_all:
                has_permission = self._check_user_permissions(
                    user_roles, ["vast:instances:all", "vast:admin"]
                )
                if not has_permission:
                    return False, "Access denied to view all instances"

            return True, ""

        except ValidationError as e:
            return False, f"Error validating instances operation: {str(e)}"

    def _extract_api_host(self, api_url: str) -> str:
        """Extract API hostname from URL."""
        try:
            if "://" in api_url:
                return api_url.split("://")[1].split("/")[0]
            else:
                return api_url.split("/")[0]
        except CustomError:
            return "unknown"

    def _setup_vast_ai_ssl_certificates(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Setup SSL certificates for Vast.ai connections."""
        try:
            # This could be extended to integrate with mcp-security-framework
            # For now, just configure basic SSL settings
            ssl_config = config or {}

            # Store SSL configuration
            self.settings_manager.set(
                "vast.ssl.verify", ssl_config.get("ssl_verify", True)
            )
            self.settings_manager.set(
                "vast.ssl.timeout", ssl_config.get("ssl_timeout", 30)
            )

            return True, "SSL certificates configured successfully"

        except SSLError as e:
            return False, f"Error setting up SSL certificates: {str(e)}"

    def _verify_vast_ai_ssl_certificates(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Verify SSL certificates for Vast.ai connections."""
        try:
            # Check SSL configuration
            ssl_verify = self.settings_manager.get("vast.ssl.verify", True)
            ssl_timeout = self.settings_manager.get("vast.ssl.timeout", 30)

            if not ssl_verify:
                return False, "SSL verification is disabled"

            return (
                True,
                f"SSL certificates are properly configured (timeout: {ssl_timeout}s)",
            )

        except SSLError as e:
            return False, f"Error verifying SSL certificates: {str(e)}"

    def _remove_vast_ai_ssl_certificates(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Remove SSL certificates configuration for Vast.ai connections."""
        try:
            # Remove SSL configuration
            ssl_configs = [
                "vast.ssl.verify",
                "vast.ssl.cert_path",
                "vast.ssl.key_path",
                "vast.ssl.ca_path",
                "vast.ssl.timeout",
            ]

            for config_key in ssl_configs:
                self.settings_manager.remove(config_key)

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
            self.logger.info(f"Audit data stored: {audit_data}")

        except CustomError as e:
            self.logger.error(f"Error storing audit data: {str(e)}")
