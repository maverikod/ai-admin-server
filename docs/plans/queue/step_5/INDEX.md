# Step 5: Tests — Cover New Job Classes and Migrated Commands

## Goal
Ensure the new queue layer is fully tested BEFORE deleting the legacy layer.
All tests must pass before proceeding to Step 6.

## Tactical Steps

| # | Task | Detail |
|---|------|---------|
| 5.1 | Unit tests for `DockerJob`: mock subprocess, verify params mapping | [TASKS.md](TASKS.md#51-unit-tests-dockerjob) |
| 5.2 | Unit tests for `GitJob` / `GitHubJob` | [TASKS.md](TASKS.md#52-unit-tests-gitjob--githubjob) |
| 5.3 | Unit tests for `K8sJob`: all 5 operation types | [TASKS.md](TASKS.md#53-unit-tests-k8sjob) |
| 5.4 | Unit tests for `VastJob`: create/destroy/search/list | [TASKS.md](TASKS.md#54-unit-tests-vastjob) |
| 5.5 | Unit tests for `FtpJob`, `OllamaJob`, `SslJob`, `SystemJob` | [TASKS.md](TASKS.md#55-unit-tests-remaining-jobs) |
| 5.6 | Integration test: `QueueManagerIntegration` lifecycle | [TASKS.md](TASKS.md#56-integration-test-queue-lifecycle) |
| 5.7 | Integration test: command → job → queue → result | [TASKS.md](TASKS.md#57-integration-test-command--queue) |
| 5.8 | Test `max_queue_size` eviction | [TASKS.md](TASKS.md#58-test-queue-size-limits) |
| 5.9 | Test TTL expiry of completed jobs | [TASKS.md](TASKS.md#59-test-completed-job-retention-ttl) |
| 5.10 | Run `comprehensive_analysis` on `vast_srv` — zero critical issues | [TASKS.md](TASKS.md#510-final-comprehensiveanalysis) |

## Detailed Tasks
See: [TASKS.md](TASKS.md)

## Coverage Targets
- All Job classes: `run()`, error handling, progress reporting
- All migrated commands: happy path + error path
- Queue lifecycle: pending → running → completed / failed / cancelled

## Gate to Step 6
- All unit tests pass
- All integration tests pass
- `comprehensive_analysis` shows zero stubs in production code
- Only then proceed to delete legacy layer (Step 6)
