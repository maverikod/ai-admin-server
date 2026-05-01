# 1.8: Catalogue QueueAction / QueueFilter Enum Usages

## Atomic Steps
1. Run `get_code_entity_info(entity_type="class", entity_name="QueueAction")` — list all values
2. Run `get_code_entity_info(entity_type="class", entity_name="QueueFilter")` — list all values
3. Search for each value usage in commands and `QueueClient`
4. Determine which actions map to `queuemgr` equivalents: start/stop/delete
5. Flag any actions without a `queuemgr` equivalent (need custom impl or drop)
6. Save mapping to `docs/plans/step_1/queue_action_filter_map.md`
