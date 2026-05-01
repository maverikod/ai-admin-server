# SSL/mTLS Guide

**Author:** Vasiliy Zdanovskiy  
**Email:** vasilyvz@gmail.com  
**Version:** 1.0  
**Date:** January 11, 2025

## Table of Contents

1. [Introduction](#introduction)
2. [SSL/TLS Overview](#ssltls-overview)
3. [mTLS Authentication](#mtls-authentication)
4. [Configuration](#configuration)
5. [SSL Modes](#ssl-modes)
6. [Certificate Management](#certificate-management)
7. [Security Best Practices](#security-best-practices)
8. [Examples](#examples)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

## Introduction

This guide provides comprehensive information about SSL/TLS and mTLS (mutual TLS) implementation in the AI Admin server. The system supports multiple authentication modes and provides robust security features for secure communication.

### Key Features

- **Multiple SSL Modes**: HTTP only, HTTPS only, mTLS, Token authentication
- **Certificate Management**: Automated certificate validation and management
- **Role-based Access Control**: Integration with certificate-based roles
- **Security Validation**: Comprehensive security checks and vulnerability scanning
- **Flexible Configuration**: Easy configuration through JSON files

## SSL/TLS Overview

### What is SSL/TLS?

SSL (Secure Sockets Layer) and TLS (Transport Layer Security) are cryptographic protocols that provide secure communication over a computer network. TLS is the successor to SSL and is widely used for securing web traffic, email, and other network communications.

### Key Components

1. **Encryption**: Data is encrypted during transmission
2. **Authentication**: Server identity is verified using certificates
3. **Integrity**: Data integrity is ensured through message authentication codes
4. **Perfect Forward Secrecy**: Each session uses unique encryption keys

### TLS Versions

The system supports TLS versions 1.2 and 1.3, with TLS 1.2 as the minimum recommended version for security.

## mTLS Authentication

### What is mTLS?

Mutual TLS (mTLS) is a security protocol where both the client and server authenticate each other using certificates. This provides stronger security than standard TLS, where only the server is authenticated.

### Benefits of mTLS

- **Strong Authentication**: Both parties are authenticated
- **Zero Trust Security**: No implicit trust between services
- **Certificate-based Roles**: Roles can be embedded in certificates
- **Audit Trail**: All connections are cryptographically verified

### mTLS Flow

1. Client initiates connection with server
2. Server presents its certificate to client
3. Client validates server certificate
4. Client presents its certificate to server
5. Server validates client certificate and extracts roles
6. Secure communication begins with role-based access control

## Configuration

### Basic SSL Configuration

```json
{
  "ssl": {
    "enabled": true,
    "mode": "https_only",
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key",
    "ca_cert": "./certs/ca.crt",
    "verify_client": false,
    "min_tls_version": "TLSv1.2",
    "max_tls_version": "TLSv1.3"
  }
}
```

### mTLS Configuration

```json
{
  "ssl": {
    "enabled": true,
    "mode": "mtls",
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key",
    "ca_cert": "./certs/ca.crt",
    "verify_client": true,
    "require_client_cert": true,
    "min_tls_version": "TLSv1.2"
  },
  "roles": {
    "enabled": true,
    "certificate_based": true
  }
}
```

### Security Parameters

```json
{
  "ssl": {
    "cipher_suite": "TLS_AES_256_GCM_SHA384",
    "check_hostname": true,
    "check_expiry": true,
    "expiry_warning_days": 30
  },
  "certificates": {
    "key_size": 2048,
    "hash_algorithm": "sha256",
    "default_validity_days": 365,
    "auto_renewal": false
  }
}
```

## SSL Modes

### HTTP Only Mode

```json
{
  "ssl": {
    "enabled": false
  }
}
```

- No encryption
- Suitable for development only
- Not recommended for production

### HTTPS Only Mode

```json
{
  "ssl": {
    "enabled": true,
    "mode": "https_only",
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key"
  }
}
```

- Server authentication only
- Client authentication via tokens or other methods
- Standard web security

### mTLS Mode

```json
{
  "ssl": {
    "enabled": true,
    "mode": "mtls",
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key",
    "ca_cert": "./certs/ca.crt",
    "verify_client": true,
    "require_client_cert": true
  }
}
```

- Mutual authentication
- Certificate-based client authentication
- Role-based access control
- Highest security level

### Token Authentication Mode

```json
{
  "ssl": {
    "enabled": true,
    "mode": "token_auth",
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key",
    "token_auth_enabled": true
  }
}
```

- SSL encryption with token authentication
- Hybrid approach
- Flexible authentication

## Certificate Management

### Certificate Types

1. **Server Certificate**: Identifies the server to clients
2. **Client Certificate**: Identifies clients to the server
3. **CA Certificate**: Root certificate authority
4. **Intermediate Certificate**: Intermediate CA certificates

### Certificate Storage

```
certs/
├── server.crt          # Server certificate
├── server.key          # Server private key
├── ca.crt              # CA certificate
├── client.crt          # Client certificate
├── client.key          # Client private key
└── intermediate.crt    # Intermediate certificate
```

### Certificate Validation

The system performs comprehensive certificate validation:

- **Expiry Check**: Validates certificate expiration dates
- **Chain Validation**: Verifies certificate chain integrity
- **Revocation Check**: Checks certificate revocation status
- **Key Strength**: Validates key size and algorithms
- **Signature Verification**: Verifies certificate signatures

### Certificate Generation

```bash
# Generate CA certificate
openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 365 -key ca.key -out ca.crt

# Generate server certificate
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr
openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -out server.crt

# Generate client certificate
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr
openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key -out client.crt
```

## Security Best Practices

### Certificate Security

1. **Strong Keys**: Use at least 2048-bit RSA keys
2. **Secure Storage**: Protect private keys with proper file permissions
3. **Regular Rotation**: Rotate certificates before expiration
4. **Monitoring**: Monitor certificate expiration dates
5. **Backup**: Maintain secure backups of certificates

### TLS Configuration

1. **Minimum TLS Version**: Use TLS 1.2 or higher
2. **Strong Ciphers**: Use strong cipher suites
3. **Perfect Forward Secrecy**: Enable PFS for session keys
4. **Certificate Pinning**: Consider certificate pinning for clients
5. **HSTS**: Use HTTP Strict Transport Security headers

### Network Security

1. **Firewall Rules**: Restrict access to SSL ports
2. **Network Segmentation**: Isolate SSL traffic
3. **Monitoring**: Monitor SSL connections and errors
4. **Logging**: Enable comprehensive SSL logging
5. **Intrusion Detection**: Use IDS/IPS for SSL traffic

## Examples

### Basic HTTPS Server

```python
from ai_admin.core.server import ServerManager
from ai_admin.config.ssl_config import SSLConfig

# Configure SSL
ssl_config = SSLConfig({
    "ssl": {
        "enabled": true,
        "mode": "https_only",
        "cert_file": "./certs/server.crt",
        "key_file": "./certs/server.key"
    }
})

# Create server
server = ServerManager(ssl_config=ssl_config)
await server.start()
```

### mTLS Server with Roles

```python
from ai_admin.core.server import ServerManager
from ai_admin.config.ssl_config import SSLConfig
from ai_admin.config.roles_config import RolesConfig

# Configure SSL with mTLS
ssl_config = SSLConfig({
    "ssl": {
        "enabled": true,
        "mode": "mtls",
        "cert_file": "./certs/server.crt",
        "key_file": "./certs/server.key",
        "ca_cert": "./certs/ca.crt",
        "verify_client": true,
        "require_client_cert": true
    }
})

# Configure roles
roles_config = RolesConfig({
    "roles": {
        "enabled": true,
        "certificate_based": true,
        "roles": {
            "admin": ["read", "write", "delete"],
            "user": ["read"],
            "guest": ["read_public"]
        }
    }
})

# Create server
server = ServerManager(ssl_config=ssl_config, roles_config=roles_config)
await server.start()
```

### Client Connection

```python
import ssl
import aiohttp

# Create SSL context
ssl_context = ssl.create_default_context()
ssl_context.load_cert_chain("client.crt", "client.key")
ssl_context.load_verify_locations("ca.crt")

# Make request
async with aiohttp.ClientSession() as session:
    async with session.get(
        "https://server:8443/api/data",
        ssl=ssl_context
    ) as response:
        data = await response.json()
```

## Troubleshooting

### Common Issues

#### Certificate Errors

**Problem**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution**: 
- Verify certificate chain
- Check certificate expiration
- Ensure CA certificate is trusted

#### Connection Refused

**Problem**: `Connection refused`

**Solution**:
- Check if server is running
- Verify port configuration
- Check firewall rules

#### mTLS Authentication Failed

**Problem**: `Client certificate required`

**Solution**:
- Ensure client certificate is provided
- Verify client certificate is signed by trusted CA
- Check certificate roles and permissions

### Debugging

Enable debug logging:

```json
{
  "logging": {
    "level": "DEBUG",
    "ssl_debug": true
  }
}
```

### Validation Commands

```bash
# Validate certificate
openssl x509 -in server.crt -text -noout

# Check certificate chain
openssl verify -CAfile ca.crt server.crt

# Test SSL connection
openssl s_client -connect server:8443 -cert client.crt -key client.key -CAfile ca.crt
```

## FAQ

### Q: What is the difference between SSL and TLS?

A: TLS is the successor to SSL. SSL 3.0 was deprecated due to security vulnerabilities. TLS 1.2 and 1.3 are the current secure standards.

### Q: When should I use mTLS?

A: Use mTLS when you need strong authentication for both client and server, such as in microservices architectures or high-security environments.

### Q: How do I handle certificate expiration?

A: The system provides automatic expiration monitoring and warnings. Set up automated certificate renewal processes for production environments.

### Q: Can I use self-signed certificates?

A: Yes, for development and testing. For production, use certificates from a trusted Certificate Authority.

### Q: What key size should I use?

A: Use at least 2048-bit RSA keys. For new deployments, consider 3072-bit or 4096-bit keys for enhanced security.

### Q: How do I implement certificate-based roles?

A: Embed role information in certificate extensions or use certificate CN/SAN fields to map to roles in your configuration.

---

**For more information, see:**
- [Certificate Management Guide](certificate_management.md)
- [Role-based Access Guide](role_based_access.md)
- [Security Best Practices](security_best_practices.md)
- [API Reference](api_reference.md)
