# Шаг 1.5: SCP/SSH интеграция с менеджером очереди

**Дата:** 14 августа 2025  
**Автор:** AI Assistant  
**Цель:** Создание надежной SCP/SSH интеграции с обязательным использованием менеджера очереди

## 🎯 Обзор

SCP/SSH операции должны ОБЯЗАТЕЛЬНО интегрироваться с менеджером очереди задач для обеспечения:
- Надежности выполнения операций
- Мониторинга прогресса
- Retry механизма при сбоях
- Безопасности и аудита
- Масштабируемости

## 📋 Детальный план реализации

### 1. Расширение TaskType enum

**Файл:** `ai_admin/queue/task_queue.py`

```python
class TaskType(Enum):
    # ... существующие типы ...
    
    # SCP/SSH operations
    SCP_UPLOAD = "scp_upload"
    SCP_DOWNLOAD = "scp_download"
    SCP_SYNC = "scp_sync"
    SCP_LIST = "scp_list"
    SSH_EXECUTE = "ssh_execute"
    SSH_CONNECT = "ssh_connect"
    SSH_TUNNEL = "ssh_tunnel"
```

### 2. Расширение TaskErrorCode enum

**Файл:** `ai_admin/queue/task_queue.py`

```python
class TaskErrorCode(Enum):
    # ... существующие коды ...
    
    # SCP/SSH errors
    SCP_CONNECTION_FAILED = "SCP_CONNECTION_FAILED"
    SCP_AUTHENTICATION_FAILED = "SCP_AUTHENTICATION_FAILED"
    SCP_FILE_NOT_FOUND = "SCP_FILE_NOT_FOUND"
    SCP_PERMISSION_DENIED = "SCP_PERMISSION_DENIED"
    SCP_TRANSFER_FAILED = "SCP_TRANSFER_FAILED"
    SCP_TIMEOUT = "SCP_TIMEOUT"
    SCP_DISK_SPACE = "SCP_DISK_SPACE"
    SCP_NETWORK_ERROR = "SCP_NETWORK_ERROR"
    
    SSH_COMMAND_FAILED = "SSH_COMMAND_FAILED"
    SSH_KEY_INVALID = "SSH_KEY_INVALID"
    SSH_HOST_UNREACHABLE = "SSH_HOST_UNREACHABLE"
    SSH_PORT_CLOSED = "SSH_PORT_CLOSED"
    SSH_BANNER_ERROR = "SSH_BANNER_ERROR"
    SSH_PROTOCOL_ERROR = "SSH_PROTOCOL_ERROR"
```

### 3. Реализация методов выполнения SCP задач

**Файл:** `ai_admin/queue/task_queue.py`

```python
async def _execute_scp_upload_task(self, task: Task) -> None:
    """Execute SCP upload task with progress tracking."""
    params = task.params
    host = params.get("host")
    username = params.get("username")
    local_path = params.get("local_path")
    remote_path = params.get("remote_path")
    port = params.get("port", 22)
    key_file = params.get("key_file")
    password = params.get("password")
    recursive = params.get("recursive", False)
    preserve_attributes = params.get("preserve_attributes", True)
    
    try:
        # Update progress and status
        task.current_step = "Connecting to remote host"
        task.progress = 10
        await self._update_task_progress(task)
        
        # Establish SSH connection
        ssh_client = await self._create_ssh_client(
            host, username, port, key_file, password
        )
        
        task.current_step = "Establishing SCP connection"
        task.progress = 20
        await self._update_task_progress(task)
        
        # Create SCP client
        scp_client = await self._create_scp_client(ssh_client)
        
        task.current_step = "Starting file transfer"
        task.progress = 30
        await self._update_task_progress(task)
        
        # Perform upload with progress tracking
        if recursive:
            await self._upload_directory_recursive(
                scp_client, local_path, remote_path, task
            )
        else:
            await self._upload_file(
                scp_client, local_path, remote_path, task
            )
        
        task.current_step = "Transfer completed"
        task.progress = 100
        task.status = TaskStatus.COMPLETED
        task.result = {
            "success": True,
            "files_transferred": task.result.get("files_transferred", 1),
            "bytes_transferred": task.result.get("bytes_transferred", 0),
            "duration": task.get_duration()
        }
        
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error = str(e)
        task.error_code = self._determine_scp_error_code(e)
        task.result = {
            "success": False,
            "error": str(e),
            "error_code": task.error_code.value
        }
        raise
    finally:
        # Cleanup connections
        if 'ssh_client' in locals():
            await self._close_ssh_client(ssh_client)

async def _execute_scp_download_task(self, task: Task) -> None:
    """Execute SCP download task with progress tracking."""
    # Similar implementation for download operations
    pass

async def _execute_ssh_execute_task(self, task: Task) -> None:
    """Execute SSH command task with output capture."""
    params = task.params
    host = params.get("host")
    username = params.get("username")
    command = params.get("command")
    port = params.get("port", 22)
    key_file = params.get("key_file")
    password = params.get("password")
    
    try:
        task.current_step = "Connecting to remote host"
        task.progress = 20
        await self._update_task_progress(task)
        
        # Establish SSH connection
        ssh_client = await self._create_ssh_client(
            host, username, port, key_file, password
        )
        
        task.current_step = "Executing command"
        task.progress = 50
        await self._update_task_progress(task)
        
        # Execute command
        stdin, stdout, stderr = await ssh_client.exec_command(command)
        
        # Capture output
        exit_code = stdout.channel.recv_exit_status()
        stdout_data = stdout.read().decode('utf-8')
        stderr_data = stderr.read().decode('utf-8')
        
        task.current_step = "Command completed"
        task.progress = 100
        task.status = TaskStatus.COMPLETED
        task.result = {
            "success": exit_code == 0,
            "exit_code": exit_code,
            "stdout": stdout_data,
            "stderr": stderr_data,
            "command": command,
            "duration": task.get_duration()
        }
        
        if exit_code != 0:
            task.status = TaskStatus.FAILED
            task.error = f"Command failed with exit code {exit_code}"
            task.error_code = TaskErrorCode.SSH_COMMAND_FAILED
        
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error = str(e)
        task.error_code = self._determine_ssh_error_code(e)
        task.result = {
            "success": False,
            "error": str(e),
            "error_code": task.error_code.value
        }
        raise
    finally:
        if 'ssh_client' in locals():
            await self._close_ssh_client(ssh_client)
```

### 4. Расширение QueueManager

**Файл:** `ai_admin/queue/queue_manager.py`

```python
async def add_scp_upload_task(
    self,
    host: str,
    username: str,
    local_path: str,
    remote_path: str,
    port: int = 22,
    key_file: Optional[str] = None,
    password: Optional[str] = None,
    recursive: bool = False,
    preserve_attributes: bool = True,
    timeout: int = 300,
    retry_count: int = 3,
    **options
) -> str:
    """Add SCP upload task to queue."""
    task = Task(
        task_type=TaskType.SCP_UPLOAD,
        params={
            "host": host,
            "username": username,
            "local_path": local_path,
            "remote_path": remote_path,
            "port": port,
            "key_file": key_file,
            "password": password,
            "recursive": recursive,
            "preserve_attributes": preserve_attributes,
            "timeout": timeout,
            "retry_count": retry_count,
            **options
        },
        category="scp",
        tags=["scp", "upload", "file-transfer"],
        priority=TaskPriority.NORMAL
    )
    
    return await self.task_queue.add_task(task)

async def add_scp_download_task(
    self,
    host: str,
    username: str,
    remote_path: str,
    local_path: str,
    port: int = 22,
    key_file: Optional[str] = None,
    password: Optional[str] = None,
    recursive: bool = False,
    preserve_attributes: bool = True,
    timeout: int = 300,
    retry_count: int = 3,
    **options
) -> str:
    """Add SCP download task to queue."""
    task = Task(
        task_type=TaskType.SCP_DOWNLOAD,
        params={
            "host": host,
            "username": username,
            "remote_path": remote_path,
            "local_path": local_path,
            "port": port,
            "key_file": key_file,
            "password": password,
            "recursive": recursive,
            "preserve_attributes": preserve_attributes,
            "timeout": timeout,
            "retry_count": retry_count,
            **options
        },
        category="scp",
        tags=["scp", "download", "file-transfer"],
        priority=TaskPriority.NORMAL
    )
    
    return await self.task_queue.add_task(task)

async def add_ssh_execute_task(
    self,
    host: str,
    username: str,
    command: str,
    port: int = 22,
    key_file: Optional[str] = None,
    password: Optional[str] = None,
    timeout: int = 60,
    retry_count: int = 2,
    **options
) -> str:
    """Add SSH command execution task to queue."""
    task = Task(
        task_type=TaskType.SSH_EXECUTE,
        params={
            "host": host,
            "username": username,
            "command": command,
            "port": port,
            "key_file": key_file,
            "password": password,
            "timeout": timeout,
            "retry_count": retry_count,
            **options
        },
        category="ssh",
        tags=["ssh", "command", "remote-execution"],
        priority=TaskPriority.NORMAL
    )
    
    return await self.task_queue.add_task(task)

async def add_scp_sync_task(
    self,
    host: str,
    username: str,
    local_path: str,
    remote_path: str,
    port: int = 22,
    key_file: Optional[str] = None,
    password: Optional[str] = None,
    direction: str = "both",  # "local_to_remote", "remote_to_local", "both"
    delete_extra: bool = False,
    preserve_attributes: bool = True,
    timeout: int = 600,
    retry_count: int = 3,
    **options
) -> str:
    """Add SCP sync task to queue."""
    task = Task(
        task_type=TaskType.SCP_SYNC,
        params={
            "host": host,
            "username": username,
            "local_path": local_path,
            "remote_path": remote_path,
            "port": port,
            "key_file": key_file,
            "password": password,
            "direction": direction,
            "delete_extra": delete_extra,
            "preserve_attributes": preserve_attributes,
            "timeout": timeout,
            "retry_count": retry_count,
            **options
        },
        category="scp",
        tags=["scp", "sync", "file-transfer"],
        priority=TaskPriority.NORMAL
    )
    
    return await self.task_queue.add_task(task)
```

### 5. Создание SSH/SCP клиентов

**Файл:** `ai_admin/commands/ssh_client_command.py`

```python
"""SSH client command with queue integration."""

from typing import Dict, Any, Optional
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import ValidationError
from ai_admin.queue.queue_manager import queue_manager


class SSHClientCommand(Command):
    """Command for SSH client operations with queue integration."""
    
    name = "ssh_client"
    
    async def execute(
        self,
        action: str = "execute",  # "execute", "connect", "tunnel"
        host: str = "localhost",
        port: int = 22,
        username: Optional[str] = None,
        password: Optional[str] = None,
        key_file: Optional[str] = None,
        command: Optional[str] = None,
        timeout: int = 60,
        retry_count: int = 2,
        **kwargs
    ) -> SuccessResult:
        """Execute SSH client operations through queue."""
        try:
            # Validate inputs
            if not host:
                raise ValidationError("Host is required")
            
            if not username:
                raise ValidationError("Username is required")
            
            if action == "execute":
                if not command:
                    raise ValidationError("Command is required for execute action")
                
                # Add SSH execute task to queue
                task_id = await queue_manager.add_ssh_execute_task(
                    host=host,
                    username=username,
                    command=command,
                    port=port,
                    key_file=key_file,
                    password=password,
                    timeout=timeout,
                    retry_count=retry_count
                )
                
                return SuccessResult(data={
                    "status": "success",
                    "message": "SSH command task added to queue",
                    "task_id": task_id,
                    "host": host,
                    "username": username,
                    "command": command,
                    "port": port,
                    "timeout": timeout,
                    "retry_count": retry_count,
                    "timestamp": datetime.now().isoformat(),
                    "note": "Use 'queue_task_status' command to monitor progress"
                })
            
            elif action == "connect":
                # Test connection without executing commands
                task_id = await queue_manager.add_ssh_execute_task(
                    host=host,
                    username=username,
                    command="echo 'Connection test successful'",
                    port=port,
                    key_file=key_file,
                    password=password,
                    timeout=timeout,
                    retry_count=retry_count
                )
                
                return SuccessResult(data={
                    "status": "success",
                    "message": "SSH connection test task added to queue",
                    "task_id": task_id,
                    "host": host,
                    "username": username,
                    "port": port,
                    "timestamp": datetime.now().isoformat(),
                    "note": "Use 'queue_task_status' command to monitor progress"
                })
            
            elif action == "tunnel":
                # SSH tunnel functionality (to be implemented)
                raise ValidationError("SSH tunnel functionality not yet implemented")
            
            else:
                raise ValidationError(f"Invalid action: {action}. Must be one of: execute, connect, tunnel")
            
        except ValidationError as e:
            return ErrorResult(
                message=str(e),
                code="VALIDATION_ERROR",
                details={"error_type": "validation"}
            )
        except Exception as e:
            return ErrorResult(
                message=f"Error adding SSH task to queue: {str(e)}",
                code="QUEUE_ERROR",
                details={"error_type": "unexpected", "error": str(e)}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for SSH client command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["execute", "connect", "tunnel"],
                    "default": "execute",
                    "examples": ["execute", "connect", "tunnel"]
                },
                "host": {
                    "type": "string",
                    "description": "Remote host address",
                    "default": "localhost",
                    "examples": ["192.168.1.100", "server.example.com", "localhost"]
                },
                "port": {
                    "type": "integer",
                    "description": "SSH port",
                    "default": 22,
                    "minimum": 1,
                    "maximum": 65535,
                    "examples": [22, 2222, 8022]
                },
                "username": {
                    "type": "string",
                    "description": "SSH username",
                    "examples": ["root", "admin", "user"]
                },
                "password": {
                    "type": "string",
                    "description": "SSH password (not recommended, use key_file instead)",
                    "examples": ["password123"]
                },
                "key_file": {
                    "type": "string",
                    "description": "Path to SSH private key file",
                    "examples": ["/home/user/.ssh/id_rsa", "/path/to/private_key"]
                },
                "command": {
                    "type": "string",
                    "description": "Command to execute on remote host",
                    "examples": ["ls -la", "df -h", "systemctl status nginx"]
                },
                "timeout": {
                    "type": "integer",
                    "description": "Command timeout in seconds",
                    "default": 60,
                    "minimum": 1,
                    "maximum": 3600,
                    "examples": [30, 60, 300]
                },
                "retry_count": {
                    "type": "integer",
                    "description": "Number of retry attempts on failure",
                    "default": 2,
                    "minimum": 0,
                    "maximum": 10,
                    "examples": [1, 2, 3]
                }
            },
            "required": ["host", "username"],
            "additionalProperties": False
        }
```

### 6. Создание SCP клиента

**Файл:** `ai_admin/commands/scp_client_command.py`

```python
"""SCP client command with queue integration."""

from typing import Dict, Any, Optional
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import ValidationError
from ai_admin.queue.queue_manager import queue_manager


class SCPClientCommand(Command):
    """Command for SCP-like file transfer operations with queue integration."""
    
    name = "scp_client"
    
    async def execute(
        self,
        action: str = "upload",  # "upload", "download", "sync", "list"
        host: str = "localhost",
        port: int = 22,
        username: Optional[str] = None,
        password: Optional[str] = None,
        key_file: Optional[str] = None,
        local_path: str = "",
        remote_path: str = "",
        recursive: bool = False,
        preserve_attributes: bool = True,
        timeout: int = 300,
        retry_count: int = 3,
        **kwargs
    ) -> SuccessResult:
        """Execute SCP-like file transfer operations through queue."""
        try:
            # Validate inputs
            if not host:
                raise ValidationError("Host is required")
            
            if not username:
                raise ValidationError("Username is required")
            
            if action == "upload":
                if not local_path or not remote_path:
                    raise ValidationError("Both local_path and remote_path are required for upload")
                
                # Add SCP upload task to queue
                task_id = await queue_manager.add_scp_upload_task(
                    host=host,
                    username=username,
                    local_path=local_path,
                    remote_path=remote_path,
                    port=port,
                    key_file=key_file,
                    password=password,
                    recursive=recursive,
                    preserve_attributes=preserve_attributes,
                    timeout=timeout,
                    retry_count=retry_count
                )
                
                return SuccessResult(data={
                    "status": "success",
                    "message": "SCP upload task added to queue",
                    "task_id": task_id,
                    "host": host,
                    "username": username,
                    "local_path": local_path,
                    "remote_path": remote_path,
                    "port": port,
                    "recursive": recursive,
                    "preserve_attributes": preserve_attributes,
                    "timeout": timeout,
                    "retry_count": retry_count,
                    "timestamp": datetime.now().isoformat(),
                    "note": "Use 'queue_task_status' command to monitor progress"
                })
            
            elif action == "download":
                if not remote_path or not local_path:
                    raise ValidationError("Both remote_path and local_path are required for download")
                
                # Add SCP download task to queue
                task_id = await queue_manager.add_scp_download_task(
                    host=host,
                    username=username,
                    remote_path=remote_path,
                    local_path=local_path,
                    port=port,
                    key_file=key_file,
                    password=password,
                    recursive=recursive,
                    preserve_attributes=preserve_attributes,
                    timeout=timeout,
                    retry_count=retry_count
                )
                
                return SuccessResult(data={
                    "status": "success",
                    "message": "SCP download task added to queue",
                    "task_id": task_id,
                    "host": host,
                    "username": username,
                    "remote_path": remote_path,
                    "local_path": local_path,
                    "port": port,
                    "recursive": recursive,
                    "preserve_attributes": preserve_attributes,
                    "timeout": timeout,
                    "retry_count": retry_count,
                    "timestamp": datetime.now().isoformat(),
                    "note": "Use 'queue_task_status' command to monitor progress"
                })
            
            elif action == "sync":
                if not local_path or not remote_path:
                    raise ValidationError("Both local_path and remote_path are required for sync")
                
                # Add SCP sync task to queue
                task_id = await queue_manager.add_scp_sync_task(
                    host=host,
                    username=username,
                    local_path=local_path,
                    remote_path=remote_path,
                    port=port,
                    key_file=key_file,
                    password=password,
                    preserve_attributes=preserve_attributes,
                    timeout=timeout,
                    retry_count=retry_count
                )
                
                return SuccessResult(data={
                    "status": "success",
                    "message": "SCP sync task added to queue",
                    "task_id": task_id,
                    "host": host,
                    "username": username,
                    "local_path": local_path,
                    "remote_path": remote_path,
                    "port": port,
                    "preserve_attributes": preserve_attributes,
                    "timeout": timeout,
                    "retry_count": retry_count,
                    "timestamp": datetime.now().isoformat(),
                    "note": "Use 'queue_task_status' command to monitor progress"
                })
            
            elif action == "list":
                if not remote_path:
                    raise ValidationError("remote_path is required for list action")
                
                # Use SSH execute to list remote directory
                task_id = await queue_manager.add_ssh_execute_task(
                    host=host,
                    username=username,
                    command=f"ls -la {remote_path}",
                    port=port,
                    key_file=key_file,
                    password=password,
                    timeout=timeout,
                    retry_count=retry_count
                )
                
                return SuccessResult(data={
                    "status": "success",
                    "message": "SCP list task added to queue",
                    "task_id": task_id,
                    "host": host,
                    "username": username,
                    "remote_path": remote_path,
                    "port": port,
                    "timeout": timeout,
                    "retry_count": retry_count,
                    "timestamp": datetime.now().isoformat(),
                    "note": "Use 'queue_task_status' command to monitor progress"
                })
            
            else:
                raise ValidationError(f"Invalid action: {action}. Must be one of: upload, download, sync, list")
            
        except ValidationError as e:
            return ErrorResult(
                message=str(e),
                code="VALIDATION_ERROR",
                details={"error_type": "validation"}
            )
        except Exception as e:
            return ErrorResult(
                message=f"Error adding SCP task to queue: {str(e)}",
                code="QUEUE_ERROR",
                details={"error_type": "unexpected", "error": str(e)}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for SCP client command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["upload", "download", "sync", "list"],
                    "default": "upload",
                    "examples": ["upload", "download", "sync", "list"]
                },
                "host": {
                    "type": "string",
                    "description": "Remote host address",
                    "default": "localhost",
                    "examples": ["192.168.1.100", "server.example.com", "localhost"]
                },
                "port": {
                    "type": "integer",
                    "description": "SSH port",
                    "default": 22,
                    "minimum": 1,
                    "maximum": 65535,
                    "examples": [22, 2222, 8022]
                },
                "username": {
                    "type": "string",
                    "description": "SSH username",
                    "examples": ["root", "admin", "user"]
                },
                "password": {
                    "type": "string",
                    "description": "SSH password (not recommended, use key_file instead)",
                    "examples": ["password123"]
                },
                "key_file": {
                    "type": "string",
                    "description": "Path to SSH private key file",
                    "examples": ["/home/user/.ssh/id_rsa", "/path/to/private_key"]
                },
                "local_path": {
                    "type": "string",
                    "description": "Local file or directory path",
                    "examples": ["/home/user/file.txt", "/var/log/", "./data/"]
                },
                "remote_path": {
                    "type": "string",
                    "description": "Remote file or directory path",
                    "examples": ["/home/user/file.txt", "/var/log/", "/tmp/data/"]
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Transfer directories recursively",
                    "default": False,
                    "examples": [True, False]
                },
                "preserve_attributes": {
                    "type": "boolean",
                    "description": "Preserve file attributes (permissions, timestamps)",
                    "default": True,
                    "examples": [True, False]
                },
                "timeout": {
                    "type": "integer",
                    "description": "Transfer timeout in seconds",
                    "default": 300,
                    "minimum": 1,
                    "maximum": 3600,
                    "examples": [60, 300, 600]
                },
                "retry_count": {
                    "type": "integer",
                    "description": "Number of retry attempts on failure",
                    "default": 3,
                    "minimum": 0,
                    "maximum": 10,
                    "examples": [1, 3, 5]
                }
            },
            "required": ["host", "username"],
            "additionalProperties": False
        }
```

## 🔧 Вспомогательные методы

### SSH/SCP утилиты

**Файл:** `ai_admin/utils/ssh_utils.py`

```python
"""SSH/SCP utility functions."""

import asyncio
import paramiko
from typing import Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SSHUtils:
    """Utility class for SSH/SCP operations."""
    
    @staticmethod
    async def create_ssh_client(
        host: str,
        username: str,
        port: int = 22,
        key_file: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30
    ) -> paramiko.SSHClient:
        """Create and connect SSH client."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Connect with key file or password
            if key_file and Path(key_file).exists():
                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    key_filename=key_file,
                    timeout=timeout
                )
            elif password:
                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=timeout
                )
            else:
                raise ValueError("Either key_file or password must be provided")
            
            return client
            
        except Exception as e:
            client.close()
            raise
    
    @staticmethod
    async def create_scp_client(ssh_client: paramiko.SSHClient) -> paramiko.SCPClient:
        """Create SCP client from SSH client."""
        return ssh_client.open_sftp()
    
    @staticmethod
    async def close_ssh_client(client: paramiko.SSHClient) -> None:
        """Close SSH client connection."""
        if client:
            client.close()
    
    @staticmethod
    def determine_scp_error_code(error: Exception) -> 'TaskErrorCode':
        """Determine appropriate error code for SCP operations."""
        error_str = str(error).lower()
        
        if "authentication" in error_str or "permission denied" in error_str:
            return TaskErrorCode.SCP_AUTHENTICATION_FAILED
        elif "connection" in error_str or "network" in error_str:
            return TaskErrorCode.SCP_CONNECTION_FAILED
        elif "no such file" in error_str or "file not found" in error_str:
            return TaskErrorCode.SCP_FILE_NOT_FOUND
        elif "permission denied" in error_str:
            return TaskErrorCode.SCP_PERMISSION_DENIED
        elif "timeout" in error_str:
            return TaskErrorCode.SCP_TIMEOUT
        elif "disk space" in error_str or "no space" in error_str:
            return TaskErrorCode.SCP_DISK_SPACE
        else:
            return TaskErrorCode.SCP_TRANSFER_FAILED
    
    @staticmethod
    def determine_ssh_error_code(error: Exception) -> 'TaskErrorCode':
        """Determine appropriate error code for SSH operations."""
        error_str = str(error).lower()
        
        if "authentication" in error_str or "permission denied" in error_str:
            return TaskErrorCode.SSH_COMMAND_FAILED
        elif "connection" in error_str or "network" in error_str:
            return TaskErrorCode.SSH_HOST_UNREACHABLE
        elif "timeout" in error_str:
            return TaskErrorCode.SSH_COMMAND_FAILED
        elif "key" in error_str:
            return TaskErrorCode.SSH_KEY_INVALID
        else:
            return TaskErrorCode.SSH_COMMAND_FAILED
```

## 🧪 Тестирование

### Unit тесты

**Файл:** `tests/test_scp_ssh_integration.py`

```python
"""Tests for SCP/SSH integration with queue."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from ai_admin.queue.task_queue import TaskQueue, Task, TaskType, TaskStatus
from ai_admin.queue.queue_manager import QueueManager
from ai_admin.commands.ssh_client_command import SSHClientCommand
from ai_admin.commands.scp_client_command import SCPClientCommand


class TestSCPSSHIntegration:
    """Test SCP/SSH integration with queue system."""
    
    @pytest.fixture
    async def queue_manager(self):
        """Create queue manager for testing."""
        return QueueManager()
    
    @pytest.fixture
    def ssh_command(self):
        """Create SSH command for testing."""
        return SSHClientCommand()
    
    @pytest.fixture
    def scp_command(self):
        """Create SCP command for testing."""
        return SCPClientCommand()
    
    async def test_ssh_execute_task_creation(self, queue_manager):
        """Test SSH execute task creation."""
        task_id = await queue_manager.add_ssh_execute_task(
            host="test.example.com",
            username="testuser",
            command="ls -la",
            port=22
        )
        
        assert task_id is not None
        
        task = await queue_manager.get_task(task_id)
        assert task.task_type == TaskType.SSH_EXECUTE
        assert task.params["host"] == "test.example.com"
        assert task.params["username"] == "testuser"
        assert task.params["command"] == "ls -la"
        assert task.params["port"] == 22
    
    async def test_scp_upload_task_creation(self, queue_manager):
        """Test SCP upload task creation."""
        task_id = await queue_manager.add_scp_upload_task(
            host="test.example.com",
            username="testuser",
            local_path="/local/file.txt",
            remote_path="/remote/file.txt",
            recursive=True
        )
        
        assert task_id is not None
        
        task = await queue_manager.get_task(task_id)
        assert task.task_type == TaskType.SCP_UPLOAD
        assert task.params["host"] == "test.example.com"
        assert task.params["username"] == "testuser"
        assert task.params["local_path"] == "/local/file.txt"
        assert task.params["remote_path"] == "/remote/file.txt"
        assert task.params["recursive"] is True
    
    async def test_scp_download_task_creation(self, queue_manager):
        """Test SCP download task creation."""
        task_id = await queue_manager.add_scp_download_task(
            host="test.example.com",
            username="testuser",
            remote_path="/remote/file.txt",
            local_path="/local/file.txt",
            preserve_attributes=False
        )
        
        assert task_id is not None
        
        task = await queue_manager.get_task(task_id)
        assert task.task_type == TaskType.SCP_DOWNLOAD
        assert task.params["host"] == "test.example.com"
        assert task.params["username"] == "testuser"
        assert task.params["remote_path"] == "/remote/file.txt"
        assert task.params["local_path"] == "/local/file.txt"
        assert task.params["preserve_attributes"] is False
    
    async def test_ssh_command_execution(self, ssh_command):
        """Test SSH command execution through queue."""
        with patch('ai_admin.queue.queue_manager.queue_manager') as mock_queue:
            mock_queue.add_ssh_execute_task = AsyncMock(return_value="test-task-id")
            
            result = await ssh_command.execute(
                action="execute",
                host="test.example.com",
                username="testuser",
                command="ls -la"
            )
            
            assert result.success is True
            assert result.data["task_id"] == "test-task-id"
            assert result.data["host"] == "test.example.com"
            assert result.data["command"] == "ls -la"
    
    async def test_scp_command_upload(self, scp_command):
        """Test SCP command upload through queue."""
        with patch('ai_admin.queue.queue_manager.queue_manager') as mock_queue:
            mock_queue.add_scp_upload_task = AsyncMock(return_value="test-task-id")
            
            result = await scp_command.execute(
                action="upload",
                host="test.example.com",
                username="testuser",
                local_path="/local/file.txt",
                remote_path="/remote/file.txt"
            )
            
            assert result.success is True
            assert result.data["task_id"] == "test-task-id"
            assert result.data["host"] == "test.example.com"
            assert result.data["local_path"] == "/local/file.txt"
            assert result.data["remote_path"] == "/remote/file.txt"
    
    async def test_scp_command_download(self, scp_command):
        """Test SCP command download through queue."""
        with patch('ai_admin.queue.queue_manager.queue_manager') as mock_queue:
            mock_queue.add_scp_download_task = AsyncMock(return_value="test-task-id")
            
            result = await scp_command.execute(
                action="download",
                host="test.example.com",
                username="testuser",
                remote_path="/remote/file.txt",
                local_path="/local/file.txt"
            )
            
            assert result.success is True
            assert result.data["task_id"] == "test-task-id"
            assert result.data["host"] == "test.example.com"
            assert result.data["remote_path"] == "/remote/file.txt"
            assert result.data["local_path"] == "/local/file.txt"
    
    async def test_validation_errors(self, ssh_command, scp_command):
        """Test validation error handling."""
        # Test SSH command without required parameters
        result = await ssh_command.execute(action="execute")
        assert result.success is False
        assert "Host is required" in result.message
        
        # Test SCP command without required parameters
        result = await scp_command.execute(action="upload")
        assert result.success is False
        assert "Host is required" in result.message
        
        # Test SCP upload without paths
        result = await scp_command.execute(
            action="upload",
            host="test.example.com",
            username="testuser"
        )
        assert result.success is False
        assert "local_path and remote_path are required" in result.message
```

## 📋 Чек-лист реализации

### Обязательные компоненты:
- [ ] Расширение `TaskType` enum для SCP/SSH операций
- [ ] Расширение `TaskErrorCode` enum для SCP/SSH ошибок
- [ ] Реализация методов выполнения SCP задач в `TaskQueue`
- [ ] Добавление методов в `QueueManager` для SCP/SSH задач
- [ ] Создание `SSHClientCommand` с интеграцией в очередь
- [ ] Создание `SCPClientCommand` с интеграцией в очередь
- [ ] Создание утилит `SSHUtils` для работы с SSH/SCP
- [ ] Написание unit-тестов для всех компонентов

### Дополнительные возможности:
- [ ] Поддержка SSH туннелей и порт-форвардинга
- [ ] Интеграция с системой ролей для контроля доступа
- [ ] Поддержка множественных одновременных соединений
- [ ] Кэширование SSH соединений для повторного использования
- [ ] Поддержка различных типов SSH ключей
- [ ] Интеграция с SSL/mTLS для дополнительной безопасности

### Тестирование:
- [ ] Unit-тесты для всех новых методов
- [ ] Интеграционные тесты с реальными SSH серверами
- [ ] Тесты производительности для больших файлов
- [ ] Тесты обработки ошибок и retry механизма
- [ ] Тесты безопасности и аутентификации

## 🚀 Преимущества интеграции с очередью

1. **Надежность:** Операции выполняются в фоновом режиме с retry механизмом
2. **Мониторинг:** Полное отслеживание прогресса и статуса операций
3. **Масштабируемость:** Поддержка множественных одновременных операций
4. **Безопасность:** Интеграция с системой ролей и SSL/mTLS
5. **Аудит:** Подробное логирование всех операций
6. **Управление:** Возможность паузы, возобновления и отмены операций
7. **Производительность:** Оптимизация ресурсов через очередь задач

Этот подход обеспечивает максимальную надежность и функциональность для SCP/SSH операций в ai_admin.
