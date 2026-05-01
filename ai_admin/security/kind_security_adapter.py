from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, PermissionError, SSLError, ValidationError
"""Kind Security Adapter for AI Admin.

This module provides security integration for Kind operations including
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


class KindOperation(Enum):
    """Kind operation types."""

    CREATE = "create"
    DELETE = "delete"
    LIST = "list"
    GET_NODES = "get_nodes"
    LOAD_IMAGE = "load_image"
    CONFIGURE = "configure"
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    STATUS = "status"
    LOGS = "logs"
    BACKUP = "backup"
    RESTORE = "restore"


class KindClusterType(Enum):
    """Kind cluster types."""

    SINGLE_NODE = "single_node"
    MULTI_NODE = "multi_node"
    HA = "ha"
    CUSTOM = "custom"


class KindSecurityAdapter:
    """Security adapter for Kind operations.

    This class provides:
    - Role-based access control for Kind operations
    - Operation auditing and logging
    - Permission validation for Kind resources
    - Cluster access validation
    - SSL/TLS certificate management for Kind connections
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize Kind Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig(roles_file="config/roles.json")
        self.logger = logging.getLogger("ai_admin.kind_security")

        # Kind operation permissions mapping
        self.kind_permissions = {
            KindOperation.CREATE: ["kind:create", "kind:admin"],
            KindOperation.DELETE: ["kind:delete", "kind:admin"],
            KindOperation.LIST: ["kind:list", "kind:admin"],
            KindOperation.GET_NODES: ["kind:nodes", "kind:admin"],
            KindOperation.LOAD_IMAGE: ["kind:load_image", "kind:admin"],
            KindOperation.CONFIGURE: ["kind:configure", "kind:admin"],
            KindOperation.START: ["kind:start", "kind:admin"],
            KindOperation.STOP: ["kind:stop", "kind:admin"],
            KindOperation.RESTART: ["kind:restart", "kind:admin"],
            KindOperation.STATUS: ["kind:status", "kind:admin"],
            KindOperation.LOGS: ["kind:logs", "kind:admin"],
            KindOperation.BACKUP: ["kind:backup", "kind:admin"],
            KindOperation.RESTORE: ["kind:restore", "kind:admin"],
        }

        # Kind cluster type permissions
        self.cluster_type_permissions = {
            KindClusterType.SINGLE_NODE: ["kind:cluster:single_node"],
            KindClusterType.MULTI_NODE: ["kind:cluster:multi_node"],
            KindClusterType.HA: ["kind:cluster:ha"],
            KindClusterType.CUSTOM: ["kind:cluster:custom"],
        }

        # Resource limits
        self.resource_limits = {
            "max_clusters": 5,
            "max_nodes_per_cluster": 10,
            "max_memory_per_node": "8Gi",
            "max_cpu_per_node": "4",
        }

    def validate_kind_operation(
        self,
        operation: KindOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate if user has permission to perform Kind operation.

        Args:
            operation: Kind operation type
            user_roles: List of user roles
            operation_params: Operation parameters for additional validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.logger.info(f"Validating Kind operation: {operation.value}")

            # Check basic operation permissions
            required_permissions = self.kind_permissions.get(operation, [])
            if not required_permissions:
                return False, f"Unknown Kind operation: {operation.value}"

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
            self.audit_kind_operation(
                operation, user_roles, operation_params, "validated"
            )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating Kind operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def check_kind_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if user has required Kind permissions.

        Args:
            user_roles: List of user roles
            required_permissions: List of required permissions

        Returns:
            Tuple of (has_permission, missing_permissions)
        """
        try:
            user_permissions = self.roles_config.get_user_permissions(user_roles)
            missing_permissions = []

            for permission in required_permissions:
                if permission not in user_permissions:
                    missing_permissions.append(permission)

            has_permission = len(missing_permissions) == 0
            return has_permission, missing_permissions

        except PermissionError as e:
            self.logger.error(f"Error checking Kind permissions: {str(e)}")
            return False, required_permissions

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
            user_permissions = self.roles_config.get_user_permissions(user_roles)
            return any(
                permission in user_permissions for permission in required_permissions
            )
        except PermissionError as e:
            self.logger.error(f"Error checking user permissions: {str(e)}")
            return False

    def _validate_operation_specific_params(
        self,
        operation: KindOperation,
        operation_params: Dict[str, Any],
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Validate operation-specific parameters.

        Args:
            operation: Kind operation type
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate cluster type permissions for create operations
            if operation == KindOperation.CREATE:
                cluster_type = operation_params.get("cluster_type", "single_node")
                try:
                    cluster_type_enum = KindClusterType(cluster_type)
                    cluster_type_permissions = self.cluster_type_permissions.get(
                        cluster_type_enum, []
                    )
                    if cluster_type_permissions:
                        has_cluster_type_permission = self._check_user_permissions(
                            user_roles, cluster_type_permissions
                        )
                        if not has_cluster_type_permission:
                            return (
                                False,
                                f"Insufficient permissions for cluster type: {cluster_type}",
                            )
                except ValueError:
                    pass  # Unknown cluster type, allow if no specific permissions

            # Validate resource limits
            if operation == KindOperation.CREATE:
                resource_validation = self._validate_resource_limits(
                    operation_params, user_roles
                )
                if not resource_validation[0]:
                    return resource_validation

            # Validate cluster name
            cluster_name = operation_params.get("cluster_name")
            if cluster_name:
                name_validation = self._validate_cluster_name(cluster_name, user_roles)
                if not name_validation[0]:
                    return name_validation

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating operation parameters: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def _validate_resource_limits(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate resource limits for cluster creation.

        Args:
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if user has admin permissions for resource limits
            admin_permissions = ["kind:admin", "kind:unlimited_resources"]
            has_admin_permission = self._check_user_permissions(
                user_roles, admin_permissions
            )

            if has_admin_permission:
                return True, ""

            # Validate against default limits
            num_nodes = operation_params.get("num_nodes", 1)
            if num_nodes > self.resource_limits["max_nodes_per_cluster"]:
                return (
                    False,
                    f"Too many nodes: {num_nodes} > {self.resource_limits['max_nodes_per_cluster']}",
                )

            memory = operation_params.get("memory", "2Gi")
            if self._parse_memory(memory) > self._parse_memory(
                self.resource_limits["max_memory_per_node"]
            ):
                return (
                    False,
                    f"Too much memory: {memory} > {self.resource_limits['max_memory_per_node']}",
                )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating resource limits: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def _parse_memory(self, memory_str: str) -> int:
        """
        Parse memory string to bytes.

        Args:
            memory_str: Memory string (e.g., "2Gi", "512Mi")

        Returns:
            Memory in bytes
        """
        try:
            memory_str = memory_str.upper()
            if memory_str.endswith("GI"):
                return int(memory_str[:-2]) * 1024 * 1024 * 1024
            elif memory_str.endswith("MI"):
                return int(memory_str[:-2]) * 1024 * 1024
            elif memory_str.endswith("G"):
                return int(memory_str[:-1]) * 1000 * 1000 * 1000
            elif memory_str.endswith("M"):
                return int(memory_str[:-1]) * 1000 * 1000
            else:
                return int(memory_str)
        except (ValueError, IndexError):
            return 0

    def _validate_cluster_name(
        self, cluster_name: str, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate cluster name.

        Args:
            cluster_name: Name of the cluster
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check for reserved names
            reserved_names = ["kind", "kubernetes", "k8s", "cluster"]
            if cluster_name.lower() in reserved_names:
                reserved_permissions = ["kind:reserved_names", "kind:admin"]
                has_reserved_permission = self._check_user_permissions(
                    user_roles, reserved_permissions
                )
                if not has_reserved_permission:
                    return (
                        False,
                        f"Reserved cluster name: {cluster_name}",
                    )

            # Check name format
            if not cluster_name.replace("-", "").replace("_", "").isalnum():
                return (
                    False,
                    f"Invalid cluster name format: {cluster_name}",
                )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating cluster name: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def audit_kind_operation(
        self,
        operation: KindOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        status: str = "executed",
    ) -> None:
        """
        Audit Kind operation.

        Args:
            operation: Kind operation type
            user_roles: List of user roles
            operation_params: Operation parameters
            status: Operation status
        """
        try:
            audit_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "operation": operation.value,
                "user_roles": user_roles,
                "status": status,
                "operation_params": operation_params or {},
            }

            self.logger.info(
                f"Kind operation audited: {operation.value}",
                extra={"audit_data": audit_data},
            )

        except CustomError as e:
            self.logger.error(f"Error auditing Kind operation: {str(e)}")

    def get_kind_roles(self) -> List[str]:
        """
        Get all Kind related roles.

        Returns:
            List of Kind roles
        """
        try:
            return self.roles_config.get_roles_by_category("kind")
        except CustomError as e:
            self.logger.error(f"Error getting Kind roles: {str(e)}")
            return []

    def validate_access(self, user_roles: List[str], resource: str) -> bool:
        """
        Validate access to Kind resource.

        Args:
            user_roles: List of user roles
            resource: Resource name

        Returns:
            True if access is allowed
        """
        try:
            # Check if resource is a cluster type
            try:
                cluster_type = KindClusterType(resource)
                cluster_type_permissions = self.cluster_type_permissions.get(
                    cluster_type, []
                )
                if cluster_type_permissions:
                    return self._check_user_permissions(
                        user_roles, cluster_type_permissions
                    )
            except ValueError:
                pass

            # Default to allowing access if no specific permissions
            return True

        except ValidationError as e:
            self.logger.error(f"Error validating access: {str(e)}")
            return False

    def check_resource_permissions(
        self, user_roles: List[str], resources: List[str]
    ) -> Dict[str, bool]:
        """
        Check permissions for multiple resources.

        Args:
            user_roles: List of user roles
            resources: List of resource names

        Returns:
            Dictionary mapping resource names to permission status
        """
        try:
            permissions = {}
            for resource in resources:
                permissions[resource] = self.validate_access(user_roles, resource)

            return permissions

        except PermissionError as e:
            self.logger.error(f"Error checking resource permissions: {str(e)}")
            return {resource: False for resource in resources}

    def manage_certificates(
        self, operation: str, user_roles: List[str], **kwargs
    ) -> Tuple[bool, str]:
        """
        Manage SSL certificates for Kind connections.

        Args:
            operation: Certificate operation (generate, validate, revoke)
            user_roles: List of user roles
            **kwargs: Additional parameters

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check certificate management permissions
            cert_permissions = ["kind:certificates", "kind:admin"]
            has_permission = self._check_user_permissions(user_roles, cert_permissions)

            if not has_permission:
                return False, "Insufficient permissions for certificate management"

            # Audit certificate operation
            self.audit_kind_operation(
                KindOperation.CONFIGURE, user_roles, {"cert_operation": operation}
            )

            return True, "Certificate operation authorized"

        except SSLError as e:
            error_msg = f"Error managing certificates: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def setup_ssl(
        self, user_roles: List[str], cluster_name: str, **kwargs
    ) -> Tuple[bool, str]:
        """
        Setup SSL/TLS for Kind connections.

        Args:
            user_roles: List of user roles
            cluster_name: Name of the cluster
            **kwargs: Additional parameters

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check SSL setup permissions
            ssl_permissions = ["kind:ssl", "kind:admin"]
            has_permission = self._check_user_permissions(user_roles, ssl_permissions)

            if not has_permission:
                return False, "Insufficient permissions for SSL setup"

            # Validate cluster name
            cluster_validation = self._validate_cluster_name(cluster_name, user_roles)
            if not cluster_validation[0]:
                return cluster_validation

            # Audit SSL setup
            self.audit_kind_operation(
                KindOperation.CONFIGURE,
                user_roles,
                {"ssl_setup": True, "cluster_name": cluster_name},
            )

            return True, "SSL setup authorized"

        except ConfigurationError as e:
            error_msg = f"Error setting up SSL: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg
