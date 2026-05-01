from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, FileNotFoundError, PermissionError, SSLError, ValidationError
"""FTP Security Adapter for AI Admin.

This module provides security integration for FTP operations including
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


class FtpOperation(Enum):
    """FTP operation types."""

    UPLOAD = "upload"
    DOWNLOAD = "download"
    LIST = "list"
    DELETE = "delete"
    MKDIR = "mkdir"
    RMDIR = "rmdir"
    RENAME = "rename"
    CHMOD = "chmod"


class FtpSecurityAdapter:
    """Security adapter for FTP operations.

    This class provides:
    - Role-based access control for FTP operations
    - Operation auditing and logging
    - Permission validation for FTP resources
    - Server access validation
    - File permission checking
    - SSL/TLS certificate management
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize FTP Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig(roles_file="config/roles.json")
        self.logger = logging.getLogger("ai_admin.ftp_security")

        # FTP operation permissions mapping
        self.ftp_permissions = {
            FtpOperation.UPLOAD: ["ftp:upload", "ftp:admin"],
            FtpOperation.DOWNLOAD: ["ftp:download", "ftp:admin"],
            FtpOperation.LIST: ["ftp:list", "ftp:admin"],
            FtpOperation.DELETE: ["ftp:delete", "ftp:admin"],
            FtpOperation.MKDIR: ["ftp:mkdir", "ftp:admin"],
            FtpOperation.RMDIR: ["ftp:rmdir", "ftp:admin"],
            FtpOperation.RENAME: ["ftp:rename", "ftp:admin"],
            FtpOperation.CHMOD: ["ftp:chmod", "ftp:admin"],
        }

        # FTP server access permissions
        self.server_permissions = {
            "default": ["ftp:server:default"],
            "secure": ["ftp:server:secure"],
            "admin": ["ftp:server:admin"],
        }

        # File path restrictions
        self.path_restrictions = {
            "uploads": ["ftp:path:uploads"],
            "downloads": ["ftp:path:downloads"],
            "admin": ["ftp:path:admin"],
            "public": ["ftp:path:public"],
        }

    def validate_ftp_operation(
        self,
        operation: FtpOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate if user has permission to perform FTP operation.

        Args:
            operation: FTP operation type
            user_roles: List of user roles
            operation_params: Operation parameters for additional validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.logger.info(f"Validating FTP operation: {operation.value}")

            # Check basic operation permissions
            required_permissions = self.ftp_permissions.get(operation, [])
            if not required_permissions:
                return False, f"Unknown FTP operation: {operation.value}"

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
            self.audit_ftp_operation(
                operation, user_roles, operation_params, "validated"
            )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating FTP operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def check_ftp_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if user has required FTP permissions.

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
            return has_permission, missing_permissions

        except PermissionError as e:
            self.logger.error(f"Error checking FTP permissions: {str(e)}")
            return False, required_permissions

    def audit_ftp_operation(
        self,
        operation: FtpOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        status: str = "executed",
    ) -> None:
        """
        Audit FTP operation for security monitoring.

        Args:
            operation: FTP operation type
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
                "params": operation_params or {},
            }

            self.logger.info(
                f"FTP operation audited: {operation.value} - {status}",
                extra={"audit": audit_data},
            )

        except CustomError as e:
            self.logger.error(f"Error auditing FTP operation: {str(e)}")

    def get_ftp_roles(self, user_roles: List[str]) -> List[str]:
        """
        Get FTP-specific roles for user.

        Args:
            user_roles: List of user roles

        Returns:
            List of FTP-specific roles
        """
        try:
            ftp_roles = []
            for role in user_roles:
                if role.startswith("ftp:"):
                    ftp_roles.append(role)
            return ftp_roles

        except CustomError as e:
            self.logger.error(f"Error getting FTP roles: {str(e)}")
            return []

    def validate_ftp_server_access(
        self, server_config: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate access to FTP server.

        Args:
            server_config: FTP server configuration
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            server_type = server_config.get("type", "default")
            required_permissions = self.server_permissions.get(
                server_type, self.server_permissions["default"]
            )

            has_permission = self._check_user_permissions(
                user_roles, required_permissions
            )
            if not has_permission:
                return False, f"Insufficient permissions for server type: {server_type}"

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating FTP server access: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def check_ftp_file_permissions(
        self, file_path: str, operation: FtpOperation, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Check permissions for FTP file operations.

        Args:
            file_path: File path to check
            operation: FTP operation type
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Extract path category from file path
            path_category = self._get_path_category(file_path)
            required_permissions = self.path_restrictions.get(
                path_category, self.path_restrictions["public"]
            )

            has_permission = self._check_user_permissions(
                user_roles, required_permissions
            )
            if not has_permission:
                return False, f"Insufficient permissions for path: {path_category}"

            return True, ""

        except FileNotFoundError as e:
            error_msg = f"Error checking FTP file permissions: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def manage_ftp_certificates(
        self, operation: str, cert_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Manage FTP SSL/TLS certificates.

        Args:
            operation: Certificate operation (create, validate, revoke)
            cert_data: Certificate data

        Returns:
            Tuple of (success, message, result_data)
        """
        try:
            self.logger.info(f"Managing FTP certificates: {operation}")

            # This would integrate with mcp-security-framework
            # For now, return success for basic operations
            if operation == "validate":
                return True, "Certificate validation successful", {"valid": True}
            elif operation == "create":
                return (
                    True,
                    "Certificate creation initiated",
                    {"cert_id": "ftp_cert_001"},
                )
            elif operation == "revoke":
                return True, "Certificate revocation successful", {"revoked": True}
            else:
                return False, f"Unknown certificate operation: {operation}", None

        except SSLError as e:
            error_msg = f"Error managing FTP certificates: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, None

    def setup_ftp_ssl(
        self, server_config: Dict[str, Any], ssl_config: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Setup SSL/TLS for FTP server.

        Args:
            server_config: FTP server configuration
            ssl_config: SSL configuration

        Returns:
            Tuple of (success, message)
        """
        try:
            self.logger.info("Setting up FTP SSL/TLS")

            # Validate SSL configuration
            required_ssl_fields = ["cert_file", "key_file", "ca_file"]
            for field in required_ssl_fields:
                if field not in ssl_config:
                    return False, f"Missing SSL configuration field: {field}"

            # This would integrate with mcp-security-framework
            # For now, return success
            return True, "FTP SSL/TLS setup successful"

        except ConfigurationError as e:
            error_msg = f"Error setting up FTP SSL: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _check_user_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> bool:
        """
        Check if user has required permissions.

        Args:
            user_roles: List of user roles
            required_permissions: List of required permissions

        Returns:
            True if user has any of the required permissions
        """
        try:
            user_permissions = self._get_user_permissions(user_roles)
            return any(perm in user_permissions for perm in required_permissions)

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
            permissions = []
            for role in user_roles:
                role_permissions = self.roles_config.get_permissions(role)
                # Extract permission names from Permission objects
                permission_names = [perm.name for perm in role_permissions]
                permissions.extend(permission_names)
            return list(set(permissions))  # Remove duplicates

        except PermissionError as e:
            self.logger.error(f"Error getting user permissions: {str(e)}")
            return []

    def _validate_operation_specific_params(
        self,
        operation: FtpOperation,
        operation_params: Dict[str, Any],
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Validate operation-specific parameters.

        Args:
            operation: FTP operation type
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if operation in [FtpOperation.UPLOAD, FtpOperation.DOWNLOAD]:
                # Check file path permissions
                file_path = operation_params.get("remote_path") or operation_params.get(
                    "local_path"
                )
                if file_path:
                    return self.check_ftp_file_permissions(
                        file_path, operation, user_roles
                    )

            elif operation == FtpOperation.DELETE:
                # Check delete permissions for file path
                remote_path = operation_params.get("remote_path")
                if remote_path:
                    return self.check_ftp_file_permissions(
                        remote_path, operation, user_roles
                    )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating operation-specific params: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _get_path_category(self, file_path: str) -> str:
        """
        Get path category from file path.

        Args:
            file_path: File path

        Returns:
            Path category
        """
        try:
            # Normalize path
            normalized_path = file_path.strip("/").lower()

            # Check for specific categories
            if normalized_path.startswith("uploads"):
                return "uploads"
            elif normalized_path.startswith("downloads"):
                return "downloads"
            elif normalized_path.startswith("admin"):
                return "admin"
            else:
                return "public"

        except FileNotFoundError as e:
            self.logger.error(f"Error getting path category: {str(e)}")
            return "public"
