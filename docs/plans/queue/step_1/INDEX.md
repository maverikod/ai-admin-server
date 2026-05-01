# Step 1: Audit & Map — Catalogue Every Task Queue Consumer

## Goal
Before touching any code, build a complete map of what uses the Task Queue
so nothing is missed during migration. Also identify duplicates for cleanup.

## Tactical Steps

| # | Task | Detail |
|---|------|---------|
| 1.1 | List all files that import `QueueManager` | [1_1/](1_1/INDEX.md) |
| 1.2 | List all files that import `QueueClient` | [1_2/](1_2/INDEX.md) |
| 1.3 | List all Executor classes and their methods | [1_3/](1_3/INDEX.md) |
| 1.4 | Map each `add_*_task` method to its Executor | [1_4/](1_4/INDEX.md) |
| 1.5 | **Diff** `queue_manager.py` vs `queue_manager_impl.py` — decide canonical | [1_5/](1_5/INDEX.md) |
| 1.6 | **Diff** `FTPExecutor` vs `FtpExecutor` — decide merge strategy | [1_6/](1_6/INDEX.md) |
| 1.7 | Catalogue `TaskStatus` enum values and map to `queuemgr` statuses | [1_7/](1_7/INDEX.md) |
| 1.8 | Catalogue `QueueAction` / `QueueFilter` enum usages and map to `queuemgr` | [1_8/](1_8/INDEX.md) |
| 1.9 | Document `QueueDaemon` usages and entry points | [1_9/](1_9/INDEX.md) |
| 1.10 | Produce final dependency matrix: command → task method → executor → Job class | [1_10/](1_10/INDEX.md) |

## Output Artifacts
- `docs/plans/queue/step_1/outputs/queuemanager_importers.md` — all QueueManager consumers
- `docs/plans/queue/step_1/outputs/queueclient_importers.md` — all QueueClient consumers
- `docs/plans/queue/step_1/outputs/executors_map.md` — executor class → methods table
- `docs/plans/queue/step_1/task_executor_map.md` — add_*_task → executor mapping
- `docs/plans/queue/step_1/outputs/queuemanager_diff.md` — impl vs root duplicate diff
- `docs/plans/queue/step_1/outputs/ftp_executor_diff.md` — FTP executor merge plan
- `docs/plans/queue/step_1/outputs/task_status_map.md` — old → new status translation
- `docs/plans/queue/step_1/outputs/queue_action_filter_map.md` — action/filter mapping
- `docs/plans/queue/step_1/outputs/queue_daemon_analysis.md` — daemon analysis
- `docs/plans/queue/step_1/dependency_matrix.md` — **master migration checklist**

## Note on duplicates
Steps 1.5 and 1.6 perform the **analysis** of duplicates (formerly Step 6.1–6.5).
The actual **deletion** of duplicate files happens in Step 6 (delete legacy layer)
after all migrations and tests pass.

## Note on command paths
All commands in `vast_srv` live under `ai_admin/commands/` or root `commands/`.
The dependency matrix must use consistent relative paths from project root.
Use `list_project_files(glob="**/commands/**")` to discover exact locations.
