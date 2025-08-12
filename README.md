# AI Admin - Enhanced MCP Server

AI Admin - это расширенный MCP (Model Context Protocol) сервер для управления Docker, Vast.ai, FTP, GitHub и Kubernetes ресурсами.

## 🚀 Возможности

- **Docker Management**: Сборка, загрузка, поиск и управление Docker образами
- **Vast.ai Integration**: Создание, мониторинг и управление GPU инстансами
- **FTP Operations**: Загрузка, скачивание и управление файлами через FTP
- **GitHub Integration**: Управление репозиториями и проектами
- **Kubernetes Management**: Развертывание и управление K8s ресурсами
- **Queue System**: Асинхронное выполнение задач
- **System Monitoring**: Мониторинг системных ресурсов
- **Enhanced Hooks**: Расширенная система хуков для кастомизации

## 📁 Структура проекта

```
vast_srv/
├── ai_admin/                 # Основной пакет AI Admin
│   ├── commands/            # Команды для различных сервисов
│   ├── queue/              # Система очередей
│   ├── server.py           # Основной сервер
│   └── settings_manager.py # Управление настройками
├── config/                 # Конфигурационные файлы
│   ├── config.json        # Основная конфигурация
│   └── auth.json          # Учетные данные
├── scripts/               # Скрипты для тестирования и отладки
│   ├── gpu_test_script.py # GPU тестирование
│   ├── cuda_ftp_test.py   # CUDA + FTP тестирование
│   └── ...
├── tests/                 # Тесты
├── docs/                  # Документация
├── results/               # Результаты тестов
├── logs/                  # Логи приложения
└── docker/               # Docker файлы
```

## 🛠️ Установка

1. **Клонирование репозитория**:
```bash
git clone <repository-url>
cd vast_srv
```

2. **Создание виртуального окружения**:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows
```

3. **Установка зависимостей**:
```bash
pip install -r requirements.txt
```

4. **Настройка конфигурации**:
```bash
cp config/config.example.json config/config.json
cp config/auth.example.json config/auth.json
# Отредактируйте файлы с вашими настройками
```

## 🚀 Запуск

### Запуск сервера
```bash
python -m ai_admin
```

### Запуск с отладкой
```bash
python -m ai_admin --debug
```

### Запуск с кастомной конфигурацией
```bash
python -m ai_admin --config config/my_config.json
```

## 📖 Использование

### API Endpoints

Сервер предоставляет JSON-RPC API на порту 8060:

```bash
# Получение списка команд
curl -X POST http://localhost:8060/cmd \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "help", "id": 1}'

# Мониторинг системы
curl -X POST http://localhost:8060/cmd \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "system_monitor", "id": 1}'

# Поиск Vast.ai инстансов
curl -X POST http://localhost:8060/cmd \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "vast_search", "params": {"max_cost": 0.5}, "id": 1}'
```

### Доступные команды

#### Docker Commands
- `docker_build` - Сборка Docker образа
- `docker_push` - Загрузка образа в registry
- `docker_images` - Список образов
- `docker_search` - Поиск образов

#### Vast.ai Commands
- `vast_search` - Поиск доступных инстансов
- `vast_create` - Создание инстанса
- `vast_destroy` - Удаление инстанса
- `vast_instances` - Список инстансов

#### FTP Commands
- `ftp_upload` - Загрузка файла
- `ftp_download` - Скачивание файла
- `ftp_list` - Список файлов
- `ftp_delete` - Удаление файла

#### System Commands
- `system_monitor` - Мониторинг системы
- `queue_status` - Статус очереди
- `queue_push` - Добавление задачи в очередь

## 🧪 Тестирование

### GPU Testing
```bash
# Локальное тестирование GPU
python scripts/gpu_test_local.py

# Тестирование на Vast.ai
python scripts/cuda_ftp_test.py
```

### FTP Testing
```bash
# Проверка FTP соединения
python scripts/check_ftp.py

# Отладка FTP
bash scripts/full_ftp_debug.sh
```

## 📚 Документация

- [Техническая спецификация](docs/tech_spec.md)
- [Docker команды](docs/docker_images_commands.md)
- [FTP команды](docs/ftp_commands.md)
- [Система очередей](docs/enhanced_queue_system.md)
- [Управление сервером](docs/server_management.md)

## 🔧 Конфигурация

### Основные настройки (config/config.json)
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8060,
    "debug": false
  },
  "commands": {
    "auto_discovery": true,
    "discovery_path": "ai_admin.commands"
  },
  "ai_admin": {
    "features": {
      "docker_operations": true,
      "vast_operations": true,
      "ftp_operations": true
    }
  }
}
```

### Учетные данные (config/auth.json)
```json
{
  "docker": {
    "username": "your_username",
    "password": "your_password"
  },
  "vast": {
    "api_key": "your_api_key"
  },
  "ftp": {
    "host": "ftp.example.com",
    "username": "your_username",
    "password": "your_password"
  }
}
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License.

## 🆘 Поддержка

Для получения помощи:
- Создайте Issue в GitHub
- Обратитесь к документации в папке `docs/`
- Проверьте логи в папке `logs/` 