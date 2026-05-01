# 2.5: Implement K8sJob

## Atomic Steps
1. Read `K8sExecutor` and `K8sKindExecutor` and `KindExecutor` bodies
2. Create `ai_admin/jobs/k8s_job.py` with `class K8sJob(QueueJobBase)`
3. Implement `run()`: dispatch by `params["operation"]` → deploy/pod/cluster/cert/mtls
4. Port kubectl/kind subprocess calls from all three Executors
5. Merge Kind-specific logic into same dispatch (params["cluster_type"] = "kind")
6. Port namespace, image, port, replicas param handling
7. Add progress: cluster contact, resource creation, readiness check
8. Docstring, type hints, lint + typecheck
