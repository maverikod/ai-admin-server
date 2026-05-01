# 1.4 TASKS — Atomic Instructions for Haiku

## TASK 1
**Action:** Read queue_manager_impl.py lines 1-100 to find __init__ and first add_* method
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/task_queue/queue_manager/queue_manager_impl.py",
  start_line=1,
  end_line=100
)
```

## TASK 2
**Action:** Read lines 100-250 (add_push_task, add_git_task, add_github_task)
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/task_queue/queue_manager/queue_manager_impl.py",
  start_line=100,
  end_line=250
)
```
**For each add_* method found:** note which Executor class is instantiated and which method is called.

## TASK 3
**Action:** Read lines 250-450 (add_build_task through add_ollama_run_task)
```
universal_file_read(..., start_line=250, end_line=450)
```

## TASK 4
**Action:** Read lines 450-650 (add_k8s_* methods)
```
universal_file_read(..., start_line=450, end_line=650)
```

## TASK 5
**Action:** Read lines 650-950 (add_vast_*, add_system_*, add_ssl_*, add_task, push_task)
```
universal_file_read(..., start_line=650, end_line=950)
```

## TASK 6
**Action:** Build mapping table from all reads
```
| add_method | executor_class | executor_method | params_passed |
|------------|----------------|-----------------|---------------|
| add_push_task | DockerExecutor | push() | image_name, tag |
| add_git_task | GitExecutor | execute() | operation_type, ... |
```

## TASK 7
**Action:** For each row: verify executor_method exists in executors_map.md (cross-check with 1.3)
If method not found in executors_map — mark row as INLINE (logic inside QueueManager itself).

## TASK 8
**Action:** Write file
```
create_text_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/task_executor_map.md",
  content=<table>
)
```

## TASK 9
**Action:** Verify
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="docs/plans/step_1/task_executor_map.md"
)
```
**Expected:** count=1

## DONE CHECK
- [ ] All 20 add_* methods mapped
- [ ] INLINE rows flagged separately
- [ ] No row has empty executor_method
