# Step 6 Atomic Steps: Deduplicate & Clean

## 6.1–6.3: QueueManager Deduplication
1. Read both `queue_manager.py` (line 937) and `queue_manager_impl.py` (line 938) entirely
2. Run diff: extract method list from each via `list_class_methods` calls
3. Confirm `queue_manager_impl.py` is the canonical version (has the package `__init__` re-export)
4. Find all `from ai_admin.task_queue.queue_manager import QueueManager` pointing to root file
5. Update those imports to point to `queue_manager_impl` (or package path)
6. Delete `queue_manager.py` via `delete_file`

## 6.4–6.5: FTP Deduplication (already done in 2.7, verify)
1. Confirm `FtpJob` covers all operations from both old executors
2. Confirm both old executor files are in trash from Step 5

## 6.6: Remove stale QueueManagerError subclasses
1. List all `QueueManagerError` subclasses via `get_class_hierarchy`
2. For each: check if referenced anywhere outside deleted code
3. Delete orphan error classes via CST or `delete_file`

## 6.7: Audit commands for remaining QueueManager() direct calls
1. Run `fulltext_search(query="QueueManager()")` on `vast_srv`
2. Any hit = missed migration; fix before proceeding

## 6.8: Fix validate_log_path duplication
1. Run `find_usages(target_name="validate_log_path")` — find all 3 locations
2. Extract to `ai_admin/core/log_utils.py` as single function
3. Replace 3 inline definitions with import via CST
4. Lint + typecheck

## 6.9–6.10: Final quality pass
1. Run `format_code` on all modified files
2. Run `lint_code` — fix all E303/E302 spacing issues
3. Run `type_check_code` — fix `arg-type` and `override` errors in migrated files
4. Target: zero flake8 errors in `ai_admin/commands/` and `ai_admin/jobs/`
