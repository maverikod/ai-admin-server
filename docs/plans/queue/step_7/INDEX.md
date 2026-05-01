# Step 7: Final Cleanup

## Goal
Polish code quality across all modified files, run final comprehensive_analysis,
and permanently hard-delete the legacy code from trash.

## Tactical Steps

| # | Task | Detail |
|---|------|---------|
| 7.1 | `format_code` on all files in `ai_admin/jobs/` | [TASKS.md](TASKS.md#71-format-all-job-files) |
| 7.2 | `format_code` on all files in `ai_admin/commands/` that were migrated | [TASKS.md](TASKS.md#72-format-migrated-commands) |
| 7.3 | `lint_code` on `ai_admin/jobs/` — expect 0 errors | [TASKS.md](TASKS.md#73-lint-job-files) |
| 7.4 | `lint_code` on `ai_admin/commands/` — expect 0 errors | [TASKS.md](TASKS.md#74-lint-migrated-commands) |
| 7.5 | `type_check_code` on `ai_admin/jobs/` — fix `arg-type` / `override` errors | [TASKS.md](TASKS.md#75-typecheck-job-files) |
| 7.6 | `type_check_code` on `ai_admin/commands/` — fix errors | [TASKS.md](TASKS.md#76-typecheck-migrated-commands) |
| 7.7 | Run final `comprehensive_analysis` on whole `vast_srv` | [TASKS.md](TASKS.md#77-final-comprehensiveanalysis) |
| 7.8 | Hard-delete trash (permanent removal of legacy code) | [TASKS.md](TASKS.md#78-hard-delete-trash) |
| 7.9 | Write `REFACTORING_COMPLETE.md` | [TASKS.md](TASKS.md#79-write-completion-report) |

## Detailed Tasks
See: [TASKS.md](TASKS.md)

## Gate to hard-delete (7.8)
- comprehensive_analysis total_stubs = 0 in production
- flake8 errors in ai_admin/ = 0
- All tests from Step 5 still passing
- Only after all checks pass: `cleanup_deleted_files(hard_delete=True)`
