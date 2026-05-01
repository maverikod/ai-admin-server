# Certificate Management Guide

**Author:** Vasiliy Zdanovskiy  
**Email:** vasilyvz@gmail.com  
**Version:** 1.0  
**Date:** January 11, 2025

## Table of Contents

1. [Introduction](#introduction)
2. [Certificate Types](#certificate-types)
3. [Certificate Lifecycle](#certificate-lifecycle)
4. [Certificate Operations](#certificate-operations)
5. [Security and Permissions](#security-and-permissions)
6. [Certificate Storage](#certificate-storage)
7. [Automation and Monitoring](#automation-and-monitoring)
8. [Best Practices](#best-practices)
9. [Examples](#examples)
10. [Troubleshooting](#troubleshooting)

## Introduction

This guide provides comprehensive information about certificate management in the AI Admin server. The system supports various certificate types, automated lifecycle management, and role-based access control for certificate operations.

### Key Features

- **Multiple Certificate Types**: Server, client, CA, and intermediate certificates
- **Automated Lifecycle Management**: Generation, validation, renewal, and revocation
- **Role-based Access Control**: Secure certificate operations with permission validation
- **Certificate Storage**: Organized storage with security controls
- **Monitoring and Alerts**: Expiration monitoring and automated notifications
- **Integration**: Seamless integration with SSL/mTLS and role systems

## Certificate Types

### Server Certificates

Server certificates identify the server to clients and are used for HTTPS connections.

**Characteristics:**
- Identifies the server (Common Name or Subject Alternative Names)
- Used for server authentication
- Contains public key for encryption
- Signed by CA or self-signed

**Usage:**
```json
{
  "cert_type": "server",
  "common_name": "api.example.com",
  "subject_alt_names": ["api.example.com", "*.example.com"],
  "key_usage": ["digitalSignature", "keyEncipherment"],
  "extended_key_usage": ["serverAuth"]
}
```

### Client Certificates

Client certificates identify clients to the server and are used for mTLS authentication.

**Characteristics:**
- Identifies the client (user or service)
- Used for client authentication
- Contains roles and permissions
- Signed by trusted CA

**Usage:**
```json
{
  "cert_type": "client",
  "common_name": "user@example.com",
  "roles": ["admin", "user"],
  "key_usage": ["digitalSignature"],
  "extended_key_usage": ["clientAuth"]
}
```

### CA Certificates

Certificate Authority (CA) certificates are used to sign other certificates.

**Characteristics:**
- Root of trust for certificate chain
- Used to sign other certificates
- Long validity period
- High security requirements

**Usage:**
```json
{
  "cert_type": "ca",
  "common_name": "Example CA",
  "basic_constraints": {"ca": true, "pathlen": 1},
  "key_usage": ["keyCertSign", "cRLSign"],
  "validity_days": 3650
}
```

### Intermediate Certificates

Intermediate certificates bridge the gap between root CA and end certificates.

**Characteristics:**
- Signed by root CA
- Used to sign end certificates
- Shorter validity than root CA
- Provides additional security layer

## Certificate Lifecycle

### 1. Generation

Certificates are generated using the `ssl_cert_generate` command with role-based access control.

**Basic Generation:**
```python
from ai_admin.commands.ssl_cert_generate_command import SSLCertGenerateCommand

command = SSLCertGenerateCommand()
result = await command.execute(
    cert_type="server",
    common_name="api.example.com",
    key_size=2048,
    days_valid=365,
    user_roles=["ssl:admin"]
)
```

**Advanced Generation with Roles:**
```python
result = await command.execute(
    cert_type="client",
    common_name="admin@example.com",
    roles=["admin", "ssl:manage"],
    ca_cert_path="./certs/ca.crt",
    ca_key_path="./certs/ca.key",
    user_roles=["ssl:admin"]
)
```

### 2. Validation

Certificates are validated for:
- **Expiration**: Check if certificate is still valid
- **Chain**: Verify certificate chain integrity
- **Revocation**: Check if certificate is revoked
- **Key Strength**: Validate key size and algorithms
- **Signature**: Verify certificate signature

**Validation Command:**
```python
from ai_admin.commands.ssl_cert_verify_command import SSLCertVerifyCommand

command = SSLCertVerifyCommand()
result = await command.execute(
    cert_path="./certs/server.crt",
    ca_cert_path="./certs/ca.crt",
    check_expiry=True,
    check_revocation=True,
    user_roles=["ssl:read"]
)
```

### 3. Renewal

Certificates can be automatically renewed before expiration.

**Renewal Configuration:**
```json
{
  "certificates": {
    "auto_renewal": true,
    "renewal_threshold_days": 30,
    "renewal_notification_days": 60
  }
}
```

**Manual Renewal:**
```python
result = await command.execute(
    action="renew",
    cert_path="./certs/server.crt",
    days_valid=365,
    user_roles=["ssl:manage"]
)
```

### 4. Revocation

Certificates can be revoked when compromised or no longer needed.

**Revocation via CRL:**
```python
from ai_admin.commands.crl_operations_command import CRLOperationsCommand

command = CRLOperationsCommand()
result = await command.execute(
    action="create",
    ca_cert_path="./certs/ca.crt",
    ca_key_path="./certs/ca.key",
    revoked_serials=[{"serial": "12345", "reason": "keyCompromise"}],
    user_roles=["ssl:admin"]
)
```

## Certificate Operations

### Available Commands

#### 1. SSL Certificate Generation (`ssl_cert_generate`)

Generate various types of certificates with role-based access control.

**Parameters:**
- `cert_type`: Type of certificate (self_signed, ca_signed, server, client)
- `common_name`: Common Name for the certificate
- `key_size`: Key size in bits (2048, 4096)
- `days_valid`: Certificate validity period
- `roles`: List of roles to assign to certificate
- `user_roles`: User roles for permission validation

**Example:**
```python
result = await command.execute(
    cert_type="server",
    common_name="api.example.com",
    key_size=2048,
    days_valid=365,
    subject_alt_names=["api.example.com", "*.example.com"],
    user_roles=["ssl:admin"]
)
```

#### 2. SSL Certificate Verification (`ssl_cert_verify`)

Verify certificate validity, chain, and revocation status.

**Parameters:**
- `cert_path`: Path to certificate file
- `ca_cert_path`: Path to CA certificate
- `check_expiry`: Check certificate expiration
- `check_revocation`: Check revocation status
- `user_roles`: User roles for permission validation

#### 3. Certificate Key Pair (`cert_key_pair`)

Manage certificate and key pairs together.

**Parameters:**
- `action`: Operation (create, validate, backup, restore)
- `cert_path`: Path to certificate file
- `key_path`: Path to private key file
- `user_roles`: User roles for permission validation

#### 4. CRL Operations (`crl_operations`)

Manage Certificate Revocation Lists.

**Parameters:**
- `action`: CRL operation (create, update, view, verify)
- `ca_cert_path`: Path to CA certificate
- `ca_key_path`: Path to CA private key
- `revoked_serials`: List of revoked certificate serials
- `user_roles`: User roles for permission validation

#### 5. mTLS Roles (`mtls_roles`)

Manage roles embedded in certificates for mTLS authentication.

**Parameters:**
- `action`: Role operation (assign, remove, list, validate)
- `cert_path`: Path to certificate file
- `roles`: List of roles to assign
- `user_roles`: User roles for permission validation

### Kubernetes Certificate Management

For Kubernetes clusters, use the `k8s_certificates` command:

```python
from ai_admin.commands.k8s_certificates_command import K8sCertificatesCommand

command = K8sCertificatesCommand()
result = await command.execute(
    action="list",
    cluster_name="production",
    certificate_type="server",
    user_roles=["k8s:admin"]
)
```

## Security and Permissions

### Role-based Access Control

Certificate operations are protected by role-based access control:

**SSL Admin Roles:**
- `ssl:admin`: Full access to all certificate operations
- `ssl:manage`: Manage certificates (create, update, delete)
- `ssl:read`: Read-only access to certificates
- `ssl:verify`: Verify certificates only

**Certificate-specific Roles:**
- `certificate:create`: Create new certificates
- `certificate:update`: Update existing certificates
- `certificate:delete`: Delete certificates
- `certificate:revoke`: Revoke certificates
- `certificate:backup`: Backup certificates
- `certificate:restore`: Restore certificates

### Permission Validation

All certificate operations are validated through security adapters:

```python
# Example permission check
has_permission = security_adapter.check_ssl_certificate_permissions(
    user_roles=["ssl:admin"],
    certificate_type=SSLCertificateType.SERVER,
    operation=SSLOperation.CREATE
)
```

### Audit Logging

All certificate operations are logged for audit purposes:

```python
# Audit log entry
{
    "timestamp": "2025-01-11T10:30:00Z",
    "user": "admin@example.com",
    "operation": "certificate:create",
    "certificate_type": "server",
    "common_name": "api.example.com",
    "result": "success"
}
```

## Certificate Storage

### Directory Structure

```
certificates/
├── ca/                    # CA certificates
│   ├── root-ca.crt
│   ├── root-ca.key
│   └── intermediate-ca.crt
├── server/               # Server certificates
│   ├── api.example.com.crt
│   ├── api.example.com.key
│   └── *.example.com.crt
├── client/               # Client certificates
│   ├── admin@example.com.crt
│   ├── admin@example.com.key
│   └── user@example.com.crt
├── k8s/                  # Kubernetes certificates
│   ├── test-cluster/
│   └── production/
└── backup/               # Certificate backups
    ├── 2025-01-11/
    └── 2025-01-10/
```

### File Permissions

**Certificate Files (.crt):**
- Owner: `root:ssl-cert`
- Permissions: `644` (readable by all, writable by owner)

**Private Key Files (.key):**
- Owner: `root:ssl-cert`
- Permissions: `600` (readable/writable by owner only)

**CA Files:**
- Owner: `root:ssl-cert`
- Permissions: `600` (highest security)

### Backup Strategy

**Automated Backups:**
```json
{
  "certificates": {
    "backup_enabled": true,
    "backup_interval": "daily",
    "backup_retention_days": 90,
    "backup_encryption": true
  }
}
```

**Manual Backup:**
```python
result = await command.execute(
    action="backup",
    cert_path="./certs/server.crt",
    backup_path="./backup/2025-01-11/",
    user_roles=["ssl:admin"]
)
```

## Automation and Monitoring

### Expiration Monitoring

**Configuration:**
```json
{
  "certificates": {
    "monitoring_enabled": true,
    "expiry_warning_days": 30,
    "expiry_critical_days": 7,
    "notification_channels": ["email", "webhook"]
  }
}
```

**Monitoring Commands:**
```python
# Check certificate expiration
result = await command.execute(
    action="check_expiry",
    cert_path="./certs/server.crt",
    warning_days=30,
    user_roles=["ssl:read"]
)
```

### Automated Renewal

**Renewal Configuration:**
```json
{
  "certificates": {
    "auto_renewal": true,
    "renewal_threshold_days": 30,
    "renewal_attempts": 3,
    "renewal_backoff_hours": 24
  }
}
```

**Renewal Process:**
1. Monitor certificate expiration
2. Generate new certificate before expiration
3. Validate new certificate
4. Update server configuration
5. Restart services if needed
6. Backup old certificate

## Best Practices

### Certificate Security

1. **Strong Keys**: Use at least 2048-bit RSA keys, prefer 3072-bit or 4096-bit
2. **Secure Storage**: Protect private keys with proper file permissions
3. **Regular Rotation**: Rotate certificates before expiration
4. **Monitoring**: Monitor certificate expiration and health
5. **Backup**: Maintain secure backups of certificates and keys

### Key Management

1. **Key Generation**: Use cryptographically secure random number generators
2. **Key Storage**: Store keys in secure locations with proper permissions
3. **Key Rotation**: Implement regular key rotation policies
4. **Key Destruction**: Securely destroy old keys when no longer needed

### Certificate Lifecycle

1. **Planning**: Plan certificate lifecycle before deployment
2. **Documentation**: Document certificate purposes and owners
3. **Automation**: Automate certificate renewal and monitoring
4. **Testing**: Test certificate operations in non-production environments
5. **Recovery**: Have recovery procedures for certificate failures

### Compliance

1. **Standards**: Follow industry standards (X.509, PKCS)
2. **Audit**: Maintain audit logs for all certificate operations
3. **Retention**: Follow data retention policies for certificates
4. **Reporting**: Generate compliance reports for auditors

## Examples

### Complete Certificate Setup

```python
from ai_admin.commands.ssl_cert_generate_command import SSLCertGenerateCommand
from ai_admin.commands.ssl_cert_verify_command import SSLCertVerifyCommand
from ai_admin.commands.crl_operations_command import CRLOperationsCommand

# 1. Generate CA certificate
ca_command = SSLCertGenerateCommand()
ca_result = await ca_command.execute(
    cert_type="ca",
    common_name="Example CA",
    key_size=4096,
    days_valid=3650,
    basic_constraints={"ca": True, "pathlen": 1},
    user_roles=["ssl:admin"]
)

# 2. Generate server certificate
server_result = await ca_command.execute(
    cert_type="server",
    common_name="api.example.com",
    key_size=2048,
    days_valid=365,
    ca_cert_path="./certs/ca.crt",
    ca_key_path="./certs/ca.key",
    subject_alt_names=["api.example.com", "*.example.com"],
    user_roles=["ssl:admin"]
)

# 3. Generate client certificate with roles
client_result = await ca_command.execute(
    cert_type="client",
    common_name="admin@example.com",
    key_size=2048,
    days_valid=365,
    ca_cert_path="./certs/ca.crt",
    ca_key_path="./certs/ca.key",
    roles=["admin", "ssl:manage"],
    user_roles=["ssl:admin"]
)

# 4. Verify certificates
verify_command = SSLCertVerifyCommand()
verify_result = await verify_command.execute(
    cert_path="./certs/server.crt",
    ca_cert_path="./certs/ca.crt",
    check_expiry=True,
    check_revocation=True,
    user_roles=["ssl:read"]
)

# 5. Create CRL
crl_command = CRLOperationsCommand()
crl_result = await crl_command.execute(
    action="create",
    ca_cert_path="./certs/ca.crt",
    ca_key_path="./certs/ca.key",
    crl_path="./certs/ca.crl",
    validity_days=30,
    user_roles=["ssl:admin"]
)
```

### Certificate Monitoring Script

```python
import asyncio
from datetime import datetime, timedelta
from ai_admin.commands.ssl_cert_verify_command import SSLCertVerifyCommand

async def monitor_certificates():
    """Monitor certificate expiration and send alerts."""
    verify_command = SSLCertVerifyCommand()
    
    certificates = [
        "./certs/server.crt",
        "./certs/ca.crt",
        "./certs/client.crt"
    ]
    
    for cert_path in certificates:
        try:
            result = await verify_command.execute(
                cert_path=cert_path,
                check_expiry=True,
                user_roles=["ssl:read"]
            )
            
            if result.get("expires_soon"):
                days_until_expiry = result.get("days_until_expiry", 0)
                print(f"WARNING: {cert_path} expires in {days_until_expiry} days")
                
                if days_until_expiry <= 7:
                    print(f"CRITICAL: {cert_path} expires in {days_until_expiry} days")
                    # Send critical alert
                    
        except Exception as e:
            print(f"ERROR: Failed to check {cert_path}: {e}")

# Run monitoring
asyncio.run(monitor_certificates())
```

## Troubleshooting

### Common Issues

#### Certificate Generation Failed

**Problem**: `Certificate generation failed: Invalid key size`

**Solution**: 
- Use supported key sizes: 1024, 2048, 3072, 4096
- Check system resources for large key generation

#### Certificate Validation Failed

**Problem**: `Certificate validation failed: Invalid signature`

**Solution**:
- Verify certificate chain
- Check CA certificate validity
- Ensure certificate is not corrupted

#### Permission Denied

**Problem**: `Permission denied: Insufficient permissions for certificate operation`

**Solution**:
- Check user roles and permissions
- Ensure user has required roles (e.g., `ssl:admin`)
- Verify security adapter configuration

#### Certificate Expired

**Problem**: `Certificate expired: Certificate is no longer valid`

**Solution**:
- Generate new certificate
- Update server configuration
- Restart services

### Debug Commands

```bash
# Check certificate details
openssl x509 -in server.crt -text -noout

# Verify certificate chain
openssl verify -CAfile ca.crt server.crt

# Check certificate expiration
openssl x509 -in server.crt -dates -noout

# Test SSL connection
openssl s_client -connect server:443 -cert client.crt -key client.key -CAfile ca.crt
```

### Log Analysis

Check logs for certificate-related issues:

```bash
# Check SSL logs
grep "certificate" /var/log/ai_admin/ssl.log

# Check security logs
grep "ssl" /var/log/ai_admin/security.log

# Check audit logs
grep "certificate" /var/log/ai_admin/audit.log
```

---

**For more information, see:**
- [SSL/mTLS Guide](ssl_mtls_guide.md)
- [Role-based Access Guide](role_based_access.md)
- [Security Best Practices](security_best_practices.md)
- [API Reference](api_reference.md)
