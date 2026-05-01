# STEP 6 TASKS — Atomic Instructions for Haiku
# Delete Legacy Layer (soft-delete only)

## PRE-CONDITION: Step 5 gate must show ALL PASS before starting.

---

## 6.1: Verify zero QueueManager imports

### TASK 1
```
find_usages(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  target_name="QueueManager",
  target_type="class"
)
```
Filter results: keep only `usage_type=="import"`, exclude paths containing `ai_admin/queue/`.
**Expected:** 0 remaining results.
**If count > 0:** STOP. Return to Step 4, fix the remaining consumers, re-run Step 5 tests.

---

## 6.2: Verify zero QueueClient imports

### TASK 1
```
find_usages(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  target_name="QueueClient",
  target_type="class"
)
```
**Expected:** count=0. If count>0: STOP, fix first.

---

## 6.3: Verify zero Executor imports

### TASK 1
For each name in this list:
`DockerExecutor, K8sExecutor, K8sKindExecutor, KindExecutor, FTPExecutor, FtpExecutor,
VastExecutor, OllamaExecutor, GitExecutor, GitHubExecutor, SSLExecutor, SystemExecutor`

Run one call per name:
```
find_usages(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  target_name="<executor_name>",
  target_type="class"
)
```
**Expected each:** count=0.
**If any count>0:** STOP, fix that consumer.

---

## 6.4: Delete queue_manager.py root duplicate

### TASK 1
Check file exists:
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="ai_admin/task_queue/queue_manager.py"
)
```
If count=0: file already gone — skip to 6.5.

### TASK 2
Search for any import pointing directly to this file:
```
fulltext_search(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  query="from ai_admin.task_queue import queue_manager"
)
```
For each hit: update import to use package path via CST (load → find ImportFrom → replace → save).

### TASK 3
Delete root duplicate:
```
delete_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/task_queue/queue_manager.py"
)
```
**Note:** This is a soft-delete. File goes to trash, not permanently removed.

### TASK 4
Verify deleted:
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="ai_admin/task_queue/queue_manager.py"
)
```
**Expected:** count=0.

---

## 6.5: Soft-delete ai_admin/task_queue/

### TASK 1
List all files:
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="ai_admin/task_queue/**"
)
```
Save: list of all `relative_path` values.

### TASK 2
For EACH file in the list, run ONE call:
```
delete_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<relative_path>
)
```
One call per file. Do not batch. Wait for each to complete.

### TASK 3
Verify directory empty:
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="ai_admin/task_queue/**"
)
```
**Expected:** count=0.

### TASK 4
Confirm in trash:
```
list_deleted_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9"
)
```
Expect all task_queue files visible in deleted list.

---

## 6.6: Soft-delete ai_admin/queue_management/

### TASK 1
List files:
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="ai_admin/queue_management/**"
)
```

### TASK 2
For each file: `delete_file(project_id, file_path)` (one call per file)

### TASK 3
Verify empty:
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="ai_admin/queue_management/**"
)
```
**Expected:** count=0.

---

## 6.7: Remove QueueDaemon

### TASK 1
Read the analysis from Step 1:
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/queue_daemon_analysis.md"
)
```
Extract: `File path` and `CLI entry points` fields.

### TASK 2
Delete QueueDaemon source file:
```
delete_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<daemon_file_relative_path>
)
```

### TASK 3 (only if CLI entry point exists)
Delete CLI entry point script:
```
delete_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<cli_script_relative_path>
)
```

---

## 6.8: Clean up __init__.py stale re-exports

### TASK 1
Read `ai_admin/__init__.py`:
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/__init__.py"
)
```
Search for any line importing from: `task_queue`, `queue_management`, `QueueManager`, `QueueClient`.

### TASK 2
If stale imports found: load file into CST:
```
cst_load_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/__init__.py"
)
```
Save: tree_id

### TASK 3
For each stale import: find its node:
```
cst_find_node(
  tree_id=<tree_id>,
  search_type="xpath",
  query="ImportFrom[module='ai_admin.task_queue']"
)
```
Save: node_id

### TASK 4
Delete node:
```
cst_modify_tree(
  tree_id=<tree_id>,
  operations=[{"action": "delete", "node_id": <node_id>}]
)
```
Repeat TASK 3–4 for each stale import.

### TASK 5
Save tree:
```
cst_save_tree(
  tree_id=<tree_id>,
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/__init__.py",
  backup=True,
  validate=True
)
```

### TASK 6
Repeat TASKS 1–5 for `commands/__init__.py` if it also imports from deleted modules.

---

## 6.9: Run test suite

### TASK 1
```
run_project_module(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  module="pytest",
  args=["tests/", "-x", "-q", "--tb=short"]
)
```
Read output. If any `ImportError` or `ModuleNotFoundError`:
- Identify which deleted module is still imported somewhere
- Use `fulltext_search(query=<module_name>)` to find the file
- Fix via CST (load → delete stale import node → save)
- Re-run until all tests pass

---

## 6.10: Deduplicate validate_log_path (3 copies → 1)

### TASK 1
Find all 3 definitions:
```
find_usages(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  target_name="validate_log_path",
  target_type="function"
)
```
Filter: `usage_type=="definition"`. Save all 3 file_path + line values.

### TASK 2
Read function body from first occurrence:
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<first_file>,
  start_line=<line>,
  end_line=<line+20>
)
```
Save: exact function body lines.

### TASK 3
Create `ai_admin/core/log_utils.py`:
```
cst_create_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/core/log_utils.py",
  docstring="Shared logging utilities."
)
```
Save: tree_id

### TASK 4
Add the function to tree:
```
cst_modify_tree(
  tree_id=<tree_id>,
  operations=[{
    "action": "insert",
    "parent_node_id": "__root__",
    "position": "last",
    "code_lines": <exact body lines from TASK 2>
  }]
)
```

### TASK 5
Save new file:
```
cst_save_tree(
  tree_id=<tree_id>,
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/core/log_utils.py",
  backup=False,
  validate=True
)
```

### TASK 6
For each of the 3 original files:
- `cst_load_file(project_id, file_path)`
- `cst_find_node(tree_id, search_type="simple", node_type="FunctionDef", name="validate_log_path")`
- `cst_modify_tree` → replace function with `from ai_admin.core.log_utils import validate_log_path`
  (delete function node + insert import at top)
- `cst_save_tree(backup=True, validate=True)`

### TASK 7
Lint all modified files:
```
lint_code(project_id=PROJ, file_path=<each modified file>)
```

## DONE CHECK for Step 6
- [ ] find_usages(QueueManager) = 0 outside ai_admin/queue/
- [ ] find_usages(QueueClient) = 0
- [ ] All 12 Executor find_usages = 0
- [ ] queue_manager.py root duplicate deleted
- [ ] ai_admin/task_queue/ empty in project (all soft-deleted)
- [ ] ai_admin/queue_management/ empty in project (all soft-deleted)
- [ ] QueueDaemon deleted
- [ ] ai_admin/__init__.py has no stale imports
- [ ] pytest suite passes with no ImportErrors
- [ ] validate_log_path deduplicated (3 → 1 in log_utils.py)
- [ ] lint passes on all modified files
