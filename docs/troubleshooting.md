# Troubleshooting Guide

**Author:** Vasiliy Zdanovskiy  
**Email:** vasilyvz@gmail.com  
**Version:** 1.0  
**Date:** January 11, 2025

## Table of Contents

1. [Introduction](#introduction)
2. [Common Issues](#common-issues)
3. [SSL/mTLS Issues](#sslmts-issues)
4. [Certificate Issues](#certificate-issues)
5. [Authentication Issues](#authentication-issues)
6. [Performance Issues](#performance-issues)
7. [Network Issues](#network-issues)
8. [Configuration Issues](#configuration-issues)
9. [Debugging Tools](#debugging-tools)
10. [Log Analysis](#log-analysis)
11. [Emergency Procedures](#emergency-procedures)

## Introduction

This troubleshooting guide provides comprehensive solutions for common issues encountered when using the AI Admin server with SSL/mTLS support. It covers diagnosis, resolution, and prevention strategies for various problems.

### Troubleshooting Approach

1. **Identify the Problem**: Understand what's not working
2. **Gather Information**: Collect logs, error messages, and system state
3. **Diagnose the Root Cause**: Use debugging tools and analysis
4. **Apply Solution**: Implement the appropriate fix
5. **Verify Resolution**: Confirm the problem is resolved
6. **Document**: Record the solution for future reference

## Common Issues

### Service Won't Start

#### Problem
The AI Admin service fails to start or crashes immediately after startup.

#### Symptoms
- Service status shows "failed" or "inactive"
- Error messages in system logs
- Port not listening

#### Diagnosis
```bash
# Check service status
sudo systemctl status ai-admin

# Check service logs
sudo journalctl -u ai-admin -f

# Check configuration
python -m ai_admin.server --check-config
```

#### Common Causes and Solutions

**1. Configuration File Issues**
```bash
# Validate configuration
python -c "
from ai_admin.config.ssl_config import SSLConfig
import json

try:
    with open('config/config.json') as f:
        config = json.load(f)
    ssl_config = SSLConfig(config)
    print('Configuration is valid')
except Exception as e:
    print(f'Configuration error: {e}')
"
```

**2. Missing Dependencies**
```bash
# Check Python dependencies
pip list | grep -E "(fastapi|uvicorn|cryptography)"

# Install missing dependencies
pip install -r requirements.txt
```

**3. Port Already in Use**
```bash
# Check port usage
sudo netstat -tlnp | grep :443
sudo lsof -i :443

# Kill process using port
sudo kill -9 <PID>
```

**4. Permission Issues**
```bash
# Check file permissions
ls -la certs/ keys/ config/

# Fix permissions
sudo chown -R ai-admin:ai-admin /opt/ai-admin
sudo chmod 700 keys/
sudo chmod 644 certs/*.crt
```

### API Endpoints Not Responding

#### Problem
API endpoints return errors or don't respond to requests.

#### Symptoms
- HTTP 500 errors
- Connection timeouts
- Empty responses

#### Diagnosis
```bash
# Test basic connectivity
curl -k https://localhost:443/health

# Test with verbose output
curl -v -k https://localhost:443/api/v1/info

# Check server logs
tail -f logs/ai-admin.log
```

#### Solutions

**1. Check SSL Configuration**
```bash
# Verify SSL certificates
openssl x509 -in certs/server.crt -text -noout

# Test SSL connection
openssl s_client -connect localhost:443 -servername api.example.com
```

**2. Check Middleware Configuration**
```bash
# Verify middleware is loaded
grep -i "middleware" logs/ai-admin.log

# Check CORS configuration
curl -H "Origin: https://example.com" -v https://localhost:443/api/v1/info
```

**3. Check Command Registration**
```bash
# Verify commands are registered
python -c "
from ai_admin.commands import command_registry
print('Registered commands:', list(command_registry.keys()))
"
```

## SSL/mTLS Issues

### SSL Handshake Failures

#### Problem
SSL handshake fails during connection establishment.

#### Symptoms
- "SSL handshake failed" errors
- Connection refused on SSL ports
- Certificate validation errors

#### Diagnosis
```bash
# Test SSL handshake
openssl s_client -connect localhost:443 -debug

# Check certificate chain
openssl verify -CAfile certs/ca.crt certs/server.crt

# Check SSL configuration
python -c "
from ai_admin.config.ssl_config import SSLConfig
import json

with open('config/config.json') as f:
    config = json.load(f)
ssl_config = SSLConfig(config)
print('SSL Config:', ssl_config.get_config_summary())
"
```

#### Solutions

**1. Certificate Issues**
```bash
# Regenerate certificates
python -m ai_admin.commands.ssl_cert_generate \
  --cert-type server \
  --common-name api.example.com \
  --key-size 2048 \
  --days-valid 365

# Verify certificate
openssl x509 -in certs/server.crt -text -noout
```

**2. SSL Configuration Issues**
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

**3. Port Configuration**
```bash
# Check if SSL port is listening
sudo netstat -tlnp | grep :443

# Check firewall rules
sudo ufw status
sudo iptables -L
```

### mTLS Authentication Failures

#### Problem
mTLS authentication fails for client connections.

#### Symptoms
- "Client certificate required" errors
- "Certificate validation failed" errors
- "Access denied" errors

#### Diagnosis
```bash
# Test mTLS connection
openssl s_client -connect localhost:8443 \
  -cert certs/client.crt -key keys/client.key -CAfile certs/ca.crt

# Check client certificate
openssl x509 -in certs/client.crt -text -noout

# Verify certificate roles
python -c "
from ai_admin.commands.ssl_cert_verify import SSLCertVerifyCommand
import asyncio

async def test_cert():
    command = SSLCertVerifyCommand()
    result = await command.execute(
        cert_path='certs/client.crt',
        ca_cert_path='certs/ca.crt',
        check_roles=True
    )
    print('Certificate verification:', result.data)

asyncio.run(test_cert())
"
```

#### Solutions

**1. Client Certificate Issues**
```bash
# Generate new client certificate
python -m ai_admin.commands.ssl_cert_generate \
  --cert-type client \
  --common-name user@example.com \
  --roles admin,ssl:manage \
  --ca-cert-path certs/ca.crt \
  --ca-key-path keys/ca.key

# Verify client certificate
openssl verify -CAfile certs/ca.crt certs/client.crt
```

**2. Role Configuration Issues**
```json
{
  "ssl": {
    "mtls": {
      "verify_client": true,
      "require_client_cert": true,
      "role_extraction": {
        "enabled": true,
        "oid": "1.2.3.4.5.6.7.8.9",
        "required_roles": ["admin"]
      }
    }
  }
}
```

**3. Certificate Chain Issues**
```bash
# Verify certificate chain
openssl verify -CAfile certs/ca.crt -untrusted certs/intermediate.crt certs/client.crt

# Check certificate chain in server
openssl s_client -connect localhost:8443 -showcerts
```

## Certificate Issues

### Certificate Expiration

#### Problem
Certificates have expired or are about to expire.

#### Symptoms
- "Certificate expired" errors
- SSL handshake failures
- Security warnings

#### Diagnosis
```bash
# Check certificate expiration
openssl x509 -in certs/server.crt -dates -noout

# Check all certificates
for cert in certs/*.crt; do
    echo "=== $cert ==="
    openssl x509 -in "$cert" -dates -noout
done

# Automated expiration check
python -c "
from ai_admin.commands.ssl_cert_verify import SSLCertVerifyCommand
import asyncio

async def check_expiry():
    command = SSLCertVerifyCommand()
    result = await command.execute(
        cert_path='certs/server.crt',
        check_expiry=True
    )
    print('Expiry check:', result.data)

asyncio.run(check_expiry())
"
```

#### Solutions

**1. Renew Expired Certificates**
```bash
# Generate new certificate
python -m ai_admin.commands.ssl_cert_generate \
  --cert-type server \
  --common-name api.example.com \
  --key-size 2048 \
  --days-valid 365 \
  --ca-cert-path certs/ca.crt \
  --ca-key-path keys/ca.key

# Backup old certificate
mv certs/server.crt certs/server.crt.backup
mv keys/server.key keys/server.key.backup

# Install new certificate
cp new_certs/server.crt certs/
cp new_keys/server.key keys/

# Restart service
sudo systemctl restart ai-admin
```

**2. Set Up Automated Renewal**
```bash
# Create renewal script
cat > scripts/auto_renew_certificates.sh << 'EOF'
#!/bin/bash
# Automated certificate renewal

CERT_DIR="/opt/ai-admin/certs"
KEY_DIR="/opt/ai-admin/keys"
LOG_FILE="/opt/ai-admin/logs/cert_renewal.log"

check_and_renew() {
    local cert_file="$1"
    local days_until_expiry=$(openssl x509 -in "$cert_file" -noout -dates | \
        grep "notAfter" | cut -d= -f2 | xargs -I {} date -d {} +%s)
    local current_time=$(date +%s)
    local days_until_expiry=$(( (days_until_expiry - current_time) / 86400 ))
    
    if [ $days_until_expiry -lt 30 ]; then
        echo "$(date): Certificate $cert_file expires in $days_until_expiry days. Renewing..." >> "$LOG_FILE"
        # Add renewal logic here
        python -m ai_admin.commands.ssl_cert_generate \
          --cert-type server \
          --common-name api.example.com \
          --key-size 2048 \
          --days-valid 365
        sudo systemctl restart ai-admin
    fi
}

check_and_renew "$CERT_DIR/server.crt"
EOF

chmod +x scripts/auto_renew_certificates.sh

# Add to crontab
echo "0 2 * * * /opt/ai-admin/scripts/auto_renew_certificates.sh" | crontab -
```

### Certificate Validation Failures

#### Problem
Certificate validation fails during verification.

#### Symptoms
- "Certificate validation failed" errors
- "Invalid certificate chain" errors
- "Certificate not trusted" errors

#### Diagnosis
```bash
# Verify certificate chain
openssl verify -CAfile certs/ca.crt certs/server.crt

# Check certificate details
openssl x509 -in certs/server.crt -text -noout

# Test certificate validation
python -c "
from ai_admin.commands.ssl_cert_verify import SSLCertVerifyCommand
import asyncio

async def validate_cert():
    command = SSLCertVerifyCommand()
    result = await command.execute(
        cert_path='certs/server.crt',
        ca_cert_path='certs/ca.crt',
        verify_chain=True,
        check_expiry=True
    )
    print('Validation result:', result.data)

asyncio.run(validate_cert())
"
```

#### Solutions

**1. Fix Certificate Chain**
```bash
# Verify CA certificate
openssl x509 -in certs/ca.crt -text -noout

# Check intermediate certificates
openssl verify -CAfile certs/ca.crt -untrusted certs/intermediate.crt certs/server.crt

# Recreate certificate with proper chain
python -m ai_admin.commands.ssl_cert_generate \
  --cert-type server \
  --common-name api.example.com \
  --ca-cert-path certs/ca.crt \
  --ca-key-path keys/ca.key \
  --intermediate-cert-path certs/intermediate.crt
```

**2. Update Trust Store**
```bash
# Add CA to system trust store
sudo cp certs/ca.crt /usr/local/share/ca-certificates/ai-admin-ca.crt
sudo update-ca-certificates

# Verify trust store
openssl verify -CApath /etc/ssl/certs certs/server.crt
```

## Authentication Issues

### Role-based Access Control Failures

#### Problem
Users are denied access despite having valid certificates.

#### Symptoms
- "Access denied" errors
- "Insufficient permissions" errors
- "Role validation failed" errors

#### Diagnosis
```bash
# Check role configuration
python -c "
from ai_admin.config.roles_config import RolesConfig
import json

with open('config/config.json') as f:
    config = json.load(f)
roles_config = RolesConfig(config)
print('Roles Config:', roles_config.get_config_summary())
"

# Check user roles
python -c "
from ai_admin.commands.mtls_roles import MtlsRolesCommand
import asyncio

async def check_roles():
    command = MtlsRolesCommand()
    result = await command.execute(
        action='list_roles'
    )
    print('Available roles:', result.data)

asyncio.run(check_roles())
"
```

#### Solutions

**1. Fix Role Configuration**
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
      }
    }
  }
}
```

**2. Update Certificate Roles**
```bash
# Generate certificate with correct roles
python -m ai_admin.commands.ssl_cert_generate \
  --cert-type client \
  --common-name admin@example.com \
  --roles admin,ssl:manage \
  --ca-cert-path certs/ca.crt \
  --ca-key-path keys/ca.key

# Verify certificate roles
python -c "
from ai_admin.commands.ssl_cert_verify import SSLCertVerifyCommand
import asyncio

async def verify_roles():
    command = SSLCertVerifyCommand()
    result = await command.execute(
        cert_path='certs/client.crt',
        check_roles=True,
        required_roles=['admin']
    )
    print('Role verification:', result.data)

asyncio.run(verify_roles())
"
```

### Token Authentication Issues

#### Problem
Token-based authentication fails.

#### Symptoms
- "Invalid token" errors
- "Token expired" errors
- "Authentication failed" errors

#### Diagnosis
```bash
# Check token configuration
grep -i "token" config/config.json

# Test token authentication
curl -H "Authorization: Bearer <token>" https://localhost:443/api/v1/info

# Check token validation
python -c "
from ai_admin.core.token_auth_manager import TokenAuthManager
import asyncio

async def test_token():
    manager = TokenAuthManager()
    result = await manager.validate_token('<token>')
    print('Token validation:', result)

asyncio.run(test_token())
"
```

#### Solutions

**1. Generate New Token**
```bash
# Generate new token
python -c "
from ai_admin.core.token_auth_manager import TokenAuthManager
import asyncio

async def generate_token():
    manager = TokenAuthManager()
    token = await manager.generate_token(
        user_id='admin',
        roles=['admin'],
        expires_in=3600
    )
    print('New token:', token)

asyncio.run(generate_token())
"
```

**2. Update Token Configuration**
```json
{
  "token": {
    "enabled": true,
    "secret_key": "your-secret-key",
    "algorithm": "HS256",
    "expires_in": 3600,
    "refresh_expires_in": 86400
  }
}
```

## Performance Issues

### High CPU Usage

#### Problem
Server consumes excessive CPU resources.

#### Symptoms
- High CPU usage (>80%)
- Slow response times
- System becomes unresponsive

#### Diagnosis
```bash
# Check CPU usage
top -p $(pgrep -f ai-admin)

# Check system resources
python -c "
from ai_admin.commands.system_monitor import SystemMonitorCommand
import asyncio

async def check_cpu():
    command = SystemMonitorCommand()
    result = await command.execute(action='cpu', duration=60)
    print('CPU usage:', result.data)

asyncio.run(check_cpu())
"

# Check for resource leaks
ps aux | grep ai-admin
```

#### Solutions

**1. Optimize Configuration**
```json
{
  "server": {
    "workers": 2,
    "worker_class": "uvicorn.workers.UvicornWorker",
    "worker_connections": 1000,
    "max_requests": 1000,
    "max_requests_jitter": 100
  }
}
```

**2. Enable Caching**
```json
{
  "cache": {
    "enabled": true,
    "backend": "redis",
    "ttl": 300,
    "max_size": 1000
  }
}
```

**3. Optimize SSL Configuration**
```json
{
  "ssl": {
    "session_cache_size": 1000,
    "session_timeout": 300,
    "enable_session_resumption": true
  }
}
```

### Memory Issues

#### Problem
Server consumes excessive memory or has memory leaks.

#### Symptoms
- High memory usage (>80%)
- Out of memory errors
- System swapping

#### Diagnosis
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Check for memory leaks
python -c "
import gc
import sys
print('Memory usage:', sys.getsizeof(gc.get_objects()))

# Check memory monitoring
from ai_admin.commands.system_monitor import SystemMonitorCommand
import asyncio

async def check_memory():
    command = SystemMonitorCommand()
    result = await command.execute(action='memory', duration=60)
    print('Memory usage:', result.data)

asyncio.run(check_memory())
"
```

#### Solutions

**1. Optimize Memory Usage**
```json
{
  "server": {
    "max_requests": 1000,
    "max_requests_jitter": 100,
    "preload_app": true,
    "worker_tmp_dir": "/dev/shm"
  }
}
```

**2. Enable Memory Monitoring**
```bash
# Create memory monitoring script
cat > scripts/monitor_memory.sh << 'EOF'
#!/bin/bash
# Memory monitoring script

LOG_FILE="/opt/ai-admin/logs/memory.log"
THRESHOLD=80

check_memory() {
    local memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    echo "$(date): Memory usage: ${memory_usage}%" >> "$LOG_FILE"
    
    if [ $memory_usage -gt $THRESHOLD ]; then
        echo "High memory usage detected: ${memory_usage}%"
        # Restart service if memory usage is too high
        if [ $memory_usage -gt 90 ]; then
            sudo systemctl restart ai-admin
        fi
    fi
}

check_memory
EOF

chmod +x scripts/monitor_memory.sh

# Add to crontab
echo "*/5 * * * * /opt/ai-admin/scripts/monitor_memory.sh" | crontab -
```

## Network Issues

### Connection Timeouts

#### Problem
Network connections timeout or fail to establish.

#### Symptoms
- Connection timeout errors
- Slow response times
- Intermittent connectivity

#### Diagnosis
```bash
# Test network connectivity
ping -c 4 api.example.com
telnet api.example.com 443

# Check network statistics
netstat -i
ss -tuln

# Test SSL connection
openssl s_client -connect api.example.com:443 -timeout 10
```

#### Solutions

**1. Optimize Network Configuration**
```json
{
  "server": {
    "timeout": 30,
    "keepalive": 2,
    "keepalive_timeout": 5,
    "client_max_body_size": "10m"
  }
}
```

**2. Configure Load Balancing**
```nginx
# Nginx configuration
upstream ai_admin_backend {
    server 127.0.0.1:8443 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8444 backup;
}

server {
    listen 443 ssl;
    server_name api.example.com;
    
    location / {
        proxy_pass https://ai_admin_backend;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
```

### Firewall Issues

#### Problem
Firewall blocks legitimate connections.

#### Symptoms
- Connection refused errors
- Port not accessible
- Intermittent connectivity

#### Diagnosis
```bash
# Check firewall status
sudo ufw status
sudo iptables -L

# Test port accessibility
nmap -p 443,8443 api.example.com

# Check if port is listening
sudo netstat -tlnp | grep :443
```

#### Solutions

**1. Configure Firewall Rules**
```bash
# Allow HTTPS
sudo ufw allow 443/tcp

# Allow mTLS
sudo ufw allow 8443/tcp

# Allow SSH
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

**2. Configure iptables**
```bash
# Allow HTTPS
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow mTLS
iptables -A INPUT -p tcp --dport 8443 -j ACCEPT

# Save rules
iptables-save > /etc/iptables/rules.v4
```

## Configuration Issues

### Invalid Configuration

#### Problem
Server fails to start due to configuration errors.

#### Symptoms
- Configuration validation errors
- Service startup failures
- Unexpected behavior

#### Diagnosis
```bash
# Validate configuration
python -c "
from ai_admin.config.ssl_config import SSLConfig
from ai_admin.config.roles_config import RolesConfig
import json

try:
    with open('config/config.json') as f:
        config = json.load(f)
    
    ssl_config = SSLConfig(config)
    roles_config = RolesConfig(config)
    
    print('SSL Config valid:', ssl_config.is_configuration_valid())
    print('Roles Config valid:', roles_config.validate_roles_config())
    
except Exception as e:
    print(f'Configuration error: {e}')
"

# Check configuration syntax
python -m json.tool config/config.json
```

#### Solutions

**1. Fix Configuration Syntax**
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 443,
    "debug": false
  },
  "ssl": {
    "enabled": true,
    "mode": "https_only",
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key"
  }
}
```

**2. Validate Configuration**
```bash
# Create configuration validator
cat > scripts/validate_config.py << 'EOF'
#!/usr/bin/env python3
import json
import sys
from ai_admin.config.ssl_config import SSLConfig
from ai_admin.config.roles_config import RolesConfig

def validate_config(config_file):
    try:
        with open(config_file) as f:
            config = json.load(f)
        
        ssl_config = SSLConfig(config)
        roles_config = RolesConfig(config)
        
        ssl_valid = ssl_config.is_configuration_valid()
        roles_valid = roles_config.validate_roles_config()
        
        if ssl_valid and roles_valid:
            print("Configuration is valid")
            return True
        else:
            print("Configuration validation failed")
            return False
            
    except Exception as e:
        print(f"Configuration error: {e}")
        return False

if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config/config.json"
    success = validate_config(config_file)
    sys.exit(0 if success else 1)
EOF

chmod +x scripts/validate_config.py

# Run validation
python scripts/validate_config.py
```

## Debugging Tools

### SSL Debugging

#### OpenSSL Commands
```bash
# Test SSL connection
openssl s_client -connect localhost:443 -debug

# Check certificate details
openssl x509 -in certs/server.crt -text -noout

# Verify certificate chain
openssl verify -CAfile certs/ca.crt certs/server.crt

# Test mTLS connection
openssl s_client -connect localhost:8443 \
  -cert certs/client.crt -key keys/client.key -CAfile certs/ca.crt
```

#### Python SSL Testing
```python
# SSL connection test
import ssl
import socket

def test_ssl_connection(host, port, cert_file=None, key_file=None):
    context = ssl.create_default_context()
    
    if cert_file and key_file:
        context.load_cert_chain(cert_file, key_file)
    
    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            print(f"SSL connection successful to {host}:{port}")
            print(f"Protocol: {ssock.version()}")
            print(f"Cipher: {ssock.cipher()}")
            print(f"Certificate: {ssock.getpeercert()}")

# Test connection
test_ssl_connection('localhost', 443)
test_ssl_connection('localhost', 8443, 'certs/client.crt', 'keys/client.key')
```

### Certificate Analysis

#### Certificate Information
```bash
# Get certificate information
openssl x509 -in certs/server.crt -text -noout

# Check certificate expiration
openssl x509 -in certs/server.crt -dates -noout

# Verify certificate signature
openssl x509 -in certs/server.crt -verify -CAfile certs/ca.crt

# Check certificate extensions
openssl x509 -in certs/server.crt -extensions -noout
```

#### Certificate Chain Analysis
```bash
# Verify certificate chain
openssl verify -CAfile certs/ca.crt -untrusted certs/intermediate.crt certs/server.crt

# Check certificate chain in server
openssl s_client -connect localhost:443 -showcerts

# Analyze certificate chain
openssl crl2pkcs7 -nocrl -certfile certs/server.crt -certfile certs/intermediate.crt -certfile certs/ca.crt | openssl pkcs7 -print_certs -text -noout
```

### Network Debugging

#### Network Connectivity
```bash
# Test basic connectivity
ping -c 4 api.example.com

# Test port connectivity
telnet api.example.com 443
nc -zv api.example.com 443

# Check DNS resolution
nslookup api.example.com
dig api.example.com
```

#### Network Analysis
```bash
# Check network interfaces
ip addr show
ifconfig

# Check routing table
ip route show
route -n

# Check network statistics
netstat -i
ss -tuln
```

## Log Analysis

### Log Locations

#### System Logs
```bash
# Service logs
sudo journalctl -u ai-admin -f

# Application logs
tail -f logs/ai-admin.log

# SSL logs
tail -f logs/ssl.log

# Security logs
tail -f logs/security.log
```

#### Log Analysis Commands
```bash
# Find errors
grep -i error logs/ai-admin.log

# Find SSL errors
grep -i "ssl\|tls" logs/ai-admin.log

# Find authentication errors
grep -i "auth\|login" logs/ai-admin.log

# Find certificate errors
grep -i "certificate\|cert" logs/ai-admin.log

# Count error types
grep -i error logs/ai-admin.log | cut -d: -f4 | sort | uniq -c
```

### Log Monitoring

#### Real-time Monitoring
```bash
# Monitor all logs
tail -f logs/*.log

# Monitor specific log types
tail -f logs/ai-admin.log | grep -i error
tail -f logs/ssl.log | grep -i "handshake\|certificate"

# Monitor with timestamps
tail -f logs/ai-admin.log | while read line; do
    echo "$(date): $line"
done
```

#### Log Analysis Scripts
```bash
# Create log analysis script
cat > scripts/analyze_logs.sh << 'EOF'
#!/bin/bash
# Log analysis script

LOG_DIR="/opt/ai-admin/logs"
REPORT_FILE="/opt/ai-admin/logs/analysis_report.txt"

echo "=== Log Analysis Report ===" > "$REPORT_FILE"
echo "Generated: $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Error analysis
echo "=== Error Analysis ===" >> "$REPORT_FILE"
grep -i error "$LOG_DIR/ai-admin.log" | wc -l >> "$REPORT_FILE"
echo "Total errors found" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# SSL error analysis
echo "=== SSL Error Analysis ===" >> "$REPORT_FILE"
grep -i "ssl\|tls" "$LOG_DIR/ai-admin.log" | grep -i error | wc -l >> "$REPORT_FILE"
echo "SSL errors found" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Certificate error analysis
echo "=== Certificate Error Analysis ===" >> "$REPORT_FILE"
grep -i "certificate\|cert" "$LOG_DIR/ai-admin.log" | grep -i error | wc -l >> "$REPORT_FILE"
echo "Certificate errors found" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Top error messages
echo "=== Top Error Messages ===" >> "$REPORT_FILE"
grep -i error "$LOG_DIR/ai-admin.log" | cut -d: -f4- | sort | uniq -c | sort -nr | head -10 >> "$REPORT_FILE"

echo "Log analysis complete. Report saved to: $REPORT_FILE"
EOF

chmod +x scripts/analyze_logs.sh

# Run analysis
./scripts/analyze_logs.sh
```

## Emergency Procedures

### Service Recovery

#### Quick Recovery
```bash
# Stop service
sudo systemctl stop ai-admin

# Check configuration
python scripts/validate_config.py

# Fix common issues
sudo chown -R ai-admin:ai-admin /opt/ai-admin
sudo chmod 700 keys/
sudo chmod 644 certs/*.crt

# Start service
sudo systemctl start ai-admin

# Check status
sudo systemctl status ai-admin
```

#### Full Recovery
```bash
# Stop all services
sudo systemctl stop ai-admin nginx

# Backup current state
cp -r /opt/ai-admin /opt/ai-admin.backup.$(date +%Y%m%d_%H%M%S)

# Restore from backup
cp -r /opt/ai-admin.backup.20250111_100000/* /opt/ai-admin/

# Fix permissions
sudo chown -R ai-admin:ai-admin /opt/ai-admin
sudo chmod 700 keys/
sudo chmod 644 certs/*.crt

# Start services
sudo systemctl start ai-admin nginx

# Verify recovery
curl -k https://localhost:443/health
```

### Certificate Emergency

#### Certificate Recovery
```bash
# Stop service
sudo systemctl stop ai-admin

# Backup current certificates
cp -r certs/ certs.backup.$(date +%Y%m%d_%H%M%S)/
cp -r keys/ keys.backup.$(date +%Y%m%d_%H%M%S)/

# Generate emergency certificates
python -m ai_admin.commands.ssl_cert_generate \
  --cert-type server \
  --common-name localhost \
  --key-size 2048 \
  --days-valid 30

# Start service
sudo systemctl start ai-admin

# Test connection
curl -k https://localhost:443/health
```

### Data Recovery

#### Configuration Recovery
```bash
# Stop service
sudo systemctl stop ai-admin

# Restore configuration from backup
cp /opt/ai-admin/backup/20250111/config/* /opt/ai-admin/config/

# Restore certificates from backup
cp /opt/ai-admin/backup/20250111/certs/* /opt/ai-admin/certs/

# Restore keys from backup (decrypt if encrypted)
gpg --decrypt /opt/ai-admin/backup/20250111/keys.tar.gz.gpg | tar -xzf - -C /

# Fix permissions
sudo chown -R ai-admin:ai-admin /opt/ai-admin
sudo chmod 700 keys/
sudo chmod 644 certs/*.crt

# Start service
sudo systemctl start ai-admin
```

---

**For more information, see:**
- [SSL/mTLS Guide](ssl_mtls_guide.md)
- [Certificate Management Guide](certificate_management.md)
- [Role-based Access Guide](role_based_access.md)
- [Security Best Practices](security_best_practices.md)
- [Deployment Guide](deployment_guide.md)
- [API Reference](api_reference.md)
