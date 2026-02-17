# agent/ — Intel Brief Pipeline

Automated SLED procurement intelligence pipeline. Takes a webhook (prospect domain + product info), queries Starbridge's 296K+ buyer database, generates a branded intel report via Claude LLM sub-agents, and publishes to Notion — all in under 60 seconds.

**Status**: Built and tested (15 successful runs). Core pipeline is complete. Remaining: production webhook integration, Slack dispatch, monitoring.

## Architecture Overview

```
HTTP POST / CLI
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  server.py — FastAPI (POST /api/run → background thread)     │
│  or: run_vmock.py / direct call to run_pipeline(webhook)     │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  pipeline.py — Orchestrator (run_pipeline)                  │
│                                                             │
│  Phase I-II:   s0 → s1           (parse, validate, DB)     │
│  Phase III:    s2                 (LLM: search strategy)    │
│  Phase IV:     s3a ║ s3b ║ s3c   (parallel API discovery)  │
│  Phase V:      s4 → s5           (rank, persist)           │
│  Phase VI:     s8 ║ s6→s9 ║ s7→s10 ║ s11 ║ s12            │
│                (parallel enrich + generate)                  │
│  Phase VII:    s13 → s14 → s15 → s16                       │
│                (assemble, validate, publish, respond)        │
└─────────┬──────────┬──────────┬────────────────────────────┘
          │          │          │
          ▼          ▼          ▼
      llm.py     tools.py    db.py
      (Claude     (Starbridge (SQLite:
       CLI)        REST API,   runs,
                   Datagen     discoveries,
                   SDK)        contacts,
                               audit_log)
```

## File Inventory

| File | Lines | Purpose |
|---|---|---|
| `config.py` | 279 | All tunables: timeouts, page sizes, LLM model, thread pools, CTA copy, state codes |
| `db.py` | 372 | SQLite: 4 tables, CRUD operations, `StepTimer` context manager, audit logging |
| `llm.py` | 376 | 5 LLM sub-agents + Q&A function. Backend: `claude -p` CLI via subprocess |
| `pipeline.py` | 1186 | 19-step orchestrator with 7 phases, parallel execution, state management |
| `tools.py` | 199 | Starbridge custom tools (REST) + Notion MCP (Datagen SDK) |
| `server.py` | 154 | FastAPI server: serves pipeline-explorer.html, runs pipeline via HTTP, polls status |
| `run_vmock.py` | 85 | End-to-end test runner (real Starbridge API + real LLM calls) |

**Total: 2,651 lines of Python**

## The 19 Steps

### Phase I — SOURCE

| Step | Function | Type | What It Does |
|---|---|---|---|
| **s0** | `s0_parse_webhook` | Python | Extract & validate 7 webhook fields (company, domain, product, campaign, prospect) |

### Phase II — INPUT

| Step | Function | Type | What It Does |
|---|---|---|---|
| **s1** | `s1_validate_and_load` | Python + SQLite | Validate domain format, init DB, create run stub (run_id), load prior runs + cached discoveries |

### Phase III — ANALYZE

| Step | Function | Type | What It Does |
|---|---|---|---|
| **s2** | `s2_search_strategy` | **LLM** (`llm.search_strategy`) | Analyze product → SLED segments, primary/alternate/meeting/rfp keywords, buyer types, opportunity types, geo hints, ideal buyer profile |

### Phase IV — DISCOVER (parallel)

| Step | Function | Type | What It Does |
|---|---|---|---|
| **s3a** | `s3a_primary_search` | API (`tools.opportunity_search`) | Search opportunities with primary keywords + LLM-chosen opp types |
| **s3b** | `s3b_alternate_search` | API (`tools.opportunity_search`) | Search opportunities with alternate keywords |
| **s3c** | `s3c_buyer_search` | API (`tools.buyer_search`) | Search buyers by type + geographic hints (state codes) |

All three run in parallel via `ThreadPoolExecutor(max_workers=3)`.

### Phase V — SELECT

| Step | Function | Type | What It Does |
|---|---|---|---|
| **s4** | `s4_rank_and_select` | Python (deterministic) | Merge, dedupe, score buyers (type match 25%, signal count 20%, recency 20%, urgency 15%, dollar 10%, keyword 10%). Select featured + up to 4 secondary |
| **s5** | `s5_persist_discovery` | SQLite | Backfill discovery data into the run stub, insert scored buyers into discoveries table |

### Phase VI — ENRICH & GENERATE (5 parallel branches)

| Branch | Steps | Type | What It Does |
|---|---|---|---|
| **a** | s8 | Template | Executive summary (signal count, buyer count, featured buyer) |
| **b** | s6 → s9 | API → **LLM** | Fetch profile + contacts + AI chat for featured buyer, then `llm.featured_section` generates deep-dive markdown |
| **c** | s7 → s10 | API → **LLM** | Fetch profile + contacts for each secondary buyer, then `llm.secondary_cards` generates compact cards |
| **d** | s11 | Template | CTA section (Starbridge marketing copy) |
| **e** | s12 | Template | Footer with data source attribution |

s6 internally parallelizes 3 sub-calls: `buyer_profile` + `buyer_contacts` + `buyer_chat` (async polling).

### Phase VII — ASSEMBLE & VALIDATE

| Step | Function | Type | What It Does |
|---|---|---|---|
| **s13** | `s13_assemble` | Python | Concatenate 5 sections into final markdown report |
| **s14** | `s14_validate` | Python + **LLM** | 7 deterministic checks + 1 advisory LLM fact-check against source data |
| **s15** | `s15_publish_notion` | API (Datagen SDK) | Create Notion page under parent via `mcp_Notion_notion_create_pages` |
| **s16** | `s16_save_and_respond` | SQLite | Update run to 'completed', save all sections + contacts, build response JSON |

## LLM Sub-Agents (`llm.py`)

All LLM calls go through the `claude` CLI in print mode (`claude -p`), authenticated via `CLAUDE_CODE_OAUTH_TOKEN` from `.env`.

| Sub-Agent | Pipeline Step | System Prompt Focus | Output |
|---|---|---|---|
| `search_strategy()` | s2 | SLED procurement intelligence analyst | JSON: keywords (primary, alternate, meeting, rfp), buyer_types, opportunity_types, geo_hints, ideal_buyer_profile |
| `buyer_profile_summary()` | (unused) | Buyer profile synthesis into narrative summary | Markdown: structured overview (attributes, mission, tech context, relevance) |
| `featured_section()` | s9 | Featured buyer report writer (data-only, no hallucination) | Markdown: snapshot card, why-this-buyer, key contact, signals |
| `secondary_cards()` | s10 | Compact card generator | Markdown: 3-4 line card per secondary buyer |
| `fact_check()` | s14 | Fact-checker comparing report vs source data | Tuple: (passed: bool, detail: str) |
| `ask()` | standalone | General Q&A for Starbridge pipeline | Free-text answer |

`buyer_profile_summary()` is defined but not currently called in the pipeline. It's available for future integration into the featured buyer enrichment phase (e.g., as a pre-processing step before `featured_section()`).

**Default model**: `anthropic.claude-opus-4-6-v1` (override via `LLM_MODEL` env var)

**CLI invocation**: `claude -p --model {LLM_MODEL} --max-turns {LLM_MAX_TURNS}`

Key detail: The `CLAUDECODE` env var is unset in the subprocess (`CLAUDECODE=""`) to allow nested invocation from within Claude Code sessions.

### Q&A Sub-Agent

```bash
# From CLI
python -m agent.llm "What buyer types does Starbridge track?"
python -m agent.llm "Explain the scoring algorithm" --context "$(cat agent/pipeline.py)"

# From Python
from agent.llm import ask
answer = ask("What buyer types does Starbridge track?")
```

## External Dependencies

| Service | Used By | Auth | Calls Per Run |
|---|---|---|---|
| **Starbridge API** (via Datagen REST) | `tools.py` | `DATAGEN_API_KEY` | ~10-15 (search + profiles + contacts) |
| **Starbridge buyer_chat** (async) | `tools.py` | `DATAGEN_API_KEY` | 1 (async POST + polling) |
| **Notion** (via Datagen MCP SDK) | `tools.py` | `DATAGEN_API_KEY` | 1 (create page) |
| **Claude CLI** (`anthropic.claude-opus-4-6-v1`) | `llm.py` | `CLAUDE_CODE_OAUTH_TOKEN` | 4 (s2 + s9 + s10 + s14) |

### Starbridge Custom Tool UUIDs

| Tool | UUID | Endpoint Type |
|---|---|---|
| `opportunity_search` | `c15b3524-cd08-4f7a-ae78-d73f6a6c2bad` | Sync REST |
| `buyer_search` | `e69f8d37-6601-4e73-a517-c8ea434b877b` | Sync REST |
| `buyer_profile` | `74345947-2f94-4eed-97a3-d10b2b2e3ad9` | Sync REST |
| `buyer_contacts` | `b81036af-1c0f-4b9a-a03b-4c301927518f` | Sync REST |
| `buyer_chat` | `043dc240-4517-4185-9dbb-e24ae0abf04d` | **Async** (POST → poll) |

## SQLite Schema (`data/pipeline.db`)

### `runs` — One row per pipeline execution

Core fields: `target_domain`, `target_company`, `prospect_email`, `campaign_id`, `product_description`

Discovery fields: `search_strategy` (JSON), `discovery_signals_a` (JSON), `discovery_signals_b` (JSON), `discovery_buyers` (JSON), `featured_buyer_id`, `featured_buyer_name`, `secondary_buyers` (JSON)

Enrichment fields: `feat_profile` (JSON), `feat_contacts` (JSON), `feat_opportunities` (JSON), `feat_ai_context` (text), `feat_ai_context_available` (bool), `sec_profiles` (JSON), `sec_contacts` (JSON)

Output fields: `section_exec_summary`, `section_featured`, `section_secondary`, `section_cta`, `section_footer`, `report_markdown`, `notion_url`

Status: `status` ('processing' | 'completed' | 'failed'), `created_at`, `completed_at`

### `discoveries` — Scored buyers per run

`run_id`, `target_domain`, `buyer_id`, `buyer_name`, `signal_type`, `signal_summary`, `signal_score`

### `contacts` — Featured buyer contacts per run

`run_id`, `buyer_id`, `contact_name`, `contact_title`, `contact_email`, `email_verified`, `relevance_score`

### `audit_log` — Step-level execution log

`run_id`, `step`, `status` ('success'|'failure'|'timeout'|'warning'|'skipped'), `message`, `duration_seconds`, `metadata` (JSON), `created_at`

## State Preservation

The pipeline preserves all collected state on failure:

1. **Run stub created in s1** — every step from s2 onward has a valid `run_id` for audit logging
2. **Partial state persisted on crash** — `update_run_failed()` saves whatever was collected (search strategy, signals, buyers, report markdown) using `COALESCE` to avoid overwriting already-saved data
3. **Run marked 'failed'** — not left as 'processing'. `completed_at` timestamp set
4. **Failure logged to audit_log** — `pipeline_failed` entry with exception type, duration, and which state keys were populated
5. **Error response includes partial state** — the return dict contains `partial_state` with all collected data + `metadata.last_completed_keys`

The only unrecoverable edge case is s0 failing before s1 runs (webhook validation error) — but there's nothing to persist since no data was collected.

## Configuration Reference (`config.py`)

All values are documented inline with options and gotchas. Key categories:

| Category | Examples | Env Override |
|---|---|---|
| **LLM** | `LLM_MODEL`, `LLM_MAX_TURNS`, `LLM_MAX_TOKENS` | Yes |
| **Timeouts** | `TIMEOUTS["s6"]` = 90s, `TIMEOUTS["s9"]` = 30s | No |
| **Page sizes** | `OPPORTUNITY_PAGE_SIZE` = 40, `BUYER_SEARCH_PAGE_SIZE` = 25 | No |
| **Context limits** | `AI_PROFILE_CHAR_LIMIT` = 3000, `AI_OPPS_MAX` = 15 | No |
| **Thread pools** | `MAX_WORKERS_DISCOVERY` = 3, `MAX_WORKERS_ENRICHMENT` = 5 | No |
| **Async polling** | `ASYNC_POLL_INTERVAL` = 3s, `BUYER_CHAT_MAX_WAIT` = 60s | No |
| **CTA copy** | `CTA_BUYERS_COUNT`, `CTA_RECORDS_COUNT` | No |
| **External** | `NOTION_PARENT_PAGE_ID`, `DB_PATH` | Yes |

## Running

### Full end-to-end (real API calls)

```bash
python agent/run_vmock.py
```

### Q&A sub-agent

```bash
python -m agent.llm "What SLED buyer types does Starbridge support?"
```

### HTTP server (pipeline monitor + webhook intake)

```bash
python -m agent.server
# or: uvicorn agent.server:app --port 8111
# Open http://127.0.0.1:8111 for the pipeline explorer + live monitor
```

Endpoints:
- `GET /` — serves `pipeline-explorer.html`
- `POST /api/run` — accepts webhook JSON, runs pipeline in background thread, returns `run_id`
- `GET /api/status/{run_id}` — poll target (audit_log entries + run metadata)
- `GET /api/runs` — list recent runs for the run selector
- `GET /api/data/{run_id}/{table}` — fetch discoveries/contacts/audit_log/run detail

Single concurrent run enforced (returns 409 if pipeline already running).

### Query the database

```bash
python -c "
from agent.db import get_connection
conn = get_connection()
for row in conn.execute('SELECT id, target_domain, status, created_at FROM runs ORDER BY id DESC LIMIT 5'):
    print(dict(row))
"
```

## Scoring Algorithm (s4)

Deterministic, no LLM. Weights:

| Factor | Weight | Source |
|---|---|---|
| Buyer type match | 25% | Does buyer type match LLM's target types? |
| Signal count | 20% | How many opportunities reference this buyer |
| Recency | 20% | Most recent signal age (365-day decay) |
| Urgency | 15% | Has RFP, contract expiration, or deadline? |
| Dollar value | 10% | Highest dollar amount across signals |
| Keyword hits | 10% | How many primary keywords appear in signal text |

Normalized per-batch (0-1 scale), sorted descending. Top buyer = featured, next 4 = secondary.

## Validation Checks (s14)

7 deterministic checks + 1 advisory LLM check:

1. Buyer name in report header
2. Product name appears in report
3. Footer has current month/year
4. No contact rows with both email AND phone as "—"
5. Report length > 500 chars
6. Featured contact emails exist in source data
7. Secondary buyer names appear in secondary section (warnings only)
8. (LLM, advisory) Fact-check: contacts, buyer attributes, initiative names, dollar amounts vs source
