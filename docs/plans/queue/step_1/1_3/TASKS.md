# 1.3 TASKS — Atomic Instructions for Haiku

Executor class names to process:
`DockerExecutor, K8sExecutor, K8sKindExecutor, KindExecutor, FTPExecutor, FtpExecutor,
VastExecutor, OllamaExecutor, GitExecutor, GitHubExecutor, SSLExecutor, SystemExecutor`

## TASK 1
**Action:** Get all classes in ai_admin/task_queue/
```
list_code_entities(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  entity_type="class",
  file_path="ai_admin/task_queue"
)
```
**Save:** `executor_classes` (list of {name, file_path, line})

## TASK 2
**Action:** For DockerExecutor — get methods
```
list_class_methods(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  class_name="DockerExecutor"
)
```
**Save:** `docker_methods`

## TASK 3
**Action:** For K8sExecutor — get methods
```
list_class_methods(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  class_name="K8sExecutor"
)
```

## TASK 4
**Action:** Repeat for each remaining executor:
- K8sKindExecutor
- KindExecutor
- FTPExecutor
- FtpExecutor
- VastExecutor
- OllamaExecutor
- GitExecutor
- GitHubExecutor
- SSLExecutor
- SystemExecutor

**One call per executor. Save each result separately.**

## TASK 5
**Action:** Build table
```
| Executor | file_path | method_name | args | docstring_first_line |
```
For each executor, for each method, add one row.

## TASK 6
**Action:** Write file
```
create_text_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/executors_map.md",
  content=<table>
)
```

## TASK 7
**Action:** Verify
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="docs/plans/step_1/executors_map.md"
)
```
**Expected:** count=1

## DONE CHECK
- [ ] All 12 executors listed
- [ ] Each executor has at least 1 method row
- [ ] FTPExecutor and FtpExecutor both present (for diff in 1.6)
