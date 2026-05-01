# Executor map (Step 1.3) — repo truth vs plan checklist

The plan lists 12 classes including GitExecutor, GitHubExecutor, VastExecutor, SSLExecutor, SystemExecutor. **Those do not exist as standalone classes.** Work is grouped under **`MiscExecutor`**.

## Classes found (representative canonical paths)

| Logical role | Class name | Primary file (one of many duplicates) |
|--------------|------------|--------------------------------------|
| Docker | `DockerExecutor` | queue/docker_executor.py, queue_impl/docker_executor.py, monolith queue.py / queue_impl.py / task_queue.py |
| Kubernetes | `K8sExecutor` | queue/k8s_executor.py |
| Kind | `KindExecutor` | queue/kind_executor.py |
| K8s+Kind combined | `K8sKindExecutor` | queue_impl/k8s_executor.py, nested task_queue/k8s_* |
| FTP upper | `FTPExecutor` | queue_impl/ftp_executor.py |
| FTP lower | `FtpExecutor` | queue/ftp_executor.py |
| Ollama | `OllamaExecutor` | queue/ollama_executor.py (+ nested copies) |
| Catch-all | `MiscExecutor` | task_queue/misc_executor.py |

## TaskQueue façade warning
`TaskQueue.__init__` only sets `TaskQueueCore`; methods reference `self.dockerExecutor` / `self.fTPExecutor` / etc. **Those attributes are never assigned on `TaskQueue`.** Verify runtime path through `TaskQueueCore._execute_task` vs dead façade methods (needs coder follow-up).
