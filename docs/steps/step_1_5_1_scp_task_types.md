# Шаг 1.5.1: Расширение TaskType для SCP операций

**Зависимости:** Нет  
**Приоритет:** Средний  
**Время:** 15-30 минут  
**Этап:** 1 (Независимые шаги)

## 📋 Задача шага

Расширить enum TaskType и TaskErrorCode для поддержки SCP/SSH операций. Добавить новые типы задач и соответствующие коды ошибок.

## 📁 Файлы изменений

### Создаваемые файлы:
- Нет

### Модифицируемые файлы:
- `ai_admin/queue/task_queue.py` - расширение TaskType и TaskErrorCode

## 🔧 Описание изменений

### 1. Расширение TaskType enum
Добавить новые типы задач для SCP/SSH операций:
- SCP_UPLOAD - загрузка файлов через SCP
- SCP_DOWNLOAD - скачивание файлов через SCP
- SCP_SYNC - синхронизация файлов через SCP
- SCP_LIST - получение списка файлов через SCP
- SSH_EXECUTE - выполнение команд через SSH
- SSH_CONNECT - подключение через SSH
- SSH_TUNNEL - создание SSH туннеля

### 2. Расширение TaskErrorCode enum
Добавить коды ошибок для SCP/SSH операций:
- SCP_CONNECTION_FAILED - ошибка подключения SCP
- SCP_AUTHENTICATION_FAILED - ошибка аутентификации SCP
- SCP_FILE_NOT_FOUND - файл не найден
- SCP_PERMISSION_DENIED - отказ в доступе
- SCP_TRANSFER_FAILED - ошибка передачи файлов
- SCP_TIMEOUT - таймаут операции
- SSH_COMMAND_FAILED - ошибка выполнения SSH команды
- SSH_KEY_INVALID - неверный SSH ключ
- SSH_HOST_UNREACHABLE - хост недоступен

## 💻 Описание реализации

### ai_admin/queue/task_queue.py
Расширить enum классы:
- Добавить новые значения в TaskType enum для SCP/SSH операций
- Добавить новые значения в TaskErrorCode enum для SCP/SSH ошибок
- Обновить документацию enum классов

## 📊 Метрики успешного завершения

### Специфичные метрики для данного шага:
- [ ] **Расширен TaskType enum** с SCP/SSH типами задач
- [ ] **Добавлены типы задач** (SCP_UPLOAD, SCP_DOWNLOAD, SCP_SYNC, SCP_LIST, SSH_EXECUTE, SSH_CONNECT, SSH_TUNNEL)
- [ ] **Расширен TaskErrorCode enum** с SCP/SSH кодами ошибок
- [ ] **Добавлены коды ошибок** (SCP_CONNECTION_FAILED, SCP_AUTHENTICATION_FAILED, SCP_FILE_NOT_FOUND, SCP_PERMISSION_DENIED, SCP_TRANSFER_FAILED, SCP_TIMEOUT, SSH_COMMAND_FAILED, SSH_KEY_INVALID, SSH_HOST_UNREACHABLE)
- [ ] **Обновлена документация** enum классов
- [ ] **Код проходит линтеры** (flake8, mypy, black)

### Общие метрики успеха:
- [ ] **Код ВСЕХ шагов с номером таким же, или ниже в плане реализован ПОЛНОСТЬЮ**
- [ ] **Прошел проверку на отсутствие ошибок инструментами**
- [ ] **Покрытие КАЖДОГО файла проекта, котороый относится к уже пройденным шагам не ниже 90%+**
- [ ] **После написания кода была проведена ПОЛНАЯ и тщательная проверка на наличие нереализованного кода**
- [ ] **В коде отсутсвтует хардкод**

## 🔗 Связанные шаги

- **Зависимости:** Нет
- **Используется в:** Шаг 1.5.2 (Методы выполнения SCP задач), Шаг 1.5.3 (Расширение QueueManager)

## 📚 Дополнительные ресурсы

- [Python Enum Documentation](https://docs.python.org/3/library/enum.html)
- [SCP Protocol](https://en.wikipedia.org/wiki/Secure_copy_protocol)
- [SSH Protocol](https://en.wikipedia.org/wiki/Secure_Shell)
