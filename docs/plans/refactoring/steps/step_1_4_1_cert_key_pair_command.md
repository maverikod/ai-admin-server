# Шаг 1.4.1: Создание команды для генерации пары сертификат-ключ

**Зависимости:** Шаг 1.1 (CertificateUtils)  
**Приоритет:** Высокий  
**Время:** 45-60 минут  
**Этап:** 1 (Независимые шаги)

## 📋 Задача шага

Создать команду `CertKeyPairCommand` для генерации пар сертификат-ключ с использованием mcp_security_framework. Команда должна поддерживать создание различных типов сертификатов (CA, серверные, клиентские) с ролевой системой.

## 📁 Файлы изменений

### Создаваемые файлы:
- `ai_admin/commands/cert_key_pair_command.py` - команда для генерации пар сертификат-ключ

### Модифицируемые файлы:
- `ai_admin/server.py` - регистрация новой команды

## 🔧 Описание изменений

### 1. Создание CertKeyPairCommand класса
Создать класс `CertKeyPairCommand` с методами:
- `execute()` - основной метод выполнения команды
- `_generate_ca_pair()` - генерация CA сертификата и ключа
- `_generate_server_pair()` - генерация серверного сертификата и ключа
- `_generate_client_pair()` - генерация клиентского сертификата и ключа
- `_save_to_database()` - сохранение информации о сертификате в SQL базу

### 2. Интеграция с mcp_security_framework
Использовать `CertificateManager` из mcp_security_framework для:
- Генерации сертификатов с ролевой системой
- Валидации параметров сертификата
- Управления жизненным циклом сертификатов

### 3. SQL база для учета сертификатов
Интегрировать с SQL базой для отслеживания:
- Выпущенных сертификатов
- Метаданных сертификатов (роли, срок действия, статус)
- Связей между сертификатами (CA -> подписанные)

## 💻 Описание реализации

### ai_admin/commands/cert_key_pair_command.py
Создать класс `CertKeyPairCommand` с методами:

```python
class CertKeyPairCommand(Command):
    """Command for generating certificate-key pairs."""
    
    name = "cert_key_pair"
    
    async def execute(self,
                     cert_type: str = "client",
                     common_name: str = "test-client",
                     organization: str = "AI Admin",
                     roles: Optional[List[str]] = None,
                     validity_days: int = 365,
                     key_size: int = 2048,
                     output_dir: Optional[str] = None,
                     ca_cert_path: Optional[str] = None,
                     ca_key_path: Optional[str] = None,
                     save_to_db: bool = True,
                     **kwargs) -> SuccessResult:
        """
        Generate certificate-key pair.
        
        Args:
            cert_type: Type of certificate (ca, server, client)
            common_name: Common Name for the certificate
            organization: Organization name
            roles: List of roles for the certificate
            validity_days: Certificate validity period in days
            key_size: Key size in bits
            output_dir: Output directory for files
            ca_cert_path: Path to CA certificate (for non-CA certs)
            ca_key_path: Path to CA private key (for non-CA certs)
            save_to_db: Whether to save certificate info to database
        """
```

### 4. Параметры команды
- `cert_type`: Тип сертификата (ca, server, client)
- `common_name`: Общее имя сертификата
- `organization`: Название организации
- `roles`: Список ролей для сертификата
- `validity_days`: Срок действия в днях
- `key_size`: Размер ключа в битах
- `output_dir`: Директория для сохранения файлов
- `ca_cert_path`: Путь к CA сертификату
- `ca_key_path`: Путь к CA приватному ключу
- `save_to_db`: Сохранять ли информацию в базу данных

### 5. Результат выполнения
Возвращать `SuccessResult` с информацией:
- Пути к созданным файлам
- Метаданные сертификата
- Статус сохранения в базу данных
- Информация о ролях

## 🧪 Тестирование

### Unit тесты:
- Тестирование генерации CA сертификата
- Тестирование генерации серверного сертификата
- Тестирование генерации клиентского сертификата
- Тестирование сохранения в базу данных
- Тестирование валидации параметров

### Интеграционные тесты:
- Тестирование с реальными файлами
- Тестирование интеграции с mcp_security_framework
- Тестирование SQL базы данных

## 📊 Ожидаемый результат

После выполнения шага будет создана команда `cert_key_pair` для генерации пар сертификат-ключ с полной интеграцией в mcp_security_framework и SQL базой для учета сертификатов.

## 🔗 Связанные шаги

- **Зависимости:** Шаг 1.1 (CertificateUtils)
- **Используется в:** Шаг 1.4.2 (CertRequestCommand), Шаг 1.4.3 (CertRevokeCommand)
- **Следующий шаг:** Шаг 1.4.2 (CertRequestCommand)
