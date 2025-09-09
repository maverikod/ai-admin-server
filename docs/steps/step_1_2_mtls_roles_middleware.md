# Шаг 1.2: Создание middleware для проверки ролей

**Зависимости:** Нет  
**Приоритет:** Высокий  
**Время:** 3-4 часа  
**Этап:** 1 (Независимые шаги)

## 📋 Задача шага

Создать middleware для автоматической проверки ролей в mTLS соединениях. Middleware должен извлекать клиентские сертификаты из SSL контекста, извлекать роли из сертификатов и валидировать доступ на основе ролевой конфигурации.

## 📁 Файлы изменений

### Создаваемые файлы:
- `ai_admin/middleware/__init__.py` - инициализация пакета middleware
- `ai_admin/middleware/mtls_roles_middleware.py` - middleware для проверки ролей
- `ai_admin/middleware/middleware_exceptions.py` - исключения для middleware
- `tests/test_mtls_roles_middleware.py` - unit-тесты для middleware
- `tests/test_middleware_exceptions.py` - unit-тесты для исключений

### Модифицируемые файлы:
- Нет

## 🔧 Описание изменений

### 1. Создание пакета middleware
Создать новый пакет `ai_admin/middleware` для размещения middleware компонентов.

### 2. Реализация MTLSRolesMiddleware
Создать класс `MTLSRolesMiddleware` с функциональностью:
- Извлечение клиентских сертификатов из SSL контекста
- Извлечение ролей из сертификатов
- Валидация доступа на основе ролевой конфигурации
- Обработка запросов без сертификатов
- Логирование событий аутентификации

### 3. Создание исключений
Создать отдельный файл с исключениями для middleware:
- `MiddlewareError` - базовое исключение для middleware
- `RoleValidationError` - ошибки валидации ролей
- `CertificateExtractionError` - ошибки извлечения сертификатов
- `AccessDeniedError` - ошибки отказа в доступе

### 4. Создание unit-тестов
Написать comprehensive unit-тесты для всех методов middleware и исключений.

## 💻 Декларативный код

### ai_admin/middleware/__init__.py
```python
"""AI Admin middleware package."""

from .mtls_roles_middleware import MTLSRolesMiddleware
from .middleware_exceptions import (
    MiddlewareError,
    RoleValidationError,
    CertificateExtractionError,
    AccessDeniedError
)

__all__ = [
    "MTLSRolesMiddleware",
    "MiddlewareError",
    "RoleValidationError",
    "CertificateExtractionError",
    "AccessDeniedError"
]
```

### ai_admin/middleware/middleware_exceptions.py
```python
"""Middleware-related exceptions for AI Admin."""

from typing import Optional, Dict, Any, List


class MiddlewareError(Exception):
    """Base exception for middleware-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize middleware error.
        
        Args:
            message: Error message
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class RoleValidationError(MiddlewareError):
    """Exception raised when role validation fails."""
    
    def __init__(
        self,
        message: str,
        client_roles: Optional[List[str]] = None,
        server_role: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize role validation error.
        
        Args:
            message: Error message
            client_roles: List of client roles
            server_role: Server role
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, error_code, details)
        self.client_roles = client_roles or []
        self.server_role = server_role


class CertificateExtractionError(MiddlewareError):
    """Exception raised when certificate extraction fails."""
    
    def __init__(
        self,
        message: str,
        extraction_type: str,
        scope_info: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize certificate extraction error.
        
        Args:
            message: Error message
            extraction_type: Type of extraction that failed
            scope_info: ASGI scope information
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, error_code, details)
        self.extraction_type = extraction_type
        self.scope_info = scope_info or {}


class AccessDeniedError(MiddlewareError):
    """Exception raised when access is denied."""
    
    def __init__(
        self,
        message: str,
        client_identifier: Optional[str] = None,
        requested_resource: Optional[str] = None,
        reason: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize access denied error.
        
        Args:
            message: Error message
            client_identifier: Client identifier
            requested_resource: Requested resource
            reason: Reason for denial
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, error_code, details)
        self.client_identifier = client_identifier
        self.requested_resource = requested_resource
        self.reason = reason
```

### ai_admin/middleware/mtls_roles_middleware.py
```python
"""mTLS Roles Middleware for role-based certificate validation."""

import json
import ssl
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import ExtensionOID
from mcp_proxy_adapter.core.logging import get_logger
from .middleware_exceptions import (
    MiddlewareError,
    RoleValidationError,
    CertificateExtractionError,
    AccessDeniedError
)


class MTLSRolesMiddleware:
    """Middleware for validating mTLS client certificates based on roles."""
    
    def __init__(
        self,
        app: Callable,
        roles_config_path: str,
        default_policy: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize mTLS roles middleware.
        
        Args:
            app: ASGI application
            roles_config_path: Path to roles configuration file
            default_policy: Default access policy if roles config not found
        """
        pass
    
    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: Callable,
        send: Callable
    ) -> None:
        """
        Process ASGI request with role validation.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        pass
    
    def _load_roles_config(self) -> Optional[Dict[str, Any]]:
        """
        Load roles configuration from file.
        
        Returns:
            Roles configuration dictionary or None if not found
        """
        pass
    
    def _extract_client_certificate(
        self,
        scope: Dict[str, Any]
    ) -> Optional[x509.Certificate]:
        """
        Extract client certificate from SSL context in ASGI scope.
        
        Args:
            scope: ASGI scope dictionary
            
        Returns:
            Client certificate object or None if not found
        """
        pass
    
    def _extract_roles_from_certificate(
        self,
        cert: x509.Certificate
    ) -> List[str]:
        """
        Extract roles from certificate extensions.
        
        Args:
            cert: X.509 certificate object
            
        Returns:
            List of roles extracted from certificate
        """
        pass
    
    def _validate_role_access(
        self,
        client_roles: List[str],
        scope: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validate if client roles have access to the requested endpoint.
        
        Args:
            client_roles: List of client roles
            scope: ASGI scope with request information
            
        Returns:
            Tuple of (access_granted, reason)
        """
        pass
    
    def _extract_server_role(
        self,
        scope: Dict[str, Any]
    ) -> str:
        """
        Extract server role from request context.
        
        Args:
            scope: ASGI scope with request information
            
        Returns:
            Server role identifier
        """
        pass
    
    def _get_endpoint_permissions(
        self,
        path: str,
        method: str
    ) -> List[str]:
        """
        Get required permissions for endpoint.
        
        Args:
            path: Request path
            method: HTTP method
            
        Returns:
            List of required permissions
        """
        pass
    
    async def _send_unauthorized_response(
        self,
        send: Callable,
        reason: str,
        status_code: int = 403
    ) -> None:
        """
        Send unauthorized response to client.
        
        Args:
            send: ASGI send callable
            reason: Reason for denial
            status_code: HTTP status code
        """
        pass
    
    def _log_access_attempt(
        self,
        client_roles: List[str],
        server_role: str,
        path: str,
        method: str,
        granted: bool,
        reason: str
    ) -> None:
        """
        Log access attempt for audit purposes.
        
        Args:
            client_roles: Client roles
            server_role: Server role
            path: Request path
            method: HTTP method
            granted: Whether access was granted
            reason: Reason for decision
        """
        pass
    
    def _is_public_endpoint(
        self,
        path: str,
        method: str
    ) -> bool:
        """
        Check if endpoint is public and doesn't require authentication.
        
        Args:
            path: Request path
            method: HTTP method
            
        Returns:
            True if endpoint is public
        """
        pass
    
    def _get_client_identifier(
        self,
        cert: x509.Certificate
    ) -> str:
        """
        Get client identifier from certificate.
        
        Args:
            cert: Client certificate
            
        Returns:
            Client identifier string
        """
        pass
    
    def _validate_certificate_chain(
        self,
        cert: x509.Certificate
    ) -> bool:
        """
        Validate client certificate chain.
        
        Args:
            cert: Client certificate
            
        Returns:
            True if certificate chain is valid
        """
        pass
    
    def _check_certificate_expiry(
        self,
        cert: x509.Certificate
    ) -> bool:
        """
        Check if certificate is not expired.
        
        Args:
            cert: Client certificate
            
        Returns:
            True if certificate is not expired
        """
        pass
    
    def _get_roles_config_for_client(
        self,
        client_roles: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Get roles configuration for specific client roles.
        
        Args:
            client_roles: List of client roles
            
        Returns:
            Roles configuration for client or None
        """
        pass
    
    def _check_permission_hierarchy(
        self,
        client_roles: List[str],
        required_permissions: List[str]
    ) -> bool:
        """
        Check if client roles have required permissions.
        
        Args:
            client_roles: List of client roles
            required_permissions: List of required permissions
            
        Returns:
            True if client has required permissions
        """
        pass
```

### tests/test_mtls_roles_middleware.py
```python
"""Unit tests for MTLSRolesMiddleware."""

import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from ai_admin.middleware.mtls_roles_middleware import MTLSRolesMiddleware
from ai_admin.middleware.middleware_exceptions import (
    MiddlewareError,
    RoleValidationError,
    CertificateExtractionError,
    AccessDeniedError
)


class TestMTLSRolesMiddleware(unittest.TestCase):
    """Test cases for MTLSRolesMiddleware class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.roles_config_path = f"{self.temp_dir}/roles.json"
        self.app_mock = Mock()
        self.create_test_roles_config()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_roles_config(self):
        """Create test roles configuration file."""
        roles_config = {
            "admin": {
                "description": "Administrator role",
                "permissions": ["read", "write", "execute", "delete", "admin"],
                "allowed_servers": ["*"]
            },
            "user": {
                "description": "User role",
                "permissions": ["read", "execute"],
                "allowed_servers": ["api", "monitor"]
            },
            "readonly": {
                "description": "Read-only role",
                "permissions": ["read"],
                "allowed_servers": ["monitor"]
            }
        }
        
        with open(self.roles_config_path, 'w') as f:
            json.dump(roles_config, f)
    
    def test_init_with_valid_config(self):
        """Test middleware initialization with valid config."""
        pass
    
    def test_init_with_missing_config(self):
        """Test middleware initialization with missing config file."""
        pass
    
    def test_extract_client_certificate_success(self):
        """Test successful client certificate extraction."""
        pass
    
    def test_extract_client_certificate_no_ssl(self):
        """Test client certificate extraction when no SSL context."""
        pass
    
    def test_extract_roles_from_certificate_custom_extension(self):
        """Test role extraction from custom extension."""
        pass
    
    def test_extract_roles_from_certificate_san_fallback(self):
        """Test role extraction from SAN as fallback."""
        pass
    
    def test_validate_role_access_admin_full_access(self):
        """Test role access validation for admin role."""
        pass
    
    def test_validate_role_access_user_limited_access(self):
        """Test role access validation for user role."""
        pass
    
    def test_validate_role_access_readonly_restricted(self):
        """Test role access validation for readonly role."""
        pass
    
    def test_validate_role_access_no_roles(self):
        """Test role access validation with no roles."""
        pass
    
    def test_extract_server_role_from_path(self):
        """Test server role extraction from request path."""
        pass
    
    def test_get_endpoint_permissions(self):
        """Test endpoint permissions extraction."""
        pass
    
    def test_send_unauthorized_response(self):
        """Test unauthorized response sending."""
        pass
    
    def test_log_access_attempt(self):
        """Test access attempt logging."""
        pass
    
    def test_is_public_endpoint(self):
        """Test public endpoint detection."""
        pass
    
    def test_get_client_identifier(self):
        """Test client identifier extraction."""
        pass
    
    def test_validate_certificate_chain(self):
        """Test certificate chain validation."""
        pass
    
    def test_check_certificate_expiry(self):
        """Test certificate expiry check."""
        pass
    
    def test_get_roles_config_for_client(self):
        """Test roles configuration retrieval for client."""
        pass
    
    def test_check_permission_hierarchy(self):
        """Test permission hierarchy check."""
        pass
```

### tests/test_middleware_exceptions.py
```python
"""Unit tests for middleware exceptions."""

import unittest
from ai_admin.middleware.middleware_exceptions import (
    MiddlewareError,
    RoleValidationError,
    CertificateExtractionError,
    AccessDeniedError
)


class TestMiddlewareError(unittest.TestCase):
    """Test cases for MiddlewareError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_error_code(self):
        """Test initialization with error code."""
        pass
    
    def test_init_with_details(self):
        """Test initialization with details."""
        pass


class TestRoleValidationError(unittest.TestCase):
    """Test cases for RoleValidationError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_roles(self):
        """Test initialization with client and server roles."""
        pass


class TestCertificateExtractionError(unittest.TestCase):
    """Test cases for CertificateExtractionError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_scope_info(self):
        """Test initialization with scope information."""
        pass


class TestAccessDeniedError(unittest.TestCase):
    """Test cases for AccessDeniedError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_client_info(self):
        """Test initialization with client information."""
        pass
```
    
    def test_asgi_call_success(self):
        """Test successful ASGI call processing."""
        pass
    
    def test_asgi_call_unauthorized(self):
        """Test unauthorized ASGI call processing."""
        pass
    
    def test_asgi_call_public_endpoint(self):
        """Test public endpoint ASGI call processing."""
        pass
```

## 📊 Метрики успешного завершения

### Специфичные метрики для данного шага:
- [ ] **Создан класс MTLSRolesMiddleware** с всеми заявленными методами
- [ ] **Реализован метод __call__** - обрабатывает ASGI запросы с валидацией ролей
- [ ] **Реализован метод _extract_client_certificate** - извлекает сертификаты из SSL контекста
- [ ] **Реализован метод _extract_roles_from_certificate** - извлекает роли из сертификатов
- [ ] **Реализован метод _validate_role_access** - валидирует доступ на основе ролей
- [ ] **Реализован метод _extract_server_role** - определяет роль сервера из запроса
- [ ] **Реализован метод _get_endpoint_permissions** - определяет требуемые разрешения
- [ ] **Реализован метод _send_unauthorized_response** - отправляет ответ об отказе в доступе
- [ ] **Реализован метод _log_access_attempt** - логирует попытки доступа
- [ ] **Реализован метод _is_public_endpoint** - определяет публичные эндпоинты
- [ ] **Реализованы все вспомогательные методы** (_get_client_identifier, _validate_certificate_chain, etc.)
- [ ] **Написаны unit-тесты** с покрытием не менее 90%
- [ ] **Создан пакет ai_admin/middleware** с правильной инициализацией
- [ ] **Создан файл middleware_exceptions.py** с иерархией исключений
- [ ] **Middleware корректно обрабатывает ASGI протокол**
- [ ] **Поддерживается загрузка конфигурации ролей из JSON файла**
- [ ] **Реализована валидация цепочки сертификатов**
- [ ] **Реализована проверка срока действия сертификатов**
- [ ] **Документация методов** содержит полные docstrings с типами и описаниями
- [ ] **Код проходит линтеры** (flake8, mypy, black)
- [ ] **Тесты проходят успешно** (pytest)
- [ ] **Middleware интегрируется с FastAPI/ASGI приложениями**

### Общие метрики успеха:
- [ ] **Код ВСЕХ шагов с номером таким же, или ниже в плане реализован ПОЛНОСТЬЮ**
- [ ] **Прошел проверку на отсутствие ошибок инструментами**
- [ ] **Покрытие КАЖДОГО файла проекта, котороый относится к уже пройденным шагам не ниже 90%+**
- [ ] **После написания кода была проведена ПОЛНАЯ и тщательная проверка на наличие нереализованного кода**
- [ ] **В коде отсутсвтует хардкод**

## 🔗 Связанные шаги

- **Зависимости:** Нет
- **Используется в:** Шаг 2.1 (Расширение конфигурации), Шаг 2.2 (Фабричный метод), Шаг 3.1 (Модификация server.py), Шаг 3.3 (Интеграция SSL/mTLS)

## 📚 Дополнительные ресурсы

- [ASGI Specification](https://asgi.readthedocs.io/en/latest/specs/main.html)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [X.509 Certificate Extensions](https://tools.ietf.org/html/rfc5280#section-4.2)
- [Role-Based Access Control](https://en.wikipedia.org/wiki/Role-based_access_control)
