# agent/ — Intel Brief Pipeline

Automated SLED procurement intelligence pipeline. Takes a webhook (prospect domain + product info), queries Starbridge's 296K+ buyer database, generates a branded intel report via Claude LLM sub-agents, and publishes to Notion — all in under 60 seconds.

**Status**: Built and tested (15 successful runs). Core pipeline is complete. Remaining: production webhook integration, Slack dispatch, monitoring.

## Architecture Overview

```
HTTP POST / CLI
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  server.py — FastAPI (run/batch/config API + config snapshots)│
│  or: run_vmock.py / direct call to run_pipeline(webhook)     │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  pipeline.py — Orchestrator (run_pipeline)                  │
│                                                             │
│  Phase I-II:   s0 → s1           (parse, validate, DB)     │
│  Phase III:    s2                 (LLM: search strategy)    │
│  Phase IV:     s3a ║ s3b ║ s3c ║ s3d (parallel API discovery) │
│  Phase V:      s4 → s5           (rank, persist)           │
│  Phase VI:     s8 ║ s6→s9 ║ s7→s10 ║ s11                   │
│                (parallel enrich + generate)                  │
│  Phase VII:    s12 → s13 → s14                                │
│                (LLM shape+publish, validate, respond)          │
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
| `config.py` | 350 | All tunables + CONFIG_METADATA (31 entries), runtime config editing, factory reset, config snapshotting for run isolation |
| `db.py` | 434 | SQLite: 4 tables, CRUD operations, `StepTimer` context manager, audit logging |
| `llm.py` | 635 | 5 LLM sub-agents + Q&A function. Backend: `claude -p` CLI via subprocess |
| `pipeline.py` | ~1,250 | 18-step orchestrator with 7 phases, parallel execution, LLM-driven Notion publish |
| `tools.py` | 233 | Starbridge custom tools (REST) + Notion MCP (Datagen SDK) |
| `server.py` | 370 | FastAPI server: pipeline-explorer.html, HTTP run/batch, config API (GET/PATCH/reset), config snapshot per run |
| `run_vmock.py` | 84 | End-to-end test runner (real Starbridge API + real LLM calls) |

**Total: ~3,400 lines of Python** (excluding tests)

## The 18 Steps

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
| **s2** | `s2_search_strategy` | **LLM** (`llm.search_strategy`) | Analyze product → SLED segments, primary/alternate/meeting/rfp keywords, buyer types, opportunity types, geographic hints, ideal buyer profile |

### Phase IV — DISCOVER (parallel)

| Step | Function | Type | What It Does |
|---|---|---|---|
| **s3a** | `s3a_primary_search` | API (`tools.opportunity_search`) | Search opportunities with primary keywords + LLM-chosen opp types |
| **s3b** | `s3b_alternate_search` | API (`tools.opportunity_search`) | Search opportunities with alternate keywords |
| **s3c** | `s3c_buyer_type_search` | API (`tools.buyer_search`) | Search buyers by type (e.g. SchoolDistrict, City) from LLM strategy |
| **s3d** | `s3d_buyer_geo_search` | API (`tools.buyer_search`) | Search buyers by geographic state codes (e.g. CA, TX, NY) |

All four run in parallel via `ThreadPoolExecutor(max_workers=4)`.

### Phase V — SELECT

| Step | Function | Type | What It Does |
|---|---|---|---|
| **s4** | `s4_rank_and_select` | Python (deterministic) | Merge, dedupe, score buyers (type match 25%, signal count 20%, recency 20%, urgency 15%, dollar 10%, keyword 10%). Select featured + up to 4 secondary |
| **s5** | `s5_persist_discovery` | SQLite | Backfill discovery data into the run stub, insert scored buyers into discoveries table |

### Phase VI — ENRICH & GENERATE (4 parallel branches)

| Branch | Steps | Type | What It Does |
|---|---|---|---|
| **a** | s8 | Template | Executive summary (signal count, buyer count, featured buyer) |
| **b** | s6 → s9 | API → **LLM** | Fetch profile + contacts + AI chat for featured buyer, then `llm.featured_section` generates deep-dive markdown → feeds into s12 assembly |
| **c** | s7 → s10 | API → **LLM** | Fetch profile + contacts for each secondary buyer, then `llm.secondary_cards` generates compact cards → feeds into s12 assembly |
| **d** | s11 | Template | CTA section (Starbridge marketing copy) |

s6 internally parallelizes 3 sub-calls: `buyer_profile` + `buyer_contacts` + `buyer_chat` (async polling).

### Phase VII — ASSEMBLE & VALIDATE

| Step | Function | Type | What It Does |
|---|---|---|---|
| **s12** | `s12_assemble` | **LLM** + API | LLM assembles report from pre-generated sections (s8, s9, s10, s11) and publishes to Notion via MCP tools in one CLI session. Retries once on failure (fresh LLM call). |
| **s13** | `s13_validate` | Python + **LLM** + API | 6 deterministic issue checks + 2 warning checks (1 deterministic, 1 LLM). If any findings, LLM fixes the report and updates the Notion page. passed = len(issues) == 0 |
| **s14** | `s14_save_and_respond` | SQLite | Update run to 'completed', save all sections + contacts, build response JSON |

## LLM Sub-Agents (`llm.py`)

All LLM calls go through the `claude` CLI in print mode (`claude -p`), authenticated via `CLAUDE_CODE_OAUTH_TOKEN` from `.env`.

| Sub-Agent | Pipeline Step | System Prompt Focus | Output |
|---|---|---|---|
| `search_strategy()` | s2 | SLED procurement intelligence analyst | JSON: keywords (primary, alternate, meeting, rfp), buyer_types, opportunity_types, geographic_hints, ideal_buyer_profile |
| `featured_section()` | s9 | Featured buyer report writer (data-only, no hallucination) | Markdown: snapshot card, why-this-buyer, key contact, signals |
| `secondary_cards()` | s10 | Compact card generator | Markdown: 3-4 line card per secondary buyer |
| `shape_and_publish_report()` | s12 | Processing Logic + CEO format + Notion publish (CLI with MCP tools) | Tuple: (markdown, notion_url) |
| `fact_check()` | s13 | Fact-checker comparing report vs source data | Tuple: (passed: bool, detail: str) |
| `fix_report()` | s13 | Report editor — fixes issues/warnings in the report | String: corrected markdown |
| `ask()` | standalone | General Q&A for Starbridge pipeline | Free-text answer |

**Default model**: `claude-opus-4-6` (override via `LLM_MODEL` env var)

**Max output tokens**: 64,000 (the CLI maximum). Set via `CLAUDE_CODE_MAX_OUTPUT_TOKENS` in the subprocess env. Configured in `config.py` as `LLM_MAX_OUTPUT_TOKENS`.

**CLI invocation**: `claude -p --model {LLM_MODEL}` (text-only sub-agents — no --max-turns, bounded by 300s subprocess timeout)

**CLI with MCP tools** (s12): `claude -p --model {LLM_MODEL} --mcp-config {temp} --allowedTools mcp__datagen__executeTool` (no --max-turns, bounded by LLM_TOOL_TIMEOUT)

All LLM steps hard-fail with no fallback.

Key detail: The `CLAUDECODE` env var is unset in the subprocess (`CLAUDECODE=""`) to allow nested invocation from within Claude Code sessions.

### Report Assembly + Publishing Architecture (s12 — `shape_and_publish_report`)

The report is **assembled from pre-generated sections AND published to Notion in a single CLI session**. The LLM receives SECTION_FEATURED (s9), SECTION_SECONDARY (s10), SECTION_EXEC_SUMMARY (s8), and SECTION_CTA (s11), combines them with a title header and footer, then publishes to Notion via MCP tool access.

This is an LLM-driven approach: the Claude CLI subprocess is spawned with `--mcp-config` (Datagen MCP server) and `--allowedTools` (restricted to `executeTool` for Notion). The LLM assembles the sections, adds dividers and footer, then calls the Notion create-pages tool, returning both the markdown and page URL.

**Data flow:**
```
s9 SECTION_FEATURED (LLM deep-dive)        ─┐
s10 SECTION_SECONDARY (LLM compact cards)  ─┤
s8 SECTION_EXEC_SUMMARY (template)         ─┼──→ s12 LLM → assemble + publish → REPORT_MARKDOWN + NOTION_PAGE_URL
s11 SECTION_CTA (template)                 ─┘
```

s12 assembles the report from pre-generated sections — it does NOT receive raw data from s6/s7. Raw data (profiles, contacts, opportunities) is processed upstream by s9 and s10, whose outputs feed directly into s12.

**Prompt design — what the section generators (s9/s10) CAN vs CANNOT infer:**

| Can Infer (analysis) | Cannot Infer (hallucination) |
|---|---|
| Use Case Archetype (product ↔ buyer type connection) | Buyer attributes not in FEAT_PROFILE |
| "Why this contact" (title ↔ product need) | Contact names/emails not in FEAT_CONTACTS |
| Outreach script (synthesizing real data points) | Signal details not in FEAT_OPPORTUNITIES |
| Relevancy analysis (why signals matter for product) | Procurement channels not in AI context |
| Strategy bullets (actions based on actual signals) | Any factual claim not in the source data |

**Anti-hallucination enforcement:** s9/s10 prompts mandate "use ONLY the data provided below — zero tolerance for hallucination." s12 assembler is instructed not to add, remove, or alter facts from the pre-generated sections. s13 runs deterministic checks + LLM internal consistency review on the final report, then fixes any findings and updates the Notion page with the corrected version.

### CEO-Approved Report Format

The s12 LLM outputs a structured markdown report published directly as a Notion page:

```
# 📊 [Buyer Name] — Intelligence Report for [Product]

# Buyer Snapshot
> [Emoji] **[Buyer Name]** | [Type Label]
> State, City, Enrollment/Population, Procurement Score, Fiscal Year, Website, Phone
  (all pulled from FEAT_PROFILE — omit lines where data is missing)

# 🎯 Relevancy Analysis
> 🔥 Use Case Archetype: [1-line — inferred from product + buyer type]
  2-3 paragraphs citing SPECIFIC opportunities by name/title/date/dollar amount

# 📋 Gameplan
> Primary DM Target: [Name — Title — Email from FEAT_CONTACTS]
  Why this contact, secondary contacts, outreach script, procurement path
  (procurement path only if data exists in AI context or profile)

# 👥 Key Contacts
  Markdown table from FEAT_CONTACTS (up to 10, ✅ for verified emails)

# 📡 Recent Strategic Signals
  Top 3-5 opportunities with 2-3 sentence analysis each

## Additional Buyers
  Per secondary buyer: location, signal type, heat level, strategy bullets

## What Starbridge Can Do
  CTA section (used from s11 template as-is)

*Generated Starbridge Intelligence [Month Year]*
*Data source: buyer profile, contacts, [AI analysis if available,] opportunity database*
```

### Notion Publishing (integrated into s12)

s12 publishes the report to Notion as part of the LLM session — the Notion page is the final deliverable that BDRs see.

- The Claude CLI session calls `executeTool` → `mcp_Notion_notion_create_pages` via Datagen MCP
- **Page title**: `"{FEATURED_BUYER_NAME} — Intelligence Report for {target_company}"`
- **Parent page**: `NOTION_PARENT_PAGE_ID` (env var, default: `30a845c1-6a83-81d8-9a22-f2360c6b1093`)
- **Output**: `NOTION_PAGE_URL` — this becomes the "intel is ready" link posted to Slack `#intent-reports`

### Context Budget Per LLM Call

| LLM Call | Source Data | Char Limit | ~Tokens |
|---|---|---|---|
| s2 `search_strategy` | Company, domain, product, campaign | ~500 | 125 |
| s9 `featured_section` | Profile + contacts + opps + AI context | ~13K | 3,250 |
| s10 `secondary_cards` | Secondary buyer profiles + contacts + signals | ~4K per buyer | 1,000/buyer |
| **s12 `shape_and_publish_report`** | **All of the above + secondary data + reference sections** | **~24K** | **6,000** |
| s13 `fact_check` | Report text + profile + contacts + opps + AI context | ~11K | 2,750 |

s12 is the most context-heavy call. Limits are configured in `config.py` (`AI_PROFILE_CHAR_LIMIT`, `AI_CONTACTS_CHAR_LIMIT`, `AI_OPPS_CHAR_LIMIT`, `AI_CONTEXT_CHAR_LIMIT`, `AI_REPORT_OPPS_CHAR_LIMIT`, `AI_REPORT_SECTION_CHAR_LIMIT`).

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
| **Notion** (via Datagen MCP SDK) | `tools.py` | `DATAGEN_API_KEY` | 1-2 (create page + optional update). Auto-retry (3x) on transient 500s. |
| **Claude CLI** (`claude-opus-4-6`) | `llm.py` | `CLAUDE_CODE_OAUTH_TOKEN` | 5 (s2 + s9 + s10 + s12 + s13) |

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

Enrichment fields: `feat_profile` (JSON), `feat_contacts` (JSON), `feat_opportunities` (JSON), `feat_ai_context` (text), `sec_profiles` (JSON), `sec_contacts` (JSON)

Output fields: `section_exec_summary`, `section_featured`, `section_secondary`, `section_cta`, `report_markdown`, `notion_url`

Status: `status` ('processing' | 'completed' | 'failed'), `created_at`, `completed_at`

### `discoveries` — Scored buyers per run

`run_id`, `target_domain`, `buyer_id`, `buyer_name`, `signal_type`, `signal_summary`, `signal_score`

### `contacts` — Featured buyer contacts per run

`run_id`, `buyer_id`, `contact_name`, `contact_title`, `contact_email`, `email_verified`

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

All 31 tunables are documented inline with options and gotchas. Key categories:

| Category | Examples | Env Override |
|---|---|---|
| **LLM** | `LLM_MODEL`, `LLM_MAX_OUTPUT_TOKENS`, `LLM_TOOL_TIMEOUT` | Yes |
| **Timeouts** | `TIMEOUTS["s6"]` = 330s, `TIMEOUTS["s3a"]` = 300s | No |
| **Page sizes** | `OPPORTUNITY_PAGE_SIZE` = 40, `BUYER_SEARCH_PAGE_SIZE` = 25 | No |
| **Context limits** | `AI_PROFILE_CHAR_LIMIT` = 3000, `AI_OPPS_MAX` = 15, `AI_REPORT_OPPS_MAX` = 20 | No |
| **Thread pools** | `MAX_WORKERS_DISCOVERY` = 4, `MAX_WORKERS_ENRICHMENT` = 4 | No |
| **Async polling** | `ASYNC_POLL_INTERVAL` = 3s, `BUYER_CHAT_MAX_WAIT` = 300s | No |
| **CTA copy** | `CTA_BUYERS_COUNT`, `CTA_RECORDS_COUNT` | No |
| **External** | `NOTION_PARENT_PAGE_ID`, `DB_PATH` | Yes |

### Runtime Config Editing

All 31 tunables can be edited at runtime via the pipeline explorer UI or API. Changes are **in-memory only** — lost on server restart. Key infrastructure in `config.py`:

- **`CONFIG_METADATA`** — dict mapping each tunable to `{cat, type, desc, unit?}`. Drives the UI config panel and API validation.
- **`get_config_snapshot()`** — returns deep-copied dict of all current tunable values. Used by the API and for run isolation snapshots.
- **`set_config_value(key, value)`** — validates type (int/str/dict) against metadata, updates the module global. Returns `(ok, error_msg)`.
- **`reset_config()`** — restores all tunables to factory defaults (captured at module load via `_FACTORY_DEFAULTS`).
- **`apply_config_to_modules(snapshot)`** — pushes config values into `pipeline.py`, `tools.py`, and `llm.py` cached module-level bindings via `setattr()`. Required because `from .config import X` creates copies that don't update when config globals change.

### Run Isolation

Config is **snapshotted at run submission time**. Each pipeline run uses the config values that were active when it was started, not whatever the user may have changed in the UI since then.

- `server.py` calls `get_config_snapshot()` when a run (or batch) is submitted, stores it in the run entry.
- Before `run_pipeline()` executes, `apply_config_to_modules(snapshot)` pushes the snapshot into the pipeline/tools/llm modules.
- Config changes made mid-run only affect the _next_ run.

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
- `POST /api/run` — accepts webhook JSON, snapshots config, runs pipeline in background thread, returns `run_id`
- `POST /api/batch` — accepts list of webhooks, snapshots config once, runs all in parallel (semaphore-gated)
- `GET /api/status/{run_id}` — poll target (audit_log entries + run metadata)
- `GET /api/batch-status/{batch_id}` — status summary for all runs in a batch
- `POST /api/kill/{run_id}` — signal an active pipeline to stop
- `POST /api/batch-kill/{batch_id}` — kill all active runs in a batch
- `GET /api/runs` — list recent runs for the run selector
- `GET /api/data/{run_id}/{table}` — fetch discoveries/contacts/audit_log/run detail
- `GET /api/config` — returns all 31 tunable values + metadata (categories, types, descriptions)
- `PATCH /api/config` — update one or more config values at runtime (in-memory only)
- `POST /api/config/reset` — restore all tunables to factory defaults

Concurrent runs gated by `MAX_CONCURRENT_RUNS` semaphore (default 3, returns 409 if full).

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

## Validation Checks (s13)

6 deterministic issue checks + 2 warning checks (1 deterministic, 1 LLM). `passed = len(issues) == 0` — only issue checks block.

**If any findings (issues OR warnings) exist:**
1. `llm.fix_report()` generates a corrected report from the original + all findings
2. `tools.notion_update_page()` replaces the Notion page content with the corrected report
3. Corrected report is stored as `VALIDATED_REPORT_MARKDOWN` (s14 saves this to DB instead of the original)

Both fix and Notion update are non-blocking (try/except) — if either fails, the pipeline continues with the original report.

**Issues (block validation — `passed = false`):**
1. Buyer name in first 500 chars of REPORT_MARKDOWN
2. Product name (target_company) appears in REPORT_MARKDOWN (case-insensitive)
3. Current month/year appears in REPORT_MARKDOWN
4. No contact table rows with both email AND phone as "—"
5. REPORT_MARKDOWN length > 500 chars
6. Emails extracted from SECTION_FEATURED (s9 output) must exist in FEAT_CONTACTS

**Warnings (logged but don't block — `passed` unaffected):**
7. Secondary buyer names from SECONDARY_BUYERS appear in SECTION_SECONDARY (s10 output) — deterministic
8. LLM fact-check via `llm.fact_check()` — contacts, buyer attributes, initiative names, dollar amounts vs source

## Retry & Resilience

| Layer | Retries | Delay | What's Retried | What's Not |
|---|---|---|---|---|
| **Notion MCP** (`tools.py`) | 3 | 2s, 5s, 10s | Transient failures: 500, 502, 503, timeout | 4xx schema/auth errors (would fail identically) |
| **s12 LLM+MCP publish** (`pipeline.py`) | 2 | immediate | Any exception — fresh LLM call may format MCP params differently | — |
| **Starbridge REST** (`tools.py`) | none | — | — | All errors hard-fail (tool responses are deterministic) |

The Notion MCP retry wrapper (`_call_notion`) applies to all 4 Notion functions: `create_page`, `search`, `fetch`, `update_page`. The s12 retry is separate — it re-runs the entire LLM session (including report assembly + Notion publish) on failure.

## Smoke Tests (`smoke_test.py`)

Integration tests that validate every external tool and conditional pipeline path against live APIs.

```bash
python -m agent.smoke_test          # quick — API tools only, skip LLM/async (~2 min)
python -m agent.smoke_test --full   # full — include LLM + buyer_chat (~5 min)
```

| Category | Tests | Mode |
|---|---|---|
| **A. Tool schemas** | `opportunity_search`, `buyer_search`, `buyer_profile`, `buyer_contacts`, `buyer_chat`, `notion_create_page`, `notion_search`, `notion_fetch`, `notion_update_page` | quick (buyer_chat: full) |
| **B. Conditional paths** | `s3b_skip`, `s3c_skip`, `s3d_skip`, `s4_no_buyers`, `s13_no_findings`, `s13_fix_path` | quick (s13: full) |
| **C. LLM sub-agents** | `llm_search_strategy`, `llm_fact_check`, `llm_fix_report` | full only |

Run after any change to `tools.py` or `pipeline.py` to catch parameter format bugs and broken conditional paths.
