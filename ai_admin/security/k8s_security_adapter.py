from ai_admin.core.custom_exceptions import CustomError, PermissionError, SSLError, ValidationError
"""Kubernetes Security Adapter for AI Admin.

This module provides security integration for Kubernetes operations including
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


class K8sOperation(Enum):
    """Kubernetes operation types."""

    DEPLOYMENT_CREATE = "deployment_create"
    DEPLOYMENT_DELETE = "deployment_delete"
    DEPLOYMENT_UPDATE = "deployment_update"
    POD_CREATE = "pod_create"
    POD_DELETE = "pod_delete"
    POD_STATUS = "pod_status"
    POD_LOGS = "pod_logs"
    POD_EXEC = "pod_exec"
    SERVICE_CREATE = "service_create"
    SERVICE_DELETE = "service_delete"
    NAMESPACE_CREATE = "namespace_create"
    NAMESPACE_DELETE = "namespace_delete"
    CONFIGMAP_CREATE = "configmap_create"
    CONFIGMAP_DELETE = "configmap_delete"
    CLUSTER_CREATE = "cluster_create"
    CLUSTER_DELETE = "cluster_delete"
    CLUSTER_STATUS = "cluster_status"
    CERTIFICATE_CREATE = "certificate_create"
    CERTIFICATE_DELETE = "certificate_delete"
    MTLS_SETUP = "mtls_setup"


class K8sResourceType(Enum):
    """Kubernetes resource types."""

    DEPLOYMENT = "deployment"
    POD = "pod"
    SERVICE = "service"
    NAMESPACE = "namespace"
    CONFIGMAP = "configmap"
    CLUSTER = "cluster"
    CERTIFICATE = "certificate"
    SECRET = "secret"


class K8sSecurityAdapter:
    """Security adapter for Kubernetes operations.

    This class provides:
    - Role-based access control for Kubernetes operations
    - Operation auditing and logging
    - Permission validation for Kubernetes resources
    - Cluster access validation
    - Certificate management integration
    - mTLS setup validation
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize Kubernetes Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig(roles_file="config/roles.json")
        self.logger = logging.getLogger("ai_admin.k8s_security")

        # Kubernetes operation permissions mapping
        self.k8s_permissions = {
            K8sOperation.DEPLOYMENT_CREATE: ["k8s:deployment:create", "k8s:admin"],
            K8sOperation.DEPLOYMENT_DELETE: ["k8s:deployment:delete", "k8s:admin"],
            K8sOperation.DEPLOYMENT_UPDATE: ["k8s:deployment:update", "k8s:admin"],
            K8sOperation.POD_CREATE: ["k8s:pod:create", "k8s:admin"],
            K8sOperation.POD_DELETE: ["k8s:pod:delete", "k8s:admin"],
            K8sOperation.POD_STATUS: ["k8s:pod:read", "k8s:admin"],
            K8sOperation.POD_LOGS: ["k8s:pod:logs", "k8s:admin"],
            K8sOperation.POD_EXEC: ["k8s:pod:exec", "k8s:admin"],
            K8sOperation.SERVICE_CREATE: ["k8s:service:create", "k8s:admin"],
            K8sOperation.SERVICE_DELETE: ["k8s:service:delete", "k8s:admin"],
            K8sOperation.NAMESPACE_CREATE: ["k8s:namespace:create", "k8s:admin"],
            K8sOperation.NAMESPACE_DELETE: ["k8s:namespace:delete", "k8s:admin"],
            K8sOperation.CONFIGMAP_CREATE: ["k8s:configmap:create", "k8s:admin"],
            K8sOperation.CONFIGMAP_DELETE: ["k8s:configmap:delete", "k8s:admin"],
            K8sOperation.CLUSTER_CREATE: ["k8s:cluster:create", "k8s:admin"],
            K8sOperation.CLUSTER_DELETE: ["k8s:cluster:delete", "k8s:admin"],
            K8sOperation.CLUSTER_STATUS: ["k8s:cluster:read", "k8s:admin"],
            K8sOperation.CERTIFICATE_CREATE: ["k8s:certificate:create", "k8s:admin"],
            K8sOperation.CERTIFICATE_DELETE: ["k8s:certificate:delete", "k8s:admin"],
            K8sOperation.MTLS_SETUP: ["k8s:mtls:setup", "k8s:admin"],
        }

        # Cluster access permissions
        self.cluster_permissions = {
            "default": ["k8s:cluster:default"],
            "production": ["k8s:cluster:production"],
            "staging": ["k8s:cluster:staging"],
            "development": ["k8s:cluster:development"],
        }

        # Namespace access permissions
        self.namespace_permissions = {
            "default": ["k8s:namespace:default"],
            "kube-system": ["k8s:namespace:kube-system"],
            "production": ["k8s:namespace:production"],
            "staging": ["k8s:namespace:staging"],
            "development": ["k8s:namespace:development"],
        }

    def validate_k8s_operation(
        self,
        operation: K8sOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate if user has permission to perform Kubernetes operation.

        Args:
            operation: Kubernetes operation type
            user_roles: List of user roles
            operation_params: Operation parameters for additional validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.logger.info(f"Validating Kubernetes operation: {operation.value}")

            # Check basic operation permissions
            required_permissions = self.k8s_permissions.get(operation, [])
            if not required_permissions:
                return False, f"Unknown Kubernetes operation: {operation.value}"

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
            self.audit_k8s_operation(
                operation, user_roles, operation_params, "validated"
            )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating Kubernetes operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def check_k8s_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if user has required Kubernetes permissions.

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
            self.logger.error(f"Error checking Kubernetes permissions: {str(e)}")
            return False, required_permissions

    def audit_k8s_operation(
        self,
        operation: K8sOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        status: str = "executed",
    ) -> None:
        """
        Audit Kubernetes operation for security monitoring.

        Args:
            operation: Kubernetes operation type
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
            self.logger.info(f"Kubernetes operation audited: {audit_data}")

            # Store audit data (could be extended to write to database)
            self._store_audit_data(audit_data)

        except CustomError as e:
            self.logger.error(f"Error auditing Kubernetes operation: {str(e)}")

    def get_k8s_roles(self) -> Dict[str, List[str]]:
        """
        Get Kubernetes-related roles and their permissions.

        Returns:
            Dictionary mapping roles to their Kubernetes permissions
        """
        try:
            k8s_roles = {}

            # Get all roles from configuration
            all_roles = self.roles_config.get_all_roles()

            for role_name, role_config in all_roles.items():
                role_permissions = role_config.get("permissions", [])
                k8s_permissions = [
                    perm for perm in role_permissions if perm.startswith("k8s:")
                ]

                if k8s_permissions:
                    k8s_roles[role_name] = k8s_permissions

            return k8s_roles

        except CustomError as e:
            self.logger.error(f"Error getting Kubernetes roles: {str(e)}")
            return {}

    def validate_k8s_cluster_access(
        self, cluster_name: str, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate user access to Kubernetes cluster.

        Args:
            cluster_name: Cluster name
            user_roles: List of user roles

        Returns:
            Tuple of (has_access, error_message)
        """
        try:
            # Check cluster-specific permissions
            required_permissions = self.cluster_permissions.get(
                cluster_name, ["k8s:cluster:default"]
            )

            has_permission, missing_permissions = self.check_k8s_permissions(
                user_roles, required_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to cluster {cluster_name}. Missing permissions: {missing_permissions}",
                )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating cluster access: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def check_k8s_resource_permissions(
        self,
        resource_type: K8sResourceType,
        operation: K8sOperation,
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Check permissions for specific Kubernetes resource operation.

        Args:
            resource_type: Kubernetes resource type
            operation: Kubernetes operation
            user_roles: List of user roles

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check if user has admin permissions (bypass resource-specific checks)
            if self._check_user_permissions(user_roles, ["k8s:admin"]):
                return True, ""

            # Check resource-specific permissions
            resource_permissions = self._get_resource_permissions(
                resource_type, operation
            )
            if not resource_permissions:
                # No specific restrictions, check general operation permissions
                return self.validate_k8s_operation(operation, user_roles)

            # Check if user has required resource permissions
            has_permission, missing_permissions = self.check_k8s_permissions(
                user_roles, resource_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to {resource_type.value} {operation.value}. Missing permissions: {missing_permissions}",
                )

            return True, ""

        except PermissionError as e:
            error_msg = f"Error checking resource permissions: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def manage_k8s_certificates(
        self,
        operation: str,
        user_roles: List[str],
        cert_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Manage Kubernetes certificates with security validation.

        Args:
            operation: Certificate operation (create, delete, verify)
            user_roles: List of user roles
            cert_params: Certificate parameters

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check certificate management permissions
            required_permissions = ["k8s:certificate:manage", "k8s:admin"]
            has_permission = self._check_user_permissions(
                user_roles, required_permissions
            )

            if not has_permission:
                return False, "Insufficient permissions for certificate management"

            # Additional validation based on operation
            if operation == "create" and cert_params:
                # Validate certificate creation parameters
                validation_result = self._validate_certificate_creation(
                    cert_params, user_roles
                )
                if not validation_result[0]:
                    return validation_result

            # Audit certificate operation
            self.audit_k8s_operation(
                (
                    K8sOperation.CERTIFICATE_CREATE
                    if operation == "create"
                    else K8sOperation.CERTIFICATE_DELETE
                ),
                user_roles,
                cert_params,
                "validated",
            )

            return True, ""

        except SSLError as e:
            error_msg = f"Error managing certificates: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def setup_k8s_mtls(
        self, user_roles: List[str], mtls_params: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Setup mTLS for Kubernetes with security validation.

        Args:
            user_roles: List of user roles
            mtls_params: mTLS setup parameters

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check mTLS setup permissions
            required_permissions = ["k8s:mtls:setup", "k8s:admin"]
            has_permission = self._check_user_permissions(
                user_roles, required_permissions
            )

            if not has_permission:
                return False, "Insufficient permissions for mTLS setup"

            # Validate mTLS parameters
            if mtls_params:
                validation_result = self._validate_mtls_params(mtls_params, user_roles)
                if not validation_result[0]:
                    return validation_result

            # Audit mTLS setup
            self.audit_k8s_operation(
                K8sOperation.MTLS_SETUP, user_roles, mtls_params, "validated"
            )

            return True, ""

        except SSLError as e:
            error_msg = f"Error setting up mTLS: {str(e)}"
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
        operation: K8sOperation,
        operation_params: Dict[str, Any],
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Validate operation-specific parameters.

        Args:
            operation: Kubernetes operation
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if operation in [K8sOperation.DEPLOYMENT_CREATE, K8sOperation.POD_CREATE]:
                return self._validate_create_operation(operation_params, user_roles)
            elif operation in [
                K8sOperation.CLUSTER_CREATE,
                K8sOperation.CLUSTER_DELETE,
            ]:
                return self._validate_cluster_operation(operation_params, user_roles)
            elif operation == K8sOperation.NAMESPACE_CREATE:
                return self._validate_namespace_operation(operation_params, user_roles)

            return True, ""

        except ValidationError as e:
            return False, f"Error validating operation parameters: {str(e)}"

    def _validate_create_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Kubernetes create operation parameters."""
        try:
            namespace = operation_params.get("namespace", "default")

            # Check namespace access
            has_access, error_msg = self._validate_namespace_access(
                namespace, user_roles
            )
            if not has_access:
                return False, error_msg

            # Check cluster access if specified
            cluster_name = operation_params.get("cluster_name")
            if cluster_name:
                has_access, error_msg = self.validate_k8s_cluster_access(
                    cluster_name, user_roles
                )
                if not has_access:
                    return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating create operation: {str(e)}"

    def _validate_cluster_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Kubernetes cluster operation parameters."""
        try:
            cluster_name = operation_params.get("cluster_name", "default")

            # Check cluster access
            has_access, error_msg = self.validate_k8s_cluster_access(
                cluster_name, user_roles
            )
            if not has_access:
                return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating cluster operation: {str(e)}"

    def _validate_namespace_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Kubernetes namespace operation parameters."""
        try:
            namespace = operation_params.get("namespace", "default")

            # Check namespace access
            has_access, error_msg = self._validate_namespace_access(
                namespace, user_roles
            )
            if not has_access:
                return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating namespace operation: {str(e)}"

    def _validate_namespace_access(
        self, namespace: str, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate user access to Kubernetes namespace.

        Args:
            namespace: Namespace name
            user_roles: List of user roles

        Returns:
            Tuple of (has_access, error_message)
        """
        try:
            # Check namespace-specific permissions
            required_permissions = self.namespace_permissions.get(
                namespace, ["k8s:namespace:default"]
            )

            has_permission, missing_permissions = self.check_k8s_permissions(
                user_roles, required_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to namespace {namespace}. Missing permissions: {missing_permissions}",
                )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating namespace access: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _validate_certificate_creation(
        self, cert_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate certificate creation parameters."""
        try:
            cluster_name = cert_params.get("cluster_name")
            if cluster_name:
                has_access, error_msg = self.validate_k8s_cluster_access(
                    cluster_name, user_roles
                )
                if not has_access:
                    return False, error_msg

            return True, ""

        except SSLError as e:
            return False, f"Error validating certificate creation: {str(e)}"

    def _validate_mtls_params(
        self, mtls_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate mTLS setup parameters."""
        try:
            cluster_name = mtls_params.get("cluster_name")
            if cluster_name:
                has_access, error_msg = self.validate_k8s_cluster_access(
                    cluster_name, user_roles
                )
                if not has_access:
                    return False, error_msg

            return True, ""

        except SSLError as e:
            return False, f"Error validating mTLS parameters: {str(e)}"

    def _get_resource_permissions(
        self, resource_type: K8sResourceType, operation: K8sOperation
    ) -> List[str]:
        """
        Get specific permissions required for resource operation.

        Args:
            resource_type: Kubernetes resource type
            operation: Kubernetes operation

        Returns:
            List of required permissions for the resource operation
        """
        try:
            # This could be extended to read from configuration
            # For now, return empty list (no specific restrictions)
            return []

        except PermissionError as e:
            self.logger.error(f"Error getting resource permissions: {str(e)}")
            return []

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
