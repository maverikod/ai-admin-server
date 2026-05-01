# Queue Refactoring Plan: Task Queue → queuemgr

## Goal

Replace the custom Task Queue (`ai_admin/task_queue/`, `ai_admin/queue_management/`) with the
unified `queuemgr`-based system already used by `mcp_proxy_adapter`. Remove all Executor classes,
deduplicate `QueueManager`, eliminate `FTPExecutor`/`FtpExecutor` split, and make every command
submit jobs via `QueueManagerIntegration`.

## High-Level Steps

| # | Step | Directory |
|---|------|-----------|
| 1 | **Audit & map** — catalogue every Task Queue consumer, diff duplicates, build dependency matrix | [step_1/](step_1/INDEX.md) |
| 2 | **Define Job classes** — create `QueueJobBase` subclasses for each domain | [step_2/](step_2/INDEX.md) |
| 3 | **Wire `QueueManagerIntegration`** — replace singleton `QueueManager` with integration layer | [step_3/](step_3/INDEX.md) |
| 4 | **Migrate commands** — rewrite each command to submit via `QueueManagerIntegration` | [step_4/](step_4/INDEX.md) |
| 5 | **Tests** — cover new Job classes and migrated commands | [step_5/](step_5/INDEX.md) |
| 6 | **Delete legacy layer** — remove Executors, old `QueueManager`, `QueueClient`, `QueueDaemon` | [step_6/](step_6/INDEX.md) |
| 7 | **Final cleanup** — format, lint, typecheck, comprehensive_analysis, hard-delete trash | [step_7/](step_7/INDEX.md) |

**Order change vs original plan:**
- Tests (was Step 7) moved to Step 5 — tests BEFORE deletion
- Delete legacy (was Step 5) moved to Step 6 — delete only after tests pass
- Deduplicate & clean (was Step 6) merged: duplicate diffs moved to Step 1 (audit),
  code cleanup merged into Step 7 (final cleanup)

## Key Files Affected

```
ai_admin/task_queue/              ← DELETE entirely after migration (Step 6)
ai_admin/queue_management/        ← DELETE entirely after migration (Step 6)
ai_admin/commands/*_command.py    ← MODIFY: replace QueueManager calls (Step 4)
ai_admin/__init__.py              ← MODIFY: startup wiring (Step 3)
```

## New Files Created

```
ai_admin/jobs/                    ← 9 Job classes + __init__.py (Step 2)
ai_admin/queue/integration.py     ← queue integration accessor (Step 3)
tests/queue/                      ← unit + integration tests (Step 5)
```

## Dependencies

- `queuemgr` — already in `.venv`, used by `mcp_proxy_adapter`
- `QueueJobBase` — base class for all new Job classes
- `QueueManagerIntegration` — already implemented in `mcp_proxy_adapter`

## Important: Python file creation

**Do NOT use `create_text_file` for `.py` files** — it only supports `.md/.txt/.rst/.adoc`.
Use `cst_create_file(project_id, file_path, docstring)` to create Python files,
then `cst_modify_tree` to add classes/functions, then `cst_save_tree` to persist.
