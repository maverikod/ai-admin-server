# Step 7 Atomic Steps: Tests

## 7.1–7.5: Unit Tests Per Job Class

### Pattern for each Job:
1. Create `tests/queue/test_{domain}_job.py`
2. Mock the underlying subprocess/API call (patch at the call site)
3. Instantiate job with params dict matching the command signature
4. Call `job.run()` synchronously via `asyncio.run()`
5. Assert: result dict contains expected keys, progress was reported, no exception
6. Test error path: mock raises exception, assert job status is `failed`

### Files to create:
- `tests/queue/test_docker_job.py` — build/push/pull ops
- `tests/queue/test_git_job.py` — clone/push/pull + ssl_config
- `tests/queue/test_github_job.py` — repo create with token auth
- `tests/queue/test_k8s_job.py` — 5 op types
- `tests/queue/test_vast_job.py` — 4 op types
- `tests/queue/test_ftp_job.py` — merged operations
- `tests/queue/test_ollama_job.py` — pull + run with streaming
- `tests/queue/test_ssl_job.py` — generate/view/verify/revoke
- `tests/queue/test_system_job.py` — system_monitor with flags

## 7.6: Integration Test — Queue Lifecycle
1. Create `tests/queue/test_integration_lifecycle.py`
2. Instantiate `QueueManagerIntegration(in_memory=True, max_concurrent_jobs=2)`
3. `await integration.start()`
4. `await integration.add_job(SystemJob, "test_job_1", {...})`
5. Poll `get_job_status("test_job_1")` until completed
6. Assert status=completed, result is not empty
7. `await integration.stop()`
8. Assert no running processes remain

## 7.7: Integration Test — Command → Queue → Result
1. Create `tests/queue/test_command_integration.py`
2. For each domain: instantiate command, mock actual executor (subprocess), run command
3. Assert: `add_job` was called with correct Job class and params
4. Assert: returned job_id is present in queue

## 7.8–7.9: Limit and Cleanup Tests
1. `test_queue_size_limit`: add N+1 jobs with `max_queue_size=N`, verify oldest evicted
2. `test_per_job_type_limit`: add 3 DockerJobs with `per_job_type_limits={"DockerJob": 2}`, verify eviction
3. `test_completed_job_retention`: complete a job, advance clock past retention, trigger cleanup, verify gone

## 7.10: Final comprehensive_analysis
1. Run `comprehensive_analysis` on `vast_srv` project
2. Target: total_stubs=0 in production code, total_long_files for `ai_admin/` = 0
3. After passing: hard-delete trash (`cleanup_deleted_files(hard_delete=True)`)
