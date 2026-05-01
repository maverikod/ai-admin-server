#!/usr/bin/env python3
"""
Script to create test certificates using OpenSSL directly.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import subprocess
import tempfile
from pathlib import Path


def create_openssl_config(common_name: str, is_ca: bool = False) -> str:
    """Create OpenSSL configuration file."""
    config_content = f"""[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = UA
ST = Kyiv
L = Kyiv
O = Test Organization
OU = IT
CN = {common_name}
emailAddress = test@example.com

[v3_req]
basicConstraints = CA:{'TRUE' if is_ca else 'FALSE'}
keyUsage = {'keyCertSign, cRLSign' if is_ca else 'keyEncipherment, dataEncipherment'}
{'extendedKeyUsage = serverAuth, clientAuth' if not is_ca else ''}
subjectAltName = @alt_names
subjectKeyIdentifier = hash

[alt_names]
DNS.1 = {common_name}
DNS.2 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
"""
    
    # Create temporary config file
    config_fd, config_path = tempfile.mkstemp(suffix=".cnf")
    with os.fdopen(config_fd, "w") as f:
        f.write(config_content)
    
    return config_path


def create_test_certificates():
    """Create test certificates using OpenSSL."""
    cert_dir = Path("test_environment/certs")
    cert_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Creating test certificates in {cert_dir}")
    
    try:
        # Create CA certificate
        print("Creating CA certificate...")
        ca_key_path = cert_dir / "ca.key"
        ca_cert_path = cert_dir / "ca.crt"
        
        # Generate CA private key
        subprocess.run([
            "openssl", "genrsa", "-out", str(ca_key_path), "2048"
        ], check=True, capture_output=True)
        
        # Create CA config
        ca_config = create_openssl_config("Test CA", is_ca=True)
        
        # Generate CA certificate
        subprocess.run([
            "openssl", "req", "-new", "-x509", "-key", str(ca_key_path),
            "-out", str(ca_cert_path), "-days", "365", "-config", ca_config
        ], check=True, capture_output=True)
        
        print(f"✅ CA certificate created: {ca_cert_path}")
        
        # Create server certificate
        print("Creating server certificate...")
        server_key_path = cert_dir / "server.key"
        server_cert_path = cert_dir / "server.crt"
        server_csr_path = cert_dir / "server.csr"
        
        # Generate server private key
        subprocess.run([
            "openssl", "genrsa", "-out", str(server_key_path), "2048"
        ], check=True, capture_output=True)
        
        # Create server config
        server_config = create_openssl_config("test-server.local")
        
        # Generate server CSR
        subprocess.run([
            "openssl", "req", "-new", "-key", str(server_key_path),
            "-out", str(server_csr_path), "-config", server_config
        ], check=True, capture_output=True)
        
        # Sign server certificate with CA
        subprocess.run([
            "openssl", "x509", "-req", "-in", str(server_csr_path),
            "-CA", str(ca_cert_path), "-CAkey", str(ca_key_path),
            "-CAcreateserial", "-out", str(server_cert_path),
            "-days", "365", "-extensions", "v3_req", "-extfile", server_config
        ], check=True, capture_output=True)
        
        print(f"✅ Server certificate created: {server_cert_path}")
        
        # Create admin client certificate
        print("Creating admin client certificate...")
        admin_key_path = cert_dir / "admin-client.key"
        admin_cert_path = cert_dir / "admin-client.crt"
        admin_csr_path = cert_dir / "admin-client.csr"
        
        # Generate admin client private key
        subprocess.run([
            "openssl", "genrsa", "-out", str(admin_key_path), "2048"
        ], check=True, capture_output=True)
        
        # Create admin client config
        admin_config = create_openssl_config("admin-client")
        
        # Generate admin client CSR
        subprocess.run([
            "openssl", "req", "-new", "-key", str(admin_key_path),
            "-out", str(admin_csr_path), "-config", admin_config
        ], check=True, capture_output=True)
        
        # Sign admin client certificate with CA
        subprocess.run([
            "openssl", "x509", "-req", "-in", str(admin_csr_path),
            "-CA", str(ca_cert_path), "-CAkey", str(ca_key_path),
            "-CAcreateserial", "-out", str(admin_cert_path),
            "-days", "365", "-extensions", "v3_req", "-extfile", admin_config
        ], check=True, capture_output=True)
        
        print(f"✅ Admin client certificate created: {admin_cert_path}")
        
        # Create user client certificate
        print("Creating user client certificate...")
        user_key_path = cert_dir / "user-client.key"
        user_cert_path = cert_dir / "user-client.crt"
        user_csr_path = cert_dir / "user-client.csr"
        
        # Generate user client private key
        subprocess.run([
            "openssl", "genrsa", "-out", str(user_key_path), "2048"
        ], check=True, capture_output=True)
        
        # Create user client config
        user_config = create_openssl_config("user-client")
        
        # Generate user client CSR
        subprocess.run([
            "openssl", "req", "-new", "-key", str(user_key_path),
            "-out", str(user_csr_path), "-config", user_config
        ], check=True, capture_output=True)
        
        # Sign user client certificate with CA
        subprocess.run([
            "openssl", "x509", "-req", "-in", str(user_csr_path),
            "-CA", str(ca_cert_path), "-CAkey", str(ca_key_path),
            "-CAcreateserial", "-out", str(user_cert_path),
            "-days", "365", "-extensions", "v3_req", "-extfile", user_config
        ], check=True, capture_output=True)
        
        print(f"✅ User client certificate created: {user_cert_path}")
        
        # Create self-signed certificate
        print("Creating self-signed certificate...")
        self_key_path = cert_dir / "self-signed.key"
        self_cert_path = cert_dir / "self-signed.crt"
        
        # Generate self-signed private key
        subprocess.run([
            "openssl", "genrsa", "-out", str(self_key_path), "2048"
        ], check=True, capture_output=True)
        
        # Create self-signed config
        self_config = create_openssl_config("self-signed-test")
        
        # Generate self-signed certificate
        subprocess.run([
            "openssl", "req", "-new", "-x509", "-key", str(self_key_path),
            "-out", str(self_cert_path), "-days", "365", "-config", self_config
        ], check=True, capture_output=True)
        
        print(f"✅ Self-signed certificate created: {self_cert_path}")
        
        # Clean up temporary files
        os.unlink(ca_config)
        os.unlink(server_config)
        os.unlink(admin_config)
        os.unlink(user_config)
        os.unlink(self_config)
        os.unlink(server_csr_path)
        os.unlink(admin_csr_path)
        os.unlink(user_csr_path)
        
        print("\n🎉 All test certificates created successfully!")
        print(f"📁 Certificates location: {cert_dir.absolute()}")
        
        # List created files
        print("\n📋 Created files:")
        for cert_file in sorted(cert_dir.glob("*")):
            print(f"  - {cert_file.name}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ OpenSSL command failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.decode()}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = create_test_certificates()
    exit(0 if success else 1)
