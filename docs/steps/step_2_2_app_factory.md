# Шаг 2.2: Создание фабричного метода для приложения

**Зависимости:** Шаг 2.1 (Расширение конфигурации)  
**Приоритет:** Высокий  
**Время:** 3-4 часа  
**Этап:** 2 (Конфигурация и фабрики)

## 📋 Задача шага

Создать фабричный метод для создания и настройки FastAPI приложения с поддержкой SSL/mTLS. Фабрика должна интегрировать все созданные компоненты (SSL конфигурацию, middleware, команды) и обеспечивать единообразную инициализацию приложения.

## 📁 Файлы изменений

### Создаваемые файлы:
- `ai_admin/core/__init__.py` - инициализация пакета core
- `ai_admin/core/app_factory.py` - фабричный метод для создания приложения
- `ai_admin/core/factory_exceptions.py` - исключения для фабрики
- `tests/test_app_factory.py` - unit-тесты для фабрики
- `tests/test_factory_exceptions.py` - unit-тесты для исключений

### Модифицируемые файлы:
- Нет

## 🔧 Описание изменений

### 1. Создание AppFactory класса
Создать класс `AppFactory` для создания и настройки FastAPI приложения:
- Создание FastAPI приложения
- Настройка SSL/mTLS middleware
- Регистрация команд
- Настройка маршрутов
- Конфигурация логирования

### 2. Создание исключений
Создать отдельный файл с исключениями для фабрики:
- `FactoryError` - базовое исключение для фабрики
- `AppCreationError` - ошибки создания приложения
- `MiddlewareSetupError` - ошибки настройки middleware
- `CommandRegistrationError` - ошибки регистрации команд

### 3. Создание unit-тестов
Написать comprehensive unit-тесты для всех методов фабрики и исключений.

## 💻 Декларативный код

### ai_admin/core/__init__.py
```python
"""AI Admin core package."""

from .app_factory import AppFactory
from .factory_exceptions import (
    FactoryError,
    AppCreationError,
    MiddlewareSetupError,
    CommandRegistrationError
)

__all__ = [
    "AppFactory",
    "FactoryError",
    "AppCreationError",
    "MiddlewareSetupError",
    "CommandRegistrationError"
]
```

### ai_admin/core/factory_exceptions.py
```python
"""Factory-related exceptions for AI Admin."""

from typing import Optional, Dict, Any, List


class FactoryError(Exception):
    """Base exception for factory-related errors."""
    
    def __init__(
        self,
        message: str,
        factory_component: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize factory error.
        
        Args:
            message: Error message
            factory_component: Factory component that failed
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.factory_component = factory_component
        self.error_code = error_code
        self.details = details or {}


class AppCreationError(FactoryError):
    """Exception raised when application creation fails."""
    
    def __init__(
        self,
        message: str,
        app_config: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize application creation error.
        
        Args:
            message: Error message
            app_config: Application configuration that failed
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, "app_creation", error_code, details)
        self.app_config = app_config or {}


class MiddlewareSetupError(FactoryError):
    """Exception raised when middleware setup fails."""
    
    def __init__(
        self,
        message: str,
        middleware_type: Optional[str] = None,
        middleware_config: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize middleware setup error.
        
        Args:
            message: Error message
            middleware_type: Type of middleware that failed
            middleware_config: Middleware configuration
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, "middleware_setup", error_code, details)
        self.middleware_type = middleware_type
        self.middleware_config = middleware_config or {}


class CommandRegistrationError(FactoryError):
    """Exception raised when command registration fails."""
    
    def __init__(
        self,
        message: str,
        command_name: Optional[str] = None,
        command_class: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize command registration error.
        
        Args:
            message: Error message
            command_name: Name of command that failed to register
            command_class: Command class that failed
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, "command_registration", error_code, details)
        self.command_name = command_name
        self.command_class = command_class
```

### ai_admin/core/app_factory.py
```python
"""Application factory for creating and configuring AI Admin FastAPI application."""

import os
import logging
from typing import Dict, Any, List, Optional, Type, Callable
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp_proxy_adapter.core.logging import get_logger
from ai_admin.settings_manager import get_settings_manager
from ai_admin.config.ssl_config import SSLConfig
from ai_admin.middleware.mtls_roles_middleware import MTLSRolesMiddleware
from .factory_exceptions import (
    FactoryError,
    AppCreationError,
    MiddlewareSetupError,
    CommandRegistrationError
)


class AppFactory:
    """Factory for creating and configuring AI Admin FastAPI application."""
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        settings_manager: Optional[Any] = None
    ):
        """
        Initialize application factory.
        
        Args:
            config_path: Path to configuration file
            settings_manager: Settings manager instance
        """
        pass
    
    def create_app(
        self,
        app_name: str = "AI Admin",
        app_version: str = "1.0.0",
        description: str = "AI Admin API Server",
        custom_commands: Optional[List[Type]] = None,
        custom_middleware: Optional[List[Callable]] = None,
        enable_ssl: bool = True,
        enable_mtls: bool = True,
        enable_cors: bool = True
    ) -> FastAPI:
        """
        Create and configure FastAPI application.
        
        Args:
            app_name: Application name
            app_version: Application version
            description: Application description
            custom_commands: List of custom command classes
            custom_middleware: List of custom middleware functions
            enable_ssl: Whether to enable SSL support
            enable_mtls: Whether to enable mTLS support
            enable_cors: Whether to enable CORS support
            
        Returns:
            Configured FastAPI application
            
        Raises:
            AppCreationError: If application creation fails
            MiddlewareSetupError: If middleware setup fails
            CommandRegistrationError: If command registration fails
        """
        pass
    
    def _create_fastapi_app(
        self,
        app_name: str,
        app_version: str,
        description: str
    ) -> FastAPI:
        """
        Create basic FastAPI application.
        
        Args:
            app_name: Application name
            app_version: Application version
            description: Application description
            
        Returns:
            FastAPI application instance
        """
        pass
    
    def _setup_ssl_middleware(
        self,
        app: FastAPI,
        enable_ssl: bool,
        enable_mtls: bool
    ) -> None:
        """
        Setup SSL/mTLS middleware.
        
        Args:
            app: FastAPI application
            enable_ssl: Whether to enable SSL
            enable_mtls: Whether to enable mTLS
            
        Raises:
            MiddlewareSetupError: If middleware setup fails
        """
        pass
    
    def _setup_cors_middleware(
        self,
        app: FastAPI,
        enable_cors: bool
    ) -> None:
        """
        Setup CORS middleware.
        
        Args:
            app: FastAPI application
            enable_cors: Whether to enable CORS
        """
        pass
    
    def _setup_custom_middleware(
        self,
        app: FastAPI,
        custom_middleware: List[Callable]
    ) -> None:
        """
        Setup custom middleware.
        
        Args:
            app: FastAPI application
            custom_middleware: List of custom middleware functions
            
        Raises:
            MiddlewareSetupError: If middleware setup fails
        """
        pass
    
    def _register_commands(
        self,
        app: FastAPI,
        custom_commands: Optional[List[Type]] = None
    ) -> None:
        """
        Register commands with the application.
        
        Args:
            app: FastAPI application
            custom_commands: List of custom command classes
            
        Raises:
            CommandRegistrationError: If command registration fails
        """
        pass
    
    def _register_builtin_commands(self, app: FastAPI) -> None:
        """
        Register built-in commands.
        
        Args:
            app: FastAPI application
            
        Raises:
            CommandRegistrationError: If command registration fails
        """
        pass
    
    def _register_custom_commands(
        self,
        app: FastAPI,
        custom_commands: List[Type]
    ) -> None:
        """
        Register custom commands.
        
        Args:
            app: FastAPI application
            custom_commands: List of custom command classes
            
        Raises:
            CommandRegistrationError: If command registration fails
        """
        pass
    
    def _setup_routes(self, app: FastAPI) -> None:
        """
        Setup application routes.
        
        Args:
            app: FastAPI application
        """
        pass
    
    def _setup_health_endpoints(self, app: FastAPI) -> None:
        """
        Setup health check endpoints.
        
        Args:
            app: FastAPI application
        """
        pass
    
    def _setup_ssl_endpoints(self, app: FastAPI) -> None:
        """
        Setup SSL/mTLS related endpoints.
        
        Args:
            app: FastAPI application
        """
        pass
    
    def _configure_logging(self, app: FastAPI) -> None:
        """
        Configure application logging.
        
        Args:
            app: FastAPI application
        """
        pass
    
    def _validate_ssl_config(self) -> Tuple[bool, List[str]]:
        """
        Validate SSL configuration.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass
    
    def _get_ssl_config(self) -> SSLConfig:
        """
        Get SSL configuration.
        
        Returns:
            SSL configuration instance
        """
        pass
    
    def _create_mtls_middleware(
        self,
        ssl_config: SSLConfig
    ) -> MTLSRolesMiddleware:
        """
        Create mTLS roles middleware.
        
        Args:
            ssl_config: SSL configuration
            
        Returns:
            mTLS roles middleware instance
        """
        pass
    
    def _get_builtin_commands(self) -> List[Type]:
        """
        Get list of built-in command classes.
        
        Returns:
            List of built-in command classes
        """
        pass
    
    def _validate_command_class(self, command_class: Type) -> Tuple[bool, str]:
        """
        Validate command class.
        
        Args:
            command_class: Command class to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    def _get_app_config(self) -> Dict[str, Any]:
        """
        Get application configuration.
        
        Returns:
            Application configuration dictionary
        """
        pass
    
    def _setup_error_handlers(self, app: FastAPI) -> None:
        """
        Setup error handlers.
        
        Args:
            app: FastAPI application
        """
        pass
    
    def _setup_request_middleware(self, app: FastAPI) -> None:
        """
        Setup request processing middleware.
        
        Args:
            app: FastAPI application
        """
        pass
    
    def _setup_response_middleware(self, app: FastAPI) -> None:
        """
        Setup response processing middleware.
        
        Args:
            app: FastAPI application
        """
        pass
    
    def _get_middleware_config(self) -> Dict[str, Any]:
        """
        Get middleware configuration.
        
        Returns:
            Middleware configuration dictionary
        """
        pass
    
    def _validate_middleware_function(self, middleware_func: Callable) -> Tuple[bool, str]:
        """
        Validate middleware function.
        
        Args:
            middleware_func: Middleware function to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
```

### tests/test_app_factory.py
```python
"""Unit tests for AppFactory."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI
from ai_admin.core.app_factory import AppFactory
from ai_admin.core.factory_exceptions import (
    FactoryError,
    AppCreationError,
    MiddlewareSetupError,
    CommandRegistrationError
)


class TestAppFactory(unittest.TestCase):
    """Test cases for AppFactory class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = AppFactory()
    
    def test_init_default(self):
        """Test default initialization."""
        pass
    
    def test_init_with_config_path(self):
        """Test initialization with config path."""
        pass
    
    def test_init_with_settings_manager(self):
        """Test initialization with settings manager."""
        pass
    
    def test_create_app_basic(self):
        """Test basic application creation."""
        pass
    
    def test_create_app_with_custom_commands(self):
        """Test application creation with custom commands."""
        pass
    
    def test_create_app_with_custom_middleware(self):
        """Test application creation with custom middleware."""
        pass
    
    def test_create_app_ssl_disabled(self):
        """Test application creation with SSL disabled."""
        pass
    
    def test_create_app_mtls_disabled(self):
        """Test application creation with mTLS disabled."""
        pass
    
    def test_create_app_cors_disabled(self):
        """Test application creation with CORS disabled."""
        pass
    
    def test_create_fastapi_app(self):
        """Test FastAPI application creation."""
        pass
    
    def test_setup_ssl_middleware_enabled(self):
        """Test SSL middleware setup when enabled."""
        pass
    
    def test_setup_ssl_middleware_disabled(self):
        """Test SSL middleware setup when disabled."""
        pass
    
    def test_setup_ssl_middleware_mtls_enabled(self):
        """Test SSL middleware setup with mTLS enabled."""
        pass
    
    def test_setup_ssl_middleware_invalid_config(self):
        """Test SSL middleware setup with invalid configuration."""
        pass
    
    def test_setup_cors_middleware_enabled(self):
        """Test CORS middleware setup when enabled."""
        pass
    
    def test_setup_cors_middleware_disabled(self):
        """Test CORS middleware setup when disabled."""
        pass
    
    def test_setup_custom_middleware_success(self):
        """Test custom middleware setup success."""
        pass
    
    def test_setup_custom_middleware_invalid(self):
        """Test custom middleware setup with invalid middleware."""
        pass
    
    def test_register_commands_basic(self):
        """Test basic command registration."""
        pass
    
    def test_register_commands_with_custom(self):
        """Test command registration with custom commands."""
        pass
    
    def test_register_commands_invalid_class(self):
        """Test command registration with invalid command class."""
        pass
    
    def test_register_builtin_commands(self):
        """Test built-in command registration."""
        pass
    
    def test_register_custom_commands(self):
        """Test custom command registration."""
        pass
    
    def test_setup_routes(self):
        """Test route setup."""
        pass
    
    def test_setup_health_endpoints(self):
        """Test health endpoint setup."""
        pass
    
    def test_setup_ssl_endpoints(self):
        """Test SSL endpoint setup."""
        pass
    
    def test_configure_logging(self):
        """Test logging configuration."""
        pass
    
    def test_validate_ssl_config_valid(self):
        """Test SSL configuration validation with valid config."""
        pass
    
    def test_validate_ssl_config_invalid(self):
        """Test SSL configuration validation with invalid config."""
        pass
    
    def test_get_ssl_config(self):
        """Test SSL configuration retrieval."""
        pass
    
    def test_create_mtls_middleware(self):
        """Test mTLS middleware creation."""
        pass
    
    def test_get_builtin_commands(self):
        """Test built-in commands retrieval."""
        pass
    
    def test_validate_command_class_valid(self):
        """Test command class validation with valid class."""
        pass
    
    def test_validate_command_class_invalid(self):
        """Test command class validation with invalid class."""
        pass
    
    def test_get_app_config(self):
        """Test application configuration retrieval."""
        pass
    
    def test_setup_error_handlers(self):
        """Test error handler setup."""
        pass
    
    def test_setup_request_middleware(self):
        """Test request middleware setup."""
        pass
    
    def test_setup_response_middleware(self):
        """Test response middleware setup."""
        pass
    
    def test_get_middleware_config(self):
        """Test middleware configuration retrieval."""
        pass
    
    def test_validate_middleware_function_valid(self):
        """Test middleware function validation with valid function."""
        pass
    
    def test_validate_middleware_function_invalid(self):
        """Test middleware function validation with invalid function."""
        pass
```

### tests/test_factory_exceptions.py
```python
"""Unit tests for factory exceptions."""

import unittest
from ai_admin.core.factory_exceptions import (
    FactoryError,
    AppCreationError,
    MiddlewareSetupError,
    CommandRegistrationError
)


class TestFactoryError(unittest.TestCase):
    """Test cases for FactoryError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_factory_component(self):
        """Test initialization with factory component."""
        pass
    
    def test_init_with_error_code(self):
        """Test initialization with error code."""
        pass
    
    def test_init_with_details(self):
        """Test initialization with details."""
        pass


class TestAppCreationError(unittest.TestCase):
    """Test cases for AppCreationError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_app_config(self):
        """Test initialization with app config."""
        pass


class TestMiddlewareSetupError(unittest.TestCase):
    """Test cases for MiddlewareSetupError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_middleware_type(self):
        """Test initialization with middleware type."""
        pass
    
    def test_init_with_middleware_config(self):
        """Test initialization with middleware config."""
        pass


class TestCommandRegistrationError(unittest.TestCase):
    """Test cases for CommandRegistrationError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_command_name(self):
        """Test initialization with command name."""
        pass
    
    def test_init_with_command_class(self):
        """Test initialization with command class."""
        pass
```

## 📊 Метрики успешного завершения

### Специфичные метрики для данного шага:
- [ ] **Создан класс AppFactory** с всеми заявленными методами
- [ ] **Реализован метод create_app** - основная точка входа для создания приложения
- [ ] **Реализован метод _create_fastapi_app** - создает базовое FastAPI приложение
- [ ] **Реализован метод _setup_ssl_middleware** - настраивает SSL/mTLS middleware
- [ ] **Реализован метод _setup_cors_middleware** - настраивает CORS middleware
- [ ] **Реализован метод _setup_custom_middleware** - настраивает пользовательские middleware
- [ ] **Реализован метод _register_commands** - регистрирует команды
- [ ] **Реализован метод _register_builtin_commands** - регистрирует встроенные команды
- [ ] **Реализован метод _register_custom_commands** - регистрирует пользовательские команды
- [ ] **Реализован метод _setup_routes** - настраивает маршруты
- [ ] **Реализован метод _setup_health_endpoints** - настраивает эндпоинты здоровья
- [ ] **Реализован метод _setup_ssl_endpoints** - настраивает SSL эндпоинты
- [ ] **Реализован метод _configure_logging** - настраивает логирование
- [ ] **Реализованы все вспомогательные методы** (_validate_ssl_config, _get_ssl_config, etc.)
- [ ] **Написаны unit-тесты** с покрытием не менее 90%
- [ ] **Создан файл factory_exceptions.py** с иерархией исключений
- [ ] **Создан пакет ai_admin/core** с правильной инициализацией
- [ ] **Фабрика интегрируется с SSLConfig** для настройки SSL/mTLS
- [ ] **Фабрика интегрируется с MTLSRolesMiddleware** для проверки ролей
- [ ] **Поддерживается регистрация пользовательских команд** и middleware
- [ ] **Реализована валидация конфигурации** с детальными сообщениями об ошибках
- [ ] **Поддерживается настройка всех типов middleware** (SSL, CORS, пользовательские)
- [ ] **Документация методов** содержит полные docstrings с типами и описаниями
- [ ] **Код проходит линтеры** (flake8, mypy, black)
- [ ] **Тесты проходят успешно** (pytest)
- [ ] **Фабрика создает полностью функциональное FastAPI приложение**

### Общие метрики успеха:
- [ ] **Код ВСЕХ шагов с номером таким же, или ниже в плане реализован ПОЛНОСТЬЮ**
- [ ] **Прошел проверку на отсутствие ошибок инструментами**
- [ ] **Покрытие КАЖДОГО файла проекта, котороый относится к уже пройденным шагам не ниже 90%+**
- [ ] **После написания кода была проведена ПОЛНАЯ и тщательная проверка на наличие нереализованного кода**
- [ ] **В коде отсутсвтует хардкод**

## 🔗 Связанные шаги

- **Зависимости:** Шаг 2.1 (Расширение конфигурации)
- **Использует:** Шаг 1.1 (CertificateUtils), Шаг 1.2 (MTLSRolesMiddleware), Шаг 1.3 (MTLSRolesCommand), Шаг 1.4 (SSLSetupCommand)
- **Используется в:** Шаг 3.1 (Модификация server.py), Шаг 3.3 (Интеграция SSL/mTLS)

## 📚 Дополнительные ресурсы

- [FastAPI Application Factory Pattern](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Factory Pattern in Python](https://realpython.com/factory-method-python/)
- [Application Configuration Management](https://12factor.net/config)
