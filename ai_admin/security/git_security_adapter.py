from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, PermissionError, SSLError, ValidationError
"""Git Security Adapter for AI Admin.

This module provides security integration for Git operations including
role-based access control, operation auditing, and permission validation.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import subprocess
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

import logging
from ai_admin.settings_manager import get_settings_manager
from ai_admin.config.roles_config import RolesConfig


class GitOperation(Enum):
    """Git operation types."""

    CLONE = "clone"
    PUSH = "push"
    PULL = "pull"
    FETCH = "fetch"
    COMMIT = "commit"
    BRANCH = "branch"
    CHECKOUT = "checkout"
    MERGE = "merge"
    REBASE = "rebase"
    RESET = "reset"
    REMOTE = "remote"
    ADD = "add"
    STATUS = "status"
    LOG = "log"
    DIFF = "diff"
    TAG = "tag"
    STASH = "stash"
    CLEAN = "clean"
    CONFIG = "config"
    GREP = "grep"
    BLAME = "blame"
    CHERRY_PICK = "cherry-pick"


class GitSecurityAdapter:
    """Security adapter for Git operations.

    This class provides:
    - Role-based access control for Git operations
    - Operation auditing and logging
    - Permission validation for Git repositories
    - Repository access validation
    - Branch permission checking
    - SSL/TLS certificate management
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize Git Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig()
        self.logger = logging.getLogger("ai_admin.git_security")

        # Git operation permissions mapping
        self.git_permissions = {
            GitOperation.CLONE: ["git:clone", "git:admin"],
            GitOperation.PUSH: ["git:push", "git:admin"],
            GitOperation.PULL: ["git:pull", "git:admin"],
            GitOperation.FETCH: ["git:fetch", "git:admin"],
            GitOperation.COMMIT: ["git:commit", "git:admin"],
            GitOperation.BRANCH: ["git:branch", "git:admin"],
            GitOperation.CHECKOUT: ["git:checkout", "git:admin"],
            GitOperation.MERGE: ["git:merge", "git:admin"],
            GitOperation.REBASE: ["git:rebase", "git:admin"],
            GitOperation.RESET: ["git:reset", "git:admin"],
            GitOperation.REMOTE: ["git:remote", "git:admin"],
            GitOperation.ADD: ["git:add", "git:admin"],
            GitOperation.STATUS: ["git:status", "git:admin"],
            GitOperation.LOG: ["git:log", "git:admin"],
            GitOperation.DIFF: ["git:diff", "git:admin"],
            GitOperation.TAG: ["git:tag", "git:admin"],
            GitOperation.STASH: ["git:stash", "git:admin"],
            GitOperation.CLEAN: ["git:clean", "git:admin"],
            GitOperation.CONFIG: ["git:config", "git:admin"],
            GitOperation.GREP: ["git:grep", "git:admin"],
            GitOperation.BLAME: ["git:blame", "git:admin"],
            GitOperation.CHERRY_PICK: ["git:cherry-pick", "git:admin"],
        }

        # Repository access permissions
        self.repository_permissions = {
            "github.com": ["git:repository:github.com"],
            "gitlab.com": ["git:repository:gitlab.com"],
            "bitbucket.org": ["git:repository:bitbucket.org"],
            "dev.azure.com": ["git:repository:azure.com"],
            "default": ["git:repository:default"],
        }

        # Branch protection levels
        self.branch_protection = {
            "main": ["git:branch:main", "git:admin"],
            "master": ["git:branch:master", "git:admin"],
            "develop": ["git:branch:develop", "git:admin"],
            "production": ["git:branch:production", "git:admin"],
            "default": ["git:branch:default"],
        }

    def validate_git_operation(
        self,
        operation: GitOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate if user has permission to perform Git operation.

        Args:
            operation: Git operation type
            user_roles: List of user roles
            operation_params: Operation parameters for additional validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.logger.info(f"Validating Git operation: {operation.value}")

            # Check basic operation permissions
            required_permissions = self.git_permissions.get(operation, [])
            if not required_permissions:
                return False, f"Unknown Git operation: {operation.value}"

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
            self.audit_git_operation(
                operation, user_roles, operation_params, "validated"
            )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating Git operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def check_git_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if user has required Git permissions.

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
            self.logger.error(f"Error checking Git permissions: {str(e)}")
            return False, required_permissions

    def audit_git_operation(
        self,
        operation: GitOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        status: str = "executed",
    ) -> None:
        """
        Audit Git operation for security monitoring.

        Args:
            operation: Git operation type
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
            self.logger.info(f"Git operation audited: {audit_data}")

            # Store audit data (could be extended to write to database)
            self._store_audit_data(audit_data)

        except CustomError as e:
            self.logger.error(f"Error auditing Git operation: {str(e)}")

    def get_git_roles(self) -> Dict[str, List[str]]:
        """
        Get Git-related roles and their permissions.

        Returns:
            Dictionary mapping roles to their Git permissions
        """
        try:
            git_roles = {}

            # Get all roles from configuration
            all_roles = self.roles_config.get_all_roles()

            for role_name, role_config in all_roles.items():
                role_permissions = role_config.get("permissions", [])
                git_permissions = [
                    perm for perm in role_permissions if perm.startswith("git:")
                ]

                if git_permissions:
                    git_roles[role_name] = git_permissions

            return git_roles

        except CustomError as e:
            self.logger.error(f"Error getting Git roles: {str(e)}")
            return {}

    def validate_git_repository_access(
        self, repository_url: str, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate user access to Git repository.

        Args:
            repository_url: Repository URL
            user_roles: List of user roles

        Returns:
            Tuple of (has_access, error_message)
        """
        try:
            # Extract repository hostname
            repository_host = self._extract_repository_host(repository_url)

            # Check repository-specific permissions
            required_permissions = self.repository_permissions.get(
                repository_host, self.repository_permissions["default"]
            )

            has_permission, missing_permissions = self.check_git_permissions(
                user_roles, required_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to repository {repository_host}. "
                    f"Missing permissions: {missing_permissions}",
                )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating repository access: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def check_git_branch_permissions(
        self, branch_name: str, operation: GitOperation, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Check permissions for specific Git branch operation.

        Args:
            branch_name: Git branch name
            operation: Git operation
            user_roles: List of user roles

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check if user has admin permissions (bypass branch-specific checks)
            if self._check_user_permissions(user_roles, ["git:admin"]):
                return True, ""

            # Check branch-specific permissions
            branch_permissions = self.branch_protection.get(
                branch_name, self.branch_protection["default"]
            )

            # For destructive operations, require higher permissions
            destructive_operations = [
                GitOperation.PUSH,
                GitOperation.RESET,
                GitOperation.REBASE,
                GitOperation.MERGE,
            ]

            if operation in destructive_operations:
                # Check if branch is protected
                if branch_name in self.branch_protection:
                    has_permission, missing_permissions = self.check_git_permissions(
                        user_roles, branch_permissions
                    )

                    if not has_permission:
                        return (
                            False,
                            f"Access denied to protected branch {branch_name}. "
                            f"Missing permissions: {missing_permissions}",
                        )

            return True, ""

        except PermissionError as e:
            error_msg = f"Error checking branch permissions: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def manage_git_certificates(
        self, repository_path: str, operation: str = "setup"
    ) -> Tuple[bool, str]:
        """
        Manage Git SSL/TLS certificates.

        Args:
            repository_path: Path to Git repository
            operation: Certificate operation (setup, verify, remove)

        Returns:
            Tuple of (success, message)
        """
        try:
            if operation == "setup":
                return self._setup_git_ssl_certificates(repository_path)
            elif operation == "verify":
                return self._verify_git_ssl_certificates(repository_path)
            elif operation == "remove":
                return self._remove_git_ssl_certificates(repository_path)
            else:
                return False, f"Unknown certificate operation: {operation}"

        except SSLError as e:
            error_msg = f"Error managing Git certificates: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def setup_git_ssl(
        self, repository_path: str, ssl_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Setup SSL/TLS configuration for Git repository.

        Args:
            repository_path: Path to Git repository
            ssl_config: SSL configuration parameters

        Returns:
            Tuple of (success, message)
        """
        try:
            if not os.path.exists(repository_path):
                return False, f"Repository path does not exist: {repository_path}"

            # Default SSL configuration
            default_config = {
                "ssl_verify": True,
                "ssl_cert_path": None,
                "ssl_key_path": None,
                "ssl_ca_path": None,
            }

            if ssl_config:
                default_config.update(ssl_config)

            # Configure Git SSL settings
            ssl_commands = [
                [
                    "git",
                    "config",
                    "http.sslVerify",
                    str(default_config["ssl_verify"]).lower(),
                ],
            ]

            if default_config["ssl_cert_path"]:
                ssl_commands.append(
                    ["git", "config", "http.sslCert", default_config["ssl_cert_path"]]
                )

            if default_config["ssl_key_path"]:
                ssl_commands.append(
                    ["git", "config", "http.sslKey", default_config["ssl_key_path"]]
                )

            if default_config["ssl_ca_path"]:
                ssl_commands.append(
                    ["git", "config", "http.sslCAInfo", default_config["ssl_ca_path"]]
                )

            # Execute SSL configuration commands
            for cmd in ssl_commands:
                result = subprocess.run(
                    cmd,
                    cwd=repository_path,
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    return False, f"Failed to configure SSL: {result.stderr}"

            self.logger.info(
                f"SSL configuration completed for repository: {repository_path}"
            )
            return True, "SSL configuration completed successfully"

        except ConfigurationError as e:
            error_msg = f"Error setting up Git SSL: {str(e)}"
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
        operation: GitOperation,
        operation_params: Dict[str, Any],
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Validate operation-specific parameters.

        Args:
            operation: Git operation
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if operation == GitOperation.CLONE:
                return self._validate_clone_operation(operation_params, user_roles)
            elif operation == GitOperation.PUSH:
                return self._validate_push_operation(operation_params, user_roles)
            elif operation == GitOperation.PULL:
                return self._validate_pull_operation(operation_params, user_roles)
            elif operation == GitOperation.BRANCH:
                return self._validate_branch_operation(operation_params, user_roles)

            return True, ""

        except ValidationError as e:
            return False, f"Error validating operation parameters: {str(e)}"

    def _validate_clone_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Git clone operation parameters."""
        try:
            repository_url = operation_params.get("repository_url", "")
            if not repository_url:
                return False, "Repository URL is required for clone operation"

            # Check repository access
            has_access, error_msg = self.validate_git_repository_access(
                repository_url, user_roles
            )
            if not has_access:
                return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating clone operation: {str(e)}"

    def _validate_push_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Git push operation parameters."""
        try:
            branch = operation_params.get("branch")
            if branch:
                has_permission, error_msg = self.check_git_branch_permissions(
                    branch, GitOperation.PUSH, user_roles
                )
                if not has_permission:
                    return False, error_msg

            # Check force push permissions
            force = operation_params.get("force", False)
            if force:
                if not self._check_user_permissions(
                    user_roles, ["git:force", "git:admin"]
                ):
                    return False, "Force push requires special permissions"

            return True, ""

        except ValidationError as e:
            return False, f"Error validating push operation: {str(e)}"

    def _validate_pull_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Git pull operation parameters."""
        try:
            branch = operation_params.get("branch")
            if branch:
                has_permission, error_msg = self.check_git_branch_permissions(
                    branch, GitOperation.PULL, user_roles
                )
                if not has_permission:
                    return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating pull operation: {str(e)}"

    def _validate_branch_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Git branch operation parameters."""
        try:
            branch_name = operation_params.get("branch_name", "")
            if branch_name:
                has_permission, error_msg = self.check_git_branch_permissions(
                    branch_name, GitOperation.BRANCH, user_roles
                )
                if not has_permission:
                    return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating branch operation: {str(e)}"

    def _extract_repository_host(self, repository_url: str) -> str:
        """Extract repository hostname from URL."""
        try:
            if "://" in repository_url:
                host_part = repository_url.split("://")[1].split("/")[0]
            else:
                host_part = repository_url.split("/")[0]

            # Handle SSH URLs
            if "@" in host_part:
                host_part = host_part.split("@")[1]

            return host_part
        except CustomError:
            return "unknown"

    def _setup_git_ssl_certificates(self, repository_path: str) -> Tuple[bool, str]:
        """Setup SSL certificates for Git repository."""
        try:
            # This could be extended to integrate with mcp-security-framework
            # For now, just configure basic SSL verification
            result = subprocess.run(
                ["git", "config", "http.sslVerify", "true"],
                cwd=repository_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return False, f"Failed to setup SSL certificates: {result.stderr}"

            return True, "SSL certificates configured successfully"

        except SSLError as e:
            return False, f"Error setting up SSL certificates: {str(e)}"

    def _verify_git_ssl_certificates(self, repository_path: str) -> Tuple[bool, str]:
        """Verify SSL certificates for Git repository."""
        try:
            # Check SSL configuration
            result = subprocess.run(
                ["git", "config", "--get", "http.sslVerify"],
                cwd=repository_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return False, "SSL verification not configured"

            ssl_verify = result.stdout.strip()
            if ssl_verify.lower() != "true":
                return False, f"SSL verification is disabled: {ssl_verify}"

            return True, "SSL certificates are properly configured"

        except SSLError as e:
            return False, f"Error verifying SSL certificates: {str(e)}"

    def _remove_git_ssl_certificates(self, repository_path: str) -> Tuple[bool, str]:
        """Remove SSL certificates configuration for Git repository."""
        try:
            # Remove SSL configuration
            ssl_configs = [
                "http.sslVerify",
                "http.sslCert",
                "http.sslKey",
                "http.sslCAInfo",
            ]

            for config in ssl_configs:
                subprocess.run(
                    ["git", "config", "--unset", config],
                    cwd=repository_path,
                    capture_output=True,
                )

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
