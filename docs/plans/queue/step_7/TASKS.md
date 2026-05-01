# STEP 7 TASKS — Atomic Instructions for Haiku
# Final Cleanup: format, lint, typecheck, hard-delete, report

---

## 7.1: Format all Job files

### TASK 1
List all Job files:
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="ai_admin/jobs/*.py"
)
```
Save: list of `relative_path` values.

### TASK 2
For EACH file in list:
```
format_code(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<relative_path>
)
```
**Expected:** `formatted=True` for each. One call per file.

---

## 7.2: Format migrated command files

### TASK 1
Get list of all migrated command files from dependency_matrix.md:
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/dependency_matrix.md"
)
```
Extract: all `command` column values (unique file paths).

### TASK 2
For EACH command file:
```
format_code(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<command_file>
)
```

---

## 7.3: Lint Job files

### TASK 1
For EACH file in `ai_admin/jobs/` (from 7.1 list):
```
lint_code(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<relative_path>
)
```
**Expected:** `error_count=0` for each.
**If errors:** read `errors` list, fix via CST (load → find node → fix → save), re-run lint.

---

## 7.4: Lint migrated command files

### TASK 1
For EACH migrated command file (from 7.2 list):
```
lint_code(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<command_file>
)
```
**Expected:** `error_count=0` for each.

---

## 7.5: Type check Job files

### TASK 1
For EACH file in `ai_admin/jobs/`:
```
type_check_code(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<relative_path>
)
```
**Save:** all errors per file.

### TASK 2
For each `arg-type` error:
- Read the error: which function, which argument, expected type vs actual type
- CST load file → find the function node → fix the type annotation → save tree

### TASK 3
For each `override` error:
- The method signature must match the parent class (`QueueJobBase.run()` return type)
- Fix return type annotation: change to match parent
- CST load → find method → fix signature → save

### TASK 4
Re-run type_check_code after fixes. Repeat until 0 errors.

---

## 7.6: Type check migrated command files

### TASK 1
For EACH migrated command file:
```
type_check_code(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<command_file>
)
```
Fix errors same as 7.5 TASK 2–4.

---

## 7.7: Final comprehensive_analysis

### TASK 1
```
comprehensive_analysis(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  check_placeholders=True,
  check_stubs=True,
  check_empty_methods=True,
  check_imports=True,
  check_long_files=True,
  check_duplicates=True,
  check_flake8=True,
  check_mypy=True
)
```
This is queued. Save job_id.

### TASK 2
Poll until completed:
```
queue_get_job_status(job_id=<from TASK 1>)
```

### TASK 3
Read summary. Check ALL of:
- `total_stubs` = 0 in production files (`ai_admin/`)
- `total_empty_methods` = 0 in production files
- `files_with_flake8_errors` in `ai_admin/` = 0
- No file in `ai_admin/jobs/` or `ai_admin/commands/` exceeds 400 lines

### TASK 4
If any check fails:
- Fix the issue
- Re-run comprehensive_analysis
- Do NOT proceed to TASK 5 until all pass

---

## 7.8: Hard-delete trash

### TASK 1: Final check — confirm Step 5 tests still pass
```
run_project_module(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  module="pytest",
  args=["tests/queue/", "-q", "--tb=short"]
)
```
**Expected:** all tests pass.
**If any fail:** STOP. Do NOT proceed with hard-delete.

### TASK 2: List what will be permanently deleted
```
list_deleted_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9"
)
```
Read the list. Confirm all entries are legacy queue files (task_queue, queue_management, executors).
If any non-legacy file appears: investigate before proceeding.

### TASK 3: Hard-delete
```
cleanup_deleted_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  hard_delete=True
)
```
**WARNING:** This is IRREVERSIBLE. Only run after Step 7.7 and 7.8 TASK 1 pass.

### TASK 4: Verify trash empty
```
list_deleted_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9"
)
```
**Expected:** count=0.

---

## 7.9: Write completion report

### TASK 1: Count migrated commands
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/dependency_matrix.md"
)
```
Count rows. Save as `N_commands`.

### TASK 2: Count new files created
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="ai_admin/jobs/*.py"
)
```
Count. Save as `N_jobs`.

### TASK 3: Write report
```
create_text_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/REFACTORING_COMPLETE.md",
  content=<report>
)
```
**Report template:**
```markdown
# Queue Refactoring Complete

## Result
Task Queue (ai_admin/task_queue/ + ai_admin/queue_management/) fully replaced
with queuemgr-based QueueManagerIntegration.

## Metrics
- Deleted: ai_admin/task_queue/ ({N} files, permanently removed)
- Deleted: ai_admin/queue_management/ ({N} files, permanently removed)
- Created: ai_admin/jobs/ ({N_jobs} Job classes)
- Created: ai_admin/queue/integration.py
- Migrated: {N_commands} commands to QueueManagerIntegration
- Tests: {N_unit} unit + {N_integration} integration tests passing
- comprehensive_analysis: 0 stubs, 0 flake8 errors in production

## Steps completed
1. Audit & map ✔
2. Define Job classes ✔
3. Wire QueueManagerIntegration ✔
4. Migrate commands ✔
5. Tests ✔
6. Delete legacy layer ✔
7. Final cleanup ✔
```

## DONE CHECK for Step 7 (and entire refactoring)
- [ ] format_code ran on all Job files
- [ ] format_code ran on all migrated command files
- [ ] lint passes: 0 errors in ai_admin/jobs/ and ai_admin/commands/
- [ ] typecheck: 0 errors in ai_admin/jobs/ and ai_admin/commands/
- [ ] comprehensive_analysis: 0 stubs, 0 empty methods, 0 flake8 in production
- [ ] Step 5 tests still passing
- [ ] Trash hard-deleted (permanently)
- [ ] REFACTORING_COMPLETE.md written
