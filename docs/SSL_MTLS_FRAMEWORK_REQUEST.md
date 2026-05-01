# Запрос на добавление поддержки SSL и mTLS в mcp_proxy_adapter

**Дата:** 14 августа 2025  
**От:** Команда AI Admin  
**Кому:** Разработчики mcp_proxy_adapter  
**Тема:** Расширение фреймворка для поддержки SSL, mTLS и ролевой аутентификации

## 🎯 Обоснование

Фреймворк `mcp_proxy_adapter` используется в качестве универсального адаптера для всех серверов и клиентов в кластере. В настоящее время отсутствует поддержка SSL/TLS и mTLS, что критично для:

- **Безопасности кластера** - все коммуникации должны быть зашифрованы
- **Аутентификации** - необходимо различать клиентов и серверы по ролям
- **Авторизации** - контроль доступа на основе ролей в сертификатах
- **Соответствия стандартам** - mTLS является стандартом для микросервисов

## 🔧 Требуемые возможности

### 1. SSL/TLS поддержка

#### Конфигурация в config.json:
```json
{
  "ssl": {
    "enabled": true,
    "mode": "https_only",  // "https_only", "mtls", "token_auth"
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key",
    "ca_cert": "./certs/ca.crt",
    "verify_client": false,  // для простого HTTPS
    "client_cert_required": false,
    "cipher_suites": ["TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256"],
    "min_tls_version": "1.2",
    "max_tls_version": "1.3"
  }
}
```

#### Модификация запуска сервера:
```python
# В api/app.py или server.py
def create_app_with_ssl():
    app = create_app()
    
    ssl_config = config.get("ssl", {})
    if ssl_config.get("enabled", False):
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(
            ssl_config["cert_file"], 
            ssl_config["key_file"]
        )
        
        if ssl_config.get("ca_cert"):
            ssl_context.load_verify_locations(ssl_config["ca_cert"])
        
        return uvicorn.run(
            app,
            host=host,
            port=port,
            ssl_certfile=ssl_config["cert_file"],
            ssl_keyfile=ssl_config["key_file"],
            ssl_ca_certs=ssl_config.get("ca_cert"),
            ssl_verify_mode=ssl.CERT_REQUIRED if ssl_config.get("verify_client") else ssl.CERT_NONE
        )
```

### 2. mTLS поддержка с ролями

#### Расширенная конфигурация:
```json
{
  "ssl": {
    "enabled": true,
    "mode": "mtls",
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key",
    "ca_cert": "./certs/ca.crt",
    "verify_client": true,
    "client_cert_required": true,
    "roles_config": {
      "enabled": true,
      "config_file": "./mtls_roles_config.json",
      "default_policy": {
        "deny_by_default": true,
        "require_role_match": true
      }
    }
  }
}
```

#### Ролевая конфигурация (mtls_roles_config.json):
```json
{
  "roles": {
    "admin": {
      "description": "Administrator with full access",
      "allowed_servers": ["*"],
      "allowed_clients": ["*"],
      "permissions": ["read", "write", "delete", "admin"]
    },
    "operator": {
      "description": "Operator with limited access",
      "allowed_servers": ["kubernetes_manager", "docker_manager", "monitor"],
      "allowed_clients": ["admin", "operator"],
      "permissions": ["read", "write"]
    },
    "monitor": {
      "description": "Monitoring role with read-only access",
      "allowed_servers": ["monitor", "health_check"],
      "allowed_clients": ["admin", "operator", "monitor"],
      "permissions": ["read"]
    },
    "kubernetes_manager": {
      "description": "Kubernetes management role",
      "allowed_servers": ["kubernetes_manager", "monitor"],
      "allowed_clients": ["admin", "operator"],
      "permissions": ["read", "write", "kubernetes_ops"]
    },
    "docker_manager": {
      "description": "Docker management role",
      "allowed_servers": ["docker_manager", "monitor"],
      "allowed_clients": ["admin", "operator"],
      "permissions": ["read", "write", "docker_ops"]
    }
  }
}
```

### 3. Middleware для проверки ролей

#### Новый файл: `api/middleware/mtls_roles_middleware.py`
```python
import ssl
from typing import Dict, List, Optional
from fastapi import Request, HTTPException
from cryptography import x509
import json

class MTLSRolesMiddleware:
    def __init__(self, app, roles_config_path: str):
        self.app = app
        self.roles_config = self._load_roles_config(roles_config_path)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract client certificate from SSL context
            client_cert = self._extract_client_cert(scope)
            if client_cert:
                # Extract roles from certificate
                client_roles = self._extract_roles_from_cert(client_cert)
                # Validate access
                if not self._validate_access(client_roles, scope):
                    await self._send_unauthorized(send)
                    return
        
        await self.app(scope, receive, send)
    
    def _extract_client_cert(self, scope) -> Optional[x509.Certificate]:
        """Extract client certificate from SSL context."""
        if "ssl" in scope:
            ssl_context = scope["ssl"]
            if hasattr(ssl_context, 'getpeercert'):
                cert_data = ssl_context.getpeercert(binary_form=True)
                if cert_data:
                    return x509.load_der_x509_certificate(cert_data)
        return None
    
    def _extract_roles_from_cert(self, cert: x509.Certificate) -> List[str]:
        """Extract roles from certificate extensions."""
        roles = []
        
        # Try custom extension first
        try:
            custom_oid = x509.ObjectIdentifier("1.3.6.1.4.1.99999.1")
            extension = cert.extensions.get_extension_for_oid(custom_oid)
            if extension:
                roles_data = extension.value.value
                roles = [role.decode() for role in roles_data.split(b',')]
        except x509.extensions.ExtensionNotFound:
            pass
        
        # Fallback to DNS names in SAN
        if not roles:
            try:
                san = cert.extensions.get_extension_for_oid(
                    x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
                )
                if san:
                    for dns_name in san.value:
                        if dns_name.value.endswith('.certificate'):
                            roles_str = dns_name.value.replace('.certificate', '')
                            roles = roles_str.split('.')
                            break
            except x509.extensions.ExtensionNotFound:
                pass
        
        return roles
    
    def _validate_access(self, client_roles: List[str], scope) -> bool:
        """Validate if client roles have access to the requested endpoint."""
        if not client_roles:
            return self.roles_config.get("default_policy", {}).get("deny_by_default", True)
        
        # Extract server role from request path or headers
        server_role = self._extract_server_role(scope)
        
        # Check access based on roles configuration
        for client_role in client_roles:
            if client_role in self.roles_config.get("roles", {}):
                role_config = self.roles_config["roles"][client_role]
                allowed_servers = role_config.get("allowed_servers", [])
                
                if "*" in allowed_servers or server_role in allowed_servers:
                    return True
        
        return False
    
    def _extract_server_role(self, scope) -> str:
        """Extract server role from request context."""
        # Can be extracted from path, headers, or server configuration
        path = scope.get("path", "")
        if "/kubernetes/" in path:
            return "kubernetes_manager"
        elif "/docker/" in path:
            return "docker_manager"
        elif "/monitor/" in path:
            return "monitor"
        else:
            return "default"
    
    async def _send_unauthorized(self, send):
        """Send unauthorized response."""
        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": [(b"content-type", b"application/json")]
        })
        await send({
            "type": "http.response.body",
            "body": b'{"error": "Access denied: insufficient privileges"}'
        })
```

### 4. Токен-аутентификация

#### Конфигурация для токенов:
```json
{
  "ssl": {
    "enabled": true,
    "mode": "token_auth",
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key",
    "token_auth": {
      "enabled": true,
      "header_name": "Authorization",
      "token_prefix": "Bearer",
      "tokens_file": "./tokens.json",
      "token_expiry": 3600
    }
  }
}
```

#### Middleware для токенов:
```python
class TokenAuthMiddleware:
    def __init__(self, app, token_config: Dict):
        self.app = app
        self.token_config = token_config
        self.tokens = self._load_tokens()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract token from headers
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()
            
            if not self._validate_token(auth_header):
                await self._send_unauthorized(send)
                return
        
        await self.app(scope, receive, send)
    
    def _validate_token(self, auth_header: str) -> bool:
        """Validate JWT or API token."""
        if not auth_header.startswith(self.token_config["token_prefix"]):
            return False
        
        token = auth_header[len(self.token_config["token_prefix"]):].strip()
        return token in self.tokens
```

### 5. Утилиты для работы с сертификатами

#### Новый файл: `core/certificate_utils.py`
```python
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime
from typing import List, Dict, Any

class CertificateUtils:
    @staticmethod
    def create_ca_certificate(common_name: str, output_dir: str) -> Dict[str, str]:
        """Create CA certificate and key."""
        # Implementation for CA creation
    
    @staticmethod
    def create_server_certificate(common_name: str, roles: List[str], 
                                ca_cert_path: str, ca_key_path: str, 
                                output_dir: str) -> Dict[str, str]:
        """Create server certificate with embedded roles."""
        # Implementation for server cert with roles
    
    @staticmethod
    def create_client_certificate(common_name: str, roles: List[str],
                                ca_cert_path: str, ca_key_path: str,
                                output_dir: str) -> Dict[str, str]:
        """Create client certificate with embedded roles."""
        # Implementation for client cert with roles
    
    @staticmethod
    def extract_roles_from_certificate(cert_path: str) -> List[str]:
        """Extract roles from certificate."""
        # Implementation for role extraction
    
    @staticmethod
    def validate_certificate_chain(cert_path: str, ca_cert_path: str) -> bool:
        """Validate certificate against CA."""
        # Implementation for chain validation
```

### 6. Команды для управления сертификатами

#### Новые команды в commands/:
- `ssl_setup_command.py` - настройка SSL/mTLS
- `certificate_management_command.py` - управление сертификатами
- `roles_management_command.py` - управление ролями

### 7. Обновление конфигурации

#### Расширение config.py:
```python
class Config:
    def __init__(self, config_path: Optional[str] = None):
        # ... existing code ...
        
        # Add SSL configuration to default config
        self.config_data["ssl"] = {
            "enabled": False,
            "mode": "https_only",
            "cert_file": None,
            "key_file": None,
            "ca_cert": None,
            "verify_client": False,
            "client_cert_required": False,
            "roles_config": {
                "enabled": False,
                "config_file": "mtls_roles_config.json"
            },
            "token_auth": {
                "enabled": False,
                "header_name": "Authorization",
                "token_prefix": "Bearer",
                "tokens_file": "tokens.json"
            }
        }
```

## 🚀 Режимы работы

### 1. HTTPS Only
- Простое шифрование трафика
- Без проверки клиентских сертификатов
- Подходит для публичных API

### 2. mTLS с ролями
- Полная взаимная аутентификация
- Проверка ролей в сертификатах
- Контроль доступа на основе ролей
- Подходит для внутренних сервисов

### 3. Токен-аутентификация
- HTTPS + JWT/API токены
- Гибкая система авторизации
- Подходит для внешних клиентов

## 📋 План реализации

### Этап 1: Базовая SSL поддержка
1. Добавить SSL конфигурацию в config.py
2. Модифицировать create_app() для поддержки SSL
3. Обновить uvicorn.run() с SSL параметрами
4. Добавить примеры конфигурации

### Этап 2: mTLS поддержка
1. Создать CertificateUtils для работы с сертификатами
2. Добавить middleware для проверки клиентских сертификатов
3. Реализовать извлечение ролей из сертификатов
4. Создать команды для управления сертификатами

### Этап 3: Ролевая система
1. Создать MTLSRolesMiddleware
2. Реализовать конфигурацию ролей
3. Добавить валидацию доступа
4. Создать команды для управления ролями

### Этап 4: Токен-аутентификация
1. Создать TokenAuthMiddleware
2. Реализовать управление токенами
3. Добавить JWT поддержку
4. Создать команды для управления токенами

### Этап 5: Документация и примеры
1. Обновить документацию
2. Создать примеры конфигураций
3. Добавить тесты
4. Создать руководство по миграции

## 🔒 Безопасность

### Требования к безопасности:
- Поддержка TLS 1.2+ и TLS 1.3
- Современные cipher suites
- Проверка цепочки сертификатов
- Валидация сроков действия
- Отзыв сертификатов (CRL/OCSP)
- Безопасное хранение ключей

### Рекомендации:
- Использовать короткий срок действия сертификатов (30-90 дней)
- Автоматическая ротация сертификатов
- Мониторинг истечения сертификатов
- Логирование всех аутентификационных событий

## 📞 Контакты

Для обсуждения деталей реализации и координации разработки:
- Email: security@ai-admin.com
- GitHub Issues: [ссылка на репозиторий]
- Slack: #security-team

---

**Приоритет:** Высокий  
**Сроки:** 2-3 недели  
**Влияние:** Критично для безопасности кластера 