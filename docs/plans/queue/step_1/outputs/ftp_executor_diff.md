# FTPExecutor vs FtpExecutor (Step 1.6)

| | FTPExecutor | FtpExecutor |
|---|-------------|-------------|
| Path | task_queue/queue_impl/ftp_executor.py | task_queue/queue/ftp_executor.py |
| Methods | `_create_ftp_connection`, `_execute_ftp_upload_task`, etc. | same set |

Merge strategy (draft): pick **one file** as source of truth for `FtpJob`, fold diff if drift-only.
