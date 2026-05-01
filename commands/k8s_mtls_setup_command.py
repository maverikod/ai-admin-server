from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import SSLError
"""Kubernetes mTLS setup command for setting up mTLS certificates.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.k8s_security_adapter import K8sSecurityAdapter

class K8sMtlsSetupCommand(BaseUnifiedCommand):
    """Command to setup mTLS certificates for Kubernetes clusters."""

    name = "k8s_mtls_setup"
    
    def __init__(self):
        """Initialize K8s mTLS setup command."""
        super().__init__()
        self.security_adapter = K8sSecurityAdapter()

    async def execute(
        self,
        action: str = "create",
        cluster_name: str = "my-cluster",
        namespace: str = "default",
        cert_name: str = "mtls-cert",
        ca_cert: Optional[str] = None,
        server_cert: Optional[str] = None,
        server_key: Optional[str] = None,
        client_cert: Optional[str] = None,
        client_key: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute K8s mTLS setup command with unified security.
        
        Args:
            action: mTLS action (create, get, delete, list)
            cluster_name: Name of the cluster
            namespace: Kubernetes namespace
            cert_name: Name of the certificate
            ca_cert: CA certificate
            server_cert: Server certificate
            server_key: Server private key
            client_cert: Client certificate
            client_key: Client private key
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with mTLS setup information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            cluster_name=cluster_name,
            namespace=namespace,
            cert_name=cert_name,
            ca_cert=ca_cert,
            server_cert=server_cert,
            server_key=server_key,
            client_cert=client_cert,
            client_key=client_key,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for K8s mTLS setup command."""
        return "k8s:mtls_setup"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute K8s mTLS setup command logic."""
        action = kwargs.get("action", "create")
        
        if action == "create":
            return await self._create_mtls_cert(**kwargs)
        elif action == "get":
            return await self._get_mtls_cert(**kwargs)
        elif action == "delete":
            return await self._delete_mtls_cert(**kwargs)
        elif action == "list":
            return await self._list_mtls_certs(**kwargs)
        else:
            raise SSLError(f"Unknown mTLS action: {action}")

    async def _create_mtls_cert(
        self,
        cluster_name: str = "my-cluster",
        namespace: str = "default",
        cert_name: str = "mtls-cert",
        ca_cert: Optional[str] = None,
        server_cert: Optional[str] = None,
        server_key: Optional[str] = None,
        client_cert: Optional[str] = None,
        client_key: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create mTLS certificate secret."""
        try:
            if not all([ca_cert, server_cert, server_key, client_cert, client_key]):
                raise SSLError("All certificate components are required for mTLS setup")

            # Create secret YAML
            secret_yaml = f"""
apiVersion: v1
kind: Secret
metadata:
  name: {cert_name}
  namespace: {namespace}
type: kubernetes.io/tls
data:
  ca.crt: {ca_cert}
  tls.crt: {server_cert}
  tls.key: {server_key}
  client.crt: {client_cert}
  client.key: {client_key}
"""

            # Apply secret
            result = subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=secret_yaml,
                text=True,
                capture_output=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise SSLError(f"mTLS certificate creation failed: {result.stderr}")

            return {
                "message": f"Successfully created mTLS certificate '{cert_name}' in namespace '{namespace}'",
                "action": "create",
                "cluster_name": cluster_name,
                "namespace": namespace,
                "cert_name": cert_name,
                "secret_yaml": secret_yaml,
                "raw_output": result.stdout,
            }

        except subprocess.TimeoutExpired as e:
            raise SSLError(f"mTLS certificate creation command timed out: {str(e)}")
        except SSLError as e:
            raise SSLError(f"mTLS certificate creation failed: {str(e)}")

    async def _get_mtls_cert(
        self,
        cluster_name: str = "my-cluster",
        namespace: str = "default",
        cert_name: str = "mtls-cert",
        **kwargs,
    ) -> Dict[str, Any]:
        """Get mTLS certificate secret."""
        try:
            cmd = ["kubectl", "get", "secret", cert_name, "-n", namespace, "-o", "yaml"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise SSLError(f"mTLS certificate retrieval failed: {result.stderr}")

            return {
                "message": f"Retrieved mTLS certificate '{cert_name}' from namespace '{namespace}'",
                "action": "get",
                "cluster_name": cluster_name,
                "namespace": namespace,
                "cert_name": cert_name,
                "secret_yaml": result.stdout,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise SSLError(f"mTLS certificate retrieval command timed out: {str(e)}")
        except SSLError as e:
            raise SSLError(f"mTLS certificate retrieval failed: {str(e)}")

    async def _delete_mtls_cert(
        self,
        cluster_name: str = "my-cluster",
        namespace: str = "default",
        cert_name: str = "mtls-cert",
        **kwargs,
    ) -> Dict[str, Any]:
        """Delete mTLS certificate secret."""
        try:
            cmd = ["kubectl", "delete", "secret", cert_name, "-n", namespace]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise SSLError(f"mTLS certificate deletion failed: {result.stderr}")

            return {
                "message": f"Successfully deleted mTLS certificate '{cert_name}' from namespace '{namespace}'",
                "action": "delete",
                "cluster_name": cluster_name,
                "namespace": namespace,
                "cert_name": cert_name,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise SSLError(f"mTLS certificate deletion command timed out: {str(e)}")
        except SSLError as e:
            raise SSLError(f"mTLS certificate deletion failed: {str(e)}")

    async def _list_mtls_certs(
        self,
        cluster_name: str = "my-cluster",
        namespace: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        """List mTLS certificate secrets."""
        try:
            cmd = ["kubectl", "get", "secrets", "-n", namespace, "-o", "wide"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise SSLError(f"mTLS certificate listing failed: {result.stderr}")

            secrets = []
            lines = result.stdout.strip().split("\n")
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        secrets.append({
                            "name": parts[0],
                            "type": parts[1],
                            "data": parts[2],
                            "age": parts[3],
                        })

            return {
                "message": f"Found {len(secrets)} secrets in namespace '{namespace}'",
                "action": "list",
                "cluster_name": cluster_name,
                "namespace": namespace,
                "secrets": secrets,
                "count": len(secrets),
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise SSLError(f"mTLS certificate listing command timed out: {str(e)}")
        except SSLError as e:
            raise SSLError(f"mTLS certificate listing failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for K8s mTLS setup command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "mTLS action (create, get, delete, list)",
                    "default": "create",
                    "enum": ["create", "get", "delete", "list"],
                },
                "cluster_name": {
                    "type": "string",
                    "description": "Name of the cluster",
                    "default": "my-cluster",
                },
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace",
                    "default": "default",
                },
                "cert_name": {
                    "type": "string",
                    "description": "Name of the certificate",
                    "default": "mtls-cert",
                },
                "ca_cert": {
                    "type": "string",
                    "description": "CA certificate",
                },
                "server_cert": {
                    "type": "string",
                    "description": "Server certificate",
                },
                "server_key": {
                    "type": "string",
                    "description": "Server private key",
                },
                "client_cert": {
                    "type": "string",
                    "description": "Client certificate",
                },
                "client_key": {
                    "type": "string",
                    "description": "Client private key",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }