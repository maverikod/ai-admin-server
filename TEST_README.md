# AI Admin Server Comprehensive Test Suite

Комплексный тестовый скрипт для тестирования всех команд AI Admin сервера через HTTP API.

## Возможности

- 🐳 **Docker тесты** - тестирование всех Docker команд
- ☁️ **Vast.ai тесты** - тестирование Vast.ai операций
- ☸️ **Kubernetes тесты** - тестирование K8s команд
- 🔐 **SSH тесты** - тестирование SSH соединений и команд
- 📁 **FTP тесты** - тестирование FTP операций
- 📝 **Git тесты** - тестирование Git команд
- 🐙 **GitHub тесты** - тестирование GitHub API
- 🤖 **Ollama тесты** - тестирование Ollama команд
- 🔒 **SSL тесты** - тестирование SSL сертификатов
- 📋 **Queue тесты** - тестирование очереди задач
- 💻 **System тесты** - тестирование системного мониторинга

## Установка зависимостей

```bash
pip install -r test_requirements.txt
```

## Использование

### Запуск всех тестов
```bash
python test_server_comprehensive.py all
```

### Запуск тестов по категориям
```bash
# Docker тесты
python test_server_comprehensive.py docker

# SSH тесты
python test_server_comprehensive.py ssh

# Vast.ai тесты
python test_server_comprehensive.py vast

# Kubernetes тесты
python test_server_comprehensive.py kubernetes

# FTP тесты
python test_server_comprehensive.py ftp

# Git тесты
python test_server_comprehensive.py git

# GitHub тесты
python test_server_comprehensive.py github

# Ollama тесты
python test_server_comprehensive.py ollama

# SSL тесты
python test_server_comprehensive.py ssl

# Queue тесты
python test_server_comprehensive.py queue

# System тесты
python test_server_comprehensive.py system
```

### Использование с кастомным конфигом
```bash
python test_server_comprehensive.py --config config/config_working.json all
```

## SSH Настройка

Для SSH тестов созданы тестовые ключи в директории `test_ssh_keys/`:

- `test_key` - RSA 4096 ключ
- `test_ed25519_key` - Ed25519 ключ

SSH сервер должен быть запущен на localhost:22. Ключи уже добавлены в `~/.ssh/authorized_keys`.

## Конфигурация

SSH настройки добавлены в `config/config.json`:

```json
{
  "ssh": {
    "default_timeout": 30,
    "default_port": 22,
    "key_directory": "./test_ssh_keys",
    "servers": {
      "localhost": {
        "host": "localhost",
        "port": 22,
        "username": "vasilyvz",
        "key_path": "./test_ssh_keys/test_key",
        "description": "Local SSH server for testing"
      }
    },
    "security": {
      "strict_host_key_checking": false,
      "user_known_hosts_file": "/dev/null",
      "connect_timeout": 30
    }
  }
}
```

## Структура тестов

Каждый тест возвращает:
- ✅ **PASS** - тест прошел успешно
- ❌ **FAIL** - тест не прошел
- ⏱️ **Duration** - время выполнения
- 📝 **Error** - описание ошибки (если есть)

## Пример вывода

```
🚀 Starting AI Admin Server Test Suite
📡 Starting AI Admin server...
✅ Server started successfully

🔐 Running SSH tests...
🐳 Running Docker tests...
☁️ Running Vast.ai tests...
☸️ Running Kubernetes tests...

📊 TEST RESULTS SUMMARY
================================================================================

🔹 SSH TESTS
┌──────────────────────────────┬──────────┬──────────┬──────────────────────────────┐
│ Test Name                    │ Status   │ Duration │ Error                        │
├──────────────────────────────┼──────────┼──────────┼──────────────────────────────┤
│ ssh_connect                  │ ✅ PASS  │ 0.15s    │                              │
│ ssh_exec                     │ ✅ PASS  │ 0.12s    │                              │
└──────────────────────────────┴──────────┴──────────┴──────────────────────────────┘

📈 OVERALL SUMMARY
================================================================================
┌─────────────┬───────┐
│ Metric      │ Value │
├─────────────┼───────┤
│ Total Tests │ 45    │
│ Passed      │ 42    │
│ Failed      │ 3     │
│ Success Rate│ 93.3% │
└─────────────┴───────┘
```

## Автор

**Vasiliy Zdanovskiy**  
email: vasilyvz@gmail.com
