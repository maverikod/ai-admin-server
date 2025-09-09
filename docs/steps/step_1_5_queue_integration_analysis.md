# Шаг 1.5: Детальный анализ интеграции с существующей очередью

**Зависимости:** Шаг 1.1 (mcp-security-framework)  
**Приоритет:** Критический  
**Время:** 3-4 часа  
**Этап:** 1 (Независимые шаги)

## 📋 Задача шага

Провести детальный анализ существующей системы очередей и создать план интеграции SCP/SSH операций с `TaskQueue`, `QueueManager` и существующими командами.

## 📁 Анализ существующей системы очередей

### **Существующие компоненты:**

#### **1. TaskQueue (ai_admin/queue/task_queue.py)**
- **Универсальная очередь задач** с поддержкой любых операций
- **TaskType enum** - 50+ типов задач (Docker, K8s, Vast.ai, GitHub, System, etc.)
- **TaskStatus enum** - статусы задач (PENDING, RUNNING, COMPLETED, FAILED, etc.)
- **TaskErrorCode enum** - коды ошибок для различных операций
- **Task dataclass** - универсальное представление задачи
- **Асинхронное выполнение** с ограничением concurrent задач
- **Retry механизм** с настраиваемыми параметрами
- **Progress tracking** с детальными логами

#### **2. QueueManager (ai_admin/queue/queue_manager.py)**
- **Singleton pattern** для управления очередью
- **Методы для добавления задач** (add_push_task, add_build_task, etc.)
- **Интеграция с TaskQueue** для выполнения задач
- **Управление жизненным циклом** задач

#### **3. Существующие команды очереди:**
- `QueuePushCommand` - добавление задач в очередь
- `QueueStatusCommand` - получение статуса очереди
- `QueueCancelCommand` - отмена задач
- `QueueTaskStatusCommand` - статус конкретной задачи
- `QueueManageCommand` - управление задачами (pause, resume, retry)

### **Анализ интеграции SCP/SSH:**

#### **Текущее состояние:**
- **Отсутствуют SCP/SSH типы задач** в TaskType enum
- **Отсутствуют SCP/SSH команды** для работы с очередью
- **Отсутствует интеграция** с существующими FTP командами

#### **Требуемые изменения:**

### **1. Расширение TaskType enum:**
```python
# Добавить в ai_admin/queue/task_queue.py
class TaskType(Enum):
    # ... существующие типы ...
    
    # SCP/SSH operations
    SCP_UPLOAD = "scp_upload"
    SCP_DOWNLOAD = "scp_download"
    SCP_SYNC = "scp_sync"
    SCP_LIST = "scp_list"
    SSH_EXECUTE = "ssh_execute"
    SSH_TUNNEL = "ssh_tunnel"
    SSH_COPY = "ssh_copy"
```

### **2. Расширение TaskErrorCode enum:**
```python
# Добавить в ai_admin/queue/task_queue.py
class TaskErrorCode(Enum):
    # ... существующие коды ...
    
    # SCP/SSH specific errors
    SCP_CONNECTION_FAILED = "SCP_CONNECTION_FAILED"
    SCP_AUTHENTICATION_FAILED = "SCP_AUTHENTICATION_FAILED"
    SCP_FILE_NOT_FOUND = "SCP_FILE_NOT_FOUND"
    SCP_PERMISSION_DENIED = "SCP_PERMISSION_DENIED"
    SCP_TRANSFER_FAILED = "SCP_TRANSFER_FAILED"
    SSH_CONNECTION_FAILED = "SSH_CONNECTION_FAILED"
    SSH_AUTHENTICATION_FAILED = "SSH_AUTHENTICATION_FAILED"
    SSH_COMMAND_FAILED = "SSH_COMMAND_FAILED"
    SSH_TIMEOUT = "SSH_TIMEOUT"
```

### **3. Расширение QueueManager:**
```python
# Добавить в ai_admin/queue/queue_manager.py
class QueueManager:
    # ... существующие методы ...
    
    async def add_scp_upload_task(
        self,
        source_path: str,
        destination_path: str,
        host: str,
        username: str,
        **options
    ) -> str:
        """Add SCP upload task to queue."""
        
    async def add_scp_download_task(
        self,
        source_path: str,
        destination_path: str,
        host: str,
        username: str,
        **options
    ) -> str:
        """Add SCP download task to queue."""
        
    async def add_ssh_execute_task(
        self,
        command: str,
        host: str,
        username: str,
        **options
    ) -> str:
        """Add SSH execute task to queue."""
```

### **4. Расширение TaskQueue:**
```python
# Добавить в ai_admin/queue/task_queue.py
class TaskQueue:
    # ... существующие методы ...
    
    async def _execute_scp_upload_task(self, task: Task) -> None:
        """Execute SCP upload task."""
        
    async def _execute_scp_download_task(self, task: Task) -> None:
        """Execute SCP download task."""
        
    async def _execute_ssh_execute_task(self, task: Task) -> None:
        """Execute SSH command task."""
```

## 🔧 План интеграции

### **Этап 1: Расширение системы очередей**
1. Добавить SCP/SSH типы задач в TaskType enum
2. Добавить SCP/SSH коды ошибок в TaskErrorCode enum
3. Реализовать методы выполнения SCP/SSH задач в TaskQueue
4. Добавить методы добавления SCP/SSH задач в QueueManager

### **Этап 2: Создание SCP/SSH команд**
1. Создать SCPClientCommand с интеграцией в очередь
2. Создать SSHClientCommand с интеграцией в очередь
3. Интегрировать с существующими FTP командами
4. Добавить поддержку аутентификации и безопасности

### **Этап 3: Интеграция с существующими командами**
1. Интегрировать SCP/SSH команды с системой очередей
2. Добавить поддержку мониторинга и логирования
3. Интегрировать с системой конфигурации
4. Добавить поддержку retry и error handling

## 📊 Метрики успешного завершения

### Специфичные метрики для данного шага:
- [ ] **Проведен детальный анализ** существующей системы очередей
- [ ] **Определены требуемые изменения** для интеграции SCP/SSH
- [ ] **Создан план интеграции** с существующими компонентами
- [ ] **Определены новые типы задач** для SCP/SSH операций
- [ ] **Определены новые коды ошибок** для SCP/SSH операций
- [ ] **Определены методы выполнения** SCP/SSH задач
- [ ] **Определены методы добавления** SCP/SSH задач в очередь
- [ ] **Создан план интеграции** с существующими командами
- [ ] **Определены требования** к безопасности и аутентификации
- [ ] **Создан план мониторинга** и логирования SCP/SSH операций
- [ ] **Определены требования** к конфигурации SCP/SSH
- [ ] **Создан план тестирования** интеграции с очередью
- [ ] **Документация анализа** содержит полные описания компонентов
- [ ] **План интеграции** готов к реализации

### Общие метрики успеха:
- [ ] **Анализ проведен полностью** и детально
- [ ] **План интеграции** учитывает все существующие компоненты
- [ ] **Определены все требуемые изменения** для интеграции
- [ ] **Создан детальный план** реализации интеграции

## 🔗 Связанные шаги

- **Зависимости:** Шаг 1.1 (mcp-security-framework)
- **Используется в:** Шаг 1.5.1 (Расширение TaskType), Шаг 1.5.2 (Реализация методов выполнения), Шаг 1.5.3 (Расширение QueueManager), Шаг 1.5.4 (SCPClientCommand), Шаг 1.5.5 (SSHClientCommand)

## 📚 Дополнительные ресурсы

- [Existing Queue System Documentation](ai_admin/queue/README.md)
- [Task Queue Implementation](ai_admin/queue/task_queue.py)
- [Queue Manager Implementation](ai_admin/queue/queue_manager.py)
