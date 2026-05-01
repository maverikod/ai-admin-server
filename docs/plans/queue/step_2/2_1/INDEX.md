# 2.1: Create ai_admin/jobs/ Package

## Atomic Steps
1. Create `ai_admin/jobs/__init__.py` with exports of all Job classes
2. Create `ai_admin/jobs/base.py` — optional thin mixin if all jobs share common validation
3. Verify `queuemgr` is importable: `from queuemgr.jobs.base_core import QueueJobBase`
4. Add `ai_admin/jobs/` to project structure documentation
5. Run `lint_code` on new package to verify clean
