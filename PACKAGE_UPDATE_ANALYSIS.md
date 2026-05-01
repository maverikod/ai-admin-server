# Анализ необходимых изменений после обновления пакетов

**Дата:** 2025-01-27  
**Последнее обновление:** 2025-01-27 (добавлена информация о версии 1.6.0)  
**Проверка готовности:** 2025-01-27 (см. MIGRATION_CHECKLIST.md)

## 🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ

**Статус готовности:** ❌ **НЕ ГОТОВО К ПЕРЕЕЗДУ**

**Обнаружены критические проблемы:**
1. ❌ Отсутствуют зависимости `mcp_security_framework>=1.6.0` и `queuemgr>=1.0.13` в requirements.txt
2. ❌ 10 команд используют несуществующий API `mcp_proxy_adapter.queue`
3. ❌ 3 команды используют собственный менеджер очереди
4. ❌ Отсутствует конфигурация `queue_manager` в config.json
5. ❌ Неправильная инициализация очереди в dependency_injection.py

**Подробный чеклист:** См. `MIGRATION_CHECKLIST.md`

**Рекомендация:** Исправить критические проблемы перед переездом.

**Обновленные пакеты:**
- `mcp-proxy-adapter-6.9.102` (было >=5.0.0)
- `mcp_security_framework-1.6.0` (было >=1.1.2) ⭐ **ОБНОВЛЕНО: добавлены все запрошенные компоненты!**
- `queuemgr-1.0.13` (новый пакет)
- `werkzeug-3.1.4` (обновлен)

**✅ ВАЖНОЕ ОБНОВЛЕНИЕ:**
Версия `mcp_security_framework-1.6.0` уже содержит все запрошенные универсальные компоненты:
- ✅ `SecurityAdapter` - базовый класс для адаптеров
- ✅ `OperationType` - базовый класс для типов операций
- ✅ `OperationContext` - контекст операций
- ✅ `AuditLogger`, `AuditEvent`, `AuditStatus` - структурированный аудит
- ✅ `SecurityAdapterWrapper` - обертка для legacy-адаптеров
- ✅ Методы регистрации и управления адаптерами в `SecurityManager`

**Проверено:** Все компоненты доступны и работают (см. раздел "ОБНОВЛЕНИЕ: mcp_security_framework-1.6.0")

**🚨 КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ:**
**Проверка готовности к переезду выявила критические проблемы!**

**Статус:** ❌ **НЕ ГОТОВО К ПЕРЕЕЗДУ** - требуется исправление критических проблем.

**Обнаруженные проблемы:**
1. ❌ В `requirements.txt` отсутствуют: `mcp_security_framework>=1.6.0` и `queuemgr>=1.0.13`
2. ❌ 10 команд используют несуществующий API `mcp_proxy_adapter.queue` (должен быть `queuemgr_integration`)
3. ❌ 3 команды используют собственный менеджер `ai_admin.task_queue` вместо адаптера
4. ❌ В `config.json` отсутствует секция `queue_manager` для автоматической инициализации
5. ❌ В `dependency_injection.py` неправильная регистрация очереди

**Подробный чеклист:** См. `MIGRATION_CHECKLIST.md`

**Рекомендация:** **НЕ ПЕРЕЕЗЖАТЬ** до исправления критических проблем из Этапа 1 чеклиста.

**Важные замечания:**
- Сервер используется на компьютере разработчика **БЕЗ контейнера**
- **Сильно изменилась** инициализация и регистрация команд
- **Очередь, безопасность и API - это забота внешних проектов**
- **Безопасность ТОЛЬКО через `mcp_security_framework`** из установленного пакета
- **Адаптер берет на себя соединения и их защиту** - не нужно реализовывать самостоятельно
- В `mcp-proxy-adapter-6.9.102` есть **генератор и валидатор конфигов** - использовать как основу

## 🔍 ПРОВЕРКИ (выполнить первыми - по результатам будет скорректирован план)

## 📊 РЕЗУЛЬТАТЫ ПРОВЕРОК (выполнено 2025-01-27)

### ✅ Проверка 1: Использование очереди адаптера - РЕЗУЛЬТАТЫ

#### 1.1. Анализ использования очереди в командах

**КРИТИЧЕСКОЕ ОТКРЫТИЕ:** В версии `mcp-proxy-adapter-6.9.102` **НЕТ** модуля `mcp_proxy_adapter.queue` с `queue_manager`, `Task`, `TaskType`, `TaskStatus`.

**Вместо этого используется:**
- `mcp_proxy_adapter.integrations.queuemgr_integration` - интеграция с пакетом `queuemgr`
- `QueueManagerIntegration` - основной класс для управления очередью
- `QueueJobBase` - базовый класс для задач очереди
- `QueueJobStatus` - статусы задач (PENDING, RUNNING, COMPLETED, FAILED, STOPPED, DELETED)

**Команды, использующие СТАРЫЙ API (требуют обновления):**

1. **`commands/vast_create_command.py`** (строки 20-21):
   ```python
   from mcp_proxy_adapter.queue import Task, TaskType, TaskStatus
   from mcp_proxy_adapter.queue import queue_manager
   ```
   - ❌ **НЕ РАБОТАЕТ** - модуль `mcp_proxy_adapter.queue` не существует
   - Использует: `queue_manager.add_task(task)` (строка 117)
   - Использует: `queue_manager.get_tasks_by_status(TaskStatus.PENDING)` (строка 137)

2. **`commands/vast_destroy_command.py`** (строки 20-21):
   ```python
   from mcp_proxy_adapter.queue import Task, TaskType, TaskStatus
   from mcp_proxy_adapter.queue import queue_manager
   ```
   - ❌ **НЕ РАБОТАЕТ** - модуль `mcp_proxy_adapter.queue` не существует

3. **`commands/ssh_exec_command.py`** (строки 59-60):
   ```python
   from mcp_proxy_adapter.queue import queue_manager
   from mcp_proxy_adapter.queue import TaskType, Task
   ```
   - ❌ **НЕ РАБОТАЕТ** - модуль `mcp_proxy_adapter.queue` не существует
   - Использует: `queue_manager.add_task(Task(...))` (строка 63)

4. **`commands/ftp_upload_command.py`** (строки 118-119):
   ```python
   from mcp_proxy_adapter.queue import queue_manager
   from mcp_proxy_adapter.queue import Task, TaskType
   ```
   - ❌ **НЕ РАБОТАЕТ** - модуль `mcp_proxy_adapter.queue` не существует
   - Использует: `queue_manager.add_task(task)` (строка 143)

5. **`commands/ftp_mkdir_command.py`** (строки 96-97):
   ```python
   from mcp_proxy_adapter.queue import queue_manager
   from mcp_proxy_adapter.queue import Task, TaskType
   ```
   - ❌ **НЕ РАБОТАЕТ** - модуль `mcp_proxy_adapter.queue` не существует

6. **`commands/ftp_rename_command.py`** (строки 102-103):
   ```python
   from mcp_proxy_adapter.queue import queue_manager
   from mcp_proxy_adapter.queue import Task, TaskType
   ```
   - ❌ **НЕ РАБОТАЕТ** - модуль `mcp_proxy_adapter.queue` не существует

7. **`commands/ftp_info_command.py`** (строки 96-97):
   ```python
   from mcp_proxy_adapter.queue import queue_manager
   from mcp_proxy_adapter.queue import Task, TaskType
   ```
   - ❌ **НЕ РАБОТАЕТ** - модуль `mcp_proxy_adapter.queue` не существует

8. **`commands/docker_pull_command.py`** (строка 96):
   ```python
   from mcp_proxy_adapter.queue import TaskQueueManager, Task, TaskType
   ```
   - ❌ **НЕ РАБОТАЕТ** - `TaskQueueManager` не существует в `mcp_proxy_adapter.queue`
   - Использует: `queue_manager = TaskQueueManager()` (строка 98)
   - Использует: `queue_manager.add_task(task)` (строка 114)

9. **`commands/queue_remove_task_command.py`** (строка 16):
   ```python
   from mcp_proxy_adapter.queue import queue_manager
   ```
   - ❌ **НЕ РАБОТАЕТ** - модуль `mcp_proxy_adapter.queue` не существует
   - Использует: `queue_manager.get_task(task_id)` (строка 64)
   - Использует: `queue_manager.remove_task(task_id, force=force)` (строка 73)

10. **`commands/queue_cancel_task_command.py`** (строка 16):
    ```python
    from mcp_proxy_adapter.queue import queue_manager
    ```
    - ❌ **НЕ РАБОТАЕТ** - модуль `mcp_proxy_adapter.queue` не существует
    - Использует: `queue_manager.get_task(task_id)` (строка 64)
    - Использует: `queue_manager.cancel_task(task_id, force=force)` (строка 76)

**Команды, использующие СОБСТВЕННЫЙ менеджер (требуют миграции):**

1. **`commands/ftp_download_command.py`** (строка 82):
   ```python
   from ai_admin.task_queue.task_queue_manager import TaskQueueManager, Task, TaskType
   ```
   - ⚠️ Использует собственный менеджер вместо адаптера
   - Использует: `task_queue = TaskQueueManager()` (строка 84)
   - Использует: `task_queue.add_task(task)` (строка 97)

2. **`commands/ftp_list_command.py`** (строка 66):
   ```python
   from ai_admin.task_queue.task_queue_manager import TaskQueueManager, Task, TaskType
   ```
   - ⚠️ Использует собственный менеджер вместо адаптера
   - Использует: `task_queue = TaskQueueManager()` (строка 68)
   - Использует: `task_queue.add_task(task)` (строка 78)

3. **`commands/ftp_delete_command.py`** (строка 70):
   ```python
   from ai_admin.task_queue.task_queue_manager import TaskQueueManager, Task, TaskType
   ```
   - ⚠️ Использует собственный менеджер вместо адаптера
   - Использует: `task_queue = TaskQueueManager()` (строка 72)
   - Использует: `task_queue.add_task(task)` (строка 82)

#### 1.2. Новый API очереди в mcp-proxy-adapter-6.9.102

**Правильный способ использования очереди:**

```python
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    QueueManagerIntegration,
    QueueJobBase,
    QueueJobStatus,
    get_global_queue_manager,
    init_global_queue_manager
)
```

**Основные изменения API:**

1. **Вместо `queue_manager.add_task(task)`** → **`queue_manager.add_job(job_class, job_id, params)`**
   - Старый API: `task_id = await queue_manager.add_task(Task(task_type=TaskType.SSH_EXEC, params={...}))`
   - Новый API: `result = await queue_manager.add_job(MyJobClass, job_id, params)`

2. **Вместо `queue_manager.get_task(task_id)`** → **`queue_manager.get_job_status(job_id)`**
   - Старый API: `task = await queue_manager.get_task(task_id)`
   - Новый API: `result = await queue_manager.get_job_status(job_id)` → возвращает `QueueJobResult`

3. **Вместо `queue_manager.cancel_task(task_id, force)`** → **`queue_manager.stop_job(job_id)`**
   - Старый API: `success = await queue_manager.cancel_task(task_id, force=force)`
   - Новый API: `result = await queue_manager.stop_job(job_id)` → возвращает `QueueJobResult`

4. **Вместо `queue_manager.remove_task(task_id, force)`** → **`queue_manager.delete_job(job_id)`**
   - Старый API: `success = await queue_manager.remove_task(task_id, force=force)`
   - Новый API: `result = await queue_manager.delete_job(job_id)` → возвращает `QueueJobResult`

5. **Вместо `queue_manager.get_tasks_by_status(status)`** → **`queue_manager.list_jobs()`**
   - Старый API: `tasks = await queue_manager.get_tasks_by_status(TaskStatus.PENDING)`
   - Новый API: `jobs = await queue_manager.list_jobs()` → фильтрация по статусу в коде

6. **Вместо `Task`, `TaskType`, `TaskStatus`** → **`QueueJobBase`, `QueueJobStatus`**
   - Старый API: `Task(task_type=TaskType.SSH_EXEC, params={...})`
   - Новый API: Создание класса-наследника `QueueJobBase` с методом `run()`

**Инициализация глобального менеджера очереди:**

```python
# В startup event сервера
from mcp_proxy_adapter.integrations.queuemgr_integration import init_global_queue_manager

await init_global_queue_manager(
    in_memory=True,  # Для локальной разработки
    max_concurrent_jobs=10,
    completed_job_retention_seconds=3600
)

# В командах
from mcp_proxy_adapter.integrations.queuemgr_integration import get_global_queue_manager

queue_manager = await get_global_queue_manager()
```

#### 1.3. Выводы по проверке очереди

**Критические проблемы:**
1. ❌ **10 команд используют несуществующий модуль `mcp_proxy_adapter.queue`** - код не будет работать
2. ❌ **3 команды используют собственный менеджер `ai_admin.task_queue`** - требуется миграция
3. ❌ **API полностью изменился** - требуется переписать всю логику работы с очередью

**Необходимые действия:**
1. Заменить все импорты `from mcp_proxy_adapter.queue import ...` на `from mcp_proxy_adapter.integrations.queuemgr_integration import ...`
2. Переписать все команды для использования нового API `QueueManagerIntegration`
3. Создать классы-наследники `QueueJobBase` для каждого типа задачи
4. Обновить инициализацию очереди в startup event сервера
5. Удалить или заменить использование собственного менеджера `ai_admin.task_queue`

### ✅ Проверка 1.1: Использование безопасности через mcp_security_framework - РЕЗУЛЬТАТЫ

#### 1.1.1. Анализ использования mcp_security_framework

**Команды, использующие `mcp_security_framework` (правильно):**

1. **`commands/ssl_cert_generate_command.py`** (строки 24-25):
   ```python
   from mcp_security_framework import CertificateManager
   from mcp_security_framework.schemas import CertificateConfig
   ```
   - ✅ Использует правильный импорт
   - Использует: `CertificateManager(cert_config)` (строка 42)
   - Использует: `cert_manager.register_certificate_operation()` (строка 157)

2. **`commands/ssl_cert_verify_command.py`** (строки 20-21):
   ```python
   from mcp_security_framework import CertificateManager
   from mcp_security_framework.schemas import CertificateConfig
   ```
   - ✅ Использует правильный импорт

3. **`commands/ssl_crl_command.py`** (строки 14-15):
   ```python
   from mcp_security_framework import CertificateManager
   from mcp_security_framework.schemas import CertificateConfig
   ```
   - ✅ Использует правильный импорт

**Доступные компоненты в mcp_security_framework-1.5.1:**

Проверено через инспекцию модуля:
- ✅ `SecurityManager` - основной менеджер безопасности
  - Методы: `authenticate_user`, `check_permissions`, `check_rate_limit`, `create_certificate`, `create_ssl_context`, `get_certificate_info`, `get_security_metrics`, `get_security_status`, `perform_security_audit`, `revoke_certificate`, `validate_configuration`, `validate_request`
- ✅ `CertificateManager` - управление сертификатами
  - Методы: `create_certificate_signing_request`, `create_client_certificate`, `create_crl`, `create_intermediate_ca`, `create_root_ca`, `create_server_certificate`, `export_certificate`, `export_private_key`, `get_certificate_info`, `get_crl_info`, `is_certificate_revoked`, `is_crl_valid`, `renew_certificate`, `revoke_certificate`, `validate_certificate_against_crl`, `validate_certificate_chain`
- ✅ `PermissionManager` - управление разрешениями
  - Методы: `add_role_permission`, `check_role_hierarchy`, `clear_cache`, `clear_permission_cache`, `export_roles_config`, `get_all_roles`, `get_effective_permissions`, `get_role_hierarchy`, `get_role_permissions`, `get_user_roles`, `reload_roles_configuration`, `remove_role_permission`, `validate_access`
- ✅ `AuthManager` - управление аутентификацией (доступен через импорт)

#### 1.1.2. Анализ использования собственных адаптеров безопасности

**КРИТИЧЕСКОЕ ОТКРЫТИЕ:** Проект **массово использует** собственные адаптеры безопасности из `ai_admin.security.*` вместо `mcp_security_framework`.

**Статистика использования:**
- **113 команд** используют `from ai_admin.security.*` адаптеры
- **3 команды** используют `mcp_security_framework` (только SSL команды)

**Типы собственных адаптеров:**
1. `FtpSecurityAdapter` - используется в 8 FTP командах
2. `VastAiSecurityAdapter` - используется в 4 Vast командах
3. `DockerSecurityAdapter` - используется в 10+ Docker командах
4. `GitSecurityAdapter` - используется в 20+ Git командах
5. `K8sSecurityAdapter` - используется в 10+ Kubernetes командах
6. `OllamaSecurityAdapter` - используется в 10+ Ollama командах
7. `QueueSecurityAdapter` - используется в 10+ Queue командах
8. `SSLSecurityAdapter` - используется в 3 SSL командах
9. `LLMSecurityAdapter` - используется в LLM командах
10. `VectorStoreSecurityAdapter` - используется в Vector Store командах
11. `GitHubSecurityAdapter` - используется в GitHub командах
12. `UnifiedSecurityIntegration` - используется в security команде

**Выводы:**
- ⚠️ Проект использует **собственную систему безопасности** вместо `mcp_security_framework`
- ⚠️ Только SSL команды используют `mcp_security_framework` для работы с сертификатами
- ⚠️ Все остальные команды используют собственные адаптеры для валидации операций

**Рекомендации:**
1. Сохранить собственные адаптеры для специфичных операций (Vast, Docker, Git и т.д.)
2. Использовать `mcp_security_framework` для базовых операций безопасности (сертификаты, аутентификация)
3. Интегрировать собственные адаптеры с `mcp_security_framework` для единообразия

### ✅ Проверка 1.2: Поддержка FTP операций в mcp_security_framework - РЕЗУЛЬТАТЫ

#### 1.2.1. Проверка поддержки FTP в mcp_security_framework

**Результаты проверки:**

Проверено через инспекцию модуля `mcp_security_framework`:
- ❌ `SecurityManager` **НЕ имеет** метода `validate_ftp_operation()`
- ❌ `SecurityManager` **НЕ имеет** метода `check_ftp_permissions()`
- ❌ `SecurityManager` **НЕ имеет** метода `audit_ftp_operation()`
- ❌ `PermissionManager` **НЕ имеет** метода `check_ftp_permissions()`

**Вывод:** `mcp_security_framework-1.5.1` **НЕ поддерживает** FTP операции напрямую.

#### 1.2.2. Текущая реализация FTP безопасности

**Файл:** `ai_admin/security/ftp_security_adapter.py`

**Методы, реализованные в собственном адаптере:**
1. ✅ `validate_ftp_operation(operation, user_roles, operation_params)` - валидация FTP операций
2. ✅ `check_ftp_permissions(user_roles, required_permissions)` - проверка разрешений
3. ✅ `audit_ftp_operation(operation, user_roles, operation_params, status)` - аудит операций
4. ✅ `validate_ftp_server_access(server_config, user_roles)` - валидация доступа к серверу
5. ✅ `check_ftp_file_permissions(file_path, operation, user_roles)` - проверка прав на файлы
6. ✅ `manage_ftp_certificates(operation, cert_data)` - управление сертификатами FTP
7. ✅ `setup_ftp_ssl(server_config, ssl_config)` - настройка SSL/TLS для FTP

**Поддерживаемые FTP операции:**
- ✅ `FtpOperation.UPLOAD` - загрузка файлов
- ✅ `FtpOperation.DOWNLOAD` - скачивание файлов
- ✅ `FtpOperation.LIST` - список файлов
- ✅ `FtpOperation.DELETE` - удаление файлов
- ✅ `FtpOperation.MKDIR` - создание директорий
- ✅ `FtpOperation.RMDIR` - удаление директорий
- ✅ `FtpOperation.RENAME` - переименование файлов
- ✅ `FtpOperation.CHMOD` - изменение прав доступа

**Выводы:**
- ✅ Собственный `FtpSecurityAdapter` полностью реализован и работает
- ❌ `mcp_security_framework` не поддерживает FTP операции
- ⚠️ Рекомендуется сохранить собственный адаптер или интегрировать его с `mcp_security_framework`

**Рекомендации:**
1. **Вариант 1 (рекомендуется):** Сохранить собственный `FtpSecurityAdapter` и использовать его для FTP операций
2. **Вариант 2:** Расширить `mcp_security_framework` для поддержки FTP операций (требует изменений в пакете)
3. **Вариант 3:** Интегрировать `FtpSecurityAdapter` с `mcp_security_framework` через общий интерфейс

## 📚 АНАЛИЗ ПРИМЕРОВ КОМАНД С ОЧЕРЕДЬЮ ИЗ АДАПТЕРА

### Примеры использования очереди в mcp-proxy-adapter-6.9.102

#### 1. Базовый пример команды с очередью

**Файл:** `examples/full_application/commands/queued_echo_command.py`

**Ключевые особенности:**
```python
class QueuedEchoCommand(Command):
    name = "queued_echo"
    use_queue = True  # Включает автоматическое выполнение через очередь
    
    async def execute(self, message: str = "Hello from queue!", **kwargs):
        # Команда автоматически выполняется в фоне через очередь
        # Клиент получает job_id и может проверить статус позже
        await asyncio.sleep(2)
        return CommandResult(success=True, data={"message": message})
```

**Выводы:**
- ✅ Команды с `use_queue = True` автоматически выполняются через очередь
- ✅ Клиент получает `job_id` вместо результата
- ✅ Результат можно получить позже через `queue_get_job_status`

#### 2. Создание кастомных задач очереди

**Файл:** `commands/queue/jobs.py`

**Примеры классов задач:**

1. **DataProcessingJob** - обработка данных
2. **FileOperationJob** - операции с файлами
3. **ApiCallJob** - HTTP запросы
4. **LongRunningJob** - длительные задачи с прогрессом
5. **BatchProcessingJob** - пакетная обработка
6. **FileDownloadJob** - загрузка файлов с прогрессом
7. **CommandExecutionJob** - выполнение MCP команд в очереди
8. **PeriodicLoggingJob** - периодическое логирование

**Структура класса задачи:**
```python
from mcp_proxy_adapter.integrations.queuemgr_integration import QueueJobBase

class MyCustomJob(QueueJobBase):
    """Кастомная задача для очереди."""
    
    def run(self) -> None:
        """Выполнение логики задачи."""
        # Получение параметров
        params = self.mcp_params
        
        # Обновление статуса
        self.set_status("running")
        self.set_description("Выполняется задача...")
        
        # Обновление прогресса
        self.set_progress(50)
        
        # Выполнение работы
        result = {"status": "completed", "data": "..."}
        
        # Сохранение результата
        self.set_mcp_result(result)
        
        # Или в случае ошибки
        # self.set_mcp_error("Ошибка выполнения")
```

**Ключевые методы QueueJobBase:**
- `set_status(status: str)` - установка статуса задачи
- `set_description(description: str)` - установка описания
- `set_progress(progress: int)` - установка прогресса (0-100)
- `set_mcp_result(result: Dict, status: Optional[str])` - сохранение результата
- `set_mcp_error(message: str, status: str = "failed")` - сохранение ошибки
- `self.mcp_params` - параметры задачи
- `self.job_id` - идентификатор задачи
- `self.logger` - логгер для записи логов

#### 3. Использование QueueManagerIntegration

**Файл:** `examples/queue_integration_example.py`

**Инициализация:**
```python
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    init_global_queue_manager,
    get_global_queue_manager,
    shutdown_global_queue_manager
)

# В startup event
queue_manager = await init_global_queue_manager(
    in_memory=True,  # Для локальной разработки
    max_concurrent_jobs=10,
    completed_job_retention_seconds=3600
)

# В командах
queue_manager = await get_global_queue_manager()
```

**Добавление задачи:**
```python
result = await queue_manager.add_job(
    MyCustomJob,  # Класс задачи
    "job_id_123",  # Уникальный ID
    {"param1": "value1", "param2": "value2"}  # Параметры
)
```

**Управление задачами:**
```python
# Запуск задачи
await queue_manager.start_job("job_id_123")

# Остановка задачи
await queue_manager.stop_job("job_id_123")

# Удаление задачи
await queue_manager.delete_job("job_id_123")

# Получение статуса
status = await queue_manager.get_job_status("job_id_123")
print(f"Status: {status.status}, Progress: {status.progress}%")

# Список всех задач
jobs = await queue_manager.list_jobs()
```

#### 4. CommandExecutionJob - выполнение команд в очереди

**Особенности:**
- Выполняет любую MCP команду в фоне через очередь
- Поддерживает spawn mode (для CUDA)
- Автоматически регистрирует кастомные команды в дочернем процессе
- Передает `auto_import_modules` для регистрации команд

**Использование:**
```python
from mcp_proxy_adapter.commands.queue.jobs import CommandExecutionJob

result = await queue_manager.add_job(
    CommandExecutionJob,
    "command_job_1",
    {
        "command": "vast_create",  # Имя команды
        "params": {
            "bundle_id": 123,
            "image": "pytorch/pytorch:2.1.0"
        },
        "auto_import_modules": ["commands.vast_create_command"]  # Модули для импорта
    }
)
```

#### 5. Выводы по примерам очереди

**Что нужно сделать в проекте:**
1. ✅ Создать классы-наследники `QueueJobBase` для каждого типа задачи:
   - `VastCreateJob` - создание инстансов Vast.ai
   - `VastDestroyJob` - удаление инстансов
   - `SshExecJob` - выполнение SSH команд
   - `FtpUploadJob` - загрузка файлов через FTP
   - `FtpDownloadJob` - скачивание файлов через FTP
   - `DockerPullJob` - загрузка Docker образов
   - И другие...

2. ✅ Обновить команды для использования нового API:
   - Заменить `queue_manager.add_task()` на `queue_manager.add_job()`
   - Использовать классы задач вместо `Task` объектов
   - Обновить обработку результатов

3. ✅ Инициализировать очередь в startup event:
   - Вызвать `init_global_queue_manager()` при старте сервера
   - Вызвать `shutdown_global_queue_manager()` при остановке

4. ✅ Использовать `CommandExecutionJob` для выполнения команд через очередь:
   - Передавать имя команды и параметры
   - Указывать модули для автоматической регистрации

### 🎯 УТОЧНЕНИЯ НА ОСНОВЕ РЕАЛЬНОГО ПРОЕКТА EMBED

**Анализ проекта `/home/vasilyvz/projects/embed` (работающий векторизатор):**

#### 1. Упрощенный подход для команд с очередью

**Важное открытие:** Для большинства команд НЕ нужно создавать кастомные классы задач!

**Пример из `embed/commands/embed_command.py`:**
```python
class EmbedCommand(Command):
    name = "embed"
    # Ключевой момент: просто установить use_queue = True
    use_queue = True
    
    async def execute(self, context=None, **kwargs) -> SuccessResult:
        # Адаптер автоматически оборачивает execute() в CommandExecutionJob
        # Не нужно создавать кастомный класс задачи!
        # Просто пишем обычную логику команды
        ...
```

**Как это работает:**
1. Адаптер видит `use_queue = True` в классе команды
2. Автоматически создает `CommandExecutionJob` с параметрами команды
3. Выполняет `execute()` внутри задачи в фоновом процессе
4. Возвращает `job_id` сразу, результат доступен через `queue_get_job_status`

**Преимущества:**
- ✅ Минимальные изменения в коде команды
- ✅ Не нужно создавать классы задач для простых команд
- ✅ Автоматическая обработка ошибок и результатов
- ✅ Поддержка spawn mode для CUDA

#### 2. Инициализация очереди

**Важно:** Очередь инициализируется автоматически адаптером!

**Из `embed/embed/main.py`:**
```python
# Комментарий в коде:
# Note: Queue commands are automatically registered by the adapter
# when queue_manager.enabled: true in configuration. No manual registration needed.

# НЕТ явной инициализации очереди в коде!
# Адаптер делает это автоматически при старте сервера
```

**Конфигурация (`config.json`):**
```json
{
  "queue_manager": {
    "enabled": true,
    "in_memory": true,
    "max_concurrent_jobs": 10,
    "completed_job_retention_seconds": 3600
  }
}
```

**Что делает адаптер:**
1. Читает `queue_manager.enabled` из конфигурации
2. Если `true` - автоматически вызывает `init_global_queue_manager()`
3. Регистрирует команды очереди (`queue_add_job`, `queue_get_job_status`, и т.д.)
4. Инициализирует менеджер очереди с параметрами из конфига

**Вывод:** НЕ нужно вручную вызывать `init_global_queue_manager()` в коде проекта!

#### 3. Получение статуса задачи

**Пример из `embed/commands/embed_job_status_command.py`:**
```python
from mcp_proxy_adapter.integrations.queuemgr_integration import get_global_queue_manager

async def execute(self, context=None, **kwargs) -> SuccessResult:
    # Получить менеджер очереди
    queue_manager = await get_global_queue_manager()
    if queue_manager is None:
        return ErrorResult(
            message="Queue manager is not available",
            code=-32603
        )
    
    # Использовать встроенную команду queue_get_job_status
    queue_cmd_class = registry.get_command("queue_get_job_status")
    queue_cmd = queue_cmd_class()
    queue_result = await queue_cmd.execute(context=context, job_id=job_id)
    
    return SuccessResult(data=queue_result.data)
```

**Важно:**
- Использовать `get_global_queue_manager()` для получения менеджера
- Можно использовать встроенную команду `queue_get_job_status` вместо прямого вызова API
- Проверять `queue_manager is None` перед использованием

#### 4. Когда нужны кастомные классы задач?

**Кастомные классы нужны ТОЛЬКО если:**
1. Нужна сложная логика выполнения задачи (не просто вызов команды)
2. Нужна предобработка/постобработка данных
3. Нужна специфичная обработка ошибок
4. Нужна интеграция с внешними системами

**Пример кастомной задачи:**
```python
from mcp_proxy_adapter.integrations.queuemgr_integration import QueueJobBase

class VastCreateJob(QueueJobBase):
    """Кастомная задача для создания Vast.ai инстанса с дополнительной логикой."""
    
    def run(self) -> None:
        # Сложная логика создания инстанса
        # Предобработка данных
        # Интеграция с внешними системами
        # Специфичная обработка ошибок
        ...
```

**Для простых команд (большинство случаев):**
- ✅ Просто установить `use_queue = True`
- ✅ Адаптер сделает все остальное

#### 5. Обновленные рекомендации для проекта vast_srv

**Для команд, которые уже используют очередь:**

1. **Команды с `use_queue = True` (рекомендуется):**
   ```python
   class VastCreateCommand(Command):
       name = "vast_create"
       use_queue = True  # Адаптер автоматически создаст задачу
       
       async def execute(self, context=None, **kwargs):
           # Обычная логика команды
           # Адаптер обернет в CommandExecutionJob
           ...
   ```

2. **Команды, которые создают задачи вручную:**
   - Если нужна простая очередь - использовать `use_queue = True`
   - Если нужна сложная логика - создать кастомный класс `QueueJobBase`
   - Использовать `CommandExecutionJob` для выполнения других команд через очередь

3. **Команды для получения статуса:**
   ```python
   from mcp_proxy_adapter.integrations.queuemgr_integration import get_global_queue_manager
   from mcp_proxy_adapter.commands.command_registry import registry
   
   async def execute(self, context=None, **kwargs):
       queue_manager = await get_global_queue_manager()
       if queue_manager is None:
           return ErrorResult(...)
       
       # Использовать встроенную команду
       queue_cmd = registry.get_command("queue_get_job_status")()
       return await queue_cmd.execute(context=context, job_id=job_id)
   ```

4. **Конфигурация:**
   ```json
   {
     "queue_manager": {
       "enabled": true,
       "in_memory": true,
       "max_concurrent_jobs": 10,
       "completed_job_retention_seconds": 3600
     }
   }
   ```

#### 6. Миграционный план (обновленный)

**Этап 1: Простые команды (большинство случаев)**
1. ✅ Установить `use_queue = True` в классе команды
2. ✅ Убрать ручное создание задач через `queue_manager.add_task()`
3. ✅ Убрать импорты `from mcp_proxy_adapter.queue import Task, TaskType`
4. ✅ Обновить команды статуса для использования `get_global_queue_manager()`

**Этап 2: Сложные команды (если нужна кастомная логика)**
1. ✅ Создать класс-наследник `QueueJobBase`
2. ✅ Реализовать метод `run()` с логикой задачи
3. ✅ Использовать `queue_manager.add_job(MyCustomJob, job_id, params)`

**Этап 3: Конфигурация**
1. ✅ Добавить секцию `queue_manager` в `config.json`
2. ✅ Установить `enabled: true`
3. ✅ Настроить `max_concurrent_jobs` в зависимости от нагрузки

**Этап 4: Удаление старого кода**
1. ✅ Удалить `ai_admin/task_queue/` (если не используется)
2. ✅ Удалить импорты `from ai_admin.task_queue`
3. ✅ Обновить все команды на новый API

#### 7. Паттерны создания команд с очередью (на основе реальных проектов)

**На основе анализа проектов `embed` и `svo` выявлены следующие паттерны:**

##### Паттерн 1: Простая команда с `use_queue = True` (наиболее распространенный)

**Когда использовать:**
- Команда выполняет стандартную логику
- Не нужна сложная предобработка/постобработка
- Логика команды может выполняться в дочернем процессе

**Структура:**
```python
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

class MyCommand(Command):
    """
    Описание команды.
    
    Эта команда выполняется через очередь (use_queue=True).
    Клиент должен опрашивать статус через queue_get_job_status.
    """
    
    name = "my_command"
    use_queue = True  # Ключевой момент: адаптер автоматически создаст задачу
    
    def validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация параметров."""
        if "text" not in params:
            raise InvalidParamsError("Parameter 'text' is required")
        return super().validate_params(params)
    
    async def execute(self, context=None, **kwargs) -> SuccessResult:
        """
        Выполнение команды.
        
        ВАЖНО: Когда use_queue=True, адаптер:
        1. Создает CommandExecutionJob с параметрами команды
        2. Возвращает job_id клиенту немедленно
        3. Выполняет этот метод в дочернем процессе (spawn mode)
        4. Сохраняет результат в задаче
        """
        validated_params = self.validate_params(kwargs)
        
        # Обычная логика команды
        # Адаптер обернет выполнение в CommandExecutionJob
        result = await do_something(validated_params)
        
        return SuccessResult(data=result)
```

**Пример из проекта `svo` (`queue_commands.py`):**
```python
class ChunkCommand(Command):
    """Chunk command - executes through adapter's queue system."""
    
    name = "chunk"
    result_class = ChunkResult
    use_queue = True  # Адаптер автоматически создаст задачу
    
    async def execute(self, context=None, **kwargs) -> Any:
        # Делегирование в отдельный модуль для читаемости
        return await execute_chunk_command(
            context=context,
            validated_params=self.validate_params(kwargs),
            fallback_config=self.config_dict,
        )
```

**Преимущества:**
- ✅ Минимальный код
- ✅ Автоматическая обработка очереди
- ✅ Поддержка spawn mode для CUDA
- ✅ Автоматическая обработка ошибок

##### Паттерн 2: Команда с делегированием в executor (для сложной логики)

**Когда использовать:**
- Логика команды сложная и требует отдельного модуля
- Нужно разделить команду и логику выполнения
- Команда должна оставаться тонкой оберткой

**Структура:**
```python
# commands/my_command.py - тонкая обертка
class MyCommand(Command):
    name = "my_command"
    use_queue = True
    
    async def execute(self, context=None, **kwargs) -> SuccessResult:
        # Делегирование в executor для читаемости
        return await execute_my_command(
            context=context,
            validated_params=self.validate_params(kwargs),
            fallback_config=self.config_dict,
        )

# commands/my_command_executor.py - логика выполнения
async def execute_my_command(
    *,
    context: Optional[Dict[str, Any]],
    validated_params: Dict[str, Any],
    fallback_config: Dict[str, Any],
) -> SuccessResult:
    """
    Логика выполнения команды.
    
    Вынесена в отдельный модуль для:
    - Улучшения читаемости
    - Упрощения тестирования
    - Соблюдения лимитов на размер файла
    """
    # Сложная логика выполнения
    ...
    return SuccessResult(data=result)
```

**Пример из проекта `svo`:**
- `queue_commands.py` - тонкая обертка `ChunkCommand`
- `chunk_command_executor.py` - сложная логика выполнения
- `chunk_command_helpers.py` - вспомогательные функции

##### Паттерн 3: Кастомный класс задачи (QueueJobBase)

**Когда использовать:**
- Нужна сложная логика выполнения задачи
- Требуется предобработка/постобработка данных
- Нужна специфичная обработка ошибок
- Интеграция с внешними системами
- Нужен контроль над жизненным циклом задачи

**Структура:**
```python
from mcp_proxy_adapter.integrations.queuemgr_integration import QueueJobBase
import asyncio

class MyCustomJob(QueueJobBase):
    """
    Кастомная задача для выполнения сложной логики.
    
    Используется когда стандартного use_queue=True недостаточно.
    """
    
    def run(self) -> None:
        """
        Выполнение задачи.
        
        ВАЖНО:
        - Выполняется в дочернем процессе (spawn mode)
        - Все импорты должны быть внутри метода run()
        - Параметры доступны через self.mcp_params
        - Используйте self.logger для логирования
        - Используйте self.set_status(), self.set_progress() для обновления статуса
        - Используйте self.set_mcp_result() для сохранения результата
        - Используйте self.set_mcp_error() для сохранения ошибки
        """
        self.logger.info(f"MyCustomJob {self.job_id}: Starting")
        
        try:
            # Извлечение параметров
            param1 = self.mcp_params.get("param1")
            config = self.mcp_params.get("config", {})
            
            # Установка начального статуса
            self.set_status("running")
            self.set_description("Starting processing...")
            self.set_progress(10)
            
            # Импорт модулей в дочернем процессе
            from my_module import MyProcessor
            
            # Выполнение логики
            self.set_progress(50)
            self.set_description("Processing data...")
            
            # Для async операций используйте asyncio.run()
            async def _async_work():
                processor = await MyProcessor.create(config)
                result = await processor.process(param1)
                return result
            
            result = asyncio.run(_async_work())
            
            # Сохранение результата
            self.set_progress(100)
            self.set_description("Completed successfully")
            self.set_mcp_result(result, "completed")
            
        except Exception as e:
            self.logger.exception(f"MyCustomJob {self.job_id}: Failed: {e}")
            self.set_mcp_error(f"Job failed: {str(e)}", "failed")
```

**Пример из проекта `svo` (`chunking_job.py`):**
```python
class ChunkingJob(QueueJobBase):
    """Job for executing chunking tasks in the queue."""
    
    def run(self) -> None:
        # Извлечение параметров из self.mcp_params
        text = self.mcp_params.get("text")
        config = self.mcp_params.get("config", {})
        
        # Установка статуса
        self.set_status("running")
        self.set_progress(10)
        
        # Импорт модулей в дочернем процессе
        from svo_chunker.chunker_pipeline import ChunkerPipeline
        
        # Async выполнение
        async def _execute_chunking():
            pipeline = await ChunkerPipeline.create(config)
            chunks = await pipeline.chunk(text, ...)
            self.set_mcp_result({"chunks": chunks}, "completed")
        
        asyncio.run(_execute_chunking())
```

**Использование кастомной задачи:**
```python
from mcp_proxy_adapter.integrations.queuemgr_integration import get_global_queue_manager

async def execute(self, context=None, **kwargs) -> SuccessResult:
    # Создание задачи через менеджер очереди
    queue_manager = await get_global_queue_manager()
    
    job_id = str(uuid.uuid4())
    result = await queue_manager.add_job(
        MyCustomJob,  # Класс задачи
        job_id,       # Уникальный ID
        {             # Параметры задачи
            "param1": validated_params.get("param1"),
            "config": config_dict,
        }
    )
    
    # Запуск задачи
    await queue_manager.start_job(job_id)
    
    # Возврат job_id клиенту
    return SuccessResult(data={"job_id": job_id})
```

##### Паттерн 4: Команда для получения статуса задачи

**Когда использовать:**
- Нужна команда для проверки статуса задачи
- Требуется кастомная обработка статуса
- Нужна обратная совместимость с клиентами

**Структура:**
```python
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    get_global_queue_manager,
    QueueJobError,
)

class MyJobStatusCommand(Command):
    """
    Команда для получения статуса задачи.
    
    Может быть прокси к queue_get_job_status или
    кастомная реализация с дополнительной логикой.
    """
    
    name = "my_job_status"
    use_queue = False  # Не использует очередь
    
    async def execute(self, context=None, **kwargs) -> SuccessResult:
        job_id = kwargs.get("job_id")
        if not job_id:
            return ErrorResult(
                message="Parameter 'job_id' is required",
                code=-32602,
            )
        
        try:
            # Получение менеджера очереди
            queue_manager = await get_global_queue_manager()
            if queue_manager is None:
                return ErrorResult(
                    message="Queue manager is not available",
                    code=-32603,
                )
            
            # Получение статуса задачи
            result = await queue_manager.get_job_status(job_id)
            
            # Возврат результата
            return SuccessResult(
                data={
                    "job_id": result.job_id,
                    "status": result.status,
                    "progress": result.progress,
                    "description": result.description,
                    "result": result.result,
                    "error": result.error,
                }
            )
        except QueueJobError as e:
            # Обработка ошибок (например, задача не найдена)
            if "not found" in str(e).lower():
                return SuccessResult(
                    data={
                        "job_id": job_id,
                        "status": "not_found",
                        "message": "Job not found (may have been auto-deleted)",
                    }
                )
            return ErrorResult(
                message=f"Queue job error: {str(e)}",
                code=-32603,
            )
```

**Пример из проекта `svo` (`embed_job_status_command.py`):**
```python
class EmbedJobStatusCommand(Command):
    """Proxy command for embed_job_status."""
    
    name = "embed_job_status"
    use_queue = False
    
    async def execute(self, context=None, **kwargs) -> SuccessResult:
        job_id = kwargs.get("job_id")
        queue_manager = await get_global_queue_manager()
        result = await queue_manager.get_job_status(job_id)
        
        return SuccessResult(
            data={
                "job_id": result.job_id,
                "status": result.status,
                "progress": result.progress,
                "result": result.result,
            }
        )
```

##### Паттерн 5: Команда с использованием CommandExecutionJob

**Когда использовать:**
- Нужно выполнить другую команду через очередь
- Требуется создание цепочки команд
- Нужна динамическая выборка команды для выполнения

**Структура:**
```python
from mcp_proxy_adapter.commands.queue.jobs import CommandExecutionJob
from mcp_proxy_adapter.integrations.queuemgr_integration import get_global_queue_manager

async def execute(self, context=None, **kwargs) -> SuccessResult:
    # Создание задачи для выполнения другой команды
    queue_manager = await get_global_queue_manager()
    
    job_id = str(uuid.uuid4())
    await queue_manager.add_job(
        CommandExecutionJob,  # Встроенный класс для выполнения команд
        job_id,
        {
            "command": "other_command",  # Имя команды для выполнения
            "params": {
                "param1": "value1",
                "param2": "value2",
            },
            "auto_import_modules": [  # Модули для импорта в дочернем процессе
                "commands.other_command",
            ],
        }
    )
    
    await queue_manager.start_job(job_id)
    
    return SuccessResult(data={"job_id": job_id})
```

#### 8. Критические изменения в API

**Старый API (больше не работает):**
```python
from mcp_proxy_adapter.queue import Task, TaskType, TaskStatus, queue_manager

task = Task(
    task_id="task_123",
    task_type=TaskType.VAST_CREATE,
    params={"bundle_id": 123}
)
queue_manager.add_task(task)
```

**Новый API (используется в embed и svo):**
```python
# Вариант 1: Простая команда (рекомендуется)
class MyCommand(Command):
    use_queue = True  # Адаптер делает все автоматически

# Вариант 2: Кастомная задача
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    QueueJobBase,
    get_global_queue_manager
)

class MyJob(QueueJobBase):
    def run(self):
        ...

queue_manager = await get_global_queue_manager()
await queue_manager.add_job(MyJob, "job_123", {"param": "value"})
```

## 🔒 АНАЛИЗ ТРЕБОВАНИЙ К ФРЕЙМВОРКУ БЕЗОПАСНОСТИ

### Текущее состояние mcp_security_framework-1.5.1

**Доступные компоненты:**
- ✅ `SecurityManager` - основной менеджер безопасности
- ✅ `CertificateManager` - управление сертификатами
- ✅ `PermissionManager` - управление разрешениями
- ✅ `AuthManager` - управление аутентификацией
- ✅ `RateLimiter` - ограничение скорости запросов

**Доступные методы SecurityManager:**
- `authenticate_user()` - аутентификация пользователя
- `check_permissions()` - проверка разрешений
- `check_rate_limit()` - проверка лимитов скорости
- `create_certificate()` - создание сертификатов
- `create_ssl_context()` - создание SSL контекста
- `get_certificate_info()` - получение информации о сертификате
- `get_security_metrics()` - получение метрик безопасности
- `get_security_status()` - получение статуса безопасности
- `perform_security_audit()` - выполнение аудита безопасности
- `revoke_certificate()` - отзыв сертификата
- `validate_configuration()` - валидация конфигурации
- `validate_request()` - валидация запроса

### Что нужно доработать в mcp_security_framework

#### 1. Поддержка специфичных операций

**Проблема:** Проект использует множество специфичных операций, которые не поддерживаются `mcp_security_framework`:

**Требуемые операции:**

1. **FTP операции:**
   - `validate_ftp_operation(operation: FtpOperation, user_roles: List[str], params: Dict) -> Tuple[bool, str]`
   - `check_ftp_permissions(user_roles: List[str], required_permissions: List[str]) -> Tuple[bool, List[str]]`
   - `audit_ftp_operation(operation: FtpOperation, user_roles: List[str], params: Dict, status: str) -> None`
   - `validate_ftp_server_access(server_config: Dict, user_roles: List[str]) -> Tuple[bool, str]`
   - `check_ftp_file_permissions(file_path: str, operation: FtpOperation, user_roles: List[str]) -> Tuple[bool, str]`
   - `manage_ftp_certificates(operation: str, cert_data: Dict) -> Tuple[bool, str, Dict]`
   - `setup_ftp_ssl(server_config: Dict, ssl_config: Dict) -> Tuple[bool, str]`

2. **Vast.ai операции:**
   - `validate_vast_ai_operation(operation: VastAiOperation, user_roles: List[str], params: Dict) -> Tuple[bool, str]`
   - `check_vast_ai_permissions(user_roles: List[str], required_permissions: List[str]) -> Tuple[bool, List[str]]`
   - `audit_vast_ai_operation(operation: VastAiOperation, user_roles: List[str], params: Dict, status: str) -> None`
   - `validate_vast_ai_api_access(api_url: str, user_roles: List[str]) -> Tuple[bool, str]`
   - `check_vast_ai_instance_permissions(instance_id: str, operation: str, user_roles: List[str]) -> Tuple[bool, str]`
   - `check_gpu_permissions(gpu_type: str, user_roles: List[str]) -> Tuple[bool, str]`

3. **Docker операции:**
   - `validate_docker_operation(operation: DockerOperation, user_roles: List[str], params: Dict) -> Tuple[bool, str]`
   - `check_docker_permissions(user_roles: List[str], required_permissions: List[str]) -> Tuple[bool, List[str]]`
   - `audit_docker_operation(operation: DockerOperation, user_roles: List[str], params: Dict, status: str) -> None`
   - `validate_docker_registry_access(registry: str, user_roles: List[str]) -> Tuple[bool, str]`
   - `check_docker_image_permissions(image_name: str, operation: str, user_roles: List[str]) -> Tuple[bool, str]`

4. **Git операции:**
   - `validate_git_operation(operation: GitOperation, user_roles: List[str], params: Dict) -> Tuple[bool, str]`
   - `check_git_permissions(user_roles: List[str], required_permissions: List[str]) -> Tuple[bool, List[str]]`
   - `audit_git_operation(operation: GitOperation, user_roles: List[str], params: Dict, status: str) -> None`
   - `validate_git_repository_access(repo_path: str, user_roles: List[str]) -> Tuple[bool, str]`
   - `check_git_branch_permissions(branch: str, operation: str, user_roles: List[str]) -> Tuple[bool, str]`

5. **Kubernetes операции:**
   - `validate_k8s_operation(operation: K8sOperation, user_roles: List[str], params: Dict) -> Tuple[bool, str]`
   - `check_k8s_permissions(user_roles: List[str], required_permissions: List[str]) -> Tuple[bool, List[str]]`
   - `audit_k8s_operation(operation: K8sOperation, user_roles: List[str], params: Dict, status: str) -> None`
   - `validate_k8s_cluster_access(cluster_name: str, user_roles: List[str]) -> Tuple[bool, str]`
   - `check_k8s_resource_permissions(resource_type: str, resource_name: str, operation: str, user_roles: List[str]) -> Tuple[bool, str]`

6. **Ollama операции:**
   - `validate_ollama_operation(operation: OllamaOperation, user_roles: List[str], params: Dict) -> Tuple[bool, str]`
   - `check_ollama_permissions(user_roles: List[str], required_permissions: List[str]) -> Tuple[bool, List[str]]`
   - `audit_ollama_operation(operation: OllamaOperation, user_roles: List[str], params: Dict, status: str) -> None`
   - `validate_ollama_api_access(api_url: str, user_roles: List[str]) -> Tuple[bool, str]`
   - `check_ollama_model_permissions(model_name: str, operation: str, user_roles: List[str]) -> Tuple[bool, str]`
   - `check_memory_permissions(memory_size: int, user_roles: List[str]) -> Tuple[bool, str]`

7. **Queue операции:**
   - `validate_queue_operation(operation: QueueOperation, user_roles: List[str], params: Dict) -> Tuple[bool, str]`
   - `check_queue_permissions(user_roles: List[str], required_permissions: List[str]) -> Tuple[bool, List[str]]`
   - `audit_queue_operation(operation: QueueOperation, user_roles: List[str], params: Dict, status: str) -> None`
   - `validate_queue_access(queue_name: str, user_roles: List[str]) -> Tuple[bool, str]`
   - `check_queue_task_permissions(task_id: str, operation: str, user_roles: List[str]) -> Tuple[bool, str]`

8. **LLM операции:**
   - `validate_llm_operation(operation: LLMOperation, user_roles: List[str], params: Dict) -> Tuple[bool, str]`
   - `check_llm_permissions(user_roles: List[str], required_permissions: List[str]) -> Tuple[bool, List[str]]`
   - `audit_llm_operation(operation: LLMOperation, user_roles: List[str], params: Dict, status: str) -> None`

9. **Vector Store операции:**
   - `validate_vector_store_operation(operation: VectorStoreOperation, user_roles: List[str], params: Dict) -> Tuple[bool, str]`
   - `check_vector_store_permissions(user_roles: List[str], required_permissions: List[str]) -> Tuple[bool, List[str]]`
   - `audit_vector_store_operation(operation: VectorStoreOperation, user_roles: List[str], params: Dict, status: str) -> None`

10. **GitHub операции:**
    - `validate_github_operation(operation: GitHubOperation, user_roles: List[str], params: Dict) -> Tuple[bool, str]`
    - `check_github_permissions(user_roles: List[str], required_permissions: List[str]) -> Tuple[bool, List[str]]`
    - `audit_github_operation(operation: GitHubOperation, user_roles: List[str], params: Dict, status: str) -> None`
    - `validate_github_api_access(api_url: str, user_roles: List[str]) -> Tuple[bool, str]`
    - `check_github_repo_permissions(repo_name: str, operation: str, user_roles: List[str]) -> Tuple[bool, str]`

#### 2. Расширяемая система операций

**Проблема:** `mcp_security_framework` не поддерживает регистрацию кастомных типов операций.

**Требуется:**
- Система регистрации кастомных типов операций
- Плагинная архитектура для добавления новых типов операций
- Универсальный интерфейс для валидации операций

**Предлагаемое решение:**
```python
from mcp_security_framework import SecurityManager, OperationType

# Регистрация кастомного типа операции
@SecurityManager.register_operation_type
class FtpOperationType(OperationType):
    UPLOAD = "ftp:upload"
    DOWNLOAD = "ftp:download"
    LIST = "ftp:list"
    DELETE = "ftp:delete"
    MKDIR = "ftp:mkdir"
    RMDIR = "ftp:rmdir"
    RENAME = "ftp:rename"
    CHMOD = "ftp:chmod"

# Использование
security_manager.validate_operation(
    FtpOperationType.UPLOAD,
    user_roles=["ftp:upload"],
    params={"remote_path": "/files/test.txt"}
)
```

#### 3. Унифицированный интерфейс для всех адаптеров

**Проблема:** Каждый адаптер имеет свой интерфейс, что усложняет интеграцию.

**Требуется:**
- Единый базовый интерфейс для всех адаптеров
- Стандартизация методов `validate_*`, `check_*`, `audit_*`
- Общий механизм проверки разрешений

**Предлагаемое решение:**
```python
from mcp_security_framework import SecurityAdapter, OperationType

class FtpSecurityAdapter(SecurityAdapter):
    """Адаптер безопасности для FTP операций."""
    
    operation_type = FtpOperationType
    
    def validate_operation(
        self,
        operation: OperationType,
        user_roles: List[str],
        params: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Валидация FTP операции."""
        # Реализация валидации
        pass
    
    def check_permissions(
        self,
        user_roles: List[str],
        required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """Проверка разрешений."""
        # Реализация проверки
        pass
    
    def audit_operation(
        self,
        operation: OperationType,
        user_roles: List[str],
        params: Dict[str, Any],
        status: str
    ) -> None:
        """Аудит операции."""
        # Реализация аудита
        pass
```

#### 4. Интеграция с существующими адаптерами

**Проблема:** Проект использует собственные адаптеры, которые нужно интегрировать с `mcp_security_framework`.

**Требуется:**
- Адаптер-обертка для существующих адаптеров
- Миграционный путь от собственных адаптеров к `mcp_security_framework`
- Обратная совместимость

**Предлагаемое решение:**
```python
from mcp_security_framework import SecurityAdapterWrapper
from ai_admin.security.ftp_security_adapter import FtpSecurityAdapter

# Обертка для существующего адаптера
class FtpSecurityAdapterWrapper(SecurityAdapterWrapper):
    def __init__(self):
        self._adapter = FtpSecurityAdapter()
    
    def validate_operation(self, operation, user_roles, params):
        return self._adapter.validate_ftp_operation(
            operation, user_roles, params
        )
    
    def check_permissions(self, user_roles, required_permissions):
        return self._adapter.check_ftp_permissions(
            user_roles, required_permissions
        )
    
    def audit_operation(self, operation, user_roles, params, status):
        return self._adapter.audit_ftp_operation(
            operation, user_roles, params, status
        )
```

#### 5. Поддержка контекста операций

**Проблема:** `mcp_security_framework` не поддерживает передачу контекста операций.

**Требуется:**
- Класс `OperationContext` для передачи контекста
- Поддержка вложенных операций
- Трекинг цепочки операций

**Предлагаемое решение:**
```python
from mcp_security_framework import OperationContext

context = OperationContext(
    user_id="user123",
    user_roles=["ftp:upload", "docker:pull"],
    request_id="req456",
    parent_operation="batch_upload",
    metadata={"ip": "192.168.1.1", "user_agent": "..."}
)

result = security_manager.validate_operation(
    FtpOperationType.UPLOAD,
    context=context,
    params={"remote_path": "/files/test.txt"}
)
```

#### 6. Улучшенный аудит операций

**Проблема:** Текущий аудит не поддерживает структурированное логирование.

**Требуется:**
- Структурированный формат аудита
- Интеграция с внешними системами аудита
- Фильтрация и поиск по аудиту

**Предлагаемое решение:**
```python
from mcp_security_framework import AuditLogger, AuditEvent

audit_logger = AuditLogger(
    backend="database",  # или "file", "elasticsearch", "splunk"
    config={"connection_string": "..."}
)

audit_event = AuditEvent(
    operation=FtpOperationType.UPLOAD,
    user_roles=["ftp:upload"],
    params={"remote_path": "/files/test.txt"},
    status="success",
    timestamp=datetime.utcnow(),
    metadata={"duration_ms": 1234, "bytes_transferred": 1024}
)

audit_logger.log(audit_event)
```

### 🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ТРЕБОВАНИЙ К mcp_security_framework

**На основе анализа структуры фреймворка и требований проекта `vast_srv`:**

**⚠️ ВАЖНО: Принцип универсальности фреймворка**

`mcp_security_framework` используется в **разных проектах**, поэтому:

- ✅ **МОЖНО добавлять:** Универсальные компоненты (базовые классы, интерфейсы, механизмы расширения)
- ❌ **НЕЛЬЗЯ добавлять:** Специфичные для проекта компоненты (FTP, Docker, K8s адаптеры и т.д.)

**Принцип разделения ответственности:**
- **Фреймворк** предоставляет универсальные механизмы (базовые классы, регистрация, аудит, контекст)
- **Проекты** создают свои адаптеры на основе универсальных механизмов фреймворка

#### ✅ ОБНОВЛЕНИЕ: mcp_security_framework-1.6.0

**Статус:** Все запрошенные универсальные компоненты **ДОБАВЛЕНЫ** в версии 1.6.0!

**Доступные компоненты в версии 1.6.0:**
- ✅ `OperationType` - базовый класс для типов операций
- ✅ `SecurityAdapter` - абстрактный базовый класс для адаптеров
- ✅ `OperationContext` - класс для передачи контекста операций
- ✅ `AuditLogger` - структурированное логирование аудита
- ✅ `AuditEvent` - класс для событий аудита
- ✅ `AuditStatus` - перечисление статусов аудита
- ✅ `SecurityAdapterWrapper` - обертка для legacy-адаптеров
- ✅ `SecurityManager.register_adapter()` - регистрация адаптеров
- ✅ `SecurityManager.get_adapter()` - получение адаптера
- ✅ `SecurityManager.validate_operation()` - валидация через адаптер
- ✅ `SecurityManager.list_adapters()` - список адаптеров

**Проверка доступности:**
```python
from mcp_security_framework import (
    SecurityAdapter, OperationType, OperationContext,
    AuditLogger, AuditEvent, AuditStatus, SecurityAdapterWrapper
)
# ✅ Все компоненты доступны!
```

**Changelog версии 1.6.0:**
- Добавлена система адаптеров безопасности
- Добавлен контекст операций
- Добавлен структурированный аудит
- Добавлена поддержка legacy-адаптеров
- Полная обратная совместимость
- 1104 теста проходят (1037 старых + 67 новых)

#### Текущее состояние mcp_security_framework-1.6.0 (обновлено)

**Доступные компоненты:**
- ✅ `SecurityManager` - основной менеджер безопасности
- ✅ `AuthManager` - аутентификация (API keys, JWT, certificates, basic auth)
- ✅ `PermissionManager` - управление разрешениями и ролями
- ✅ `CertificateManager` - управление сертификатами SSL/mTLS
- ✅ `RateLimiter` - ограничение скорости запросов
- ✅ `SSLManager` - управление SSL/TLS контекстами

**Доступные методы SecurityManager:**
- `validate_request()` - валидация запроса
- `check_permissions()` - проверка разрешений
- `check_rate_limit()` - проверка лимитов скорости
- `authenticate_user()` - аутентификация пользователя
- `create_certificate()` - создание сертификатов
- `validate_certificate()` - валидация сертификатов
- `perform_security_audit()` - выполнение аудита безопасности

**Что НЕ поддерживается:**
- ❌ Специфичные типы операций (FTP, Docker, K8s, Git, Vast.ai и т.д.)
- ❌ Расширяемая система операций
- ❌ Плагинная архитектура для адаптеров
- ❌ Контекст операций
- ❌ Структурированный аудит операций

#### Анализ требований проекта vast_srv

**В проекте используется 10+ типов адаптеров безопасности:**

1. **FtpSecurityAdapter** - 8 типов операций (UPLOAD, DOWNLOAD, LIST, DELETE, MKDIR, RMDIR, RENAME, CHMOD)
2. **DockerSecurityAdapter** - 30+ типов операций (BUILD, RUN, PUSH, PULL, LOGIN, COPY, EXEC, STOP, START, RESTART, REMOVE, INSPECT, LOGS, HUB_IMAGES, NETWORK_*, VOLUME_*, TAG и т.д.)
3. **K8sSecurityAdapter** - 15+ типов операций (DEPLOY, SCALE, DELETE, GET, LOGS, EXEC, DEPLOYMENT_CREATE, POD_*, SERVICE_*, CONFIGMAP_*, NAMESPACE_*, CLUSTER_*, CERTIFICATE_*, MTLS_SETUP)
4. **GitSecurityAdapter** - 10+ типов операций (CLONE, PUSH, PULL, COMMIT, BRANCH, MERGE, TAG, RESET, REVERT, CHERRY_PICK)
5. **VastAiSecurityAdapter** - 12 типов операций (SEARCH, CREATE, DESTROY, INSTANCES, SSH, LOGS, STOP, START, RESTART, INSPECT, CONFIG, BILLING, API_ACCESS)
6. **GitHubSecurityAdapter** - 8+ типов операций (CREATE_REPO, LIST_REPOS, CLONE, PUSH, PULL, CREATE_BRANCH, MERGE, DELETE_REPO, API_ACCESS)
7. **OllamaSecurityAdapter** - 6+ типов операций (PULL, RUN, LIST, STATUS, API_ACCESS)
8. **QueueSecurityAdapter** - 5+ типов операций (ADD, REMOVE, CANCEL, GET, LIST)
9. **VectorStoreSecurityAdapter** - 10+ типов операций (DEPLOY, CONFIGURE, SCALE, UPDATE, DELETE, STATUS, LOGS, BACKUP, RESTORE, MONITOR)
10. **LLMSecurityAdapter** - 12+ типов операций (INFERENCE, TRAIN, FINE_TUNE, EVALUATE, DEPLOY, SCALE, MONITOR, LOGS, BACKUP, RESTORE, CONFIGURE, DELETE)
11. **SystemSecurityAdapter** - системные операции
12. **KindSecurityAdapter** - Kind кластеры
13. **ArgoCDSecurityAdapter** - ArgoCD операции
14. **SSLSecurityAdapter** - SSL операции (уже частично поддерживается через CertificateManager)

**Общий паттерн методов в адаптерах:**
- `validate_*_operation()` - валидация операции
- `check_*_permissions()` - проверка разрешений
- `audit_*_operation()` - аудит операции
- `validate_*_access()` - валидация доступа к ресурсу
- `check_*_*_permissions()` - проверка разрешений для конкретного ресурса

#### Что нужно добавить в mcp_security_framework

##### 1. Базовый класс SecurityAdapter

**Проблема:** Нет базового класса для создания адаптеров безопасности.

**Решение:**
```python
# mcp_security_framework/core/security_adapter.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum

class OperationType(Enum):
    """Базовый класс для типов операций."""
    pass

class SecurityAdapter(ABC):
    """
    Базовый класс для адаптеров безопасности.
    
    Все адаптеры должны наследоваться от этого класса
    и реализовывать стандартные методы.
    """
    
    @property
    @abstractmethod
    def operation_type(self) -> type[OperationType]:
        """Тип операций, поддерживаемых адаптером."""
        pass
    
    @abstractmethod
    def validate_operation(
        self,
        operation: OperationType,
        user_roles: List[str],
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Валидация операции.
        
        Args:
            operation: Тип операции
            user_roles: Роли пользователя
            params: Параметры операции
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def check_permissions(
        self,
        user_roles: List[str],
        required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Проверка разрешений.
        
        Args:
            user_roles: Роли пользователя
            required_permissions: Требуемые разрешения
            
        Returns:
            Tuple[bool, List[str]]: (has_permission, missing_permissions)
        """
        pass
    
    @abstractmethod
    def audit_operation(
        self,
        operation: OperationType,
        user_roles: List[str],
        params: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ) -> None:
        """
        Аудит операции.
        
        Args:
            operation: Тип операции
            user_roles: Роли пользователя
            params: Параметры операции
            status: Статус операции (success, failed, denied)
        """
        pass
```

##### 2. Регистрация адаптеров в SecurityManager

**Проблема:** SecurityManager не поддерживает регистрацию кастомных адаптеров.

**Решение:**
```python
# Добавить в SecurityManager
class SecurityManager:
    def __init__(self, config: SecurityConfig):
        # ... существующий код ...
        self._adapters: Dict[str, SecurityAdapter] = {}
    
    def register_adapter(
        self,
        name: str,
        adapter: SecurityAdapter
    ) -> None:
        """
        Регистрация адаптера безопасности.
        
        Args:
            name: Имя адаптера (например, "ftp", "docker", "k8s")
            adapter: Экземпляр адаптера
        """
        self._adapters[name] = adapter
        self.logger.info(f"Registered security adapter: {name}")
    
    def get_adapter(self, name: str) -> Optional[SecurityAdapter]:
        """Получить адаптер по имени."""
        return self._adapters.get(name)
    
    def validate_operation(
        self,
        adapter_name: str,
        operation: OperationType,
        user_roles: List[str],
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Валидация операции через адаптер.
        
        Args:
            adapter_name: Имя адаптера
            operation: Тип операции
            user_roles: Роли пользователя
            params: Параметры операции
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        adapter = self.get_adapter(adapter_name)
        if not adapter:
            return False, f"Adapter '{adapter_name}' not found"
        
        return adapter.validate_operation(operation, user_roles, params)
```

##### 3. Система расширения для кастомных адаптеров (НЕ стандартные адаптеры!)

**ВАЖНО:** Фреймворк используется в разных проектах, поэтому **НЕ нужно** создавать специфичные адаптеры (FTP, Docker, K8s и т.д.) внутри фреймворка.

**Решение:** Создать универсальную систему расширения, чтобы проекты могли добавлять свои адаптеры:

```python
# mcp_security_framework/core/security_adapter.py
# Базовый класс уже определен выше

# Проекты создают свои адаптеры в своем коде:
# ai_admin/security/ftp_security_adapter.py
from mcp_security_framework.core.security_adapter import SecurityAdapter, OperationType
from enum import Enum

class FtpOperation(OperationType):
    UPLOAD = "ftp:upload"
    DOWNLOAD = "ftp:download"
    LIST = "ftp:list"
    DELETE = "ftp:delete"
    MKDIR = "ftp:mkdir"
    RMDIR = "ftp:rmdir"
    RENAME = "ftp:rename"
    CHMOD = "ftp:chmod"

class FtpSecurityAdapter(SecurityAdapter):
    """Адаптер безопасности для FTP операций - создается в проекте."""
    
    operation_type = FtpOperation
    
    def __init__(self, permission_manager: PermissionManager):
        self.permission_manager = permission_manager
        # Маппинг операций на разрешения
        self.operation_permissions = {
            FtpOperation.UPLOAD: ["ftp:upload", "ftp:admin"],
            FtpOperation.DOWNLOAD: ["ftp:download", "ftp:admin"],
            # ... и т.д.
        }
    
    def validate_operation(self, operation, user_roles, params):
        required_perms = self.operation_permissions.get(operation, [])
        result = self.permission_manager.validate_access(
            user_roles, required_perms
        )
        return result.is_valid, result.error_message or ""
    
    def check_permissions(self, user_roles, required_permissions):
        result = self.permission_manager.validate_access(
            user_roles, required_permissions
        )
        return result.is_valid, list(result.missing_permissions)
    
    def audit_operation(self, operation, user_roles, params, status):
        # Логирование операции
        pass

# Регистрация в проекте:
# ai_admin/security/__init__.py или в startup
from mcp_security_framework import SecurityManager
from ai_admin.security.ftp_security_adapter import FtpSecurityAdapter

security_manager = SecurityManager(config)
security_manager.register_adapter("ftp", FtpSecurityAdapter(permission_manager))
```

**Принцип:**
- ✅ Фреймворк предоставляет **базовый класс** и **систему регистрации**
- ✅ Проекты создают **свои адаптеры** в своем коде
- ✅ Проекты регистрируют адаптеры через `SecurityManager.register_adapter()`
- ❌ Фреймворк **НЕ содержит** специфичные адаптеры (FTP, Docker и т.д.)

##### 4. Контекст операций

**Проблема:** Нет поддержки контекста операций (user_id, request_id, metadata).

**Решение:**
```python
# mcp_security_framework/schemas/models.py
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class OperationContext:
    """Контекст операции для передачи дополнительной информации."""
    user_id: Optional[str] = None
    user_roles: List[str] = None
    request_id: Optional[str] = None
    parent_operation: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.user_roles is None:
            self.user_roles = []
        if self.metadata is None:
            self.metadata = {}
```

**Использование:**
```python
context = OperationContext(
    user_id="user123",
    user_roles=["ftp:upload"],
    request_id="req456",
    metadata={"ip": "192.168.1.1"}
)

result = security_manager.validate_operation(
    "ftp", FtpOperation.UPLOAD, context, params
)
```

##### 5. Структурированный аудит

**Проблема:** Текущий аудит не поддерживает структурированное логирование.

**Решение:**
```python
# mcp_security_framework/core/audit_logger.py
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class AuditStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    DENIED = "denied"

@dataclass
class AuditEvent:
    """Событие аудита."""
    operation: str
    operation_type: str
    user_roles: List[str]
    params: Dict[str, Any]
    status: AuditStatus
    timestamp: datetime
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для логирования."""
        return {
            **asdict(self),
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
        }

class AuditLogger:
    """Логгер для аудита операций."""
    
    def __init__(self, backend: str = "file", config: Optional[Dict] = None):
        self.backend = backend
        self.config = config or {}
        # Инициализация бэкенда (file, database, elasticsearch и т.д.)
    
    def log(self, event: AuditEvent) -> None:
        """Логирование события аудита."""
        # Реализация логирования в зависимости от бэкенда
        pass
```

##### 6. Интеграция с существующими адаптерами

**Проблема:** Проект использует собственные адаптеры, которые нужно интегрировать.

**Решение:** Создать адаптер-обертку:

```python
# mcp_security_framework/core/adapter_wrapper.py
from mcp_security_framework.core.security_adapter import SecurityAdapter
from typing import Any

class SecurityAdapterWrapper(SecurityAdapter):
    """
    Обертка для существующих адаптеров проекта.
    
    Позволяет использовать существующие адаптеры
    через интерфейс mcp_security_framework.
    """
    
    def __init__(self, legacy_adapter: Any, operation_type: type):
        """
        Инициализация обертки.
        
        Args:
            legacy_adapter: Существующий адаптер из проекта
            operation_type: Тип операций адаптера
        """
        self._adapter = legacy_adapter
        self._operation_type = operation_type
    
    @property
    def operation_type(self) -> type:
        return self._operation_type
    
    def validate_operation(self, operation, user_roles, params):
        # Вызов метода существующего адаптера
        method_name = f"validate_{self._adapter.__class__.__name__.lower().replace('securityadapter', '')}_operation"
        if hasattr(self._adapter, method_name):
            return getattr(self._adapter, method_name)(operation, user_roles, params)
        # Fallback на общий метод
        return self._adapter.validate_operation(operation, user_roles, params)
    
    def check_permissions(self, user_roles, required_permissions):
        method_name = f"check_{self._adapter.__class__.__name__.lower().replace('securityadapter', '')}_permissions"
        if hasattr(self._adapter, method_name):
            return getattr(self._adapter, method_name)(user_roles, required_permissions)
        return self._adapter.check_permissions(user_roles, required_permissions)
    
    def audit_operation(self, operation, user_roles, params, status):
        method_name = f"audit_{self._adapter.__class__.__name__.lower().replace('securityadapter', '')}_operation"
        if hasattr(self._adapter, method_name):
            return getattr(self._adapter, method_name)(operation, user_roles, params, status)
        return self._adapter.audit_operation(operation, user_roles, params, status)
```

### Рекомендации по доработке mcp_security_framework

#### Вариант 1: Минимальные изменения (рекомендуется для быстрого старта)

**Что сделать:**
1. Добавить поддержку FTP операций в `SecurityManager`
2. Создать систему регистрации кастомных типов операций
3. Добавить универсальные методы `validate_operation()`, `check_permissions()`, `audit_operation()`

**Преимущества:**
- Минимальные изменения в существующем коде
- Быстрая реализация
- Обратная совместимость

**Недостатки:**
- Не покрывает все типы операций
- Требует расширения для каждого нового типа

#### Вариант 2: Полная интеграция

**Что сделать:**
1. Создать плагинную архитектуру для операций
2. Реализовать все типы операций из проекта
3. Мигрировать все адаптеры на `mcp_security_framework`

**Преимущества:**
- Полная интеграция
- Единая система безопасности
- Упрощенная поддержка

**Недостатки:**
- Большой объем работы
- Требует изменений во всех командах
- Риск регрессий

#### Вариант 3: Гибридный подход (оптимально)

**Что сделать:**
1. Использовать `mcp_security_framework` для базовых операций (SSL, сертификаты, аутентификация)
2. Сохранить собственные адаптеры для специфичных операций
3. Создать адаптер-обертку для интеграции

**Преимущества:**
- Использует сильные стороны обоих подходов
- Минимальные изменения в существующем коде
- Гибкость для будущих расширений

**Недостатки:**
- Две системы безопасности
- Требует поддержки обеих систем

### Итоговые рекомендации

**Для запуска проекта на mcp_security_framework:**

#### Краткосрочно (для быстрого запуска - 1-2 недели)

**Что сделать:**
1. ✅ Использовать `mcp_security_framework` только для SSL/сертификатов через `CertificateManager`
2. ✅ Сохранить собственные адаптеры (`ai_admin.security.*`) для всех специфичных операций
3. ✅ Создать адаптер-обертку `SecurityAdapterWrapper` для интеграции существующих адаптеров с `SecurityManager`
4. ✅ Использовать `PermissionManager` из фреймворка для проверки разрешений

**Преимущества:**
- Минимальные изменения в коде
- Быстрый запуск проекта
- Обратная совместимость
- Использование сильных сторон обоих подходов

**Недостатки:**
- Две системы безопасности (нужна поддержка обеих)
- Неполная интеграция

#### Среднесрочно (для улучшения - 1-2 месяца)

**Что добавить в mcp_security_framework:**

1. ✅ **Базовый класс SecurityAdapter** (`mcp_security_framework/core/security_adapter.py`)
   - Абстрактный класс с методами `validate_operation()`, `check_permissions()`, `audit_operation()`
   - Базовый класс `OperationType` для типов операций

2. ✅ **Регистрация адаптеров в SecurityManager**
   - Метод `register_adapter(name, adapter)`
   - Метод `get_adapter(name)`
   - Метод `validate_operation(adapter_name, operation, user_roles, params)`

3. ✅ **Система расширения для кастомных адаптеров** (НЕ стандартные адаптеры!)
   - Базовый класс `SecurityAdapter` для создания адаптеров в проектах
   - Примеры создания кастомных адаптеров в документации
   - **ВАЖНО:** Специфичные адаптеры (FTP, Docker и т.д.) создаются в проектах, не в фреймворке

4. ✅ **Контекст операций** (`OperationContext`)
   - Класс для передачи user_id, request_id, metadata
   - Поддержка вложенных операций

5. ✅ **Структурированный аудит** (`AuditLogger`, `AuditEvent`)
   - Структурированное логирование операций
   - Поддержка разных бэкендов (file, database, elasticsearch)

**Что сделать в проекте vast_srv:**
1. ✅ Создать адаптеры на основе `SecurityAdapter` в `ai_admin/security/`
2. ✅ Зарегистрировать адаптеры через `SecurityManager.register_adapter()`
3. ✅ Использовать `OperationContext` для передачи контекста
4. ✅ Использовать `AuditLogger` для логирования операций
5. ✅ Использовать `SecurityAdapterWrapper` для миграции существующих адаптеров

**Преимущества:**
- Единая система безопасности
- Расширяемость через плагинную архитектуру
- Упрощенная поддержка

**Недостатки:**
- Требует изменений в коде проекта
- Риск регрессий при миграции

#### Долгосрочно (для полной интеграции - 3-6 месяцев)

**Что сделать в проекте vast_srv:**
1. ✅ Мигрировать все адаптеры на интерфейс `SecurityAdapter` из фреймворка
2. ✅ Использовать `SecurityManager` для всех операций безопасности
3. ✅ Использовать `OperationContext` и `AuditLogger` везде
4. ✅ Удалить legacy-код, если он больше не нужен

**ВАЖНО:** Адаптеры остаются в проекте, но используют универсальные интерфейсы из фреймворка!

**Преимущества:**
- Полная интеграция
- Единая система безопасности
- Упрощенная поддержка и тестирование
- Стандартизация подходов

**Недостатки:**
- Большой объем работы
- Требует изменений во всех командах
- Риск регрессий

### ✅ СТАТУС: Все компоненты добавлены в mcp_security_framework-1.6.0!

**Все запрошенные компоненты уже реализованы в версии 1.6.0:**
- ✅ `SecurityAdapter` - базовый класс для адаптеров
- ✅ `OperationType` - базовый класс для типов операций
- ✅ `OperationContext` - контекст операций
- ✅ `AuditLogger` - структурированное логирование
- ✅ `AuditEvent` - события аудита
- ✅ `AuditStatus` - статусы аудита
- ✅ `SecurityAdapterWrapper` - обертка для legacy-адаптеров
- ✅ `SecurityManager.register_adapter()` - регистрация адаптеров
- ✅ `SecurityManager.get_adapter()` - получение адаптера
- ✅ `SecurityManager.validate_operation()` - валидация через адаптер
- ✅ `SecurityManager.list_adapters()` - список адаптеров

**Changelog версии 1.6.0:**
- 1104 теста проходят (1037 старых + 67 новых)
- Полная обратная совместимость
- 93% покрытие тестами для новой функциональности

### План действий для интеграции в проект vast_srv

#### Этап 1: Обновление зависимостей (1 день)

1. ✅ Обновить `requirements.txt`:
   ```txt
   mcp-security-framework>=1.6.0
   ```

2. ✅ Установить обновленную версию:
   ```bash
   pip install -U mcp-security-framework>=1.6.0
   ```

#### Этап 2: Создание адаптеров на основе SecurityAdapter (1-2 недели)

**В проекте vast_srv (НЕ в фреймворке!):**

1. Создать адаптеры на основе `SecurityAdapter`:
   - `ai_admin/security/ftp_security_adapter.py` - наследуется от `SecurityAdapter`
   - `ai_admin/security/docker_security_adapter.py` - наследуется от `SecurityAdapter`
   - `ai_admin/security/k8s_security_adapter.py` - наследуется от `SecurityAdapter`
   - И так далее для всех адаптеров

2. Пример структуры адаптера:
   ```python
   from mcp_security_framework import SecurityAdapter, OperationType, PermissionManager
   from enum import Enum
   
   class FtpOperation(OperationType):
       UPLOAD = "ftp:upload"
       DOWNLOAD = "ftp:download"
       # ...
   
   class FtpSecurityAdapter(SecurityAdapter):
       operation_type = FtpOperation
       
       def __init__(self, permission_manager: PermissionManager):
           self.permission_manager = permission_manager
           # ...
       
       def validate_operation(self, operation, user_roles, params, context=None):
           # Реализация валидации
           pass
       
       def check_permissions(self, user_roles, required_permissions):
           # Реализация проверки разрешений
           pass
       
       def audit_operation(self, operation, user_roles, params, status, context=None):
           # Реализация аудита
           pass
   ```

#### Этап 3: Регистрация адаптеров (1 день)

1. Зарегистрировать адаптеры в `SecurityManager`:
   ```python
   # В startup коде проекта (например, ai_admin/core/server_setup.py)
   from mcp_security_framework import SecurityManager
   from ai_admin.security.ftp_security_adapter import FtpSecurityAdapter
   from ai_admin.security.docker_security_adapter import DockerSecurityAdapter
   # ... и т.д.
   
   security_manager = SecurityManager(config)
   
   # Регистрация адаптеров
   security_manager.register_adapter("ftp", FtpSecurityAdapter(permission_manager))
   security_manager.register_adapter("docker", DockerSecurityAdapter(permission_manager))
   security_manager.register_adapter("k8s", K8sSecurityAdapter(permission_manager))
   # ... и т.д.
   ```

#### Этап 4: Использование OperationContext и AuditLogger (1 неделя)

**В проекте vast_srv (НЕ в фреймворке!):**

1. Создать адаптеры на основе `SecurityAdapter`:
   - `ai_admin/security/ftp_security_adapter.py` - наследуется от `SecurityAdapter`
   - `ai_admin/security/docker_security_adapter.py` - наследуется от `SecurityAdapter`
   - И так далее для всех адаптеров

2. Зарегистрировать адаптеры в `SecurityManager`:
   ```python
   # В startup коде проекта
   security_manager.register_adapter("ftp", FtpSecurityAdapter(...))
   security_manager.register_adapter("docker", DockerSecurityAdapter(...))
   ```

3. Использовать `SecurityAdapterWrapper` для миграции существующих адаптеров (если нужно)

4. Тестирование и отладка

### Выводы

**✅ СТАТУС: Все необходимые компоненты ДОБАВЛЕНЫ в mcp_security_framework-1.6.0!**

**Для переезда проекта на mcp_security_framework (универсальные компоненты):**

1. ✅ **Базовый класс SecurityAdapter** - **ДОБАВЛЕН в 1.6.0** - универсальный интерфейс для всех адаптеров
2. ✅ **Регистрация адаптеров в SecurityManager** - **ДОБАВЛЕНА в 1.6.0** - универсальная плагинная архитектура
3. ✅ **Контекст операций (OperationContext)** - **ДОБАВЛЕН в 1.6.0** - универсальный механизм передачи контекста
4. ✅ **Структурированный аудит (AuditLogger, AuditEvent)** - **ДОБАВЛЕН в 1.6.0** - универсальное логирование
5. ✅ **Адаптер-обертка (SecurityAdapterWrapper)** - **ДОБАВЛЕН в 1.6.0** - универсальная интеграция с legacy-адаптерами

**Проверка доступности (выполнено):**
```python
from mcp_security_framework import (
    SecurityAdapter, OperationType, OperationContext,
    AuditLogger, AuditEvent, AuditStatus, SecurityAdapterWrapper
)
# ✅ Все компоненты доступны в версии 1.6.0!
```

**НЕ нужно добавлять в фреймворк:**
- ❌ Специфичные адаптеры (FTP, Docker, K8s и т.д.) - это должно быть в проектах
- ❌ Специфичные типы операций - проекты создают свои
- ❌ Бизнес-логика проектов - только универсальные механизмы

**Принцип разделения ответственности:**
- **Фреймворк** предоставляет:
  - Базовые классы и интерфейсы
  - Систему регистрации и управления
  - Универсальные механизмы (аудит, контекст)
- **Проекты** создают:
  - Свои адаптеры на основе базовых классов
  - Свои типы операций
  - Свою бизнес-логику безопасности

**✅ С этими доработками (уже добавлены в 1.6.0):**
- ✅ Возможна полная интеграция с `mcp_security_framework`
- ✅ Единая система безопасности для всех операций
- ✅ Расширяемость через плагинную архитектуру (проекты добавляют свои адаптеры)
- ✅ Упрощенная поддержка и тестирование
- ✅ Фреймворк остается универсальным для всех проектов
- ✅ Полная обратная совместимость (1104 теста проходят)

**Следующие шаги для проекта vast_srv:**
1. ✅ Обновить `requirements.txt` до `mcp_security_framework>=1.6.0`
2. ✅ Создать адаптеры на основе `SecurityAdapter` в `ai_admin/security/`
3. ✅ Зарегистрировать адаптеры через `SecurityManager.register_adapter()`
4. ✅ Использовать `OperationContext` для передачи контекста
5. ✅ Использовать `AuditLogger` для структурированного логирования
6. ✅ Использовать `SecurityAdapterWrapper` для миграции существующих адаптеров (если нужно)

## 📋 ПОЛНЫЙ ПЛАН МИГРАЦИИ (пошаговый)

### Этап 0: Подготовка (1 день)

#### 0.1. Обновление зависимостей

**Действия:**
1. Обновить `requirements.txt`:
   ```txt
   mcp-proxy-adapter>=6.9.102
   mcp_security_framework>=1.6.0
   queuemgr>=1.0.13
   werkzeug>=3.1.4
   ```

2. Установить обновленные пакеты:
   ```bash
   source .venv/bin/activate  # Активировать виртуальное окружение
   pip install -U mcp-proxy-adapter>=6.9.102
   pip install -U mcp_security_framework>=1.6.0
   pip install -U queuemgr>=1.0.13
   pip install -U werkzeug>=3.1.4
   ```

3. Проверить установку:
   ```bash
   python -c "from mcp_proxy_adapter.integrations.queuemgr_integration import get_global_queue_manager; print('✅ Queue integration OK')"
   python -c "from mcp_security_framework import SecurityAdapter, OperationType; print('✅ Security framework OK')"
   ```

#### 0.2. Обновление конфигурации

**Действия:**
1. Добавить секцию `queue_manager` в `config.json`:
   ```json
   {
     "queue_manager": {
       "enabled": true,
       "in_memory": true,
       "max_concurrent_jobs": 10,
       "completed_job_retention_seconds": 3600
     }
   }
   ```

2. Проверить структуру `config.json` на соответствие новой версии адаптера

### Этап 1: Миграция очереди (2-3 дня)

#### 1.1. Замена импортов очереди

**Проблема:** 10 команд используют несуществующий API `mcp_proxy_adapter.queue`

**Команды для обновления:**
1. `commands/vast_create_command.py`
2. `commands/vast_destroy_command.py`
3. `commands/ssh_exec_command.py`
4. `commands/ftp_upload_command.py`
5. `commands/ftp_mkdir_command.py`
6. `commands/ftp_rename_command.py`
7. `commands/ftp_info_command.py`
8. `commands/docker_pull_command.py`
9. `commands/queue_remove_task_command.py`
10. `commands/queue_cancel_task_command.py`

**Действия для каждой команды:**

**Было:**
```python
from mcp_proxy_adapter.queue import Task, TaskType, TaskStatus
from mcp_proxy_adapter.queue import queue_manager
```

**Должно быть:**
```python
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    get_global_queue_manager,
    QueueJobBase,
    QueueJobStatus
)
```

#### 1.2. Обновление API очереди

**Изменения в использовании:**

**Было:**
```python
task = Task(task_type=TaskType.SSH_EXEC, params={...})
task_id = await queue_manager.add_task(task)
```

**Должно быть (вариант 1 - простая команда):**
```python
class MyCommand(Command):
    name = "my_command"
    use_queue = True  # Адаптер автоматически создаст задачу
    
    async def execute(self, context=None, **kwargs):
        # Обычная логика команды
        # Адаптер обернет в CommandExecutionJob
        ...
```

**Должно быть (вариант 2 - кастомная задача):**
```python
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    QueueJobBase,
    get_global_queue_manager
)

class MyCustomJob(QueueJobBase):
    def run(self):
        # Логика задачи
        params = self.mcp_params
        self.set_status("running")
        # ... выполнение ...
        self.set_mcp_result(result, "completed")

# В команде:
queue_manager = await get_global_queue_manager()
job_id = str(uuid.uuid4())
await queue_manager.add_job(MyCustomJob, job_id, params)
await queue_manager.start_job(job_id)
```

#### 1.3. Миграция команд с собственным менеджером

**Команды для миграции:**
1. `commands/ftp_download_command.py`
2. `commands/ftp_list_command.py`
3. `commands/ftp_delete_command.py`

**Было:**
```python
from ai_admin.task_queue.task_queue_manager import TaskQueueManager, Task, TaskType

task_queue = TaskQueueManager()
task = Task(task_type=TaskType.FTP_DOWNLOAD, params={...})
task_id = await task_queue.add_task(task)
```

**Должно быть:**
```python
# Вариант 1: Использовать use_queue = True
class FtpDownloadCommand(Command):
    use_queue = True
    # ...

# Вариант 2: Использовать новый API
from mcp_proxy_adapter.integrations.queuemgr_integration import get_global_queue_manager

queue_manager = await get_global_queue_manager()
# ... использовать новый API
```

#### 1.4. Обновление команд статуса очереди

**Команды для обновления:**
- `commands/queue_remove_task_command.py`
- `commands/queue_cancel_task_command.py`
- Все команды, которые получают статус задач

**Было:**
```python
task = await queue_manager.get_task(task_id)
await queue_manager.cancel_task(task_id, force=force)
await queue_manager.remove_task(task_id, force=force)
```

**Должно быть:**
```python
from mcp_proxy_adapter.integrations.queuemgr_integration import get_global_queue_manager

queue_manager = await get_global_queue_manager()
if queue_manager is None:
    return ErrorResult(message="Queue manager is not available")

# Получение статуса
result = await queue_manager.get_job_status(job_id)
# result.status, result.progress, result.result, result.error

# Остановка задачи
result = await queue_manager.stop_job(job_id)

# Удаление задачи
result = await queue_manager.delete_job(job_id)
```

#### 1.5. Обновление dependency_injection.py

**Действия:**
1. Удалить регистрацию собственного менеджера очереди:
   ```python
   # УДАЛИТЬ:
   from ai_admin.queue.queue_manager import queue_manager, QueueManager
   container.register_singleton(QueueManager, queue_manager)
   ```

2. Адаптер автоматически инициализирует очередь при старте сервера (если `queue_manager.enabled: true` в конфиге)

### Этап 2: Миграция безопасности (1-2 недели, опционально)

#### 2.1. Создание адаптеров на основе SecurityAdapter

**Действия:**
1. Для каждого существующего адаптера создать новый на основе `SecurityAdapter`:
   - `ai_admin/security/ftp_security_adapter.py` → наследуется от `SecurityAdapter`
   - `ai_admin/security/docker_security_adapter.py` → наследуется от `SecurityAdapter`
   - `ai_admin/security/k8s_security_adapter.py` → наследуется от `SecurityAdapter`
   - И так далее для всех адаптеров

2. Пример структуры:
   ```python
   from mcp_security_framework import SecurityAdapter, OperationType, PermissionManager
   from enum import Enum
   
   class FtpOperation(OperationType):
       UPLOAD = "ftp:upload"
       DOWNLOAD = "ftp:download"
       LIST = "ftp:list"
       DELETE = "ftp:delete"
       MKDIR = "ftp:mkdir"
       RMDIR = "ftp:rmdir"
       RENAME = "ftp:rename"
       CHMOD = "ftp:chmod"
   
   class FtpSecurityAdapter(SecurityAdapter):
       operation_type = FtpOperation
       
       def __init__(self, permission_manager: PermissionManager):
           self.permission_manager = permission_manager
           # Маппинг операций на разрешения
           self.operation_permissions = {
               FtpOperation.UPLOAD: ["ftp:upload", "ftp:admin"],
               FtpOperation.DOWNLOAD: ["ftp:download", "ftp:admin"],
               # ...
           }
       
       def validate_operation(self, operation, user_roles, params, context=None):
           required_perms = self.operation_permissions.get(operation, [])
           result = self.permission_manager.validate_access(user_roles, required_perms)
           return result.is_valid, result.error_message or ""
       
       def check_permissions(self, user_roles, required_permissions):
           result = self.permission_manager.validate_access(user_roles, required_permissions)
           return result.is_valid, list(result.missing_permissions)
       
       def audit_operation(self, operation, user_roles, params, status, context=None):
           # Логирование через AuditLogger
           pass
   ```

#### 2.2. Регистрация адаптеров в SecurityManager

**Действия:**
1. В `ai_admin/security_integration.py` или `ai_admin/core/server_setup.py`:
   ```python
   from mcp_security_framework import SecurityManager
   from ai_admin.security.ftp_security_adapter import FtpSecurityAdapter
   from ai_admin.security.docker_security_adapter import DockerSecurityAdapter
   # ... и т.д.
   
   # После инициализации SecurityManager
   security_manager = SecurityManager(security_config)
   
   # Регистрация адаптеров
   security_manager.register_adapter("ftp", FtpSecurityAdapter(permission_manager))
   security_manager.register_adapter("docker", DockerSecurityAdapter(permission_manager))
   security_manager.register_adapter("k8s", K8sSecurityAdapter(permission_manager))
   # ... и т.д.
   ```

#### 2.3. Использование SecurityAdapterWrapper для legacy-адаптеров

**Если нужно сохранить существующие адаптеры временно:**

```python
from mcp_security_framework import SecurityAdapterWrapper
from ai_admin.security.ftp_security_adapter import FtpSecurityAdapter as LegacyFtpAdapter

# Обертка для существующего адаптера
class FtpSecurityAdapterWrapper(SecurityAdapterWrapper):
    def __init__(self):
        self._adapter = LegacyFtpAdapter()
        super().__init__(self._adapter, FtpOperation)
    
    def validate_operation(self, operation, user_roles, params, context=None):
        return self._adapter.validate_ftp_operation(operation, user_roles, params)
    
    def check_permissions(self, user_roles, required_permissions):
        return self._adapter.check_ftp_permissions(user_roles, required_permissions)
    
    def audit_operation(self, operation, user_roles, params, status, context=None):
        return self._adapter.audit_ftp_operation(operation, user_roles, params, status)

# Регистрация обертки
security_manager.register_adapter("ftp", FtpSecurityAdapterWrapper())
```

### Этап 3: Обновление других компонентов (1-2 дня)

#### 3.1. Проверка импортов ошибок

**Действия:**
1. Проверить все импорты `CommandError`, `InternalError`, `AuthorizationError`
2. Убедиться, что используются правильные названия из `mcp_proxy_adapter.core.errors`
3. Обновить импорты, если изменились названия

#### 3.2. Проверка импортов результатов команд

**Действия:**
1. Проверить использование `SuccessResult`, `ErrorResult`, `CommandResult`
2. Убедиться, что API не изменился
3. Обновить использование, если изменились параметры конструкторов

#### 3.3. Проверка импортов конфигурации

**Действия:**
1. Проверить использование `config`, `Config` из `mcp_proxy_adapter.config`
2. Убедиться, что структура `Config` не изменилась
3. Обновить использование, если изменились методы

#### 3.4. Проверка импортов приложения

**Действия:**
1. Проверить использование `create_app` из `mcp_proxy_adapter.api.app`
2. Убедиться, что сигнатура не изменилась
3. Обновить вызовы, если изменились параметры

### Этап 4: Тестирование (1-2 дня)

#### 4.1. Проверка импортов

**Действия:**
1. Запустить скрипт проверки импортов:
   ```python
   # test_imports.py
   try:
       from mcp_proxy_adapter.integrations.queuemgr_integration import get_global_queue_manager
       print("✅ Queue integration OK")
   except ImportError as e:
       print(f"❌ Queue integration ERROR: {e}")
   
   try:
       from mcp_security_framework import SecurityAdapter, OperationType
       print("✅ Security framework OK")
   except ImportError as e:
       print(f"❌ Security framework ERROR: {e}")
   ```

#### 4.2. Проверка основных команд

**Действия:**
1. Протестировать команды с очередью:
   - `vast_create`
   - `vast_destroy`
   - `ssh_exec`
   - `ftp_upload`
   - `docker_pull`

2. Протестировать команды статуса очереди:
   - `queue_get_job_status`
   - `queue_cancel_task`
   - `queue_remove_task`

3. Протестировать SSL команды:
   - `ssl_cert_generate`
   - `ssl_cert_verify`
   - `ssl_crl`

#### 4.3. Запуск тестов

**Действия:**
```bash
# Запустить все тесты
pytest tests/ -v

# Запустить тесты конкретных модулей
pytest tests/test_commands/ -v
pytest tests/test_queue/ -v
pytest tests/test_security/ -v
```

### Этап 5: Очистка (1 день)

#### 5.1. Удаление старого кода

**Действия:**
1. Удалить или закомментировать собственный менеджер очереди:
   - `ai_admin/task_queue/queue_manager.py` (если больше не используется)
   - `ai_admin/task_queue/task_queue.py` (если больше не используется)

2. Удалить неиспользуемые импорты из команд

3. Обновить документацию

#### 5.2. Обновление документации

**Действия:**
1. Обновить README с новыми зависимостями
2. Обновить документацию по использованию очереди
3. Обновить документацию по безопасности

## ✅ ЧЕКЛИСТ ВЫПОЛНЕНИЯ

### Подготовка
- [ ] Обновлен `requirements.txt`
- [ ] Установлены обновленные пакеты
- [ ] Проверена установка пакетов
- [ ] Добавлена секция `queue_manager` в `config.json`

### Миграция очереди
- [ ] Обновлены импорты в 10 командах (vast_create, vast_destroy, ssh_exec, ftp_upload, ftp_mkdir, ftp_rename, ftp_info, docker_pull, queue_remove_task, queue_cancel_task)
- [ ] Обновлен API очереди в командах
- [ ] Мигрированы 3 команды с собственным менеджером (ftp_download, ftp_list, ftp_delete)
- [ ] Обновлены команды статуса очереди
- [ ] Удалена регистрация очереди из `dependency_injection.py`

### Миграция безопасности (опционально)
- [ ] Созданы адаптеры на основе `SecurityAdapter`
- [ ] Зарегистрированы адаптеры в `SecurityManager`
- [ ] Использован `SecurityAdapterWrapper` для legacy-адаптеров (если нужно)

### Обновление других компонентов
- [ ] Проверены импорты ошибок
- [ ] Проверены импорты результатов команд
- [ ] Проверены импорты конфигурации
- [ ] Проверены импорты приложения

### Тестирование
- [ ] Проверены импорты
- [ ] Протестированы команды с очередью
- [ ] Протестированы команды статуса очереди
- [ ] Протестированы SSL команды
- [ ] Запущены все тесты

### Очистка
- [ ] Удален старый код очереди (если не используется)
- [ ] Удалены неиспользуемые импорты
- [ ] Обновлена документация

## 📝 ПРИМЕЧАНИЯ

1. **Приоритет:** Сначала выполнить Этап 0 и Этап 1 (миграция очереди) - это критично для работы проекта
2. **Безопасность:** Этап 2 (миграция безопасности) можно выполнить позже, так как существующая система безопасности работает
3. **Тестирование:** После каждого этапа запускать тесты для проверки работоспособности
4. **Откат:** Сохранить бэкап кода перед началом миграции для возможности отката

### Проверка 1: Использование очереди адаптера

**Что проверить:**

1. **Проверить, какие команды используют очередь:**
   - Найти все команды с импортами `from mcp_proxy_adapter.queue`
   - Найти все команды с импортами `from ai_admin.task_queue` (не должно быть)
   - Убедиться, что все команды используют только `mcp_proxy_adapter.queue`

2. **Проверить совместимость API `mcp_proxy_adapter.queue` в версии 6.9.102:**
   - Метод `queue_manager.add_task()` - изменилась ли сигнатура?
   - Метод `queue_manager.get_task()` - изменился ли формат возврата?
   - Метод `queue_manager.cancel_task()` - изменилась ли сигнатура?
   - Метод `queue_manager.remove_task()` - изменилась ли сигнатура?
   - Метод `queue_manager.get_tasks_by_status()` - изменилась ли сигнатура?
   - Типы `Task`, `TaskType`, `TaskStatus` - изменилась ли структура?

3. **Проверить использование собственного менеджера:**
   - Найти все места, где используется `ai_admin.task_queue.queue_manager`
   - Убедиться, что собственный менеджер НЕ используется в командах

### Проверка 1.1: Использование безопасности через mcp_security_framework

**Что проверить:**

1. **Проверить использование `mcp_security_framework`:**
   - Найти все импорты из `mcp_security_framework`
   - Убедиться, что используется только `mcp_security_framework` из установленного пакета
   - Проверить, что нет собственных реализаций безопасности

2. **Проверить API `mcp_security_framework` в версии 1.5.1:**
   - `CertificateManager` - изменился ли API?
   - `CertificateConfig` - изменилась ли структура?
   - Другие классы и функции безопасности

3. **Проверить, что адаптер управляет соединениями:**
   - Убедиться, что адаптер сам создает и защищает соединения
   - Проверить, что нет собственной реализации защиты соединений
   - Проверить, что SSL/mTLS настраивается через адаптер

4. **Проверить использование собственных адаптеров безопасности:**
   - Найти все использования `ai_admin.security.*` адаптеров
   - Убедиться, что они не используются или заменены на `mcp_security_framework`

**Скрипт для проверки:**
```bash
# Найти все использования mcp_security_framework
grep -r "from mcp_security_framework\|import.*mcp_security_framework" .

# Найти все использования собственных адаптеров безопасности (не должно быть)
grep -r "from ai_admin.security\|import.*ai_admin.security" commands/
```

**Файлы для проверки:**
- `commands/ssl_*.py` - SSL команды должны использовать `mcp_security_framework`
- Все команды с использованием безопасности

**Файлы для проверки:**
- `commands/vast_create_command.py`
- `commands/vast_destroy_command.py`
- `commands/ssh_exec_command.py`
- `commands/ftp_upload_command.py`
- `commands/ftp_mkdir_command.py`
- `commands/docker_pull_command.py`
- `commands/queue_remove_task_command.py`
- `commands/queue_cancel_task_command.py`
- Все остальные команды с использованием очереди

**Скрипт для проверки:**
```bash
# Найти все использования mcp_proxy_adapter.queue
grep -r "from mcp_proxy_adapter.queue\|import.*mcp_proxy_adapter.queue" commands/

# Найти все использования собственного менеджера (не должно быть)
grep -r "from ai_admin.task_queue\|import.*ai_admin.task_queue" commands/
```

**Скрипт для проверки безопасности:**
```bash
# Найти все использования mcp_security_framework
grep -r "from mcp_security_framework\|import.*mcp_security_framework" .

# Найти все использования собственных адаптеров безопасности (проверить, нужно ли заменить)
grep -r "from ai_admin.security\|import.*ai_admin.security" commands/
```

### Проверка 1.2: Поддержка FTP операций в mcp_security_framework

**Что проверить:**

1. **Проверить текущее использование FTP безопасности:**
   - Найти все использования `FtpSecurityAdapter` из `ai_admin.security`
   - Определить, какие методы используются для FTP операций
   - Проверить типы FTP операций: UPLOAD, DOWNLOAD, LIST, DELETE, MKDIR, RMDIR, RENAME, CHMOD

2. **Проверить поддержку FTP в mcp_security_framework:**
   - Есть ли в `PermissionManager` поддержка FTP операций?
   - Есть ли в `SecurityManager` методы для валидации FTP операций?
   - Есть ли поддержка FTPS (FTP over SSL/TLS)?
   - Есть ли методы для аудита FTP операций?

3. **Определить необходимые методы для добавления:**
   - `validate_ftp_operation()` - валидация FTP операций
   - `check_ftp_permissions()` - проверка разрешений для FTP
   - `audit_ftp_operation()` - аудит FTP операций
   - Поддержка типов FTP операций
   - Поддержка FTPS конфигурации

**Файлы для проверки:**
- `ai_admin/security/ftp_security_adapter.py` - текущая реализация
- `commands/ftp_*.py` - все FTP команды
- `mcp_security_framework/core/permission_manager.py` - проверить поддержку FTP
- `mcp_security_framework/core/security_manager.py` - проверить поддержку FTP

**Скрипт для проверки:**
```python
# test_ftp_security.py
from mcp_security_framework import SecurityManager, PermissionManager
from mcp_security_framework.schemas.config import SecurityConfig

# Проверить поддержку FTP операций
security_config = SecurityConfig()
security_manager = SecurityManager(security_config)

# Проверить, есть ли методы для FTP
ftp_methods = [
    'validate_ftp_operation',
    'check_ftp_permissions',
    'audit_ftp_operation'
]

for method in ftp_methods:
    if hasattr(security_manager, method):
        print(f"✅ {method} существует")
    else:
        print(f"❌ {method} не найден - нужно добавить")
```

**Текущие FTP операции в проекте:**
- `FtpOperation.UPLOAD` - загрузка файлов
- `FtpOperation.DOWNLOAD` - скачивание файлов
- `FtpOperation.LIST` - список файлов
- `FtpOperation.DELETE` - удаление файлов
- `FtpOperation.MKDIR` - создание директорий
- `FtpOperation.RMDIR` - удаление директорий
- `FtpOperation.RENAME` - переименование файлов
- `FtpOperation.CHMOD` - изменение прав доступа

### Проверка 2: Динамически загружаемые команды

**Что проверить:**

1. **Проверить API `registry.reload_system()` в версии 6.9.102:**
   - Существует ли метод `registry.reload_system()`?
   - Какой формат возвращаемого значения?
   - Изменилась ли сигнатура метода?

2. **Проверить автоматическое обнаружение команд:**
   - Работает ли автоматическое обнаружение команд из директории `commands/`?
   - Какие настройки нужны в конфигурации?
   - Работает ли `discovery_path`?
   - Работает ли `auto_discover`?

3. **Проверить API регистрации команд:**
   - Работает ли `registry.register_custom()`?
   - Работает ли `registry.command_exists()`?
   - Изменился ли механизм регистрации?

4. **Проверить хуки:**
   - Работает ли `register_custom_commands_hook()`?
   - Изменился ли API хуков?

**Файлы для проверки:**
- `ai_admin/core/command_registry.py` - использует `registry.reload_system()`
- `ai_admin/core/server_setup.py` - настройка хуков
- `config.json` - настройки обнаружения команд

**Скрипт для проверки:**
```python
# test_command_registry.py
from mcp_proxy_adapter.commands.command_registry import registry

# Проверить API
print("Проверка registry.reload_system()...")
try:
    result = await registry.reload_system()
    print(f"✅ reload_system() работает. Результат: {result}")
except Exception as e:
    print(f"❌ reload_system() не работает: {e}")

print("Проверка registry.register_custom()...")
# Проверить регистрацию команды
```

**Скрипт для проверки безопасности:**
```python
# test_security_framework.py
from mcp_security_framework import (
    SecurityManager, 
    CertificateManager, 
    AuthManager,
    SecurityConfig,
    SSLConfig
)

# Проверить импорты
print("✅ Все компоненты безопасности доступны")

# Проверить API CertificateManager
cert_manager = CertificateManager()
print("✅ CertificateManager создан")

# Проверить API SecurityManager
security_config = SecurityConfig()
security_manager = SecurityManager(security_config)
print("✅ SecurityManager создан")
```

### Проверка 3: Remote плагины или их аналоги

**Что проверить:**

1. **Проверить поддержку remote плагинов:**
   - Существует ли поддержка remote плагинов в версии 6.9.102?
   - Какой API для загрузки плагинов из URL?
   - Работает ли механизм кеширования плагинов?

2. **Проверить `CatalogManager`:**
   - Существует ли `CatalogManager` в версии 6.9.102?
   - Какой API для управления плагинами?
   - Как работает каталог плагинов?

3. **Проверить настройки плагинов:**
   - Какие настройки нужны в конфигурации для плагинов?
   - Работает ли `plugin_servers`?
   - Как настроить автообнаружение плагинов?

**Скрипт для проверки:**
```python
# test_plugins.py
# Проверить импорты плагинов
try:
    from mcp_proxy_adapter.plugins import CatalogManager
    print("✅ CatalogManager существует")
except ImportError as e:
    print(f"❌ CatalogManager не найден: {e}")

# Проверить API загрузки плагинов
```

### Проверка 4: Инициализация и регистрация команд

**Что проверить:**

1. **Проверить изменения в API регистрации:**
   - Изменился ли `registry.reload_system()`?
   - Изменился ли `registry.register_custom()`?
   - Изменился ли `registry.command_exists()`?

2. **Проверить изменения в хуках:**
   - Изменился ли API `register_custom_commands_hook()`?
   - Работают ли хуки как раньше?

3. **Проверить конфигурацию:**
   - Какие настройки нужны для автообнаружения команд?
   - Нужно ли обновить `config.json`?

**Файлы для проверки:**
- `ai_admin/core/command_registry.py`
- `ai_admin/core/server_setup.py`
- `config.json`

### Проверка 5: Генератор и валидатор конфигов в адаптере

**Что проверить:**

1. **Проверить генератор конфигов в адаптере:**
   - Какой API у генератора конфигов?
   - Какие параметры можно генерировать?
   - Как использовать генератор для создания конфигурации проекта?

2. **Проверить валидатор конфигов в адаптере:**
   - Какой API у валидатора конфигов?
   - Какие схемы валидации используются?
   - Как валидировать конфигурацию проекта?

3. **Проверить структуру конфигурации:**
   - Какая структура конфигурации используется в адаптере?
   - Какие обязательные поля?
   - Какие опциональные поля?

**Скрипт для проверки:**
```python
# test_config_tools.py
# Проверить генератор конфигов
try:
    from mcp_proxy_adapter.config import ConfigGenerator
    print("✅ ConfigGenerator существует")
    # Проверить API
except ImportError as e:
    print(f"❌ ConfigGenerator не найден: {e}")

# Проверить валидатор конфигов
try:
    from mcp_proxy_adapter.config import ConfigValidator
    print("✅ ConfigValidator существует")
    # Проверить API
except ImportError as e:
    print(f"❌ ConfigValidator не найден: {e}")
```

### Проверка 6: Конфигурация для локальной разработки

**Что проверить:**

1. **Проверить пути:**
   - Все ли пути относительные?
   - Нет ли контейнерных путей (`/app/`, `/var/`)?

2. **Проверить настройки очереди:**
   - Работает ли очередь без Docker контейнера?
   - Где создаются логи и хранилище очереди?

3. **Проверить зависимости:**
   - Все ли зависимости установлены локально?
   - Нет ли зависимостей от Docker?

## 📋 ПЛАН ДЕЙСТВИЙ (будет скорректирован по результатам проверок)

### 1. Использовать только очередь адаптера
**Задача:** Убедиться, что все команды используют только `mcp_proxy_adapter.queue`, а не собственный менеджер.

**Текущее состояние:**
- Некоторые команды используют `mcp_proxy_adapter.queue.queue_manager` ✅
- Есть собственный менеджер `ai_admin.task_queue.queue_manager` - НЕ использовать
- Необходимо проверить совместимость API с версией 6.9.102

**Действие:** 
- ✅ Проверить, что все команды используют `mcp_proxy_adapter.queue`
- ❌ Убрать использование собственного `ai_admin.task_queue.queue_manager`
- Проверить совместимость API `mcp_proxy_adapter.queue` с версией 6.9.102
- Убедиться, что все методы очереди работают корректно

**Команды, использующие очередь (проверить, что используют адаптер):**
- `commands/vast_create_command.py`
- `commands/vast_destroy_command.py`
- `commands/ssh_exec_command.py`
- `commands/ftp_upload_command.py`
- `commands/ftp_mkdir_command.py`
- `commands/docker_pull_command.py`
- `commands/queue_remove_task_command.py`
- `commands/queue_cancel_task_command.py`


## 1. mcp-proxy-adapter-6.9.102

### Текущее использование в проекте

Проект использует следующие модули из `mcp-proxy-adapter`:

#### 1.1. Импорты ошибок
```python
from mcp_proxy_adapter.core.errors import CommandError as CustomError
from mcp_proxy_adapter.core.errors import InternalError, AuthorizationError
```

**Проверка:** Убедиться, что в версии 6.9.102 эти классы ошибок существуют и имеют те же сигнатуры.

**Необходимые изменения:**
- Проверить наличие `CommandError`, `InternalError`, `AuthorizationError` в `mcp_proxy_adapter.core.errors`
- Если изменились названия или структура, обновить импорты во всех файлах:
  - `commands/vast_search_command.py`
  - `commands/vast_instances_command.py`
  - `commands/vast_create_command.py`
  - `commands/vast_destroy_command.py`
  - `commands/system_monitor_command.py`
  - И другие файлы с импортами ошибок

#### 1.2. Импорты результатов команд
```python
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult, CommandResult
```

**Проверка:** Убедиться, что классы результатов существуют и совместимы.

**Необходимые изменения:**
- Проверить API классов `SuccessResult`, `ErrorResult`, `CommandResult`
- Если изменились параметры конструкторов или методы, обновить использование в:
  - `commands/vector_store_deploy_command.py`
  - `commands/vast_search_command.py`
  - `commands/vast_instances_command.py`
  - `commands/ssl_cert_view_command.py`
  - `commands/ssl_crl_command.py`
  - И других файлах

#### 1.3. Импорты очереди - ИСПОЛЬЗОВАТЬ ТОЛЬКО АДАПТЕР

**ЗАДАЧА:** Убедиться, что все команды используют только `mcp_proxy_adapter.queue`.

**Текущее использование в командах (ПРАВИЛЬНО):**
```python
from mcp_proxy_adapter.queue import Task, TaskType, TaskStatus
from mcp_proxy_adapter.queue import queue_manager
```

**Команды, использующие `mcp_proxy_adapter.queue` (проверить):**
- `commands/vast_create_command.py` (строки 20-21) ✅
- `commands/vast_destroy_command.py` (строки 20-21) ✅
- `commands/ssh_exec_command.py` (строки 59-60) ✅
- `commands/ftp_upload_command.py` (строки 118-119) ✅
- `commands/ftp_mkdir_command.py` (строка 96) ✅
- `commands/docker_pull_command.py` (строка 96) ✅
- `commands/queue_remove_task_command.py` (строка 16) ✅
- `commands/queue_cancel_task_command.py` (строка 16) ✅

**Собственный менеджер очереди - НЕ ИСПОЛЬЗОВАТЬ:**
- `ai_admin/task_queue/queue_manager.py` - НЕ использовать
- `ai_admin/task_queue/task_queue.py` - НЕ использовать

**Необходимые проверки:**

1. **Проверить совместимость API `mcp_proxy_adapter.queue` в версии 6.9.102:**
   - Метод `queue_manager.add_task()` - изменилась ли сигнатура?
   - Метод `queue_manager.get_task()` - изменился ли формат возврата?
   - Метод `queue_manager.cancel_task()` - изменилась ли сигнатура?
   - Метод `queue_manager.remove_task()` - изменилась ли сигнатура?
   - Метод `queue_manager.get_tasks_by_status()` - изменилась ли сигнатура?

2. **Проверить совместимость типов:**
   - `Task`, `TaskType`, `TaskStatus` из `mcp_proxy_adapter.queue` - изменилась ли структура?
   - Убедиться, что все типы задач (SSH_EXEC, FTP_UPLOAD, DOCKER_PUSH и т.д.) поддерживаются

3. **Убедиться, что собственный менеджер НЕ используется:**
   - Проверить, нет ли импортов `ai_admin.task_queue.queue_manager` в командах
   - Проверить, не используется ли собственный менеджер в других местах

#### 1.4. Импорты конфигурации
```python
from mcp_proxy_adapter.config import config, Config
```

**Проверка:** Убедиться, что объект `config` и класс `Config` совместимы.

**Необходимые изменения:**
- Проверить структуру `Config` и его методы
- Обновить использование в:
  - `ai_admin/working_server.py`
  - `ai_admin/core/server_manager.py`
  - `ai_admin/dependency_injection.py`
  - `commands/vast_search_command.py`
  - `commands/vast_instances_command.py`

#### 1.5. Импорты приложения
```python
from mcp_proxy_adapter.api.app import create_app
```

**Проверка:** Убедиться, что функция `create_app` имеет совместимую сигнатуру.

**Необходимые изменения:**
- Проверить параметры `create_app(app_config=...)`
- Обновить вызовы в:
  - `ai_admin/working_server.py`

#### 1.6. Импорты логирования
```python
from mcp_proxy_adapter.core.logging import get_logger, setup_logging
```

**Проверка:** Убедиться совместимость API логирования.

**Необходимые изменения:**
- Проверить сигнатуры функций
- Обновить использование в:
  - `ai_admin/core/server.py`
  - `ai_admin/core/server_manager.py`

### Файлы для проверки и обновления

1. **Команды:**
   - `commands/vast_*.py` (все файлы vast)
   - `commands/queue_*.py` (все файлы очереди)
   - `commands/ssl_*.py` (SSL команды)
   - `commands/system_monitor_command.py`
   - `commands/vector_store_deploy_command.py`

2. **Основные модули:**
   - `ai_admin/working_server.py`
   - `ai_admin/core/server.py`
   - `ai_admin/core/server_manager.py`
   - `ai_admin/dependency_injection.py`

#### 1.7. Динамически загружаемые команды - ПРОВЕРКА

**ЗАДАЧА:** Проверить, остались ли в адаптере механизмы динамической загрузки команд.

**Текущая реализация:**
- `ai_admin/core/command_registry.py` использует `registry.reload_system()`
- `custom_commands_hook()` регистрирует команды через `registry.register_custom()`
- Команды регистрируются вручную в списке `commands_to_register`
- Директория `commands/` - команды в файловой системе

**Необходимые проверки:**

1. **Проверить API динамической загрузки в версии 6.9.102:**
   - Проверить, существует ли `registry.reload_system()` в версии 6.9.102
   - Проверить, изменился ли формат возвращаемого значения
   - Проверить, работает ли автоматическое обнаружение команд из директории
   - Проверить, работает ли `registry.register_custom()`
   - Проверить, работает ли `registry.command_exists()`

2. **Проверить автоматическое обнаружение команд:**
   - Проверить настройки `discovery_path` в конфигурации
   - Проверить настройки `auto_discover` в конфигурации
   - Убедиться, что команды из `commands/` загружаются автоматически
   - Проверить, изменился ли механизм обнаружения

3. **Проверить `ai_admin/core/command_registry.py`:**
   - Проверить совместимость `initialize_commands()` с новой версией
   - Проверить совместимость `custom_commands_hook()` с новой версией
   - Если API изменился, обновить код

4. **Проверить `ai_admin/core/server_setup.py`:**
   - Проверить `setup_hooks()` - регистрация хуков
   - Проверить `register_custom_commands_hook()` - может измениться API

5. **Проверить `config.json`:**
   - Добавить настройки обнаружения команд, если их нет:
   ```json
   {
     "commands": {
       "discovery_path": "./commands",
       "auto_discover": true
     }
   }
   ```

**Файлы для проверки:**
- `ai_admin/core/command_registry.py` - основная логика регистрации
- `ai_admin/core/server_setup.py` - настройка хуков
- `ai_admin/working_server.py` - инициализация сервера
- `config.json` - конфигурация путей обнаружения команд

#### 1.8. Remote плагины или их аналоги - ПРОВЕРКА

**ЗАДАЧА:** Проверить, что с remote плагинами или их аналогами в версии 6.9.102.

**Текущее состояние:**
- В документации упоминается система плагинов с каталогом
- Поддержка загрузки плагинов из URL/plugin серверов
- Кеширование удаленных плагинов
- `CatalogManager` для управления плагинами

**Необходимые проверки:**

1. **Проверить поддержку remote плагинов:**
   - Проверить, осталась ли поддержка remote плагинов в версии 6.9.102
   - Проверить API загрузки плагинов из URL
   - Проверить настройки `plugin_servers` в конфигурации
   - Проверить, работает ли механизм кеширования плагинов

2. **Проверить `CatalogManager`:**
   - Проверить, существует ли `CatalogManager` в версии 6.9.102
   - Проверить API управления плагинами
   - Проверить, изменился ли механизм работы с каталогом плагинов

3. **Проверить конфигурацию плагинов:**
   - Проверить, нужно ли настраивать `plugin_servers` в `config.json`
   - Проверить настройки автообнаружения плагинов
   - Проверить настройки кеширования плагинов

4. **Проверить интеграцию:**
   - Проверить, как плагины интегрируются с системой команд
   - Проверить, работает ли приоритизация плагинов (custom > built-in > loaded)
   - Проверить, можно ли загружать плагины динамически

**Файлы для проверки:**
- `config.json` - настройки плагинов
- Документация адаптера - API плагинов
- Код адаптера - реализация плагинов

## 2. mcp_security_framework-1.5.1

**ВАЖНО:** Безопасность ТОЛЬКО через `mcp_security_framework` из установленного пакета. Адаптер берет на себя соединения и их защиту.

### Текущее использование в проекте

```python
from mcp_security_framework import CertificateManager, SecurityManager, AuthManager
from mcp_security_framework.schemas.config import CertificateConfig, SecurityConfig, SSLConfig
```

### Доступные компоненты в mcp_security_framework-1.5.1

- `SecurityManager` - основной менеджер безопасности
- `AuthManager` - управление аутентификацией
- `CertificateManager` - управление сертификатами
- `PermissionManager` - управление разрешениями
- `RateLimiter` - ограничение скорости запросов
- `SSLConfig`, `AuthConfig`, `PermissionConfig` - схемы конфигурации

### Файлы, использующие mcp_security_framework

- `commands/ssl_cert_generate_command.py`
- `commands/ssl_cert_verify_command.py`
- `commands/ssl_crl_command.py`
- `ai_admin/commands/ssl_cert_generate_command.py`
- `ai_admin/commands/ssl_cert_verify_command.py`
- `ai_admin/commands/ssl_crl_command.py`
- `ai_admin/security_integration.py`

### Необходимые изменения

1. **Проверить API компонентов безопасности:**
   - `SecurityManager` - изменился ли API?
   - `CertificateManager` - изменились ли методы?
   - `AuthManager` - изменился ли API?
   - `PermissionManager` - изменился ли API?

2. **Проверить схемы конфигурации:**
   - `CertificateConfig` - изменилась ли структура?
   - `SecurityConfig` - изменилась ли структура?
   - `SSLConfig` - изменилась ли структура?
   - Обязательные/опциональные параметры

3. **Убрать собственные реализации безопасности:**
   - Проверить, нет ли собственных адаптеров безопасности
   - Заменить на использование `mcp_security_framework`
   - Убедиться, что адаптер управляет соединениями и их защитой

4. **Проверить интеграцию с адаптером:**
   - Убедиться, что адаптер использует `mcp_security_framework` для защиты соединений
   - Проверить, что SSL/mTLS настраивается через адаптер
   - Проверить, что аутентификация настраивается через адаптер

## 3. queuemgr-1.0.13

### Анализ использования

Проект использует собственную реализацию очереди в `ai_admin/task_queue/`, но также может использовать `queuemgr` через `mcp_proxy_adapter.queue`.

### Необходимые изменения

1. **Проверить интеграцию:**
   - Если `mcp_proxy_adapter.queue` теперь использует `queuemgr-1.0.13`, проверить совместимость
   - Убедиться, что `queue_manager` из `mcp_proxy_adapter.queue` работает корректно

2. **Проверить собственную реализацию:**
   - `ai_admin/task_queue/task_queue.py` - может потребоваться миграция на `queuemgr`
   - `ai_admin/task_queue/queue_manager.py` - проверить совместимость

3. **Обновить зависимости:**
   - Если проект напрямую использует `queuemgr`, добавить в `requirements.txt`
   - Если используется только через `mcp-proxy-adapter`, проверить версию в зависимостях

## 4. Конфигурация для разработки без контейнера

**Важно:** Сервер используется на компьютере разработчика **БЕЗ контейнера**.

**Текущая конфигурация (`config.json`):**
```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 20000
  },
  "ssl": {
    "enabled": false
  },
  "security": {
    "enabled": false
  }
}
```

**Необходимые изменения:**

1. **Проверить пути к файлам:**
   - Все пути должны быть относительными к рабочей директории проекта
   - Не использовать пути типа `/app/` или `/var/` (контейнерные пути)
   - Использовать `Path(__file__).parent` для относительных путей

2. **Проверить настройки очереди:**
   - Убедиться, что очередь работает без Docker контейнера
   - Проверить, что задачи выполняются локально
   - Проверить, что логи пишутся в локальную директорию

3. **Проверить настройки безопасности:**
   - Для разработки SSL может быть отключен
   - mTLS может быть необязательным
   - Проверить, что сервер запускается без сертификатов

4. **Проверить зависимости:**
   - Убедиться, что все зависимости установлены локально
   - Проверить, что нет зависимостей от Docker или контейнеров
   - Убедиться, что `hypercorn` работает локально

5. **Обновить `ai_admin/working_server.py`:**
   - Проверить, что сервер запускается локально
   - Убедиться, что конфигурация читается из локального файла
   - Проверить, что логи пишутся локально

## 5. werkzeug-3.1.4

### Анализ использования

Werkzeug может использоваться:
- Косвенно через FastAPI/Starlette
- Через другие зависимости
- Напрямую в проекте (если есть)

### Необходимые изменения

1. **Проверить прямое использование:**
   ```bash
   grep -r "from werkzeug\|import werkzeug" .
   ```

2. **Основные breaking changes в Werkzeug 3.x:**
   - Удалены устаревшие функции и классы
   - Изменения в `werkzeug.security`
   - Изменения в `werkzeug.utils`
   - Изменения в `werkzeug.wrappers`

3. **Если используется напрямую:**
   - Обновить импорты устаревших функций
   - Обновить использование API, если изменилось
   - Проверить совместимость с FastAPI/Starlette

### Шаг 1: Обновление зависимостей

**После проверок:**
1. Обновить версии в `requirements.txt`:
   ```txt
   mcp-proxy-adapter>=6.9.102
   mcp_security_framework>=1.5.1
   queuemgr>=1.0.13
   werkzeug>=3.1.4
   ```

2. Обновить минимальные версии в:
   - `setup.py`: `mcp-proxy-adapter>=6.9.102`
   - `pyproject.toml`: `mcp-proxy-adapter>=6.9.102`

### Шаг 2: Создание генератора и валидатора конфигов для проекта

**Задача:** На основе генератора и валидатора конфигов из `mcp-proxy-adapter-6.9.102` создать генератор и валидатор для этого проекта.

**Действия:**

1. **Изучить генератор и валидатор в адаптере:**
   - Изучить API `ConfigGenerator` из `mcp_proxy_adapter.config`
   - Изучить API `ConfigValidator` из `mcp_proxy_adapter.config`
   - Понять структуру и принципы работы

2. **Создать генератор конфигов для проекта:**
   - Создать модуль `ai_admin/config/config_generator.py`
   - Реализовать генерацию конфигурации для локальной разработки
   - Поддержать генерацию с параметрами по умолчанию
   - Поддержать интерактивную генерацию

3. **Создать валидатор конфигов для проекта:**
   - Создать модуль `ai_admin/config/config_validator.py`
   - Реализовать валидацию структуры конфигурации
   - Валидировать обязательные поля
   - Валидировать типы данных
   - Валидировать значения (диапазоны, форматы и т.д.)

4. **Определить схему конфигурации:**
   - Определить обязательные поля для проекта
   - Определить опциональные поля
   - Определить значения по умолчанию
   - Определить правила валидации

5. **Интегрировать с проектом:**
   - Использовать генератор при первом запуске
   - Использовать валидатор при загрузке конфигурации
   - Добавить команду для генерации конфигурации
   - Добавить команду для валидации конфигурации

**Файлы для создания:**
- `ai_admin/config/config_generator.py` - генератор конфигов
- `ai_admin/config/config_validator.py` - валидатор конфигов
- `ai_admin/config/schema.py` - схема конфигурации (опционально)

**Пример использования:**
```python
# Генерация конфигурации
from ai_admin.config.config_generator import ConfigGenerator

generator = ConfigGenerator()
config = generator.generate(
    host="127.0.0.1",
    port=20000,
    ssl_enabled=False,
    discovery_path="./commands"
)
generator.save(config, "config.json")

# Валидация конфигурации
from ai_admin.config.config_validator import ConfigValidator

validator = ConfigValidator()
is_valid, errors = validator.validate("config.json")
if not is_valid:
    print(f"Ошибки валидации: {errors}")
```

### Шаг 3: Добавление поддержки FTP в mcp_security_framework

**Задача:** Добавить поддержку FTP операций в `mcp_security_framework`, если её нет.

**Действия:**

1. **Определить необходимые методы:**
   - `validate_ftp_operation(operation: FtpOperation, user_roles: List[str], params: Dict) -> ValidationResult`
   - `check_ftp_permissions(user_roles: List[str], required_permissions: List[str]) -> Tuple[bool, List[str]]`
   - `audit_ftp_operation(operation: FtpOperation, user_roles: List[str], params: Dict, status: str) -> None`
   - Поддержка типов FTP операций (UPLOAD, DOWNLOAD, LIST, DELETE, MKDIR, RMDIR, RENAME, CHMOD)

2. **Добавить в PermissionManager:**
   - Методы для проверки FTP разрешений
   - Маппинг FTP операций на разрешения
   - Поддержка FTP-специфичных разрешений (ftp:upload, ftp:download, ftp:admin и т.д.)

3. **Добавить в SecurityManager:**
   - Методы для валидации FTP операций
   - Интеграция с PermissionManager для FTP
   - Поддержка аудита FTP операций

4. **Добавить поддержку FTPS:**
   - Конфигурация FTPS в `SSLConfig`
   - Валидация FTPS соединений
   - Управление сертификатами для FTPS

5. **Создать схему конфигурации для FTP:**
   - `FTPConfig` в `mcp_security_framework.schemas.config`
   - Настройки разрешений для FTP операций
   - Настройки FTPS

**Файлы для изменения в mcp_security_framework:**
- `mcp_security_framework/core/permission_manager.py` - добавить FTP методы
- `mcp_security_framework/core/security_manager.py` - добавить FTP валидацию
- `mcp_security_framework/schemas/config.py` - добавить FTPConfig
- `mcp_security_framework/schemas/models.py` - добавить FtpOperation enum

**Пример API для добавления:**
```python
# В PermissionManager
def check_ftp_permissions(
    self, 
    user_roles: List[str], 
    operation: str,
    required_permissions: List[str]
) -> Tuple[bool, List[str]]:
    """Check FTP operation permissions."""
    # Реализация проверки разрешений для FTP операций
    pass

# В SecurityManager
def validate_ftp_operation(
    self,
    operation: str,
    user_roles: List[str],
    operation_params: Dict[str, Any]
) -> ValidationResult:
    """Validate FTP operation with security checks."""
    # Реализация валидации FTP операций
    pass
```

### Шаг 4: Исправления на основе результатов проверок

**Будет определено после проверок:**
- Если API очереди изменился - обновить использование в командах
- Если изменилась регистрация команд - обновить код регистрации
- Если изменились плагины - обновить интеграцию плагинов
- Если изменилась конфигурация - обновить `config.json`
- **Если есть собственные реализации безопасности - заменить на `mcp_security_framework`**
- **Если добавлена поддержка FTP в mcp_security_framework - заменить `FtpSecurityAdapter` на использование фреймворка**
- **Убедиться, что адаптер управляет соединениями и их защитой**

### Шаг 5: Тестирование

1. Запустить тесты:
   ```bash
   pytest tests/ -v
   ```

2. Проверить основные команды:
   - SSL команды
   - Queue команды
   - Vast команды
   - System команды

### Шаг 6: Проверка совместимости API (детальная)

1. Создать тестовый скрипт для проверки импортов:
```python
# test_imports.py
try:
    from mcp_proxy_adapter.core.errors import CommandError, InternalError, AuthorizationError
    print("✅ mcp_proxy_adapter.core.errors - OK")
except ImportError as e:
    print(f"❌ mcp_proxy_adapter.core.errors - ERROR: {e}")

try:
    from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult, CommandResult
    print("✅ mcp_proxy_adapter.commands.result - OK")
except ImportError as e:
    print(f"❌ mcp_proxy_adapter.commands.result - ERROR: {e}")

try:
    from mcp_proxy_adapter.queue import Task, TaskType, TaskStatus, queue_manager
    print("✅ mcp_proxy_adapter.queue - OK")
except ImportError as e:
    print(f"❌ mcp_proxy_adapter.queue - ERROR: {e}")

try:
    from mcp_security_framework import CertificateManager
    from mcp_security_framework.schemas import CertificateConfig
    print("✅ mcp_security_framework - OK")
except ImportError as e:
    print(f"❌ mcp_security_framework - ERROR: {e}")
```

### Шаг 7: Поиск и замена устаревших API

1. **Ошибки:**
   - Проверить все использования `CustomError` (должен быть `CommandError`)
   - Проверить `NetworkError` → `InternalError`
   - Проверить `PermissionError` → `AuthorizationError`

2. **Очередь:**
   - Проверить использование `Task`, `TaskType`, `TaskStatus`
   - Проверить методы `queue_manager`

3. **Безопасность:**
   - Проверить методы `CertificateManager`
   - Проверить структуру `CertificateConfig`


## Критические точки внимания

1. **API очереди** - наиболее вероятная область изменений
2. **API ошибок** - может измениться структура исключений
3. **API безопасности** - могут измениться методы CertificateManager
4. **Конфигурация** - может измениться структура Config

## Конкретные изменения в коде

### Изменение 1: Обновление requirements.txt

**Файл:** `requirements.txt`

**Было:**
```txt
mcp-proxy-adapter>=5.0.0
```

**Должно быть:**
```txt
mcp-proxy-adapter>=6.9.102
mcp_security_framework>=1.5.1
queuemgr>=1.0.13
werkzeug>=3.1.4
```

### Изменение 2: Обновление setup.py

**Файл:** `setup.py`

**Было:**
```python
install_requires=[
    "mcp-proxy-adapter>=1.0.0",
    ...
]
```

**Должно быть:**
```python
install_requires=[
    "mcp-proxy-adapter>=6.9.102",
    ...
]
```

### Изменение 3: Обновление pyproject.toml

**Файл:** `pyproject.toml`

**Было:**
```toml
dependencies = [
    "mcp-proxy-adapter>=1.0.0",
    ...
]
```

**Должно быть:**
```toml
dependencies = [
    "mcp-proxy-adapter>=6.9.102",
    ...
]
```

### Изменение 4: Проверка использования собственной очереди

**Проблема:** Проект использует собственную реализацию `ai_admin/task_queue/`, но также использует `mcp_proxy_adapter.queue`.

**Файлы для проверки:**
- `ai_admin/task_queue/task_queue.py` - собственная реализация TaskQueue
- `ai_admin/task_queue/queue_manager.py` - собственный QueueManager
- `ai_admin/dependency_injection.py` (строки 129-135) - регистрация queue_manager

**Рекомендация:** 
- Проверить, не нужно ли мигрировать на `queuemgr-1.0.13` или `mcp_proxy_adapter.queue`
- Если используется собственная реализация, убедиться в совместимости с новым API

### Изменение 5: Проверка импортов ошибок

**Файлы с потенциальными проблемами:**
- Все файлы в `commands/` с импортами `CommandError as CustomError`
- Файлы, использующие старые названия: `NetworkError`, `PermissionError`

**Действие:** Убедиться, что все используют правильные названия из новой версии.

### Изменение 6: Использовать только очередь адаптера

**ЗАДАЧА:** Убедиться, что все команды используют только `mcp_proxy_adapter.queue`.

**Команды, использующие `mcp_proxy_adapter.queue`:**

1. **commands/vast_create_command.py** (строки 20-21):
```python
from mcp_proxy_adapter.queue import Task, TaskType, TaskStatus
from mcp_proxy_adapter.queue import queue_manager
```

2. **commands/vast_destroy_command.py** (строки 20-21):
```python
from mcp_proxy_adapter.queue import Task, TaskType, TaskStatus
from mcp_proxy_adapter.queue import queue_manager
```

3. **commands/ssh_exec_command.py** (строки 59-60):
```python
from mcp_proxy_adapter.queue import queue_manager
from mcp_proxy_adapter.queue import TaskType, Task
```

4. **commands/ftp_upload_command.py** (строки 118-119):
```python
from mcp_proxy_adapter.queue import queue_manager
from mcp_proxy_adapter.queue import Task, TaskType
```

5. **Другие команды:**
   - `commands/ftp_mkdir_command.py`
   - `commands/docker_pull_command.py`
   - `commands/queue_remove_task_command.py`
   - `commands/queue_cancel_task_command.py`

**Проверка совместимости API:**

1. **Проверить API `mcp_proxy_adapter.queue.queue_manager` в версии 6.9.102:**
   - `add_task(task: Task) -> str` - изменилась ли сигнатура?
   - `get_task(task_id: str) -> Task` - изменился ли формат возврата?
   - `cancel_task(task_id: str, force: bool = False) -> bool` - изменилась ли сигнатура?
   - `remove_task(task_id: str, force: bool = False) -> bool` - изменилась ли сигнатура?
   - `get_tasks_by_status(status: TaskStatus) -> List[Task]` - изменилась ли сигнатура?

2. **Проверить собственный менеджер `ai_admin.task_queue.queue_manager`:**
   - Убедиться, что API совместим с использованием в командах
   - Проверить, что методы имеют те же сигнатуры

3. **Определить необходимость изменений:**
   - Если API адаптера изменился - обновить использование в командах
   - Если команды должны использовать собственный менеджер - заменить импорты
   - Если оба варианта работают - проверить совместимость и оставить как есть

### Изменение 7: Проверить динамически загружаемые команды

**ЗАДАЧА:** Проверить, остались ли в адаптере механизмы динамической загрузки команд.

**Проверка:**

1. **API `registry.reload_system()`:**
   - Проверить, существует ли в версии 6.9.102
   - Проверить формат возвращаемого значения
   - Проверить, работает ли автоматическое обнаружение

2. **Автоматическое обнаружение:**
   - Проверить настройки `discovery_path` в `config.json`
   - Проверить настройки `auto_discover` в `config.json`
   - Убедиться, что команды из `commands/` загружаются автоматически

3. **Обновить конфигурацию:**
   - Добавить настройки обнаружения команд, если их нет

### Изменение 8: Проверить remote плагины или их аналоги

**ЗАДАЧА:** Проверить, что с remote плагинами или их аналогами в версии 6.9.102.

**Проверка:**

1. **Поддержка remote плагинов:**
   - Проверить, осталась ли поддержка в версии 6.9.102
   - Проверить API загрузки плагинов из URL
   - Проверить настройки `plugin_servers` в конфигурации

2. **CatalogManager:**
   - Проверить, существует ли в версии 6.9.102
   - Проверить API управления плагинами

3. **Кеширование плагинов:**
   - Проверить, работает ли механизм кеширования
   - Проверить настройки кеширования

### Изменение 9: Проверка инициализации команд

**Проверить изменения в API регистрации команд:**

1. **Проверить `registry.reload_system()`:**
```python
# ai_admin/core/command_registry.py (строка 25)
result = await registry.reload_system()
# Проверить формат result - может измениться структура
```

2. **Проверить `registry.register_custom()`:**
```python
# ai_admin/core/command_registry.py (строка 313)
registry.register_custom(command_class)
# Проверить, не изменилась ли сигнатура метода
```

3. **Проверить автоматическое обнаружение:**
   - В `config.json` может потребоваться добавить:
   ```json
   {
     "commands": {
       "discovery_path": "./commands",
       "auto_discover": true
     }
   }
   ```

4. **Проверить хук регистрации:**
```python
# ai_admin/core/server_setup.py (строка 30)
register_custom_commands_hook(custom_commands_hook)
# Проверить, не изменилась ли сигнатура
```

### Изменение 8: Конфигурация для локальной разработки

**Обновить `config.json` для работы без контейнера:**

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 20000,
    "debug": true
  },
  "ssl": {
    "enabled": false
  },
  "security": {
    "enabled": false
  },
  "commands": {
    "discovery_path": "./commands",
    "auto_discover": true
  },
  "queue": {
    "max_concurrent": 2,
    "storage_path": "./queue_storage"
  },
  "logging": {
    "level": "DEBUG",
    "file": "./logs/ai_admin.log"
  }
}
```

**Проверить пути в коде:**
- Все абсолютные пути заменить на относительные
- Использовать `Path(__file__).parent` для базовых путей
- Убедиться, что директории создаются автоматически

### Изменение 9: Унификация импортов очереди (старое, оставить для справки)

**Проблема:** Обнаружены несоответствия в импортах очереди:

1. **Используется `mcp_proxy_adapter.queue`:**
   - `commands/vast_create_command.py`
   - `commands/vast_destroy_command.py`
   - `commands/ssh_exec_command.py`
   - `commands/docker_pull_command.py`

2. **Используется `ai_admin.task_queue`:**
   - `commands/ftp_download_command.py`
   - `commands/ftp_list_command.py`
   - `commands/ftp_delete_command.py`

3. **Используется `ai_admin.queue.queue_manager`:**
   - `ai_admin/dependency_injection.py` (строка 131)

**Рекомендация:** 
- Унифицировать все импорты на использование `mcp_proxy_adapter.queue` (если это поддерживается в версии 6.9.102)
- Или мигрировать на `queuemgr-1.0.13` напрямую
- Обновить `ai_admin/dependency_injection.py` для использования правильного импорта

**Файлы для изменения:**
```python
# commands/ftp_download_command.py, ftp_list_command.py, ftp_delete_command.py
# БЫЛО:
from ai_admin.task_queue.task_queue_manager import TaskQueueManager, Task, TaskType

# ДОЛЖНО БЫТЬ (если используется mcp_proxy_adapter):
from mcp_proxy_adapter.queue import queue_manager, Task, TaskType

# ИЛИ (если используется queuemgr напрямую):
from queuemgr import QueueManager, Task, TaskType
```

```python
# ai_admin/dependency_injection.py (строка 131)
# БЫЛО:
from ai_admin.queue.queue_manager import queue_manager, QueueManager

# ДОЛЖНО БЫТЬ:
from mcp_proxy_adapter.queue import queue_manager
# Или проверить правильный путь к QueueManager
```

## 💡 РЕКОМЕНДАЦИИ

1. **Сначала выполнить все проверки** - по результатам будет скорректирован план
2. Создать ветку для обновления: `git checkout -b update-packages-6.9.102`
3. Запустить тесты перед обновлением для baseline
4. Обновить пакеты по одному и тестировать после каждого
5. Использовать type checking (mypy) для выявления проблем
6. Проверить документацию обновленных пакетов на breaking changes
7. **Важно:** Сначала обновить только `requirements.txt`, установить пакеты и запустить тесты для выявления реальных проблем

## 📚 ДЕТАЛЬНЫЙ АНАЛИЗ ПАКЕТОВ (для справки)

Детальный анализ каждого пакета и его использования в проекте. Используется как справочная информация после выполнения проверок.

