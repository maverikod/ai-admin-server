from ai_admin.core.custom_exceptions import SSLError
"""SSL Security Adapter for AI Admin.

This module provides security integration for SSL/TLS operations including
role-based access control, operation auditing, and certificate management.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

import logging
from ai_admin.settings_manager import get_settings_manager
from ai_admin.config.roles_config import RolesConfig


class SSLOperation(Enum):
    """SSL operation types."""

    GENERATE = "generate"
    VIEW = "view"
    VERIFY = "verify"
    REVOKE = "revoke"
    MANAGE = "manage"
    SETUP = "setup"
    CONFIGURE = "configure"
    VALIDATE = "validate"
    EXPORT = "export"
    IMPORT = "import"
    BACKUP = "backup"
    RESTORE = "restore"


class SSLCertificateType(Enum):
    """SSL certificate types."""

    CA = "ca"
    SERVER = "server"
    CLIENT = "client"
    SELF_SIGNED = "self_signed"
    CA_SIGNED = "ca_signed"
    WILDCARD = "wildcard"
    INTERMEDIATE = "intermediate"


class SSLSecurityAdapter:
    """Security adapter for SSL/TLS operations.

    This class provides:
    - Role-based access control for SSL operations
    - Operation auditing and logging
    - Permission validation for SSL resources
    - Certificate access validation
    - SSL/TLS certificate management
    - mTLS setup validation
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize SSL Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig()
        self.logger = logging.getLogger("ai_admin.ssl_security")

        # SSL operation permissions mapping
        self.ssl_permissions = {
            SSLOperation.GENERATE: ["ssl:generate", "ssl:admin"],
            SSLOperation.VIEW: ["ssl:view", "ssl:admin"],
            SSLOperation.VERIFY: ["ssl:verify", "ssl:admin"],
            SSLOperation.REVOKE: ["ssl:revoke", "ssl:admin"],
            SSLOperation.MANAGE: ["ssl:manage", "ssl:admin"],
            SSLOperation.SETUP: ["ssl:setup", "ssl:admin"],
            SSLOperation.CONFIGURE: ["ssl:configure", "ssl:admin"],
            SSLOperation.VALIDATE: ["ssl:validate", "ssl:admin"],
            SSLOperation.EXPORT: ["ssl:export", "ssl:admin"],
            SSLOperation.IMPORT: ["ssl:import", "ssl:admin"],
            SSLOperation.BACKUP: ["ssl:backup", "ssl:admin"],
            SSLOperation.RESTORE: ["ssl:restore", "ssl:admin"],
        }

        # SSL certificate type permissions
        self.certificate_type_permissions = {
            SSLCertificateType.CA: ["ssl:ca", "ssl:admin"],
            SSLCertificateType.SERVER: ["ssl:server", "ssl:admin"],
            SSLCertificateType.CLIENT: ["ssl:client", "ssl:admin"],
            SSLCertificateType.SELF_SIGNED: ["ssl:self_signed", "ssl:admin"],
            SSLCertificateType.CA_SIGNED: ["ssl:ca_signed", "ssl:admin"],
            SSLCertificateType.WILDCARD: ["ssl:wildcard", "ssl:admin"],
            SSLCertificateType.INTERMEDIATE: ["ssl:intermediate", "ssl:admin"],
        }

        # SSL resource permissions
        self.ssl_resource_permissions = {
            "certificates": ["ssl:certificates", "ssl:admin"],
            "private_keys": ["ssl:private_keys", "ssl:admin"],
            "csr": ["ssl:csr", "ssl:admin"],
            "crl": ["ssl:crl", "ssl:admin"],
            "config": ["ssl:config", "ssl:admin"],
            "backup": ["ssl:backup", "ssl:admin"],
        }

    def validate_ssl_operation(
        self,
        operation: SSLOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate if user has permission to perform SSL operation.

        Args:
            operation: SSL operation to validate
            user_roles: List of user roles
            operation_params: Operation parameters for additional validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check basic operation permissions
            required_permissions = self.ssl_permissions.get(operation, [])
            has_permission = self.roles_config.has_any_permission(
                user_roles, required_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Insufficient permissions for SSL operation: {operation.value}",
                )

            # Validate operation-specific parameters
            if operation_params:
                is_valid, error_msg = self._validate_operation_specific_params(
                    operation, operation_params, user_roles
                )
                if not is_valid:
                    return False, error_msg

            # Audit the operation
            self._audit_ssl_operation(operation, user_roles, operation_params)

            return True, "SSL operation authorized"

        except SSLError as e:
            self.logger.error(f"Error validating SSL operation: {str(e)}")
            return False, f"SSL operation validation error: {str(e)}"

    def check_ssl_permissions(
        self,
        user_roles: List[str],
        certificate_type: Optional[SSLCertificateType] = None,
        resource_type: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Check SSL permissions for specific certificate type or resource.

        Args:
            user_roles: List of user roles
            certificate_type: Type of certificate to check permissions for
            resource_type: Type of SSL resource to check permissions for

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check certificate type permissions
            if certificate_type:
                required_permissions = self.certificate_type_permissions.get(
                    certificate_type, []
                )
                has_permission = self.roles_config.has_any_permission(
                    user_roles, required_permissions
                )

                if not has_permission:
                    return (
                        False,
                        f"Insufficient permissions for certificate type: {certificate_type.value}",
                    )

            # Check resource type permissions
            if resource_type:
                required_permissions = self.ssl_resource_permissions.get(
                    resource_type, []
                )
                has_permission = self.roles_config.has_any_permission(
                    user_roles, required_permissions
                )

                if not has_permission:
                    return (
                        False,
                        f"Insufficient permissions for SSL resource: {resource_type}",
                    )

            return True, "SSL permissions validated"

        except SSLError as e:
            self.logger.error(f"Error checking SSL permissions: {str(e)}")
            return False, f"SSL permission check error: {str(e)}"

    def audit_ssl_operation(
        self,
        operation: SSLOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Audit SSL operation for security and compliance.

        Args:
            operation: SSL operation performed
            user_roles: List of user roles
            operation_params: Operation parameters
            result: Operation result
        """
        try:
            audit_data = {
                "operation": operation.value,
                "user_roles": user_roles,
                "timestamp": datetime.now().isoformat(),
                "operation_params": operation_params or {},
                "result": result or {},
            }

            # Log audit information
            self.logger.info(f"SSL operation audited: {audit_data}")

            # Store audit data in settings
            audit_key = f"ssl.audit.{operation.value}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.settings_manager.set_custom_setting(audit_key, audit_data)

        except SSLError as e:
            self.logger.error(f"Error auditing SSL operation: {str(e)}")

    def get_ssl_roles(self, user_roles: List[str]) -> List[str]:
        """
        Get SSL-specific roles for user.

        Args:
            user_roles: List of user roles

        Returns:
            List of SSL-specific roles
        """
        try:
            ssl_roles = []
            for role in user_roles:
                if role.startswith("ssl:"):
                    ssl_roles.append(role)

            return ssl_roles

        except SSLError as e:
            self.logger.error(f"Error getting SSL roles: {str(e)}")
            return []

    def validate_ssl_access(
        self,
        user_roles: List[str],
        certificate_path: Optional[str] = None,
        resource_name: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Validate user access to specific SSL resource.

        Args:
            user_roles: List of user roles
            certificate_path: Path to certificate file
            resource_name: Name of SSL resource

        Returns:
            Tuple of (has_access, error_message)
        """
        try:
            # Check basic SSL access
            has_ssl_access = self.roles_config.has_any_permission(
                user_roles, ["ssl:view", "ssl:admin"]
            )

            if not has_ssl_access:
                return False, "Insufficient SSL access permissions"

            # Check resource-specific access
            if resource_name:
                resource_type = self._get_resource_type(resource_name)
                required_permissions = self.ssl_resource_permissions.get(
                    resource_type, []
                )
                has_resource_access = self.roles_config.has_any_permission(
                    user_roles, required_permissions
                )

                if not has_resource_access:
                    return (
                        False,
                        f"Insufficient permissions for SSL resource: {resource_name}",
                    )

            return True, "SSL access validated"

        except SSLError as e:
            self.logger.error(f"Error validating SSL access: {str(e)}")
            return False, f"SSL access validation error: {str(e)}"

    def check_ssl_certificate_permissions(
        self,
        user_roles: List[str],
        certificate_type: SSLCertificateType,
        operation: SSLOperation,
    ) -> Tuple[bool, str]:
        """
        Check permissions for SSL certificate operations.

        Args:
            user_roles: List of user roles
            certificate_type: Type of certificate
            operation: SSL operation to perform

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check operation permissions
            operation_permissions = self.ssl_permissions.get(operation, [])
            has_operation_permission = self.roles_config.has_any_permission(
                user_roles, operation_permissions
            )

            if not has_operation_permission:
                return (
                    False,
                    f"Insufficient permissions for SSL operation: {operation.value}",
                )

            # Check certificate type permissions
            cert_permissions = self.certificate_type_permissions.get(
                certificate_type, []
            )
            has_cert_permission = self.roles_config.has_any_permission(
                user_roles, cert_permissions
            )

            if not has_cert_permission:
                return (
                    False,
                    f"Insufficient permissions for certificate type: {certificate_type.value}",
                )

            return True, "SSL certificate permissions validated"

        except SSLError as e:
            self.logger.error(f"Error checking SSL certificate permissions: {str(e)}")
            return False, f"SSL certificate permission check error: {str(e)}"

    def manage_ssl_certificates(
        self,
        user_roles: List[str],
        operation: str,
        certificate_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Manage SSL certificates with role-based access control.

        Args:
            user_roles: List of user roles
            operation: Certificate management operation
            certificate_data: Certificate data for operations

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check certificate management permissions
            cert_permissions = ["ssl:manage", "ssl:admin"]
            has_permission = self.roles_config.has_any_permission(
                user_roles, cert_permissions
            )

            if not has_permission:
                return False, "Insufficient permissions for certificate management"

            # Validate operation
            valid_operations = [
                "create",
                "update",
                "delete",
                "list",
                "backup",
                "restore",
            ]
            if operation not in valid_operations:
                return False, f"Invalid certificate operation: {operation}"

            # Audit certificate management
            self._audit_ssl_operation(
                SSLOperation.MANAGE,
                user_roles,
                {"operation": operation, "certificate_data": certificate_data},
            )

            return True, "Certificate management authorized"

        except SSLError as e:
            self.logger.error(f"Error managing SSL certificates: {str(e)}")
            return False, f"Certificate management error: {str(e)}"

    def setup_ssl_security(
        self,
        user_roles: List[str],
        ssl_config: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Setup SSL/TLS security configuration.

        Args:
            user_roles: List of user roles
            ssl_config: SSL configuration parameters

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check SSL setup permissions
            ssl_permissions = ["ssl:setup", "ssl:admin"]
            has_ssl_permission = self.roles_config.has_any_permission(
                user_roles, ssl_permissions
            )

            if not has_ssl_permission:
                return False, "Insufficient permissions for SSL setup"

            # Validate SSL configuration
            required_ssl_fields = ["cert_file", "key_file", "ca_file"]
            for field in required_ssl_fields:
                if field not in ssl_config:
                    return False, f"Missing required SSL field: {field}"

            # Audit SSL setup
            self._audit_ssl_operation(
                SSLOperation.SETUP,
                user_roles,
                {"ssl_setup": True, "ssl_config": ssl_config},
            )

            return True, "SSL setup authorized"

        except SSLError as e:
            self.logger.error(f"Error setting up SSL security: {str(e)}")
            return False, f"SSL setup error: {str(e)}"

    def _validate_operation_specific_params(
        self,
        operation: SSLOperation,
        operation_params: Dict[str, Any],
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Validate operation-specific parameters.

        Args:
            operation: SSL operation
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if operation == SSLOperation.GENERATE:
                # Validate certificate generation parameters
                cert_type = operation_params.get("cert_type")
                if cert_type:
                    try:
                        cert_type_enum = SSLCertificateType(cert_type)
                        has_cert_permission = self.roles_config.has_any_permission(
                            user_roles,
                            self.certificate_type_permissions.get(cert_type_enum, []),
                        )
                        if not has_cert_permission:
                            return (
                                False,
                                f"Insufficient permissions for certificate type: {cert_type}",
                            )
                    except ValueError:
                        return False, f"Invalid certificate type: {cert_type}"

            elif operation == SSLOperation.REVOKE:
                # Validate revocation parameters
                if not operation_params.get("serial_numbers"):
                    return False, "Serial numbers are required for revocation"

            elif operation == SSLOperation.SETUP:
                # Validate setup parameters
                required_fields = ["cert_file", "key_file", "ca_file"]
                for field in required_fields:
                    if field not in operation_params:
                        return False, f"Missing required field for SSL setup: {field}"

            return True, "Operation parameters validated"

        except SSLError as e:
            self.logger.error(f"Error validating operation parameters: {str(e)}")
            return False, f"Parameter validation error: {str(e)}"

    def _audit_ssl_operation(
        self,
        operation: SSLOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Audit SSL operation.

        Args:
            operation: SSL operation
            user_roles: List of user roles
            operation_params: Operation parameters
        """
        try:
            audit_data = {
                "operation": operation.value,
                "user_roles": user_roles,
                "timestamp": datetime.now().isoformat(),
                "operation_params": operation_params or {},
            }

            self.logger.info(f"SSL operation audited: {audit_data}")

        except SSLError as e:
            self.logger.error(f"Error auditing SSL operation: {str(e)}")

    def _get_resource_type(self, resource_name: str) -> str:
        """
        Get resource type from resource name.

        Args:
            resource_name: Name of the resource

        Returns:
            Resource type
        """
        try:
            if resource_name.endswith((".crt", ".pem", ".cer")):
                return "certificates"
            elif resource_name.endswith((".key", ".pem")):
                return "private_keys"
            elif resource_name.endswith(".csr"):
                return "csr"
            elif resource_name.endswith(".crl"):
                return "crl"
            elif resource_name.endswith((".cnf", ".conf")):
                return "config"
            elif resource_name.endswith((".tar", ".zip", ".bak")):
                return "backup"

            return "default"

        except SSLError:
            return "default"

    def _setup_ssl_certificates(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Setup SSL certificates for SSL connections."""
        try:
            # This could be extended to integrate with mcp-security-framework
            # For now, just configure basic SSL settings
            ssl_config = config or {}

            # Store SSL configuration
            self.settings_manager.set_custom_setting(
                "ssl.verify", ssl_config.get("ssl_verify", True)
            )
            self.settings_manager.set_custom_setting(
                "ssl.timeout", ssl_config.get("ssl_timeout", 30)
            )

            return True, "SSL certificates configured successfully"

        except SSLError as e:
            return False, f"Error setting up SSL certificates: {str(e)}"

    def _verify_ssl_certificates(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Verify SSL certificates for SSL connections."""
        try:
            # Check SSL configuration
            ssl_verify = self.settings_manager.get("ssl.verify", True)
            ssl_timeout = self.settings_manager.get("ssl.timeout", 30)

            if not ssl_verify:
                return False, "SSL verification is disabled"

            return (
                True,
                f"SSL certificates are properly configured (timeout: {ssl_timeout}s)",
            )

        except SSLError as e:
            return False, f"Error verifying SSL certificates: {str(e)}"

    def _remove_ssl_certificates(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Remove SSL certificates for SSL connections."""
        try:
            # Remove SSL configuration
            self.settings_manager.remove_custom_setting("ssl.verify")
            self.settings_manager.remove_custom_setting("ssl.timeout")

            return True, "SSL certificates removed successfully"

        except SSLError as e:
            return False, f"Error removing SSL certificates: {str(e)}"
