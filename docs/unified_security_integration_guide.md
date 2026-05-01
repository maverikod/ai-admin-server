# Unified Security Integration Guide

**Author:** Vasiliy Zdanovskiy  
**Email:** vasilyvz@gmail.com  
**Version:** 1.0.0  
**Date:** 2024-01-01

## Overview

This guide describes the unified security integration approach implemented in the AI Admin system. The unified approach ensures consistent security implementation across all commands and components.

## Architecture

### Core Components

1. **BaseSecurityAdapter** - Base class for all security adapters
2. **CommandSecurityMixin** - Mixin for adding security to commands
3. **RolesManager** - Unified roles management
4. **SecurityMonitor** - Unified security monitoring
5. **SecurityMetrics** - Unified security metrics
6. **UnifiedSecurityIntegration** - Central integration point

### Security Flow

```
Command → CommandSecurityMixin → SecurityAdapter → RolesManager → SecurityMonitor → SecurityMetrics
```

## Implementation Guide

### 1. Command Integration

All commands should inherit from both `Command` and `CommandSecurityMixin`:

```python
from mcp_proxy_adapter.commands.base import Command
from ai_admin.security.command_security_mixin import CommandSecurityMixin

class MyCommand(Command, CommandSecurityMixin):
    """My command with unified security."""
    
    name = "my_command"
    
    def __init__(self):
        super().__init__()
        CommandSecurityMixin.__init__(self)
    
    async def execute(self, **kwargs):
        """Execute command with security validation."""
        try:
            # 1. Validate security
            is_valid, error_msg = await self._validate_security("my_operation", kwargs)
            if not is_valid:
                return ErrorResult(message=error_msg, code="SECURITY_ERROR")
            
            # 2. Execute command logic
            result = await self._execute_command_logic(**kwargs)
            
            # 3. Audit operation
            await self._audit_operation("my_operation", kwargs, result)
            
            return SuccessResult(data=result)
            
        except SecurityError as e:
            return ErrorResult(message=str(e), code=e.code)
```

### 2. Security Adapter Implementation

Security adapters should inherit from `BaseSecurityAdapter`:

```python
from ai_admin.security.base_security_adapter import SecurityAdapter

class MySecurityAdapter(SecurityAdapter):
    """Security adapter for my component."""
    
    async def validate_operation(self, operation: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate operation based on roles and permissions."""
        # Implementation here
        pass
    
    async def check_permissions(self, user_roles: List[str], operation: str) -> Tuple[bool, List[str]]:
        """Check if user has permissions for operation."""
        # Implementation here
        pass
    
    async def audit_operation(self, operation: str, params: Dict[str, Any], result: Any) -> None:
        """Audit operation for security monitoring."""
        # Implementation here
        pass
```

### 3. Configuration

Security configuration is managed through `config/unified_security_config.json`:

```json
{
  "security": {
    "enabled": true,
    "framework": "mcp-security-framework",
    "adapters": {
      "my_component": {
        "enabled": true,
        "roles": ["my_admin", "my_user", "my_readonly"],
        "permissions": {
          "my_admin": ["my:*"],
          "my_user": ["my:read", "my:write"],
          "my_readonly": ["my:read"]
        }
      }
    }
  }
}
```

## Security Features

### 1. Role-Based Access Control (RBAC)

- Hierarchical role system
- Component-specific roles
- Permission inheritance
- Dynamic role assignment

### 2. Operation Validation

- Pre-execution validation
- Parameter validation
- Permission checking
- Resource access control

### 3. Security Monitoring

- Real-time event monitoring
- Anomaly detection
- Alert generation
- Event correlation

### 4. Security Metrics

- Operation counts
- Success/failure rates
- Performance metrics
- User activity tracking

### 5. Audit Logging

- Operation auditing
- Security event logging
- Compliance reporting
- Data retention

## Best Practices

### 1. Command Implementation

- Always inherit from `CommandSecurityMixin`
- Validate security before execution
- Audit operations after execution
- Handle security errors gracefully

### 2. Security Adapter Implementation

- Implement all abstract methods
- Use consistent error handling
- Log security events
- Follow naming conventions

### 3. Configuration Management

- Use centralized configuration
- Validate configuration on startup
- Support configuration reloading
- Document all settings

### 4. Error Handling

- Use specific error codes
- Provide meaningful error messages
- Log security violations
- Implement proper fallbacks

## Examples

### Basic Command with Security

```python
class DockerListCommand(Command, CommandSecurityMixin):
    """List Docker containers with security."""
    
    name = "docker_list"
    
    def __init__(self):
        super().__init__()
        CommandSecurityMixin.__init__(self)
    
    async def execute(self, user_roles: Optional[List[str]] = None, **kwargs):
        """List Docker containers."""
        try:
            # Validate security
            is_valid, error_msg = await self._validate_security("docker:list", kwargs)
            if not is_valid:
                return ErrorResult(message=error_msg, code="SECURITY_ERROR")
            
            # Execute Docker list
            result = await self._execute_docker_list(**kwargs)
            
            # Audit operation
            await self._audit_operation("docker:list", kwargs, result)
            
            return SuccessResult(data=result)
            
        except SecurityError as e:
            return ErrorResult(message=str(e), code=e.code)
```

### Advanced Security Adapter

```python
class DockerSecurityAdapter(SecurityAdapter):
    """Docker security adapter."""
    
    async def validate_operation(self, operation: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Docker operation."""
        try:
            # Get user roles
            user_roles = await self.get_user_roles(params)
            
            # Check permissions
            has_permission, missing = await self.check_permissions(user_roles, operation)
            
            if not has_permission:
                return False, f"Missing permissions: {missing}"
            
            # Additional Docker-specific validation
            if operation.startswith("docker:run"):
                return await self._validate_docker_run(params)
            elif operation.startswith("docker:exec"):
                return await self._validate_docker_exec(params)
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    async def _validate_docker_run(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Docker run operation."""
        # Implementation here
        pass
```

## Troubleshooting

### Common Issues

1. **Security validation fails**
   - Check user roles
   - Verify permissions
   - Review configuration

2. **Adapter not found**
   - Ensure adapter is registered
   - Check component name
   - Verify imports

3. **Configuration errors**
   - Validate JSON syntax
   - Check file permissions
   - Review configuration structure

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger("ai_admin.security").setLevel(logging.DEBUG)
```

### Monitoring

Check security status:

```python
from ai_admin.security.unified_security_integration import get_unified_security

security = get_unified_security()
status = security.get_component_status()
report = security.get_security_report()
```

## Migration Guide

### From Old Security System

1. Update command inheritance
2. Replace direct adapter usage
3. Update configuration
4. Test security validation
5. Verify audit logging

### Configuration Migration

1. Backup existing configuration
2. Create unified configuration
3. Map existing roles
4. Test with new system
5. Deploy gradually

## Security Considerations

### 1. Data Protection

- Encrypt sensitive data
- Mask audit logs
- Secure configuration
- Protect credentials

### 2. Access Control

- Principle of least privilege
- Regular access reviews
- Strong authentication
- Session management

### 3. Monitoring

- Real-time monitoring
- Alert on anomalies
- Regular security reviews
- Incident response

### 4. Compliance

- Audit trail maintenance
- Data retention policies
- Regulatory compliance
- Security documentation

## Conclusion

The unified security integration provides a consistent, scalable, and maintainable approach to security across the AI Admin system. By following this guide, developers can ensure proper security implementation while maintaining system performance and usability.

For additional support or questions, please refer to the project documentation or contact the development team.
