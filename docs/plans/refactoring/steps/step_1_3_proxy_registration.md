# Шаг 1.3: Настройка Proxy Registration

**Зависимости:** Этап 0  
**Приоритет:** Средний  
**Время:** 1-2 часа  
**Этап:** 1 (Интеграция новых возможностей)

## 📋 Задача шага

Настроить автоматическую регистрацию ai_admin сервера в центральном прокси-сервере для обеспечения единой точки доступа и управления серверами.

## 📁 Файлов изменений

### Модифицируемые файлы:
- `config/config.json` - настройка регистрации в прокси
- `ai_admin/server.py` - интеграция с proxy registration manager

### Создаваемые файлы:
- `ai_admin/proxy_registration.py` - управление регистрацией в прокси

## 🔧 Описание изменений

### 1. Настройка конфигурации Proxy Registration
Настроить секцию `registration` в `config.json`:
- URL прокси-сервера
- Имя сервера и описание
- Возможности сервера
- Настройки retry и heartbeat
- Интеграция с security framework

### 2. Создание Proxy Registration Manager
Создать класс `ProxyRegistrationManager` для управления регистрацией:
- Автоматическая регистрация при запуске
- Обработка ошибок регистрации
- Retry логика с экспоненциальным backoff
- Heartbeat для поддержания соединения
- Graceful shutdown с отменой регистрации

### 3. Интеграция с server.py
Интегрировать proxy registration в основной сервер:
- Инициализация при запуске приложения
- Обработка lifecycle событий
- Логирование статуса регистрации
- Обработка ошибок и восстановление

## 💻 Описание реализации

### config/config.json
Добавить/обновить секцию `registration`:
```json
{
  "registration": {
    "enabled": true,
    "url": "http://proxy-server:port/proxy",
    "name": "ai_admin_server",
    "description": "AI Admin Server with Docker, Kubernetes, and Vast.ai support",
    "capabilities": [
      "jsonrpc",
      "rest",
      "docker_operations",
      "kubernetes_operations",
      "vast_operations",
      "ftp_operations",
      "github_operations",
      "ollama_operations",
      "queue_operations",
      "ssl_operations",
      "security_operations"
    ],
    "retry_count": 3,
    "retry_delay": 5,
    "heartbeat": {
      "enabled": true,
      "interval": 30
    },
    "security": {
      "enabled": false,
      "auth_method": "none",
      "api_key": null,
      "certificate_path": null
    }
  }
}
```

### ai_admin/proxy_registration.py
Создать класс `ProxyRegistrationManager` с методами:
- `__init__()` - инициализация с конфигурацией
- `register()` - регистрация сервера в прокси
- `unregister()` - отмена регистрации
- `start_heartbeat()` - запуск heartbeat
- `stop_heartbeat()` - остановка heartbeat
- `is_registered()` - проверка статуса регистрации
- `get_server_key()` - получение server key
- `handle_registration_error()` - обработка ошибок регистрации

### ai_admin/server.py
Интегрировать proxy registration:
- Инициализация `ProxyRegistrationManager` при запуске
- Регистрация в прокси после успешного запуска сервера
- Обработка shutdown для graceful unregister
- Логирование статуса регистрации

## 📊 Метрики успешного завершения

### Специфичные метрики для данного шага:
- [ ] **Настроена секция registration** в config.json с корректными параметрами
- [ ] **Создан класс ProxyRegistrationManager** с полным функционалом
- [ ] **Реализован метод register()** - регистрация сервера в прокси
- [ ] **Реализован метод unregister()** - отмена регистрации
- [ ] **Реализован метод start_heartbeat()** - запуск heartbeat
- [ ] **Реализован метод stop_heartbeat()** - остановка heartbeat
- [ ] **Реализован метод is_registered()** - проверка статуса регистрации
- [ ] **Реализован метод get_server_key()** - получение server key
- [ ] **Реализован метод handle_registration_error()** - обработка ошибок регистрации
- [ ] **Интегрирован ProxyRegistrationManager** в server.py
- [ ] **Поддерживается автоматическая регистрация** при запуске сервера
- [ ] **Поддерживается retry логика** с экспоненциальным backoff
- [ ] **Поддерживается heartbeat** для поддержания соединения
- [ ] **Поддерживается graceful shutdown** с отменой регистрации
- [ ] **Поддерживается обработка ошибок** с детальным логированием
- [ ] **Поддерживается интеграция с security framework** для безопасной регистрации
- [ ] **Документация методов** содержит полные docstrings с типами и описаниями
- [ ] **Код проходит линтеры** (flake8, mypy, black)
- [ ] **Proxy registration работает** корректно

### Общие метрики успеха:
- [ ] **Код ВСЕХ шагов с номером таким же, или ниже в плане реализован ПОЛНОСТЬЮ**
- [ ] **Прошел проверку на отсутствие ошибок инструментами**
- [ ] **Покрытие КАЖДОГО файла проекта, котороый относится к уже пройденным шагам не ниже 90%+**
- [ ] **После написания кода была проведена ПОЛНАЯ и тщательная проверка на наличие нереализованного кода**
- [ ] **В коде отсутсвтует хардкод**

## 🔗 Связанные шаги

- **Зависимости:** Этап 0 (Критические исправления)
- **Используется в:** Шаг 1.4 (Plugin System), Шаг 1.5 (Hooks System), Шаг 1.6 (Dependency Injection)

## 📚 Дополнительные ресурсы

- [Proxy Pattern](https://en.wikipedia.org/wiki/Proxy_pattern)
- [Service Discovery](https://microservices.io/patterns/service-registry.html)
- [Heartbeat Pattern](https://microservices.io/patterns/reliability/health-check.html)
- [Retry Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/retry)

## 🚨 Важные замечания

1. **Совместимость с mcp_proxy_adapter**: Использовать существующий ProxyRegistrationManager из адаптера
2. **Обработка ошибок**: Все ошибки регистрации должны логироваться с детальной информацией
3. **Graceful shutdown**: При остановке сервера обязательно отменять регистрацию
4. **Heartbeat**: Настроить разумный интервал heartbeat (30-60 секунд)
5. **Retry логика**: Использовать экспоненциальный backoff для retry
6. **Security**: Поддержка различных методов аутентификации при регистрации
7. **Monitoring**: Логирование всех событий регистрации для мониторинга

## 🔍 Тестирование

### Функциональные тесты:
- [ ] Регистрация сервера в прокси при запуске
- [ ] Обработка ошибок регистрации
- [ ] Retry логика при неудачной регистрации
- [ ] Heartbeat для поддержания соединения
- [ ] Отмена регистрации при shutdown
- [ ] Восстановление соединения при потере связи

### Интеграционные тесты:
- [ ] Интеграция с mcp_proxy_adapter
- [ ] Работа с различными конфигурациями
- [ ] Обработка network errors
- [ ] Graceful shutdown scenarios
- [ ] Security integration testing
