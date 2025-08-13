# Структура проекта AI Admin

## 📁 Основные директории

### `ai_admin/` - Основной пакет
- **commands/** - Команды для различных сервисов (Docker, Vast.ai, FTP, GitHub, K8s)
- **queue/** - Система асинхронных очередей
- **server.py** - Основной сервер FastAPI
- **settings_manager.py** - Управление настройками
- **hooks.py** - Система хуков для кастомизации

### `config/` - Конфигурация
- **config.json** - Основные настройки сервера
- **auth.json** - Учетные данные для сервисов
- **custom-frame-*.json** - Дополнительные конфигурации

### `scripts/` - Скрипты и утилиты
- **gpu_test_script.py** - Основной скрипт GPU тестирования
- **cuda_ftp_test.py** - CUDA тестирование с FTP загрузкой
- **gpu_test_local.py** - Локальное GPU тестирование
- **vast_monitor.py** - Мониторинг Vast.ai инстансов
- **check_ftp.py** - Проверка FTP соединения
- **manage_ai_admin.py** - Управление AI Admin сервером
- **config.py** - Загрузка конфигурации

### `tests/` - Тесты
- **test_enhanced_integration.py** - Тесты интеграции
- **test_docker_images_commands.py** - Тесты Docker команд
- **gpu_tests/** - Тесты GPU функциональности

### `docs/` - Документация
- **development/** - Документация разработки
- **docker_images_commands.md** - Документация Docker команд
- **ftp_commands.md** - Документация FTP команд
- **enhanced_queue_system.md** - Документация системы очередей
- **server_management.md** - Управление сервером

### `results/` - Результаты тестов
- **gpu_tests/** - Результаты GPU тестирования (JSON, TXT файлы)

### `logs/` - Логи
- **old/** - Архивные логи
- **mcp_proxy_adapter_*.log** - Логи MCP Proxy Adapter

### `docker/` - Docker файлы
- **Dockerfile.gpu_test** - Docker образ для GPU тестирования
- **docker-compose.yml** - Docker Compose конфигурация
- **build.sh** - Скрипт сборки

### `examples/` - Примеры использования
- **basic_usage.py** - Базовые примеры
- **docker_images_examples.py** - Примеры работы с Docker

## 🔧 Конфигурационные файлы

### Корневые файлы
- **pyproject.toml** - Конфигурация проекта Python
- **requirements.txt** - Зависимости Python
- **setup.py** - Установка пакета
- **MANIFEST.in** - Манифест для сборки
- **.gitignore** - Исключения Git

### Документация
- **README.md** - Основная документация проекта
- **K8S_COMMANDS.md** - Команды Kubernetes
- **PROJECT_STRUCTURE.md** - Этот файл

## 🚀 Запуск проекта

```bash
# Активация виртуального окружения
source .venv/bin/activate

# Запуск сервера
python -m ai_admin

# Запуск с отладкой
python -m ai_admin --debug

# Запуск с кастомной конфигурацией
python -m ai_admin --config config/my_config.json
```

## 📊 Статистика проекта

- **Всего файлов**: 56
- **Директорий**: 20
- **Python файлов**: ~30
- **Конфигурационных файлов**: 5
- **Документации**: 8 файлов

## 🎯 Основные компоненты

1. **MCP Proxy Adapter Integration** - Интеграция с фреймворком v5.0.0
2. **Command System** - Автоматическое обнаружение и регистрация команд
3. **Queue System** - Асинхронное выполнение задач
4. **Hooks System** - Расширенная система хуков
5. **Settings Management** - Централизованное управление настройками
6. **Multi-Service Support** - Поддержка Docker, Vast.ai, FTP, GitHub, K8s

## 🔄 Жизненный цикл разработки

1. **Разработка** - Создание новых команд в `ai_admin/commands/`
2. **Тестирование** - Написание тестов в `tests/`
3. **Документация** - Обновление документации в `docs/`
4. **Сборка** - Использование Docker файлов в `docker/`
5. **Развертывание** - Конфигурация через `config/` 