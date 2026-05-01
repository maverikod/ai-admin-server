# Шаг 1.4.4: Создание команды для операций над CRL

**Зависимости:** Шаг 1.4.3 (CertRevokeCommand)  
**Приоритет:** Высокий  
**Время:** 45-60 минут  
**Этап:** 1 (Независимые шаги)

## 📋 Задача шага

Создать команду `CRLOperationsCommand` для управления Certificate Revocation List (CRL) с использованием mcp_security_framework. Команда должна поддерживать создание, обновление, валидацию и мониторинг CRL.

## 📁 Файлы изменений

### Создаваемые файлы:
- `ai_admin/commands/crl_operations_command.py` - команда для операций над CRL

### Модифицируемые файлы:
- `ai_admin/server.py` - регистрация новой команды

## 🔧 Описание изменений

### 1. Создание CRLOperationsCommand класса
Создать класс `CRLOperationsCommand` с методами:
- `execute()` - основной метод выполнения команды
- `_create_crl()` - создание нового CRL
- `_update_crl()` - обновление существующего CRL
- `_validate_crl()` - валидация CRL
- `_list_revoked_certs()` - список отозванных сертификатов
- `_check_cert_status()` - проверка статуса сертификата в CRL
- `_sync_with_database()` - синхронизация с SQL базой

### 2. Интеграция с mcp_security_framework
Использовать `CertificateManager` из mcp_security_framework для:
- Создания и обновления CRL
- Валидации CRL
- Управления жизненным циклом CRL

### 3. SQL база для учета CRL
Интегрировать с SQL базой для отслеживания:
- Созданных CRL
- Метаданных CRL (версия, дата обновления, количество отозванных)
- Статуса синхронизации с базой данных

## 💻 Описание реализации

### ai_admin/commands/crl_operations_command.py
Создать класс `CRLOperationsCommand` с методами:

```python
class CRLOperationsCommand(Command):
    """Command for Certificate Revocation List (CRL) operations."""
    
    name = "crl_operations"
    
    async def execute(self,
                     action: str = "create",
                     ca_cert_path: Optional[str] = None,
                     ca_key_path: Optional[str] = None,
                     crl_path: Optional[str] = None,
                     validity_days: int = 30,
                     update_interval_hours: int = 24,
                     check_cert_path: Optional[str] = None,
                     check_serial_number: Optional[str] = None,
                     sync_with_db: bool = True,
                     **kwargs) -> SuccessResult:
        """
        Perform CRL operations.
        
        Args:
            action: Action to perform (create, update, validate, list_revoked, check_status, sync)
            ca_cert_path: Path to CA certificate
            ca_key_path: Path to CA private key
            crl_path: Path to CRL file
            validity_days: CRL validity period in days
            update_interval_hours: CRL update interval in hours
            check_cert_path: Path to certificate to check
            check_serial_number: Serial number to check
            sync_with_db: Whether to sync with database
        """
```

### 4. Параметры команды
- `action`: Действие для выполнения (create, update, validate, list_revoked, check_status, sync)
- `ca_cert_path`: Путь к CA сертификату
- `ca_key_path`: Путь к CA приватному ключу
- `crl_path`: Путь к файлу CRL
- `validity_days`: Срок действия CRL в днях
- `update_interval_hours`: Интервал обновления CRL в часах
- `check_cert_path`: Путь к сертификату для проверки
- `check_serial_number`: Серийный номер для проверки
- `sync_with_db`: Синхронизировать ли с базой данных

### 5. Результат выполнения
Возвращать `SuccessResult` с информацией:
- Статус выполнения операции
- Метаданные CRL
- Список отозванных сертификатов
- Статус синхронизации с базой данных

## 🧪 Тестирование

### Unit тесты:
- Тестирование создания CRL
- Тестирование обновления CRL
- Тестирование валидации CRL
- Тестирование проверки статуса сертификата
- Тестирование синхронизации с базой данных

### Интеграционные тесты:
- Тестирование с реальными CRL
- Тестирование интеграции с mcp_security_framework
- Тестирование SQL базы данных

## 📊 Ожидаемый результат

После выполнения шага будет создана команда `crl_operations` для управления CRL с полной интеграцией в mcp_security_framework и SQL базой для учета CRL.

## 🔗 Связанные шаги

- **Зависимости:** Шаг 1.4.3 (CertRevokeCommand)
- **Используется в:** Шаг 1.4.5 (Certificate Management Tests)
- **Следующий шаг:** Шаг 1.4.5 (Certificate Management Tests)
