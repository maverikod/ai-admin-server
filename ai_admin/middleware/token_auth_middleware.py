from ai_admin.core.custom_exceptions import AuthenticationError, ConfigurationError, CustomError, PermissionError, TokenError, ValidationError
"""Token-based authentication middleware for AI Admin.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import json
import jwt
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

import logging
from .middleware_exceptions import (
    TokenValidationError,
    TokenExpiredError,
    TokenInvalidError,
    PermissionDeniedError,
)


class TokenAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for token-based authentication and authorization."""

    def __init__(
        self,
        app: ASGIApp,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        token_expire_minutes: int = 30,
        public_endpoints: Optional[List[str]] = None,
        require_token: bool = True,
        token_header: str = "Authorization",
        token_prefix: str = "Bearer",
        roles_config_path: Optional[str] = None,
        default_policy: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize token authentication middleware.

        Args:
            app: ASGI application
            secret_key: JWT secret key for token validation
            algorithm: JWT algorithm for token validation
            token_expire_minutes: Token expiration time in minutes
            public_endpoints: List of public endpoints that don't require authentication
            require_token: Whether to require token for all endpoints
            token_header: HTTP header name containing the token
            token_prefix: Token prefix (e.g., "Bearer")
            roles_config_path: Path to roles configuration file
            default_policy: Default authorization policy
        """
        super().__init__(app)
        self.logger = logging.getLogger("ai_admin.token_auth_middleware")

        # Token configuration
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expire_minutes = token_expire_minutes
        self.token_header = token_header
        self.token_prefix = token_prefix

        # Authorization configuration
        self.require_token = require_token
        self.public_endpoints = public_endpoints or [
            "/health",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
            "/auth/login",
            "/auth/refresh",
        ]

        # Roles and permissions
        self.roles_config_path = roles_config_path or "config/roles.json"
        self.roles_config: Dict[str, Any] = {}
        self.default_policy = default_policy

        # Initialize async components
        self._initialized = False

        self.logger.info("TokenAuthMiddleware initialized")

    async def _initialize_async(self) -> None:
        """Initialize async components."""
        if not self._initialized:
            # Initialize secret key
            if not self.secret_key:
                self.secret_key = await self._get_secret_key()

            # Initialize roles config
            self.roles_config = await self._load_roles_config()

            # Initialize default policy
            if not self.default_policy:
                self.default_policy = await self._get_default_policy()

            self._initialized = True

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        """
        Process request through token authentication middleware.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response from next handler or authentication error response
        """
        try:
            # Initialize async components if not already done
            await self._initialize_async()

            # Get request path
            path = request.url.path

            # Check if endpoint is public
            if self._is_public_endpoint(path):
                self.logger.debug(f"Public endpoint accessed: {path}")
                return await call_next(request)

            # Extract token from request
            token = self._extract_token(request)

            if not token and self.require_token:
                return self._create_auth_error_response(
                    "Token required", status.HTTP_401_UNAUTHORIZED
                )

            if token:
                # Validate token
                validation_result = await self._validate_token(token)
                if not validation_result["valid"]:
                    return self._create_auth_error_response(
                        validation_result["error"], status.HTTP_401_UNAUTHORIZED
                    )

                # Check permissions
                permission_result = await self._check_permissions(
                    request, validation_result["payload"]
                )
                if not permission_result["allowed"]:
                    return self._create_auth_error_response(
                        permission_result["error"], status.HTTP_403_FORBIDDEN
                    )

                # Add user info to request state
                request.state.user = validation_result["payload"]
                request.state.token = token

                user_id = validation_result["payload"].get("sub", "unknown")
                self.logger.debug(f"Token validated for user: {user_id}")

            # Continue to next handler
            response = await call_next(request)
            return response

        except TokenValidationError as e:
            self.logger.warning(f"Token validation error: {e}")
            return self._create_auth_error_response(
                f"Token validation failed: {e}", status.HTTP_401_UNAUTHORIZED
            )
        except PermissionDeniedError as e:
            self.logger.warning(f"Permission denied: {e}")
            return self._create_auth_error_response(
                f"Permission denied: {e}", status.HTTP_403_FORBIDDEN
            )
        except AuthenticationError as e:
            self.logger.error(f"Unexpected error in token middleware: {e}")
            return self._create_auth_error_response(
                "Internal authentication error", status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract token from request headers.

        Args:
            request: FastAPI request object

        Returns:
            Extracted token or None if not found
        """
        try:
            # Get token from Authorization header
            auth_header = request.headers.get(self.token_header)
            if not auth_header:
                return None

            # Check if header starts with expected prefix
            if not auth_header.startswith(self.token_prefix):
                return None

            # Extract token
            token = auth_header[len(self.token_prefix) :].strip()
            return token if token else None

        except AuthenticationError as e:
            self.logger.warning(f"Failed to extract token: {e}")
            return None

    async def _validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token.

        Args:
            token: JWT token to validate

        Returns:
            Dictionary with validation result and payload
        """
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

            return {"valid": True, "payload": payload, "error": None}

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Invalid token: {e}")
        except ValidationError as e:
            raise TokenValidationError(f"Token validation failed: {e}")

    async def _check_permissions(
        self, request: Request, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if user has permission to access the requested resource.

        Args:
            request: FastAPI request object
            payload: JWT token payload

        Returns:
            Dictionary with permission check result
        """
        try:
            # Get user roles from token
            user_roles = payload.get("roles", [])
            if not user_roles:
                user_roles = [payload.get("role", "user")]

            # Get request method and path
            method = request.method
            path = request.url.path

            # Check permissions for each role
            for role in user_roles:
                if await self._has_permission(role, method, path):
                    return {"allowed": True, "error": None, "role": role}

            # Check default policy
            if await self._check_default_policy(method, path):
                return {"allowed": True, "error": None, "role": "default"}

            return {
                "allowed": False,
                "error": f"Access denied for roles: {user_roles}",
                "role": None,
            }

        except PermissionError as e:
            self.logger.error(f"Permission check failed: {e}")
            return {
                "allowed": False,
                "error": f"Permission check failed: {e}",
                "role": None,
            }

    async def _has_permission(self, role: str, method: str, path: str) -> bool:
        """
        Check if role has permission for the given method and path.

        Args:
            role: User role
            method: HTTP method
            path: Request path

        Returns:
            True if permission is granted, False otherwise
        """
        try:
            # Ensure roles config is initialized
            if not self.roles_config:
                self.roles_config = await self._load_roles_config()

            # Get role configuration
            role_config = self.roles_config.get("roles", {}).get(role, {})
            if not role_config:
                return False

            # Get role permissions
            permissions = role_config.get("permissions", {})
            
            # If permissions is a dict (method -> paths), check path access
            if isinstance(permissions, dict):
                allowed_paths = permissions.get(method.upper(), [])
                return self._path_matches_any_pattern(path, allowed_paths)
            
            # If permissions is a list, check permission type
            required_permission = self._get_required_permission(method)
            return required_permission in permissions

        except PermissionError as e:
            self.logger.warning(f"Failed to check role permission: {e}")
            return False

    def _path_matches_any_pattern(self, path: str, patterns: List[str]) -> bool:
        """
        Check if path matches any of the given patterns.

        Args:
            path: Request path
            patterns: List of patterns to match (supports * wildcard)

        Returns:
            True if path matches any pattern
        """
        import fnmatch
        return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)

    def _get_required_permission(self, method: str) -> str:
        """
        Get required permission for HTTP method.

        Args:
            method: HTTP method

        Returns:
            Required permission string
        """
        method_permissions = {
            "GET": "read",
            "POST": "write",
            "PUT": "write",
            "PATCH": "write",
            "DELETE": "delete",
            "HEAD": "read",
            "OPTIONS": "read",
        }
        return method_permissions.get(method.upper(), "read")

    async def _check_default_policy(self, method: str, path: str) -> bool:
        """
        Check default policy for the given method and path.

        Args:
            method: HTTP method
            path: Request path

        Returns:
            True if allowed by default policy, False otherwise
        """
        try:
            # Ensure default policy is initialized
            if not self.default_policy:
                self.default_policy = await self._get_default_policy()

            default_policy = self.default_policy.get("default_policy", {})

            # Check if allow_all is enabled
            if default_policy.get("allow_all", False):
                return True

            # Check public endpoints
            public_endpoints = default_policy.get("public_endpoints", [])
            for endpoint in public_endpoints:
                if path.startswith(endpoint):
                    return True

            return False

        except CustomError as e:
            self.logger.warning(f"Failed to check default policy: {e}")
            return False

    def _is_public_endpoint(self, path: str) -> bool:
        """
        Check if endpoint is public (doesn't require authentication).

        Args:
            path: Request path

        Returns:
            True if endpoint is public, False otherwise
        """
        for endpoint in self.public_endpoints:
            if path.startswith(endpoint):
                return True
        return False

    def _create_auth_error_response(
        self, message: str, status_code: int
    ) -> JSONResponse:
        """
        Create authentication error response.

        Args:
            message: Error message
            status_code: HTTP status code

        Returns:
            JSON error response
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "error": "authentication_error",
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def _get_secret_key(self) -> str:
        """
        Get JWT secret key from environment or configuration.

        Returns:
            JWT secret key
        """
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
                    secret_key = config.get("secret_key", "default-secret-key")
                    if isinstance(secret_key, str):
                        return secret_key

            # Return default key (should be changed in production)
            self.logger.warning("Using default JWT secret key - change in production!")
            return "default-secret-key-change-in-production"

        except CustomError as e:
            self.logger.warning(f"Failed to get secret key: {e}")
            return "default-secret-key-change-in-production"

    async def _load_roles_config(self) -> Dict[str, Any]:
        """
        Load roles configuration from file.

        Returns:
            Roles configuration dictionary
        """
        try:
            if os.path.exists(self.roles_config_path):
                with open(self.roles_config_path, "r") as f:
                    config = json.load(f)
                    if isinstance(config, dict):
                        return config

            # Return default configuration
            return await self._get_default_roles_config()

        except ConfigurationError as e:
            self.logger.warning(f"Failed to load roles config: {e}")
            return await self._get_default_roles_config()

    async def _get_default_roles_config(self) -> Dict[str, Any]:
        """
        Get default roles configuration.

        Returns:
            Default roles configuration dictionary
        """
        return {
            "roles": {
                "admin": {
                    "description": "Administrator with full access",
                    "permissions": ["read", "write", "delete", "admin"],
                },
                "operator": {
                    "description": "Operator with limited access",
                    "permissions": ["read", "write"],
                },
                "monitor": {
                    "description": "Monitoring role with read-only access",
                    "permissions": ["read"],
                },
                "user": {
                    "description": "Basic user with minimal access",
                    "permissions": ["read"],
                },
            }
        }

    async def _get_default_policy(self) -> Dict[str, Any]:
        """
        Get default authorization policy.

        Returns:
            Default policy dictionary
        """
        return {
            "default_policy": {
                "allow_all": False,
                "public_endpoints": [
                    "/health",
                    "/docs",
                    "/openapi.json",
                    "/favicon.ico",
                    "/auth/login",
                    "/auth/refresh",
                ],
            }
        }

    async def generate_token(
        self,
        user_id: str,
        roles: Optional[List[str]] = None,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate JWT token for user.

        Args:
            user_id: User identifier
            roles: List of user roles
            additional_claims: Additional claims to include in token

        Returns:
            Generated JWT token
        """
        try:
            # Prepare token payload
            now = datetime.utcnow()
            payload = {
                "sub": user_id,
                "iat": now,
                "exp": now + timedelta(minutes=self.token_expire_minutes),
                "roles": roles or ["user"],
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
            raise TokenValidationError(f"Token generation failed: {e}")

    async def refresh_token(self, token: str) -> str:
        """
        Refresh JWT token.

        Args:
            token: Current JWT token

        Returns:
            New JWT token
        """
        try:
            # Validate current token
            validation_result = await self._validate_token(token)
            if not validation_result["valid"]:
                raise TokenInvalidError("Cannot refresh invalid token")

            payload = validation_result["payload"]

            # Generate new token with same claims
            user_id = payload.get("sub")
            roles = payload.get("roles", ["user"])

            return await self.generate_token(user_id, roles, payload)

        except ValidationError as e:
            self.logger.error(f"Failed to refresh token: {e}")
            raise TokenValidationError(f"Token refresh failed: {e}")
