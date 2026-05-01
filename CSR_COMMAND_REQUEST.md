# Запрос на добавление команды CSR в mcp_proxy_adapter

**Дата:** 10 сентября 2025  
**От:** Команда AI Admin  
**Кому:** Разработчики mcp_proxy_adapter  
**Тема:** Добавление команды для генерации Certificate Signing Request (CSR)

## 🎯 Обоснование

В `mcp_security_framework` уже есть функционал для создания CSR через `CertificateManager.create_certificate_signing_request()`, но в `mcp_proxy_adapter` отсутствует соответствующая команда. Это критично для:

- **Управления сертификатами** - создание CSR для подписи внешними CA
- **Интеграции с внешними CA** - отправка CSR в коммерческие CA
- **Автоматизации процессов** - программное создание CSR
- **Соответствия стандартам** - CSR является стандартом для запроса сертификатов

## 🔧 Требуемая функциональность

### 1. Команда CSRCommand

Создать команду `CSRCommand` в `mcp_proxy_adapter.commands` с использованием существующего функционала `mcp_security_framework`:

```python
class CSRCommand(Command):
    """Command for generating Certificate Signing Requests (CSR)."""
    
    name = "csr"
    
    async def execute(self,
                     common_name: str,
                     organization: str = "AI Admin",
                     organizational_unit: Optional[str] = None,
                     country: str = "US",
                     state: Optional[str] = None,
                     locality: Optional[str] = None,
                     email: Optional[str] = None,
                     key_size: int = 2048,
                     key_type: str = "rsa",
                     output_dir: Optional[str] = None,
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
            key_size: Key size in bits
            key_type: Key type ("rsa" or "ec")
            output_dir: Output directory for CSR and key files
        """
```

### 2. Интеграция с mcp_security_framework

Использовать существующий метод `CertificateManager.create_certificate_signing_request()`:

```python
# В команде CSRCommand
from mcp_security_framework import CertificateManager

cert_manager = CertificateManager(config)
csr_path, key_path = cert_manager.create_certificate_signing_request(
    common_name=common_name,
    organization=organization,
    organizational_unit=organizational_unit,
    country=country,
    state=state,
    locality=locality,
    email=email,
    key_size=key_size,
    key_type=key_type,
    output_path=output_dir
)
```

### 3. Параметры команды

- `common_name`: Общее имя сертификата (обязательный)
- `organization`: Название организации
- `organizational_unit`: Организационное подразделение
- `country`: Код страны (2 буквы)
- `state`: Штат или провинция
- `locality`: Город или населенный пункт
- `email`: Email адрес
- `key_size`: Размер ключа в битах (2048, 4096)
- `key_type`: Тип ключа ("rsa" или "ec")
- `output_dir`: Директория для сохранения файлов

### 4. Результат выполнения

Возвращать `SuccessResult` с информацией:
- Путь к созданному CSR файлу
- Путь к созданному приватному ключу
- Метаданные CSR
- Статус создания

## 📁 Файлы для создания

### Создаваемые файлы:
- `mcp_proxy_adapter/commands/csr_command.py` - команда для генерации CSR

### Модифицируемые файлы:
- `mcp_proxy_adapter/commands/__init__.py` - добавление импорта CSRCommand

## 🧪 Тестирование

### Unit тесты:
- Тестирование генерации CSR
- Тестирование валидации параметров
- Тестирование различных типов ключей
- Тестирование обработки ошибок

### Интеграционные тесты:
- Тестирование с реальными файлами
- Тестирование интеграции с mcp_security_framework
- Тестирование различных параметров

## 📊 Ожидаемый результат

После добавления команды `CSRCommand` будет доступна функциональность для генерации Certificate Signing Request с полной интеграцией в `mcp_security_framework` и стандартным интерфейсом команд адаптера.

## 🔗 Связанные компоненты

- **Зависимости:** `mcp_security_framework.CertificateManager`
- **Используется в:** AI Admin для управления сертификатами
- **Связанные команды:** `CertKeyPairCommand`, `CertRevokeCommand`, `CRLOperationsCommand`

## 💡 Дополнительные возможности

В будущем можно расширить команду для:
- Поддержки Subject Alternative Names (SAN)
- Создания CSR с ролевой системой
- Интеграции с внешними CA API
- Автоматической отправки CSR в CA
