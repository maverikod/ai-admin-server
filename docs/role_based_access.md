# Role-based Access Control Guide

**Author:** Vasiliy Zdanovskiy  
**Email:** vasilyvz@gmail.com  
**Version:** 1.0  
**Date:** January 11, 2025

## Table of Contents

1. [Introduction](#introduction)
2. [Role System Overview](#role-system-overview)
3. [Permission Levels](#permission-levels)
4. [Role Configuration](#role-configuration)
5. [Certificate-based Roles](#certificate-based-roles)
6. [Role Hierarchy](#role-hierarchy)
7. [Security Integration](#security-integration)
8. [Examples](#examples)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Introduction

This guide provides comprehensive information about the role-based access control (RBAC) system in the AI Admin server. The system supports hierarchical roles, certificate-based authentication, and fine-grained permissions for secure access control.

### Key Features

- **Hierarchical Roles**: Support for role inheritance and hierarchy
- **Certificate-based Authentication**: Roles embedded in mTLS certificates
- **Fine-grained Permissions**: Granular control over operations and resources
- **Security Integration**: Integration with SSL/mTLS and security adapters
- **Audit Logging**: Comprehensive audit trail for all access control decisions
- **Flexible Configuration**: JSON-based configuration with validation

## Role System Overview

### Core Concepts

**Roles**: Named collections of permissions that define what a user can do.

**Permissions**: Specific actions or access rights that can be granted to roles.

**Hierarchy**: Parent-child relationships between roles that enable permission inheritance.

**Certificate OIDs**: Object Identifiers used to embed role information in certificates.

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Certificate   │───▶│   Role System   │───▶│   Permissions   │
│   (mTLS)        │    │   (RBAC)        │    │   (Actions)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Role Mapping   │    │  Role Hierarchy │    │  Access Control │
│  (OID-based)    │    │  (Inheritance)  │    │  (Enforcement)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Permission Levels

### Permission Level Hierarchy

The system supports five permission levels in ascending order of authority:

#### 1. NONE
- **Description**: No access to resources
- **Use Case**: Disabled or restricted users
- **Example**: `"level": "none"`

#### 2. READ
- **Description**: Read-only access to resources
- **Use Case**: Viewers, auditors, monitoring systems
- **Example**: `"level": "read"`

#### 3. WRITE
- **Description**: Read and write access to resources
- **Use Case**: Regular users, developers
- **Example**: `"level": "write"`

#### 4. ADMIN
- **Description**: Administrative access to resources
- **Use Case**: System administrators, team leads
- **Example**: `"level": "admin"`

#### 5. SUPER_ADMIN
- **Description**: Full system access
- **Use Case**: System owners, security administrators
- **Example**: `"level": "super_admin"`

### Permission Structure

```json
{
  "name": "ssl:manage",
  "level": "admin",
  "description": "Manage SSL certificates and configurations",
  "resource": "ssl",
  "actions": ["create", "update", "delete", "list"]
}
```

## Role Configuration

### Basic Role Definition

```json
{
  "roles": {
    "admin": {
      "description": "System administrator with full access",
      "permissions": [
        {
          "name": "ssl:admin",
          "level": "admin",
          "description": "Full SSL management access"
        },
        {
          "name": "k8s:admin",
          "level": "admin",
          "description": "Full Kubernetes management access"
        }
      ],
      "parent_roles": [],
      "certificate_oids": ["1.2.3.4.5.6.7.8.9.1"],
      "is_active": true
    }
  }
}
```

### Role with Inheritance

```json
{
  "roles": {
    "senior_admin": {
      "description": "Senior administrator with extended privileges",
      "permissions": [
        {
          "name": "system:super_admin",
          "level": "super_admin",
          "description": "Super administrator privileges"
        }
      ],
      "parent_roles": ["admin"],
      "certificate_oids": ["1.2.3.4.5.6.7.8.9.2"],
      "is_active": true
    },
    "admin": {
      "description": "System administrator",
      "permissions": [
        {
          "name": "ssl:admin",
          "level": "admin",
          "description": "SSL management access"
        }
      ],
      "parent_roles": ["user"],
      "certificate_oids": ["1.2.3.4.5.6.7.8.9.1"],
      "is_active": true
    },
    "user": {
      "description": "Regular user",
      "permissions": [
        {
          "name": "ssl:read",
          "level": "read",
          "description": "Read SSL information"
        }
      ],
      "parent_roles": [],
      "certificate_oids": ["1.2.3.4.5.6.7.8.9.3"],
      "is_active": true
    }
  }
}
```

### Complete Configuration Example

```json
{
  "permissions": {
    "roles": {
      "super_admin": {
        "description": "Super administrator with full system access",
        "permissions": [
          {
            "name": "system:super_admin",
            "level": "super_admin",
            "description": "Full system access"
          }
        ],
        "parent_roles": [],
        "certificate_oids": ["1.2.3.4.5.6.7.8.9.0"],
        "is_active": true
      },
      "admin": {
        "description": "System administrator",
        "permissions": [
          {
            "name": "ssl:admin",
            "level": "admin",
            "description": "SSL certificate management"
          },
          {
            "name": "k8s:admin",
            "level": "admin",
            "description": "Kubernetes cluster management"
          },
          {
            "name": "queue:admin",
            "level": "admin",
            "description": "Queue management"
          }
        ],
        "parent_roles": ["user"],
        "certificate_oids": ["1.2.3.4.5.6.7.8.9.1"],
        "is_active": true
      },
      "user": {
        "description": "Regular user",
        "permissions": [
          {
            "name": "ssl:read",
            "level": "read",
            "description": "Read SSL information"
          },
          {
            "name": "k8s:read",
            "level": "read",
            "description": "Read Kubernetes information"
          }
        ],
        "parent_roles": [],
        "certificate_oids": ["1.2.3.4.5.6.7.8.9.2"],
        "is_active": true
      },
      "guest": {
        "description": "Guest user with minimal access",
        "permissions": [
          {
            "name": "system:read_public",
            "level": "read",
            "description": "Read public information only"
          }
        ],
        "parent_roles": [],
        "certificate_oids": [],
        "is_active": true
      }
    },
    "default_role": "guest",
    "admin_role": "admin",
    "role_hierarchy": {
      "super_admin": ["admin"],
      "admin": ["user"],
      "user": ["guest"]
    }
  },
  "security": {
    "auth": {
      "certificate_roles_oid": "1.2.3.4.5.6.7.8.9"
    }
  }
}
```

## Certificate-based Roles

### Certificate OID Mapping

Roles can be embedded in certificates using Object Identifiers (OIDs):

```json
{
  "security": {
    "auth": {
      "certificate_roles_oid": "1.2.3.4.5.6.7.8.9"
    }
  }
}
```

### Certificate Role Assignment

When generating certificates, roles can be assigned:

```python
from ai_admin.commands.ssl_cert_generate_command import SSLCertGenerateCommand

command = SSLCertGenerateCommand()
result = await command.execute(
    cert_type="client",
    common_name="admin@example.com",
    roles=["admin", "ssl:manage"],
    user_roles=["ssl:admin"]
)
```

### Role Extraction from Certificates

The system automatically extracts roles from certificates during mTLS authentication:

```python
from ai_admin.core.mtls_auth_manager import MTLSAuthManager

auth_manager = MTLSAuthManager()
result = await auth_manager.authenticate_client(
    certificate_data=cert_data,
    required_permissions=["ssl:read"]
)

# Result contains extracted roles
roles = result.get("roles", [])
```

## Role Hierarchy

### Hierarchy Definition

Role hierarchy is defined in the configuration:

```json
{
  "role_hierarchy": {
    "super_admin": ["admin"],
    "admin": ["user"],
    "user": ["guest"]
  }
}
```

### Permission Inheritance

Roles inherit permissions from their parent roles:

```python
from ai_admin.config.roles_config import RolesConfig

config = RolesConfig(config_data)
all_permissions = config._role_hierarchy.get_all_permissions("admin")

# Returns permissions from admin role plus inherited from user role
```

### Hierarchy Validation

The system validates role hierarchy to prevent circular dependencies:

```python
# This will raise an error if circular dependency is detected
config.validate_roles_config()
```

## Security Integration

### Security Adapters

Each security adapter integrates with the role system:

```python
from ai_admin.security.ssl_security_adapter import SSLSecurityAdapter

adapter = SSLSecurityAdapter()
has_permission = adapter.check_ssl_certificate_permissions(
    user_roles=["admin"],
    certificate_type=SSLCertificateType.SERVER,
    operation=SSLOperation.CREATE
)
```

### Permission Checking

The system provides multiple methods for permission checking:

#### Single Permission Check
```python
has_permission = config.has_permission("admin", "ssl:manage")
```

#### Multiple Permission Check
```python
has_any_permission = config.has_any_permission(
    user_roles=["admin", "user"],
    required_permissions=["ssl:read", "ssl:write"]
)
```

#### Role Validation
```python
is_allowed = config.is_role_allowed("admin")
```

### Audit Logging

All role-based access control decisions are logged:

```python
# Audit log entry
{
    "timestamp": "2025-01-11T10:30:00Z",
    "user": "admin@example.com",
    "roles": ["admin", "ssl:manage"],
    "operation": "ssl:create",
    "resource": "certificate",
    "result": "allowed",
    "permissions_checked": ["ssl:admin", "ssl:manage"]
}
```

## Examples

### Basic Role Management

```python
from ai_admin.config.roles_config import RolesConfig, Role, Permission, PermissionLevel

# Create role configuration
config = RolesConfig({
    "permissions": {
        "roles": {
            "admin": {
                "description": "System administrator",
                "permissions": [
                    {
                        "name": "ssl:admin",
                        "level": "admin",
                        "description": "SSL management"
                    }
                ],
                "parent_roles": [],
                "certificate_oids": ["1.2.3.4.5.6.7.8.9.1"],
                "is_active": true
            }
        },
        "default_role": "guest",
        "admin_role": "admin"
    }
})

# Check permissions
has_permission = config.has_permission("admin", "ssl:admin")
print(f"Admin has ssl:admin permission: {has_permission}")

# Get role information
role_info = config.get_role_info("admin")
print(f"Role info: {role_info}")
```

### mTLS Role Command

```python
from ai_admin.commands.mtls_roles_command import MtlsRolesCommand

command = MtlsRolesCommand()

# Check access permissions
result = await command.execute(
    action="check_access",
    role_name="admin",
    operation="ssl:create",
    user_roles=["ssl:admin"]
)

print(f"Access check result: {result.data}")

# List all roles
result = await command.execute(
    action="list_roles",
    user_roles=["ssl:admin"]
)

print(f"Available roles: {result.data}")
```

### Certificate with Roles

```python
from ai_admin.commands.ssl_cert_generate_command import SSLCertGenerateCommand

command = SSLCertGenerateCommand()

# Generate certificate with roles
result = await command.execute(
    cert_type="client",
    common_name="admin@example.com",
    roles=["admin", "ssl:manage", "k8s:read"],
    ca_cert_path="./certs/ca.crt",
    ca_key_path="./certs/ca.key",
    user_roles=["ssl:admin"]
)

print(f"Certificate generated with roles: {result.data}")
```

### Role Validation

```python
from ai_admin.commands.ssl_cert_verify_command import SSLCertVerifyCommand

command = SSLCertVerifyCommand()

# Verify certificate with role checking
result = await command.execute(
    cert_path="./certs/client.crt",
    ca_cert_path="./certs/ca.crt",
    check_roles=True,
    required_roles=["admin"],
    user_roles=["ssl:read"]
)

print(f"Certificate verification: {result.data}")
```

## Best Practices

### Role Design

1. **Principle of Least Privilege**: Grant minimum necessary permissions
2. **Role Separation**: Separate administrative and operational roles
3. **Clear Naming**: Use descriptive role and permission names
4. **Documentation**: Document role purposes and permissions

### Permission Structure

1. **Hierarchical Permissions**: Use consistent permission naming
2. **Resource-based**: Organize permissions by resource type
3. **Action-based**: Include specific actions in permissions
4. **Level Consistency**: Use consistent permission levels

### Certificate Integration

1. **OID Management**: Use consistent OID structure
2. **Role Validation**: Always validate roles from certificates
3. **Certificate Lifecycle**: Manage certificate roles throughout lifecycle
4. **Backup Strategy**: Backup role configurations

### Security Considerations

1. **Regular Audits**: Regularly audit role assignments
2. **Access Reviews**: Periodic review of user access
3. **Monitoring**: Monitor role-based access patterns
4. **Incident Response**: Have procedures for role compromise

## Troubleshooting

### Common Issues

#### Role Not Found

**Problem**: `Role 'admin' not found in roles`

**Solution**:
- Check role configuration file
- Verify role name spelling
- Ensure role is active (`is_active: true`)

#### Permission Denied

**Problem**: `Permission denied: Insufficient permissions`

**Solution**:
- Check user roles
- Verify permission requirements
- Check role hierarchy inheritance

#### Circular Dependency

**Problem**: `Circular dependency detected in role hierarchy`

**Solution**:
- Review role hierarchy configuration
- Remove circular parent-child relationships
- Validate configuration with `validate_roles_config()`

#### Certificate Role Extraction Failed

**Problem**: `Failed to extract roles from certificate`

**Solution**:
- Verify certificate OID configuration
- Check certificate format and validity
- Ensure roles are properly embedded in certificate

### Debug Commands

```python
# Check role configuration
config = RolesConfig(config_data)
print(config.get_config_summary())

# Validate configuration
try:
    config.validate_roles_config()
    print("Configuration is valid")
except ValueError as e:
    print(f"Configuration error: {e}")

# Check permissions
has_permission = config.has_permission("admin", "ssl:manage")
print(f"Permission check: {has_permission}")

# Get all permissions for role
all_permissions = config._role_hierarchy.get_all_permissions("admin")
print(f"All permissions: {all_permissions}")
```

### Log Analysis

Check logs for role-related issues:

```bash
# Check role access logs
grep "role" /var/log/ai_admin/security.log

# Check permission logs
grep "permission" /var/log/ai_admin/audit.log

# Check certificate role logs
grep "certificate.*role" /var/log/ai_admin/ssl.log
```

---

**For more information, see:**
- [SSL/mTLS Guide](ssl_mtls_guide.md)
- [Certificate Management Guide](certificate_management.md)
- [Security Best Practices](security_best_practices.md)
- [API Reference](api_reference.md)
