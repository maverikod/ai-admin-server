# 1.5 TASKS — Atomic Instructions for Haiku

## TASK 1
**Action:** Get methods of QueueManager from queue_manager_impl.py
```
list_class_methods(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  class_name="QueueManager"
)
```
**Save:** `methods_impl` = list of method names and their line numbers

## TASK 2
**Action:** Get file_path of queue_manager.py (the root duplicate)
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="ai_admin/task_queue/queue_manager.py"
)
```
**Save:** `dup_file_path`

## TASK 3
**Action:** Get methods of QueueManager from queue_manager.py
```
get_code_entity_info(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  entity_type="class",
  entity_name="QueueManager",
  file_path="ai_admin/task_queue/queue_manager.py"
)
```
**Save:** `methods_root`

## TASK 4
**Action:** Extract method names from both results
```python
names_impl = set(m["name"] for m in methods_impl)
names_root = set(m["name"] for m in methods_root)
only_in_impl = names_impl - names_root
only_in_root = names_root - names_impl
shared = names_impl & names_root
```

## TASK 5
**Action:** Read __init__ of both files to compare Singleton logic
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/task_queue/queue_manager/queue_manager_impl.py",
  start_line=1,
  end_line=30
)
```
Then:
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/task_queue/queue_manager.py",
  start_line=1,
  end_line=30
)
```
**Compare:** do __new__ implementations differ?

## TASK 6
**Action:** Read __init__.py of the queue_manager package
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/task_queue/queue_manager/__init__.py"
)
```
**Verify:** it imports from queue_manager_impl (not from root file)

## TASK 7
**Action:** Build diff report string:
```
## QueueManager Duplicate Analysis
- queue_manager_impl.py: N methods
- queue_manager.py: M methods
- Only in impl: [...]
- Only in root: [...]
- Shared: N
- __init__ singleton diff: YES/NO
- Canonical: queue_manager_impl.py (package __init__ imports from it)
- Action: delete queue_manager.py in Step 6.2
```

## TASK 8
**Action:** Write file
```
create_text_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/queuemanager_diff.md",
  content=<report>
)
```

## DONE CHECK
- [ ] Both method lists captured
- [ ] Diff sets computed (only_in_impl, only_in_root)
- [ ] Canonical version decided
- [ ] File written
