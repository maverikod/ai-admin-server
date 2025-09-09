# Шаг 3.2: Интеграция с Hypercorn для SSL/mTLS

**Зависимости:** Шаг 3.1 (Модификация server.py)  
**Приоритет:** Высокий  
**Время:** 2-3 часа  
**Этап:** 3 (Интеграция и тестирование)

## 📋 Задача шага

Интегрировать Hypercorn ASGI сервер для замены uvicorn с полной поддержкой SSL/mTLS. Настроить Hypercorn как основной сервер для всех SSL/mTLS операций.

## 📁 Файлы изменений

### Создаваемые файлы:
- `ai_admin/core/server_adapter.py` - адаптер для переключения между серверами
- `ai_admin/core/hypercorn_config.py` - конфигурация Hypercorn
- `ai_admin/core/server_exceptions.py` - исключения для серверов
- `tests/test_server_adapter.py` - unit-тесты для адаптера
- `tests/test_hypercorn_config.py` - unit-тесты для конфигурации
- `tests/test_server_exceptions.py` - unit-тесты для исключений

### Модифицируемые файлы:
- `ai_admin/server.py` - интеграция с адаптером серверов
- `requirements.txt` - добавление зависимости hypercorn

## 🔧 Описание изменений

### 1. Создание ServerAdapter
Создать класс `ServerAdapter` для переключения между uvicorn и hypercorn:
- Автоматический выбор сервера на основе SSL конфигурации
- Единый интерфейс для запуска серверов
- Поддержка всех параметров конфигурации

### 2. Создание HypercornConfig
Создать класс `HypercornConfig` для настройки Hypercorn:
- Конфигурация SSL/mTLS параметров
- Настройка рабочих процессов
- Конфигурация логирования

### 3. Создание исключений
Создать отдельный файл с исключениями для серверов:
- `ServerError` - базовое исключение для серверов
- `ServerStartupError` - ошибки запуска сервера
- `ServerConfigError` - ошибки конфигурации сервера
- `SSLConfigError` - ошибки SSL конфигурации

### 4. Обновление server.py
Модифицировать `server.py` для использования адаптера серверов.

### 5. Добавление зависимостей
Добавить библиотеку `hypercorn` в requirements.txt.

### 6. Создание unit-тестов
Написать comprehensive unit-тесты для всех новых компонентов.

## 💻 Декларативный код

### ai_admin/core/server_exceptions.py
```python
"""Server-related exceptions for AI Admin."""

from typing import Optional, Dict, Any


class ServerError(Exception):
    """Base exception for server-related errors."""
    
    def __init__(
        self,
        message: str,
        server_type: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize server error.
        
        Args:
            message: Error message
            server_type: Type of server that failed
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.server_type = server_type
        self.error_code = error_code
        self.details = details or {}


class ServerStartupError(ServerError):
    """Exception raised when server startup fails."""
    
    def __init__(
        self,
        message: str,
        server_type: str,
        startup_config: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize server startup error.
        
        Args:
            message: Error message
            server_type: Type of server that failed to start
            startup_config: Server startup configuration
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, server_type, error_code, details)
        self.startup_config = startup_config or {}


class ServerConfigError(ServerError):
    """Exception raised when server configuration fails."""
    
    def __init__(
        self,
        message: str,
        config_type: str,
        config_data: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize server configuration error.
        
        Args:
            message: Error message
            config_type: Type of configuration that failed
            config_data: Configuration data that failed
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, "config", error_code, details)
        self.config_type = config_type
        self.config_data = config_data or {}


class SSLServerConfigError(ServerError):
    """Exception raised when SSL server configuration fails."""
    
    def __init__(
        self,
        message: str,
        ssl_setting: Optional[str] = None,
        ssl_config: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize SSL server configuration error.
        
        Args:
            message: Error message
            ssl_setting: SSL setting that failed
            ssl_config: SSL configuration that failed
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, "ssl", error_code, details)
        self.ssl_setting = ssl_setting
        self.ssl_config = ssl_config or {}
```

### ai_admin/core/hypercorn_config.py
```python
"""Hypercorn configuration for AI Admin."""

import os
import ssl
from typing import Dict, Any, Optional, List
from hypercorn.config import Config
from .server_exceptions import SSLServerConfigError


class HypercornConfig:
    """Hypercorn configuration manager for AI Admin."""
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        ssl_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Hypercorn configuration.
        
        Args:
            host: Server host
            port: Server port
            ssl_config: SSL configuration dictionary
        """
        pass
    
    def create_config(
        self,
        app_name: str = "AI Admin",
        workers: int = 1,
        worker_class: str = "asyncio",
        keep_alive_timeout: int = 5,
        max_incomplete_size: int = 16384,
        ssl_enabled: bool = False
    ) -> Config:
        """
        Create Hypercorn configuration.
        
        Args:
            app_name: Application name
            workers: Number of worker processes
            worker_class: Worker class type
            keep_alive_timeout: Keep alive timeout
            max_incomplete_size: Maximum incomplete request size
            ssl_enabled: Whether SSL is enabled
            
        Returns:
            Hypercorn Config object
            
        Raises:
            SSLServerConfigError: If SSL configuration fails
        """
        pass
    
    def configure_ssl(
        self,
        config: Config,
        ssl_config: Dict[str, Any]
    ) -> None:
        """
        Configure SSL settings for Hypercorn.
        
        Args:
            config: Hypercorn Config object
            ssl_config: SSL configuration dictionary
            
        Raises:
            SSLServerConfigError: If SSL configuration fails
        """
        pass
    
    def configure_ssl_context(
        self,
        ssl_config: Dict[str, Any]
    ) -> ssl.SSLContext:
        """
        Create SSL context for Hypercorn.
        
        Args:
            ssl_config: SSL configuration dictionary
            
        Returns:
            SSL context object
            
        Raises:
            SSLServerConfigError: If SSL context creation fails
        """
        pass
    
    def configure_mtls(
        self,
        config: Config,
        ssl_config: Dict[str, Any]
    ) -> None:
        """
        Configure mTLS settings for Hypercorn.
        
        Args:
            config: Hypercorn Config object
            ssl_config: SSL configuration dictionary
            
        Raises:
            SSLServerConfigError: If mTLS configuration fails
        """
        pass
    
    def configure_workers(
        self,
        config: Config,
        workers: int,
        worker_class: str
    ) -> None:
        """
        Configure worker settings for Hypercorn.
        
        Args:
            config: Hypercorn Config object
            workers: Number of workers
            worker_class: Worker class type
        """
        pass
    
    def configure_logging(
        self,
        config: Config,
        log_level: str = "info",
        access_log_format: str = '%(h)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
    ) -> None:
        """
        Configure logging for Hypercorn.
        
        Args:
            config: Hypercorn Config object
            log_level: Logging level
            access_log_format: Access log format
        """
        pass
    
    def configure_cors(
        self,
        config: Config,
        cors_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Configure CORS settings for Hypercorn.
        
        Args:
            config: Hypercorn Config object
            cors_config: CORS configuration dictionary
        """
        pass
    
    def _validate_ssl_config(self, ssl_config: Dict[str, Any]) -> List[str]:
        """
        Validate SSL configuration.
        
        Args:
            ssl_config: SSL configuration dictionary
            
        Returns:
            List of validation error messages
        """
        pass
    
    def _validate_certificate_files(
        self,
        cert_file: str,
        key_file: str,
        ca_cert: Optional[str] = None
    ) -> List[str]:
        """
        Validate certificate files.
        
        Args:
            cert_file: Certificate file path
            key_file: Private key file path
            ca_cert: CA certificate file path
            
        Returns:
            List of validation error messages
        """
        pass
    
    def _get_ssl_verify_mode(
        self,
        verify_client: bool,
        client_cert_required: bool
    ) -> ssl.VerifyMode:
        """
        Get SSL verification mode.
        
        Args:
            verify_client: Whether to verify client certificates
            client_cert_required: Whether client certificates are required
            
        Returns:
            SSL verification mode
        """
        pass
    
    def _configure_ssl_ciphers(
        self,
        ssl_context: ssl.SSLContext,
        cipher_suites: Optional[List[str]] = None
    ) -> None:
        """
        Configure SSL cipher suites.
        
        Args:
            ssl_context: SSL context object
            cipher_suites: List of cipher suites
        """
        pass
    
    def _configure_ssl_protocols(
        self,
        ssl_context: ssl.SSLContext,
        min_tls_version: str = "1.2",
        max_tls_version: str = "1.3"
    ) -> None:
        """
        Configure SSL protocol versions.
        
        Args:
            ssl_context: SSL context object
            min_tls_version: Minimum TLS version
            max_tls_version: Maximum TLS version
        """
        pass
    
    def _get_default_ssl_config(self) -> Dict[str, Any]:
        """
        Get default SSL configuration.
        
        Returns:
            Default SSL configuration dictionary
        """
        pass
    
    def _merge_ssl_config(
        self,
        base_config: Dict[str, Any],
        override_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge SSL configurations.
        
        Args:
            base_config: Base SSL configuration
            override_config: Override SSL configuration
            
        Returns:
            Merged SSL configuration
        """
        pass
```

### ai_admin/core/server_adapter.py
```python
"""Server adapter for switching between uvicorn and hypercorn."""

import asyncio
import ssl
from typing import Dict, Any, Optional, Union
from pathlib import Path
import uvicorn
import hypercorn.asyncio
from hypercorn.config import Config as HypercornConfig
from .hypercorn_config import HypercornConfig as AIAdminHypercornConfig
from .server_exceptions import (
    ServerError,
    ServerStartupError,
    ServerConfigError,
    SSLServerConfigError
)


class ServerAdapter:
    """Adapter for switching between uvicorn and hypercorn servers."""
    
    def __init__(
        self,
        app,
        ssl_config: Optional[Dict[str, Any]] = None,
        prefer_hypercorn: bool = True
    ):
        """
        Initialize server adapter.
        
        Args:
            app: ASGI application
            ssl_config: SSL configuration dictionary
            prefer_hypercorn: Whether to prefer hypercorn over uvicorn
        """
        pass
    
    async def run_server(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        workers: int = 1,
        reload: bool = False,
        log_level: str = "info",
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        ssl_ca_certs: Optional[str] = None,
        ssl_verify_mode: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Run server with automatic server selection.
        
        Args:
            host: Server host
            port: Server port
            workers: Number of worker processes
            reload: Whether to enable auto-reload
            log_level: Logging level
            ssl_keyfile: SSL key file path
            ssl_certfile: SSL certificate file path
            ssl_ca_certs: SSL CA certificates file path
            ssl_verify_mode: SSL verification mode
            **kwargs: Additional server parameters
            
        Raises:
            ServerStartupError: If server startup fails
            ServerConfigError: If server configuration fails
        """
        pass
    
    def _select_server(
        self,
        ssl_enabled: bool,
        workers: int,
        reload: bool
    ) -> str:
        """
        Select appropriate server based on configuration.
        
        Args:
            ssl_enabled: Whether SSL is enabled
            workers: Number of workers
            reload: Whether auto-reload is enabled
            
        Returns:
            Server type ('uvicorn' or 'hypercorn')
        """
        pass
    
    async def _run_uvicorn(
        self,
        host: str,
        port: int,
        reload: bool,
        log_level: str,
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        ssl_ca_certs: Optional[str] = None,
        ssl_verify_mode: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Run server using uvicorn.
        
        Args:
            host: Server host
            port: Server port
            reload: Whether to enable auto-reload
            log_level: Logging level
            ssl_keyfile: SSL key file path
            ssl_certfile: SSL certificate file path
            ssl_ca_certs: SSL CA certificates file path
            ssl_verify_mode: SSL verification mode
            **kwargs: Additional uvicorn parameters
        """
        pass
    
    async def _run_hypercorn(
        self,
        host: str,
        port: int,
        workers: int,
        log_level: str,
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        ssl_ca_certs: Optional[str] = None,
        ssl_verify_mode: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Run server using hypercorn.
        
        Args:
            host: Server host
            port: Server port
            workers: Number of workers
            log_level: Logging level
            ssl_keyfile: SSL key file path
            ssl_certfile: SSL certificate file path
            ssl_ca_certs: SSL CA certificates file path
            ssl_verify_mode: SSL verification mode
            **kwargs: Additional hypercorn parameters
        """
        pass
    
    def _configure_uvicorn_ssl(
        self,
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        ssl_ca_certs: Optional[str] = None,
        ssl_verify_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Configure SSL settings for uvicorn.
        
        Args:
            ssl_keyfile: SSL key file path
            ssl_certfile: SSL certificate file path
            ssl_ca_certs: SSL CA certificates file path
            ssl_verify_mode: SSL verification mode
            
        Returns:
            SSL configuration dictionary for uvicorn
        """
        pass
    
    def _configure_hypercorn_ssl(
        self,
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        ssl_ca_certs: Optional[str] = None,
        ssl_verify_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Configure SSL settings for hypercorn.
        
        Args:
            ssl_keyfile: SSL key file path
            ssl_certfile: SSL certificate file path
            ssl_ca_certs: SSL CA certificates file path
            ssl_verify_mode: SSL verification mode
            
        Returns:
            SSL configuration dictionary for hypercorn
        """
        pass
    
    def _validate_ssl_files(
        self,
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        ssl_ca_certs: Optional[str] = None
    ) -> List[str]:
        """
        Validate SSL certificate files.
        
        Args:
            ssl_keyfile: SSL key file path
            ssl_certfile: SSL certificate file path
            ssl_ca_certs: SSL CA certificates file path
            
        Returns:
            List of validation error messages
        """
        pass
    
    def _get_ssl_verify_mode_from_string(
        self,
        verify_mode_str: str
    ) -> ssl.VerifyMode:
        """
        Convert string SSL verify mode to ssl.VerifyMode.
        
        Args:
            verify_mode_str: SSL verify mode string
            
        Returns:
            SSL verify mode enum value
        """
        pass
    
    def _is_ssl_enabled(
        self,
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None
    ) -> bool:
        """
        Check if SSL is enabled based on certificate files.
        
        Args:
            ssl_keyfile: SSL key file path
            ssl_certfile: SSL certificate file path
            
        Returns:
            True if SSL is enabled
        """
        pass
    
    def _get_server_info(self, server_type: str) -> Dict[str, Any]:
        """
        Get server information.
        
        Args:
            server_type: Type of server
            
        Returns:
            Server information dictionary
        """
        pass
    
    def _log_server_selection(self, server_type: str, reason: str) -> None:
        """
        Log server selection decision.
        
        Args:
            server_type: Selected server type
            reason: Reason for selection
        """
        pass
```

### tests/test_server_adapter.py
```python
"""Unit tests for ServerAdapter."""

import asyncio
import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from ai_admin.core.server_adapter import ServerAdapter
from ai_admin.core.server_exceptions import (
    ServerError,
    ServerStartupError,
    ServerConfigError,
    SSLServerConfigError
)


class TestServerAdapter(unittest.TestCase):
    """Test cases for ServerAdapter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = Mock()
        self.ssl_config = {
            "enabled": True,
            "mode": "https_only",
            "cert_file": "test.crt",
            "key_file": "test.key"
        }
        self.adapter = ServerAdapter(self.app, self.ssl_config)
    
    def test_init_default(self):
        """Test default initialization."""
        pass
    
    def test_init_with_ssl_config(self):
        """Test initialization with SSL configuration."""
        pass
    
    def test_init_prefer_uvicorn(self):
        """Test initialization preferring uvicorn."""
        pass
    
    @patch('ai_admin.core.server_adapter.uvicorn.run')
    def test_run_server_uvicorn_selection(self, mock_uvicorn):
        """Test server run with uvicorn selection."""
        pass
    
    @patch('ai_admin.core.server_adapter.hypercorn.asyncio.serve')
    def test_run_server_hypercorn_selection(self, mock_hypercorn):
        """Test server run with hypercorn selection."""
        pass
    
    def test_run_server_ssl_enabled(self):
        """Test server run with SSL enabled."""
        pass
    
    def test_run_server_ssl_disabled(self):
        """Test server run with SSL disabled."""
        pass
    
    def test_run_server_with_workers(self):
        """Test server run with multiple workers."""
        pass
    
    def test_run_server_with_reload(self):
        """Test server run with auto-reload."""
        pass
    
    def test_select_server_ssl_enabled(self):
        """Test server selection with SSL enabled."""
        pass
    
    def test_select_server_ssl_disabled(self):
        """Test server selection with SSL disabled."""
        pass
    
    def test_select_server_multiple_workers(self):
        """Test server selection with multiple workers."""
        pass
    
    def test_select_server_reload_enabled(self):
        """Test server selection with reload enabled."""
        pass
    
    @patch('ai_admin.core.server_adapter.uvicorn.run')
    def test_run_uvicorn_success(self, mock_uvicorn):
        """Test successful uvicorn run."""
        pass
    
    @patch('ai_admin.core.server_adapter.uvicorn.run')
    def test_run_uvicorn_with_ssl(self, mock_uvicorn):
        """Test uvicorn run with SSL."""
        pass
    
    @patch('ai_admin.core.server_adapter.hypercorn.asyncio.serve')
    def test_run_hypercorn_success(self, mock_hypercorn):
        """Test successful hypercorn run."""
        pass
    
    @patch('ai_admin.core.server_adapter.hypercorn.asyncio.serve')
    def test_run_hypercorn_with_ssl(self, mock_hypercorn):
        """Test hypercorn run with SSL."""
        pass
    
    def test_configure_uvicorn_ssl_success(self):
        """Test successful uvicorn SSL configuration."""
        pass
    
    def test_configure_uvicorn_ssl_missing_files(self):
        """Test uvicorn SSL configuration with missing files."""
        pass
    
    def test_configure_hypercorn_ssl_success(self):
        """Test successful hypercorn SSL configuration."""
        pass
    
    def test_configure_hypercorn_ssl_missing_files(self):
        """Test hypercorn SSL configuration with missing files."""
        pass
    
    def test_validate_ssl_files_success(self):
        """Test successful SSL files validation."""
        pass
    
    def test_validate_ssl_files_missing(self):
        """Test SSL files validation with missing files."""
        pass
    
    def test_get_ssl_verify_mode_from_string_valid(self):
        """Test SSL verify mode conversion with valid string."""
        pass
    
    def test_get_ssl_verify_mode_from_string_invalid(self):
        """Test SSL verify mode conversion with invalid string."""
        pass
    
    def test_is_ssl_enabled_true(self):
        """Test SSL enabled check when enabled."""
        pass
    
    def test_is_ssl_enabled_false(self):
        """Test SSL enabled check when disabled."""
        pass
    
    def test_get_server_info_uvicorn(self):
        """Test server info retrieval for uvicorn."""
        pass
    
    def test_get_server_info_hypercorn(self):
        """Test server info retrieval for hypercorn."""
        pass
    
    def test_log_server_selection(self):
        """Test server selection logging."""
        pass
```

### tests/test_hypercorn_config.py
```python
"""Unit tests for HypercornConfig."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from hypercorn.config import Config
from ai_admin.core.hypercorn_config import HypercornConfig
from ai_admin.core.server_exceptions import SSLServerConfigError


class TestHypercornConfig(unittest.TestCase):
    """Test cases for HypercornConfig class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = HypercornConfig()
        self.ssl_config = {
            "enabled": True,
            "mode": "https_only",
            "cert_file": "test.crt",
            "key_file": "test.key",
            "ca_cert": "ca.crt",
            "verify_client": False,
            "client_cert_required": False
        }
    
    def test_init_default(self):
        """Test default initialization."""
        pass
    
    def test_init_with_ssl_config(self):
        """Test initialization with SSL configuration."""
        pass
    
    def test_create_config_basic(self):
        """Test basic configuration creation."""
        pass
    
    def test_create_config_with_ssl(self):
        """Test configuration creation with SSL."""
        pass
    
    def test_create_config_with_workers(self):
        """Test configuration creation with multiple workers."""
        pass
    
    def test_configure_ssl_success(self):
        """Test successful SSL configuration."""
        pass
    
    def test_configure_ssl_invalid_config(self):
        """Test SSL configuration with invalid config."""
        pass
    
    def test_configure_ssl_context_success(self):
        """Test successful SSL context creation."""
        pass
    
    def test_configure_ssl_context_invalid_files(self):
        """Test SSL context creation with invalid files."""
        pass
    
    def test_configure_mtls_success(self):
        """Test successful mTLS configuration."""
        pass
    
    def test_configure_mtls_invalid_config(self):
        """Test mTLS configuration with invalid config."""
        pass
    
    def test_configure_workers_success(self):
        """Test successful workers configuration."""
        pass
    
    def test_configure_logging_success(self):
        """Test successful logging configuration."""
        pass
    
    def test_configure_cors_success(self):
        """Test successful CORS configuration."""
        pass
    
    def test_validate_ssl_config_valid(self):
        """Test SSL configuration validation with valid config."""
        pass
    
    def test_validate_ssl_config_invalid(self):
        """Test SSL configuration validation with invalid config."""
        pass
    
    def test_validate_certificate_files_valid(self):
        """Test certificate files validation with valid files."""
        pass
    
    def test_validate_certificate_files_invalid(self):
        """Test certificate files validation with invalid files."""
        pass
    
    def test_get_ssl_verify_mode_verify_client(self):
        """Test SSL verify mode with client verification."""
        pass
    
    def test_get_ssl_verify_mode_no_verification(self):
        """Test SSL verify mode without verification."""
        pass
    
    def test_configure_ssl_ciphers_success(self):
        """Test successful SSL ciphers configuration."""
        pass
    
    def test_configure_ssl_protocols_success(self):
        """Test successful SSL protocols configuration."""
        pass
    
    def test_get_default_ssl_config(self):
        """Test default SSL configuration generation."""
        pass
    
    def test_merge_ssl_config(self):
        """Test SSL configuration merging."""
        pass
```

### tests/test_server_exceptions.py
```python
"""Unit tests for server exceptions."""

import unittest
from ai_admin.core.server_exceptions import (
    ServerError,
    ServerStartupError,
    ServerConfigError,
    SSLServerConfigError
)


class TestServerError(unittest.TestCase):
    """Test cases for ServerError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_server_type(self):
        """Test initialization with server type."""
        pass
    
    def test_init_with_error_code(self):
        """Test initialization with error code."""
        pass
    
    def test_init_with_details(self):
        """Test initialization with details."""
        pass


class TestServerStartupError(unittest.TestCase):
    """Test cases for ServerStartupError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_startup_config(self):
        """Test initialization with startup config."""
        pass


class TestServerConfigError(unittest.TestCase):
    """Test cases for ServerConfigError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_config_type(self):
        """Test initialization with config type."""
        pass
    
    def test_init_with_config_data(self):
        """Test initialization with config data."""
        pass


class TestSSLServerConfigError(unittest.TestCase):
    """Test cases for SSLServerConfigError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_ssl_setting(self):
        """Test initialization with SSL setting."""
        pass
    
    def test_init_with_ssl_config(self):
        """Test initialization with SSL config."""
        pass
```

## 📊 Метрики успешного завершения

### Специфичные метрики для данного шага:
- [ ] **Создан класс ServerAdapter** с автоматическим выбором сервера
- [ ] **Реализован метод run_server** - запускает сервер с автоматическим выбором
- [ ] **Реализован метод _select_server** - выбирает подходящий сервер
- [ ] **Реализован метод _run_uvicorn** - запускает uvicorn сервер
- [ ] **Реализован метод _run_hypercorn** - запускает hypercorn сервер
- [ ] **Реализованы методы конфигурации SSL** для обоих серверов
- [ ] **Создан класс HypercornConfig** для настройки Hypercorn
- [ ] **Реализован метод create_config** - создает конфигурацию Hypercorn
- [ ] **Реализован метод configure_ssl** - настраивает SSL для Hypercorn
- [ ] **Реализован метод configure_mtls** - настраивает mTLS для Hypercorn
- [ ] **Реализованы все вспомогательные методы** (_validate_ssl_config, _configure_ssl_context, etc.)
- [ ] **Написаны unit-тесты** с покрытием не менее 90%
- [ ] **Создан файл server_exceptions.py** с иерархией исключений
- [ ] **Модифицирован ai_admin/server.py** для использования адаптера
- [ ] **Добавлена зависимость hypercorn** в requirements.txt
- [ ] **Поддерживается автоматический выбор сервера** на основе конфигурации
- [ ] **Поддерживается полная SSL/mTLS конфигурация** для обоих серверов
- [ ] **Реализована валидация SSL файлов** и конфигурации
- [ ] **Поддерживается настройка рабочих процессов** для Hypercorn
- [ ] **Документация методов** содержит полные docstrings с типами и описаниями
- [ ] **Код проходит линтеры** (flake8, mypy, black)
- [ ] **Тесты проходят успешно** (pytest)
- [ ] **Серверы запускаются и работают** с SSL/mTLS поддержкой

### Общие метрики успеха:
- [ ] **Код ВСЕХ шагов с номером таким же, или ниже в плане реализован ПОЛНОСТЬЮ**
- [ ] **Прошел проверку на отсутствие ошибок инструментами**
- [ ] **Покрытие КАЖДОГО файла проекта, котороый относится к уже пройденным шагам не ниже 90%+**
- [ ] **После написания кода была проведена ПОЛНАЯ и тщательная проверка на наличие нереализованного кода**
- [ ] **В коде отсутсвтует хардкод**

## 🔗 Связанные шаги

- **Зависимости:** Шаг 3.1 (Модификация server.py)
- **Использует:** Шаг 1.1 (CertificateUtils), Шаг 2.1 (Расширение конфигурации)
- **Используется в:** Шаг 3.3 (Интеграция SSL/mTLS)

## 📚 Дополнительные ресурсы

- [Hypercorn Documentation](https://hypercorn.readthedocs.io/)
- [Uvicorn vs Hypercorn Comparison](https://www.uvicorn.org/#comparison)
- [ASGI Server Configuration](https://asgi.readthedocs.io/en/latest/specs/main.html)
- [SSL/TLS Server Configuration](https://docs.python.org/3/library/ssl.html#ssl-contexts)
