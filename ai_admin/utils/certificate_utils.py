from ai_admin.core.custom_exceptions import CertificateError, CustomError, SSLError, ValidationError
"""
Certificate utilities for SSL/TLS certificate management.

This module provides comprehensive utilities for creating, validating, and managing
SSL/TLS certificates with role-based access control.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.backends import default_backend
from .certificate_exceptions import (
    CertificateError,
    CertificateValidationError,
    CertificateCreationError,
    CertificateRoleError
)


class CertificateUtils:
    """Utility class for SSL/TLS certificate operations."""
    
    # Custom OID for roles extension
    ROLES_OID = x509.ObjectIdentifier("1.3.6.1.4.1.99999.1")
    
    @staticmethod
    def create_ca_certificate(
        common_name: str,
        output_dir: str,
        organization: str = "AI Admin",
        organizational_unit: str = "Certificate Authority",
        country: str = "US",
        state: str = "Test State",
        locality: str = "Test City",
        validity_years: int = 10,
        key_size: int = 2048
    ) -> Dict[str, str]:
        """
        Create a self-signed CA certificate and private key.
        
        Args:
            common_name: Common name for the CA certificate
            output_dir: Directory to save certificate and key files
            organization: Organization name
            organizational_unit: Organizational unit
            country: Country code
            state: State or province
            locality: City or locality
            validity_years: Certificate validity period in years
            key_size: RSA key size in bits
            
        Returns:
            Dictionary with paths to created certificate and key files
            
        Raises:
            CertificateCreationError: If certificate creation fails
            ValueError: If parameters are invalid
        """
        try:
            # Validate parameters
            if not common_name or not output_dir:
                raise ValueError("Common name and output directory are required")
            
            if validity_years <= 0 or key_size < 1024:
                raise ValueError("Invalid validity period or key size")
            
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create private key
            private_key = CertificateUtils._create_private_key(key_size)
            
            # Create certificate subject
            subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, country),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
                x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, organizational_unit),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ])
            
            # Create certificate
            now = datetime.datetime.utcnow()
            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(subject)  # Self-signed
                .public_key(private_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now)
                .not_valid_after(now + datetime.timedelta(days=365 * validity_years))
                .add_extension(
                    x509.BasicConstraints(ca=True, path_length=None),
                    critical=True,
                )
                .add_extension(
                    x509.KeyUsage(
                        key_cert_sign=True,
                        crl_sign=True,
                        digital_signature=False,
                        content_commitment=False,
                        key_encipherment=False,
                        data_encipherment=False,
                        key_agreement=False,
                        encipher_only=False,
                        decipher_only=False,
                    ),
                    critical=True,
                )
                .sign(private_key, hashes.SHA256(), default_backend())
            )
            
            # Save certificate and key
            cert_path = output_path / f"{common_name}_ca.crt"
            key_path = output_path / f"{common_name}_ca.key"
            
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            with open(key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            return {
                "certificate_path": str(cert_path),
                "key_path": str(key_path),
                "common_name": common_name,
                "validity_years": str(validity_years)
            }
            
        except SSLError as e:
            raise CertificateCreationError(
                message=f"Failed to create CA certificate: {str(e)}",
                certificate_type="CA",
                output_path=output_dir,
                details={"error": str(e)}
            )
    
    @staticmethod
    def create_server_certificate(
        common_name: str,
        ca_cert_path: str,
        ca_key_path: str,
        output_dir: str,
        roles: Optional[List[str]] = None,
        organization: str = "AI Admin",
        organizational_unit: str = "Server",
        country: str = "US",
        state: str = "Test State",
        locality: str = "Test City",
        validity_years: int = 1,
        key_size: int = 2048
    ) -> Dict[str, str]:
        """
        Create a server certificate signed by CA with role-based access control.
        
        Args:
            common_name: Common name for the server certificate
            ca_cert_path: Path to CA certificate file
            ca_key_path: Path to CA private key file
            output_dir: Directory to save certificate and key files
            roles: List of roles to assign to the certificate
            organization: Organization name
            organizational_unit: Organizational unit
            country: Country code
            state: State or province
            locality: City or locality
            validity_years: Certificate validity period in years
            key_size: RSA key size in bits
            
        Returns:
            Dictionary with paths to created certificate and key files
            
        Raises:
            CertificateCreationError: If certificate creation fails
            CertificateValidationError: If CA certificate is invalid
        """
        try:
            # Validate parameters
            if not common_name or not ca_cert_path or not ca_key_path or not output_dir:
                raise ValueError("Common name, CA certificate, CA key, and output directory are required")
            
            # Load CA certificate and key
            ca_cert, ca_key = CertificateUtils._load_ca_certificate_and_key(ca_cert_path, ca_key_path)
            
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create private key
            private_key = CertificateUtils._create_private_key(key_size)
            
            # Create certificate subject
            subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, country),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
                x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, organizational_unit),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ])
            
            # Create certificate
            now = datetime.datetime.utcnow()
            cert_builder = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(ca_cert.subject)
                .public_key(private_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now)
                .not_valid_after(now + datetime.timedelta(days=365 * validity_years))
                .add_extension(
                    x509.BasicConstraints(ca=False, path_length=None),
                    critical=True,
                )
                .add_extension(
                    x509.KeyUsage(
                        key_cert_sign=False,
                        crl_sign=False,
                        digital_signature=True,
                        content_commitment=False,
                        key_encipherment=True,
                        data_encipherment=False,
                        key_agreement=False,
                        encipher_only=False,
                        decipher_only=False,
                    ),
                    critical=True,
                )
                .add_extension(
                    x509.ExtendedKeyUsage([
                        x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
                    ]),
                    critical=True,
                )
            )
            
            # Add roles extension if roles are provided
            if roles:
                roles_extension = CertificateUtils._create_roles_extension(roles)
                cert_builder = cert_builder.add_extension(roles_extension, critical=False)
            
            cert = cert_builder.sign(ca_key, hashes.SHA256(), default_backend())
            
            # Save certificate and key
            cert_path = output_path / f"{common_name}_server.crt"
            key_path = output_path / f"{common_name}_server.key"
            
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            with open(key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            return {
                "certificate_path": str(cert_path),
                "key_path": str(key_path),
                "common_name": common_name,
                "roles": str(roles or []),
                "validity_years": str(validity_years)
            }
            
        except SSLError as e:
            raise CertificateCreationError(
                message=f"Failed to create server certificate: {str(e)}",
                certificate_type="Server",
                output_path=output_dir,
                details={"error": str(e)}
            )
    
    @staticmethod
    def create_client_certificate(
        common_name: str,
        ca_cert_path: str,
        ca_key_path: str,
        output_dir: str,
        roles: Optional[List[str]] = None,
        organization: str = "AI Admin",
        organizational_unit: str = "Client",
        country: str = "US",
        state: str = "Test State",
        locality: str = "Test City",
        validity_years: int = 1,
        key_size: int = 2048
    ) -> Dict[str, str]:
        """
        Create a client certificate signed by CA with role-based access control.
        
        Args:
            common_name: Common name for the client certificate
            ca_cert_path: Path to CA certificate file
            ca_key_path: Path to CA private key file
            output_dir: Directory to save certificate and key files
            roles: List of roles to assign to the certificate
            organization: Organization name
            organizational_unit: Organizational unit
            country: Country code
            state: State or province
            locality: City or locality
            validity_years: Certificate validity period in years
            key_size: RSA key size in bits
            
        Returns:
            Dictionary with paths to created certificate and key files
            
        Raises:
            CertificateCreationError: If certificate creation fails
            CertificateValidationError: If CA certificate is invalid
        """
        try:
            # Validate parameters
            if not common_name or not ca_cert_path or not ca_key_path or not output_dir:
                raise ValueError("Common name, CA certificate, CA key, and output directory are required")
            
            # Load CA certificate and key
            ca_cert, ca_key = CertificateUtils._load_ca_certificate_and_key(ca_cert_path, ca_key_path)
            
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create private key
            private_key = CertificateUtils._create_private_key(key_size)
            
            # Create certificate subject
            subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, country),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
                x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, organizational_unit),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ])
            
            # Create certificate
            now = datetime.datetime.utcnow()
            cert_builder = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(ca_cert.subject)
                .public_key(private_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now)
                .not_valid_after(now + datetime.timedelta(days=365 * validity_years))
                .add_extension(
                    x509.BasicConstraints(ca=False, path_length=None),
                    critical=True,
                )
                .add_extension(
                    x509.KeyUsage(
                        key_cert_sign=False,
                        crl_sign=False,
                        digital_signature=True,
                        content_commitment=False,
                        key_encipherment=False,
                        data_encipherment=False,
                        key_agreement=False,
                        encipher_only=False,
                        decipher_only=False,
                    ),
                    critical=True,
                )
                .add_extension(
                    x509.ExtendedKeyUsage([
                        x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                    ]),
                    critical=True,
                )
            )
            
            # Add roles extension if roles are provided
            if roles:
                roles_extension = CertificateUtils._create_roles_extension(roles)
                cert_builder = cert_builder.add_extension(roles_extension, critical=False)
            
            cert = cert_builder.sign(ca_key, hashes.SHA256(), default_backend())
            
            # Save certificate and key
            cert_path = output_path / f"{common_name}_client.crt"
            key_path = output_path / f"{common_name}_client.key"
            
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            with open(key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            return {
                "certificate_path": str(cert_path),
                "key_path": str(key_path),
                "common_name": common_name,
                "roles": str(roles or []),
                "validity_years": str(validity_years)
            }
            
        except SSLError as e:
            raise CertificateCreationError(
                message=f"Failed to create client certificate: {str(e)}",
                certificate_type="Client",
                output_path=output_dir,
                details={"error": str(e)}
            )
    
    @staticmethod
    def extract_roles_from_certificate(cert_path: str) -> List[str]:
        """
        Extract roles from a certificate's custom extension.
        
        Args:
            cert_path: Path to certificate file
            
        Returns:
            List of roles assigned to the certificate
            
        Raises:
            CertificateValidationError: If certificate is invalid
            CertificateRoleError: If roles cannot be extracted
        """
        try:
            # Load certificate
            with open(cert_path, "rb") as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            
            # Look for roles extension
            try:
                roles_extension = cert.extensions.get_extension_for_oid(CertificateUtils.ROLES_OID)
                roles_data = roles_extension.value
                roles = str(roles_data).split(',')
                return [role.strip() for role in roles if role.strip()]
            except x509.ExtensionNotFound:
                return []
                
        except SSLError as e:
            raise CertificateRoleError(
                message=f"Failed to extract roles from certificate: {str(e)}",
                operation="extract_roles",
                certificate_path=cert_path,
                details={"error": str(e)}
            )
    
    @staticmethod
    def validate_certificate_chain(
        cert_path: str,
        ca_cert_path: str,
        check_revocation: bool = False
    ) -> bool:
        """
        Validate certificate against CA certificate.
        
        Args:
            cert_path: Path to certificate file to validate
            ca_cert_path: Path to CA certificate file
            check_revocation: Whether to check certificate revocation
            
        Returns:
            True if certificate is valid, False otherwise
            
        Raises:
            CertificateValidationError: If certificates are invalid
        """
        try:
            # Load certificates
            with open(cert_path, "rb") as f:
                cert_data = f.read()
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            
            with open(ca_cert_path, "rb") as f:
                ca_cert_data = f.read()
            ca_cert = x509.load_pem_x509_certificate(ca_cert_data, default_backend())
            
            # Basic validation
            now = datetime.datetime.utcnow()
            if cert.not_valid_before > now or cert.not_valid_after < now:
                return False
            
            # Check if certificate is signed by CA
            try:
                # For now, just check that the issuer matches the CA subject
                # This is a simplified validation - in production you'd want full signature verification
                if cert.issuer == ca_cert.subject:
                    return True
                else:
                    return False
            except CustomError as e:
                return False
                
        except SSLError as e:
            raise CertificateValidationError(
                message=f"Certificate validation failed: {str(e)}",
                certificate_path=cert_path,
                validation_type="chain_validation",
                details={"error": str(e)}
            )
    
    @staticmethod
    def get_certificate_info(cert_path: str) -> Dict[str, Any]:
        """
        Get basic information about a certificate.
        
        Args:
            cert_path: Path to certificate file
            
        Returns:
            Dictionary with certificate information
            
        Raises:
            CertificateValidationError: If certificate is invalid
        """
        try:
            # Load certificate
            with open(cert_path, "rb") as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            
            # Extract basic information
            info = {
                "subject": str(cert.subject),
                "issuer": str(cert.issuer),
                "serial_number": str(cert.serial_number),
                "not_valid_before": cert.not_valid_before.isoformat(),
                "not_valid_after": cert.not_valid_after.isoformat(),
                "version": cert.version.name,
                "signature_algorithm": cert.signature_algorithm_oid._name,
                "fingerprint": cert.fingerprint(hashes.SHA256()).hex(),
                "is_ca": False,
                "roles": []
            }
            
            # Check if it's a CA certificate
            try:
                basic_constraints = cert.extensions.get_extension_for_oid(ExtensionOID.BASIC_CONSTRAINTS)
                info["is_ca"] = basic_constraints.value.ca  # type: ignore
            except x509.ExtensionNotFound:
                pass
            
            # Extract roles
            try:
                info["roles"] = CertificateUtils.extract_roles_from_certificate(cert_path)
            except CertificateRoleError:
                pass
            
            return info
            
        except SSLError as e:
            raise CertificateValidationError(
                message=f"Failed to get certificate info: {str(e)}",
                certificate_path=cert_path,
                validation_type="info_extraction",
                details={"error": str(e)}
            )
    
    @staticmethod
    def _create_private_key(key_size: int) -> rsa.RSAPrivateKey:
        """
        Create RSA private key.
        
        Args:
            key_size: RSA key size in bits
            
        Returns:
            RSA private key object
        """
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
    
    @staticmethod
    def _load_ca_certificate_and_key(ca_cert_path: str, ca_key_path: str) -> Tuple[x509.Certificate, Any]:
        """
        Load CA certificate and private key from files.
        
        Args:
            ca_cert_path: Path to CA certificate file
            ca_key_path: Path to CA private key file
            
        Returns:
            Tuple of (CA certificate, CA private key)
            
        Raises:
            CertificateValidationError: If files cannot be loaded
        """
        try:
            # Load CA certificate
            with open(ca_cert_path, "rb") as f:
                ca_cert_data = f.read()
            ca_cert = x509.load_pem_x509_certificate(ca_cert_data, default_backend())
            
            # Load CA private key
            with open(ca_key_path, "rb") as f:
                ca_key_data = f.read()
            ca_key = serialization.load_pem_private_key(ca_key_data, password=None, backend=default_backend())
            
            return ca_cert, ca_key
            
        except SSLError as e:
            raise CertificateValidationError(
                message=f"Failed to load CA certificate and key: {str(e)}",
                certificate_path=ca_cert_path,
                validation_type="ca_loading",
                details={"error": str(e)}
            )
    
    @staticmethod
    def _create_roles_extension(roles: List[str]) -> x509.UnrecognizedExtension:
        """
        Create custom roles extension for certificate.
        
        Args:
            roles: List of roles to assign
            
        Returns:
            Custom extension object
        """
        roles_data = ','.join(roles).encode('utf-8')
        return x509.UnrecognizedExtension(
            oid=CertificateUtils.ROLES_OID,
            value=roles_data
        )
