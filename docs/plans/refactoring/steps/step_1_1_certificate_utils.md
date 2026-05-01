# Шаг 1.1: Интеграция существующих утилит для работы с сертификатами

**Зависимости:** Нет  
**Приоритет:** КРИТИЧЕСКИЙ  
**Время:** 1-2 часа  
**Этап:** 0 (Критические исправления)

## 📋 Задача шага

ИНТЕГРИРОВАТЬ уже написанные и отлаженные утилиты для работы с SSL/TLS сертификатами в адаптер. Вся функциональность как единое целое уже есть в адаптере. Нужно интегрировать существующие утилиты в адаптер, а не создавать новые компоненты.

## 📁 Файлы изменений

### Интегрируемые файлы:
- `ai_admin/utils/certificate_utils.py` - ИНТЕГРИРОВАТЬ в адаптер
- `ai_admin/utils/certificate_exceptions.py` - ИНТЕГРИРОВАТЬ в адаптер
- `tests/test_certificate_utils.py` - ИНТЕГРИРОВАТЬ в адаптер
- `tests/test_certificate_exceptions.py` - ИНТЕГРИРОВАТЬ в адаптер

### Модифицируемые файлы:
- `mcp_proxy_adapter/` - интегрировать существующие утилиты

### Модифицируемые файлы:
- `requirements.txt` - добавление зависимости `cryptography`

## 🔧 Описание изменений

### 1. Создание пакета utils
Создать новый пакет `ai_admin/utils` для размещения утилит.

### 2. Реализация CertificateUtils
Создать класс `CertificateUtils` с методами для:
- Создания CA сертификата
- Создания серверного сертификата с ролями
- Создания клиентского сертификата с ролями
- Извлечения ролей из сертификатов
- Валидации цепочки сертификатов

### 3. Создание исключений
Создать отдельный файл с исключениями для работы с сертификатами:
- `CertificateError` - базовое исключение для сертификатов
- `CertificateValidationError` - ошибки валидации сертификатов
- `CertificateCreationError` - ошибки создания сертификатов
- `CertificateRoleError` - ошибки работы с ролями в сертификатах

### 4. Добавление зависимостей
Добавить библиотеку `cryptography` в requirements.txt для работы с сертификатами.

### 5. Создание unit-тестов
Написать comprehensive unit-тесты для всех методов класса и исключений.

## 💻 Декларативный код

### ai_admin/utils/__init__.py
```python
"""AI Admin utilities package."""

from .certificate_utils import CertificateUtils
from .certificate_exceptions import (
    CertificateError,
    CertificateValidationError,
    CertificateCreationError,
    CertificateRoleError
)

__all__ = [
    "CertificateUtils",
    "CertificateError",
    "CertificateValidationError", 
    "CertificateCreationError",
    "CertificateRoleError"
]
```

### ai_admin/utils/certificate_exceptions.py
```python
"""Certificate-related exceptions for AI Admin."""

from typing import Optional, Dict, Any


class CertificateError(Exception):
    """Base exception for certificate-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize certificate error.
        
        Args:
            message: Error message
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class CertificateValidationError(CertificateError):
    """Exception raised when certificate validation fails."""
    
    def __init__(
        self,
        message: str,
        validation_type: str,
        certificate_path: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize certificate validation error.
        
        Args:
            message: Error message
            validation_type: Type of validation that failed
            certificate_path: Path to certificate that failed validation
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, error_code, details)
        self.validation_type = validation_type
        self.certificate_path = certificate_path


class CertificateCreationError(CertificateError):
    """Exception raised when certificate creation fails."""
    
    def __init__(
        self,
        message: str,
        certificate_type: str,
        output_path: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize certificate creation error.
        
        Args:
            message: Error message
            certificate_type: Type of certificate being created
            output_path: Path where certificate was being created
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, error_code, details)
        self.certificate_type = certificate_type
        self.output_path = output_path


class CertificateRoleError(CertificateError):
    """Exception raised when certificate role operations fail."""
    
    def __init__(
        self,
        message: str,
        operation: str,
        roles: Optional[list] = None,
        certificate_path: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize certificate role error.
        
        Args:
            message: Error message
            operation: Role operation that failed
            roles: List of roles involved in the operation
            certificate_path: Path to certificate
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message, error_code, details)
        self.operation = operation
        self.roles = roles or []
        self.certificate_path = certificate_path
```

### ai_admin/utils/certificate_utils.py
```python
"""Certificate utilities for SSL/TLS certificate management."""

import os
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.backends import default_backend
from .certificate_exceptions import (
    CertificateError,
    CertificateValidationError,
    CertificateCreationError,
    CertificateRoleError
)


class CertificateUtils:
    """Utility class for SSL/TLS certificate operations."""
    
    # Custom OID for roles extension
    ROLES_OID = x509.ObjectIdentifier("1.3.6.1.4.1.99999.1")
    
    @staticmethod
    def create_ca_certificate(
        common_name: str,
        output_dir: str,
        organization: str = "AI Admin",
        organizational_unit: str = "Certificate Authority",
        country: str = "US",
        state: str = "Test State",
        locality: str = "Test City",
        validity_years: int = 10,
        key_size: int = 2048
    ) -> Dict[str, str]:
        """
        Create a self-signed CA certificate and private key.
        
        Args:
            common_name: Common name for the CA certificate
            output_dir: Directory to save certificate and key files
            organization: Organization name
            organizational_unit: Organizational unit
            country: Country code
            state: State or province
            locality: City or locality
            validity_years: Certificate validity period in years
            key_size: RSA key size in bits
            
        Returns:
            Dictionary with paths to created certificate and key files
            
        Raises:
            CertificateCreationError: If certificate creation fails
            ValueError: If parameters are invalid
        """
        pass
    
    @staticmethod
    def create_server_certificate(
        common_name: str,
        roles: List[str],
        ca_cert_path: str,
        ca_key_path: str,
        output_dir: str,
        organization: str = "AI Admin",
        organizational_unit: str = "Server",
        country: str = "US",
        state: str = "Test State",
        locality: str = "Test City",
        validity_days: int = 365,
        key_size: int = 2048,
        subject_alt_names: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Create a server certificate signed by CA with embedded roles.
        
        Args:
            common_name: Common name for the server certificate
            roles: List of roles to embed in the certificate
            ca_cert_path: Path to CA certificate file
            ca_key_path: Path to CA private key file
            output_dir: Directory to save certificate and key files
            organization: Organization name
            organizational_unit: Organizational unit
            country: Country code
            state: State or province
            locality: City or locality
            validity_days: Certificate validity period in days
            key_size: RSA key size in bits
            subject_alt_names: List of subject alternative names
            
        Returns:
            Dictionary with paths to created certificate and key files
            
        Raises:
            CertificateCreationError: If certificate creation fails
            ValueError: If parameters are invalid
            CertificateError: If CA certificate is invalid
        """
        pass
    
    @staticmethod
    def create_client_certificate(
        common_name: str,
        roles: List[str],
        ca_cert_path: str,
        ca_key_path: str,
        output_dir: str,
        organization: str = "AI Admin",
        organizational_unit: str = "Client",
        country: str = "US",
        state: str = "Test State",
        locality: str = "Test City",
        validity_days: int = 730,
        key_size: int = 2048
    ) -> Dict[str, str]:
        """
        Create a client certificate signed by CA with embedded roles.
        
        Args:
            common_name: Common name for the client certificate
            roles: List of roles to embed in the certificate
            ca_cert_path: Path to CA certificate file
            ca_key_path: Path to CA private key file
            output_dir: Directory to save certificate and key files
            organization: Organization name
            organizational_unit: Organizational unit
            country: Country code
            state: State or province
            locality: City or locality
            validity_days: Certificate validity period in days
            key_size: RSA key size in bits
            
        Returns:
            Dictionary with paths to created certificate and key files
            
        Raises:
            CertificateCreationError: If certificate creation fails
            ValueError: If parameters are invalid
            CertificateError: If CA certificate is invalid
        """
        pass
    
    @staticmethod
    def extract_roles_from_certificate(cert_path: str) -> List[str]:
        """
        Extract roles from certificate extensions.
        
        Args:
            cert_path: Path to certificate file
            
        Returns:
            List of roles extracted from certificate
            
        Raises:
            CertificateValidationError: If certificate is invalid
            IOError: If certificate file cannot be read
        """
        pass
    
    @staticmethod
    def validate_certificate_chain(
        cert_path: str,
        ca_cert_path: str,
        check_revocation: bool = False
    ) -> bool:
        """
        Validate certificate against CA certificate.
        
        Args:
            cert_path: Path to certificate file to validate
            ca_cert_path: Path to CA certificate file
            check_revocation: Whether to check certificate revocation
            
        Returns:
            True if certificate is valid, False otherwise
            
        Raises:
            IOError: If certificate files cannot be read
            CertificateError: If certificates are invalid
        """
        pass
    
    @staticmethod
    def get_certificate_info(cert_path: str) -> Dict[str, Any]:
        """
        Get basic information about a certificate.
        
        Args:
            cert_path: Path to certificate file
            
        Returns:
            Dictionary with certificate information
            
        Raises:
            CertificateValidationError: If certificate is invalid
            IOError: If certificate file cannot be read
        """
        pass
    
    @staticmethod
    def _create_private_key(key_size: int) -> rsa.RSAPrivateKey:
        """
        Create RSA private key.
        
        Args:
            key_size: RSA key size in bits
            
        Returns:
            RSA private key object
        """
        pass
    
    @staticmethod
    def _create_certificate_signing_request(
        private_key: rsa.RSAPrivateKey,
        common_name: str,
        organization: str,
        organizational_unit: str,
        country: str,
        state: str,
        locality: str
    ) -> x509.CertificateSigningRequest:
        """
        Create certificate signing request.
        
        Args:
            private_key: RSA private key
            common_name: Common name
            organization: Organization name
            organizational_unit: Organizational unit
            country: Country code
            state: State or province
            locality: City or locality
            
        Returns:
            Certificate signing request object
        """
        pass
    
    @staticmethod
    def _embed_roles_in_certificate(
        builder: x509.CertificateBuilder,
        roles: List[str]
    ) -> x509.CertificateBuilder:
        """
        Embed roles in certificate using custom extension and SAN.
        
        Args:
            builder: Certificate builder object
            roles: List of roles to embed
            
        Returns:
            Modified certificate builder
        """
        pass
    
    @staticmethod
    def _save_certificate_and_key(
        certificate: x509.Certificate,
        private_key: rsa.RSAPrivateKey,
        cert_path: str,
        key_path: str
    ) -> None:
        """
        Save certificate and private key to files.
        
        Args:
            certificate: Certificate object
            private_key: Private key object
            cert_path: Path to save certificate
            key_path: Path to save private key
            
        Raises:
            IOError: If file operations fail
        """
        pass
```

### tests/test_certificate_utils.py
```python
"""Unit tests for CertificateUtils."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from ai_admin.utils.certificate_utils import CertificateUtils
from ai_admin.utils.certificate_exceptions import (
    CertificateError,
    CertificateValidationError,
    CertificateCreationError,
    CertificateRoleError
)


class TestCertificateUtils(unittest.TestCase):
    """Test cases for CertificateUtils class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.ca_common_name = "Test CA"
        self.server_common_name = "test-server"
        self.client_common_name = "test-client"
        self.test_roles = ["admin", "user", "readonly"]
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_ca_certificate_success(self):
        """Test successful CA certificate creation."""
        pass
    
    def test_create_ca_certificate_invalid_params(self):
        """Test CA certificate creation with invalid parameters."""
        pass
    
    def test_create_server_certificate_success(self):
        """Test successful server certificate creation."""
        pass
    
    def test_create_client_certificate_success(self):
        """Test successful client certificate creation."""
        pass
    
    def test_extract_roles_from_certificate_custom_extension(self):
        """Test role extraction from custom extension."""
        pass
    
    def test_extract_roles_from_certificate_san_fallback(self):
        """Test role extraction from SAN as fallback."""
        pass
    
    def test_validate_certificate_chain_valid(self):
        """Test certificate chain validation with valid certificates."""
        pass
    
    def test_validate_certificate_chain_invalid(self):
        """Test certificate chain validation with invalid certificates."""
        pass
    
    def test_get_certificate_info(self):
        """Test certificate information extraction."""
        pass
    
    def test_create_private_key(self):
        """Test private key creation."""
        pass
    
    def test_embed_roles_in_certificate(self):
        """Test role embedding in certificate."""
        pass
```

### tests/test_certificate_exceptions.py
```python
"""Unit tests for certificate exceptions."""

import unittest
from ai_admin.utils.certificate_exceptions import (
    CertificateError,
    CertificateValidationError,
    CertificateCreationError,
    CertificateRoleError
)


class TestCertificateError(unittest.TestCase):
    """Test cases for CertificateError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_error_code(self):
        """Test initialization with error code."""
        pass
    
    def test_init_with_details(self):
        """Test initialization with details."""
        pass


class TestCertificateValidationError(unittest.TestCase):
    """Test cases for CertificateValidationError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_certificate_path(self):
        """Test initialization with certificate path."""
        pass


class TestCertificateCreationError(unittest.TestCase):
    """Test cases for CertificateCreationError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_output_path(self):
        """Test initialization with output path."""
        pass


class TestCertificateRoleError(unittest.TestCase):
    """Test cases for CertificateRoleError class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        pass
    
    def test_init_with_roles(self):
        """Test initialization with roles."""
        pass
```

## 📊 Метрики успешного завершения

### Специфичные метрики для данного шага:
- [ ] **Создан класс CertificateUtils** с всеми заявленными методами
- [ ] **Реализован метод create_ca_certificate** - создает валидный CA сертификат
- [ ] **Реализован метод create_server_certificate** - создает серверный сертификат с ролями
- [ ] **Реализован метод create_client_certificate** - создает клиентский сертификат с ролями
- [ ] **Реализован метод extract_roles_from_certificate** - извлекает роли из сертификатов
- [ ] **Реализован метод validate_certificate_chain** - валидирует цепочку сертификатов
- [ ] **Реализован метод get_certificate_info** - извлекает информацию о сертификате
- [ ] **Созданы все вспомогательные методы** (_create_private_key, _create_certificate_signing_request, etc.)
- [ ] **Написаны unit-тесты** с покрытием не менее 90%
- [ ] **Добавлена зависимость cryptography** в requirements.txt
- [ ] **Создан пакет ai_admin/utils** с правильной инициализацией
- [ ] **Создан файл certificate_exceptions.py** с иерархией исключений
- [ ] **Все методы обрабатывают исключения** (CertificateCreationError, CertificateValidationError, CertificateRoleError)
- [ ] **Документация методов** содержит полные docstrings с типами и описаниями
- [ ] **Код проходит линтеры** (flake8, mypy, black)
- [ ] **Тесты проходят успешно** (pytest)
- [ ] **Созданные сертификаты валидны** и могут быть использованы для SSL/TLS

### Общие метрики успеха:
- [ ] **Код ВСЕХ шагов с номером таким же, или ниже в плане реализован ПОЛНОСТЬЮ**
- [ ] **Прошел проверку на отсутствие ошибок инструментами**
- [ ] **Покрытие КАЖДОГО файла проекта, котороый относится к уже пройденным шагам не ниже 90%+**
- [ ] **После написания кода была проведена ПОЛНАЯ и тщательная проверка на наличие нереализованного кода**
- [ ] **В коде отсутсвтует хардкод**

## 🔗 Связанные шаги

- **Зависимости:** Нет
- **Используется в:** Шаг 1.2 (MTLSRolesMiddleware), Шаг 1.3 (MTLSRolesCommand), Шаг 1.4 (SSLSetupCommand), Шаг 2.1 (Расширение конфигурации), Шаг 2.2 (Фабричный метод), Шаг 3.3 (Интеграция SSL/mTLS)

## 📚 Дополнительные ресурсы

- [Cryptography Library Documentation](https://cryptography.io/en/latest/)
- [X.509 Certificate Standards](https://tools.ietf.org/html/rfc5280)
- [Subject Alternative Names](https://tools.ietf.org/html/rfc5280#section-4.2.1.6)
- [Custom X.509 Extensions](https://tools.ietf.org/html/rfc5280#section-4.2)
