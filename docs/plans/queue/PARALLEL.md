# Queue Refactoring — Parallelization Map

## Legend
```
[→] = depends on (must complete first)
[||] = can run in parallel
[!] = blocking gate (must pass before anything continues)
```

---

## Top-level dependency graph

```
Step 1 (Audit)
    │
    ├────────────────────────────────────────────────┐
    │                                               │
 Step 2 (Job classes)                          Step 3 (Wire integration)
    │                                               │
    └────────────────────────────────────────────────┘
                                    │
                               Step 4 (Migrate commands)
                                    │
                              [!] Step 5 (Tests)
                                    │
                              Step 6 (Delete legacy)
                                    │
                              Step 7 (Final cleanup)
```

---

## Step 1: Audit (sequential inside, ~10 tasks)

Все подшаги Step 1 **независимы** и могут идти параллельно:

```
[||] 1.1 find_usages(QueueManager)
[||] 1.2 find_usages(QueueClient)
[||] 1.3 list Executors + list_class_methods ×12
[||] 1.5 diff queue_manager.py vs impl
[||] 1.6 diff FTPExecutor vs FtpExecutor
[||] 1.7 catalogue TaskStatus
[||] 1.8 catalogue QueueAction/QueueFilter
[||] 1.9 analyse QueueDaemon
         │
         └── 1.4 map add_*_task → Executor  [→ 1.1 + 1.3]
                  │
                  └── 1.10 dependency_matrix  [→ 1.1..1.9 ALL]
```

**Batch strategy:** run 1.1, 1.2, 1.3, 1.5, 1.6, 1.7, 1.8, 1.9 in parallel.
Then 1.4 (needs 1.1 + 1.3). Then 1.10 (needs everything).

---

## Step 2: Job classes (all parallel after 2.1)

```
2.1 Create ai_admin/jobs/ package   [! must finish first]
         │
         ├── [||] 2.2 DockerJob
         ├── [||] 2.3 GitJob
         ├── [||] 2.4 GitHubJob
         ├── [||] 2.5 K8sJob        [→ 1.3 K8sExecutor read]
         ├── [||] 2.6 VastJob
         ├── [||] 2.7 FtpJob        [→ 1.6 ftp diff]
         ├── [||] 2.8 OllamaJob
         ├── [||] 2.9 SslJob
         └── [||] 2.10 SystemJob
```

Все 9 Job классов полностью независимы друг от друга.
**Один агент на класс = 9 агентов параллельно.**

---

## Step 3: Wire integration (parallel with Step 2)

Step 3 **не зависит** от Step 2. Запускается сразу после Step 1.

```
3.1 Verify queuemgr installed
         │
         ├── [||] 3.2–3.3 Create integration.py
         └── [||] 3.6–3.8 Configure settings
                  │
                  ├── 3.4–3.5 Wire startup/shutdown  [→ 3.2–3.3]
                  │
                  └── 3.9 Add health endpoint       [→ 3.4–3.5]
                           │
                           └── 3.10 Smoke test         [→ 3.4 + 2.10 SystemJob]
```

---

## Step 4: Migrate commands (parallel by domain, needs 2+3)

Все домены независимы. Можно запускать параллельно после готовности Job класса.

```
Step 2 + Step 3 done
         │
         ├── [||] 4.1 Docker cmds    [→ DockerJob ready]
         ├── [||] 4.2 Git cmds        [→ GitJob ready]
         ├── [||] 4.3 GitHub cmds     [→ GitHubJob ready]
         ├── [||] 4.4 K8s cmds        [→ K8sJob ready]
         ├── [||] 4.5 Vast.ai cmds    [→ VastJob ready]
         ├── [||] 4.6 FTP cmds        [→ FtpJob ready]
         ├── [||] 4.7 Ollama cmds     [→ OllamaJob ready]
         ├── [||] 4.8 SSL cmds        [→ SslJob ready]
         ├── [||] 4.9 System cmds     [→ SystemJob ready]
         └── [||] 4.10 Queue mgmt cmds [→ integration.py ready]
```

**Streaming migration:** агент 2.2 (DockerJob) → сразу агент 4.1 (Docker cmds).
Не нужно ждать всех Job классов — каждый домен мигрирует сразу после своего Job.

---

## Step 5: Tests (parallel by domain)

```
Step 4 done (all domains)
         │
         ├── [||] 5.1 Unit: DockerJob
         ├── [||] 5.2 Unit: Git/GitHubJob
         ├── [||] 5.3 Unit: K8sJob
         ├── [||] 5.4 Unit: VastJob
         ├── [||] 5.5 Unit: FTP/Ollama/SSL/SystemJob
         ├── [||] 5.6 Integration: lifecycle
         ├── [||] 5.7 Integration: command→queue
         ├── [||] 5.8 Limits test
         ├── [||] 5.9 TTL cleanup test
         │
         └── 5.10 comprehensive_analysis  [→ ALL above pass]
                  │
                 [!] GATE — must pass before Step 6
```

---

## Step 6: Delete legacy (sequential by safety)

Удаление нельзя параллелить — каждый шаг проверяет результат предыдущего.

```
6.1 verify QueueManager = 0
6.2 verify QueueClient = 0
6.3 verify Executors = 0
    │
6.4 delete queue_manager.py duplicate
6.5 delete ai_admin/task_queue/
6.6 delete ai_admin/queue_management/
6.7 delete QueueDaemon
6.8 clean __init__.py
6.9 run pytest
6.10 deduplicate validate_log_path
```

---

## Step 7: Final cleanup (parallel within)

```
7.1–7.2 format_code  [||] on all files simultaneously
7.3–7.4 lint_code    [||] on all files simultaneously  [→ 7.1–7.2]
7.5–7.6 type_check   [||] on all files simultaneously  [→ 7.3–7.4]
    │
7.7 comprehensive_analysis  [→ 7.5–7.6]
    │
7.8 hard-delete trash       [→ 7.7 pass]
7.9 write report            [→ 7.8]
```

---

## Optimal timeline (with N agents)

```
Time →

T0   [Agent A] Step 1: audit (1.1–1.9 parallel, 1.10 last)
     [Agent B] (idle, waiting for 1.10)

T1   [Agent A] Step 2.1: create jobs package
     [Agent B] Step 3.1: verify queuemgr

T2   [Agent A1] 2.2 DockerJob
     [Agent A2] 2.3 GitJob
     [Agent A3] 2.4 GitHubJob
     [Agent A4] 2.5 K8sJob
     [Agent A5] 2.6 VastJob       ← all parallel
     [Agent A6] 2.7 FtpJob
     [Agent A7] 2.8 OllamaJob
     [Agent A8] 2.9 SslJob
     [Agent A9] 2.10 SystemJob
     [Agent B]  3.2–3.5: integration.py + wire server

T3   [as each Job finishes]
     [Agent A1] 4.1 Docker cmds (immediately after DockerJob)
     [Agent A2] 4.2 Git cmds    (immediately after GitJob)
     ...
     [Agent B]  3.9–3.10: health endpoint + smoke test

T4   [ALL Step 4 done]
     [All agents] Step 5: unit tests parallel

T5   [5.10 comprehensive_analysis passes] ← GATE
     [Agent A] Step 6: sequential deletion

T6   [Step 6 done]
     [All agents] Step 7: format+lint+typecheck parallel
     [Final] 7.7 analysis → 7.8 hard-delete → 7.9 report
```

---

## Critical path (minimum sequential chain)

```
1.10 → 2.1 → any_one_Job → 4.x → 5.10 → 6.9 → 7.7 → 7.8
```

Всё остальное — параллельно вокруг этой цепочки.

---

## Constraints

| Constraint | Reason |
|---|---|
| 1.10 blocks 2+3 | Dependency matrix not ready yet |
| 2.1 blocks 2.2–2.10 | Package must exist before adding modules |
| 3.3 blocks 3.4 | integration.py must exist before wiring |
| 3.10 needs SystemJob | Smoke test uses SystemJob |
| 5.10 gate blocks 6 | Must not delete until tests pass |
| 6.x sequential | Each verify step gates the next delete |
| 7.8 needs 7.7 | Hard-delete only after analysis passes |
| 2.x can start as soon as 1.10 done | Jobs don’t depend on each other |
| 4.x can stream: 4.1 starts when 2.2 done | Don’t wait for all Jobs |
