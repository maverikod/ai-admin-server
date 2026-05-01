# 1.6: Identify FTPExecutor vs FtpExecutor Diff

## Atomic Steps
1. Run `list_class_methods(class_name="FTPExecutor")` and `list_class_methods(class_name="FtpExecutor")`
2. Compare method sets: what is unique to each, what is shared
3. Read both class bodies via `universal_file_read`
4. Identify which implements the real FTP logic and which is a stub/wrapper
5. Document the merge plan: which methods survive into `FtpJob`
6. Save to `docs/plans/step_1/ftp_executor_diff.md`
