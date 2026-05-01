from ai_admin.core.custom_exceptions import AuthenticationError
"""
Token Configuration Management for AI Admin Server

This module provides token-based authentication configuration management
for the AI Admin server, including token definitions, validation, and integration with role-based access control.

Author: Vasiliy Zdanovskiy
Email: vasilyvz@gmail.com
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, field
from enum import Enum


class TokenType(Enum):
    """Token types for authentication."""

    API_KEY = "api_key"
    JWT = "jwt"
    BEARER = "bearer"
    SESSION = "session"
    CUSTOM = "custom"


class TokenStatus(Enum):
    """Token status enumeration."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


@dataclass
class TokenDefinition:
    """Token definition for authentication."""

    token_id: str
    token_value: str
    token_type: TokenType
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    max_usage: Optional[int] = None
    status: TokenStatus = TokenStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate token definition after initialization."""
        if not self.token_id:
            raise ValueError("Token ID cannot be empty")
        if not self.token_value:
            raise ValueError("Token value cannot be empty")
        if not isinstance(self.token_type, TokenType):
            raise ValueError(f"Invalid token type: {self.token_type}")
        if not isinstance(self.status, TokenStatus):
            raise ValueError(f"Invalid token status: {self.status}")

    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid (active and not expired)."""
        if self.status != TokenStatus.ACTIVE:
            return False
        if self.is_expired():
            return False
        if self.max_usage and self.usage_count >= self.max_usage:
            return False
        return True

    def can_use(self) -> bool:
        """Check if token can be used (valid and within usage limits)."""
        return self.is_valid()

    def increment_usage(self) -> None:
        """Increment token usage count."""
        self.usage_count += 1
        self.last_used = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert token definition to dictionary."""
        return {
            "token_id": self.token_id,
            "token_value": self.token_value,
            "token_type": self.token_type.value,
            "roles": self.roles,
            "permissions": self.permissions,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "usage_count": self.usage_count,
            "max_usage": self.max_usage,
            "status": self.status.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenDefinition":
        """Create token definition from dictionary."""
        return cls(
            token_id=data["token_id"],
            token_value=data["token_value"],
            token_type=TokenType(data["token_type"]),
            roles=data.get("roles", []),
            permissions=data.get("permissions", []),
            description=data.get("description"),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else None
            ),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
            last_used=(
                datetime.fromisoformat(data["last_used"])
                if data.get("last_used")
                else None
            ),
            usage_count=data.get("usage_count", 0),
            max_usage=data.get("max_usage"),
            status=TokenStatus(data.get("status", "active")),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TokenConfig:
    """Token configuration settings."""

    enabled: bool = True
    default_token_type: TokenType = TokenType.API_KEY
    default_expiry_hours: int = 24
    max_tokens_per_user: int = 10
    token_length: int = 32
    require_https: bool = True
    validate_roles: bool = True
    auto_cleanup_expired: bool = True
    cleanup_interval_hours: int = 1
    rate_limit_per_token: int = 1000
    rate_limit_window_minutes: int = 60
    storage_file: str = "tokens.json"
    backup_enabled: bool = True
    backup_interval_hours: int = 6

    def to_dict(self) -> Dict[str, Any]:
        """Convert TokenConfig to dictionary for JSON serialization."""
        return {
            "enabled": self.enabled,
            "default_token_type": self.default_token_type.value,
            "default_expiry_hours": self.default_expiry_hours,
            "max_tokens_per_user": self.max_tokens_per_user,
            "token_length": self.token_length,
            "require_https": self.require_https,
            "validate_roles": self.validate_roles,
            "auto_cleanup_expired": self.auto_cleanup_expired,
            "cleanup_interval_hours": self.cleanup_interval_hours,
            "rate_limit_per_token": self.rate_limit_per_token,
            "rate_limit_window_minutes": self.rate_limit_window_minutes,
            "storage_file": self.storage_file,
            "backup_enabled": self.backup_enabled,
            "backup_interval_hours": self.backup_interval_hours,
        }


class TokenManager:
    """
    Token management class for AI Admin server.

    This class provides comprehensive token-based authentication management,
    including token creation, validation, role mapping, and lifecycle management.
    """

    def __init__(
        self,
        config_data: Optional[Dict[str, Any]] = None,
        tokens_file: Optional[str] = None,
    ):
        """
        Initialize token manager.

        Args:
            config_data: Configuration data dictionary. If None, uses default values.
            tokens_file: Path to tokens storage file. If provided, loads from file.
        """
        self._config_data = config_data or {}
        self._tokens_file = tokens_file or "tokens.json"
        self._config = self._parse_token_config()
        self._tokens: Dict[str, TokenDefinition] = {}
        self._token_by_value: Dict[str, str] = {}  # token_value -> token_id mapping
        self._role_tokens: Dict[str, Set[str]] = {}  # role -> set of token_ids
        self._last_cleanup = datetime.utcnow()

        # Load tokens from file if it exists
        if os.path.exists(self._tokens_file):
            self._load_tokens_from_file()

    def _parse_token_config(self) -> TokenConfig:
        """Parse token configuration from configuration data."""
        token_config = self._config_data.get("tokens", {})

        return TokenConfig(
            enabled=token_config.get("enabled", True),
            default_token_type=TokenType(
                token_config.get("default_token_type", "api_key")
            ),
            default_expiry_hours=token_config.get("default_expiry_hours", 24),
            max_tokens_per_user=token_config.get("max_tokens_per_user", 10),
            token_length=token_config.get("token_length", 32),
            require_https=token_config.get("require_https", True),
            validate_roles=token_config.get("validate_roles", True),
            auto_cleanup_expired=token_config.get("auto_cleanup_expired", True),
            cleanup_interval_hours=token_config.get("cleanup_interval_hours", 1),
            rate_limit_per_token=token_config.get("rate_limit_per_token", 1000),
            rate_limit_window_minutes=token_config.get("rate_limit_window_minutes", 60),
            storage_file=token_config.get("storage_file", "tokens.json"),
            backup_enabled=token_config.get("backup_enabled", True),
            backup_interval_hours=token_config.get("backup_interval_hours", 6),
        )

    def _load_tokens_from_file(self) -> None:
        """Load tokens from storage file."""
        try:
            with open(self._tokens_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Load tokens
            if "tokens" in data:
                for token_data in data["tokens"]:
                    token = TokenDefinition.from_dict(token_data)
                    self._tokens[token.token_id] = token
                    self._token_by_value[token.token_value] = token.token_id

                    # Update role mapping
                    for role in token.roles:
                        if role not in self._role_tokens:
                            self._role_tokens[role] = set()
                        self._role_tokens[role].add(token.token_id)

            # Load last cleanup time
            if "last_cleanup" in data:
                self._last_cleanup = datetime.fromisoformat(data["last_cleanup"])

        except AuthenticationError as e:
            raise ValueError(
                f"Failed to load tokens from file {self._tokens_file}: {e}"
            )

    def _save_tokens_to_file(self) -> None:
        """Save tokens to storage file."""
        try:
            # Create backup if enabled
            if self._config.backup_enabled and os.path.exists(self._tokens_file):
                backup_file = f"{self._tokens_file}.backup"
                with open(self._tokens_file, "r", encoding="utf-8") as src:
                    with open(backup_file, "w", encoding="utf-8") as dst:
                        dst.write(src.read())

            # Save current tokens
            data = {
                "tokens": [token.to_dict() for token in self._tokens.values()],
                "last_cleanup": self._last_cleanup.isoformat(),
                "config": self._config.to_dict(),
            }

            with open(self._tokens_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except AuthenticationError as e:
            raise ValueError(f"Failed to save tokens to file {self._tokens_file}: {e}")

    def validate_token_config(self) -> bool:
        """
        Validate token configuration.

        Returns:
            bool: True if configuration is valid, False otherwise.

        Raises:
            ValueError: If configuration is invalid with detailed error message.
        """
        errors = []

        # Validate configuration parameters
        if self._config.default_expiry_hours <= 0:
            errors.append("Default expiry hours must be positive")

        if self._config.max_tokens_per_user <= 0:
            errors.append("Max tokens per user must be positive")

        if self._config.token_length < 8:
            errors.append("Token length must be at least 8 characters")

        if self._config.rate_limit_per_token <= 0:
            errors.append("Rate limit per token must be positive")

        if self._config.rate_limit_window_minutes <= 0:
            errors.append("Rate limit window must be positive")

        # Validate token storage file path
        if self._tokens_file:
            try:
                # Check if directory exists and is writable
                tokens_dir = os.path.dirname(self._tokens_file)
                if tokens_dir and not os.path.exists(tokens_dir):
                    os.makedirs(tokens_dir, exist_ok=True)
            except AuthenticationError as e:
                errors.append(f"Cannot create tokens directory: {e}")

        if errors:
            raise ValueError(
                f"Token configuration validation failed: {'; '.join(errors)}"
            )

        return True

    def get_tokens(self) -> List[TokenDefinition]:
        """
        Get list of all tokens.

        Returns:
            List[TokenDefinition]: List of all token definitions.
        """
        return list(self._tokens.values())

    def get_token_roles(self, token_id: str) -> List[str]:
        """
        Get roles associated with a token.

        Args:
            token_id: Token identifier.

        Returns:
            List[str]: List of roles for the token.
        """
        if token_id not in self._tokens:
            return []

        token = self._tokens[token_id]
        return token.roles.copy()

    def get_token_permissions(self, token_id: str) -> List[str]:
        """
        Get permissions associated with a token.

        Args:
            token_id: Token identifier.

        Returns:
            List[str]: List of permissions for the token.
        """
        if token_id not in self._tokens:
            return []

        token = self._tokens[token_id]
        return token.permissions.copy()

    def validate_token(self, token_value: str) -> bool:
        """
        Validate a token value.

        Args:
            token_value: Token value to validate.

        Returns:
            bool: True if token is valid.
        """
        if not token_value:
            return False

        # Check if token exists
        if token_value not in self._token_by_value:
            return False

        token_id = self._token_by_value[token_value]
        token = self._tokens[token_id]

        # Check if token is valid
        if not token.is_valid():
            return False

        # Increment usage count
        token.increment_usage()

        # Auto-cleanup expired tokens if enabled
        if self._config.auto_cleanup_expired:
            self._cleanup_expired_tokens()

        return True

    def is_token_valid(self, token_value: str) -> bool:
        """
        Check if a token is valid without incrementing usage.

        Args:
            token_value: Token value to check.

        Returns:
            bool: True if token is valid.
        """
        if not token_value:
            return False

        if token_value not in self._token_by_value:
            return False

        token_id = self._token_by_value[token_value]
        token = self._tokens[token_id]

        return token.is_valid()

    def get_token_expiry(self, token_value: str) -> Optional[datetime]:
        """
        Get expiry time for a token.

        Args:
            token_value: Token value.

        Returns:
            Optional[datetime]: Token expiry time or None if no expiry.
        """
        if not token_value or token_value not in self._token_by_value:
            return None

        token_id = self._token_by_value[token_value]
        token = self._tokens[token_id]

        return token.expires_at

    def create_token(
        self,
        token_id: str,
        roles: List[str],
        permissions: Optional[List[str]] = None,
        description: Optional[str] = None,
        expires_hours: Optional[int] = None,
        max_usage: Optional[int] = None,
        token_type: Optional[TokenType] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TokenDefinition:
        """
        Create a new token.

        Args:
            token_id: Unique token identifier.
            roles: List of roles for the token.
            permissions: List of permissions for the token.
            description: Token description.
            expires_hours: Token expiry in hours.
            max_usage: Maximum usage count.
            token_type: Token type.
            metadata: Additional metadata.

        Returns:
            TokenDefinition: Created token definition.

        Raises:
            ValueError: If token creation fails.
        """
        if not self._config.enabled:
            raise ValueError("Token authentication is disabled")

        if token_id in self._tokens:
            raise ValueError(f"Token with ID '{token_id}' already exists")

        if not roles:
            raise ValueError("Token must have at least one role")

        # Generate token value
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits
        token_value = "".join(
            secrets.choice(alphabet) for _ in range(self._config.token_length)
        )

        # Ensure token value is unique
        while token_value in self._token_by_value:
            token_value = "".join(
                secrets.choice(alphabet) for _ in range(self._config.token_length)
            )

        # Set expiry time
        expires_at = None
        if expires_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        elif self._config.default_expiry_hours:
            expires_at = datetime.utcnow() + timedelta(
                hours=self._config.default_expiry_hours
            )

        # Create token definition
        token = TokenDefinition(
            token_id=token_id,
            token_value=token_value,
            token_type=token_type or self._config.default_token_type,
            roles=roles,
            permissions=permissions or [],
            description=description,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            max_usage=max_usage,
            metadata=metadata or {},
        )

        # Add token to storage
        self._tokens[token_id] = token
        self._token_by_value[token_value] = token_id

        # Update role mapping
        for role in roles:
            if role not in self._role_tokens:
                self._role_tokens[role] = set()
            self._role_tokens[role].add(token_id)

        # Save to file
        self._save_tokens_to_file()

        return token

    def revoke_token(self, token_id: str) -> bool:
        """
        Revoke a token.

        Args:
            token_id: Token identifier.

        Returns:
            bool: True if token was revoked, False if token doesn't exist.
        """
        if token_id not in self._tokens:
            return False

        token = self._tokens[token_id]
        token.status = TokenStatus.REVOKED

        # Remove from role mapping
        for role in token.roles:
            if role in self._role_tokens:
                self._role_tokens[role].discard(token_id)

        # Save to file
        self._save_tokens_to_file()

        return True

    def delete_token(self, token_id: str) -> bool:
        """
        Delete a token permanently.

        Args:
            token_id: Token identifier.

        Returns:
            bool: True if token was deleted, False if token doesn't exist.
        """
        if token_id not in self._tokens:
            return False

        token = self._tokens[token_id]

        # Remove from all mappings
        del self._tokens[token_id]
        del self._token_by_value[token.token_value]

        # Remove from role mapping
        for role in token.roles:
            if role in self._role_tokens:
                self._role_tokens[role].discard(token_id)

        # Save to file
        self._save_tokens_to_file()

        return True

    def get_tokens_by_role(self, role: str) -> List[TokenDefinition]:
        """
        Get all tokens for a specific role.

        Args:
            role: Role name.

        Returns:
            List[TokenDefinition]: List of tokens for the role.
        """
        if role not in self._role_tokens:
            return []

        token_ids = self._role_tokens[role]
        return [
            self._tokens[token_id] for token_id in token_ids if token_id in self._tokens
        ]

    def _cleanup_expired_tokens(self) -> None:
        """Clean up expired tokens."""
        if not self._config.auto_cleanup_expired:
            return

        # Check if cleanup is needed
        now = datetime.utcnow()
        if (
            now - self._last_cleanup
        ).total_seconds() < self._config.cleanup_interval_hours * 3600:
            return

        expired_tokens = []
        for token_id, token in self._tokens.items():
            if token.is_expired() or token.status == TokenStatus.REVOKED:
                expired_tokens.append(token_id)

        # Remove expired tokens
        for token_id in expired_tokens:
            self.delete_token(token_id)

        self._last_cleanup = now

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get configuration summary.

        Returns:
            Dict[str, Any]: Configuration summary dictionary.
        """
        active_tokens = len(
            [t for t in self._tokens.values() if t.status == TokenStatus.ACTIVE and not t.is_expired()]
        )
        expired_tokens = len([t for t in self._tokens.values() if t.is_expired()])
        revoked_tokens = len(
            [t for t in self._tokens.values() if t.status == TokenStatus.REVOKED]
        )

        return {
            "enabled": self._config.enabled,
            "total_tokens": len(self._tokens),
            "active_tokens": active_tokens,
            "expired_tokens": expired_tokens,
            "revoked_tokens": revoked_tokens,
            "default_token_type": self._config.default_token_type.value,
            "default_expiry_hours": self._config.default_expiry_hours,
            "max_tokens_per_user": self._config.max_tokens_per_user,
            "token_length": self._config.token_length,
            "require_https": self._config.require_https,
            "validate_roles": self._config.validate_roles,
            "auto_cleanup_expired": self._config.auto_cleanup_expired,
            "storage_file": self._tokens_file,
            "roles": list(self._role_tokens.keys()),
        }

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update token configuration.

        Args:
            new_config: New configuration data dictionary.
        """
        self._config_data.update(new_config)
        self._config = self._parse_token_config()

    def __repr__(self) -> str:
        """String representation of token manager."""
        return (
            f"TokenManager(tokens={len(self._tokens)}, enabled={self._config.enabled})"
        )
