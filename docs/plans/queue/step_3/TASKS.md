# STEP 3 TASKS — Atomic Instructions for Haiku

## CRITICAL: Python file creation
**Use `cst_create_file` (NOT `create_text_file`) for ALL `.py` files.**
`create_text_file` only supports `.md/.txt/.rst/.adoc` and will FAIL on `.py`.
Pattern for `.py`: `cst_create_file` → `cst_modify_tree` → `cst_save_tree`.

---

## 3.1: Verify queuemgr installed

### TASK 1
```
project_pip_check(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  packages=["queuemgr"]
)
```
If present=True: skip to TASK 4. Else: TASK 2.

### TASK 2 (only if not installed)
```
project_pip_install(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  packages=["queuemgr"]
)
```
Queued. Save job_id.

### TASK 3 (only if TASK 2 ran)
```
queue_get_job_status(job_id=<from TASK 2>)
```
Poll until status=="completed". If failed: STOP and report.

### TASK 4
```
project_pip_show(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  packages=["queuemgr"]
)
```
Save version string.

### TASK 5
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="requirements.txt"
)
```
If queuemgr not in content: add `queuemgr=={version}` via `universal_file_replace`.

---

## 3.2–3.3: Create integration package

### TASK 1
Check if `ai_admin/queue/` exists:
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="ai_admin/queue/*"
)
```
If count > 0: skip TASK 2–3, go to TASK 4.

### TASK 2
Create `ai_admin/queue/__init__.py`:
```
cst_create_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/queue/__init__.py",
  docstring="Queue integration package."
)
```
Save: `tree_id_init`

Add exports:
```
cst_modify_tree(
  tree_id=<tree_id_init>,
  operations=[{
    "action": "insert", "parent_node_id": "__root__", "position": "last",
    "code_lines": [
      "from .integration import get_queue_integration, set_queue_integration",
      "",
      "__all__ = ['get_queue_integration', 'set_queue_integration']"
    ]
  }]
)
```

Save (validate=False — integration.py not yet exists):
```
cst_save_tree(
  tree_id=<tree_id_init>,
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/queue/__init__.py",
  backup=False,
  validate=False
)
```

### TASK 3
Create `ai_admin/queue/integration.py`:
```
cst_create_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/queue/integration.py",
  docstring="Queue integration — wraps QueueManagerIntegration from mcp_proxy_adapter."
)
```
Save: `tree_id_int`

Add code:
```
cst_modify_tree(
  tree_id=<tree_id_int>,
  operations=[{
    "action": "insert", "parent_node_id": "__root__", "position": "last",
    "code_lines": [
      "from typing import Optional",
      "from mcp_proxy_adapter.queue.integration import QueueManagerIntegration",
      "",
      "_integration: Optional[QueueManagerIntegration] = None",
      "",
      "",
      "def get_queue_integration() -> QueueManagerIntegration:",
      "    \\\"\\\"\\\"Return the running queue integration instance.",
      "",
      "    Raises:",
      "        RuntimeError: If not started via set_queue_integration().",
      "    \\\"\\\"\\\"",
      "    if _integration is None:",
      "        raise RuntimeError(",
      "            'Queue integration not started.'",
      "            ' Call set_queue_integration() in server startup.'",
      "        )",
      "    return _integration",
      "",
      "",
      "def set_queue_integration(integration: QueueManagerIntegration) -> None:",
      "    \\\"\\\"\\\"Register the running queue integration instance.",
      "",
      "    Args:",
      "        integration: Started QueueManagerIntegration instance.",
      "    \\\"\\\"\\\"",
      "    global _integration",
      "    _integration = integration"
    ]
  }]
)
```

Save:
```
cst_save_tree(
  tree_id=<tree_id_int>,
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/queue/integration.py",
  backup=False,
  validate=True
)
```

### TASK 4
Lint + typecheck:
```
lint_code(project_id=PROJ, file_path="ai_admin/queue/integration.py")
type_check_code(project_id=PROJ, file_path="ai_admin/queue/integration.py")
```
Expected: error_count=0.

---

## 3.4–3.5: Wire into AIAdminServer startup/shutdown

### TASK 1
Find AIAdminServer:
```
get_code_entity_info(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  entity_type="class",
  entity_name="AIAdminServer"
)
```
Save: file_path, line.

### TASK 2
Get methods:
```
list_class_methods(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  class_name="AIAdminServer"
)
```
Find startup/lifespan method. Save line.

### TASK 3
Read startup body:
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<server_file>,
  start_line=<startup_line>,
  end_line=<startup_line + 40>
)
```

### TASK 4
CST load server file:
```
cst_load_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<server_file_relative>
)
```
Save: tree_id.

### TASK 5
Find startup method node:
```
cst_find_node(
  tree_id=<tree_id>,
  search_type="simple",
  node_type="FunctionDef",
  name="<startup_method_name>"
)
```
Save: node_id.

### TASK 6
Inspect current code:
```
cst_get_node_info(
  tree_id=<tree_id>,
  node_id=<node_id>,
  include_code=True
)
```

### TASK 7
Insert queue start AFTER last statement in startup:
```
cst_modify_tree(
  tree_id=<tree_id>,
  operations=[{
    "action": "insert",
    "target_node_id": <last_statement_node_id_in_startup>,
    "position": "after",
    "code_lines": [
      "# Start queue integration",
      "from ai_admin.queue import set_queue_integration",
      "from mcp_proxy_adapter.queue.integration import QueueManagerIntegration",
      "_queue = QueueManagerIntegration(in_memory=True, max_concurrent_jobs=4)",
      "await _queue.start()",
      "set_queue_integration(_queue)"
    ]
  }]
)
```

### TASK 8
Find shutdown method (same pattern as TASK 5).
Insert AT START of shutdown:
```
code_lines = [
  "from ai_admin.queue import get_queue_integration",
  "try:",
  "    await get_queue_integration().stop()",
  "except RuntimeError:",
  "    pass  # integration not started"
]
```
Use `position="before"` on first statement of shutdown method.

### TASK 9
Save tree:
```
cst_save_tree(
  tree_id=<tree_id>,
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<server_file_relative>,
  backup=True,
  validate=True
)
```

### TASK 10
Lint + typecheck server file.

---

## 3.6–3.8: Configure limits via settings

### TASK 1
Find AIAdminSettingsManager:
```
get_code_entity_info(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  entity_type="class",
  entity_name="AIAdminSettingsManager"
)
```
Save: file_path.

### TASK 2
Read settings file. Check: is there a `queue` section?

### TASK 3
CST load settings file. Insert queue config fields:
```
code_lines = [
  "# Queue configuration",
  "queue_max_concurrent: int = 4",
  "queue_max_size: Optional[int] = None",
  "queue_retention_seconds: int = 21600"
]
```
Insert at appropriate location in class body. Save. Lint. Typecheck.

### TASK 4
Update server startup (3.4 TASK 7) to use settings values:
```
code_lines = [
  "_queue = QueueManagerIntegration(",
  "    in_memory=True,",
  "    max_concurrent_jobs=settings.queue_max_concurrent,",
  "    max_queue_size=settings.queue_max_size,",
  "    completed_job_retention_seconds=settings.queue_retention_seconds,",
  ")"
]
```
CST load server file again → find the `QueueManagerIntegration(...)` call → replace → save.

---

## 3.9: Add health endpoint

### TASK 1
Find router registration:
```
fulltext_search(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  query="app.include_router"
)
```
Save: router file path.

### TASK 2
CST load router file.

### TASK 3
Insert health route:
```
cst_modify_tree(
  tree_id=<tree_id>,
  operations=[{
    "action": "insert", "parent_node_id": "__root__", "position": "last",
    "code_lines": [
      "@router.get('/queue/health')",
      "async def queue_health():",
      "    \\\"\\\"\\\"Get queue system health.\\\"\\\"\\\"",
      "    from ai_admin.queue import get_queue_integration",
      "    return await get_queue_integration().get_queue_health()"
    ]
  }]
)
```
Save. Lint. Typecheck.

---

## 3.10: Smoke test

### TASK 1
Create smoke test script via `cst_create_file` (NOT create_text_file):
```
cst_create_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="scripts/smoke_test_queue.py",
  docstring="Smoke test: submit SystemJob to QueueManagerIntegration and verify."
)
```
Save: `tree_id_smoke`.

### TASK 2
Add code:
```
cst_modify_tree(
  tree_id=<tree_id_smoke>,
  operations=[{
    "action": "insert", "parent_node_id": "__root__", "position": "last",
    "code_lines": [
      "import asyncio",
      "from mcp_proxy_adapter.queue.integration import QueueManagerIntegration",
      "from ai_admin.jobs.system_job import SystemJob",
      "",
      "",
      "async def main() -> None:",
      "    \\\"\\\"\\\"Run smoke test for queue integration.\\\"\\\"\\\"",
      "    q = QueueManagerIntegration(in_memory=True, max_concurrent_jobs=1)",
      "    await q.start()",
      "    result = await q.add_job(SystemJob, 'smoke_1', {",
      "        'operation_type': 'system_monitor',",
      "        'include_gpu': False,",
      "        'include_temperature': False,",
      "        'include_processes': False,",
      "    })",
      "    print('Added job:', result)",
      "    await asyncio.sleep(3)",
      "    status = await q.get_job_status('smoke_1')",
      "    print('Status:', status)",
      "    await q.stop()",
      "    print('DONE')",
      "",
      "",
      "asyncio.run(main())"
    ]
  }]
)
```

### TASK 3
Save:
```
cst_save_tree(
  tree_id=<tree_id_smoke>,
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="scripts/smoke_test_queue.py",
  backup=False,
  validate=True
)
```

### TASK 4
Run:
```
run_project_script(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  script_path="scripts/smoke_test_queue.py"
)
```
Expected: output contains "DONE", status = completed.
If error: read output, fix wiring, retry.

---

## DONE CHECK for Step 3
- [ ] queuemgr installed and version pinned in requirements.txt
- [ ] ai_admin/queue/__init__.py created via cst_create_file
- [ ] ai_admin/queue/integration.py created via cst_create_file
- [ ] get_queue_integration() / set_queue_integration() working
- [ ] AIAdminServer startup: integration.start() called
- [ ] AIAdminServer shutdown: integration.stop() called
- [ ] Settings: queue_max_concurrent, queue_max_size, queue_retention_seconds
- [ ] /queue/health endpoint added and responding
- [ ] Smoke test passes (status=completed, output=DONE)
