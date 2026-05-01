# Feature Request: Расширяемая система адаптеров безопасности для mcp_security_framework

## Обзор

Запрос на добавление универсальных механизмов расширения в `mcp_security_framework` для поддержки кастомных адаптеров безопасности в проектах, использующих фреймворк.

## Проблема

Текущая версия `mcp_security_framework-1.5.1` предоставляет базовые компоненты безопасности (аутентификация, авторизация, SSL/TLS, rate limiting), но не поддерживает:

1. **Расширяемую систему адаптеров** - проекты не могут создавать свои адаптеры безопасности для специфичных операций
2. **Унифицированный интерфейс** - нет базового класса для создания адаптеров
3. **Контекст операций** - нет механизма передачи контекста (user_id, request_id, metadata)
4. **Структурированный аудит** - текущий аудит не поддерживает структурированное логирование
5. **Интеграцию с legacy-адаптерами** - нет механизма миграции существующих адаптеров

## Предлагаемое решение

Добавить универсальные компоненты, которые позволят проектам создавать свои адаптеры безопасности:

### 1. Базовый класс SecurityAdapter

**Файл:** `mcp_security_framework/core/security_adapter.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum

class OperationType(Enum):
    """Базовый класс для типов операций.
    
    Проекты создают свои типы операций, наследуясь от этого класса.
    """
    pass

class SecurityAdapter(ABC):
    """
    Базовый класс для адаптеров безопасности.
    
    Все адаптеры безопасности в проектах должны наследоваться от этого класса
    и реализовывать стандартные методы.
    
    Пример использования в проекте:
        class FtpOperation(OperationType):
            UPLOAD = "ftp:upload"
            DOWNLOAD = "ftp:download"
        
        class FtpSecurityAdapter(SecurityAdapter):
            operation_type = FtpOperation
            
            def validate_operation(self, operation, user_roles, params):
                # Реализация валидации
                pass
    """
    
    @property
    @abstractmethod
    def operation_type(self) -> type[OperationType]:
        """Тип операций, поддерживаемых адаптером."""
        pass
    
    @abstractmethod
    def validate_operation(
        self,
        operation: OperationType,
        user_roles: List[str],
        params: Optional[Dict[str, Any]] = None,
        context: Optional["OperationContext"] = None
    ) -> Tuple[bool, str]:
        """
        Валидация операции.
        
        Args:
            operation: Тип операции
            user_roles: Роли пользователя
            params: Параметры операции
            context: Контекст операции (опционально)
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def check_permissions(
        self,
        user_roles: List[str],
        required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Проверка разрешений.
        
        Args:
            user_roles: Роли пользователя
            required_permissions: Требуемые разрешения
            
        Returns:
            Tuple[bool, List[str]]: (has_permission, missing_permissions)
        """
        pass
    
    @abstractmethod
    def audit_operation(
        self,
        operation: OperationType,
        user_roles: List[str],
        params: Optional[Dict[str, Any]] = None,
        status: str = "success",
        context: Optional["OperationContext"] = None
    ) -> None:
        """
        Аудит операции.
        
        Args:
            operation: Тип операции
            user_roles: Роли пользователя
            params: Параметры операции
            status: Статус операции (success, failed, denied)
            context: Контекст операции (опционально)
        """
        pass
```

### 2. Регистрация адаптеров в SecurityManager

**Файл:** `mcp_security_framework/core/security_manager.py` (дополнение)

```python
class SecurityManager:
    def __init__(self, config: SecurityConfig):
        # ... существующий код ...
        self._adapters: Dict[str, SecurityAdapter] = {}
    
    def register_adapter(
        self,
        name: str,
        adapter: SecurityAdapter
    ) -> None:
        """
        Регистрация адаптера безопасности.
        
        Проекты могут регистрировать свои адаптеры для специфичных операций.
        
        Args:
            name: Имя адаптера (например, "ftp", "docker", "k8s")
            adapter: Экземпляр адаптера, наследующегося от SecurityAdapter
            
        Example:
            >>> from mcp_security_framework import SecurityManager, SecurityAdapter
            >>> 
            >>> class MyAdapter(SecurityAdapter):
            ...     # реализация
            ...     pass
            >>> 
            >>> security_manager = SecurityManager(config)
            >>> security_manager.register_adapter("my_adapter", MyAdapter(...))
        """
        if not isinstance(adapter, SecurityAdapter):
            raise TypeError(
                f"Adapter must be an instance of SecurityAdapter, "
                f"got {type(adapter)}"
            )
        self._adapters[name] = adapter
        self.logger.info(f"Registered security adapter: {name}")
    
    def get_adapter(self, name: str) -> Optional[SecurityAdapter]:
        """
        Получить адаптер по имени.
        
        Args:
            name: Имя адаптера
            
        Returns:
            SecurityAdapter или None, если адаптер не найден
        """
        return self._adapters.get(name)
    
    def validate_operation(
        self,
        adapter_name: str,
        operation: OperationType,
        user_roles: List[str],
        params: Optional[Dict[str, Any]] = None,
        context: Optional["OperationContext"] = None
    ) -> Tuple[bool, str]:
        """
        Валидация операции через адаптер.
        
        Args:
            adapter_name: Имя адаптера
            operation: Тип операции
            user_roles: Роли пользователя
            params: Параметры операции
            context: Контекст операции (опционально)
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
            
        Raises:
            ValueError: Если адаптер не найден
        """
        adapter = self.get_adapter(adapter_name)
        if not adapter:
            raise ValueError(f"Adapter '{adapter_name}' not found")
        
        return adapter.validate_operation(operation, user_roles, params, context)
    
    def list_adapters(self) -> List[str]:
        """
        Получить список зарегистрированных адаптеров.
        
        Returns:
            Список имен адаптеров
        """
        return list(self._adapters.keys())
```

### 3. Контекст операций

**Файл:** `mcp_security_framework/schemas/operation_context.py` (новый файл)

```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

@dataclass
class OperationContext:
    """
    Контекст операции для передачи дополнительной информации.
    
    Используется для передачи контекста между операциями безопасности,
    поддержки вложенных операций и трекинга цепочки операций.
    
    Example:
        >>> context = OperationContext(
        ...     user_id="user123",
        ...     user_roles=["ftp:upload", "docker:pull"],
        ...     request_id="req456",
        ...     parent_operation="batch_upload",
        ...     metadata={"ip": "192.168.1.1", "user_agent": "..."}
        ... )
        >>> 
        >>> result = security_manager.validate_operation(
        ...     "ftp", FtpOperation.UPLOAD, context, params
        ... )
    """
    user_id: Optional[str] = None
    user_roles: List[str] = field(default_factory=list)
    request_id: Optional[str] = None
    parent_operation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сериализации."""
        return {
            "user_id": self.user_id,
            "user_roles": self.user_roles,
            "request_id": self.request_id,
            "parent_operation": self.parent_operation,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OperationContext":
        """Создание из словаря."""
        timestamp = data.get("timestamp")
        if timestamp and isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return cls(
            user_id=data.get("user_id"),
            user_roles=data.get("user_roles", []),
            request_id=data.get("request_id"),
            parent_operation=data.get("parent_operation"),
            metadata=data.get("metadata", {}),
            timestamp=timestamp or datetime.utcnow(),
        )
```

### 4. Структурированный аудит

**Файл:** `mcp_security_framework/core/audit_logger.py` (новый файл)

```python
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

class AuditStatus(Enum):
    """Статус операции в аудите."""
    SUCCESS = "success"
    FAILED = "failed"
    DENIED = "denied"
    PENDING = "pending"

@dataclass
class AuditEvent:
    """
    Событие аудита операции.
    
    Используется для структурированного логирования операций безопасности.
    """
    operation: str
    operation_type: str
    user_roles: List[str]
    params: Dict[str, Any]
    status: AuditStatus
    timestamp: datetime
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    context: Optional["OperationContext"] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для логирования."""
        result = {
            "operation": self.operation,
            "operation_type": self.operation_type,
            "user_roles": self.user_roles,
            "params": self.params,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "error_message": self.error_message,
            "metadata": self.metadata,
        }
        
        if self.context:
            result["context"] = self.context.to_dict()
        
        return result

class AuditLogger:
    """
    Логгер для аудита операций безопасности.
    
    Поддерживает разные бэкенды для логирования (file, database, elasticsearch и т.д.).
    
    Example:
        >>> audit_logger = AuditLogger(
        ...     backend="file",
        ...     config={"log_file": "/var/log/security_audit.log"}
        ... )
        >>> 
        >>> event = AuditEvent(
        ...     operation="ftp:upload",
        ...     operation_type="FtpOperation",
        ...     user_roles=["ftp:upload"],
        ...     params={"remote_path": "/files/test.txt"},
        ...     status=AuditStatus.SUCCESS,
        ...     timestamp=datetime.utcnow()
        ... )
        >>> 
        >>> audit_logger.log(event)
    """
    
    def __init__(
        self,
        backend: str = "file",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Инициализация логгера аудита.
        
        Args:
            backend: Тип бэкенда ("file", "database", "elasticsearch", "console")
            config: Конфигурация бэкенда
        """
        self.backend = backend
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{backend}")
        
        # Инициализация бэкенда
        self._initialize_backend()
    
    def _initialize_backend(self) -> None:
        """Инициализация бэкенда логирования."""
        if self.backend == "file":
            log_file = self.config.get("log_file", "/var/log/security_audit.log")
            handler = logging.FileHandler(log_file)
            handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
            self.logger.addHandler(handler)
        elif self.backend == "console":
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
            self.logger.addHandler(handler)
        # Другие бэкенды (database, elasticsearch) реализуются по необходимости
    
    def log(self, event: AuditEvent) -> None:
        """
        Логирование события аудита.
        
        Args:
            event: Событие аудита
        """
        event_dict = event.to_dict()
        
        if self.backend in ("file", "console"):
            # JSON логирование для структурированных логов
            import json
            self.logger.info(json.dumps(event_dict))
        else:
            # Другие бэкенды реализуются по необходимости
            self.logger.info(f"Audit event: {event_dict}")
    
    def log_operation(
        self,
        operation: str,
        operation_type: str,
        user_roles: List[str],
        params: Dict[str, Any],
        status: AuditStatus,
        error_message: Optional[str] = None,
        context: Optional["OperationContext"] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Удобный метод для логирования операции.
        
        Args:
            operation: Название операции
            operation_type: Тип операции
            user_roles: Роли пользователя
            params: Параметры операции
            status: Статус операции
            error_message: Сообщение об ошибке (если есть)
            context: Контекст операции
            metadata: Дополнительные метаданные
        """
        event = AuditEvent(
            operation=operation,
            operation_type=operation_type,
            user_roles=user_roles,
            params=params,
            status=status,
            timestamp=datetime.utcnow(),
            error_message=error_message,
            context=context,
            metadata=metadata or {}
        )
        self.log(event)
```

### 5. Адаптер-обертка для legacy-адаптеров

**Файл:** `mcp_security_framework/core/adapter_wrapper.py` (новый файл)

```python
from typing import Any, Dict, List, Tuple, Optional, Callable
from .security_adapter import SecurityAdapter, OperationType
from ..schemas.operation_context import OperationContext

class SecurityAdapterWrapper(SecurityAdapter):
    """
    Обертка для существующих (legacy) адаптеров безопасности.
    
    Позволяет использовать существующие адаптеры проектов
    через унифицированный интерфейс SecurityAdapter.
    
    Example:
        >>> from ai_admin.security.ftp_security_adapter import FtpSecurityAdapter
        >>> 
        >>> legacy_adapter = FtpSecurityAdapter()
        >>> 
        >>> wrapper = SecurityAdapterWrapper(
        ...     legacy_adapter=legacy_adapter,
        ...     operation_type=FtpOperation,
        ...     validate_method=lambda op, roles, params: legacy_adapter.validate_ftp_operation(op, roles, params),
        ...     check_permissions_method=lambda roles, perms: legacy_adapter.check_ftp_permissions(roles, perms),
        ...     audit_method=lambda op, roles, params, status: legacy_adapter.audit_ftp_operation(op, roles, params, status)
        ... )
        >>> 
        >>> security_manager.register_adapter("ftp", wrapper)
    """
    
    def __init__(
        self,
        legacy_adapter: Any,
        operation_type: type[OperationType],
        validate_method: Optional[Callable] = None,
        check_permissions_method: Optional[Callable] = None,
        audit_method: Optional[Callable] = None
    ):
        """
        Инициализация обертки.
        
        Args:
            legacy_adapter: Существующий адаптер из проекта
            operation_type: Тип операций адаптера
            validate_method: Метод для валидации (опционально, будет определен автоматически)
            check_permissions_method: Метод для проверки разрешений (опционально)
            audit_method: Метод для аудита (опционально)
        """
        self._adapter = legacy_adapter
        self._operation_type = operation_type
        self._validate_method = validate_method
        self._check_permissions_method = check_permissions_method
        self._audit_method = audit_method
        
        # Автоматическое определение методов, если не указаны
        if not self._validate_method:
            self._validate_method = self._find_method("validate")
        if not self._check_permissions_method:
            self._check_permissions_method = self._find_method("check_permissions")
        if not self._audit_method:
            self._audit_method = self._find_method("audit")
    
    @property
    def operation_type(self) -> type[OperationType]:
        return self._operation_type
    
    def _find_method(self, prefix: str) -> Optional[Callable]:
        """Поиск метода в legacy-адаптере по префиксу."""
        adapter_name = self._adapter.__class__.__name__.lower()
        # Удаляем "securityadapter" из имени класса
        adapter_name = adapter_name.replace("securityadapter", "").replace("adapter", "")
        
        # Пробуем разные варианты имен методов
        method_names = [
            f"{prefix}_{adapter_name}_operation",
            f"{prefix}_{adapter_name}",
            f"{prefix}_operation",
        ]
        
        for method_name in method_names:
            if hasattr(self._adapter, method_name):
                return getattr(self._adapter, method_name)
        
        return None
    
    def validate_operation(
        self,
        operation: OperationType,
        user_roles: List[str],
        params: Optional[Dict[str, Any]] = None,
        context: Optional[OperationContext] = None
    ) -> Tuple[bool, str]:
        """Валидация операции через legacy-адаптер."""
        if self._validate_method:
            # Пробуем вызвать с контекстом, если поддерживается
            try:
                if context:
                    return self._validate_method(operation, user_roles, params, context)
                else:
                    return self._validate_method(operation, user_roles, params)
            except TypeError:
                # Если метод не поддерживает контекст, вызываем без него
                return self._validate_method(operation, user_roles, params)
        
        # Fallback: пробуем стандартные методы
        if hasattr(self._adapter, "validate_operation"):
            return self._adapter.validate_operation(operation, user_roles, params)
        
        raise NotImplementedError(
            f"Cannot find validate method in {self._adapter.__class__.__name__}"
        )
    
    def check_permissions(
        self,
        user_roles: List[str],
        required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """Проверка разрешений через legacy-адаптер."""
        if self._check_permissions_method:
            return self._check_permissions_method(user_roles, required_permissions)
        
        # Fallback
        if hasattr(self._adapter, "check_permissions"):
            return self._adapter.check_permissions(user_roles, required_permissions)
        
        raise NotImplementedError(
            f"Cannot find check_permissions method in {self._adapter.__class__.__name__}"
        )
    
    def audit_operation(
        self,
        operation: OperationType,
        user_roles: List[str],
        params: Optional[Dict[str, Any]] = None,
        status: str = "success",
        context: Optional[OperationContext] = None
    ) -> None:
        """Аудит операции через legacy-адаптер."""
        if self._audit_method:
            try:
                if context:
                    return self._audit_method(operation, user_roles, params, status, context)
                else:
                    return self._audit_method(operation, user_roles, params, status)
            except TypeError:
                return self._audit_method(operation, user_roles, params, status)
        
        # Fallback
        if hasattr(self._adapter, "audit_operation"):
            return self._adapter.audit_operation(operation, user_roles, params, status)
        
        # Если метод не найден, просто логируем
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Cannot find audit method in {self._adapter.__class__.__name__}, "
            f"skipping audit"
        )
```

### 6. Обновление __init__.py

**Файл:** `mcp_security_framework/__init__.py` (дополнение)

```python
# Добавить в экспорты:
from .core.security_adapter import SecurityAdapter, OperationType
from .schemas.operation_context import OperationContext
from .core.audit_logger import AuditLogger, AuditEvent, AuditStatus
from .core.adapter_wrapper import SecurityAdapterWrapper

__all__ = [
    # ... существующие экспорты ...
    # Новые экспорты:
    "SecurityAdapter",
    "OperationType",
    "OperationContext",
    "AuditLogger",
    "AuditEvent",
    "AuditStatus",
    "SecurityAdapterWrapper",
]
```

## Примеры использования

### Пример 1: Создание кастомного адаптера в проекте

```python
# В проекте: ai_admin/security/ftp_security_adapter.py
from mcp_security_framework import SecurityAdapter, OperationType, PermissionManager
from enum import Enum

class FtpOperation(OperationType):
    UPLOAD = "ftp:upload"
    DOWNLOAD = "ftp:download"
    LIST = "ftp:list"
    DELETE = "ftp:delete"

class FtpSecurityAdapter(SecurityAdapter):
    operation_type = FtpOperation
    
    def __init__(self, permission_manager: PermissionManager):
        self.permission_manager = permission_manager
        self.operation_permissions = {
            FtpOperation.UPLOAD: ["ftp:upload", "ftp:admin"],
            FtpOperation.DOWNLOAD: ["ftp:download", "ftp:admin"],
            # ...
        }
    
    def validate_operation(self, operation, user_roles, params, context=None):
        required_perms = self.operation_permissions.get(operation, [])
        result = self.permission_manager.validate_access(user_roles, required_perms)
        return result.is_valid, result.error_message or ""
    
    def check_permissions(self, user_roles, required_permissions):
        result = self.permission_manager.validate_access(user_roles, required_permissions)
        return result.is_valid, list(result.missing_permissions)
    
    def audit_operation(self, operation, user_roles, params, status, context=None):
        # Логирование через AuditLogger
        pass

# Регистрация в проекте:
from mcp_security_framework import SecurityManager

security_manager = SecurityManager(config)
security_manager.register_adapter("ftp", FtpSecurityAdapter(permission_manager))
```

### Пример 2: Использование контекста операций

```python
from mcp_security_framework import OperationContext, SecurityManager

context = OperationContext(
    user_id="user123",
    user_roles=["ftp:upload"],
    request_id="req456",
    parent_operation="batch_upload",
    metadata={"ip": "192.168.1.1", "user_agent": "..."}
)

result = security_manager.validate_operation(
    "ftp", FtpOperation.UPLOAD, context.user_roles, params, context
)
```

### Пример 3: Использование AuditLogger

```python
from mcp_security_framework import AuditLogger, AuditEvent, AuditStatus

audit_logger = AuditLogger(backend="file", config={"log_file": "/var/log/audit.log"})

event = AuditEvent(
    operation="ftp:upload",
    operation_type="FtpOperation",
    user_roles=["ftp:upload"],
    params={"remote_path": "/files/test.txt"},
    status=AuditStatus.SUCCESS,
    timestamp=datetime.utcnow()
)

audit_logger.log(event)
```

### Пример 4: Миграция legacy-адаптера

```python
from mcp_security_framework import SecurityAdapterWrapper
from ai_admin.security.ftp_security_adapter import FtpSecurityAdapter, FtpOperation

legacy_adapter = FtpSecurityAdapter()

wrapper = SecurityAdapterWrapper(
    legacy_adapter=legacy_adapter,
    operation_type=FtpOperation
)

security_manager.register_adapter("ftp", wrapper)
```

## Преимущества

1. **Универсальность** - все компоненты универсальны и не содержат специфичной для проекта логики
2. **Расширяемость** - проекты могут создавать свои адаптеры на основе базовых классов
3. **Обратная совместимость** - существующие адаптеры можно мигрировать через SecurityAdapterWrapper
4. **Стандартизация** - единый интерфейс для всех адаптеров безопасности
5. **Гибкость** - поддержка контекста и структурированного аудита

## Обратная совместимость

Все изменения обратно совместимы:
- Существующий код продолжит работать без изменений
- Новые компоненты опциональны
- SecurityAdapterWrapper позволяет мигрировать постепенно

## Тестирование

Необходимо добавить тесты для:
- SecurityAdapter (абстрактный класс)
- SecurityManager.register_adapter() и validate_operation()
- OperationContext (сериализация/десериализация)
- AuditLogger (разные бэкенды)
- SecurityAdapterWrapper (миграция legacy-адаптеров)

## Документация

Необходимо обновить:
- README с примерами создания адаптеров
- API документацию для новых классов
- Примеры использования в examples/

## Приоритет

**Высокий** - это критически важная функциональность для расширяемости фреймворка.

## Связанные issues

- Нет связанных issues

## Дополнительные замечания

- Все компоненты универсальны и не содержат специфичной для проекта логики
- Проекты создают свои адаптеры в своем коде, не в фреймворке
- Фреймворк предоставляет только базовые механизмы расширения

