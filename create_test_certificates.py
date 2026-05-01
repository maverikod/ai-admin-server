#!/usr/bin/env python3
"""
Create test SSL certificates for testing.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import subprocess
import sys
from pathlib import Path


def create_certificates():
    """Create test SSL certificates."""
    cert_dir = Path("certificates")
    cert_dir.mkdir(exist_ok=True)
    
    # Create CA key and certificate
    print("Creating CA certificate...")
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:4096", "-keyout", 
        str(cert_dir / "ca.key"), "-out", str(cert_dir / "ca.crt"), 
        "-days", "365", "-nodes", "-subj", "/C=UA/ST=Kyiv/L=Kyiv/O=Test/CN=TestCA"
    ], check=True)
    
    # Create server key
    print("Creating server key...")
    subprocess.run([
        "openssl", "genrsa", "-out", str(cert_dir / "test.key"), "2048"
    ], check=True)
    
    # Create server certificate request
    print("Creating server certificate request...")
    subprocess.run([
        "openssl", "req", "-new", "-key", str(cert_dir / "test.key"), 
        "-out", str(cert_dir / "test.csr"), 
        "-subj", "/C=UA/ST=Kyiv/L=Kyiv/O=Test/CN=localhost"
    ], check=True)
    
    # Create server certificate
    print("Creating server certificate...")
    subprocess.run([
        "openssl", "x509", "-req", "-in", str(cert_dir / "test.csr"), 
        "-CA", str(cert_dir / "ca.crt"), "-CAkey", str(cert_dir / "ca.key"), 
        "-CAcreateserial", "-out", str(cert_dir / "test.crt"), "-days", "365"
    ], check=True)
    
    # Create client key and certificate
    print("Creating client certificate...")
    subprocess.run([
        "openssl", "genrsa", "-out", str(cert_dir / "client.key"), "2048"
    ], check=True)
    
    subprocess.run([
        "openssl", "req", "-new", "-key", str(cert_dir / "client.key"), 
        "-out", str(cert_dir / "client.csr"), 
        "-subj", "/C=UA/ST=Kyiv/L=Kyiv/O=Test/CN=client"
    ], check=True)
    
    subprocess.run([
        "openssl", "x509", "-req", "-in", str(cert_dir / "client.csr"), 
        "-CA", str(cert_dir / "ca.crt"), "-CAkey", str(cert_dir / "ca.key"), 
        "-CAcreateserial", "-out", str(cert_dir / "client.crt"), "-days", "365"
    ], check=True)
    
    print("✅ Certificates created successfully!")
    print(f"CA certificate: {cert_dir / 'ca.crt'}")
    print(f"Server certificate: {cert_dir / 'test.crt'}")
    print(f"Server key: {cert_dir / 'test.key'}")
    print(f"Client certificate: {cert_dir / 'client.crt'}")
    print(f"Client key: {cert_dir / 'client.key'}")


if __name__ == "__main__":
    try:
        create_certificates()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating certificates: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ OpenSSL not found. Please install OpenSSL.")
        sys.exit(1)
