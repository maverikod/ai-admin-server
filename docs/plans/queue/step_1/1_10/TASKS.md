# 1.10 TASKS — Atomic Instructions for Haiku

## TASK 1
**Action:** Read queuemanager_importers.md
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/queuemanager_importers.md"
)
```
**Extract:** list of {command_file, methods_called}

## TASK 2
**Action:** Read task_executor_map.md
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/task_executor_map.md"
)
```
**Extract:** list of {add_method, executor_class, executor_method}

## TASK 3
**Action:** For each command in importers, look up which add_* methods it calls
Then look up executor from task_executor_map
Build rows:
```python
rows = []
for cmd_file, methods in importers:
    for method in methods:
        executor = task_executor_map[method]
        job_class = METHOD_TO_JOB[method]  # map from Step 2 plan
        rows.append({
            "command": cmd_file,
            "add_method": method,
            "executor": executor,
            "job_class": job_class,
            "status": "TODO",
            "has_test": "NO"
        })
```

Method → Job class mapping:
```
add_push_task / add_pull_task / add_build_task → DockerJob
add_git_task                                  → GitJob
add_github_task                               → GitHubJob
add_k8s_*                                     → K8sJob
add_vast_*                                    → VastJob
add_ollama_*                                  → OllamaJob
add_ssl_task                                  → SslJob
add_system_task                               → SystemJob
add_task / push_task                          → depends on task type
```

## TASK 4
**Action:** Format as markdown table
```
| Command class | add_method | Executor | Job class | Status | Test? |
|---------------|------------|----------|-----------|--------|-------|
| VastCreateCommand | add_vast_create_task | VastExecutor | VastJob | TODO | NO |
...
```

## TASK 5
**Action:** Count totals
```python
total = len(rows)
big_table_summary = f"Total: {total} command-method pairs to migrate"
```

## TASK 6
**Action:** Write file
```
create_text_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/dependency_matrix.md",
  content=<table + summary>
)
```

## TASK 7
**Action:** Verify
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="docs/plans/step_1/dependency_matrix.md"
)
```
**Expected:** count=1

## DONE CHECK
- [ ] Every row from queuemanager_importers.md is in matrix
- [ ] Every add_method has executor and job_class
- [ ] Status column all "TODO" (will be updated during migration)
- [ ] Total count makes sense (expect 15-25 rows)
- [ ] File written and indexed
