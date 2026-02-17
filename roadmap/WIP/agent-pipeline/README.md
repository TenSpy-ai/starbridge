# Intel Brief — Discovery & Showcase Pipeline

Everything needed to build and run the automated intel brief pipeline as a Claude Code agent.

## What This Is

A 19-step agent pipeline that takes a positive email reply (via Clay webhook) and produces a published intel brief ("Discovery & Showcase" report) in < 60 seconds. Currently being converted from a manual process (20-60 min) and interactive design playground into a production Claude Code agent.

The brief discovers which SLED buyers are relevant to the target company, enriches them via Starbridge API, generates a personalized intel showcase, and publishes to Notion.

## Files

### Architecture & Implementation

| File | Description |
|---|---|
| [architecture.md](./architecture.md) | Agent structure — orchestrator, subagents, parallel groups, model selection |
| [sdk-reference.md](./sdk-reference.md) | Claude Agent SDK patterns — subagents, skills, hooks, tools, validation loops |

### Pipeline Spec (the 19 steps)

| File | Description |
|---|---|
| [intel-report-workflow-v2.html](./intel-report-workflow-v2.html) | **Interactive playground** — open in browser, click steps, view data flow diagram. Each step has: prompt, output schema, quality rules, edge cases, and data dependencies. "View All" exports the full spec as markdown. |
| [intel-report-agent-directions.md](./intel-report-agent-directions.md) | Written agent execution spec (earlier 14-step version, superseded by the 19-step v2) |
| [intel-report-prompts.md](./intel-report-prompts.md) | Agent prompt templates per phase (earlier version) |

### Legacy

| File | Description |
|---|---|
| [intel-report-workflow.html](./intel-report-workflow.html) | v1 playground (superseded by v2) |
| [playground-README.md](./playground-README.md) | Documentation for the interactive playground (data architecture, naming conventions, how to modify steps) |

## Pipeline Overview

```
Webhook → Validate → Analyze → Discover → Select → Enrich → Generate → Assemble → Validate → Publish
```

| Phase | Steps | Step Names | Execution |
|---|---|---|---|
| I. Source | s0 | Webhook Input | sequential |
| II. Input | s1 | Validate & Load Context | sequential |
| III. Analyze | s2 | Analyze Target ICP | sequential (LLM) |
| IV. Discover | s3a, s3b, s3c | Signal Discovery — Primary / Alternate / Buyer Type | **parallel (Group A)** |
| V. Select | s4, s5 | Rank & Select Buyers → Persist Discovery | sequential |
| VI. Generate | s6–s12 | Featured Buyer Deep Intel, Secondary Buyers Intel, Exec Summary, Featured Section, Secondary Cards, CTA, Footer | **parallel (Group B)** — 5 branches |
| VII. Assemble | s13, s14, s15, s16 | Assemble Report → Validate → Publish to Notion → Save & Return | sequential |

### Phase VI Execution Detail (5 parallel branches)

All branches launch after s5 completes. s9 and s10 have internal data dependencies:

| Branch | Steps | What It Does | Notes |
|---|---|---|---|
| A | s8 | Executive Summary (LLM) | Fast — no API dependencies |
| B | s6 → s9 | Featured Buyer Intel (4 API calls) → Featured Section (LLM) | **Critical path** — s6 includes AI chat (10-30s) |
| C | s7 → s10 | Secondary Buyers Intel (API) → Secondary Buyer Cards (LLM) | Skipped if 0 secondaries |
| D | s11 | Starbridge CTA (LLM) | May re-run once if s14 validation fails |
| E | s12 | Footer (template fill) | Instant — no LLM call |

### Step Types

Each step in the explorer is tagged with a type badge:

| Badge | Meaning | Steps |
|---|---|---|
| `source` | Webhook entry point | s0 |
| `validate` | Field validation / report QA | s1, s14 |
| `sqlite` | SQLite read/write | s1, s5, s16 |
| `claude` | Claude CLI sub-agent call | s2, s9, s10, s14 |
| `tool` | Starbridge/Supabase API calls | s3a, s3b, s3c, s6, s7, s15 |
| `template` | Deterministic template fill | s8, s11, s12 |
| `python` | Code-only (scoring, concat, parse) | s0, s4, s13 |

## SQLite Schema

The pipeline uses a local SQLite database to cache discovery results and enable incremental runs. Key tables (defined in s1):

- **`runs`** — One row per pipeline execution. Stores raw discovery JSON, selection results, generated sections, final report markdown, and Notion URL.
- **`discoveries`** — Cached buyer/signal insights from prior runs (ranked results from s4).
- **`contacts`** — Contact data per buyer per run.
- **`audit_log`** — Step-level execution trace. Each step logs status, duration, and optional message/metadata via `StepTimer` context manager.

s1 reads prior runs for the same domain. s5 persists discovery data. s16 saves the final report and all generated sections.

## Pipeline Explorer

The pipeline explorer (`agent/pipeline-explorer.html`) has 3 view modes: **List**, **Diagram**, **Monitor**.

### List + Diagram Views (static — no server needed)
Open `pipeline-explorer.html` directly in a browser.
1. **List view** (default): click a step to see its full detail panel (prompt, inputs/outputs, schema, quality rules, edge cases)
2. **Diagram view**: node graph with data flow arrows, parallel group boundaries (teal), and sequential chains (pink)
3. **View All**: button in bottom bar — full markdown export of all 19 steps
4. **Copy Markdown**: copies the selected step's full spec to clipboard
5. Edit any prompt in the detail panel — bottom bar markdown updates instantly

Step indicators in list/diagram nodes: service tag (LLM/SB/Notion/DB), timeout, tool count (teal). Runtime status (failed/warning) appears only in the Monitor view.

### Monitor View (live execution — requires server)

The Monitor view provides a live dashboard for running and observing pipeline executions.

**Start the server:**
```bash
cd /Users/oliviagao/project/starbridge
python -m agent.server
# Open http://127.0.0.1:8111
```

**Features:**
- **Starting Point Form** — fill in webhook fields (target_company, target_domain, product_description, etc.) or use the VMock preset for one-click testing
- **Step Progress Tracker** — 19 steps grouped by phase with live status indicators (pending/running/completed/failed). Running state is inferred from audit_log entries.
- **Data Viewer** — 4 tabs: Run metadata, Discoveries, Contacts, Audit Log
- **Past Runs** — dropdown to load and inspect any previous pipeline execution

**Server endpoints** (`agent/server.py`):

| Endpoint | Method | Purpose |
|---|---|---|
| `GET /` | GET | Serve pipeline-explorer.html |
| `POST /api/run` | POST | Launch pipeline in background thread, return run_id |
| `GET /api/status/{run_id}` | GET | Poll target — run metadata + audit_log |
| `GET /api/runs` | GET | List recent runs for dropdown |
| `GET /api/data/{run_id}/{table}` | GET | Detailed data (discoveries/contacts/audit_log/run) |

## Key Architecture Decisions

1. **Orchestrator + Subagents** — Opus orchestrator handles state/branching, Sonnet subagents handle parallel work
2. **Two parallel groups** — Group A (3 discovery searches) and Group B (5 generation branches with internal data dependencies)
3. **Validation loop** — s14 can retry s11 once if CTA fails personalization check
4. **Deterministic steps stay in code** — s0, s1, s5, s12, s13, s15, s16 are not LLM calls
5. **Datagen as tool layer** — all external API calls go through `client.execute_tool()`
6. **SQLite for state** — local DB caches discovery results, enables duplicate detection, and stores all intermediate outputs for debugging/re-runs

## Report Sections (output of Phase VI)

The final report assembled in s13 contains these sections in fixed order:

1. **Executive Summary** (s8) — 2-3 sentences, data-driven overview
2. **Featured Buyer Deep-Dive** (s9) — snapshot card + "why this buyer matters" (3 bullets) + key contact + "what's happening now"
3. **Secondary Buyer Cards** (s10) — compact cards with signal highlight + key contact per buyer
4. **What Starbridge Can Do** (s11) — personalized CTA tailored to the target company's product/segments
5. **Footer** (s12) — timestamp + data source attribution (varies based on AI chat availability)

## Open Questions

See [architecture.md § Open Questions](./architecture.md#open-questions) for unresolved decisions:
- Local vs. Datagen execution
- SQLite location
- Webhook trigger mechanism
- s4 LLM tiebreak implementation
