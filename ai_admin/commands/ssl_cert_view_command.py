"""SSL certificate viewing command for MCP server."""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class SSLCertViewCommand(Command):
    """Command to view SSL certificate details."""
    
    name = "ssl_cert_view"
    
    async def execute(self,
                     cert_path: str,
                     cert_type: str = "certificate",
                     output_format: str = "text",
                     **kwargs):
        """
        View SSL certificate details.
        
        Args:
            cert_path: Path to the certificate file
            cert_type: Type of file to view (certificate, key, csr, crl)
            output_format: Output format (text, json, pem)
        """
        try:
            if not os.path.exists(cert_path):
                return ErrorResult(
                    message=f"Certificate file not found: {cert_path}",
                    code="FILE_NOT_FOUND",
                    details={"cert_path": cert_path}
                )
            
            if cert_type == "certificate":
                return await self._view_certificate(cert_path, output_format)
            elif cert_type == "key":
                return await self._view_private_key(cert_path, output_format)
            elif cert_type == "csr":
                return await self._view_csr(cert_path, output_format)
            elif cert_type == "crl":
                return await self._view_crl(cert_path, output_format)
            else:
                return ErrorResult(
                    message=f"Unsupported certificate type: {cert_type}",
                    code="UNSUPPORTED_CERT_TYPE",
                    details={"supported_types": ["certificate", "key", "csr", "crl"]}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Failed to view certificate: {str(e)}",
                code="CERT_VIEW_FAILED",
                details={"exception": str(e)}
            )
    
    async def _view_certificate(self, cert_path: str, output_format: str) -> SuccessResult:
        """View certificate details."""
        try:
            if output_format == "text":
                # Get certificate details in human-readable format
                result = subprocess.run([
                    "openssl", "x509", "-in", cert_path, "-text", "-noout"
                ], capture_output=True, text=True, check=True)
                
                # Get certificate dates
                dates_result = subprocess.run([
                    "openssl", "x509", "-in", cert_path, "-dates", "-noout"
                ], capture_output=True, text=True, check=True)
                
                # Get certificate subject and issuer
                subject_result = subprocess.run([
                    "openssl", "x509", "-in", cert_path, "-subject", "-issuer", "-noout"
                ], capture_output=True, text=True, check=True)
                
                # Get certificate fingerprint
                fingerprint_result = subprocess.run([
                    "openssl", "x509", "-in", cert_path, "-fingerprint", "-noout"
                ], capture_output=True, text=True, check=True)
                
                cert_info = {
                    "details": result.stdout,
                    "dates": dates_result.stdout,
                    "subject_issuer": subject_result.stdout,
                    "fingerprint": fingerprint_result.stdout
                }
                
                return SuccessResult(data={
                    "message": f"Certificate details retrieved successfully",
                    "cert_path": cert_path,
                    "cert_type": "certificate",
                    "format": "text",
                    "certificate_info": cert_info,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif output_format == "json":
                # Get certificate in JSON format
                result = subprocess.run([
                    "openssl", "x509", "-in", cert_path, "-outform", "DER" | "base64"
                ], capture_output=True, text=True, check=True)
                
                # Parse certificate details
                details_result = subprocess.run([
                    "openssl", "x509", "-in", cert_path, "-text", "-noout"
                ], capture_output=True, text=True, check=True)
                
                return SuccessResult(data={
                    "message": f"Certificate details retrieved successfully",
                    "cert_path": cert_path,
                    "cert_type": "certificate",
                    "format": "json",
                    "certificate_data": result.stdout,
                    "certificate_details": details_result.stdout,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif output_format == "pem":
                # Get certificate in PEM format
                with open(cert_path, 'r') as f:
                    cert_content = f.read()
                
                return SuccessResult(data={
                    "message": f"Certificate content retrieved successfully",
                    "cert_path": cert_path,
                    "cert_type": "certificate",
                    "format": "pem",
                    "certificate_content": cert_content,
                    "timestamp": datetime.now().isoformat()
                })
            
            else:
                return ErrorResult(
                    message=f"Unsupported output format: {output_format}",
                    code="UNSUPPORTED_FORMAT",
                    details={"supported_formats": ["text", "json", "pem"]}
                )
                
        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message=f"OpenSSL command failed: {e.stderr.decode() if e.stderr else str(e)}",
                code="OPENSSL_ERROR",
                details={"return_code": e.returncode, "command": e.cmd}
            )
    
    async def _view_private_key(self, key_path: str, output_format: str) -> SuccessResult:
        """View private key details."""
        try:
            if output_format == "text":
                # Check if key is encrypted
                result = subprocess.run([
                    "openssl", "rsa", "-in", key_path, "-check", "-noout"
                ], capture_output=True, text=True, check=True)
                
                # Get key modulus
                modulus_result = subprocess.run([
                    "openssl", "rsa", "-in", key_path, "-modulus", "-noout"
                ], capture_output=True, text=True, check=True)
                
                # Get key size
                size_result = subprocess.run([
                    "openssl", "rsa", "-in", key_path, "-text", "-noout"
                ], capture_output=True, text=True, check=True)
                
                key_info = {
                    "check": result.stdout,
                    "modulus": modulus_result.stdout,
                    "details": size_result.stdout
                }
                
                return SuccessResult(data={
                    "message": f"Private key details retrieved successfully",
                    "key_path": key_path,
                    "key_type": "private_key",
                    "format": "text",
                    "key_info": key_info,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif output_format == "pem":
                # Get key in PEM format (without showing content for security)
                file_size = os.path.getsize(key_path)
                
                return SuccessResult(data={
                    "message": f"Private key information retrieved successfully",
                    "key_path": key_path,
                    "key_type": "private_key",
                    "format": "pem",
                    "file_size": file_size,
                    "warning": "Private key content not displayed for security reasons",
                    "timestamp": datetime.now().isoformat()
                })
            
            else:
                return ErrorResult(
                    message=f"Unsupported output format for private key: {output_format}",
                    code="UNSUPPORTED_FORMAT",
                    details={"supported_formats": ["text", "pem"]}
                )
                
        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message=f"OpenSSL command failed: {e.stderr.decode() if e.stderr else str(e)}",
                code="OPENSSL_ERROR",
                details={"return_code": e.returncode, "command": e.cmd}
            )
    
    async def _view_csr(self, csr_path: str, output_format: str) -> SuccessResult:
        """View certificate signing request details."""
        try:
            if output_format == "text":
                # Get CSR details
                result = subprocess.run([
                    "openssl", "req", "-in", csr_path, "-text", "-noout"
                ], capture_output=True, text=True, check=True)
                
                # Get CSR subject
                subject_result = subprocess.run([
                    "openssl", "req", "-in", csr_path, "-subject", "-noout"
                ], capture_output=True, text=True, check=True)
                
                csr_info = {
                    "details": result.stdout,
                    "subject": subject_result.stdout
                }
                
                return SuccessResult(data={
                    "message": f"CSR details retrieved successfully",
                    "csr_path": csr_path,
                    "csr_type": "certificate_signing_request",
                    "format": "text",
                    "csr_info": csr_info,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif output_format == "pem":
                # Get CSR in PEM format
                with open(csr_path, 'r') as f:
                    csr_content = f.read()
                
                return SuccessResult(data={
                    "message": f"CSR content retrieved successfully",
                    "csr_path": csr_path,
                    "csr_type": "certificate_signing_request",
                    "format": "pem",
                    "csr_content": csr_content,
                    "timestamp": datetime.now().isoformat()
                })
            
            else:
                return ErrorResult(
                    message=f"Unsupported output format for CSR: {output_format}",
                    code="UNSUPPORTED_FORMAT",
                    details={"supported_formats": ["text", "pem"]}
                )
                
        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message=f"OpenSSL command failed: {e.stderr.decode() if e.stderr else str(e)}",
                code="OPENSSL_ERROR",
                details={"return_code": e.returncode, "command": e.cmd}
            )
    
    async def _view_crl(self, crl_path: str, output_format: str) -> SuccessResult:
        """View certificate revocation list details."""
        try:
            if output_format == "text":
                # Get CRL details
                result = subprocess.run([
                    "openssl", "crl", "-in", crl_path, "-text", "-noout"
                ], capture_output=True, text=True, check=True)
                
                # Get CRL dates
                dates_result = subprocess.run([
                    "openssl", "crl", "-in", crl_path, "-dates", "-noout"
                ], capture_output=True, text=True, check=True)
                
                crl_info = {
                    "details": result.stdout,
                    "dates": dates_result.stdout
                }
                
                return SuccessResult(data={
                    "message": f"CRL details retrieved successfully",
                    "crl_path": crl_path,
                    "crl_type": "certificate_revocation_list",
                    "format": "text",
                    "crl_info": crl_info,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif output_format == "pem":
                # Get CRL in PEM format
                with open(crl_path, 'r') as f:
                    crl_content = f.read()
                
                return SuccessResult(data={
                    "message": f"CRL content retrieved successfully",
                    "crl_path": crl_path,
                    "crl_type": "certificate_revocation_list",
                    "format": "pem",
                    "crl_content": crl_content,
                    "timestamp": datetime.now().isoformat()
                })
            
            else:
                return ErrorResult(
                    message=f"Unsupported output format for CRL: {output_format}",
                    code="UNSUPPORTED_FORMAT",
                    details={"supported_formats": ["text", "pem"]}
                )
                
        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message=f"OpenSSL command failed: {e.stderr.decode() if e.stderr else str(e)}",
                code="OPENSSL_ERROR",
                details={"return_code": e.returncode, "command": e.cmd}
            ) 