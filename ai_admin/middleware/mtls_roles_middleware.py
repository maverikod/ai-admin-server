from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, SSLError, ValidationError
"""mTLS Roles Middleware for role-based authentication.

This middleware validates client certificates and enforces role-based access control.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import os
from typing import Dict, Any, List, Optional, Callable, Tuple
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from fastapi import status
from fastapi.responses import JSONResponse

import logging

from .middleware_exceptions import (
    CertificateValidationError,
    RoleValidationError,
)


class MTLSRolesMiddleware:
    """Middleware for validating mTLS client certificates based on roles."""

    def __init__(
        self,
        app: Callable,
        roles_config_path: str = "config/roles.json",
        default_policy: Optional[Dict[str, Any]] = None,
        require_certificate: bool = True,
        allow_no_cert_endpoints: Optional[List[str]] = None,
    ):
        """
        Initialize mTLS roles middleware.

        Args:
            app: ASGI application
            roles_config_path: Path to roles configuration file
            default_policy: Default access policy if roles config not found
            require_certificate: Whether to require client certificates
            allow_no_cert_endpoints: List of endpoints that don't require certificates
        """
        self.app = app
        self.roles_config_path = roles_config_path
        self.require_certificate = require_certificate
        self.allow_no_cert_endpoints = allow_no_cert_endpoints or [
            "/health",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
        ]
        self.logger = logging.getLogger("ai_admin.middleware.mtls_roles")

        # Load roles configuration
        self.roles_config = self._load_roles_config()
        if not self.roles_config and default_policy:
            self.roles_config = default_policy
            self.logger.warning("Using default policy as roles config not found")

        self.logger.info(
            f"MTLSRolesMiddleware initialized with config: {roles_config_path}"
        )

    async def __call__(
        self, scope: Dict[str, Any], receive: Callable, send: Callable
    ) -> None:
        """
        Process ASGI request with role validation.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            # Extract request information
            request_path = scope.get("path", "")
            request_method = scope.get("method", "GET")

            # Check if endpoint allows no certificate
            if self._is_no_cert_endpoint(request_path):
                self.logger.debug(f"Endpoint {request_path} allows no certificate")
                await self.app(scope, receive, send)
                return

            # Extract client certificate
            client_cert = self._extract_client_certificate(scope)

            if not client_cert and self.require_certificate:
                await self._send_unauthorized(
                    send, "Client certificate required", "MISSING_CERTIFICATE"
                )
                return

            if not client_cert:
                self.logger.debug("No client certificate found, allowing request")
                await self.app(scope, receive, send)
                return

            # Extract roles from certificate
            client_roles = self._extract_roles_from_certificate(client_cert)
            self.logger.debug(f"Client roles: {client_roles}")

            # Validate role access
            has_access, error_message = self._validate_role_access(client_roles, scope)

            if not has_access:
                await self._send_forbidden(
                    send,
                    error_message,
                    "ACCESS_DENIED",
                    {
                        "client_roles": client_roles,
                        "endpoint": request_path,
                        "method": request_method,
                    },
                )
                return

            # Add client information to scope for downstream processing
            scope["client_certificate"] = client_cert
            scope["client_roles"] = client_roles
            scope["client_identity"] = self._get_client_identity(client_cert)

            self.logger.info(
                f"Access granted to {request_method} {request_path} "
                f"for roles: {client_roles}"
            )

            await self.app(scope, receive, send)

        except CertificateValidationError as e:
            self.logger.error(f"Certificate validation error: {e.message}")
            await self._send_unauthorized(
                send, "Invalid client certificate", "CERT_VALIDATION_ERROR", e.details
            )
        except RoleValidationError as e:
            self.logger.error(f"Role validation error: {e.message}")
            await self._send_forbidden(
                send, "Insufficient permissions", "ROLE_VALIDATION_ERROR", e.details
            )
        except SSLError as e:
            self.logger.error(f"Unexpected error in MTLS middleware: {e}")
            await self._send_internal_error(
                send, "Internal server error", "INTERNAL_ERROR"
            )

    def _load_roles_config(self) -> Optional[Dict[str, Any]]:
        """
        Load roles configuration from file.

        Returns:
            Roles configuration dictionary or None if not found
        """
        try:
            if not os.path.exists(self.roles_config_path):
                self.logger.warning(
                    f"Roles config file not found: {self.roles_config_path}"
                )
                return None

            with open(self.roles_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            self.logger.info(
                f"Loaded roles configuration from {self.roles_config_path}"
            )
            return config if isinstance(config, dict) else None

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in roles config: {e}")
            return None
        except ConfigurationError as e:
            self.logger.error(f"Failed to load roles config: {e}")
            return None

    def _extract_client_certificate(
        self, scope: Dict[str, Any]
    ) -> Optional[x509.Certificate]:
        """
        Extract client certificate from SSL context in ASGI scope.

        Args:
            scope: ASGI scope dictionary

        Returns:
            Client certificate object or None if not found

        Raises:
            CertificateValidationError: If certificate extraction fails
        """
        try:
            # Check for SSL context in scope
            if "ssl" not in scope:
                return None

            ssl_context = scope["ssl"]

            # Try to get peer certificate
            if hasattr(ssl_context, "getpeercert"):
                try:
                    cert_data = ssl_context.getpeercert(binary_form=True)
                    if cert_data:
                        cert = x509.load_der_x509_certificate(cert_data)
                        self.logger.debug(
                            "Extracted client certificate from SSL context"
                        )
                        return cert
                except SSLError as e:
                    self.logger.warning(f"Failed to get peer certificate: {e}")

            # Try to get certificate from connection
            if hasattr(ssl_context, "getpeercert_chain"):
                try:
                    cert_chain = ssl_context.getpeercert_chain()
                    if cert_chain:
                        # Use the first certificate in the chain (client cert)
                        cert_data = cert_chain[0]
                        cert = x509.load_der_x509_certificate(cert_data)
                        self.logger.debug(
                            "Extracted client certificate from certificate chain"
                        )
                        return cert
                except SSLError as e:
                    self.logger.warning(f"Failed to get certificate chain: {e}")

            return None

        except SSLError as e:
            raise CertificateValidationError(
                f"Failed to extract client certificate: {e}",
                validation_details={"error": str(e)},
            )

    def _extract_roles_from_certificate(self, cert: x509.Certificate) -> List[str]:
        """
        Extract roles from certificate extensions.

        Args:
            cert: X.509 certificate object

        Returns:
            List of roles extracted from certificate
        """
        roles = []

        try:
            # Try custom extension first (OID for roles)
            custom_oid = x509.ObjectIdentifier(
                "1.3.6.1.4.1.99999.1"
            )  # Custom OID for roles
            try:
                extension = cert.extensions.get_extension_for_oid(custom_oid)
                if extension and hasattr(extension.value, "value"):
                    roles_data = extension.value.value
                    if isinstance(roles_data, bytes):
                        roles = [
                            role.strip()
                            for role in roles_data.decode("utf-8").split(",")
                        ]
                    else:
                        roles = [str(roles_data)]
                    self.logger.debug(f"Extracted roles from custom extension: {roles}")
            except x509.extensions.ExtensionNotFound:
                pass

            # Fallback to DNS names in SAN (Subject Alternative Name)
            if not roles:
                try:
                    san_extension = cert.extensions.get_extension_for_oid(
                        ExtensionOID.SUBJECT_ALTERNATIVE_NAME
                    )
                    if san_extension and hasattr(san_extension.value, "__iter__"):
                        san = san_extension.value
                        # Extract DNS names that start with 'role-'
                        for name in san:
                            if hasattr(name, "value") and str(name.value).startswith(
                                "role-"
                            ):
                                role = str(name.value)[5:]  # Remove 'role-' prefix
                                roles.append(role)
                        self.logger.debug(f"Extracted roles from SAN: {roles}")
                except x509.extensions.ExtensionNotFound:
                    pass

            # Fallback to Common Name in subject
            if not roles:
                try:
                    subject = cert.subject
                    cn_attr = subject.get_attributes_for_oid(NameOID.COMMON_NAME)
                    if cn_attr:
                        cn_value = str(cn_attr[0].value)
                        if cn_value.startswith("role-"):
                            role = cn_value[5:]  # Remove 'role-' prefix
                            roles.append(role)
                            self.logger.debug(f"Extracted role from CN: {role}")
                except CustomError as e:
                    self.logger.debug(f"Failed to extract role from CN: {e}")

            # If still no roles, try to extract from organization unit
            if not roles:
                try:
                    subject = cert.subject
                    ou_attrs = subject.get_attributes_for_oid(
                        NameOID.ORGANIZATIONAL_UNIT_NAME
                    )
                    for ou_attr in ou_attrs:
                        ou_value = str(ou_attr.value)
                        if ou_value.startswith("role-"):
                            role = ou_value[5:]  # Remove 'role-' prefix
                            roles.append(role)
                    self.logger.debug(f"Extracted roles from OU: {roles}")
                except CustomError as e:
                    self.logger.debug(f"Failed to extract roles from OU: {e}")

            return roles

        except SSLError as e:
            self.logger.warning(f"Failed to extract roles from certificate: {e}")
            return []

    def _validate_role_access(
        self, client_roles: List[str], scope: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validate if client roles have access to the requested endpoint.

        Args:
            client_roles: List of roles from client certificate
            scope: ASGI scope dictionary

        Returns:
            Tuple of (has_access, error_message)
        """
        try:
            if not self.roles_config:
                # If no roles config, allow access (permissive mode)
                self.logger.debug("No roles config found, allowing access")
                return True, ""

            request_path = scope.get("path", "")
            request_method = scope.get("method", "GET")

            # Get roles configuration
            roles = self.roles_config.get("roles", {}) if self.roles_config else {}

            # Check if any client role has access
            for role_name in client_roles:
                if role_name in roles:
                    role_config = roles[role_name]

                    # Check permissions
                    permissions = role_config.get("permissions", {})
                    if self._check_permissions_dict(
                        permissions, request_method, request_path
                    ):
                        return True, ""

            # If no role has access, check for wildcard or default access
            if self._check_default_access(request_path, request_method):
                return True, ""

            error_msg = (
                f"Access denied: roles {client_roles} do not have permission "
                f"for {request_method} {request_path}"
            )
            return False, error_msg

        except ValidationError as e:
            self.logger.error(f"Error validating role access: {e}")
            return False, f"Role validation error: {e}"

    def _check_permissions_dict(
        self, permissions: Dict[str, List[str]], method: str, path: str
    ) -> bool:
        """
        Check if permissions dictionary allows access to the endpoint.

        Args:
            permissions: Dictionary of permissions for the role (method -> paths)
            method: HTTP method
            path: Request path

        Returns:
            True if access is allowed
        """
        # Get allowed paths for the method
        allowed_paths = permissions.get(method.upper(), [])
        
        # Check if path matches any allowed pattern
        for pattern in allowed_paths:
            if self._path_matches_pattern(path, pattern):
                return True
        
        return False

    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """
        Check if path matches the given pattern.

        Args:
            path: Request path
            pattern: Pattern to match (supports * wildcard)

        Returns:
            True if path matches pattern
        """
        import fnmatch
        return fnmatch.fnmatch(path, pattern)

    def _check_permissions(
        self, permissions: List[str], method: str, path: str
    ) -> bool:
        """
        Check if permissions allow access to the endpoint.

        Args:
            permissions: List of permissions for the role
            method: HTTP method
            path: Request path

        Returns:
            True if access is allowed
        """
        # Check for wildcard permission
        if "*" in permissions or "all" in permissions:
            return True

        # Check for read permission
        if method.upper() in ["GET", "HEAD", "OPTIONS"] and "read" in permissions:
            return True

        # Check for write permission
        if method.upper() in ["POST", "PUT", "PATCH"] and "write" in permissions:
            return True

        # Check for delete permission
        if method.upper() == "DELETE" and "delete" in permissions:
            return True

        # Check for admin permission
        if "admin" in permissions:
            return True

        return False

    def _check_default_access(self, path: str, method: str) -> bool:
        """
        Check if endpoint has default access.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            True if default access is allowed
        """
        # Check default policy
        if self.roles_config:
            default_policy = self.roles_config.get("default_policy", {})
            if default_policy.get("allow_all", False):
                return True

            # Check for public endpoints
            public_endpoints = default_policy.get("public_endpoints", [])
            for endpoint in public_endpoints:
                if path.startswith(endpoint):
                    return True

        return False

    def _is_no_cert_endpoint(self, path: str) -> bool:
        """
        Check if endpoint allows no certificate.

        Args:
            path: Request path

        Returns:
            True if endpoint allows no certificate
        """
        for endpoint in self.allow_no_cert_endpoints:
            if path.startswith(endpoint):
                return True
        return False

    def _get_client_identity(self, cert: x509.Certificate) -> str:
        """
        Get client identity from certificate.

        Args:
            cert: Client certificate

        Returns:
            Client identity string
        """
        try:
            # Try to get Common Name
            subject = cert.subject
            cn_attr = subject.get_attributes_for_oid(NameOID.COMMON_NAME)
            if cn_attr:
                return str(cn_attr[0].value)

            # Fallback to serial number
            return f"cert-{cert.serial_number}"

        except CustomError:
            return "unknown"

    async def _send_unauthorized(
        self,
        send: Callable,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send 401 Unauthorized response."""
        response_body = {
            "error": "Unauthorized",
            "message": message,
            "error_code": error_code,
            "details": details or {},
        }

        response = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content=response_body
        )

        # Create proper ASGI response
        async def asgi_receive() -> Dict[str, Any]:
            return {"type": "http.request", "body": b""}

        await response(scope={"type": "http"}, receive=asgi_receive, send=send)

    async def _send_forbidden(
        self,
        send: Callable,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send 403 Forbidden response."""
        response_body = {
            "error": "Forbidden",
            "message": message,
            "error_code": error_code,
            "details": details or {},
        }

        response = JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN, content=response_body
        )

        # Create proper ASGI response
        async def asgi_receive() -> Dict[str, Any]:
            return {"type": "http.request", "body": b""}

        await response(scope={"type": "http"}, receive=asgi_receive, send=send)

    async def _send_internal_error(
        self, send: Callable, message: str, error_code: str
    ) -> None:
        """Send 500 Internal Server Error response."""
        response_body = {
            "error": "Internal Server Error",
            "message": message,
            "error_code": error_code,
        }

        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response_body
        )

        # Create proper ASGI response
        async def asgi_receive() -> Dict[str, Any]:
            return {"type": "http.request", "body": b""}

        await response(scope={"type": "http"}, receive=asgi_receive, send=send)
