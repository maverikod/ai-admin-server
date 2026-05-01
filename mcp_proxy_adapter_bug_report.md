# Bug Report: ConfigCommand.execute() got an unexpected keyword argument 'context'

## Issue Description

The built-in `ConfigCommand` in `mcp_proxy_adapter.commands.config_command` has a method signature that doesn't support the `context` parameter that the framework tries to pass to all commands.

## Error Details

```
TypeError: ConfigCommand.execute() got an unexpected keyword argument 'context'
Traceback (most recent call last):
  File "/home/vasilyvz/projects/vast_srv/.venv/lib/python3.12/site-packages/mcp_proxy_adapter/commands/base.py", line 192, in run
    result = await command.execute(**validated_params, context=context)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: ConfigCommand.execute() got an unexpected keyword argument 'context'
```

## Current Method Signature

```python
async def execute(self, operation: str = "get", path: str = None, value: Any = None) -> ConfigResult:
```

## Expected Method Signature

The method should accept `context` parameter to be compatible with the framework's command execution pattern:

```python
async def execute(self, operation: str = "get", path: str = None, value: Any = None, context: Optional[Dict] = None, **kwargs) -> ConfigResult:
```

## Environment

- Python 3.12
- mcp_proxy_adapter package
- AI Admin Server project

## Steps to Reproduce

1. Start AI Admin Server with mcp_proxy_adapter
2. Try to execute `config` command via `/cmd` endpoint
3. Framework passes `context` parameter to `ConfigCommand.execute()`
4. Method signature doesn't accept `context` parameter
5. TypeError is raised

## Proposed Fix

Add `context` parameter to the `execute` method signature in `ConfigCommand`:

```python
async def execute(self, operation: str = "get", path: str = None, value: Any = None, context: Optional[Dict] = None, **kwargs) -> ConfigResult:
    """
    Execute the command.
    
    Args:
        operation: Operation to perform (get, set)
        path: Configuration path (dot notation)
        value: Value to set (for set operation)
        context: Optional context parameter passed by framework
        **kwargs: Additional parameters
        
    Returns:
        Config operation result
    """
    # Existing implementation remains the same
    # context parameter can be ignored or used for logging/debugging
```

## Impact

This bug prevents the built-in `config` command from working properly in the mcp_proxy_adapter framework, forcing users to create custom implementations or work around the issue.

## Date

2025-09-14

## Reporter

Vasiliy Zdanovskiy (vasilyvz@gmail.com)
