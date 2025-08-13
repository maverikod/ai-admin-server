"""SSL CRL (Certificate Revocation List) command for MCP server."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class SSLCrlCommand(Command):
    """Command to manage Certificate Revocation Lists (CRL)."""
    
    name = "ssl_crl"
    
    async def execute(self,
                     action: str = "create",
                     ca_cert_path: Optional[str] = None,
                     ca_key_path: Optional[str] = None,
                     crl_path: Optional[str] = None,
                     output_dir: Optional[str] = None,
                     days_valid: int = 30,
                     serial_numbers: Optional[List[str]] = None,
                     reason: str = "unspecified",
                     **kwargs):
        """
        Manage Certificate Revocation Lists (CRL).
        
        Args:
            action: Action to perform (create, add, remove, view, verify)
            ca_cert_path: Path to CA certificate (optional, uses config if not provided)
            ca_key_path: Path to CA private key (optional, uses config if not provided)
            crl_path: Path to CRL file
            output_dir: Output directory for CRL files
            days_valid: Number of days CRL is valid
            serial_numbers: List of certificate serial numbers to add/remove
            reason: Reason for revocation (unspecified, keyCompromise, CACompromise, affiliationChanged, 
                    superseded, cessationOfOperation, certificateHold)
        """
        try:
            # Get CA paths from config if not provided
            if not ca_cert_path or not ca_key_path:
                config_paths = await self._get_ca_paths_from_config()
                if not ca_cert_path:
                    ca_cert_path = config_paths.get("ca_cert_path")
                if not ca_key_path:
                    ca_key_path = config_paths.get("ca_key_path")
            
            if action == "create":
                return await self._create_crl(ca_cert_path, ca_key_path, crl_path, output_dir, days_valid)
            elif action == "add":
                return await self._add_to_crl(ca_cert_path, ca_key_path, crl_path, serial_numbers, reason)
            elif action == "remove":
                return await self._remove_from_crl(ca_cert_path, ca_key_path, crl_path, serial_numbers)
            elif action == "view":
                return await self._view_crl(crl_path)
            elif action == "verify":
                return await self._verify_crl(crl_path, ca_cert_path)
            else:
                return ErrorResult(
                    message=f"Unknown action: {action}",
                    code="UNKNOWN_ACTION",
                    details={"supported_actions": ["create", "add", "remove", "view", "verify"]}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Failed to manage CRL: {str(e)}",
                code="CRL_OPERATION_FAILED",
                details={"exception": str(e)}
            )
    
    async def _get_ca_paths_from_config(self) -> Dict[str, str]:
        """Get CA certificate and key paths from configuration."""
        try:
            from ai_admin.settings_manager import get_settings_manager
            settings_manager = get_settings_manager()
            config = settings_manager.get_all_settings()
            
            ssl_config = config.get("ssl", {})
            return {
                "ca_cert_path": ssl_config.get("ca_cert_path"),
                "ca_key_path": ssl_config.get("ca_key_path")
            }
        except Exception:
            return {}
    
    async def _create_crl(self, ca_cert_path: str, ca_key_path: str, crl_path: Optional[str], 
                         output_dir: Optional[str], days_valid: int) -> SuccessResult:
        """Create a new CRL."""
        try:
            if not ca_cert_path or not ca_key_path:
                return ErrorResult(
                    message="CA certificate and key paths are required",
                    code="MISSING_CA_PATHS",
                    details={}
                )
            
            if not os.path.exists(ca_cert_path):
                return ErrorResult(
                    message=f"CA certificate not found: {ca_cert_path}",
                    code="CA_CERT_NOT_FOUND",
                    details={"ca_cert_path": ca_cert_path}
                )
            
            if not os.path.exists(ca_key_path):
                return ErrorResult(
                    message=f"CA private key not found: {ca_key_path}",
                    code="CA_KEY_NOT_FOUND",
                    details={"ca_key_path": ca_key_path}
                )
            
            # Set output directory
            if not output_dir:
                output_dir = os.path.expanduser("~/.ssl-certs")
            
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Set CRL path
            if not crl_path:
                crl_path = os.path.join(output_dir, "crl.pem")
            
            # Create CRL configuration
            crl_config_content = f"""[ca]
default_ca = CA_default

[CA_default]
dir = {output_dir}
certs = $dir
crl_dir = $dir/crl
database = $dir/index.txt
new_certs_dir = $dir/newcerts
certificate = {ca_cert_path}
serial = $dir/serial
crlnumber = $dir/crlnumber
crl = {crl_path}
private_key = {ca_key_path}
RANDFILE = $dir/private/.rand

x509_extensions = usr_cert
name_opt = ca_default
cert_opt = ca_default
default_days = 365
default_crl_days = {days_valid}
default_md = sha256
preserve = no
policy = policy_strict

[policy_strict]
countryName = match
stateOrProvinceName = match
organizationName = match
organizationalUnitName = optional
commonName = supplied
emailAddress = optional

[usr_cert]
basicConstraints = CA:FALSE
nsCertType = client, email
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth, emailProtection
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
"""
            
            # Create CRL config file
            crl_config_path = os.path.join(output_dir, "crl.cnf")
            with open(crl_config_path, 'w') as f:
                f.write(crl_config_content)
            
            # Create index.txt if it doesn't exist
            index_path = os.path.join(output_dir, "index.txt")
            if not os.path.exists(index_path):
                with open(index_path, 'w') as f:
                    pass
            
            # Create crlnumber file if it doesn't exist
            crlnumber_path = os.path.join(output_dir, "crlnumber")
            if not os.path.exists(crlnumber_path):
                with open(crlnumber_path, 'w') as f:
                    f.write("01")
            
            # Generate CRL
            subprocess.run([
                "openssl", "ca", "-config", crl_config_path, "-gencrl", "-out", crl_path
            ], check=True, capture_output=True)
            
            # Clean up config file
            os.unlink(crl_config_path)
            
            return SuccessResult(data={
                "message": f"CRL created successfully",
                "crl_path": crl_path,
                "ca_cert_path": ca_cert_path,
                "days_valid": days_valid,
                "output_directory": output_dir,
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message=f"Failed to create CRL: {e.stderr if isinstance(e.stderr, str) else e.stderr.decode() if e.stderr else str(e)}",
                code="CRL_CREATION_FAILED",
                details={"return_code": e.returncode, "command": e.cmd}
            )
    
    async def _add_to_crl(self, ca_cert_path: str, ca_key_path: str, crl_path: str, 
                         serial_numbers: List[str], reason: str) -> SuccessResult:
        """Add certificates to CRL."""
        try:
            if not serial_numbers:
                return ErrorResult(
                    message="Serial numbers are required",
                    code="MISSING_SERIAL_NUMBERS",
                    details={}
                )
            
            if not os.path.exists(crl_path):
                return ErrorResult(
                    message=f"CRL file not found: {crl_path}",
                    code="CRL_NOT_FOUND",
                    details={"crl_path": crl_path}
                )
            
            # Create temporary config for revocation
            revoke_config_content = f"""[ca]
default_ca = CA_default

[CA_default]
dir = {os.path.dirname(crl_path)}
certs = $dir
crl_dir = $dir
database = $dir/index.txt
new_certs_dir = $dir
certificate = {ca_cert_path}
serial = $dir/serial
crlnumber = $dir/crlnumber
crl = {crl_path}
private_key = {ca_key_path}
RANDFILE = $dir/.rand

x509_extensions = usr_cert
name_opt = ca_default
cert_opt = ca_default
default_days = 365
default_crl_days = 30
default_md = sha256
preserve = no
policy = policy_strict

[policy_strict]
countryName = match
stateOrProvinceName = match
organizationName = match
organizationalUnitName = optional
commonName = supplied
emailAddress = optional

[usr_cert]
basicConstraints = CA:FALSE
nsCertType = client, email
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth, emailProtection
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
"""
            
            revoke_config_path = os.path.join(os.path.dirname(crl_path), "revoke.cnf")
            with open(revoke_config_path, 'w') as f:
                f.write(revoke_config_content)
            
            revoked_certificates = []
            
            for serial in serial_numbers:
                try:
                    # Revoke certificate
                    subprocess.run([
                        "openssl", "ca", "-config", revoke_config_path, 
                        "-revoke", f"$dir/{serial}.pem", "-crl_reason", reason
                    ], check=True, capture_output=True)
                    
                    revoked_certificates.append({
                        "serial": serial,
                        "reason": reason,
                        "status": "revoked"
                    })
                    
                except subprocess.CalledProcessError as e:
                    revoked_certificates.append({
                        "serial": serial,
                        "reason": reason,
                        "status": "failed",
                        "error": e.stderr.decode() if e.stderr else str(e)
                    })
            
            # Update CRL
            subprocess.run([
                "openssl", "ca", "-config", revoke_config_path, "-gencrl", "-out", crl_path
            ], check=True, capture_output=True)
            
            # Clean up config file
            os.unlink(revoke_config_path)
            
            return SuccessResult(data={
                "message": f"Certificates processed for CRL",
                "crl_path": crl_path,
                "revoked_certificates": revoked_certificates,
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message=f"Failed to add to CRL: {e.stderr if isinstance(e.stderr, str) else e.stderr.decode() if e.stderr else str(e)}",
                code="CRL_ADDITION_FAILED",
                details={"return_code": e.returncode, "command": e.cmd}
            )
    
    async def _remove_from_crl(self, ca_cert_path: str, ca_key_path: str, crl_path: str, 
                              serial_numbers: List[str]) -> SuccessResult:
        """Remove certificates from CRL (restore them)."""
        try:
            if not serial_numbers:
                return ErrorResult(
                    message="Serial numbers are required",
                    code="MISSING_SERIAL_NUMBERS",
                    details={}
                )
            
            # Note: OpenSSL doesn't directly support removing from CRL
            # This would require recreating the CRL without the specified certificates
            # For now, we'll return an informational message
            
            return SuccessResult(data={
                "message": "CRL removal not directly supported by OpenSSL",
                "note": "To remove certificates from CRL, recreate the CRL without the specified certificates",
                "crl_path": crl_path,
                "serial_numbers": serial_numbers,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to remove from CRL: {str(e)}",
                code="CRL_REMOVAL_FAILED",
                details={"exception": str(e)}
            )
    
    async def _view_crl(self, crl_path: str) -> SuccessResult:
        """View CRL details."""
        try:
            if not os.path.exists(crl_path):
                return ErrorResult(
                    message=f"CRL file not found: {crl_path}",
                    code="CRL_NOT_FOUND",
                    details={"crl_path": crl_path}
                )
            
            # Get CRL details
            result = subprocess.run([
                "openssl", "crl", "-in", crl_path, "-text", "-noout"
            ], capture_output=True, text=True, check=True)
            
            # Get CRL dates
            dates_result = subprocess.run([
                "openssl", "crl", "-in", crl_path, "-lastupdate", "-nextupdate", "-noout"
            ], capture_output=True, text=True, check=True)
            
            # Get CRL issuer
            issuer_result = subprocess.run([
                "openssl", "crl", "-in", crl_path, "-issuer", "-noout"
            ], capture_output=True, text=True, check=True)
            
            return SuccessResult(data={
                "message": f"CRL details retrieved successfully",
                "crl_path": crl_path,
                "details": result.stdout,
                "dates": dates_result.stdout,
                "issuer": issuer_result.stdout,
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message=f"Failed to view CRL: {e.stderr if isinstance(e.stderr, str) else e.stderr.decode() if e.stderr else str(e)}",
                code="CRL_VIEW_FAILED",
                details={"return_code": e.returncode, "command": e.cmd}
            )
    
    async def _verify_crl(self, crl_path: str, ca_cert_path: str) -> SuccessResult:
        """Verify CRL signature."""
        try:
            if not os.path.exists(crl_path):
                return ErrorResult(
                    message=f"CRL file not found: {crl_path}",
                    code="CRL_NOT_FOUND",
                    details={"crl_path": crl_path}
                )
            
            if not os.path.exists(ca_cert_path):
                return ErrorResult(
                    message=f"CA certificate not found: {ca_cert_path}",
                    code="CA_CERT_NOT_FOUND",
                    details={"ca_cert_path": ca_cert_path}
                )
            
            # Verify CRL
            result = subprocess.run([
                "openssl", "crl", "-in", crl_path, "-CAfile", ca_cert_path, "-verify"
            ], capture_output=True, text=True, check=True)
            
            if "verify OK" in result.stdout:
                return SuccessResult(data={
                    "message": "CRL signature is valid",
                    "crl_path": crl_path,
                    "ca_cert_path": ca_cert_path,
                    "verification": "valid",
                    "details": result.stdout,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return SuccessResult(data={
                    "message": "CRL signature verification failed",
                    "crl_path": crl_path,
                    "ca_cert_path": ca_cert_path,
                    "verification": "invalid",
                    "details": result.stdout,
                    "error": result.stderr if result.stderr else "Unknown error",
                    "timestamp": datetime.now().isoformat()
                })
            
        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message=f"Failed to verify CRL: {e.stderr if isinstance(e.stderr, str) else e.stderr.decode() if e.stderr else str(e)}",
                code="CRL_VERIFICATION_FAILED",
                details={"return_code": e.returncode, "command": e.cmd}
            ) 