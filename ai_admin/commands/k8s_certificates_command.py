"""Kubernetes certificates management command for MCP server."""

import os
import json
import yaml
import ipaddress
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.settings_manager import get_settings_manager


class K8sCertificatesCommand(Command):
    """Command to manage Kubernetes cluster certificates using Python cryptography library."""
    
    name = "k8s_certificates"
    
    def __init__(self):
        """Initialize certificates command."""
        self.certs_base_dir = "./certificates"
        self.kubeconfigs_dir = "./kubeconfigs"
    
    def _generate_private_key(self, key_path: str, key_size: int = 2048) -> rsa.RSAPrivateKey:
        """Generate RSA private key using cryptography library."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        
        # Save private key to file
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        return private_key
    
    def _create_certificate(self, 
                          private_key: rsa.RSAPrivateKey,
                          subject_name: x509.Name,
                          issuer_name: x509.Name,
                          cert_type: str,
                          days_valid: int,
                          cert_path: str) -> x509.Certificate:
        """Create X.509 certificate using cryptography library."""
        
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject_name)
        builder = builder.issuer_name(issuer_name)
        builder = builder.not_valid_before(datetime.now())
        builder = builder.not_valid_after(datetime.now() + timedelta(days=days_valid))
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.public_key(private_key.public_key())
        
        # Add Subject Alternative Name
        builder = builder.add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv6Address("::1"))
            ]),
            critical=False
        )
        
        # Add extensions based on certificate type
        if cert_type == "ca":
            builder = builder.add_extension(
                x509.BasicConstraints(ca=True, path_length=0),
                critical=True
            )
            builder = builder.add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True
            )
        else:  # client, server, etc.
            builder = builder.add_extension(
                x509.BasicConstraints(ca=False),
                critical=True
            )
            builder = builder.add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=True,
                    data_encipherment=True,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True
            )
            
            if cert_type == "client":
                builder = builder.add_extension(
                    x509.ExtendedKeyUsage([x509.OID_PKIX_KP_CLIENT_AUTH]),
                    critical=False
                )
            elif cert_type == "server":
                builder = builder.add_extension(
                    x509.ExtendedKeyUsage([x509.OID_PKIX_KP_SERVER_AUTH]),
                    critical=False
                )
        
        # Sign the certificate
        if cert_type == "ca":
            # Self-signed for CA
            cert = builder.sign(private_key, hashes.SHA256())
        else:
            # Load CA certificate and key for signing
            ca_cert = x509.load_pem_x509_certificate(
                open(f"{self.certs_base_dir}/ca.crt", "rb").read()
            )
            ca_key = load_pem_private_key(
                open(f"{self.certs_base_dir}/ca.key", "rb").read(),
                password=None
            )
            cert = builder.sign(ca_key, hashes.SHA256())
        
        # Save certificate to file
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        return cert
    
    async def execute(self,
                     action: str = "create",
                     cluster_name: str = "my-cluster",
                     cert_type: str = "client",
                     common_name: str = "kubernetes-admin",
                     organization: str = "system:masters",
                     country: str = "US",
                     state: str = "State",
                     locality: str = "City",
                     organizational_unit: str = "IT",
                     email: str = "admin@kubernetes.local",
                     key_size: int = 2048,
                     days_valid: int = 365,
                     output_dir: Optional[str] = None,
                     **kwargs):
        """
        Manage Kubernetes cluster certificates using Python cryptography library.
        
        Args:
            action: Action to perform (create, setup_cluster, list, verify)
            cluster_name: Name of the Kubernetes cluster
            cert_type: Type of certificate (client, server, ca, admin)
            common_name: Common Name for the certificate
            organization: Organization name (for RBAC)
            country: Country code (2 letters)
            state: State or province
            locality: City or locality
            organizational_unit: Organizational unit
            email: Email address
            key_size: Key size in bits (2048, 4096)
            days_valid: Number of days certificate is valid
            output_dir: Output directory for certificates
        """
        try:
            if not output_dir:
                output_dir = os.path.join(self.certs_base_dir, cluster_name)
            
            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            if action == "create":
                return await self._create_single_certificate(
                    cert_type, common_name, organization, country, state,
                    locality, organizational_unit, email, key_size, days_valid, output_dir
                )
            elif action == "setup_cluster":
                return await self._setup_cluster_certificates(
                    cluster_name, common_name, organization, country, state,
                    locality, organizational_unit, email, key_size, days_valid, output_dir
                )
            elif action == "list":
                return await self._list_certificates(output_dir)
            elif action == "verify":
                return await self._verify_certificate(cert_type, output_dir)
            else:
                return ErrorResult(
                    message=f"Unknown action: {action}",
                    code="INVALID_ACTION",
                    details={"valid_actions": ["create", "setup_cluster", "list", "verify"]}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error in certificate operation: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"exception": str(e)}
            )
    
    async def _create_single_certificate(self, cert_type: str, common_name: str,
                                       organization: str, country: str, state: str,
                                       locality: str, organizational_unit: str,
                                       email: str, key_size: int, days_valid: int,
                                       output_dir: str) -> SuccessResult:
        """Create a single certificate."""
        try:
            # Create subject name
            subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, country),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
                x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, organizational_unit),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
                x509.NameAttribute(NameOID.EMAIL_ADDRESS, email)
            ])
            
            # Generate private key
            key_path = os.path.join(output_dir, f"{common_name}.key")
            private_key = self._generate_private_key(key_path, key_size)
            
            # Create certificate
            cert_path = os.path.join(output_dir, f"{common_name}.crt")
            cert = self._create_certificate(
                private_key, subject, subject, cert_type, days_valid, cert_path
            )
            
            return SuccessResult(data={
                "message": f"Certificate '{common_name}' created successfully",
                "certificate_type": cert_type,
                "common_name": common_name,
                "key_path": key_path,
                "cert_path": cert_path,
                "key_size": key_size,
                "valid_days": days_valid,
                "expiry_date": cert.not_valid_after.isoformat(),
                "output_directory": output_dir,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to create certificate: {str(e)}",
                code="CERTIFICATE_CREATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _setup_cluster_certificates(self, cluster_name: str, common_name: str,
                                        organization: str, country: str, state: str,
                                        locality: str, organizational_unit: str,
                                        email: str, key_size: int, days_valid: int,
                                        output_dir: str) -> SuccessResult:
        """Setup complete set of certificates for a Kubernetes cluster."""
        try:
            certificates = []
            
            # Create CA certificate first
            ca_result = await self._create_single_certificate(
                "ca", f"kubernetes-ca-{cluster_name}", organization, country, state,
                locality, organizational_unit, email, key_size, days_valid, output_dir
            )
            if isinstance(ca_result, ErrorResult):
                return ca_result
            certificates.append(ca_result.data)
            
            # Create admin certificate
            admin_result = await self._create_single_certificate(
                "client", f"kubernetes-admin-{cluster_name}", organization, country, state,
                locality, organizational_unit, email, key_size, days_valid, output_dir
            )
            if isinstance(admin_result, ErrorResult):
                return admin_result
            certificates.append(admin_result.data)
            
            # Create server certificate
            server_result = await self._create_single_certificate(
                "server", f"kubernetes-server-{cluster_name}", organization, country, state,
                locality, organizational_unit, email, key_size, days_valid, output_dir
            )
            if isinstance(server_result, ErrorResult):
                return server_result
            certificates.append(server_result.data)
            
            return SuccessResult(data={
                "message": f"Cluster certificates for '{cluster_name}' created successfully",
                "cluster_name": cluster_name,
                "certificates": certificates,
                "output_directory": output_dir,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to setup cluster certificates: {str(e)}",
                code="CLUSTER_SETUP_FAILED",
                details={"exception": str(e)}
            )
    
    async def _list_certificates(self, output_dir: str) -> SuccessResult:
        """List all certificates in the output directory."""
        try:
            certificates = []
            
            for file_path in Path(output_dir).glob("*.crt"):
                try:
                    cert = x509.load_pem_x509_certificate(
                        open(file_path, "rb").read()
                    )
                    
                    certificates.append({
                        "name": file_path.stem,
                        "path": str(file_path),
                        "subject": cert.subject.rfc4514_string(),
                        "issuer": cert.issuer.rfc4514_string(),
                        "not_valid_before": cert.not_valid_before.isoformat(),
                        "not_valid_after": cert.not_valid_after.isoformat(),
                        "serial_number": str(cert.serial_number)
                    })
                except Exception as e:
                    certificates.append({
                        "name": file_path.stem,
                        "path": str(file_path),
                        "error": f"Failed to read certificate: {e}"
                    })
            
            return SuccessResult(data={
                "message": f"Found {len(certificates)} certificates",
                "certificates": certificates,
                "directory": output_dir,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to list certificates: {str(e)}",
                code="LIST_FAILED",
                details={"exception": str(e)}
            )
    
    async def _verify_certificate(self, cert_type: str, output_dir: str) -> SuccessResult:
        """Verify a certificate's validity."""
        try:
            cert_path = os.path.join(output_dir, f"kubernetes-{cert_type}.crt")
            
            if not os.path.exists(cert_path):
                return ErrorResult(
                    message=f"Certificate file not found: {cert_path}",
                    code="CERTIFICATE_NOT_FOUND"
                )
            
            cert = x509.load_pem_x509_certificate(open(cert_path, "rb").read())
            
            now = datetime.now()
            is_valid = cert.not_valid_before <= now <= cert.not_valid_after
            
            return SuccessResult(data={
                "message": f"Certificate verification completed",
                "certificate_type": cert_type,
                "certificate_path": cert_path,
                "is_valid": is_valid,
                "not_valid_before": cert.not_valid_before.isoformat(),
                "not_valid_after": cert.not_valid_after.isoformat(),
                "days_until_expiry": (cert.not_valid_after - now).days,
                "subject": cert.subject.rfc4514_string(),
                "issuer": cert.issuer.rfc4514_string(),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to verify certificate: {str(e)}",
                code="VERIFICATION_FAILED",
                details={"exception": str(e)}
            )