# 1.1: List All Files Importing QueueManager

## Atomic Steps
1. Run `find_usages(target_name="QueueManager", target_type="class")` on `vast_srv`
2. Filter results by `usage_type="import"`
3. Extract unique `file_path` values
4. For each file note: which `add_*_task` methods are called (usage_type="call")
5. Save result table to `docs/plans/step_1/queuemanager_importers.md`

## Expected Output
```
file                                      | methods called
ai_admin/commands/vast_create_command.py  | add_vast_create_task
ai_admin/commands/vast_destroy_command.py | add_vast_destroy_task
ai_admin/queue_management/queue_client.py | (singleton holder)
...
```
