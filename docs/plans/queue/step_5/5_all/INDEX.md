# Step 5 Atomic Steps: Delete Legacy Layer

## 5.1–5.3: Pre-deletion Verification
1. Run `find_usages(target_name="QueueManager")` — must return zero results outside `ai_admin/queue/`
2. Run `find_usages(target_name="QueueClient")` — must return zero results
3. Run `find_usages` for each Executor class — all must be zero
4. If any non-zero: block deletion, fix remaining references first

## 5.4: Delete ai_admin/task_queue/
1. List all files in `ai_admin/task_queue/` via `list_project_files`
2. Run `delete_file` for each (soft-delete to trash)
3. Verify `list_project_files` returns empty for that path
4. Confirm DB: `list_deleted_files` shows all expected files in trash

## 5.5: Delete ai_admin/queue_management/
1. List all files in `ai_admin/queue_management/`
2. Run `delete_file` for each
3. Verify deletion

## 5.6: Remove QueueDaemon
1. `delete_file` on `QueueDaemon` source file
2. Remove any CLI entry point script referencing it

## 5.7–5.8: Clean up __init__.py re-exports
1. Read `ai_admin/__init__.py` — remove any re-exports of deleted classes
2. Read `commands/__init__.py` — remove stale imports
3. Apply via CST tools

## 5.9–5.10: Verify clean state
1. Run full pytest suite: `run_project_module(module="pytest", args=["tests/"])`
2. Fix any import errors
3. Run `comprehensive_analysis` on `vast_srv` — no critical issues
