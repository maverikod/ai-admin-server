# QueueClient importers (Step 1.2)

| file | role |
|------|------|
| ai_admin/commands/queue_health_command.py | `async with QueueClient()` |
| ai_admin/commands/queue_statistics_command.py | same |
| ai_admin/commands/queue_logs_command.py | same |
| ai_admin/commands/queue_filter_command.py | same + `QueueFilter` |
| ai_admin/commands/queue_clear_command.py | same + `QueueFilter` |
| commands/queue_* (mirror of above paths) | duplicate command tree |

Note: `QueueClient` holds `QueueManager()` in `ai_admin/queue_management/queue_client.py`. Legacy queue layer removal is scheduled in project **Step 6** (see `PARALLEL.md`), not "Step 5" as in older TASKS copy.
