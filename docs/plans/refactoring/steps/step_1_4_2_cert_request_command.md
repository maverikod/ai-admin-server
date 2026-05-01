# Шаг 1.4.2: Создание команды для генерации запроса на сертификат (CSR)

**Зависимости:** Шаг 1.4.1 (CertKeyPairCommand)  
**Приоритет:** Высокий  
**Время:** 30-45 минут  
**Этап:** 1 (Независимые шаги)

## 📋 Задача шага

Создать команду `CertRequestCommand` для генерации Certificate Signing Request (CSR) с использованием mcp_security_framework. Команда должна поддерживать создание CSR для различных типов сертификатов с ролевой системой.

## 📁 Файлы изменений

### Создаваемые файлы:
- `ai_admin/commands/cert_request_command.py` - команда для генерации CSR

### Модифицируемые файлы:
- `ai_admin/server.py` - регистрация новой команды

## 🔧 Описание изменений

### 1. Создание CertRequestCommand класса
Создать класс `CertRequestCommand` с методами:
- `execute()` - основной метод выполнения команды
- `_generate_csr()` - генерация Certificate Signing Request
- `_validate_csr()` - валидация созданного CSR
- `_save_to_database()` - сохранение информации о CSR в SQL базу

### 2. Интеграция с mcp_security_framework
Использовать `CertificateManager` из mcp_security_framework для:
- Генерации CSR с ролевой системой
- Валидации параметров CSR
- Управления жизненным циклом CSR

### 3. SQL база для учета CSR
Интегрировать с SQL базой для отслеживания:
- Созданных CSR
- Метаданных CSR (роли, статус, дата создания)
- Связей между CSR и подписанными сертификатами

## 💻 Описание реализации

### ai_admin/commands/cert_request_command.py
Создать класс `CertRequestCommand` с методами:

```python
class CertRequestCommand(Command):
    """Command for generating Certificate Signing Requests (CSR)."""
    
    name = "cert_request"
    
    async def execute(self,
                     common_name: str = "test-client",
                     organization: str = "AI Admin",
                     organizational_unit: Optional[str] = None,
                     country: str = "US",
                     state: Optional[str] = None,
                     locality: Optional[str] = None,
                     email: Optional[str] = None,
                     roles: Optional[List[str]] = None,
                     key_size: int = 2048,
                     output_dir: Optional[str] = None,
                     save_to_db: bool = True,
                     **kwargs) -> SuccessResult:
        """
        Generate Certificate Signing Request (CSR).
        
        Args:
            common_name: Common Name for the certificate
            organization: Organization name
            organizational_unit: Organizational unit
            country: Country code (2 letters)
            state: State or province
            locality: City or locality
            email: Email address
            roles: List of roles for the certificate
            key_size: Key size in bits
            output_dir: Output directory for files
            save_to_db: Whether to save CSR info to database
        """
```

### 4. Параметры команды
- `common_name`: Общее имя сертификата
- `organization`: Название организации
- `organizational_unit`: Организационное подразделение
- `country`: Код страны (2 буквы)
- `state`: Штат или провинция
- `locality`: Город или населенный пункт
- `email`: Email адрес
- `roles`: Список ролей для сертификата
- `key_size`: Размер ключа в битах
- `output_dir`: Директория для сохранения файлов
- `save_to_db`: Сохранять ли информацию в базу данных

### 5. Результат выполнения
Возвращать `SuccessResult` с информацией:
- Путь к созданному CSR файлу
- Путь к созданному приватному ключу
- Метаданные CSR
- Статус сохранения в базу данных
- Информация о ролях

## 🧪 Тестирование

### Unit тесты:
- Тестирование генерации CSR
- Тестирование валидации CSR
- Тестирование сохранения в базу данных
- Тестирование валидации параметров
- Тестирование ролевой системы

### Интеграционные тесты:
- Тестирование с реальными файлами
- Тестирование интеграции с mcp_security_framework
- Тестирование SQL базы данных

## 📊 Ожидаемый результат

После выполнения шага будет создана команда `cert_request` для генерации Certificate Signing Request с полной интеграцией в mcp_security_framework и SQL базой для учета CSR.

## 🔗 Связанные шаги

- **Зависимости:** Шаг 1.4.1 (CertKeyPairCommand)
- **Используется в:** Шаг 1.4.3 (CertRevokeCommand), Шаг 1.4.4 (CRLOperationsCommand)
- **Следующий шаг:** Шаг 1.4.3 (CertRevokeCommand)
