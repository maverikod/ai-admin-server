# FTP Commands

FTP команды для работы с файловым сервером через очередь заданий с поддержкой докачки.

## Конфигурация

FTP настройки хранятся в `config/config.json`:

```json
{
  "ftp": {
    "host": "testing.techsup.od.ua",
    "user": "aidata",
    "password": "lkhvvssvfasDsrvr234523--!fwevrwe",
    "port": 21,
    "timeout": 30,
    "passive_mode": true
  }
}
```

## Команды

### ftp_upload

Загружает файл на FTP сервер с поддержкой докачки.

**Параметры:**
- `local_path` (string, обязательный) - Локальный путь к файлу
- `remote_path` (string, опциональный) - Удаленный путь (по умолчанию использует имя локального файла)
- `resume` (boolean, по умолчанию true) - Включить режим докачки
- `overwrite` (boolean, по умолчанию false) - Перезаписать существующий файл
- `use_queue` (boolean, по умолчанию true) - Использовать очередь для длительных операций

**Примеры:**

```bash
# Загрузить файл с докачкой
curl -X POST http://localhost:8060/cmd \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "ftp_upload",
    "params": {
      "local_path": "/path/to/file.txt",
      "remote_path": "uploads/file.txt",
      "resume": true
    },
    "id": 1
  }'

# Загрузить файл с перезаписью
curl -X POST http://localhost:8060/cmd \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "ftp_upload",
    "params": {
      "local_path": "/path/to/file.txt",
      "overwrite": true
    },
    "id": 1
  }'
```

### ftp_download

Скачивает файл с FTP сервера с поддержкой докачки.

**Параметры:**
- `remote_path` (string, обязательный) - Удаленный путь к файлу
- `local_path` (string, опциональный) - Локальный путь (по умолчанию использует имя удаленного файла)
- `resume` (boolean, по умолчанию true) - Включить режим докачки
- `overwrite` (boolean, по умолчанию false) - Перезаписать существующий файл
- `use_queue` (boolean, по умолчанию true) - Использовать очередь для длительных операций

**Примеры:**

```bash
# Скачать файл с докачкой
curl -X POST http://localhost:8060/cmd \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "ftp_download",
    "params": {
      "remote_path": "uploads/file.txt",
      "local_path": "/path/to/file.txt",
      "resume": true
    },
    "id": 1
  }'

# Скачать файл с перезаписью
curl -X POST http://localhost:8060/cmd \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "ftp_download",
    "params": {
      "remote_path": "uploads/file.txt",
      "overwrite": true
    },
    "id": 1
  }'
```

### ftp_list

Показывает список файлов в удаленной директории.

**Параметры:**
- `remote_path` (string, по умолчанию "/") - Удаленный путь к директории
- `use_queue` (boolean, по умолчанию true) - Использовать очередь для операций

**Примеры:**

```bash
# Список файлов в корневой директории
curl -X POST http://localhost:8060/cmd \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "ftp_list",
    "params": {},
    "id": 1
  }'

# Список файлов в конкретной директории
curl -X POST http://localhost:8060/cmd \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "ftp_list",
    "params": {
      "remote_path": "/uploads"
    },
    "id": 1
  }'
```

### ftp_delete

Удаляет файл на FTP сервере.

**Параметры:**
- `remote_path` (string, обязательный) - Удаленный путь к файлу
- `use_queue` (boolean, по умолчанию true) - Использовать очередь для операций

**Примеры:**

```bash
# Удалить файл
curl -X POST http://localhost:8060/cmd \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "ftp_delete",
    "params": {
      "remote_path": "uploads/file.txt"
    },
    "id": 1
  }'
```

## Мониторинг заданий

Все FTP операции выполняются через очередь заданий. Для мониторинга используйте команды:

```bash
# Статус очереди
curl -X POST http://localhost:8060/cmd \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "queue_status",
    "params": {},
    "id": 1
  }'

# Статус конкретного задания
curl -X POST http://localhost:8060/cmd \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "queue_task_status",
    "params": {
      "task_id": "task-uuid-here"
    },
    "id": 1
  }'
```

## Особенности докачки

### Загрузка (Upload)
- Проверяет размер существующего файла на сервере
- Если файл уже существует и размер совпадает - пропускает загрузку
- Если файл неполный - продолжает с места остановки
- Поддерживает параметр `overwrite` для принудительной перезаписи

### Скачивание (Download)
- Проверяет размер локального файла
- Если файл уже существует и размер совпадает - пропускает скачивание
- Если файл неполный - продолжает с места остановки
- Использует режим append для докачки

## Обработка ошибок

FTP команды возвращают детальные коды ошибок:

- `FTP_CONNECTION_FAILED` - Ошибка подключения к серверу
- `FTP_AUTHENTICATION_FAILED` - Ошибка аутентификации
- `FTP_FILE_NOT_FOUND` - Файл не найден
- `FTP_PERMISSION_DENIED` - Отказано в доступе
- `FTP_UPLOAD_FAILED` - Ошибка загрузки
- `FTP_DOWNLOAD_FAILED` - Ошибка скачивания
- `FTP_RESUME_FAILED` - Ошибка докачки
- `FTP_INVALID_PATH` - Неверный путь

## Логирование

Все FTP операции логируются с детальной информацией:
- Прогресс выполнения (0-100%)
- Размеры файлов
- Позиции докачки
- Время выполнения
- Ошибки и их детали 