# 3.1: Add queuemgr to Dependencies

## Atomic Steps
1. Run `project_pip_list` on `vast_srv` — check if `queuemgr` is already installed
2. If not: run `project_pip_install(packages=["queuemgr"])` 
3. Run `project_pip_check(packages=["queuemgr"])` to verify installation
4. Add `queuemgr` to `requirements.txt` with pinned version
5. Verify import: `from queuemgr.jobs.base_core import QueueJobBase` works in project venv
