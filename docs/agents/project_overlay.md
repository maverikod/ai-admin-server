<!--
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
-->

# Project overlay — `vast_srv` / AI Admin (this repository)

Repository-specific paths, behavior, and restrictions. Universal layout: [`PROJECT_RULES.md`](../PROJECT_RULES.md) §3 (`LAYOUT-*`).

## Functional context

- **Role:** Python **AI Admin** server — FastAPI / JSON-RPC style command surface over `mcp-proxy-adapter`, with Docker, Kubernetes, Vast.ai, FTP, Git/GitHub, SSL/mTLS, queues, and related adapters.
- **Installable package:** [`ai_admin/`](../../ai_admin/) — application factory, commands, security adapters, task queue, settings.
- **Duplicate / legacy tree:** root [`commands/`](../../commands/) may mirror or shadow packaged commands during migrations; prefer changes under `ai_admin/` unless a task explicitly targets the root tree.
- **Tests:** primary suite under [`tests/`](../../tests/) (pytest). **Non-pytest** harnesses and ops-style checks → [`scripts/`](../../scripts/) per **LAYOUT-07**.
- **Runtime configuration:** primary checked-in samples under [`config/`](../../config/) (`config.example.json`, `auth.example.json`); universal template also expects a root [`configs/`](../../configs/) directory for non-secret samples (see **LAYOUT-04**).
- **Planning stack (when used):** under `docs/tech_spec/` per hierarchy agents (`tech_spec.md`, `steps/`, `branches/...`).

## Directories and files beyond the universal skeleton

| Path | Note |
|------|------|
| `config/` | App JSON config and auth examples (this repo’s main config location alongside template `configs/`). |
| `certificates/` | TLS material for dev/proxy; do not commit real production private keys. |
| `code_analysis/` | Generated indices when `code_mapper` is run (`USE_CODE_MAP` = yes in [`PROJECT_RULES.md`](../PROJECT_RULES.md) §7). |
| `code_analysis_reports/` | Alternate/older mapper output — treat as generated. |
| `docs/plans/`, `docs/refactoring/` | Large plans and step docs. |
| `docs/ai_reports/` | Working AI reports per universal **LAYOUT-06**. |
| `logs/` | Runtime logs (gitignored patterns as applicable); no secrets in tracked logs. |
| `scripts/` | Ops, maintenance, and **non-pytest** runners per **LAYOUT-07**. |
| Root `*.py` | Ad-hoc migration / fix scripts — not part of the `ai_admin` package API. |

## Project-specific restrictions

- **Secrets:** Never add real credentials, API keys, or production cert private keys to the repo.
- **Scope:** Changes stay within **this** repository unless the user explicitly allows other paths.
- **Generated artifacts:** Do not hand-edit `code_analysis/*.yaml` — regenerate via `code_mapper` when required by project rules.

## Filled profile pointer

Concrete profile values for this repo: [`PROJECT_RULES.md`](../PROJECT_RULES.md) **§7**.
