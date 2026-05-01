# Шаг 1.4.3: Создание команды для отзыва сертификатов

**Зависимости:** Шаг 1.4.1 (CertKeyPairCommand), Шаг 1.4.2 (CertRequestCommand)  
**Приоритет:** Высокий  
**Время:** 45-60 минут  
**Этап:** 1 (Независимые шаги)

## 📋 Задача шага

Создать команду `CertRevokeCommand` для отзыва сертификатов с использованием mcp_security_framework. Команда должна поддерживать отзыв сертификатов по различным критериям и обновление CRL.

## 📁 Файлы изменений

### Создаваемые файлы:
- `ai_admin/commands/cert_revoke_command.py` - команда для отзыва сертификатов

### Модифицируемые файлы:
- `ai_admin/server.py` - регистрация новой команды

## 🔧 Описание изменений

### 1. Создание CertRevokeCommand класса
Создать класс `CertRevokeCommand` с методами:
- `execute()` - основной метод выполнения команды
- `_revoke_by_serial()` - отзыв сертификата по серийному номеру
- `_revoke_by_common_name()` - отзыв сертификата по общему имени
- `_revoke_by_fingerprint()` - отзыв сертификата по отпечатку
- `_update_crl()` - обновление Certificate Revocation List
- `_update_database()` - обновление статуса в SQL базе

### 2. Интеграция с mcp_security_framework
Использовать `CertificateManager` из mcp_security_framework для:
- Отзыва сертификатов
- Обновления CRL
- Валидации операций отзыва

### 3. SQL база для учета отзывов
Интегрировать с SQL базой для отслеживания:
- Отозванных сертификатов
- Причин отзыва
- Даты отзыва
- Статуса обновления CRL

## 💻 Описание реализации

### ai_admin/commands/cert_revoke_command.py
Создать класс `CertRevokeCommand` с методами:

```python
class CertRevokeCommand(Command):
    """Command for revoking certificates."""
    
    name = "cert_revoke"
    
    async def execute(self,
                     action: str = "revoke",
                     cert_path: Optional[str] = None,
                     serial_number: Optional[str] = None,
                     common_name: Optional[str] = None,
                     fingerprint: Optional[str] = None,
                     reason: str = "unspecified",
                     ca_cert_path: Optional[str] = None,
                     ca_key_path: Optional[str] = None,
                     crl_path: Optional[str] = None,
                     update_crl: bool = True,
                     update_db: bool = True,
                     **kwargs) -> SuccessResult:
        """
        Revoke certificate and update CRL.
        
        Args:
            action: Action to perform (revoke, list_revoked, check_status)
            cert_path: Path to certificate file
            serial_number: Serial number of certificate to revoke
            common_name: Common name of certificate to revoke
            fingerprint: Fingerprint of certificate to revoke
            reason: Reason for revocation
            ca_cert_path: Path to CA certificate
            ca_key_path: Path to CA private key
            crl_path: Path to CRL file
            update_crl: Whether to update CRL
            update_db: Whether to update database
        """
```

### 4. Параметры команды
- `action`: Действие для выполнения (revoke, list_revoked, check_status)
- `cert_path`: Путь к файлу сертификата
- `serial_number`: Серийный номер сертификата для отзыва
- `common_name`: Общее имя сертификата для отзыва
- `fingerprint`: Отпечаток сертификата для отзыва
- `reason`: Причина отзыва
- `ca_cert_path`: Путь к CA сертификату
- `ca_key_path`: Путь к CA приватному ключу
- `crl_path`: Путь к файлу CRL
- `update_crl`: Обновлять ли CRL
- `update_db`: Обновлять ли базу данных

### 5. Результат выполнения
Возвращать `SuccessResult` с информацией:
- Статус отзыва сертификата
- Информация об обновлении CRL
- Метаданные отозванного сертификата
- Статус обновления базы данных

## 🧪 Тестирование

### Unit тесты:
- Тестирование отзыва по серийному номеру
- Тестирование отзыва по общему имени
- Тестирование отзыва по отпечатку
- Тестирование обновления CRL
- Тестирование обновления базы данных

### Интеграционные тесты:
- Тестирование с реальными сертификатами
- Тестирование интеграции с mcp_security_framework
- Тестирование SQL базы данных

## 📊 Ожидаемый результат

После выполнения шага будет создана команда `cert_revoke` для отзыва сертификатов с полной интеграцией в mcp_security_framework и SQL базой для учета отзывов.

## 🔗 Связанные шаги

- **Зависимости:** Шаг 1.4.1 (CertKeyPairCommand), Шаг 1.4.2 (CertRequestCommand)
- **Используется в:** Шаг 1.4.4 (CRLOperationsCommand)
- **Следующий шаг:** Шаг 1.4.4 (CRLOperationsCommand)
