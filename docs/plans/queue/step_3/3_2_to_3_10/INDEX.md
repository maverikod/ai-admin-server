# 3.2–3.10: Integration Wiring Atomic Steps

## 3.2: Create ai_admin/queue/integration.py
1. Create `ai_admin/queue/__init__.py`
2. Create `ai_admin/queue/integration.py` importing `QueueManagerIntegration` from `mcp_proxy_adapter`
3. Wrap it with project-specific defaults (max_concurrent=4, in_memory=True)
4. Lint + typecheck

## 3.3: Add get_queue_integration() accessor
1. Add module-level `_integration: Optional[QueueManagerIntegration] = None`
2. Add `get_queue_integration() -> QueueManagerIntegration` that raises if not started
3. Add `set_queue_integration(i)` for wiring in startup
4. Export both from `ai_admin/queue/__init__.py`

## 3.4: Wire startup into AIAdminServer
1. Read `AIAdminServer` body via `universal_file_read`
2. Locate lifespan/startup handler
3. Add `integration = QueueManagerIntegration(...); await integration.start(); set_queue_integration(integration)`
4. Preview via `cst_modify_tree` before applying

## 3.5: Wire shutdown into AIAdminServer
1. Locate shutdown/lifespan exit handler in `AIAdminServer`
2. Add `await get_queue_integration().stop()`
3. Handle case where integration not started (graceful no-op)
4. Apply via CST tools

## 3.6–3.8: Configure limits and settings
1. Add `queue` section to `AIAdminSettingsManager` with fields: `max_concurrent`, `max_queue_size`, `per_job_type_limits`, `retention_seconds`
2. Pass settings values into `QueueManagerIntegration.__init__`
3. Add validation for `max_concurrent >= 1`

## 3.9: Add health endpoint
1. Add `/queue/health` route to `AIAdminServer`
2. Handler calls `get_queue_integration().get_queue_health()`
3. Returns JSON with running/pending counts

## 3.10: Smoke test
1. Run server in dev mode
2. Submit a `SystemJob` via direct API call
3. Poll `/queue/health` — verify job appears as running then completed
4. Verify no errors in logs
