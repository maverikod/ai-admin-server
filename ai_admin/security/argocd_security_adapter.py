from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, PermissionError, SSLError, ValidationError
"""ArgoCD Security Adapter for AI Admin.

This module provides security integration for ArgoCD operations including
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


class ArgoCDOperation(Enum):
    """ArgoCD operation types."""

    INIT = "init"
    DEPLOY = "deploy"
    SYNC = "sync"
    ROLLBACK = "rollback"
    DELETE = "delete"
    STATUS = "status"
    LOGS = "logs"
    CONFIGURE = "configure"
    UPDATE = "update"
    SCALE = "scale"
    MONITOR = "monitor"
    BACKUP = "backup"
    RESTORE = "restore"


class ArgoCDComponent(Enum):
    """ArgoCD component types."""

    SERVER = "server"
    REPO_SERVER = "repo_server"
    APPLICATION_CONTROLLER = "application_controller"
    REDIS = "redis"
    DEX = "dex"
    NOTIFICATIONS = "notifications"


class ArgoCDSecurityAdapter:
    """Security adapter for ArgoCD operations.

    This class provides:
    - Role-based access control for ArgoCD operations
    - Operation auditing and logging
    - Permission validation for ArgoCD resources
    - Cluster access validation
    - SSL/TLS certificate management for ArgoCD connections
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize ArgoCD Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig(roles_file="config/roles.json")
        self.logger = logging.getLogger("ai_admin.argocd_security")

        # ArgoCD operation permissions mapping
        self.argocd_permissions = {
            ArgoCDOperation.INIT: ["argocd:init", "argocd:admin"],
            ArgoCDOperation.DEPLOY: ["argocd:deploy", "argocd:admin"],
            ArgoCDOperation.SYNC: ["argocd:sync", "argocd:admin"],
            ArgoCDOperation.ROLLBACK: ["argocd:rollback", "argocd:admin"],
            ArgoCDOperation.DELETE: ["argocd:delete", "argocd:admin"],
            ArgoCDOperation.STATUS: ["argocd:status", "argocd:admin"],
            ArgoCDOperation.LOGS: ["argocd:logs", "argocd:admin"],
            ArgoCDOperation.CONFIGURE: ["argocd:configure", "argocd:admin"],
            ArgoCDOperation.UPDATE: ["argocd:update", "argocd:admin"],
            ArgoCDOperation.SCALE: ["argocd:scale", "argocd:admin"],
            ArgoCDOperation.MONITOR: ["argocd:monitor", "argocd:admin"],
            ArgoCDOperation.BACKUP: ["argocd:backup", "argocd:admin"],
            ArgoCDOperation.RESTORE: ["argocd:restore", "argocd:admin"],
        }

        # ArgoCD component permissions
        self.component_permissions = {
            ArgoCDComponent.SERVER: ["argocd:component:server"],
            ArgoCDComponent.REPO_SERVER: ["argocd:component:repo_server"],
            ArgoCDComponent.APPLICATION_CONTROLLER: [
                "argocd:component:application_controller"
            ],
            ArgoCDComponent.REDIS: ["argocd:component:redis"],
            ArgoCDComponent.DEX: ["argocd:component:dex"],
            ArgoCDComponent.NOTIFICATIONS: ["argocd:component:notifications"],
        }

        # ArgoCD namespace permissions
        self.namespace_permissions = {
            "argocd": ["argocd:namespace:argocd"],
            "argocd-system": ["argocd:namespace:argocd-system"],
            "default": ["argocd:namespace:default"],
        }

    def validate_argocd_operation(
        self,
        operation: ArgoCDOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate if user has permission to perform ArgoCD operation.

        Args:
            operation: ArgoCD operation type
            user_roles: List of user roles
            operation_params: Operation parameters for additional validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.logger.info(f"Validating ArgoCD operation: {operation.value}")

            # Check basic operation permissions
            required_permissions = self.argocd_permissions.get(operation, [])
            if not required_permissions:
                return False, f"Unknown ArgoCD operation: {operation.value}"

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
            self.audit_argocd_operation(
                operation, user_roles, operation_params, "validated"
            )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating ArgoCD operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def check_argocd_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if user has required ArgoCD permissions.

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
            self.logger.error(f"Error checking ArgoCD permissions: {str(e)}")
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
        operation: ArgoCDOperation,
        operation_params: Dict[str, Any],
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Validate operation-specific parameters.

        Args:
            operation: ArgoCD operation type
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate namespace permissions
            namespace = operation_params.get("namespace", "argocd")
            if namespace:
                namespace_permissions = self.namespace_permissions.get(namespace, [])
                if namespace_permissions:
                    has_namespace_permission = self._check_user_permissions(
                        user_roles, namespace_permissions
                    )
                    if not has_namespace_permission:
                        return (
                            False,
                            f"Insufficient permissions for namespace: {namespace}",
                        )

            # Validate component permissions for init operations
            if operation == ArgoCDOperation.INIT:
                components = operation_params.get("components", [])
                for component in components:
                    try:
                        component_enum = ArgoCDComponent(component)
                        component_permissions = self.component_permissions.get(
                            component_enum, []
                        )
                        if component_permissions:
                            has_component_permission = self._check_user_permissions(
                                user_roles, component_permissions
                            )
                            if not has_component_permission:
                                return (
                                    False,
                                    f"Insufficient permissions for component: {component}",
                                )
                    except ValueError:
                        pass  # Unknown component, allow if no specific permissions

            # Validate cluster access
            cluster_name = operation_params.get("cluster_name")
            if cluster_name:
                cluster_access = self._validate_cluster_access(cluster_name, user_roles)
                if not cluster_access[0]:
                    return cluster_access

            # Validate service type permissions
            service_type = operation_params.get("service_type", "ClusterIP")
            if service_type in ["NodePort", "LoadBalancer"]:
                service_permissions = ["argocd:service:external", "argocd:admin"]
                has_service_permission = self._check_user_permissions(
                    user_roles, service_permissions
                )
                if not has_service_permission:
                    return (
                        False,
                        f"Insufficient permissions for service type: {service_type}",
                    )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating operation parameters: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def _validate_cluster_access(
        self, cluster_name: str, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate cluster access permissions.

        Args:
            cluster_name: Name of the cluster
            user_roles: List of user roles

        Returns:
            Tuple of (has_access, error_message)
        """
        try:
            # Check cluster-specific permissions
            cluster_permissions = [f"cluster:{cluster_name}", "cluster:admin"]
            has_access = self._check_user_permissions(user_roles, cluster_permissions)

            if not has_access:
                return (
                    False,
                    f"Insufficient permissions for cluster: {cluster_name}",
                )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating cluster access: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def audit_argocd_operation(
        self,
        operation: ArgoCDOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        status: str = "executed",
    ) -> None:
        """
        Audit ArgoCD operation.

        Args:
            operation: ArgoCD operation type
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
                f"ArgoCD operation audited: {operation.value}",
                extra={"audit_data": audit_data},
            )

        except CustomError as e:
            self.logger.error(f"Error auditing ArgoCD operation: {str(e)}")

    def get_argocd_roles(self) -> List[str]:
        """
        Get all ArgoCD related roles.

        Returns:
            List of ArgoCD roles
        """
        try:
            return self.roles_config.get_roles_by_category("argocd")
        except CustomError as e:
            self.logger.error(f"Error getting ArgoCD roles: {str(e)}")
            return []

    def validate_access(self, user_roles: List[str], resource: str) -> bool:
        """
        Validate access to ArgoCD resource.

        Args:
            user_roles: List of user roles
            resource: Resource name

        Returns:
            True if access is allowed
        """
        try:
            # Check if resource is a component
            try:
                component = ArgoCDComponent(resource)
                component_permissions = self.component_permissions.get(component, [])
                if component_permissions:
                    return self._check_user_permissions(
                        user_roles, component_permissions
                    )
            except ValueError:
                pass

            # Check if resource is a namespace
            if resource in self.namespace_permissions:
                namespace_permissions = self.namespace_permissions[resource]
                return self._check_user_permissions(user_roles, namespace_permissions)

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
        Manage SSL certificates for ArgoCD connections.

        Args:
            operation: Certificate operation (generate, validate, revoke)
            user_roles: List of user roles
            **kwargs: Additional parameters

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check certificate management permissions
            cert_permissions = ["argocd:certificates", "argocd:admin"]
            has_permission = self._check_user_permissions(user_roles, cert_permissions)

            if not has_permission:
                return False, "Insufficient permissions for certificate management"

            # Audit certificate operation
            self.audit_argocd_operation(
                ArgoCDOperation.CONFIGURE, user_roles, {"cert_operation": operation}
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
        Setup SSL/TLS for ArgoCD connections.

        Args:
            user_roles: List of user roles
            cluster_name: Name of the cluster
            **kwargs: Additional parameters

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check SSL setup permissions
            ssl_permissions = ["argocd:ssl", "argocd:admin"]
            has_permission = self._check_user_permissions(user_roles, ssl_permissions)

            if not has_permission:
                return False, "Insufficient permissions for SSL setup"

            # Validate cluster access
            cluster_access = self._validate_cluster_access(cluster_name, user_roles)
            if not cluster_access[0]:
                return cluster_access

            # Audit SSL setup
            self.audit_argocd_operation(
                ArgoCDOperation.CONFIGURE,
                user_roles,
                {"ssl_setup": True, "cluster_name": cluster_name},
            )

            return True, "SSL setup authorized"

        except ConfigurationError as e:
            error_msg = f"Error setting up SSL: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg
