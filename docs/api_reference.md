# API Reference

**Author:** Vasiliy Zdanovskiy  
**Email:** vasilyvz@gmail.com  
**Version:** 1.0  
**Date:** January 11, 2025

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Base URL and Endpoints](#base-url-and-endpoints)
4. [SSL/mTLS Commands](#sslmts-commands)
5. [Certificate Management Commands](#certificate-management-commands)
6. [Kubernetes Commands](#kubernetes-commands)
7. [Docker Commands](#docker-commands)
8. [Queue Commands](#queue-commands)
9. [System Commands](#system-commands)
10. [Error Handling](#error-handling)
11. [Response Formats](#response-formats)

## Introduction

This API reference provides comprehensive documentation for all available endpoints and commands in the AI Admin server. The API supports SSL/mTLS authentication, role-based access control, and provides access to various system management functions.

### API Features

- **RESTful API**: Standard HTTP methods and status codes
- **SSL/mTLS Support**: Secure communication with certificate-based authentication
- **Role-based Access Control**: Fine-grained permissions for different operations
- **Command-based Architecture**: Modular command system for different functionalities
- **Comprehensive Error Handling**: Detailed error responses with error codes
- **Audit Logging**: All operations are logged for security and compliance

## Authentication

### SSL/mTLS Authentication

The API supports mutual TLS (mTLS) authentication where both client and server authenticate each other using certificates.

#### Client Certificate Requirements

- **Certificate Format**: X.509 certificate in PEM format
- **Certificate Chain**: Must be signed by a trusted CA
- **Role Information**: Roles embedded in certificate extensions
- **Validity**: Certificate must be valid and not expired

#### Authentication Headers

```http
X-Client-Certificate: <base64-encoded-certificate>
X-Client-Certificate-Chain: <base64-encoded-certificate-chain>
```

### Token Authentication

For non-mTLS environments, the API supports token-based authentication.

#### Authorization Header

```http
Authorization: Bearer <token>
```

### Role-based Access Control

All API endpoints require appropriate permissions based on user roles:

- **ssl:admin**: Full SSL/certificate management access
- **ssl:manage**: SSL certificate management operations
- **ssl:read**: Read-only SSL information access
- **k8s:admin**: Full Kubernetes management access
- **k8s:manage**: Kubernetes resource management
- **k8s:read**: Read-only Kubernetes information
- **system:admin**: System administration access
- **queue:admin**: Queue management access

## Base URL and Endpoints

### Base URL

```
https://api.example.com/api/v1
```

### Standard Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-11T10:30:00Z",
  "version": "1.0.0",
  "ssl_enabled": true,
  "mtls_enabled": true
}
```

#### API Information
```http
GET /info
```

**Response:**
```json
{
  "name": "AI Admin API",
  "version": "1.0.0",
  "description": "AI Admin server with SSL/mTLS support",
  "endpoints": {
    "ssl": "/api/v1/ssl",
    "certificates": "/api/v1/certificates",
    "k8s": "/api/v1/k8s",
    "docker": "/api/v1/docker",
    "queue": "/api/v1/queue",
    "system": "/api/v1/system"
  }
}
```

## SSL/mTLS Commands

### SSL Certificate Generation

#### Generate Certificate
```http
POST /api/v1/ssl/certificates/generate
```

**Request Body:**
```json
{
  "cert_type": "server",
  "common_name": "api.example.com",
  "key_size": 2048,
  "days_valid": 365,
  "subject_alt_names": ["api.example.com", "*.example.com"],
  "roles": ["admin", "ssl:manage"],
  "ca_cert_path": "./certs/ca.crt",
  "ca_key_path": "./certs/ca.key"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "certificate_path": "./certs/server.crt",
    "key_path": "./certs/server.key",
    "certificate_info": {
      "subject": "CN=api.example.com",
      "issuer": "CN=AI Admin CA",
      "valid_from": "2025-01-11T00:00:00Z",
      "valid_to": "2026-01-11T00:00:00Z",
      "serial_number": "1234567890"
    }
  },
  "message": "Certificate generated successfully"
}
```

#### Verify Certificate
```http
POST /api/v1/ssl/certificates/verify
```

**Request Body:**
```json
{
  "cert_path": "./certs/server.crt",
  "ca_cert_path": "./certs/ca.crt",
  "check_expiry": true,
  "check_revocation": true,
  "check_roles": true,
  "required_roles": ["admin"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "certificate_valid": true,
    "chain_valid": true,
    "not_expired": true,
    "not_revoked": true,
    "roles_valid": true,
    "extracted_roles": ["admin", "ssl:manage"],
    "verification_details": {
      "basic_verification": {"valid": true},
      "chain_verification": {"valid": true},
      "expiry_check": {"valid": true, "days_until_expiry": 300},
      "roles_verification": {"valid": true}
    }
  }
}
```

### mTLS Role Management

#### Check Access Permissions
```http
POST /api/v1/ssl/mtls/check-access
```

**Request Body:**
```json
{
  "role_name": "admin",
  "operation": "ssl:create",
  "resource": "certificate"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "has_access": true,
    "role_name": "admin",
    "operation": "ssl:create",
    "permissions": ["ssl:admin", "ssl:manage"],
    "message": "Access granted"
  }
}
```

#### List Available Roles
```http
GET /api/v1/ssl/mtls/roles
```

**Response:**
```json
{
  "success": true,
  "data": {
    "roles": [
      {
        "name": "admin",
        "description": "System administrator",
        "permissions": ["ssl:admin", "k8s:admin"],
        "is_active": true
      },
      {
        "name": "user",
        "description": "Regular user",
        "permissions": ["ssl:read", "k8s:read"],
        "is_active": true
      }
    ],
    "total_roles": 2
  }
}
```

## Certificate Management Commands

### Certificate Operations

#### List Certificates
```http
GET /api/v1/certificates
```

**Query Parameters:**
- `type`: Certificate type (server, client, ca)
- `status`: Certificate status (valid, expired, revoked)
- `limit`: Maximum number of results (default: 100)
- `offset`: Number of results to skip (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "certificates": [
      {
        "id": "cert_001",
        "type": "server",
        "subject": "CN=api.example.com",
        "issuer": "CN=AI Admin CA",
        "valid_from": "2025-01-11T00:00:00Z",
        "valid_to": "2026-01-11T00:00:00Z",
        "status": "valid",
        "roles": ["admin"]
      }
    ],
    "total_count": 1,
    "limit": 100,
    "offset": 0
  }
}
```

#### Create Certificate
```http
POST /api/v1/certificates
```

**Request Body:**
```json
{
  "cert_type": "client",
  "common_name": "user@example.com",
  "key_size": 2048,
  "days_valid": 365,
  "roles": ["user"],
  "ca_cert_path": "./certs/ca.crt",
  "ca_key_path": "./certs/ca.key"
}
```

#### Update Certificate
```http
PUT /api/v1/certificates/{certificate_id}
```

**Request Body:**
```json
{
  "roles": ["admin", "ssl:manage"],
  "extensions": {
    "keyUsage": ["digitalSignature", "keyEncipherment"]
  }
}
```

#### Delete Certificate
```http
DELETE /api/v1/certificates/{certificate_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "certificate_id": "cert_001",
    "deleted": true,
    "message": "Certificate deleted successfully"
  }
}
```

### CRL Operations

#### Create CRL
```http
POST /api/v1/certificates/crl
```

**Request Body:**
```json
{
  "ca_cert_path": "./certs/ca.crt",
  "ca_key_path": "./certs/ca.key",
  "crl_path": "./certs/ca.crl",
  "validity_days": 30,
  "revoked_serials": [
    {
      "serial": "1234567890",
      "reason": "keyCompromise"
    }
  ]
}
```

#### Verify CRL
```http
POST /api/v1/certificates/crl/verify
```

**Request Body:**
```json
{
  "crl_path": "./certs/ca.crl",
  "ca_cert_path": "./certs/ca.crt"
}
```

## Kubernetes Commands

### Cluster Management

#### List Clusters
```http
GET /api/v1/k8s/clusters
```

**Response:**
```json
{
  "success": true,
  "data": {
    "clusters": [
      {
        "name": "production",
        "status": "running",
        "nodes": 3,
        "version": "1.25.0",
        "endpoint": "https://k8s-prod.example.com:6443"
      }
    ],
    "total_count": 1
  }
}
```

#### Create Cluster
```http
POST /api/v1/k8s/clusters
```

**Request Body:**
```json
{
  "name": "staging",
  "version": "1.25.0",
  "nodes": 2,
  "node_type": "t3.medium",
  "region": "us-west-2"
}
```

### Certificate Management

#### List K8s Certificates
```http
GET /api/v1/k8s/certificates
```

**Query Parameters:**
- `cluster_name`: Name of the cluster
- `namespace`: Kubernetes namespace
- `certificate_type`: Type of certificate

**Response:**
```json
{
  "success": true,
  "data": {
    "certificates": [
      {
        "name": "tls-secret",
        "namespace": "default",
        "type": "kubernetes.io/tls",
        "certificates": ["server.crt", "server.key"],
        "expires": "2026-01-11T00:00:00Z"
      }
    ],
    "cluster_name": "production"
  }
}
```

#### Create K8s Certificate
```http
POST /api/v1/k8s/certificates
```

**Request Body:**
```json
{
  "cluster_name": "production",
  "namespace": "default",
  "cert_name": "api-tls",
  "server_cert": "base64-encoded-server-cert",
  "server_key": "base64-encoded-server-key",
  "ca_cert": "base64-encoded-ca-cert"
}
```

### mTLS Setup

#### Setup K8s mTLS
```http
POST /api/v1/k8s/mtls/setup
```

**Request Body:**
```json
{
  "cluster_name": "production",
  "namespace": "default",
  "cert_name": "mtls-cert",
  "ca_cert": "base64-encoded-ca-cert",
  "server_cert": "base64-encoded-server-cert",
  "server_key": "base64-encoded-server-key",
  "client_cert": "base64-encoded-client-cert",
  "client_key": "base64-encoded-client-key"
}
```

## Docker Commands

### Container Management

#### List Containers
```http
GET /api/v1/docker/containers
```

**Query Parameters:**
- `status`: Container status (running, stopped, all)
- `limit`: Maximum number of results

**Response:**
```json
{
  "success": true,
  "data": {
    "containers": [
      {
        "id": "abc123def456",
        "name": "ai-admin-server",
        "image": "ai-admin:latest",
        "status": "running",
        "ports": ["443:443", "8443:8443"],
        "created": "2025-01-11T08:00:00Z"
      }
    ],
    "total_count": 1
  }
}
```

#### Create Container
```http
POST /api/v1/docker/containers
```

**Request Body:**
```json
{
  "image": "ai-admin:latest",
  "name": "ai-admin-test",
  "ports": {
    "443": 8443,
    "8443": 9443
  },
  "environment": {
    "CONFIG_FILE": "/app/config/config.json"
  },
  "volumes": {
    "/host/certs": "/app/certs",
    "/host/logs": "/app/logs"
  }
}
```

### Image Management

#### List Images
```http
GET /api/v1/docker/images
```

**Response:**
```json
{
  "success": true,
  "data": {
    "images": [
      {
        "id": "sha256:abc123def456",
        "repository": "ai-admin",
        "tag": "latest",
        "size": "500MB",
        "created": "2025-01-11T07:00:00Z"
      }
    ],
    "total_count": 1
  }
}
```

#### Build Image
```http
POST /api/v1/docker/images/build
```

**Request Body:**
```json
{
  "dockerfile_path": "./Dockerfile",
  "tag": "ai-admin:latest",
  "build_args": {
    "PYTHON_VERSION": "3.11"
  },
  "context_path": "."
}
```

## Queue Commands

### Queue Management

#### Get Queue Status
```http
GET /api/v1/queue/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "queue_name": "default",
    "status": "running",
    "total_tasks": 150,
    "pending_tasks": 5,
    "running_tasks": 3,
    "completed_tasks": 140,
    "failed_tasks": 2,
    "workers": 4
  }
}
```

#### Push Task to Queue
```http
POST /api/v1/queue/tasks
```

**Request Body:**
```json
{
  "task_type": "ssl_cert_generate",
  "task_data": {
    "cert_type": "server",
    "common_name": "api.example.com",
    "key_size": 2048
  },
  "priority": "normal",
  "delay": 0
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "status": "queued",
    "estimated_completion": "2025-01-11T10:35:00Z"
  }
}
```

#### Get Task Status
```http
GET /api/v1/queue/tasks/{task_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "status": "completed",
    "result": {
      "certificate_path": "./certs/server.crt",
      "key_path": "./certs/server.key"
    },
    "started_at": "2025-01-11T10:30:00Z",
    "completed_at": "2025-01-11T10:32:00Z",
    "duration": 120
  }
}
```

### SSL Queue Operations

#### Setup Queue SSL
```http
POST /api/v1/queue/ssl/setup
```

**Request Body:**
```json
{
  "ssl_config": {
    "enabled": true,
    "cert_file": "./certs/queue.crt",
    "key_file": "./certs/queue.key",
    "ca_cert": "./certs/ca.crt"
  },
  "certificate_data": {
    "common_name": "queue.example.com",
    "key_size": 2048
  }
}
```

## System Commands

### System Monitoring

#### Get System Status
```http
GET /api/v1/system/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "system": {
      "hostname": "ai-admin-server",
      "uptime": "7 days, 12 hours",
      "load_average": [0.5, 0.8, 1.2],
      "cpu_usage": 25.5,
      "memory_usage": 60.2,
      "disk_usage": 45.8
    },
    "services": {
      "ai-admin": "running",
      "nginx": "running",
      "redis": "running"
    },
    "ssl_status": {
      "enabled": true,
      "certificates_valid": true,
      "mtls_enabled": true
    }
  }
}
```

#### Monitor System Resources
```http
POST /api/v1/system/monitor
```

**Request Body:**
```json
{
  "action": "cpu",
  "interval": 1,
  "duration": 60,
  "metrics": ["cpu_usage", "memory_usage", "disk_usage"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "monitoring": {
      "action": "cpu",
      "duration": 60,
      "interval": 1,
      "metrics": [
        {
          "timestamp": "2025-01-11T10:30:00Z",
          "cpu_usage": 25.5,
          "memory_usage": 60.2,
          "disk_usage": 45.8
        }
      ]
    }
  }
}
```

## Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "CERTIFICATE_VALIDATION_FAILED",
    "message": "Certificate validation failed",
    "details": {
      "certificate_path": "./certs/invalid.crt",
      "validation_errors": [
        "Certificate has expired",
        "Invalid certificate chain"
      ]
    },
    "timestamp": "2025-01-11T10:30:00Z",
    "request_id": "req_123456"
  }
}
```

### HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error

### Error Codes

#### SSL/Certificate Errors
- `CERTIFICATE_VALIDATION_FAILED`: Certificate validation error
- `CERTIFICATE_EXPIRED`: Certificate has expired
- `CERTIFICATE_REVOKED`: Certificate has been revoked
- `INVALID_CERTIFICATE_CHAIN`: Certificate chain validation failed
- `SSL_CONFIGURATION_ERROR`: SSL configuration error
- `MTLS_AUTHENTICATION_FAILED`: mTLS authentication failed

#### Permission Errors
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions
- `ROLE_VALIDATION_FAILED`: Role validation failed
- `ACCESS_DENIED`: Access denied to resource

#### System Errors
- `SYSTEM_ERROR`: General system error
- `CONFIGURATION_ERROR`: Configuration error
- `NETWORK_ERROR`: Network communication error
- `TIMEOUT_ERROR`: Operation timeout

## Response Formats

### Success Response

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully",
  "timestamp": "2025-01-11T10:30:00Z",
  "request_id": "req_123456"
}
```

### Paginated Response

```json
{
  "success": true,
  "data": {
    "items": [
      // Array of items
    ],
    "pagination": {
      "total_count": 100,
      "limit": 20,
      "offset": 0,
      "has_next": true,
      "has_previous": false
    }
  }
}
```

### Command Response

```json
{
  "success": true,
  "data": {
    "command": "ssl_cert_generate",
    "operation": "ssl:create",
    "result": {
      // Command-specific result data
    },
    "execution_time": 1.5,
    "timestamp": "2025-01-11T10:30:00Z"
  }
}
```

---

**For more information, see:**
- [SSL/mTLS Guide](ssl_mtls_guide.md)
- [Certificate Management Guide](certificate_management.md)
- [Role-based Access Guide](role_based_access.md)
- [Security Best Practices](security_best_practices.md)
- [Deployment Guide](deployment_guide.md)
