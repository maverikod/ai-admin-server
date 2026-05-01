# Step 6: Delete Legacy Layer

## Goal
All tests pass (Step 5 gate cleared). Now safely remove the entire old
Task Queue infrastructure. Use soft-delete only — hard-delete happens in Step 7.

## Pre-condition
**Step 5 gate must be cleared before starting Step 6.**
All unit tests, integration tests, and comprehensive_analysis must pass.

## Tactical Steps

| # | Task | Detail |
|---|------|---------|
| 6.1 | Verify zero imports of `QueueManager` outside `ai_admin/queue/` | [TASKS.md](TASKS.md#61-verify-zero-queuemanager-imports) |
| 6.2 | Verify zero imports of `QueueClient` | [TASKS.md](TASKS.md#62-verify-zero-queueclient-imports) |
| 6.3 | Verify zero imports of any Executor class | [TASKS.md](TASKS.md#63-verify-zero-executor-imports) |
| 6.4 | Delete `queue_manager.py` root duplicate (keep `queue_manager_impl.py`) | [TASKS.md](TASKS.md#64-delete-queuemanagerpy-root-duplicate) |
| 6.5 | Soft-delete `ai_admin/task_queue/` directory | [TASKS.md](TASKS.md#65-soft-delete-aitask_queue) |
| 6.6 | Soft-delete `ai_admin/queue_management/` directory | [TASKS.md](TASKS.md#66-soft-delete-aiqueue_management) |
| 6.7 | Remove `QueueDaemon` and its CLI entry point | [TASKS.md](TASKS.md#67-remove-queuedaemon) |
| 6.8 | Clean up `ai_admin/__init__.py` stale re-exports | [TASKS.md](TASKS.md#68-clean-up-init-re-exports) |
| 6.9 | Run full test suite to confirm no import errors | [TASKS.md](TASKS.md#69-run-test-suite) |
| 6.10 | Extract `validate_log_path` duplication (3 copies → 1) | [TASKS.md](TASKS.md#610-deduplicate-validate_log_path) |

## Detailed Tasks
See: [TASKS.md](TASKS.md)

## Safety
- Use `delete_file` MCP command only (soft-delete to trash)
- Do NOT use `cleanup_deleted_files(hard_delete=True)` here
- Hard-delete only in Step 7 after final comprehensive_analysis
- Git history provides additional backup
