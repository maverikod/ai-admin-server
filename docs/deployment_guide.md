# Deployment Guide

**Author:** Vasiliy Zdanovskiy  
**Email:** vasilyvz@gmail.com  
**Version:** 1.0  
**Date:** January 11, 2025

## Table of Contents

1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [SSL/mTLS Setup](#sslmts-setup)
6. [Production Deployment](#production-deployment)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Scaling and High Availability](#scaling-and-high-availability)
9. [Backup and Recovery](#backup-and-recovery)
10. [Troubleshooting](#troubleshooting)

## Introduction

This guide provides comprehensive instructions for deploying the AI Admin server with SSL/mTLS support in various environments. It covers everything from basic installation to production deployment with high availability.

### Deployment Options

1. **Development Environment**: Single server setup for testing
2. **Staging Environment**: Production-like setup for validation
3. **Production Environment**: High-availability cluster deployment
4. **Container Deployment**: Docker and Kubernetes deployment
5. **Cloud Deployment**: AWS, Azure, GCP deployment options

## System Requirements

### Minimum Requirements

#### Hardware
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4 GB
- **Storage**: 20 GB SSD
- **Network**: 100 Mbps

#### Software
- **OS**: Ubuntu 20.04+ LTS, CentOS 8+, RHEL 8+
- **Python**: 3.8+
- **OpenSSL**: 1.1.1+
- **Docker**: 20.10+ (optional)

### Recommended Requirements

#### Hardware
- **CPU**: 4+ cores, 3.0+ GHz
- **RAM**: 8+ GB
- **Storage**: 100+ GB SSD
- **Network**: 1+ Gbps

#### Software
- **OS**: Ubuntu 22.04 LTS
- **Python**: 3.11+
- **OpenSSL**: 3.0+
- **Docker**: 24.0+
- **Kubernetes**: 1.25+ (for cluster deployment)

### Network Requirements

#### Ports
- **443/tcp**: HTTPS (required)
- **8443/tcp**: mTLS (optional)
- **22/tcp**: SSH (management)
- **80/tcp**: HTTP redirect (optional)

#### Firewall Rules
```bash
# Allow HTTPS
ufw allow 443/tcp

# Allow mTLS
ufw allow 8443/tcp

# Allow SSH
ufw allow 22/tcp

# Deny HTTP (redirect to HTTPS)
ufw deny 80/tcp
```

## Installation

### 1. System Preparation

#### Update System
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

#### Install Dependencies
```bash
# Ubuntu/Debian
sudo apt install -y python3 python3-pip python3-venv openssl curl wget git

# CentOS/RHEL
sudo yum install -y python3 python3-pip openssl curl wget git
```

### 2. Python Environment Setup

#### Create Virtual Environment
```bash
# Create project directory
mkdir -p /opt/ai-admin
cd /opt/ai-admin

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

#### Install Application
```bash
# Clone repository
git clone https://github.com/your-org/ai-admin.git .

# Install dependencies
pip install -r requirements.txt

# Install application
pip install -e .
```

### 3. Directory Structure Setup

```bash
# Create necessary directories
mkdir -p {certs,keys,logs,config,backup}

# Set proper permissions
chmod 755 certs keys logs config backup
chmod 700 keys  # Private keys directory
```

### 4. Service User Creation

```bash
# Create service user
sudo useradd -r -s /bin/false ai-admin

# Set ownership
sudo chown -R ai-admin:ai-admin /opt/ai-admin

# Set permissions
sudo chmod 755 /opt/ai-admin
sudo chmod 700 /opt/ai-admin/keys
```

## Configuration

### 1. Basic Configuration

#### Create Configuration File
```bash
# Copy example configuration
cp config/config_like_example.json config/config.json

# Edit configuration
nano config/config.json
```

#### Basic Configuration Template
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 443,
    "debug": false,
    "workers": 4
  },
  "ssl": {
    "enabled": true,
    "mode": "https_only",
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key",
    "min_tls_version": "TLSv1.2"
  },
  "logging": {
    "level": "INFO",
    "file": "./logs/ai-admin.log",
    "max_size": "100MB",
    "backup_count": 5
  }
}
```

### 2. SSL Configuration

#### HTTPS Only Mode
```json
{
  "ssl": {
    "enabled": true,
    "mode": "https_only",
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key",
    "min_tls_version": "TLSv1.2",
    "cipher_suites": [
      "TLS_AES_256_GCM_SHA384",
      "TLS_CHACHA20_POLY1305_SHA256"
    ]
  }
}
```

#### mTLS Mode
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

### 3. Role Configuration

#### Basic Role Setup
```json
{
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
        "certificate_oids": ["1.2.3.4.5.6.7.8.9.2"],
        "is_active": true
      }
    },
    "default_role": "guest",
    "admin_role": "admin"
  }
}
```

## SSL/mTLS Setup

### 1. Certificate Generation

#### Generate CA Certificate
```bash
# Generate CA private key
openssl genrsa -out keys/ca.key 4096

# Generate CA certificate
openssl req -new -x509 -days 3650 -key keys/ca.key -out certs/ca.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=AI Admin CA"
```

#### Generate Server Certificate
```bash
# Generate server private key
openssl genrsa -out keys/server.key 2048

# Generate server certificate request
openssl req -new -key keys/server.key -out server.csr \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=api.example.com"

# Generate server certificate
openssl x509 -req -days 365 -in server.csr -CA certs/ca.crt -CAkey keys/ca.key \
  -out certs/server.crt -extensions v3_req -extfile <(
    echo "[v3_req]"
    echo "keyUsage = keyEncipherment, dataEncipherment"
    echo "extendedKeyUsage = serverAuth"
    echo "subjectAltName = @alt_names"
    echo "[alt_names]"
    echo "DNS.1 = api.example.com"
    echo "DNS.2 = *.example.com"
  )
```

#### Generate Client Certificate
```bash
# Generate client private key
openssl genrsa -out keys/client.key 2048

# Generate client certificate request
openssl req -new -key keys/client.key -out client.csr \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=admin@example.com"

# Generate client certificate
openssl x509 -req -days 365 -in client.csr -CA certs/ca.crt -CAkey keys/ca.key \
  -out certs/client.crt -extensions v3_req -extfile <(
    echo "[v3_req]"
    echo "keyUsage = digitalSignature"
    echo "extendedKeyUsage = clientAuth"
  )
```

### 2. Certificate Validation

#### Test Certificate Chain
```bash
# Verify server certificate
openssl verify -CAfile certs/ca.crt certs/server.crt

# Verify client certificate
openssl verify -CAfile certs/ca.crt certs/client.crt
```

#### Test SSL Connection
```bash
# Test HTTPS connection
openssl s_client -connect localhost:443 -servername api.example.com

# Test mTLS connection
openssl s_client -connect localhost:8443 \
  -cert certs/client.crt -key keys/client.key -CAfile certs/ca.crt
```

### 3. Certificate Management

#### Automated Certificate Renewal
```bash
# Create renewal script
cat > scripts/renew_certificates.sh << 'EOF'
#!/bin/bash
# Certificate renewal script

CERT_DIR="/opt/ai-admin/certs"
KEY_DIR="/opt/ai-admin/keys"
LOG_FILE="/opt/ai-admin/logs/cert_renewal.log"

# Check certificate expiration
check_expiry() {
    local cert_file="$1"
    local days_left=$(openssl x509 -in "$cert_file" -noout -dates | \
        grep "notAfter" | cut -d= -f2 | xargs -I {} date -d {} +%s)
    local current_time=$(date +%s)
    local days_until_expiry=$(( (days_left - current_time) / 86400 ))
    echo $days_until_expiry
}

# Renew certificate if needed
renew_certificate() {
    local cert_file="$1"
    local key_file="$2"
    local days_until_expiry=$(check_expiry "$cert_file")
    
    if [ $days_until_expiry -lt 30 ]; then
        echo "$(date): Certificate $cert_file expires in $days_until_expiry days. Renewing..." >> "$LOG_FILE"
        # Add renewal logic here
    fi
}

# Check all certificates
renew_certificate "$CERT_DIR/server.crt" "$KEY_DIR/server.key"
renew_certificate "$CERT_DIR/client.crt" "$KEY_DIR/client.key"
EOF

chmod +x scripts/renew_certificates.sh
```

#### Certificate Monitoring
```bash
# Create monitoring script
cat > scripts/monitor_certificates.sh << 'EOF'
#!/bin/bash
# Certificate monitoring script

CERT_DIR="/opt/ai-admin/certs"
ALERT_EMAIL="admin@example.com"

check_certificate() {
    local cert_file="$1"
    local days_until_expiry=$(openssl x509 -in "$cert_file" -noout -dates | \
        grep "notAfter" | cut -d= -f2 | xargs -I {} date -d {} +%s)
    local current_time=$(date +%s)
    local days_until_expiry=$(( (days_until_expiry - current_time) / 86400 ))
    
    if [ $days_until_expiry -lt 7 ]; then
        echo "CRITICAL: Certificate $cert_file expires in $days_until_expiry days"
        # Send alert email
        echo "Certificate $cert_file expires in $days_until_expiry days" | \
            mail -s "Certificate Expiration Alert" "$ALERT_EMAIL"
    elif [ $days_until_expiry -lt 30 ]; then
        echo "WARNING: Certificate $cert_file expires in $days_until_expiry days"
    fi
}

# Check all certificates
for cert in "$CERT_DIR"/*.crt; do
    if [ -f "$cert" ]; then
        check_certificate "$cert"
    fi
done
EOF

chmod +x scripts/monitor_certificates.sh
```

## Production Deployment

### 1. System Service Setup

#### Create Systemd Service
```bash
# Create service file
sudo tee /etc/systemd/system/ai-admin.service << 'EOF'
[Unit]
Description=AI Admin Server
After=network.target

[Service]
Type=exec
User=ai-admin
Group=ai-admin
WorkingDirectory=/opt/ai-admin
Environment=PATH=/opt/ai-admin/venv/bin
ExecStart=/opt/ai-admin/venv/bin/python -m ai_admin.server
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-admin

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable ai-admin
sudo systemctl start ai-admin
```

#### Service Management
```bash
# Start service
sudo systemctl start ai-admin

# Stop service
sudo systemctl stop ai-admin

# Restart service
sudo systemctl restart ai-admin

# Check status
sudo systemctl status ai-admin

# View logs
sudo journalctl -u ai-admin -f
```

### 2. Load Balancer Configuration

#### Nginx Configuration
```nginx
# /etc/nginx/sites-available/ai-admin
upstream ai_admin_backend {
    server 127.0.0.1:8443;
    server 127.0.0.1:8444 backup;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;
    
    # SSL Configuration
    ssl_certificate /opt/ai-admin/certs/server.crt;
    ssl_certificate_key /opt/ai-admin/keys/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    
    # Proxy Configuration
    location / {
        proxy_pass https://ai_admin_backend;
        proxy_ssl_verify on;
        proxy_ssl_certificate /opt/ai-admin/certs/client.crt;
        proxy_ssl_certificate_key /opt/ai-admin/keys/client.key;
        proxy_ssl_trusted_certificate /opt/ai-admin/certs/ca.crt;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name api.example.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. Firewall Configuration

#### UFW Configuration
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Allow mTLS
sudo ufw allow 8443/tcp

# Deny HTTP
sudo ufw deny 80/tcp

# Check status
sudo ufw status
```

#### iptables Configuration
```bash
# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTPS
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow mTLS
iptables -A INPUT -p tcp --dport 8443 -j ACCEPT

# Drop all other traffic
iptables -A INPUT -j DROP

# Save rules
iptables-save > /etc/iptables/rules.v4
```

## Monitoring and Maintenance

### 1. Log Management

#### Log Rotation
```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/ai-admin << 'EOF'
/opt/ai-admin/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ai-admin ai-admin
    postrotate
        systemctl reload ai-admin
    endscript
}
EOF
```

#### Log Monitoring
```bash
# Create log monitoring script
cat > scripts/monitor_logs.sh << 'EOF'
#!/bin/bash
# Log monitoring script

LOG_DIR="/opt/ai-admin/logs"
ALERT_EMAIL="admin@example.com"

# Monitor error logs
monitor_errors() {
    local error_count=$(grep -c "ERROR" "$LOG_DIR/ai-admin.log" 2>/dev/null || echo 0)
    if [ $error_count -gt 10 ]; then
        echo "High error count detected: $error_count errors" | \
            mail -s "AI Admin Error Alert" "$ALERT_EMAIL"
    fi
}

# Monitor SSL errors
monitor_ssl_errors() {
    local ssl_error_count=$(grep -c "SSL\|TLS" "$LOG_DIR/ai-admin.log" 2>/dev/null || echo 0)
    if [ $ssl_error_count -gt 5 ]; then
        echo "SSL error count detected: $ssl_error_count errors" | \
            mail -s "AI Admin SSL Error Alert" "$ALERT_EMAIL"
    fi
}

# Run monitoring
monitor_errors
monitor_ssl_errors
EOF

chmod +x scripts/monitor_logs.sh
```

### 2. Health Checks

#### Health Check Script
```bash
# Create health check script
cat > scripts/health_check.sh << 'EOF'
#!/bin/bash
# Health check script

BASE_URL="https://localhost:443"
CLIENT_CERT="/opt/ai-admin/certs/client.crt"
CLIENT_KEY="/opt/ai-admin/keys/client.key"
CA_CERT="/opt/ai-admin/certs/ca.crt"

# Check HTTPS endpoint
check_https() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" \
        --cert "$CLIENT_CERT" --key "$CLIENT_KEY" --cacert "$CA_CERT" \
        "$BASE_URL/health")
    
    if [ "$response" = "200" ]; then
        echo "HTTPS health check: OK"
        return 0
    else
        echo "HTTPS health check: FAILED (HTTP $response)"
        return 1
    fi
}

# Check mTLS endpoint
check_mtls() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" \
        --cert "$CLIENT_CERT" --key "$CLIENT_KEY" --cacert "$CA_CERT" \
        "https://localhost:8443/health")
    
    if [ "$response" = "200" ]; then
        echo "mTLS health check: OK"
        return 0
    else
        echo "mTLS health check: FAILED (HTTP $response)"
        return 1
    fi
}

# Run health checks
check_https
check_mtls
EOF

chmod +x scripts/health_check.sh
```

### 3. Performance Monitoring

#### System Monitoring
```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Create performance monitoring script
cat > scripts/monitor_performance.sh << 'EOF'
#!/bin/bash
# Performance monitoring script

LOG_FILE="/opt/ai-admin/logs/performance.log"

# Monitor CPU usage
monitor_cpu() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo "$(date): CPU usage: ${cpu_usage}%" >> "$LOG_FILE"
    
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        echo "High CPU usage detected: ${cpu_usage}%"
    fi
}

# Monitor memory usage
monitor_memory() {
    local memory_usage=$(free | grep Mem | awk '{printf "%.2f", $3/$2 * 100.0}')
    echo "$(date): Memory usage: ${memory_usage}%" >> "$LOG_FILE"
    
    if (( $(echo "$memory_usage > 80" | bc -l) )); then
        echo "High memory usage detected: ${memory_usage}%"
    fi
}

# Monitor disk usage
monitor_disk() {
    local disk_usage=$(df /opt/ai-admin | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    echo "$(date): Disk usage: ${disk_usage}%" >> "$LOG_FILE"
    
    if [ $disk_usage -gt 80 ]; then
        echo "High disk usage detected: ${disk_usage}%"
    fi
}

# Run monitoring
monitor_cpu
monitor_memory
monitor_disk
EOF

chmod +x scripts/monitor_performance.sh
```

## Scaling and High Availability

### 1. Load Balancing

#### Multiple Instance Setup
```bash
# Create multiple instances
for i in {1..3}; do
    sudo cp /etc/systemd/system/ai-admin.service /etc/systemd/system/ai-admin-$i.service
    sudo sed -i "s/ai-admin/ai-admin-$i/g" /etc/systemd/system/ai-admin-$i.service
    sudo sed -i "s/port 443/port 844$i/g" /etc/systemd/system/ai-admin-$i.service
    sudo systemctl enable ai-admin-$i
    sudo systemctl start ai-admin-$i
done
```

#### HAProxy Configuration
```bash
# Install HAProxy
sudo apt install -y haproxy

# Configure HAProxy
sudo tee /etc/haproxy/haproxy.cfg << 'EOF'
global
    daemon
    user haproxy
    group haproxy

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend https_frontend
    bind *:443 ssl crt /opt/ai-admin/certs/server.pem
    redirect scheme https if !{ ssl_fc }
    default_backend ai_admin_backend

backend ai_admin_backend
    balance roundrobin
    option httpchk GET /health
    server ai-admin-1 127.0.0.1:8441 check
    server ai-admin-2 127.0.0.1:8442 check
    server ai-admin-3 127.0.0.1:8443 check
EOF

# Start HAProxy
sudo systemctl enable haproxy
sudo systemctl start haproxy
```

### 2. Database Clustering

#### Redis Cluster Setup
```bash
# Install Redis
sudo apt install -y redis-server

# Configure Redis cluster
sudo tee /etc/redis/redis.conf << 'EOF'
port 6379
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
appendonly yes
EOF

# Start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3. Container Deployment

#### Docker Setup
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 443 8443

CMD ["python", "-m", "ai_admin.server"]
```

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  ai-admin:
    build: .
    ports:
      - "443:443"
      - "8443:8443"
    volumes:
      - ./certs:/app/certs
      - ./keys:/app/keys
      - ./logs:/app/logs
    environment:
      - CONFIG_FILE=/app/config/config.json
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - ai-admin
    restart: unless-stopped
```

## Backup and Recovery

### 1. Backup Strategy

#### Configuration Backup
```bash
# Create backup script
cat > scripts/backup_config.sh << 'EOF'
#!/bin/bash
# Configuration backup script

BACKUP_DIR="/opt/ai-admin/backup/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup configuration files
cp -r /opt/ai-admin/config "$BACKUP_DIR/"

# Backup certificates
cp -r /opt/ai-admin/certs "$BACKUP_DIR/"

# Backup keys (encrypted)
tar -czf "$BACKUP_DIR/keys.tar.gz" /opt/ai-admin/keys
gpg --symmetric --cipher-algo AES256 "$BACKUP_DIR/keys.tar.gz"
rm "$BACKUP_DIR/keys.tar.gz"

# Backup logs
cp -r /opt/ai-admin/logs "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x scripts/backup_config.sh
```

#### Database Backup
```bash
# Create database backup script
cat > scripts/backup_database.sh << 'EOF'
#!/bin/bash
# Database backup script

BACKUP_DIR="/opt/ai-admin/backup/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup Redis data
redis-cli --rdb "$BACKUP_DIR/redis_backup.rdb"

# Backup certificate database
cp /opt/ai-admin/certificate_database.json "$BACKUP_DIR/"

echo "Database backup completed: $BACKUP_DIR"
EOF

chmod +x scripts/backup_database.sh
```

### 2. Recovery Procedures

#### Configuration Recovery
```bash
# Create recovery script
cat > scripts/recover_config.sh << 'EOF'
#!/bin/bash
# Configuration recovery script

BACKUP_DIR="$1"
if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

# Stop service
sudo systemctl stop ai-admin

# Restore configuration
cp -r "$BACKUP_DIR/config" /opt/ai-admin/

# Restore certificates
cp -r "$BACKUP_DIR/certs" /opt/ai-admin/

# Restore keys
gpg --decrypt "$BACKUP_DIR/keys.tar.gz.gpg" | tar -xzf - -C /

# Set permissions
sudo chown -R ai-admin:ai-admin /opt/ai-admin
sudo chmod 700 /opt/ai-admin/keys

# Start service
sudo systemctl start ai-admin

echo "Recovery completed"
EOF

chmod +x scripts/recover_config.sh
```

### 3. Disaster Recovery

#### Full System Recovery
```bash
# Create disaster recovery script
cat > scripts/disaster_recovery.sh << 'EOF'
#!/bin/bash
# Disaster recovery script

# Install system dependencies
sudo apt update && sudo apt install -y python3 python3-pip openssl

# Create service user
sudo useradd -r -s /bin/false ai-admin

# Restore from backup
./scripts/recover_config.sh /path/to/backup

# Verify installation
./scripts/health_check.sh

echo "Disaster recovery completed"
EOF

chmod +x scripts/disaster_recovery.sh
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status ai-admin

# Check logs
sudo journalctl -u ai-admin -f

# Check configuration
python -m ai_admin.server --check-config
```

#### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in certs/server.crt -text -noout

# Check certificate chain
openssl verify -CAfile certs/ca.crt certs/server.crt

# Test SSL connection
openssl s_client -connect localhost:443
```

#### Permission Issues
```bash
# Check file permissions
ls -la certs/ keys/

# Fix permissions
sudo chown -R ai-admin:ai-admin /opt/ai-admin
sudo chmod 700 keys/
sudo chmod 644 certs/*.crt
```

### Debug Commands

#### Configuration Validation
```bash
# Validate configuration
python -c "
from ai_admin.config.ssl_config import SSLConfig
from ai_admin.config.roles_config import RolesConfig
import json

with open('config/config.json') as f:
    config = json.load(f)

ssl_config = SSLConfig(config)
roles_config = RolesConfig(config)

print('SSL Config:', ssl_config.get_config_summary())
print('Roles Config:', roles_config.get_config_summary())
"
```

#### Certificate Testing
```bash
# Test certificate generation
python -c "
from ai_admin.commands.ssl_cert_generate_command import SSLCertGenerateCommand
import asyncio

async def test_cert():
    command = SSLCertGenerateCommand()
    result = await command.execute(
        cert_type='server',
        common_name='test.example.com',
        user_roles=['ssl:admin']
    )
    print('Certificate generation test:', result.data)

asyncio.run(test_cert())
"
```

### Log Analysis

#### Error Analysis
```bash
# Find errors in logs
grep -i error logs/ai-admin.log

# Find SSL errors
grep -i "ssl\|tls" logs/ai-admin.log

# Find authentication errors
grep -i "auth\|login" logs/ai-admin.log
```

#### Performance Analysis
```bash
# Analyze response times
grep "response_time" logs/ai-admin.log | awk '{print $NF}' | sort -n

# Find slow requests
grep "slow_request" logs/ai-admin.log
```

---

**For more information, see:**
- [SSL/mTLS Guide](ssl_mtls_guide.md)
- [Certificate Management Guide](certificate_management.md)
- [Role-based Access Guide](role_based_access.md)
- [Security Best Practices](security_best_practices.md)
- [API Reference](api_reference.md)
