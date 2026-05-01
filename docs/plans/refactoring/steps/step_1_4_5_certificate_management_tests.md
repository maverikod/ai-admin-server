# Шаг 1.4.5: Создание тестов для команд управления сертификатами

**Зависимости:** Шаг 1.4.1-1.4.4 (Все команды управления сертификатами)  
**Приоритет:** Средний  
**Время:** 60-90 минут  
**Этап:** 1 (Независимые шаги)

## 📋 Задача шага

Создать comprehensive unit-тесты и интеграционные тесты для всех команд управления сертификатами. Покрыть все сценарии использования, валидацию параметров и обработку ошибок.

## 📁 Файлы изменений

### Создаваемые файлы:
- `tests/test_cert_key_pair_command.py` - тесты для CertKeyPairCommand
- `tests/test_cert_request_command.py` - тесты для CertRequestCommand
- `tests/test_cert_revoke_command.py` - тесты для CertRevokeCommand
- `tests/test_crl_operations_command.py` - тесты для CRLOperationsCommand
- `tests/test_certificate_management_integration.py` - интеграционные тесты

### Модифицируемые файлы:
- Нет

## 🔧 Описание изменений

### 1. Unit тесты для CertKeyPairCommand
Создать тесты для проверки:
- Генерации CA сертификата
- Генерации серверного сертификата
- Генерации клиентского сертификата
- Валидации параметров
- Обработки ошибок
- Сохранения в базу данных

### 2. Unit тесты для CertRequestCommand
Создать тесты для проверки:
- Генерации CSR
- Валидации CSR
- Ролевой системы
- Обработки ошибок
- Сохранения в базу данных

### 3. Unit тесты для CertRevokeCommand
Создать тесты для проверки:
- Отзыва по серийному номеру
- Отзыва по общему имени
- Отзыва по отпечатку
- Обновления CRL
- Обработки ошибок

### 4. Unit тесты для CRLOperationsCommand
Создать тесты для проверки:
- Создания CRL
- Обновления CRL
- Валидации CRL
- Проверки статуса сертификата
- Синхронизации с базой данных

### 5. Интеграционные тесты
Создать тесты для проверки:
- Полного жизненного цикла сертификата
- Интеграции с mcp_security_framework
- SQL базы данных
- Взаимодействия между командами

## 💻 Описание реализации

### tests/test_cert_key_pair_command.py
```python
import pytest
import tempfile
import os
from ai_admin.commands.cert_key_pair_command import CertKeyPairCommand

class TestCertKeyPairCommand:
    """Test cases for CertKeyPairCommand."""
    
    @pytest.fixture
    def command(self):
        """Create command instance."""
        return CertKeyPairCommand()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    async def test_generate_ca_certificate(self, command, temp_dir):
        """Test CA certificate generation."""
        # Test implementation
        pass
    
    async def test_generate_server_certificate(self, command, temp_dir):
        """Test server certificate generation."""
        # Test implementation
        pass
    
    async def test_generate_client_certificate(self, command, temp_dir):
        """Test client certificate generation."""
        # Test implementation
        pass
    
    async def test_validation_errors(self, command):
        """Test parameter validation."""
        # Test implementation
        pass
```

### tests/test_cert_request_command.py
```python
import pytest
import tempfile
from ai_admin.commands.cert_request_command import CertRequestCommand

class TestCertRequestCommand:
    """Test cases for CertRequestCommand."""
    
    @pytest.fixture
    def command(self):
        """Create command instance."""
        return CertRequestCommand()
    
    async def test_generate_csr(self, command):
        """Test CSR generation."""
        # Test implementation
        pass
    
    async def test_validate_csr(self, command):
        """Test CSR validation."""
        # Test implementation
        pass
    
    async def test_roles_integration(self, command):
        """Test roles integration."""
        # Test implementation
        pass
```

### tests/test_cert_revoke_command.py
```python
import pytest
from ai_admin.commands.cert_revoke_command import CertRevokeCommand

class TestCertRevokeCommand:
    """Test cases for CertRevokeCommand."""
    
    @pytest.fixture
    def command(self):
        """Create command instance."""
        return CertRevokeCommand()
    
    async def test_revoke_by_serial(self, command):
        """Test revocation by serial number."""
        # Test implementation
        pass
    
    async def test_revoke_by_common_name(self, command):
        """Test revocation by common name."""
        # Test implementation
        pass
    
    async def test_update_crl(self, command):
        """Test CRL update."""
        # Test implementation
        pass
```

### tests/test_crl_operations_command.py
```python
import pytest
from ai_admin.commands.crl_operations_command import CRLOperationsCommand

class TestCRLOperationsCommand:
    """Test cases for CRLOperationsCommand."""
    
    @pytest.fixture
    def command(self):
        """Create command instance."""
        return CRLOperationsCommand()
    
    async def test_create_crl(self, command):
        """Test CRL creation."""
        # Test implementation
        pass
    
    async def test_update_crl(self, command):
        """Test CRL update."""
        # Test implementation
        pass
    
    async def test_validate_crl(self, command):
        """Test CRL validation."""
        # Test implementation
        pass
    
    async def test_check_cert_status(self, command):
        """Test certificate status check."""
        # Test implementation
        pass
```

### tests/test_certificate_management_integration.py
```python
import pytest
import tempfile
from ai_admin.commands.cert_key_pair_command import CertKeyPairCommand
from ai_admin.commands.cert_request_command import CertRequestCommand
from ai_admin.commands.cert_revoke_command import CertRevokeCommand
from ai_admin.commands.crl_operations_command import CRLOperationsCommand

class TestCertificateManagementIntegration:
    """Integration tests for certificate management commands."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    async def test_full_certificate_lifecycle(self, temp_dir):
        """Test complete certificate lifecycle."""
        # Test implementation
        pass
    
    async def test_mcp_security_framework_integration(self, temp_dir):
        """Test mcp_security_framework integration."""
        # Test implementation
        pass
    
    async def test_sql_database_integration(self, temp_dir):
        """Test SQL database integration."""
        # Test implementation
        pass
```

## 🧪 Тестирование

### Покрытие тестами:
- Все методы команд
- Все сценарии использования
- Валидация параметров
- Обработка ошибок
- Интеграция с mcp_security_framework
- SQL база данных

### Интеграционные тесты:
- Полный жизненный цикл сертификата
- Взаимодействие между командами
- Реальные файлы и база данных

## 📊 Ожидаемый результат

После выполнения шага будут созданы comprehensive тесты для всех команд управления сертификатами с полным покрытием функциональности и интеграции.

## 🔗 Связанные шаги

- **Зависимости:** Шаг 1.4.1-1.4.4 (Все команды управления сертификатами)
- **Используется в:** Шаг 2.12 (SSL Commands Integration)
- **Следующий шаг:** Шаг 2.12 (SSL Commands Integration)
