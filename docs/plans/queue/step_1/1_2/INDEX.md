# 1.2: List All Files Importing QueueClient

## Atomic Steps
1. Run `find_usages(target_name="QueueClient", target_type="class")` on `vast_srv`
2. Filter by `usage_type="import"` and `usage_type="instantiation"`
3. List unique importing files and call sites
4. Note: `QueueClient` wraps `QueueManager` singleton — it will be deleted entirely
5. Save to `docs/plans/step_1/queueclient_importers.md`
