# QueueManager importers (Step 1.1)

| file | import style | queue API used (observed) |
|------|--------------|---------------------------|
| ai_admin/task_queue/__init__.py | `from ai_admin.task_queue.queue_manager import QueueManager` | re-export |
| ai_admin/queue_management/queue_client.py | same | `QueueManager()`; wraps manager |
| ai_admin/commands/queue_cancel_task_command.py | same | `get_task`, `cancel_task` |
| ai_admin/commands/queue_remove_task_command.py | same | `get_task`, `remove_task` |
| ai_admin/commands/vast_create_command.py | same | inside `use_queue`: `QueueManager()`, then `add_task`, `get_tasks_by_status` |
| ai_admin/commands/vast_destroy_command.py | same | inside `use_queue`: `QueueManager()`, then `add_task`, `get_tasks_by_status` |
| ai_admin/commands/docker_pull_command.py | dynamic `TaskQueueManager` / `queue_manager` | mixed legacy |
| ai_admin/commands/ftp_* (several) | dynamic `queue_manager` singleton from `queue_manager.py` | `add_task` |
| ai_admin/commands/ssh_exec_command.py | dynamic `queue_manager` | `add_task` |

Notes: Root `ai_admin/task_queue/queue_manager.py` exports module-level `queue_manager`; package canonical is `queue_manager_impl.py` (see 1.5).
