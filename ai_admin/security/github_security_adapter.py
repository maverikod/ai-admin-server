from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, PermissionError, SSLError, ValidationError
"""GitHub Security Adapter for AI Admin.

This module provides security integration for GitHub operations including
role-based access control, operation auditing, and permission validation.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

import logging
from ai_admin.settings_manager import get_settings_manager
from ai_admin.config.roles_config import RolesConfig


class GitHubOperation(Enum):
    """GitHub operation types."""

    CREATE_REPO = "create_repo"
    LIST_REPOS = "list_repos"
    DELETE_REPO = "delete_repo"
    UPDATE_REPO = "update_repo"
    GET_REPO = "get_repo"
    CLONE_REPO = "clone_repo"
    FORK_REPO = "fork_repo"
    CREATE_BRANCH = "create_branch"
    DELETE_BRANCH = "delete_branch"
    CREATE_PULL_REQUEST = "create_pull_request"
    MERGE_PULL_REQUEST = "merge_pull_request"
    CREATE_ISSUE = "create_issue"
    UPDATE_ISSUE = "update_issue"
    CREATE_WIKI = "create_wiki"
    UPDATE_WIKI = "update_wiki"
    MANAGE_WEBHOOKS = "manage_webhooks"
    MANAGE_COLLABORATORS = "manage_collaborators"
    MANAGE_TEAMS = "manage_teams"
    API_ACCESS = "api_access"


class GitHubSecurityAdapter:
    """Security adapter for GitHub operations.

    This class provides:
    - Role-based access control for GitHub operations
    - Operation auditing and logging
    - Permission validation for GitHub repositories
    - Repository access validation
    - Branch permission checking
    - SSL/TLS certificate management for GitHub connections
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize GitHub Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig()
        self.logger = logging.getLogger("ai_admin.github_security")

        # GitHub operation permissions mapping
        self.github_permissions = {
            GitHubOperation.CREATE_REPO: [
                "github:create_repo",
                "github:admin",
            ],
            GitHubOperation.LIST_REPOS: ["github:list_repos", "github:admin"],
            GitHubOperation.DELETE_REPO: [
                "github:delete_repo",
                "github:admin",
            ],
            GitHubOperation.UPDATE_REPO: [
                "github:update_repo",
                "github:admin",
            ],
            GitHubOperation.GET_REPO: ["github:get_repo", "github:admin"],
            GitHubOperation.CLONE_REPO: ["github:clone_repo", "github:admin"],
            GitHubOperation.FORK_REPO: ["github:fork_repo", "github:admin"],
            GitHubOperation.CREATE_BRANCH: [
                "github:create_branch",
                "github:admin",
            ],
            GitHubOperation.DELETE_BRANCH: [
                "github:delete_branch",
                "github:admin",
            ],
            GitHubOperation.CREATE_PULL_REQUEST: [
                "github:create_pr",
                "github:admin",
            ],
            GitHubOperation.MERGE_PULL_REQUEST: [
                "github:merge_pr",
                "github:admin",
            ],
            GitHubOperation.CREATE_ISSUE: [
                "github:create_issue",
                "github:admin",
            ],
            GitHubOperation.UPDATE_ISSUE: [
                "github:update_issue",
                "github:admin",
            ],
            GitHubOperation.CREATE_WIKI: [
                "github:create_wiki",
                "github:admin",
            ],
            GitHubOperation.UPDATE_WIKI: [
                "github:update_wiki",
                "github:admin",
            ],
            GitHubOperation.MANAGE_WEBHOOKS: [
                "github:manage_webhooks",
                "github:admin",
            ],
            GitHubOperation.MANAGE_COLLABORATORS: [
                "github:manage_collaborators",
                "github:admin",
            ],
            GitHubOperation.MANAGE_TEAMS: [
                "github:manage_teams",
                "github:admin",
            ],
            GitHubOperation.API_ACCESS: ["github:api", "github:admin"],
        }

        # GitHub repository access permissions
        self.repository_permissions = {
            "public": ["github:repository:public"],
            "private": ["github:repository:private", "github:admin"],
            "organization": ["github:repository:organization", "github:admin"],
            "enterprise": ["github:repository:enterprise", "github:admin"],
        }

        # GitHub organization permissions
        self.organization_permissions = {
            "read": ["github:org:read"],
            "write": ["github:org:write", "github:admin"],
            "admin": ["github:org:admin", "github:admin"],
        }

        # GitHub API access permissions
        self.api_permissions = {
            "read": ["github:api:read"],
            "write": ["github:api:write", "github:admin"],
            "admin": ["github:api:admin", "github:admin"],
        }

    def validate_github_operation(
        self,
        operation: GitHubOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate if user has permission to perform GitHub operation.

        Args:
            operation: GitHub operation type
            user_roles: List of user roles
            operation_params: Operation parameters for additional validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.logger.info(f"Validating GitHub operation: {operation.value}")

            # Check basic operation permissions
            required_permissions = self.github_permissions.get(operation, [])
            if not required_permissions:
                return False, f"Unknown GitHub operation: {operation.value}"

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
            self.audit_github_operation(
                operation, user_roles, operation_params, "validated"
            )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating GitHub operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def check_github_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if user has required GitHub permissions.

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
            self.logger.error(f"Error checking GitHub permissions: {str(e)}")
            return False, required_permissions

    def audit_github_operation(
        self,
        operation: GitHubOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        status: str = "executed",
    ) -> None:
        """
        Audit GitHub operation for security monitoring.

        Args:
            operation: GitHub operation type
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
            self.logger.info(f"GitHub operation audited: {audit_data}")

            # Store audit data (could be extended to write to database)
            self._store_audit_data(audit_data)

        except CustomError as e:
            self.logger.error(f"Error auditing GitHub operation: {str(e)}")

    def get_github_roles(self) -> Dict[str, List[str]]:
        """
        Get GitHub-related roles and their permissions.

        Returns:
            Dictionary mapping roles to their GitHub permissions
        """
        try:
            github_roles = {}

            # Get all roles from configuration
            all_roles = self.roles_config.get_all_roles()

            for role_name, role_config in all_roles.items():
                role_permissions = role_config.get("permissions", [])
                github_permissions = [
                    perm for perm in role_permissions if perm.startswith("github:")
                ]

                if github_permissions:
                    github_roles[role_name] = github_permissions

            return github_roles

        except CustomError as e:
            self.logger.error(f"Error getting GitHub roles: {str(e)}")
            return {}

    def validate_github_api_access(
        self, api_endpoint: str, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate user access to GitHub API endpoint.

        Args:
            api_endpoint: GitHub API endpoint
            user_roles: List of user roles

        Returns:
            Tuple of (has_access, error_message)
        """
        try:
            # Determine required API permissions based on endpoint
            if "/repos" in api_endpoint:
                if (
                    "POST" in api_endpoint
                    or "PUT" in api_endpoint
                    or "DELETE" in api_endpoint
                ):
                    required_permissions = self.api_permissions["write"]
                else:
                    required_permissions = self.api_permissions["read"]
            elif "/user" in api_endpoint:
                required_permissions = self.api_permissions["read"]
            elif "/orgs" in api_endpoint:
                required_permissions = self.api_permissions["admin"]
            else:
                required_permissions = self.api_permissions["read"]

            has_permission, missing_permissions = self.check_github_permissions(
                user_roles, required_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to GitHub API endpoint {api_endpoint}. "
                    f"Missing permissions: {missing_permissions}",
                )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating GitHub API access: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def check_github_repo_permissions(
        self, repo_name: str, operation: GitHubOperation, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Check permissions for specific GitHub repository operation.

        Args:
            repo_name: GitHub repository name
            operation: GitHub operation
            user_roles: List of user roles

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check if user has admin permissions (bypass repository-specific checks)
            if self._check_user_permissions(user_roles, ["github:admin"]):
                return True, ""

            # Check repository-specific permissions
            if "private" in repo_name.lower():
                required_permissions = self.repository_permissions["private"]
            elif "org" in repo_name.lower() or "/" in repo_name:
                required_permissions = self.repository_permissions["organization"]
            else:
                required_permissions = self.repository_permissions["public"]

            # For destructive operations, require higher permissions
            destructive_operations = [
                GitHubOperation.DELETE_REPO,
                GitHubOperation.DELETE_BRANCH,
                GitHubOperation.MERGE_PULL_REQUEST,
                GitHubOperation.MANAGE_WEBHOOKS,
                GitHubOperation.MANAGE_COLLABORATORS,
            ]

            if operation in destructive_operations:
                has_permission, missing_permissions = self.check_github_permissions(
                    user_roles, required_permissions
                )

                if not has_permission:
                    return (
                        False,
                        f"Access denied to repository {repo_name} for operation {operation.value}. "
                        f"Missing permissions: {missing_permissions}",
                    )

            return True, ""

        except PermissionError as e:
            error_msg = f"Error checking GitHub repository permissions: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def manage_github_certificates(
        self,
        operation: str = "setup",
        cert_config: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Manage GitHub SSL/TLS certificates.

        Args:
            operation: Certificate operation (setup, verify, remove)
            cert_config: Certificate configuration

        Returns:
            Tuple of (success, message)
        """
        try:
            if operation == "setup":
                return self._setup_github_ssl_certificates(cert_config)
            elif operation == "verify":
                return self._verify_github_ssl_certificates()
            elif operation == "remove":
                return self._remove_github_ssl_certificates()
            else:
                return False, f"Unknown certificate operation: {operation}"

        except SSLError as e:
            error_msg = f"Error managing GitHub certificates: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def setup_github_ssl(
        self, ssl_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Setup SSL/TLS configuration for GitHub connections.

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
                "github_api_ssl": True,
            }

            if ssl_config:
                default_config.update(ssl_config)

            # Configure GitHub SSL settings
            ssl_commands = []

            # Configure curl SSL settings for GitHub API
            if default_config["ssl_verify"]:
                ssl_commands.append(["curl", "--config", "-", "--version"])

            # Configure Git SSL settings for GitHub repositories
            git_ssl_commands = [
                [
                    "git",
                    "config",
                    "--global",
                    "http.sslVerify",
                    str(default_config["ssl_verify"]).lower(),
                ],
            ]

            if default_config["ssl_cert_path"]:
                git_ssl_commands.append(
                    [
                        "git",
                        "config",
                        "--global",
                        "http.sslCert",
                        default_config["ssl_cert_path"],
                    ]
                )

            if default_config["ssl_key_path"]:
                git_ssl_commands.append(
                    [
                        "git",
                        "config",
                        "--global",
                        "http.sslKey",
                        default_config["ssl_key_path"],
                    ]
                )

            if default_config["ssl_ca_path"]:
                git_ssl_commands.append(
                    [
                        "git",
                        "config",
                        "--global",
                        "http.sslCAInfo",
                        default_config["ssl_ca_path"],
                    ]
                )

            # Execute Git SSL configuration commands
            for cmd in git_ssl_commands:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    return (
                        False,
                        f"Failed to configure Git SSL: {result.stderr}",
                    )

            self.logger.info("GitHub SSL configuration completed successfully")
            return True, "GitHub SSL configuration completed successfully"

        except ConfigurationError as e:
            error_msg = f"Error setting up GitHub SSL: {str(e)}"
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
        operation: GitHubOperation,
        operation_params: Dict[str, Any],
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Validate operation-specific parameters.

        Args:
            operation: GitHub operation
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if operation == GitHubOperation.CREATE_REPO:
                return self._validate_create_repo_operation(
                    operation_params, user_roles
                )
            elif operation == GitHubOperation.DELETE_REPO:
                return self._validate_delete_repo_operation(
                    operation_params, user_roles
                )
            elif operation == GitHubOperation.CREATE_PULL_REQUEST:
                return self._validate_create_pr_operation(operation_params, user_roles)
            elif operation == GitHubOperation.MERGE_PULL_REQUEST:
                return self._validate_merge_pr_operation(operation_params, user_roles)

            return True, ""

        except ValidationError as e:
            return False, f"Error validating operation parameters: {str(e)}"

    def _validate_create_repo_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate GitHub create repository operation parameters."""
        try:
            repo_name = operation_params.get("repo_name", "")
            if not repo_name:
                return (
                    False,
                    "Repository name is required for create repository operation",
                )

            # Check if user can create repositories
            has_permission, missing_permissions = self.check_github_permissions(
                user_roles, ["github:create_repo", "github:admin"]
            )
            if not has_permission:
                return (
                    False,
                    f"Missing permissions to create repository: {missing_permissions}",
                )

            # Check private repository permissions
            is_private = operation_params.get("private", False)
            if is_private:
                has_private_permission, missing_private_permissions = (
                    self.check_github_permissions(
                        user_roles,
                        ["github:repository:private", "github:admin"],
                    )
                )
                if not has_private_permission:
                    return (
                        False,
                        f"Missing permissions to create private repository: {missing_private_permissions}",
                    )

            return True, ""

        except ValidationError as e:
            return (
                False,
                f"Error validating create repository operation: {str(e)}",
            )

    def _validate_delete_repo_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate GitHub delete repository operation parameters."""
        try:
            repo_name = operation_params.get("repo_name", "")
            if not repo_name:
                return (
                    False,
                    "Repository name is required for delete repository operation",
                )

            # Check repository permissions
            has_permission, error_msg = self.check_github_repo_permissions(
                repo_name, GitHubOperation.DELETE_REPO, user_roles
            )
            if not has_permission:
                return False, error_msg

            return True, ""

        except ValidationError as e:
            return (
                False,
                f"Error validating delete repository operation: {str(e)}",
            )

    def _validate_create_pr_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate GitHub create pull request operation parameters."""
        try:
            repo_name = operation_params.get("repo_name", "")
            if not repo_name:
                return (
                    False,
                    "Repository name is required for create pull request operation",
                )

            # Check repository permissions
            has_permission, error_msg = self.check_github_repo_permissions(
                repo_name, GitHubOperation.CREATE_PULL_REQUEST, user_roles
            )
            if not has_permission:
                return False, error_msg

            return True, ""

        except ValidationError as e:
            return (
                False,
                f"Error validating create pull request operation: {str(e)}",
            )

    def _validate_merge_pr_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate GitHub merge pull request operation parameters."""
        try:
            repo_name = operation_params.get("repo_name", "")
            if not repo_name:
                return (
                    False,
                    "Repository name is required for merge pull request operation",
                )

            # Check repository permissions
            has_permission, error_msg = self.check_github_repo_permissions(
                repo_name, GitHubOperation.MERGE_PULL_REQUEST, user_roles
            )
            if not has_permission:
                return False, error_msg

            return True, ""

        except ValidationError as e:
            return (
                False,
                f"Error validating merge pull request operation: {str(e)}",
            )

    def _setup_github_ssl_certificates(
        self, cert_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Setup SSL certificates for GitHub connections."""
        try:
            # This could be extended to integrate with mcp-security-framework
            # For now, just configure basic SSL verification
            result = subprocess.run(
                ["git", "config", "--global", "http.sslVerify", "true"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return (
                    False,
                    f"Failed to setup GitHub SSL certificates: {result.stderr}",
                )

            return True, "GitHub SSL certificates configured successfully"

        except SSLError as e:
            return False, f"Error setting up GitHub SSL certificates: {str(e)}"

    def _verify_github_ssl_certificates(self) -> Tuple[bool, str]:
        """Verify SSL certificates for GitHub connections."""
        try:
            # Check SSL configuration
            result = subprocess.run(
                ["git", "config", "--global", "--get", "http.sslVerify"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return False, "GitHub SSL verification not configured"

            ssl_verify = result.stdout.strip()
            if ssl_verify.lower() != "true":
                return (
                    False,
                    f"GitHub SSL verification is disabled: {ssl_verify}",
                )

            return True, "GitHub SSL certificates are properly configured"

        except SSLError as e:
            return False, f"Error verifying GitHub SSL certificates: {str(e)}"

    def _remove_github_ssl_certificates(self) -> Tuple[bool, str]:
        """Remove SSL certificates configuration for GitHub connections."""
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
                    ["git", "config", "--global", "--unset", config],
                    capture_output=True,
                )

            return True, "GitHub SSL certificates configuration removed"

        except SSLError as e:
            return False, f"Error removing GitHub SSL certificates: {str(e)}"

    def _store_audit_data(self, audit_data: Dict[str, Any]) -> None:
        """
        Store audit data for security monitoring.

        Args:
            audit_data: Audit data to store
        """
        try:
            # This could be extended to write to database or external system
            # For now, just log the data
            self.logger.info(f"GitHub audit data stored: {audit_data}")

        except CustomError as e:
            self.logger.error(f"Error storing GitHub audit data: {str(e)}")
