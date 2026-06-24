# Queue migration plan — execution status

Last updated: 2026-05-01 (orchestrator → coder → tester chain).

## Completed (in repo)

| Step | Status | Notes |
|------|--------|--------|
| **1** Audit | **Done** | Artifacts under `docs/plans/queue/step_1/outputs/` including `dependency_matrix.md`, `task_executor_map.md`. |
| **2.1** | **Done** | Package `ai_admin/jobs/`. |
| **2.2–2.10** | **Partial** | All jobs use `execute()` per `queuemgr`. **DockerJob** runs push/pull/build via `DockerExecutor` + `Task` bridge (`task_from_params.py`). Other jobs return `set_result({status: "deferred", ...})` until executor bridges exist. |
| **3.2–3.3** | **Done** | `ai_admin/queue/__init__.py`, `integration.py` with `get_queue_integration` / `set_queue_integration`, async `start_queue_integration` / `stop_queue_integration` wrapping `QueueManagerIntegration` from `mcp_proxy_adapter`. |
| **3.4–3.5** | **Skipped** | No in-repo FastAPI lifespan hook found at wiring time; comment in `integration.py`. |
| **3.6–3.10** | **Not done** | Settings keys, `/queue/health`, smoke test with `SystemJob` still open. |

## Not done (plan scope)

| Step | Reason |
|------|--------|
| **4** Migrate commands | Needs stable `add_job` contract + per-domain command edits; large surface (`ai_admin/commands/*`, mirrors under `commands/`). |
| **5** Tests + gate 5.10 | `tests/test_queue_integration.py` currently fails on `get_settings_manager()` / harness; collection issues for some integration tests. |
| **6** Delete legacy | Blocked until Step 5 green; `QueueDaemon` absent — see `step_1/outputs/queue_daemon_analysis.md`. |
| **7** Final cleanup | After Step 6. |

## Known technical blockers

1. **Deferred jobs** — Git/GitHub/K8s/Vast/FTP/Ollama/SSL/System paths do not yet delegate to legacy executors; `MiscExecutor._execute_generic_task` does not cover many `TaskType` values (documented in dependency matrix).
2. **TaskQueue / TaskQueueCore** — Structural mismatch between façade and core (audit); full fix is outside the minimal integration slice.
3. **CI / tests** — Queue-related pytest may fail until `settings_manager/helpers.py` init and missing command imports in the test tree are resolved.
4. **Lifespan** — `start_queue_integration` / `stop_queue_integration` must be called from server startup when a hook exists (Step 3.4–3.5).

## Next orchestrator → coder → tester cycles (suggested order)

1. Implement `execute()` for remaining jobs by reusing the `Task` + executor pattern (FTP, Ollama, …) where `_execute_task` already dispatches.
2. Step **3.6–3.9**: settings section + `/queue/health` on the app that hosts MCP routes.
3. Fix **settings_manager** / test harness so `pytest … queue` is meaningful.
4. Step **4** domain by domain: replace `QueueManager.add_*` with `get_queue_integration().add_job(...)` + job params mapping.
5. Step **5–7** per `PARALLEL.md`.
