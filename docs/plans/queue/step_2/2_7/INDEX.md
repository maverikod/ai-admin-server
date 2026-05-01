# 2.7: Implement FtpJob (Merge FTPExecutor + FtpExecutor)

## Atomic Steps
1. Read both `FTPExecutor` and `FtpExecutor` bodies (from 1.6 diff)
2. Create `ai_admin/jobs/ftp_job.py` with `class FtpJob(QueueJobBase)`
3. Implement `run()`: dispatch by `params["operation"]` → upload/download/list/delete
4. Take unique logic from each executor, resolve conflicts (keep more complete version)
5. Port FTP connection params: host, port, user, password, ssl_config
6. Add progress reporting for file transfer (bytes sent/total)
7. Docstring, type hints, lint + typecheck
8. Confirm: neither old class is needed after this step
