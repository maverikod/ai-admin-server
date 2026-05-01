"""mTLS Authentication Manager for AI Admin Server.

This module provides comprehensive mTLS authentication management including
client certificate validation, role extraction, permission checking, and
integration with the role-based access control system.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

import logging
from ai_admin.core.custom_exceptions import SSLError, CustomError

from ..config.ssl_config import SSLConfig
from ..config.roles_config import RolesConfig
from .ssl_context_manager import SSLContextManager
from .ssl_error_handler import SSLErrorHandler


class MTLSAuthError(Exception):
    """Base exception for mTLS authentication errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "MTLS_AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class CertificateValidationError(MTLSAuthError):
    """Exception raised when certificate validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CERT_VALIDATION_ERROR", details)


class RoleExtractionError(MTLSAuthError):
    """Exception raised when role extraction from certificate fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "ROLE_EXTRACTION_ERROR", details)


class PermissionCheckError(MTLSAuthError):
    """Exception raised when permission check fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "PERMISSION_CHECK_ERROR", details)


class MTLSAuthManager:
    """
    Manager for mTLS authentication and authorization.

    This class provides comprehensive mTLS authentication management including:
    - Client certificate validation
    - Role extraction from certificates
    - Permission checking and authorization
    - Integration with role-based access control
    - Certificate chain validation
    - Security policy enforcement
    """

    def __init__(
        self,
        ssl_config: Optional[SSLConfig] = None,
        roles_config: Optional[RolesConfig] = None,
        ssl_context_manager: Optional[SSLContextManager] = None,
        error_handler: Optional[SSLErrorHandler] = None,
    ):
        """
        Initialize mTLS authentication manager.

        Args:
            ssl_config: SSL configuration instance
            roles_config: Roles configuration instance
            ssl_context_manager: SSL context manager instance
            error_handler: SSL error handler for comprehensive error management
        """
        self.logger = logging.getLogger("ai_admin.mtls_auth_manager")
        self.ssl_config = ssl_config
        self.roles_config = roles_config
        self.ssl_context_manager = ssl_context_manager
        self.error_handler = error_handler or SSLErrorHandler()

        # Cache for validated certificates and roles
        self._certificate_cache: Dict[str, Dict[str, Any]] = {}
        self._role_cache: Dict[str, List[str]] = {}
        self._cache_ttl = timedelta(hours=1)

        # Security settings
        self._require_certificate = True
        self._validate_certificate_chain = True
        self._check_certificate_expiry = True
        self._check_certificate_revocation = False
        self._max_certificate_age = timedelta(days=365)

        self.logger.info("MTLSAuthManager initialized")

    async def validate_client_certificate(
        self, certificate_data: bytes, certificate_chain: Optional[List[bytes]] = None
    ) -> x509.Certificate:
        """
        Validate client certificate and certificate chain.

        Args:
            certificate_data: Client certificate data in DER format
            certificate_chain: Optional certificate chain for validation

        Returns:
            Validated X.509 certificate object

        Raises:
            CertificateValidationError: If certificate validation fails
        """
        try:
            # Load certificate from DER data
            certificate = x509.load_der_x509_certificate(certificate_data)

            # Check certificate cache
            cert_fingerprint = self._get_certificate_fingerprint(certificate)
            if cert_fingerprint in self._certificate_cache:
                cached_data = self._certificate_cache[cert_fingerprint]
                if self._is_cache_valid(cached_data):
                    self.logger.debug("Using cached certificate validation")
                    return certificate

            # Validate certificate basic properties
            await self._validate_certificate_basic_properties(certificate)

            # Validate certificate chain if provided
            if certificate_chain and self._validate_certificate_chain:
                await self._validate_certificate_chain_async(
                    certificate, certificate_chain
                )

            # Check certificate expiry
            if self._check_certificate_expiry:
                await self._validate_certificate_expiry(certificate)

            # Check certificate age
            await self._validate_certificate_age(certificate)

            # Cache validated certificate
            self._certificate_cache[cert_fingerprint] = {
                "certificate": certificate,
                "validated_at": datetime.utcnow(),
                "is_valid": True,
            }

            self.logger.info(
                f"Client certificate validated successfully: {cert_fingerprint}"
            )
            return certificate

        except SSLError as e:
            error_msg = f"Certificate validation failed: {e}"
            self.logger.error(error_msg)

            # Handle error through error handler
            await self.error_handler.handle_mtls_error(
                error=e,
                operation="validate_client_certificate",
                user_roles=[],
                cert_info={"certificate_data_length": len(certificate_data)},
            )
            raise CertificateValidationError(error_msg, {"exception": str(e)})

    async def extract_roles_from_certificate(
        self, certificate: x509.Certificate
    ) -> List[str]:
        """
        Extract roles from certificate extensions and attributes.

        Args:
            certificate: X.509 certificate object

        Returns:
            List of roles extracted from certificate

        Raises:
            RoleExtractionError: If role extraction fails
        """
        try:
            # Check role cache
            cert_fingerprint = self._get_certificate_fingerprint(certificate)
            if cert_fingerprint in self._role_cache:
                self.logger.debug("Using cached roles")
                return self._role_cache[cert_fingerprint]

            roles = []

            # Try to extract roles from custom extension
            roles.extend(await self._extract_roles_from_custom_extension(certificate))

            # Try to extract roles from Subject Alternative Name
            if not roles:
                roles.extend(await self._extract_roles_from_san(certificate))

            # Try to extract roles from Subject attributes
            if not roles:
                roles.extend(await self._extract_roles_from_subject(certificate))

            # Try to extract roles from certificate OID mapping
            if not roles:
                roles.extend(await self._extract_roles_from_oid_mapping(certificate))

            # Cache extracted roles
            self._role_cache[cert_fingerprint] = roles

            self.logger.info(f"Extracted roles from certificate: {roles}")
            return roles

        except SSLError as e:
            error_msg = f"Role extraction failed: {e}"
            self.logger.error(error_msg)

            # Handle error through error handler
            await self.error_handler.handle_mtls_error(
                error=e,
                operation="extract_roles_from_certificate",
                user_roles=[],
                cert_info={
                    "certificate_serial": (
                        certificate.serial_number if certificate else None
                    )
                },
            )
            raise RoleExtractionError(error_msg, {"exception": str(e)})

    async def check_permissions(
        self,
        client_roles: List[str],
        required_permissions: List[str],
        resource: Optional[str] = None,
    ) -> bool:
        """
        Check if client roles have required permissions.

        Args:
            client_roles: List of client roles
            required_permissions: List of required permissions
            resource: Optional resource identifier

        Returns:
            True if client has required permissions, False otherwise

        Raises:
            PermissionCheckError: If permission check fails
        """
        try:
            if not self.roles_config:
                self.logger.warning("No roles configuration available, denying access")
                return False

            # Check if any client role has any of the required permissions
            for role_name in client_roles:
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
                f"Access denied: roles {client_roles} do not have required "
                f"permissions {required_permissions}"
            )
            return False

        except SSLError as e:
            error_msg = f"Permission check failed: {e}"
            self.logger.error(error_msg)

            # Handle error through error handler
            await self.error_handler.handle_mtls_error(
                error=e,
                operation="check_permissions",
                user_roles=client_roles,
                cert_info={
                    "required_permissions": required_permissions,
                    "resource": resource,
                },
            )
            raise PermissionCheckError(error_msg, {"exception": str(e)})

    async def authenticate_client(
        self,
        certificate_data: bytes,
        certificate_chain: Optional[List[bytes]] = None,
        required_permissions: Optional[List[str]] = None,
        resource: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Authenticate client and check permissions.

        Args:
            certificate_data: Client certificate data in DER format
            certificate_chain: Optional certificate chain for validation
            required_permissions: Optional list of required permissions
            resource: Optional resource identifier

        Returns:
            Authentication result dictionary with client information

        Raises:
            MTLSAuthError: If authentication fails
        """
        try:
            # Validate client certificate
            certificate = await self.validate_client_certificate(
                certificate_data, certificate_chain
            )

            # Extract roles from certificate
            client_roles = await self.extract_roles_from_certificate(certificate)

            # Check permissions if required
            has_permissions = True
            if required_permissions:
                has_permissions = await self.check_permissions(
                    client_roles, required_permissions, resource
                )

            # Get client identity
            client_identity = await self._get_client_identity(certificate)

            # Prepare authentication result
            auth_result = {
                "authenticated": True,
                "client_identity": client_identity,
                "client_roles": client_roles,
                "has_permissions": has_permissions,
                "certificate": certificate,
                "certificate_fingerprint": self._get_certificate_fingerprint(
                    certificate
                ),
                "authenticated_at": datetime.utcnow().isoformat(),
                "required_permissions": required_permissions,
                "resource": resource,
            }

            self.logger.info(
                f"Client authenticated successfully: {client_identity} "
                f"with roles {client_roles}"
            )
            return auth_result

        except (CertificateValidationError, RoleExtractionError, PermissionCheckError):
            raise
        except SSLError as e:
            error_msg = f"Client authentication failed: {e}"
            self.logger.error(error_msg)

            # Handle error through error handler
            await self.error_handler.handle_mtls_error(
                error=e,
                operation="authenticate_client",
                user_roles=[],
                cert_info={"certificate_data_length": len(certificate_data)},
            )
            raise MTLSAuthError(
                error_msg, "AUTHENTICATION_ERROR", {"exception": str(e)}
            )

    async def get_client_roles(self, certificate: x509.Certificate) -> List[str]:
        """
        Get client roles from certificate.

        Args:
            certificate: X.509 certificate object

        Returns:
            List of client roles
        """
        return await self.extract_roles_from_certificate(certificate)

    async def validate_certificate_chain(
        self, certificate: x509.Certificate, certificate_chain: List[bytes]
    ) -> bool:
        """
        Validate certificate chain.

        Args:
            certificate: Client certificate
            certificate_chain: Certificate chain for validation

        Returns:
            True if certificate chain is valid, False otherwise
        """
        try:
            return await self._validate_certificate_chain_async(
                certificate, certificate_chain
            )
        except SSLError as e:
            self.logger.error(f"Certificate chain validation failed: {e}")
            return False

    async def _validate_certificate_basic_properties(
        self, certificate: x509.Certificate
    ) -> None:
        """Validate basic certificate properties."""
        # Check certificate version
        if certificate.version != x509.Version.v3:
            raise CertificateValidationError(
                f"Unsupported certificate version: {certificate.version}"
            )

        # Check certificate serial number
        if certificate.serial_number <= 0:
            raise CertificateValidationError("Invalid certificate serial number")

        # Check certificate signature algorithm
        if not certificate.signature_algorithm_oid:
            raise CertificateValidationError("Certificate missing signature algorithm")

    async def _validate_certificate_chain_async(
        self, certificate: x509.Certificate, certificate_chain: List[bytes]
    ) -> bool:
        """Validate certificate chain asynchronously."""
        try:
            # Load certificate chain
            chain_certificates = []
            for cert_data in certificate_chain:
                chain_cert = x509.load_der_x509_certificate(cert_data)
                chain_certificates.append(chain_cert)

            # Basic chain validation
            if not chain_certificates:
                self.logger.warning("Empty certificate chain provided")
                return False

            # Check if the certificate is signed by any certificate in the chain
            for chain_cert in chain_certificates:
                try:
                    # Verify signature (simplified check)
                    if await self._verify_certificate_signature(
                        certificate, chain_cert
                    ):
                        self.logger.debug("Certificate chain validation successful")
                        return True
                except CustomError as e:
                    self.logger.debug(f"Signature verification failed: {e}")
                    continue

            self.logger.warning("Certificate chain validation failed")
            return False

        except SSLError as e:
            self.logger.error(f"Certificate chain validation error: {e}")
            return False

    async def _verify_certificate_signature(
        self, certificate: x509.Certificate, issuer_certificate: x509.Certificate
    ) -> bool:
        """Verify certificate signature against issuer certificate."""
        try:
            # Get issuer public key
            issuer_public_key = issuer_certificate.public_key()

            # Get certificate signature and data
            signature = certificate.signature
            tbs_certificate_bytes = certificate.tbs_certificate_bytes

            # Verify signature based on key type
            from cryptography.hazmat.primitives.asymmetric import (
                rsa,
                ec,
                ed25519,
                ed448,
                dsa,
            )

            # For RSA keys
            if isinstance(issuer_public_key, rsa.RSAPublicKey):
                issuer_public_key.verify(
                    signature,
                    tbs_certificate_bytes,
                    padding.PKCS1v15(),
                    hashes.SHA256(),
                )
            # For elliptic curve keys
            elif isinstance(issuer_public_key, ec.EllipticCurvePublicKey):
                issuer_public_key.verify(
                    signature, tbs_certificate_bytes, ec.ECDSA(hashes.SHA256())
                )
            # For Ed25519 keys
            elif isinstance(issuer_public_key, ed25519.Ed25519PublicKey):
                issuer_public_key.verify(signature, tbs_certificate_bytes)
            # For Ed448 keys
            elif isinstance(issuer_public_key, ed448.Ed448PublicKey):
                issuer_public_key.verify(signature, tbs_certificate_bytes)
            # For DSA keys
            elif isinstance(issuer_public_key, dsa.DSAPublicKey):
                issuer_public_key.verify(
                    signature, tbs_certificate_bytes, hashes.SHA256()
                )
            else:
                self.logger.debug(
                    f"Unsupported public key type: {type(issuer_public_key)}"
                )
                return False

            return True

        except CustomError as e:
            self.logger.debug(f"Signature verification failed: {e}")
            return False

    async def _validate_certificate_expiry(self, certificate: x509.Certificate) -> None:
        """Validate certificate expiry."""
        now = datetime.utcnow()

        # Check not before
        if certificate.not_valid_before > now:
            raise CertificateValidationError(
                f"Certificate not yet valid: {certificate.not_valid_before}"
            )

        # Check not after
        if certificate.not_valid_after < now:
            raise CertificateValidationError(
                f"Certificate expired: {certificate.not_valid_after}"
            )

    async def _validate_certificate_age(self, certificate: x509.Certificate) -> None:
        """Validate certificate age."""
        now = datetime.utcnow()
        cert_age = now - certificate.not_valid_before

        if cert_age > self._max_certificate_age:
            raise CertificateValidationError(
                f"Certificate too old: {cert_age} (max: {self._max_certificate_age})"
            )

    async def _extract_roles_from_custom_extension(
        self, certificate: x509.Certificate
    ) -> List[str]:
        """Extract roles from custom certificate extension."""
        roles = []

        try:
            # Try custom OID for roles
            custom_oid = x509.ObjectIdentifier("1.3.6.1.4.1.99999.1")
            extension = certificate.extensions.get_extension_for_oid(custom_oid)

            if extension and hasattr(extension.value, "value"):
                roles_data = extension.value.value
                if isinstance(roles_data, bytes):
                    roles = [
                        role.strip()
                        for role in roles_data.decode("utf-8").split(",")
                        if role.strip()
                    ]
                else:
                    roles = [str(roles_data)]

                self.logger.debug(f"Extracted roles from custom extension: {roles}")

        except x509.extensions.ExtensionNotFound:
            pass
        except CustomError as e:
            self.logger.debug(f"Failed to extract roles from custom extension: {e}")

        return roles

    async def _extract_roles_from_san(self, certificate: x509.Certificate) -> List[str]:
        """Extract roles from Subject Alternative Name extension."""
        roles = []

        try:
            san_extension = certificate.extensions.get_extension_for_oid(
                ExtensionOID.SUBJECT_ALTERNATIVE_NAME
            )

            if san_extension and hasattr(san_extension.value, "__iter__"):
                san = san_extension.value
                for name in san:
                    if hasattr(name, "value"):
                        name_value = str(name.value)
                        if name_value.startswith("role-"):
                            role = name_value[5:]  # Remove 'role-' prefix
                            roles.append(role)

                self.logger.debug(f"Extracted roles from SAN: {roles}")

        except x509.extensions.ExtensionNotFound:
            pass
        except CustomError as e:
            self.logger.debug(f"Failed to extract roles from SAN: {e}")

        return roles

    async def _extract_roles_from_subject(
        self, certificate: x509.Certificate
    ) -> List[str]:
        """Extract roles from certificate subject attributes."""
        roles = []

        try:
            subject = certificate.subject

            # Try Common Name
            cn_attrs = subject.get_attributes_for_oid(NameOID.COMMON_NAME)
            for cn_attr in cn_attrs:
                cn_value = str(cn_attr.value)
                if cn_value.startswith("role-"):
                    role = cn_value[5:]  # Remove 'role-' prefix
                    roles.append(role)

            # Try Organizational Unit
            ou_attrs = subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)
            for ou_attr in ou_attrs:
                ou_value = str(ou_attr.value)
                if ou_value.startswith("role-"):
                    role = ou_value[5:]  # Remove 'role-' prefix
                    roles.append(role)

            self.logger.debug(f"Extracted roles from subject: {roles}")

        except CustomError as e:
            self.logger.debug(f"Failed to extract roles from subject: {e}")

        return roles

    async def _extract_roles_from_oid_mapping(
        self, certificate: x509.Certificate
    ) -> List[str]:
        """Extract roles from certificate OID mapping in roles configuration."""
        roles: List[str] = []

        try:
            if not self.roles_config:
                return roles

            # Get certificate OID mappings from roles config
            cert_oid_mappings = self.roles_config._certificate_roles_mapping

            # Check each OID mapping
            for oid_str, mapped_roles in cert_oid_mappings.items():
                try:
                    oid = x509.ObjectIdentifier(oid_str)
                    extension = certificate.extensions.get_extension_for_oid(oid)

                    if extension:
                        # If extension exists, add mapped roles
                        roles.extend(mapped_roles)
                        self.logger.debug(
                            f"Extracted roles from OID mapping {oid_str}: "
                            f"{mapped_roles}"
                        )

                except x509.extensions.ExtensionNotFound:
                    pass
                except CustomError as e:
                    self.logger.debug(
                        f"Failed to extract roles from OID {oid_str}: {e}"
                    )

        except CustomError as e:
            self.logger.debug(f"Failed to extract roles from OID mapping: {e}")

        return roles

    async def _get_client_identity(self, certificate: x509.Certificate) -> str:
        """Get client identity from certificate."""
        try:
            # Try to get Common Name
            subject = certificate.subject
            cn_attrs = subject.get_attributes_for_oid(NameOID.COMMON_NAME)
            if cn_attrs:
                return str(cn_attrs[0].value)

            # Fallback to serial number
            return f"cert-{certificate.serial_number}"

        except CustomError:
            return "unknown"

    def _get_certificate_fingerprint(self, certificate: x509.Certificate) -> str:
        """Get certificate fingerprint for caching."""
        try:
            # Use SHA-256 fingerprint
            fingerprint = certificate.fingerprint(hashes.SHA256())
            return fingerprint.hex()
        except SSLError:
            # Fallback to serial number
            return str(certificate.serial_number)

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
        """Clear certificate and role caches."""
        self._certificate_cache.clear()
        self._role_cache.clear()
        self.logger.info("MTLS authentication cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "certificate_cache_size": len(self._certificate_cache),
            "role_cache_size": len(self._role_cache),
            "cache_ttl_hours": self._cache_ttl.total_seconds() / 3600,
        }

    def update_security_settings(
        self,
        require_certificate: Optional[bool] = None,
        validate_certificate_chain: Optional[bool] = None,
        check_certificate_expiry: Optional[bool] = None,
        check_certificate_revocation: Optional[bool] = None,
        max_certificate_age_days: Optional[int] = None,
    ) -> None:
        """Update security settings."""
        if require_certificate is not None:
            self._require_certificate = require_certificate
        if validate_certificate_chain is not None:
            self._validate_certificate_chain = validate_certificate_chain
        if check_certificate_expiry is not None:
            self._check_certificate_expiry = check_certificate_expiry
        if check_certificate_revocation is not None:
            self._check_certificate_revocation = check_certificate_revocation
        if max_certificate_age_days is not None:
            self._max_certificate_age = timedelta(days=max_certificate_age_days)

        self.logger.info("MTLS security settings updated")

    def get_security_settings(self) -> Dict[str, Any]:
        """Get current security settings."""
        return {
            "require_certificate": self._require_certificate,
            "validate_certificate_chain": self._validate_certificate_chain,
            "check_certificate_expiry": self._check_certificate_expiry,
            "check_certificate_revocation": self._check_certificate_revocation,
            "max_certificate_age_days": self._max_certificate_age.days,
        }
