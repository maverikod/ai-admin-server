# 2.10: Implement SystemJob

## Atomic Steps
1. Read `SystemExecutor` body
2. Create `ai_admin/jobs/system_job.py` with `class SystemJob(QueueJobBase)`
3. Implement `run()`: dispatch by `params["operation_type"]` → system_monitor
4. Port psutil/nvidia-smi calls for GPU, temperature, processes
5. Port `include_gpu`, `include_temperature`, `include_processes` param flags
6. Add progress: data collection phases
7. Update `ai_admin/jobs/__init__.py` to export all 9 Job classes
8. Docstring, type hints, lint + typecheck on all jobs
