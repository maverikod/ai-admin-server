# 2.9: Implement SslJob

## Atomic Steps
1. Read `SSLExecutor` body
2. Create `ai_admin/jobs/ssl_job.py` with `class SslJob(QueueJobBase)`
3. Implement `run()`: dispatch by `params["operation_type"]` → generate/view/verify/revoke
4. Port cert_type handling: self_signed, ca_signed, server, client
5. Port common_name, ssl_config, user_roles params
6. Add progress: CSR generation, signing, file write
7. Docstring, type hints, lint + typecheck
