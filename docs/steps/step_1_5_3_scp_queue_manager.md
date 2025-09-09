# Шаг 1.5.3: Расширение QueueManager для SCP операций

**Зависимости:** Шаг 1.5.1 (TaskType для SCP), Шаг 1.5.2 (Методы выполнения SCP задач)  
**Приоритет:** Средний  
**Время:** 30-45 минут  
**Этап:** 1 (Независимые шаги)

## 📋 Задача шага

Расширить QueueManager для поддержки SCP/SSH операций. Добавить методы для создания SCP/SSH задач с различными параметрами.

## 📁 Файлы изменений

### Создаваемые файлы:
- Нет

### Модифицируемые файлы:
- `ai_admin/queue/queue_manager.py` - добавление методов для SCP/SSH задач

## 🔧 Описание изменений

### 1. Расширение QueueManager
Добавить методы для создания SCP/SSH задач:
- `add_scp_upload_task()` - добавление SCP upload задачи
- `add_scp_download_task()` - добавление SCP download задачи
- `add_scp_sync_task()` - добавление SCP sync задачи
- `add_ssh_execute_task()` - добавление SSH execute задачи
- `add_ssh_connect_task()` - добавление SSH connect задачи

### 2. Параметры задач
Поддержка параметров для SCP/SSH операций:
- host, port, username, password, key_file
- local_path, remote_path для SCP операций
- command для SSH операций
- recursive, preserve_attributes для SCP
- timeout, retry_count для всех операций

### 3. Категоризация и теги
Добавить категоризацию и теги для SCP/SSH задач:
- category: "scp" или "ssh"
- tags: ["scp", "upload", "file-transfer"] или ["ssh", "command", "remote-execution"]

## 💻 Описание реализации

### ai_admin/queue/queue_manager.py
Добавить методы для SCP/SSH задач:
- `add_scp_upload_task()` - создание SCP upload задачи с параметрами (host, username, local_path, remote_path, port, key_file, password, recursive, preserve_attributes, timeout, retry_count)
- `add_scp_download_task()` - создание SCP download задачи с параметрами
- `add_scp_sync_task()` - создание SCP sync задачи с параметрами (direction, delete_extra)
- `add_ssh_execute_task()` - создание SSH execute задачи с параметрами (host, username, command, port, key_file, password, timeout, retry_count)
- `add_ssh_connect_task()` - создание SSH connect задачи для тестирования подключения
- Все методы должны создавать Task объекты с правильными task_type, category и tags

## 📊 Метрики успешного завершения

### Специфичные метрики для данного шага:
- [ ] **Реализован метод add_scp_upload_task** с полными параметрами
- [ ] **Реализован метод add_scp_download_task** с полными параметрами
- [ ] **Реализован метод add_scp_sync_task** с параметрами синхронизации
- [ ] **Реализован метод add_ssh_execute_task** с полными параметрами
- [ ] **Реализован метод add_ssh_connect_task** для тестирования подключения
- [ ] **Поддержка всех параметров** (host, port, username, password, key_file, paths, command, timeout, retry_count)
- [ ] **Правильная категоризация** (category: "scp" или "ssh")
- [ ] **Правильные теги** для каждой операции
- [ ] **Создание Task объектов** с корректными task_type
- [ ] **Документация методов** содержит полные docstrings с описанием параметров
- [ ] **Код проходит линтеры** (flake8, mypy, black)

### Общие метрики успеха:
- [ ] **Код ВСЕХ шагов с номером таким же, или ниже в плане реализован ПОЛНОСТЬЮ**
- [ ] **Прошел проверку на отсутствие ошибок инструментами**
- [ ] **Покрытие КАЖДОГО файла проекта, котороый относится к уже пройденным шагам не ниже 90%+**
- [ ] **После написания кода была проведена ПОЛНАЯ и тщательная проверка на наличие нереализованного кода**
- [ ] **В коде отсутсвтует хардкод**

## 🔗 Связанные шаги

- **Зависимости:** Шаг 1.5.1 (TaskType для SCP), Шаг 1.5.2 (Методы выполнения SCP задач)
- **Используется в:** Шаг 1.5.4 (SSHClientCommand), Шаг 1.5.5 (SCPClientCommand), Шаг 1.5.6 (Unit-тесты)

## 📚 Дополнительные ресурсы

- [Queue Management Patterns](https://docs.python.org/3/library/queue.html)
- [Task Queue Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html)
