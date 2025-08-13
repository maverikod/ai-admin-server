"""SSL certificate verification command for MCP server."""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class SSLCertVerifyCommand(Command):
    """Command to verify SSL certificates."""
    
    name = "ssl_cert_verify"
    
    async def execute(self,
                     cert_path: str,
                     ca_cert_path: Optional[str] = None,
                     ca_key_path: Optional[str] = None,
                     verify_chain: bool = True,
                     check_expiry: bool = True,
                     check_revocation: bool = False,
                     crl_path: Optional[str] = None,
                     **kwargs):
        """
        Verify SSL certificate.
        
        Args:
            cert_path: Path to the certificate to verify
            ca_cert_path: Path to CA certificate (optional, uses config if not provided)
            ca_key_path: Path to CA private key (optional, uses config if not provided)
            verify_chain: Verify certificate chain
            check_expiry: Check certificate expiry
            check_revocation: Check certificate revocation
            crl_path: Path to CRL file for revocation checking
        """
        try:
            if not os.path.exists(cert_path):
                return ErrorResult(
                    message=f"Certificate file not found: {cert_path}",
                    code="FILE_NOT_FOUND",
                    details={"cert_path": cert_path}
                )
            
            # Get CA paths from config if not provided
            if not ca_cert_path or not ca_key_path:
                config_paths = await self._get_ca_paths_from_config()
                if not ca_cert_path:
                    ca_cert_path = config_paths.get("ca_cert_path")
                if not ca_key_path:
                    ca_key_path = config_paths.get("ca_key_path")
            
            verification_results = {}
            
            # Basic certificate verification
            basic_result = await self._verify_basic_certificate(cert_path)
            verification_results["basic_verification"] = basic_result
            
            # Certificate chain verification
            if verify_chain and ca_cert_path:
                chain_result = await self._verify_certificate_chain(cert_path, ca_cert_path)
                verification_results["chain_verification"] = chain_result
            
            # Expiry check
            if check_expiry:
                expiry_result = await self._check_certificate_expiry(cert_path)
                verification_results["expiry_check"] = expiry_result
            
            # Revocation check
            if check_revocation and crl_path:
                revocation_result = await self._check_certificate_revocation(cert_path, crl_path)
                verification_results["revocation_check"] = revocation_result
            
            # Overall verification status
            overall_status = self._determine_overall_status(verification_results)
            
            return SuccessResult(data={
                "message": f"Certificate verification completed",
                "cert_path": cert_path,
                "ca_cert_path": ca_cert_path,
                "overall_status": overall_status,
                "verification_results": verification_results,
                "timestamp": datetime.now().isoformat()
            })
                
        except Exception as e:
            return ErrorResult(
                message=f"Failed to verify certificate: {str(e)}",
                code="CERT_VERIFICATION_FAILED",
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
    
    async def _verify_basic_certificate(self, cert_path: str) -> Dict[str, Any]:
        """Verify basic certificate format and structure."""
        try:
            # Check certificate format
            result = subprocess.run([
                "openssl", "x509", "-in", cert_path, "-text", "-noout"
            ], capture_output=True, text=True, check=True)
            
            # Check certificate dates
            dates_result = subprocess.run([
                "openssl", "x509", "-in", cert_path, "-dates", "-noout"
            ], capture_output=True, text=True, check=True)
            
            return {
                "status": "valid",
                "message": "Certificate format is valid",
                "details": result.stdout,
                "dates": dates_result.stdout
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "status": "invalid",
                "message": f"Certificate format is invalid: {e.stderr.decode() if e.stderr else str(e)}",
                "error": str(e)
            }
    
    async def _verify_certificate_chain(self, cert_path: str, ca_cert_path: str) -> Dict[str, Any]:
        """Verify certificate chain against CA certificate."""
        try:
            if not os.path.exists(ca_cert_path):
                return {
                    "status": "error",
                    "message": f"CA certificate not found: {ca_cert_path}"
                }
            
            # Verify certificate against CA
            result = subprocess.run([
                "openssl", "verify", "-CAfile", ca_cert_path, cert_path
            ], capture_output=True, text=True, check=True)
            
            if "OK" in result.stdout:
                return {
                    "status": "valid",
                    "message": "Certificate chain is valid",
                    "details": result.stdout
                }
            else:
                return {
                    "status": "invalid",
                    "message": "Certificate chain verification failed",
                    "details": result.stdout,
                    "error": result.stderr
                }
            
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": f"Certificate chain verification error: {e.stderr.decode() if e.stderr else str(e)}",
                "error": str(e)
            }
    
    async def _check_certificate_expiry(self, cert_path: str) -> Dict[str, Any]:
        """Check certificate expiry date."""
        try:
            # Get certificate end date
            result = subprocess.run([
                "openssl", "x509", "-in", cert_path, "-enddate", "-noout"
            ], capture_output=True, text=True, check=True)
            
            # Parse the date
            end_date_str = result.stdout.strip().replace("notAfter=", "")
            
            # Convert to datetime
            from datetime import datetime
            end_date = datetime.strptime(end_date_str, "%b %d %H:%M:%S %Y %Z")
            current_date = datetime.now()
            
            if end_date > current_date:
                days_remaining = (end_date - current_date).days
                return {
                    "status": "valid",
                    "message": f"Certificate is valid for {days_remaining} more days",
                    "expiry_date": end_date.isoformat(),
                    "days_remaining": days_remaining
                }
            else:
                days_expired = (current_date - end_date).days
                return {
                    "status": "expired",
                    "message": f"Certificate expired {days_expired} days ago",
                    "expiry_date": end_date.isoformat(),
                    "days_expired": days_expired
                }
            
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": f"Failed to check certificate expiry: {e.stderr.decode() if e.stderr else str(e)}",
                "error": str(e)
            }
        except ValueError as e:
            return {
                "status": "error",
                "message": f"Failed to parse certificate date: {str(e)}",
                "error": str(e)
            }
    
    async def _check_certificate_revocation(self, cert_path: str, crl_path: str) -> Dict[str, Any]:
        """Check if certificate is revoked using CRL."""
        try:
            if not os.path.exists(crl_path):
                return {
                    "status": "error",
                    "message": f"CRL file not found: {crl_path}"
                }
            
            # Get certificate serial number
            serial_result = subprocess.run([
                "openssl", "x509", "-in", cert_path, "-serial", "-noout"
            ], capture_output=True, text=True, check=True)
            
            serial_number = serial_result.stdout.strip().replace("serial=", "")
            
            # Check CRL for the serial number
            crl_result = subprocess.run([
                "openssl", "crl", "-in", crl_path, "-text", "-noout"
            ], capture_output=True, text=True, check=True)
            
            if serial_number in crl_result.stdout:
                return {
                    "status": "revoked",
                    "message": f"Certificate with serial {serial_number} is revoked",
                    "serial_number": serial_number
                }
            else:
                return {
                    "status": "valid",
                    "message": f"Certificate with serial {serial_number} is not revoked",
                    "serial_number": serial_number
                }
            
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": f"Failed to check certificate revocation: {e.stderr.decode() if e.stderr else str(e)}",
                "error": str(e)
            }
    
    def _determine_overall_status(self, verification_results: Dict[str, Any]) -> str:
        """Determine overall verification status based on all checks."""
        if not verification_results:
            return "unknown"
        
        # Check for any invalid or error statuses
        for check_name, result in verification_results.items():
            if isinstance(result, dict) and result.get("status") in ["invalid", "expired", "revoked", "error"]:
                return result["status"]
        
        # If all checks passed, return valid
        return "valid" 