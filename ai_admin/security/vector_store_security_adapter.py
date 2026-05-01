from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, PermissionError, SSLError, ValidationError
"""Vector Store Security Adapter for AI Admin.

This module provides security integration for Vector Store operations including
role-based access control, operation auditing, and permission validation.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

import logging
from ai_admin.settings_manager import get_settings_manager
from ai_admin.config.roles_config import RolesConfig


class VectorStoreOperation(Enum):
    """Vector Store operation types."""

    DEPLOY = "deploy"
    CONFIGURE = "configure"
    SCALE = "scale"
    UPDATE = "update"
    DELETE = "delete"
    STATUS = "status"
    LOGS = "logs"
    BACKUP = "backup"
    RESTORE = "restore"
    MONITOR = "monitor"


class VectorStoreSecurityAdapter:
    """Security adapter for Vector Store operations.

    This class provides:
    - Role-based access control for Vector Store operations
    - Operation auditing and logging
    - Permission validation for Vector Store resources
    - Cluster access validation
    - SSL/TLS certificate management for Vector Store connections
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize Vector Store Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig(roles_file="config/roles.json")
        self.logger = logging.getLogger("ai_admin.vector_store_security")

        # Vector Store operation permissions mapping
        self.vector_store_permissions = {
            VectorStoreOperation.DEPLOY: ["vector_store:deploy", "vector_store:admin"],
            VectorStoreOperation.CONFIGURE: [
                "vector_store:configure",
                "vector_store:admin",
            ],
            VectorStoreOperation.SCALE: ["vector_store:scale", "vector_store:admin"],
            VectorStoreOperation.UPDATE: ["vector_store:update", "vector_store:admin"],
            VectorStoreOperation.DELETE: ["vector_store:delete", "vector_store:admin"],
            VectorStoreOperation.STATUS: ["vector_store:status", "vector_store:admin"],
            VectorStoreOperation.LOGS: ["vector_store:logs", "vector_store:admin"],
            VectorStoreOperation.BACKUP: ["vector_store:backup", "vector_store:admin"],
            VectorStoreOperation.RESTORE: [
                "vector_store:restore",
                "vector_store:admin",
            ],
            VectorStoreOperation.MONITOR: [
                "vector_store:monitor",
                "vector_store:admin",
            ],
        }

        # Vector Store resource permissions
        self.resource_permissions = {
            "redis": ["vector_store:redis"],
            "faiss": ["vector_store:faiss"],
            "elasticsearch": ["vector_store:elasticsearch"],
            "pinecone": ["vector_store:pinecone"],
            "weaviate": ["vector_store:weaviate"],
        }

    def validate_vector_store_operation(
        self,
        operation: VectorStoreOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate if user has permission to perform Vector Store operation.

        Args:
            operation: Vector Store operation type
            user_roles: List of user roles
            operation_params: Operation parameters for additional validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.logger.info(f"Validating Vector Store operation: {operation.value}")

            # Check basic operation permissions
            required_permissions = self.vector_store_permissions.get(operation, [])
            if not required_permissions:
                return False, f"Unknown Vector Store operation: {operation.value}"

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
            self.audit_vector_store_operation(
                operation, user_roles, operation_params, "validated"
            )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating Vector Store operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def check_vector_store_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if user has required Vector Store permissions.

        Args:
            user_roles: List of user roles
            required_permissions: List of required permissions

        Returns:
            Tuple of (has_permission, missing_permissions)
        """
        try:
            user_permissions = []
            for role in user_roles:
                permissions = self.roles_config.get_permissions(role)
                user_permissions.extend([p.name for p in permissions])
            missing_permissions = []

            for permission in required_permissions:
                if permission not in user_permissions:
                    missing_permissions.append(permission)

            has_permission = len(missing_permissions) == 0
            return has_permission, missing_permissions

        except PermissionError as e:
            self.logger.error(f"Error checking Vector Store permissions: {str(e)}")
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
            user_permissions = []
            for role in user_roles:
                permissions = self.roles_config.get_permissions(role)
                user_permissions.extend([p.name for p in permissions])
            return any(
                permission in user_permissions for permission in required_permissions
            )
        except PermissionError as e:
            self.logger.error(f"Error checking user permissions: {str(e)}")
            return False

    def _validate_operation_specific_params(
        self,
        operation: VectorStoreOperation,
        operation_params: Dict[str, Any],
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Validate operation-specific parameters.

        Args:
            operation: Vector Store operation type
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate cluster access for deployment operations
            if operation in [
                VectorStoreOperation.DEPLOY,
                VectorStoreOperation.CONFIGURE,
            ]:
                cluster_name = operation_params.get("cluster_name")
                if cluster_name:
                    cluster_access = self._validate_cluster_access(
                        cluster_name, user_roles
                    )
                    if not cluster_access[0]:
                        return cluster_access

            # Validate resource permissions
            if "resources" in operation_params:
                resources = operation_params["resources"]
                for resource in resources:
                    resource_permissions = self.resource_permissions.get(resource, [])
                    if resource_permissions:
                        has_resource_permission = self._check_user_permissions(
                            user_roles, resource_permissions
                        )
                        if not has_resource_permission:
                            return (
                                False,
                                f"Insufficient permissions for resource: {resource}",
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

    def audit_vector_store_operation(
        self,
        operation: VectorStoreOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        status: str = "executed",
    ) -> None:
        """
        Audit Vector Store operation.

        Args:
            operation: Vector Store operation type
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
                f"Vector Store operation audited: {operation.value}",
                extra={"audit_data": audit_data},
            )

        except CustomError as e:
            self.logger.error(f"Error auditing Vector Store operation: {str(e)}")

    def get_vector_store_roles(self) -> List[str]:
        """
        Get all Vector Store related roles.

        Returns:
            List of Vector Store roles
        """
        try:
            all_roles = self.roles_config.get_roles()
            # Filter roles that might be related to vector store operations
            vector_store_roles = [role for role in all_roles if "vector" in role.lower() or "store" in role.lower()]
            return vector_store_roles
        except CustomError as e:
            self.logger.error(f"Error getting Vector Store roles: {str(e)}")
            return []

    def validate_access(self, user_roles: List[str], resource: str) -> bool:
        """
        Validate access to Vector Store resource.

        Args:
            user_roles: List of user roles
            resource: Resource name

        Returns:
            True if access is allowed
        """
        try:
            resource_permissions = self.resource_permissions.get(resource, [])
            if not resource_permissions:
                return True  # No specific permissions required

            return self._check_user_permissions(user_roles, resource_permissions)

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
        self, operation: str, user_roles: List[str], **kwargs: Any
    ) -> Tuple[bool, str]:
        """
        Manage SSL certificates for Vector Store connections.

        Args:
            operation: Certificate operation (generate, validate, revoke)
            user_roles: List of user roles
            **kwargs: Additional parameters

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check certificate management permissions
            cert_permissions = ["vector_store:certificates", "vector_store:admin"]
            has_permission = self._check_user_permissions(user_roles, cert_permissions)

            if not has_permission:
                return False, "Insufficient permissions for certificate management"

            # Audit certificate operation
            self.audit_vector_store_operation(
                VectorStoreOperation.CONFIGURE,
                user_roles,
                {"cert_operation": operation},
            )

            return True, "Certificate operation authorized"

        except SSLError as e:
            error_msg = f"Error managing certificates: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def setup_ssl(
        self, user_roles: List[str], cluster_name: str, **kwargs: Any
    ) -> Tuple[bool, str]:
        """
        Setup SSL/TLS for Vector Store connections.

        Args:
            user_roles: List of user roles
            cluster_name: Name of the cluster
            **kwargs: Additional parameters

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check SSL setup permissions
            ssl_permissions = ["vector_store:ssl", "vector_store:admin"]
            has_permission = self._check_user_permissions(user_roles, ssl_permissions)

            if not has_permission:
                return False, "Insufficient permissions for SSL setup"

            # Validate cluster access
            cluster_access = self._validate_cluster_access(cluster_name, user_roles)
            if not cluster_access[0]:
                return cluster_access

            # Audit SSL setup
            self.audit_vector_store_operation(
                VectorStoreOperation.CONFIGURE,
                user_roles,
                {"ssl_setup": True, "cluster_name": cluster_name},
            )

            return True, "SSL setup authorized"

        except ConfigurationError as e:
            error_msg = f"Error setting up SSL: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg
