"""Module manager."""

from ai_admin.core.custom_exceptions import AuthenticationError, CustomError, SSLError, TokenError, ValidationError
import os
import json
import jwt
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from ..config.token_config import TokenManager, TokenStatus
from ..config.roles_config import RolesConfig
from .ssl_error_handler import SSLErrorHandler
from .types import PermissionCheckError, TokenAuthError, TokenAuthResult, TokenExpiredError, TokenInvalidError, TokenValidationError

class TokenAuthManager:
    """
    Manager for token-based authentication and authorization.

    This class provides comprehensive token authentication management including:
    - Token validation and verification
    - Role extraction from tokens
    - Permission checking and authorization
    - Integration with role-based access control
    - JWT token handling
    - Token lifecycle management
    """

    def __init__(
        self,
        token_manager: Optional[TokenManager] = None,
        roles_config: Optional[RolesConfig] = None,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        token_expire_minutes: int = 30,
        error_handler: Optional[SSLErrorHandler] = None,
    ):
        """
        Initialize token authentication manager.

        Args:
            token_manager: Token manager instance for token storage and management
            roles_config: Roles configuration instance for role-based access control
            secret_key: JWT secret key for token validation
            algorithm: JWT algorithm for token validation
            token_expire_minutes: Default token expiration time in minutes
            error_handler: SSL error handler for comprehensive error management
        """
        self.logger = logging.getLogger("ai_admin.token_auth_manager")
        self.token_manager = token_manager
        self.roles_config = roles_config
        self.secret_key = secret_key or self._get_default_secret_key()
        self.algorithm = algorithm
        self.token_expire_minutes = token_expire_minutes
        self.error_handler = error_handler or SSLErrorHandler()

        # Cache for validated tokens and roles
        self._token_cache: Dict[str, Dict[str, Any]] = {}
        self._role_cache: Dict[str, List[str]] = {}
        self._cache_ttl = timedelta(minutes=15)

        # Security settings
        self._require_token = True
        self._validate_token_expiry = True
        self._check_token_revocation = True
        self._max_token_age = timedelta(hours=24)

        self.logger.info("TokenAuthManager initialized")

    async def validate_token(self, token: str) -> TokenAuthResult:
        """
        Validate token and extract user information.

        Args:
            token: Token to validate

        Returns:
            TokenAuthResult with authentication information

        Raises:
            TokenValidationError: If token validation fails
        """
        try:
            if not token:
                return TokenAuthResult(
                    authenticated=False,
                    error_message="Token is required",
                    error_code="TOKEN_REQUIRED",
                )

            # Check token cache
            if token in self._token_cache:
                cached_data = self._token_cache[token]
                if self._is_cache_valid(cached_data):
                    self.logger.debug("Using cached token validation")
                    return TokenAuthResult(
                        authenticated=True,
                        user_id=cached_data.get("user_id"),
                        roles=cached_data.get("roles", []),
                        permissions=cached_data.get("permissions", []),
                        token_info=cached_data.get("token_info"),
                    )

            # Validate token based on type
            if self._is_jwt_token(token):
                result = await self._validate_jwt_token(token)
            else:
                result = await self._validate_stored_token(token)

            # Cache validation result if successful
            if result.authenticated:
                self._token_cache[token] = {
                    "user_id": result.user_id,
                    "roles": result.roles,
                    "permissions": result.permissions,
                    "token_info": result.token_info,
                    "validated_at": datetime.utcnow(),
                }

            return result

        except ValidationError as e:
            error_msg = f"Token validation failed: {e}"
            self.logger.error(error_msg)

            # Handle error through error handler
            await self.error_handler.handle_token_error(
                error=e,
                operation="validate_token",
                user_roles=[],
                token_info={"token_length": len(token) if token else 0},
            )

            return TokenAuthResult(
                authenticated=False,
                error_message=error_msg,
                error_code="TOKEN_VALIDATION_ERROR",
            )

    async def extract_roles_from_token(self, token: str) -> List[str]:
        """
        Extract roles from token.

        Args:
            token: Token to extract roles from

        Returns:
            List of roles extracted from token

        Raises:
            TokenValidationError: If role extraction fails
        """
        try:
            # Check role cache
            if token in self._role_cache:
                self.logger.debug("Using cached roles")
                return self._role_cache[token]

            roles = []

            # Validate token first
            validation_result = await self.validate_token(token)
            if not validation_result.authenticated:
                raise TokenValidationError(
                    f"Cannot extract roles from invalid token: "
                    f"{validation_result.error_message}"
                )

            # Extract roles from validation result
            roles = validation_result.roles or []

            # Cache extracted roles
            self._role_cache[token] = roles

            self.logger.info(f"Extracted roles from token: {roles}")
            return roles

        except ValidationError as e:
            error_msg = f"Role extraction failed: {e}"
            self.logger.error(error_msg)

            # Handle error through error handler
            await self.error_handler.handle_token_error(
                error=e,
                operation="extract_roles_from_token",
                user_roles=[],
                token_info={"token_length": len(token) if token else 0},
            )
            raise TokenValidationError(error_msg, {"exception": str(e)})

    async def check_permissions(
        self,
        token: str,
        required_permissions: List[str],
        resource: Optional[str] = None,
    ) -> bool:
        """
        Check if token has required permissions.

        Args:
            token: Token to check permissions for
            required_permissions: List of required permissions
            resource: Optional resource identifier

        Returns:
            True if token has required permissions, False otherwise

        Raises:
            PermissionCheckError: If permission check fails
        """
        try:
            # Validate token and get user information
            validation_result = await self.validate_token(token)
            if not validation_result.authenticated:
                raise PermissionCheckError(
                    f"Cannot check permissions for invalid token: "
                    f"{validation_result.error_message}"
                )

            user_roles = validation_result.roles or []
            user_permissions = validation_result.permissions or []

            # Check if user has any of the required permissions directly
            for permission in required_permissions:
                if permission in user_permissions:
                    self.logger.info(f"Permission {permission} granted directly")
                    return True

            # Check if any user role has any of the required permissions
            if self.roles_config:
                for role_name in user_roles:
                    if not self.roles_config.is_role_allowed(role_name):
                        self.logger.debug(f"Role {role_name} is not allowed")
                        continue

                    # Check if role has any of the required permissions
                    for permission in required_permissions:
                        if self.roles_config.has_permission(role_name, permission):
                            self.logger.info(
                                f"Permission {permission} granted to role {role_name}"
                            )
                            return True

            self.logger.info(
                f"Access denied: token roles {user_roles} do not have required "
                f"permissions {required_permissions}"
            )
            return False

        except AuthenticationError as e:
            error_msg = f"Permission check failed: {e}"
            self.logger.error(error_msg)

            # Handle error through error handler
            await self.error_handler.handle_token_error(
                error=e,
                operation="check_permissions",
                user_roles=user_roles,
                token_info={
                    "required_permissions": required_permissions,
                    "resource": resource,
                },
            )
            raise PermissionCheckError(error_msg, {"exception": str(e)})

    async def authenticate_client(
        self,
        token: str,
        required_permissions: Optional[List[str]] = None,
        resource: Optional[str] = None,
    ) -> TokenAuthResult:
        """
        Authenticate client using token and check permissions.

        Args:
            token: Token to authenticate with
            required_permissions: Optional list of required permissions
            resource: Optional resource identifier

        Returns:
            TokenAuthResult with authentication information

        Raises:
            TokenAuthError: If authentication fails
        """
        try:
            # Validate token
            validation_result = await self.validate_token(token)
            if not validation_result.authenticated:
                return validation_result

            # Check permissions if required
            has_permissions = True
            if required_permissions:
                has_permissions = await self.check_permissions(
                    token, required_permissions, resource
                )

            # Prepare authentication result
            auth_result = TokenAuthResult(
                authenticated=True,
                user_id=validation_result.user_id,
                roles=validation_result.roles,
                permissions=validation_result.permissions,
                token_info=validation_result.token_info,
            )

            if not has_permissions:
                auth_result.authenticated = False
                auth_result.error_message = "Access denied: insufficient permissions"
                auth_result.error_code = "PERMISSION_DENIED"

            self.logger.info(
                f"Client authenticated successfully: {validation_result.user_id} "
                f"with roles {validation_result.roles}"
            )
            return auth_result

        except AuthenticationError as e:
            error_msg = f"Client authentication failed: {e}"
            self.logger.error(error_msg)

            # Handle error through error handler
            await self.error_handler.handle_token_error(
                error=e,
                operation="authenticate_client",
                user_roles=[],
                token_info={"token_length": len(token) if token else 0},
            )
            return TokenAuthResult(
                authenticated=False,
                error_message=error_msg,
                error_code="AUTHENTICATION_ERROR",
            )

    async def get_client_roles(self, token: str) -> List[str]:
        """
        Get client roles from token.

        Args:
            token: Token to get roles from

        Returns:
            List of client roles
        """
        return await self.extract_roles_from_token(token)

    async def check_token_expiry(self, token: str) -> bool:
        """
        Check if token is expired.

        Args:
            token: Token to check

        Returns:
            True if token is expired, False otherwise
        """
        try:
            if self._is_jwt_token(token):
                return await self._check_jwt_token_expiry(token)
            else:
                return await self._check_stored_token_expiry(token)

        except AuthenticationError as e:
            self.logger.error(f"Token expiry check failed: {e}")
            return True  # Assume expired on error

    async def generate_token(
        self,
        user_id: str,
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        expires_minutes: Optional[int] = None,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate JWT token for user.

        Args:
            user_id: User identifier
            roles: List of user roles
            permissions: List of user permissions
            expires_minutes: Token expiration time in minutes
            additional_claims: Additional claims to include in token

        Returns:
            Generated JWT token

        Raises:
            TokenValidationError: If token generation fails
        """
        try:
            # Prepare token payload
            now = datetime.utcnow()
            exp_minutes = expires_minutes or self.token_expire_minutes
            payload = {
                "sub": user_id,
                "iat": now,
                "exp": now + timedelta(minutes=exp_minutes),
                "roles": roles or [],
                "permissions": permissions or [],
            }

            # Add additional claims
            if additional_claims:
                payload.update(additional_claims)

            # Generate token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

            self.logger.info(f"Generated token for user: {user_id}")
            return token

        except ValidationError as e:
            self.logger.error(f"Failed to generate token: {e}")

            # Handle error through error handler
            await self.error_handler.handle_token_error(
                error=e,
                operation="generate_token",
                user_roles=roles or [],
                token_info={"user_id": user_id, "expires_minutes": expires_minutes},
            )
            raise TokenValidationError(f"Token generation failed: {e}")

    async def refresh_token(self, token: str) -> str:
        """
        Refresh JWT token.

        Args:
            token: Current JWT token

        Returns:
            New JWT token

        Raises:
            TokenValidationError: If token refresh fails
        """
        try:
            # Validate current token
            validation_result = await self.validate_token(token)
            if not validation_result.authenticated:
                raise TokenInvalidError("Cannot refresh invalid token")

            # Generate new token with same claims
            return await self.generate_token(
                user_id=validation_result.user_id,
                roles=validation_result.roles,
                permissions=validation_result.permissions,
            )

        except ValidationError as e:
            self.logger.error(f"Failed to refresh token: {e}")

            # Handle error through error handler
            await self.error_handler.handle_token_error(
                error=e,
                operation="refresh_token",
                user_roles=[],
                token_info={"token_length": len(token) if token else 0},
            )
            raise TokenValidationError(f"Token refresh failed: {e}")

    async def _validate_jwt_token(self, token: str) -> TokenAuthResult:
        """Validate JWT token."""
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True},
            )

            # Check token expiration
            exp = payload.get("exp")
            if exp and exp < time.time():
                raise TokenExpiredError("Token has expired")

            # Validate required claims
            required_claims = ["sub", "iat"]
            for claim in required_claims:
                if claim not in payload:
                    raise TokenInvalidError(f"Missing required claim: {claim}")

            # Extract user information
            user_id = payload.get("sub")
            roles = payload.get("roles", [])
            permissions = payload.get("permissions", [])

            return TokenAuthResult(
                authenticated=True,
                user_id=user_id,
                roles=roles,
                permissions=permissions,
                token_info={
                    "type": "jwt",
                    "issued_at": payload.get("iat"),
                    "expires_at": payload.get("exp"),
                    "algorithm": self.algorithm,
                },
            )

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Invalid token: {e}")
        except ValidationError as e:
            # Handle error through error handler
            await self.error_handler.handle_token_error(
                error=e,
                operation="validate_jwt_token",
                user_roles=[],
                token_info={"token_length": len(token) if token else 0},
            )
            raise TokenValidationError(f"JWT token validation failed: {e}")

    async def _validate_stored_token(self, token: str) -> TokenAuthResult:
        """Validate stored token using token manager."""
        try:
            if not self.token_manager:
                raise TokenValidationError("Token manager not available")

            # Check if token is valid
            if not self.token_manager.validate_token(token):
                return TokenAuthResult(
                    authenticated=False,
                    error_message="Token is invalid or expired",
                    error_code="TOKEN_INVALID",
                )

            # Get token definition
            token_id = self.token_manager._token_by_value.get(token)
            if not token_id:
                return TokenAuthResult(
                    authenticated=False,
                    error_message="Token not found",
                    error_code="TOKEN_NOT_FOUND",
                )

            token_def = self.token_manager._tokens.get(token_id)
            if not token_def:
                return TokenAuthResult(
                    authenticated=False,
                    error_message="Token definition not found",
                    error_code="TOKEN_DEFINITION_NOT_FOUND",
                )

            # Check if token is expired
            if token_def.is_expired():
                return TokenAuthResult(
                    authenticated=False,
                    error_message="Token has expired",
                    error_code="TOKEN_EXPIRED",
                )

            # Check token status
            if token_def.status != TokenStatus.ACTIVE:
                return TokenAuthResult(
                    authenticated=False,
                    error_message=f"Token status is {token_def.status.value}",
                    error_code="TOKEN_INACTIVE",
                )

            return TokenAuthResult(
                authenticated=True,
                user_id=token_def.token_id,
                roles=token_def.roles,
                permissions=token_def.permissions,
                token_info={
                    "type": "stored",
                    "token_type": token_def.token_type.value,
                    "created_at": (
                        token_def.created_at.isoformat()
                        if token_def.created_at
                        else None
                    ),
                    "expires_at": (
                        token_def.expires_at.isoformat()
                        if token_def.expires_at
                        else None
                    ),
                    "usage_count": token_def.usage_count,
                    "max_usage": token_def.max_usage,
                    "status": token_def.status.value,
                },
            )

        except ValidationError as e:
            # Handle error through error handler
            await self.error_handler.handle_token_error(
                error=e,
                operation="validate_stored_token",
                user_roles=[],
                token_info={"token_length": len(token) if token else 0},
            )
            raise TokenValidationError(f"Stored token validation failed: {e}")

    async def _check_jwt_token_expiry(self, token: str) -> bool:
        """Check if JWT token is expired."""
        try:
            # Decode token without verification to check expiry
            payload = jwt.decode(
                token, options={"verify_signature": False, "verify_exp": False}
            )

            exp = payload.get("exp")
            if exp and exp < time.time():
                return True

            return False

        except AuthenticationError as e:
            self.logger.error(f"Failed to check JWT token expiry: {e}")
            return True

    async def _check_stored_token_expiry(self, token: str) -> bool:
        """Check if stored token is expired."""
        try:
            if not self.token_manager:
                return True

            token_id = self.token_manager._token_by_value.get(token)
            if not token_id:
                return True

            token_def = self.token_manager._tokens.get(token_id)
            if not token_def:
                return True

            return token_def.is_expired()

        except AuthenticationError as e:
            self.logger.error(f"Failed to check stored token expiry: {e}")
            return True

    def _is_jwt_token(self, token: str) -> bool:
        """Check if token is a JWT token."""
        try:
            # JWT tokens have 3 parts separated by dots
            parts = token.split(".")
            return len(parts) == 3
        except CustomError:
            return False

    def _get_default_secret_key(self) -> str:
        """Get default JWT secret key."""
        try:
            # Try environment variable first
            secret_key = os.getenv("JWT_SECRET_KEY")
            if secret_key:
                return secret_key

            # Try configuration file
            config_path = "config/jwt_config.json"
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    secret_key = config.get("secret_key")
                    if isinstance(secret_key, str):
                        return secret_key

            # Return default key (should be changed in production)
            self.logger.warning("Using default JWT secret key - change in production!")
            return "default-secret-key-change-in-production"

        except CustomError as e:
            self.logger.warning(f"Failed to get secret key: {e}")
            return "default-secret-key-change-in-production"

    def _is_cache_valid(self, cached_data: Dict[str, Any]) -> bool:
        """Check if cached data is still valid."""
        try:
            validated_at = cached_data.get("validated_at")
            if not validated_at:
                return False

            if isinstance(validated_at, str):
                validated_at = datetime.fromisoformat(validated_at)

            return datetime.utcnow() - validated_at < self._cache_ttl
        except CustomError:
            return False

    def clear_cache(self) -> None:
        """Clear token and role caches."""
        self._token_cache.clear()
        self._role_cache.clear()
        self.logger.info("Token authentication cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "token_cache_size": len(self._token_cache),
            "role_cache_size": len(self._role_cache),
            "cache_ttl_minutes": self._cache_ttl.total_seconds() / 60,
        }

    def update_security_settings(
        self,
        require_token: Optional[bool] = None,
        validate_token_expiry: Optional[bool] = None,
        check_token_revocation: Optional[bool] = None,
        max_token_age_hours: Optional[int] = None,
    ) -> None:
        """Update security settings."""
        if require_token is not None:
            self._require_token = require_token
        if validate_token_expiry is not None:
            self._validate_token_expiry = validate_token_expiry
        if check_token_revocation is not None:
            self._check_token_revocation = check_token_revocation
        if max_token_age_hours is not None:
            self._max_token_age = timedelta(hours=max_token_age_hours)

        self.logger.info("Token authentication security settings updated")

    def get_security_settings(self) -> Dict[str, Any]:
        """Get current security settings."""
        return {
            "require_token": self._require_token,
            "validate_token_expiry": self._validate_token_expiry,
            "check_token_revocation": self._check_token_revocation,
            "max_token_age_hours": self._max_token_age.total_seconds() / 3600,
            "token_expire_minutes": self.token_expire_minutes,
            "algorithm": self.algorithm,
        }

