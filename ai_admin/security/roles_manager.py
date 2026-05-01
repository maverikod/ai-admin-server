from ai_admin.core.custom_exceptions import CustomError, FileNotFoundError, PermissionError, ValidationError
"""Roles Manager for AI Admin.

This module provides unified roles management for all components,
ensuring consistent role-based access control across the system.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import json
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

import logging
from ai_admin.settings_manager import get_settings_manager
from ai_admin.config.roles_config import RolesConfig


class RolesManager:
    """Unified roles management for all components.

    This class provides:
    - Centralized role management across all components
    - Role hierarchy and inheritance
    - Permission mapping and validation
    - Component-specific role filtering
    - Role-based access control validation
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize Roles Manager.

        Args:
            config: Configuration dictionary
            roles_config: Roles configuration instance
        """
        self.config = config or {}
        self.roles_config = roles_config or RolesConfig()
        self.logger = logging.getLogger("ai_admin.roles_manager")
        self.settings_manager = get_settings_manager()

        # Load roles from configuration
        self.roles = self._load_roles()

        # Component-specific role mappings
        self.component_roles = self._load_component_roles()

        # Role hierarchy
        self.role_hierarchy = self._load_role_hierarchy()

    def _load_roles(self) -> Dict[str, Dict[str, Any]]:
        """
        Load roles from configuration.

        Returns:
            Dictionary of roles and their configurations
        """
        try:
            # Get roles from roles_config
            all_roles = self.roles_config.get_all_roles()

            # Add default roles if not present
            default_roles = self._get_default_roles()
            for role_name, role_config in default_roles.items():
                if role_name not in all_roles:
                    all_roles[role_name] = role_config

            self.logger.info(f"Loaded {len(all_roles)} roles")
            return all_roles

        except CustomError as e:
            self.logger.error(f"Error loading roles: {str(e)}")
            return self._get_default_roles()

    def _load_component_roles(self) -> Dict[str, List[str]]:
        """
        Load component-specific role mappings.

        Returns:
            Dictionary mapping components to their available roles
        """
        try:
            component_roles = {
                "docker": ["docker_admin", "docker_user", "docker_readonly"],
                "k8s": ["k8s_admin", "k8s_user", "k8s_readonly"],
                "kubernetes": ["k8s_admin", "k8s_user", "k8s_readonly"],
                "ftp": ["ftp_admin", "ftp_user", "ftp_readonly"],
                "git": ["git_admin", "git_user", "git_readonly"],
                "github": ["github_admin", "github_user", "github_readonly"],
                "vast": ["vast_admin", "vast_user", "vast_readonly"],
                "vast_ai": ["vast_admin", "vast_user", "vast_readonly"],
                "system": ["system_admin", "system_user", "system_readonly"],
                "queue": ["queue_admin", "queue_user", "queue_readonly"],
                "ssl": ["ssl_admin", "ssl_user", "ssl_readonly"],
                "vector_store": [
                    "vector_store_admin",
                    "vector_store_user",
                    "vector_store_readonly",
                ],
                "llm": ["llm_admin", "llm_user", "llm_readonly"],
                "test": ["test_admin", "test_user", "test_readonly"],
                "kind": ["kind_admin", "kind_user", "kind_readonly"],
                "argocd": ["argocd_admin", "argocd_user", "argocd_readonly"],
            }

            # Load from configuration if available
            config_component_roles = self.config.get("component_roles", {})
            component_roles.update(config_component_roles)

            return component_roles

        except CustomError as e:
            self.logger.error(f"Error loading component roles: {str(e)}")
            return {}

    def _load_role_hierarchy(self) -> Dict[str, List[str]]:
        """
        Load role hierarchy for inheritance.

        Returns:
            Dictionary mapping roles to their parent roles
        """
        try:
            role_hierarchy = {
                "admin": [],
                "user": ["admin"],
                "readonly": ["user", "admin"],
                "docker_admin": ["admin"],
                "docker_user": ["user", "docker_admin"],
                "docker_readonly": ["readonly", "docker_user", "docker_admin"],
                "k8s_admin": ["admin"],
                "k8s_user": ["user", "k8s_admin"],
                "k8s_readonly": ["readonly", "k8s_user", "k8s_admin"],
                "ftp_admin": ["admin"],
                "ftp_user": ["user", "ftp_admin"],
                "ftp_readonly": ["readonly", "ftp_user", "ftp_admin"],
                "git_admin": ["admin"],
                "git_user": ["user", "git_admin"],
                "git_readonly": ["readonly", "git_user", "git_admin"],
                "github_admin": ["admin"],
                "github_user": ["user", "github_admin"],
                "github_readonly": ["readonly", "github_user", "github_admin"],
                "vast_admin": ["admin"],
                "vast_user": ["user", "vast_admin"],
                "vast_readonly": ["readonly", "vast_user", "vast_admin"],
                "system_admin": ["admin"],
                "system_user": ["user", "system_admin"],
                "system_readonly": ["readonly", "system_user", "system_admin"],
                "queue_admin": ["admin"],
                "queue_user": ["user", "queue_admin"],
                "queue_readonly": ["readonly", "queue_user", "queue_admin"],
                "ssl_admin": ["admin"],
                "ssl_user": ["user", "ssl_admin"],
                "ssl_readonly": ["readonly", "ssl_user", "ssl_admin"],
                "vector_store_admin": ["admin"],
                "vector_store_user": ["user", "vector_store_admin"],
                "vector_store_readonly": [
                    "readonly",
                    "vector_store_user",
                    "vector_store_admin",
                ],
                "llm_admin": ["admin"],
                "llm_user": ["user", "llm_admin"],
                "llm_readonly": ["readonly", "llm_user", "llm_admin"],
                "test_admin": ["admin"],
                "test_user": ["user", "test_admin"],
                "test_readonly": ["readonly", "test_user", "test_admin"],
                "kind_admin": ["admin"],
                "kind_user": ["user", "kind_admin"],
                "kind_readonly": ["readonly", "kind_user", "kind_admin"],
                "argocd_admin": ["admin"],
                "argocd_user": ["user", "argocd_admin"],
                "argocd_readonly": ["readonly", "argocd_user", "argocd_admin"],
            }

            # Load from configuration if available
            config_hierarchy = self.config.get("role_hierarchy", {})
            role_hierarchy.update(config_hierarchy)

            return role_hierarchy

        except CustomError as e:
            self.logger.error(f"Error loading role hierarchy: {str(e)}")
            return {}

    def _get_default_roles(self) -> Dict[str, Dict[str, Any]]:
        """
        Get default roles configuration.

        Returns:
            Dictionary of default roles
        """
        return {
            "admin": {
                "description": "Full administrative access to all components",
                "permissions": ["*"],
                "category": "system",
                "level": 100,
            },
            "user": {
                "description": "Standard user access with limited permissions",
                "permissions": ["read", "write"],
                "category": "system",
                "level": 50,
            },
            "readonly": {
                "description": "Read-only access to components",
                "permissions": ["read"],
                "category": "system",
                "level": 10,
            },
            "docker_admin": {
                "description": "Docker administration access",
                "permissions": ["docker:*"],
                "category": "docker",
                "level": 90,
            },
            "docker_user": {
                "description": "Docker user access",
                "permissions": ["docker:run", "docker:pull", "docker:push"],
                "category": "docker",
                "level": 60,
            },
            "docker_readonly": {
                "description": "Docker read-only access",
                "permissions": ["docker:inspect", "docker:logs"],
                "category": "docker",
                "level": 20,
            },
            "k8s_admin": {
                "description": "Kubernetes administration access",
                "permissions": ["k8s:*"],
                "category": "kubernetes",
                "level": 90,
            },
            "k8s_user": {
                "description": "Kubernetes user access",
                "permissions": ["k8s:deploy", "k8s:get", "k8s:list"],
                "category": "kubernetes",
                "level": 60,
            },
            "k8s_readonly": {
                "description": "Kubernetes read-only access",
                "permissions": ["k8s:get", "k8s:list"],
                "category": "kubernetes",
                "level": 20,
            },
            "ssl_admin": {
                "description": "SSL/TLS administration access",
                "permissions": ["ssl:*"],
                "category": "ssl",
                "level": 90,
            },
            "ssl_user": {
                "description": "SSL/TLS user access",
                "permissions": ["ssl:view", "ssl:verify"],
                "category": "ssl",
                "level": 60,
            },
            "ssl_readonly": {
                "description": "SSL/TLS read-only access",
                "permissions": ["ssl:view"],
                "category": "ssl",
                "level": 20,
            },
        }

    def get_roles_for_component(self, component: str) -> List[str]:
        """
        Get available roles for component.

        Args:
            component: Component name

        Returns:
            List of available roles for the component
        """
        try:
            component_roles = self.component_roles.get(component, [])

            # Add inherited roles
            all_roles = set(component_roles)
            for role in component_roles:
                inherited_roles = self._get_inherited_roles(role)
                all_roles.update(inherited_roles)

            return list(all_roles)

        except CustomError as e:
            self.logger.error(
                f"Error getting roles for component {component}: {str(e)}"
            )
            return []

    def get_permissions_for_role(self, component: str, role: str) -> List[str]:
        """
        Get permissions for role in component.

        Args:
            component: Component name
            role: Role name

        Returns:
            List of permissions for the role in the component
        """
        try:
            # Get role configuration
            role_config = self.roles.get(role, {})
            role_permissions = role_config.get("permissions", [])

            # Filter component-specific permissions
            component_permissions = []
            for permission in role_permissions:
                if (
                    permission == "*"
                    or permission.startswith(f"{component}:")
                    or permission.startswith("system:")
                ):
                    component_permissions.append(permission)

            # Add inherited permissions
            inherited_roles = self._get_inherited_roles(role)
            for inherited_role in inherited_roles:
                inherited_config = self.roles.get(inherited_role, {})
                inherited_permissions = inherited_config.get("permissions", [])
                for permission in inherited_permissions:
                    if (
                        permission == "*"
                        or permission.startswith(f"{component}:")
                        or permission.startswith("system:")
                    ):
                        if permission not in component_permissions:
                            component_permissions.append(permission)

            return component_permissions

        except PermissionError as e:
            self.logger.error(
                f"Error getting permissions for role {role} in component {component}: {str(e)}"
            )
            return []

    def validate_role_permission(
        self, component: str, role: str, permission: str
    ) -> bool:
        """
        Validate if role has permission in component.

        Args:
            component: Component name
            role: Role name
            permission: Permission to validate

        Returns:
            True if role has the permission
        """
        try:
            role_permissions = self.get_permissions_for_role(component, role)

            # Check for wildcard permission
            if "*" in role_permissions:
                return True

            # Check for exact permission match
            if permission in role_permissions:
                return True

            # Check for component-specific permission
            component_permission = f"{component}:{permission}"
            if component_permission in role_permissions:
                return True

            # Check for system permission
            system_permission = f"system:{permission}"
            if system_permission in role_permissions:
                return True

            return False

        except ValidationError as e:
            self.logger.error(f"Error validating role permission: {str(e)}")
            return False

    def get_role_hierarchy(self, role: str) -> List[str]:
        """
        Get role hierarchy (parent roles).

        Args:
            role: Role name

        Returns:
            List of parent roles
        """
        try:
            return self.role_hierarchy.get(role, [])

        except CustomError as e:
            self.logger.error(f"Error getting role hierarchy for {role}: {str(e)}")
            return []

    def get_all_roles(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all roles configuration.

        Returns:
            Dictionary of all roles
        """
        try:
            return self.roles.copy()

        except CustomError as e:
            self.logger.error(f"Error getting all roles: {str(e)}")
            return {}

    def get_roles_by_category(self, category: str) -> List[str]:
        """
        Get roles by category.

        Args:
            category: Role category

        Returns:
            List of roles in the category
        """
        try:
            roles = []
            for role_name, role_config in self.roles.items():
                if role_config.get("category") == category:
                    roles.append(role_name)

            return roles

        except CustomError as e:
            self.logger.error(f"Error getting roles by category {category}: {str(e)}")
            return []

    def get_role_level(self, role: str) -> int:
        """
        Get role level (higher number = more permissions).

        Args:
            role: Role name

        Returns:
            Role level
        """
        try:
            role_config = self.roles.get(role, {})
            return role_config.get("level", 0)

        except CustomError as e:
            self.logger.error(f"Error getting role level for {role}: {str(e)}")
            return 0

    def compare_roles(self, role1: str, role2: str) -> int:
        """
        Compare two roles by level.

        Args:
            role1: First role name
            role2: Second role name

        Returns:
            -1 if role1 < role2, 0 if equal, 1 if role1 > role2
        """
        try:
            level1 = self.get_role_level(role1)
            level2 = self.get_role_level(role2)

            if level1 < level2:
                return -1
            elif level1 > level2:
                return 1
            else:
                return 0

        except CustomError as e:
            self.logger.error(f"Error comparing roles {role1} and {role2}: {str(e)}")
            return 0

    def has_role_permission(
        self, user_roles: List[str], required_permission: str, component: str = None
    ) -> bool:
        """
        Check if user has required permission.

        Args:
            user_roles: List of user roles
            required_permission: Required permission
            component: Component name (optional)

        Returns:
            True if user has the permission
        """
        try:
            for role in user_roles:
                if component:
                    if self.validate_role_permission(
                        component, role, required_permission
                    ):
                        return True
                else:
                    # Check all components
                    for comp in self.component_roles.keys():
                        if self.validate_role_permission(
                            comp, role, required_permission
                        ):
                            return True

            return False

        except PermissionError as e:
            self.logger.error(f"Error checking role permission: {str(e)}")
            return False

    def get_user_permissions(
        self, user_roles: List[str], component: str = None
    ) -> List[str]:
        """
        Get all permissions for user roles.

        Args:
            user_roles: List of user roles
            component: Component name (optional)

        Returns:
            List of user permissions
        """
        try:
            all_permissions = set()

            for role in user_roles:
                if component:
                    role_permissions = self.get_permissions_for_role(component, role)
                else:
                    # Get permissions for all components
                    role_permissions = []
                    for comp in self.component_roles.keys():
                        comp_permissions = self.get_permissions_for_role(comp, role)
                        role_permissions.extend(comp_permissions)

                all_permissions.update(role_permissions)

            return list(all_permissions)

        except PermissionError as e:
            self.logger.error(f"Error getting user permissions: {str(e)}")
            return []

    def _get_inherited_roles(self, role: str) -> Set[str]:
        """
        Get all inherited roles for a role.

        Args:
            role: Role name

        Returns:
            Set of inherited roles
        """
        try:
            inherited = set()
            to_process = [role]

            while to_process:
                current_role = to_process.pop(0)
                if current_role in inherited:
                    continue

                inherited.add(current_role)
                parent_roles = self.role_hierarchy.get(current_role, [])
                to_process.extend(parent_roles)

            # Remove the original role from inherited set
            inherited.discard(role)
            return inherited

        except CustomError as e:
            self.logger.error(f"Error getting inherited roles for {role}: {str(e)}")
            return set()

    def add_role(self, role_name: str, role_config: Dict[str, Any]) -> bool:
        """
        Add a new role.

        Args:
            role_name: Role name
            role_config: Role configuration

        Returns:
            True if role was added successfully
        """
        try:
            self.roles[role_name] = role_config
            self.logger.info(f"Added role: {role_name}")
            return True

        except CustomError as e:
            self.logger.error(f"Error adding role {role_name}: {str(e)}")
            return False

    def remove_role(self, role_name: str) -> bool:
        """
        Remove a role.

        Args:
            role_name: Role name

        Returns:
            True if role was removed successfully
        """
        try:
            if role_name in self.roles:
                del self.roles[role_name]
                self.logger.info(f"Removed role: {role_name}")
                return True
            else:
                self.logger.warning(f"Role {role_name} not found")
                return False

        except CustomError as e:
            self.logger.error(f"Error removing role {role_name}: {str(e)}")
            return False

    def update_role(self, role_name: str, role_config: Dict[str, Any]) -> bool:
        """
        Update an existing role.

        Args:
            role_name: Role name
            role_config: Updated role configuration

        Returns:
            True if role was updated successfully
        """
        try:
            if role_name in self.roles:
                self.roles[role_name].update(role_config)
                self.logger.info(f"Updated role: {role_name}")
                return True
            else:
                self.logger.warning(f"Role {role_name} not found")
                return False

        except CustomError as e:
            self.logger.error(f"Error updating role {role_name}: {str(e)}")
            return False

    def save_roles(self, file_path: Optional[str] = None) -> bool:
        """
        Save roles to file.

        Args:
            file_path: Path to save roles (optional)

        Returns:
            True if roles were saved successfully
        """
        try:
            if not file_path:
                file_path = "config/roles_manager.json"

            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Save roles configuration
            config_data = {
                "roles": self.roles,
                "component_roles": self.component_roles,
                "role_hierarchy": self.role_hierarchy,
                "last_updated": datetime.utcnow().isoformat(),
            }

            with open(file_path, "w") as f:
                json.dump(config_data, f, indent=2)

            self.logger.info(f"Saved roles to {file_path}")
            return True

        except CustomError as e:
            self.logger.error(f"Error saving roles: {str(e)}")
            return False

    def load_roles_from_file(self, file_path: str) -> bool:
        """
        Load roles from file.

        Args:
            file_path: Path to load roles from

        Returns:
            True if roles were loaded successfully
        """
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"Roles file {file_path} not found")
                return False

            with open(file_path, "r") as f:
                config_data = json.load(f)

            self.roles = config_data.get("roles", {})
            self.component_roles = config_data.get("component_roles", {})
            self.role_hierarchy = config_data.get("role_hierarchy", {})

            self.logger.info(f"Loaded roles from {file_path}")
            return True

        except FileNotFoundError as e:
            self.logger.error(f"Error loading roles from {file_path}: {str(e)}")
            return False
