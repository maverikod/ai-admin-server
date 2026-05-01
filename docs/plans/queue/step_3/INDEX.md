# Step 3: Wire QueueManagerIntegration — Replace Singleton QueueManager

## Goal
Introduce `QueueManagerIntegration` as the single queue backend.
Remove the Singleton pattern from `QueueManager`. Wire startup/shutdown
into `AIAdminServer` lifespan.

## Tactical Steps

| # | Task | Detail |
|---|------|---------|
| 3.1 | Verify `queuemgr` installed in project venv | [3_1/INDEX.md](3_1/INDEX.md) |
| 3.2 | Create `ai_admin/queue/__init__.py` | [TASKS.md](TASKS.md#32-33-create-integrationpy-and-accessor) |
| 3.3 | Create `ai_admin/queue/integration.py` with `get/set_queue_integration()` | [TASKS.md](TASKS.md#32-33-create-integrationpy-and-accessor) |
| 3.4 | Wire `integration.start()` into `AIAdminServer` startup lifespan | [TASKS.md](TASKS.md#34-35-wire-into-aiadminserver-startupshutdown) |
| 3.5 | Wire `integration.stop()` into `AIAdminServer` shutdown lifespan | [TASKS.md](TASKS.md#34-35-wire-into-aiadminserver-startupshutdown) |
| 3.6 | Configure `max_concurrent_jobs`, `max_queue_size` | [TASKS.md](TASKS.md#36-38-configure-limits-via-settings) |
| 3.7 | Configure `completed_job_retention_seconds` (default 6h) | [TASKS.md](TASKS.md#36-38-configure-limits-via-settings) |
| 3.8 | Add `queue` section to `AIAdminSettingsManager` config | [TASKS.md](TASKS.md#36-38-configure-limits-via-settings) |
| 3.9 | Add `/queue/health` endpoint | [TASKS.md](TASKS.md#39-add-health-endpoint) |
| 3.10 | Smoke-test: submit `SystemJob` and verify status flow | [TASKS.md](TASKS.md#310-smoke-test) |

## Detailed Tasks
See: [TASKS.md](TASKS.md) and [3_2_to_3_10/INDEX.md](3_2_to_3_10/INDEX.md)

## Notes
- `QueueManagerIntegration` already has full IPC, job lifecycle, cleanup
- Do NOT delete old `QueueManager` yet — commands still use it until Step 4
- `in_memory=True` default is fine for dev; configure path for prod
- **Use `cst_create_file` for all `.py` files** (not `create_text_file`)
