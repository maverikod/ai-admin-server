"""Module ssl_cert_generate_impl."""

from ai_admin.core.custom_exceptions import CertificateError, SSLError
import os
from pathlib import Path
import subprocess
import tempfile
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.utils.certificate_utils import CertificateUtils
from ai_admin.utils.certificate_exceptions import CertificateCreationError, CertificateError
from ai_admin.security.ssl_security_adapter import (
    SSLSecurityAdapter,
    SSLOperation,
    SSLCertificateType,
)
from mcp_security_framework import CertificateManager
from mcp_security_framework.schemas import CertificateConfig

class SSLCertGenerateCommand(BaseUnifiedCommand):
    """Command to generate SSL certificates and keys."""

    name = "ssl_cert_generate"

    def _get_default_operation(self) -> str:
        """Get default operation name for SSLCertGenerateCommand."""
        return "sslcertgenerate:execute"

    def __init__(self) -> None:
        """Initialize SSL certificate generation command with security adapter."""
        super().__init__()
        self.ssl_security_adapter = SSLSecurityAdapter()
        # Initialize CertificateManager for certificate operations
        self.cert_config = CertificateConfig()
        self.cert_manager = CertificateManager(self.cert_config)

    async def execute(
        self,
        cert_type: str = "self_signed",
        common_name: str = "localhost",
        country: str = "US",
        state: str = "State",
        locality: str = "City",
        organization: str = "Organization",
        organizational_unit: str = "IT",
        email: str = "admin@example.com",
        key_size: int = 2048,
        days_valid: int = 365,
        output_dir: Optional[str] = None,
        extensions: Optional[Dict[str, Any]] = None,
        key_usage: Optional[List[str]] = None,
        extended_key_usage: Optional[List[str]] = None,
        subject_alt_names: Optional[List[str]] = None,
        basic_constraints: Optional[Dict[str, Any]] = None,
        roles: Optional[List[str]] = None,
        ca_cert_path: Optional[str] = None,
        ca_key_path: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ):
        """
        Generate SSL certificates and keys with role-based access control.

        Args:
            cert_type: Type of certificate (self_signed, ca_signed, server, client)
            common_name: Common Name for the certificate
            country: Country code (2 letters)
            state: State or province
            locality: City or locality
            organization: Organization name
            organizational_unit: Organizational unit
            email: Email address
            key_size: Key size in bits (2048, 4096)
            days_valid: Number of days certificate is valid
            roles: List of roles to assign to the certificate
            ca_cert_path: Path to CA certificate (for ca_signed, server, client)
            ca_key_path: Path to CA private key (for ca_signed, server, client)
            output_dir: Output directory for certificates
            extensions: Custom x509 extensions
            key_usage: Key usage extensions (digitalSignature, keyEncipherment, etc.)
            extended_key_usage: Extended key usage (serverAuth, clientAuth, etc.)
            subject_alt_names: Subject Alternative Names (DNS, IP addresses)
            basic_constraints: Basic constraints (CA:TRUE/FALSE, pathlen)
            user_roles: List of user roles for security validation
        """
        try:
            # Security validation
            user_roles = user_roles or []

            # Validate SSL operation
            operation_params = {
                "cert_type": cert_type,
                "common_name": common_name,
                "output_dir": output_dir,
                "roles": roles,
            }

            is_valid, error_msg = self.ssl_security_adapter.validate_ssl_operation(
                SSLOperation.GENERATE, user_roles, operation_params
            )

            if not is_valid:
                return ErrorResult(
                    message="Security validation failed: {error_msg}",
                    code="SECURITY_VALIDATION_FAILED",
                    details={"error": error_msg, "user_roles": user_roles},
                )

            # Check certificate type permissions
            try:
                cert_type_enum = SSLCertificateType(cert_type)
                has_cert_permission, cert_error = self.ssl_security_adapter.check_ssl_certificate_permissions(
                    user_roles, cert_type_enum, SSLOperation.GENERATE
                )

                if not has_cert_permission:
                    return ErrorResult(
                        message="Certificate type permission denied: {cert_error}",
                        code="CERT_TYPE_PERMISSION_DENIED",
                        details={"cert_type": cert_type, "error": cert_error},
                    )
            except ValueError:
                return ErrorResult(
                    message="Invalid certificate type: {cert_type}",
                    code="INVALID_CERT_TYPE",
                    details={
                        "cert_type": cert_type,
                        "supported_types": [t.value for t in SSLCertificateType],
                    },
                )
            if not output_dir:
                output_dir = os.path.expanduser("~/.ssl-certs")

            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Integrate with mcp-security-framework for certificate management
            try:
                # Register certificate operation with security framework
                cert_metadata = {
                    "cert_type": cert_type,
                    "common_name": common_name,
                    "organization": organization,
                    "user_roles": user_roles,
                    "output_dir": output_dir,
                    "timestamp": datetime.now().isoformat(),
                }

                # Store certificate metadata in security framework
                self.cert_manager.register_certificate_operation(operation="generate", metadata=cert_metadata)
            except SSLError as e:
                # Log warning but continue with certificate generation
                import logging

                logging.warning("Failed to register with security framework: {e}")

            # Use new certificate utilities for enhanced functionality
            if cert_type == "ca":
                return await self._generate_ca_certificate(
                    common_name,
                    country,
                    state,
                    locality,
                    organization,
                    organizational_unit,
                    key_size,
                    days_valid,
                    output_dir,
                )
            elif cert_type == "server":
                return await self._generate_server_certificate(
                    common_name,
                    country,
                    state,
                    locality,
                    organization,
                    organizational_unit,
                    key_size,
                    days_valid,
                    output_dir,
                    roles,
                    ca_cert_path,
                    ca_key_path,
                )
            elif cert_type == "client":
                return await self._generate_client_certificate(
                    common_name,
                    country,
                    state,
                    locality,
                    organization,
                    organizational_unit,
                    key_size,
                    days_valid,
                    output_dir,
                    roles,
                    ca_cert_path,
                    ca_key_path,
                )
            elif cert_type == "self_signed":
                return await self._generate_self_signed_cert(
                    common_name,
                    country,
                    state,
                    locality,
                    organization,
                    organizational_unit,
                    email,
                    key_size,
                    days_valid,
                    output_dir,
                    key_usage,
                    extended_key_usage,
                    subject_alt_names,
                    basic_constraints,
                    extensions,
                )
            elif cert_type == "ca_signed":
                return await self._generate_ca_signed_cert(
                    common_name,
                    country,
                    state,
                    locality,
                    organization,
                    organizational_unit,
                    email,
                    key_size,
                    days_valid,
                    output_dir,
                    key_usage,
                    extended_key_usage,
                    subject_alt_names,
                    basic_constraints,
                    extensions,
                )
            elif cert_type == "wildcard":
                return await self._generate_wildcard_cert(
                    common_name,
                    country,
                    state,
                    locality,
                    organization,
                    organizational_unit,
                    email,
                    key_size,
                    days_valid,
                    output_dir,
                    key_usage,
                    extended_key_usage,
                    subject_alt_names,
                    basic_constraints,
                    extensions,
                )
            else:
                return ErrorResult(
                    message="Unsupported certificate type: {cert_type}",
                    code="UNSUPPORTED_CERT_TYPE",
                    details={
                        "supported_types": [
                            "ca",
                            "server",
                            "client",
                            "self_signed",
                            "ca_signed",
                            "wildcard",
                        ]
                    },
                )

        except SSLError as e:
            # Audit failed operation
            self.ssl_security_adapter.audit_ssl_operation(
                SSLOperation.GENERATE,
                user_roles or [],
                operation_params,
                {"error": str(e)},
            )

            return ErrorResult(
                message="Failed to generate certificate: {str(e)}",
                code="CERT_GENERATION_FAILED",
                details={"exception": str(e)},
            )

    async def _generate_self_signed_cert(
        self,
        common_name: str,
        country: str,
        state: str,
        locality: str,
        organization: str,
        organizational_unit: str,
        email: str,
        key_size: int,
        days_valid: int,
        output_dir: str,
        key_usage: Optional[List[str]] = None,
        extended_key_usage: Optional[List[str]] = None,
        subject_alt_names: Optional[List[str]] = None,
        basic_constraints: Optional[Dict[str, Any]] = None,
        extensions: Optional[Dict[str, Any]] = None,
    ) -> SuccessResult:
        """Generate self-signed certificate."""
        try:
            # Generate private key
            key_path = os.path.join(output_dir, "{common_name}.key")
            subprocess.run(
                ["openssl", "genrsa", "-out", key_path, str(key_size)],
                check=True,
                capture_output=True,
            )

            # Create certificate signing request
            csr_path = os.path.join(output_dir, "{common_name}.csr")
            config_path = self._create_openssl_config(
                common_name,
                country,
                state,
                locality,
                organization,
                organizational_unit,
                email,
                key_usage,
                extended_key_usage,
                subject_alt_names,
                basic_constraints,
                extensions,
            )

            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-new",
                    "-key",
                    key_path,
                    "-out",
                    csr_path,
                    "-config",
                    config_path,
                ],
                check=True,
                capture_output=True,
            )

            # Generate self-signed certificate
            cert_path = os.path.join(output_dir, "{common_name}.crt")
            subprocess.run(
                [
                    "openssl",
                    "x509",
                    "-req",
                    "-in",
                    csr_path,
                    "-signkey",
                    key_path,
                    "-out",
                    cert_path,
                    "-days",
                    str(days_valid),
                    "-extensions",
                    "v3_req",
                    "-extfile",
                    config_path,
                ],
                check=True,
                capture_output=True,
            )

            # Clean up temporary files
            os.unlink(csr_path)
            os.unlink(config_path)

            result_data = {
                "message": "Self-signed certificate generated successfully",
                "certificate_type": "self_signed",
                "common_name": common_name,
                "key_path": key_path,
                "cert_path": cert_path,
                "key_size": key_size,
                "valid_days": days_valid,
                "expiry_date": (datetime.now() + timedelta(days=days_valid)).isoformat(),
                "output_directory": output_dir,
                "timestamp": datetime.now().isoformat(),
            }

            # Audit successful operation
            self.ssl_security_adapter.audit_ssl_operation(
                SSLOperation.GENERATE,
                [],
                {"cert_type": "self_signed", "common_name": common_name},
                result_data,
            )

            return SuccessResult(data=result_data)

        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message="OpenSSL command failed: {e.stderr.decode() if e.stderr else str(e)}",
                code="OPENSSL_ERROR",
                details={"return_code": e.returncode, "command": e.cmd},
            )

    async def _generate_ca_signed_cert(
        self,
        common_name: str,
        country: str,
        state: str,
        locality: str,
        organization: str,
        organizational_unit: str,
        email: str,
        key_size: int,
        days_valid: int,
        output_dir: str,
        key_usage: Optional[List[str]] = None,
        extended_key_usage: Optional[List[str]] = None,
        subject_alt_names: Optional[List[str]] = None,
        basic_constraints: Optional[Dict[str, Any]] = None,
        extensions: Optional[Dict[str, Any]] = None,
    ) -> SuccessResult:
        """Generate CA-signed certificate."""
        try:
            # First generate CA certificate
            ca_key_path = os.path.join(output_dir, "ca.key")
            ca_cert_path = os.path.join(output_dir, "ca.crt")

            # Generate CA private key
            subprocess.run(
                ["openssl", "genrsa", "-out", ca_key_path, str(key_size)],
                check=True,
                capture_output=True,
            )

            # Generate CA certificate with proper CA extensions
            ca_basic_constraints = {"CA": "TRUE", "pathlen": 0}
            ca_key_usage = ["keyCertSign", "cRLSign"]
            ca_extended_key_usage = []

            ca_config_path = self._create_openssl_config(
                "CA-{common_name}",
                country,
                state,
                locality,
                organization,
                organizational_unit,
                email,
                ca_key_usage,
                ca_extended_key_usage,
                None,
                ca_basic_constraints,
                None,
            )

            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-new",
                    "-x509",
                    "-key",
                    ca_key_path,
                    "-out",
                    ca_cert_path,
                    "-days",
                    str(days_valid),
                    "-config",
                    ca_config_path,
                ],
                check=True,
                capture_output=True,
            )

            # Generate server private key
            key_path = os.path.join(output_dir, "{common_name}.key")
            subprocess.run(
                ["openssl", "genrsa", "-out", key_path, str(key_size)],
                check=True,
                capture_output=True,
            )

            # Create server certificate signing request
            csr_path = os.path.join(output_dir, "{common_name}.csr")

            # For CA-signed certificates, we need to use a different config without authorityKeyIdentifier
            # since the CA certificate doesn't exist yet during CSR creation
            temp_extensions = extensions.copy() if extensions else {}
            temp_extensions.pop("authorityKeyIdentifier", None)  # Remove if present

            config_path = self._create_openssl_config(
                common_name,
                country,
                state,
                locality,
                organization,
                organizational_unit,
                email,
                key_usage,
                extended_key_usage,
                subject_alt_names,
                basic_constraints,
                temp_extensions,
            )

            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-new",
                    "-key",
                    key_path,
                    "-out",
                    csr_path,
                    "-config",
                    config_path,
                ],
                check=True,
                capture_output=True,
            )

            # Sign server certificate with CA
            cert_path = os.path.join(output_dir, "{common_name}.crt")
            subprocess.run(
                [
                    "openssl",
                    "x509",
                    "-req",
                    "-in",
                    csr_path,
                    "-CA",
                    ca_cert_path,
                    "-CAkey",
                    ca_key_path,
                    "-CAcreateserial",
                    "-out",
                    cert_path,
                    "-days",
                    str(days_valid),
                    "-extensions",
                    "v3_req",
                    "-extfile",
                    config_path,
                ],
                check=True,
                capture_output=True,
            )

            # Clean up temporary files
            os.unlink(csr_path)
            os.unlink(config_path)
            os.unlink(ca_config_path)

            return SuccessResult(
                data={
                    "message": "CA-signed certificate generated successfully",
                    "certificate_type": "ca_signed",
                    "common_name": common_name,
                    "ca_key_path": ca_key_path,
                    "ca_cert_path": ca_cert_path,
                    "key_path": key_path,
                    "cert_path": cert_path,
                    "key_size": key_size,
                    "valid_days": days_valid,
                    "expiry_date": (datetime.now() + timedelta(days=days_valid)).isoformat(),
                    "output_directory": output_dir,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message="OpenSSL command failed: {e.stderr.decode() if e.stderr else str(e)}",
                code="OPENSSL_ERROR",
                details={"return_code": e.returncode, "command": e.cmd},
            )

    async def _generate_wildcard_cert(
        self,
        common_name: str,
        country: str,
        state: str,
        locality: str,
        organization: str,
        organizational_unit: str,
        email: str,
        key_size: int,
        days_valid: int,
        output_dir: str,
        key_usage: Optional[List[str]] = None,
        extended_key_usage: Optional[List[str]] = None,
        subject_alt_names: Optional[List[str]] = None,
        basic_constraints: Optional[Dict[str, Any]] = None,
        extensions: Optional[Dict[str, Any]] = None,
    ) -> SuccessResult:
        """Generate wildcard certificate."""
        try:
            # Generate private key
            key_path = os.path.join(output_dir, "wildcard-{common_name}.key")
            subprocess.run(
                ["openssl", "genrsa", "-out", key_path, str(key_size)],
                check=True,
                capture_output=True,
            )

            # Create certificate signing request with wildcard
            csr_path = os.path.join(output_dir, "wildcard-{common_name}.csr")

            # Add wildcard to subject alt names if not already present
            if subject_alt_names is None:
                subject_alt_names = ["*.{common_name}"]
            elif "*.{common_name}" not in subject_alt_names:
                subject_alt_names.append("*.{common_name}")

            config_path = self._create_openssl_config(
                "*.{common_name}",
                country,
                state,
                locality,
                organization,
                organizational_unit,
                email,
                key_usage,
                extended_key_usage,
                subject_alt_names,
                basic_constraints,
                extensions,
            )

            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-new",
                    "-key",
                    key_path,
                    "-out",
                    csr_path,
                    "-config",
                    config_path,
                ],
                check=True,
                capture_output=True,
            )

            # Generate self-signed wildcard certificate
            cert_path = os.path.join(output_dir, "wildcard-{common_name}.crt")
            subprocess.run(
                [
                    "openssl",
                    "x509",
                    "-req",
                    "-in",
                    csr_path,
                    "-signkey",
                    key_path,
                    "-out",
                    cert_path,
                    "-days",
                    str(days_valid),
                    "-extensions",
                    "v3_req",
                    "-extfile",
                    config_path,
                ],
                check=True,
                capture_output=True,
            )

            # Clean up temporary files
            os.unlink(csr_path)
            os.unlink(config_path)

            return SuccessResult(
                data={
                    "message": "Wildcard certificate generated successfully",
                    "certificate_type": "wildcard",
                    "common_name": "*.{common_name}",
                    "key_path": key_path,
                    "cert_path": cert_path,
                    "key_size": key_size,
                    "valid_days": days_valid,
                    "expiry_date": (datetime.now() + timedelta(days=days_valid)).isoformat(),
                    "output_directory": output_dir,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message="OpenSSL command failed: {e.stderr.decode() if e.stderr else str(e)}",
                code="OPENSSL_ERROR",
                details={"return_code": e.returncode, "command": e.cmd},
            )

    def _create_openssl_config(
        self,
        common_name: str,
        country: str,
        state: str,
        locality: str,
        organization: str,
        organizational_unit: str,
        email: str,
        key_usage: Optional[List[str]] = None,
        extended_key_usage: Optional[List[str]] = None,
        subject_alt_names: Optional[List[str]] = None,
        basic_constraints: Optional[Dict[str, Any]] = None,
        extensions: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create OpenSSL configuration file with x509 extensions."""

        # Default values
        if key_usage is None:
            key_usage = ["keyEncipherment", "dataEncipherment"]
        if extended_key_usage is None:
            extended_key_usage = ["serverAuth"]
        if subject_alt_names is None:
            subject_alt_names = [common_name, "*.{common_name}", "127.0.0.1", "::1"]
        if basic_constraints is None:
            basic_constraints = {"CA": "FALSE", "pathlen": None}

        # Build key usage string
        key_usage_str = ", ".join(key_usage)

        # Build extended key usage string
        if extended_key_usage:
            extended_key_usage_str = ", ".join(extended_key_usage)
        else:
            extended_key_usage_str = ""

        # Build basic constraints string
        basic_constraints_str = "CA:{basic_constraints['CA']}"
        if basic_constraints.get("pathlen"):
            basic_constraints_str += ", pathlen:{basic_constraints['pathlen']}"

        # Build subject alt names
        alt_names_content = ""
        for i, san in enumerate(subject_alt_names, 1):
            if san.startswith("IP:"):
                alt_names_content += "IP.{i} = {san[3:]}\n"
            elif san.startswith("DNS:"):
                alt_names_content += "DNS.{i} = {san[4:]}\n"
            elif san.startswith("URI:"):
                alt_names_content += "URI.{i} = {san[4:]}\n"
            elif san.startswith("EMAIL:"):
                alt_names_content += "email.{i} = {san[6:]}\n"
            else:
                # Try to determine if it's an IP address
                import ipaddress

                try:
                    ipaddress.ip_address(san)
                    alt_names_content += "IP.{i} = {san}\n"
                except ValueError:
                    alt_names_content += "DNS.{i} = {san}\n"

        # Build custom extensions
        custom_extensions = ""
        if extensions:
            for ext_name, ext_value in extensions.items():
                custom_extensions += "{ext_name} = {ext_value}\n"

        # Determine if this is a CA certificate
        is_ca = basic_constraints.get("CA") == "TRUE"

        # Build authority key identifier - only for non-CA certificates
        # But for CSR generation, we don't add authorityKeyIdentifier since CA doesn't exist yet
        authority_key_id = ""
        # Note: authorityKeyIdentifier is added during certificate signing, not during CSR creation

        config_content = """[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = {country}
ST = {state}
L = {locality}
O = {organization}
OU = {organizational_unit}
CN = {common_name}
emailAddress = {email}

[v3_req]
basicConstraints = {basic_constraints_str}
keyUsage = {key_usage_str}
{"extendedKeyUsage = {extended_key_usage_str}" if extended_key_usage_str else ""}
subjectAltName = @alt_names
subjectKeyIdentifier = hash
{authority_key_id}{custom_extensions}

[alt_names]
{alt_names_content}
"""

        # Create temporary config file
        config_fd, config_path = tempfile.mkstemp(suffix=".cn")
        with os.fdopen(config_fd, "w") as f:
            f.write(config_content)

        return config_path

    async def _generate_ca_certificate(
        self,
        common_name,
        country,
        state,
        locality,
        organization,
        organizational_unit,
        key_size,
        days_valid,
        output_dir,
    ):
        """Generate CA certificate using CertificateUtils."""
        try:
            validity_years = max(1, days_valid // 365)

            result = CertificateUtils.create_ca_certificate(
                common_name=common_name,
                output_dir=output_dir,
                organization=organization,
                organizational_unit=organizational_unit,
                country=country,
                state=state,
                locality=locality,
                validity_years=validity_years,
                key_size=key_size,
            )

            return SuccessResult(
                data={
                    "message": "CA certificate generated successfully",
                    "certificate_path": result["certificate_path"],
                    "key_path": result["key_path"],
                    "common_name": result["common_name"],
                    "validity_years": result["validity_years"],
                    "cert_type": "CA",
                }
            )

        except CertificateCreationError as e:
            return ErrorResult(
                message="Failed to create CA certificate: {e.message}",
                code="CA_CREATION_FAILED",
                details=e.details,
            )
        except SSLError as e:
            return ErrorResult(
                message="Unexpected error creating CA certificate: {str(e)}",
                code="CA_CREATION_ERROR",
                details={"error": str(e)},
            )

    async def _generate_server_certificate(
        self,
        common_name,
        country,
        state,
        locality,
        organization,
        organizational_unit,
        key_size,
        days_valid,
        output_dir,
        roles,
        ca_cert_path,
        ca_key_path,
    ):
        """Generate server certificate using CertificateUtils."""
        try:
            if not ca_cert_path or not ca_key_path:
                return ErrorResult(
                    message="CA certificate and key paths are required for server certificate",
                    code="MISSING_CA_PATHS",
                    details={"ca_cert_path": ca_cert_path, "ca_key_path": ca_key_path},
                )

            validity_years = max(1, days_valid // 365)

            result = CertificateUtils.create_server_certificate(
                common_name=common_name,
                ca_cert_path=ca_cert_path,
                ca_key_path=ca_key_path,
                output_dir=output_dir,
                roles=roles,
                organization=organization,
                organizational_unit=organizational_unit,
                country=country,
                state=state,
                locality=locality,
                validity_years=validity_years,
                key_size=key_size,
            )

            return SuccessResult(
                data={
                    "message": "Server certificate generated successfully",
                    "certificate_path": result["certificate_path"],
                    "key_path": result["key_path"],
                    "common_name": result["common_name"],
                    "roles": result["roles"],
                    "validity_years": result["validity_years"],
                    "cert_type": "Server",
                }
            )

        except CertificateCreationError as e:
            return ErrorResult(
                message="Failed to create server certificate: {e.message}",
                code="SERVER_CREATION_FAILED",
                details=e.details,
            )
        except SSLError as e:
            return ErrorResult(
                message="Unexpected error creating server certificate: {str(e)}",
                code="SERVER_CREATION_ERROR",
                details={"error": str(e)},
            )

    async def _generate_client_certificate(
        self,
        common_name,
        country,
        state,
        locality,
        organization,
        organizational_unit,
        key_size,
        days_valid,
        output_dir,
        roles,
        ca_cert_path,
        ca_key_path,
    ):
        """Generate client certificate using CertificateUtils."""
        try:
            if not ca_cert_path or not ca_key_path:
                return ErrorResult(
                    message="CA certificate and key paths are required for client certificate",
                    code="MISSING_CA_PATHS",
                    details={"ca_cert_path": ca_cert_path, "ca_key_path": ca_key_path},
                )

            validity_years = max(1, days_valid // 365)

            result = CertificateUtils.create_client_certificate(
                common_name=common_name,
                ca_cert_path=ca_cert_path,
                ca_key_path=ca_key_path,
                output_dir=output_dir,
                roles=roles,
                organization=organization,
                organizational_unit=organizational_unit,
                country=country,
                state=state,
                locality=locality,
                validity_years=validity_years,
                key_size=key_size,
            )

            return SuccessResult(
                data={
                    "message": "Client certificate generated successfully",
                    "certificate_path": result["certificate_path"],
                    "key_path": result["key_path"],
                    "common_name": result["common_name"],
                    "roles": result["roles"],
                    "validity_years": result["validity_years"],
                    "cert_type": "Client",
                }
            )

        except CertificateCreationError as e:
            return ErrorResult(
                message="Failed to create client certificate: {e.message}",
                code="CLIENT_CREATION_FAILED",
                details=e.details,
            )
        except SSLError as e:
            return ErrorResult(
                message="Unexpected error creating client certificate: {str(e)}",
                code="CLIENT_CREATION_ERROR",
                details={"error": str(e)},
            )

