# CLAUDE.md — Starbridge GTM Engine Context

Read this file first. It's the entry point for understanding the entire system.

## What This Repo Is

A comprehensive context repository for Starbridge.ai's GTM (Go-To-Market) automation pipeline. It documents every system, workflow, decision, and data structure involved in converting outbound email replies into branded intelligence reports delivered to BDRs via Slack.

**Owner**: Jeremy Ross (Senior RevOps Consultant / GTM Engineer) — **this is the user**
**Client**: Starbridge.ai — SLED procurement intelligence platform
**Engagement**: 3-6 week paid trial ($20K). Terms agreed 1/20/26, announced in #gtm-eng 1/29/26, onboarding 2/4/26.

## The Core Workflow (Read This First)

```
1. Smartlead sends outbound emails to SLED prospects
2. Prospect replies positively
3. Smartlead fires a webhook to Clay
4. Clay posts "new positive reply" to Slack #intent-reports
5. Clay sends the prospect's domain to Datagen
6. Datagen queries Supabase for all intent signals for that domain
7. Datagen runs LLM processing: rank signals, generate SLED Signal Bullets
8. Datagen generates an intel report page (Notion → Webflow)
9. Datagen returns the report URL to Clay
10. Clay posts "intel is ready" + report link to Slack #intent-reports
11. BDR sends the report to the prospect and calls them
```

**Current state**: Steps 1-4 manual (Hagel). Steps 5-10 automated by `agent/pipeline.py` (~47s). Steps 5-10 run as a 18-step pipeline: webhook → LLM strategy → Starbridge API discovery → deterministic scoring → parallel enrichment (profile, contacts, AI chat) → LLM report generation → validation → Notion publish.
**V1 target**: Steps 3-10 fully automated end-to-end via Clay webhook trigger, completing in < 60 seconds.
**Remaining**: Clay webhook → pipeline trigger (step 3), Slack dispatch of report URL (step 10).

## Starbridge's Moat

Starbridge monitors 296K+ government/education buyers and has indexed 107M+ board meetings and procurement records. Their intelligence is sourced from public records, FOIA requests, and institutional documents — data that's technically public but practically inaccessible at scale. No competitor has this dataset.

## Key Systems

| System | Role | Owner | Status |
|---|---|---|---|
| **Smartlead** | Outbound email + reply detection | Gurmohit (deliverability) | Active — webhook config TBD |
| **Clay** | Routing hub (webhook intake → Datagen → Slack) | Jeremy | Active — workspace 484780 |
| **Datagen** | Tool hosting (Starbridge custom tools + Notion MCP) | Jeremy | Active — tools deployed, SDK + REST |
| **Intel Pipeline** | Local orchestrator (`agent/`) — webhook → report → Notion | Jeremy | **Built & tested** — see `agent/README.md` |
| **Starbridge API** | Buyer data (296K buyers, 107M signals) via Datagen custom tools | Yurii | Active — accessed via Datagen REST |
| **Supabase** | Signal database (intent signals by domain) | Kushagra | Active — schema pending |
| **Slack** | Dispatch hub (#intent-reports) | All | Active |
| **Notion** | Report hosting — published via Datagen MCP SDK | Jeremy | Active — reports auto-published |
| **Apollo/Nooks** | Dialer (BDR phone calls) | BDRs | Active |

## Team

| Person | Role | Key Responsibility |
|---|---|---|
| **Henry Bell** | Head of Growth | Jeremy's main stakeholder. Final decisions on strategy. LinkedIn: [henryhamerbell](https://www.linkedin.com/in/henryhamerbell/) |
| **Kushagra** | GTM Engineer | Supabase, signal allocation, Slack bots. Key technical counterpart. |
| **Yurii Talashko** | Engineer | Starbridge API access. V2 blocker. |
| **Hagel Alejandro** | Fulfillment Operator (Philippines) | Current manual process owner. Shifts to QA in V1+. |
| **Neil Daiksel** | BDR + Intel Formatting | Gemini prompts for signal processing. Starting point for LLM logic. |
| **Nastia** | Design Lead | Report branding. V2 dependency. |
| **Jorge, Joseph, Glenn, Jaime** | BDRs | End users — receive intel, contact prospects. |

## Intel Report Tiers

| Tier | Content | Data Source |
|---|---|---|
| **Tier 1** | Top signals + SLED Signal Bullets | Supabase (V1) |
| **Tier 2** | Tier 1 + DM contact card + buyer attributes | + Starbridge API (V2) |
| **Tier 3** | Tier 2 + relevancy analysis + pitch angle + gameplan | + LLM analysis (V3) |

## Repo Structure

```
CLAUDE.md                              # Entry point — system overview, team, core workflow, critical path
PLACEHOLDERS.md                        # Index of all {{UNKNOWN}}/{{UNVERIFIED}}/{{TBD}} tags. 320 open items.

agent/                                 # ⭐ Intel brief pipeline — the core automation (see agent/README.md)
  pipeline.py                          #   18-step orchestrator: 7 phases, parallel execution, hard-fail, ~47s per run
  llm.py                              #   5 LLM sub-agents via `claude -p` CLI (search_strategy, featured, secondary, shape+publish, fact_check) + ask() Q&A
  tools.py                            #   Starbridge custom tools (REST) + Notion MCP (Datagen SDK): search, profile, contacts, chat, publish
  config.py                           #   All tunables + CONFIG_METADATA, runtime editing, factory reset, config snapshotting
  db.py                               #   SQLite: 4 tables (runs, discoveries, contacts, audit_log), StepTimer, CRUD
  server.py                           #   FastAPI on port 8111: pipeline-explorer.html, run/batch API, config API (GET/PATCH/reset), run isolation
  run_vmock.py                         #   End-to-end test runner (VMock webhook → real API + LLM calls → Notion report)
  pipeline-explorer.html               #   Interactive pipeline monitor UI (run launcher, live step tracking, data explorer, config panel)
  README.md                           #   Full architecture docs, 18-step reference, scoring algorithm, validation checks

context/                               # Stable company knowledge — changes slowly
  company-overview.md                  #   What Starbridge is, SLED moat, funding ($10M seed → $42M Series A), data flywheel
  engagement-scope.md                  #   Trial terms ($20K/6wk), what Jeremy owns, timeline, comp context, expenses
  team-roster.md                       #   Names, roles, Slack handles, who owns what, meeting plan
  tech-stack.md                        #   All tools + how they connect (Clay, Smartlead, Supabase, SB API, Datagen, etc.)
  terminology.md                       #   Starbridge-specific vocab — Bridges, signals, SLED, tiers, DM-later, etc.

workflows/                             # Operational processes — how leads move, how data flows
  project-endgame-overview.md          #   Full outbound engine end-to-end. 7 campaigns/mo, FY25 benchmarks.
  positive-reply-flow.md               #   THE core workflow being automated. SL → Clay → Datagen → Supabase → LLM → report → Slack → BDR.
  intel-report-tiers.md                #   Tier 1/2/3 definitions + real examples (Point Quest, OxBlue, SwiftComply, etc.)
  current-state.md                     #   Hagel's manual process today — Smartlead → Slack bots → Gemini → Gamma → BDR dispatch
  future-state.md                      #   Target automated architecture. V1 (signals only) → V2 (+ DM/attributes) → V3 (full auto)
  bdr-handoff.md                       #   How BDRs receive intel via Slack, send payload emails, call via Nooks, book meetings
  multi-signal-campaigns.md            #   Kushagra's signal allocation — multiple signals per sequence, 52% of PRs from email 2+
  contact-enrichment.md                #   Enrichment waterfall (FullEnrich → Clay), 15% monthly data decay, ZeroBounce validation

systems/                               # Per-tool technical documentation
  clay/                                #   Central routing hub — receives webhooks, dispatches to Datagen and Slack
    README.md                          #     Workspace overview, how Clay fits in the pipeline
    project-endgame.md                 #     Main workbook — tables, webhook source columns, SLED Signal Bullets, automations
    boiler-room.md                     #     Secondary workbook — converts signals into phone-ready intel snippets for BDRs
  smartlead/                           #   Outbound email sending + positive reply detection
    README.md                          #     Campaign structure, sending volume (targeting 3.3M/mo), deliverability (Gurmohit)
    webhook-spec.md                    #     Positive reply webhook — trigger conditions, payload schema (mostly {{UNKNOWN}})
  supabase/                            #   Kushagra's signal database — ⚠️ #1 V1 blocker (schema unknown until Kushagra meeting)
    README.md                          #     What Supabase stores, how it relates to SB API, access status
    schema.md                          #     Tables, columns, relationships — all {{UNKNOWN}}, scaffolding only
    queries.md                         #     Key query patterns — "all signals for domain X", hypothetical until schema confirmed
  starbridge-api/                      #   Buyer attributes + DM info — internal-only, dev-gated, V2 dependency
    README.md                          #     Access status, auth (unknown), two-data-source model, priority endpoints, credits
    endpoints.md                       #     Full API endpoint reference captured from the platform (40+ endpoints)
    data-model.md                      #     Entity model — 107M meetings, 107M purchases, 44.3K RFPs, 296K buyers, FOIA
  datagen/                             #   Orchestration layer — cloud agents that wire Supabase → LLM → report → Clay
    README.md                          #     How Datagen fits in the pipeline, pricing ($50 → $500/mo)
    agents.md                          #     Agent spec — 8-step pipeline pseudocode, implementation checklist, async polling vision
  slack/                               #   Dispatch + handoff hub — #intent-reports is the operational nerve center
    README.md                          #     Channel overview (#intent-reports, #gtm-eng, #proj-endgame)
    intent-reports-format.md           #     Two Slack message templates — "new positive response" + "custom intel is ready"
    slack-bots.md                      #     Kushagra's endgame-lookup bot + Starbridge Slack app (platform data)
  deliverables/                        #   What gets sent to prospects — the intel report itself
    README.md                          #     Report format options and evolution path
    gamma-legacy.md                    #     Current Gamma process — 5 known problems (non-deterministic, unbranded, manual, etc.)
    intel-report-v2.md                 #     Target: branded landing page. Notion vs Super.so vs Webflow comparison.

playbooks/                             # Operator-facing SOPs — "how to do the job" docs
  README.md                            #   Index of all playbooks
  positive-reply-sop.md               #   Step-by-step: what happens when a positive reply comes in (manual + future automated)
  operator-checklist.md                #   Hagel's per-reply checklist — what to verify before posting dispatch/intel-ready messages
  bdr-response.md                      #   BDR actions: acknowledge → payload email → call → convert. Threading guidance.
  dm-later-flow.md                     #   New flow (2/4/26): lead with intel, offer DMs on call. Decouples DM lookup from speed.
  campaign-launch.md                   #   How to spin up a new campaign — signal selection, Clay config, Smartlead setup, launch checklist

templates/                             # Copy-paste artifacts — messages, emails, report structures
  README.md                            #   Index + usage notes
  slack-dispatch.md                    #   "New positive response" Slack message template with variables
  slack-intel-ready.md                 #   "Custom intel is ready" Slack message template with Gamma link + DM card + notes
  post-positive-reply-email.md         #   BDR payload emails — Tier 1/2/3 variants + DM-later follow-up + voicemail script
  follow-up-sequence.md               #   4-email follow-up sequence (Nudge → New Value → Social Proof → Break-Up)
  intel-report-template.md             #   Structured template for the intel report content — sections, attributes by tier

decisions/                             # Architecture Decision Records — "why we did X"
  README.md                            #   ADR index + how to add new decisions
  001-gamma-to-branded-reports.md      #   Why replacing Gamma with Notion/Webflow
  002-datagen-cloud-agents.md          #   Why using Datagen for orchestration instead of Clay-only
  003-dm-later-flow.md                 #   Why decoupling DM lookup from initial intel delivery
  004-multi-signal-allocation.md       #   Kushagra's framework for distributing signals across email sequences

data/                                  # Reference data + pipeline runtime artifacts
  README.md                            #   What lives here
  signal-taxonomy.md                   #   Signal types (contract expiration, board mention, budget, RFP, leadership change, grant)
  buyer-attributes.md                  #   Attributes from SB API — budget (most valuable per Justin), logo, location, type, etc.
  sample-intel.md                      #   Redacted examples of all 3 intel tiers — real patterns from Slack
  pipeline.db                          #   SQLite: run history, discoveries, contacts, audit_log (auto-created on first run)

roadmap/                               # What ships when — V1 deadline vs. future vision
  README.md                            #   Current priorities + sequencing
  v1-mvp.md                           #   V1 spec — deadline, scope in/out, critical path, blockers, acceptance criteria
  v2-scale.md                         #   V2 — multi-signal, multi-channel, branded reports, SB API integration
  ideas-parking-lot.md                 #   Future ideas — Signal Refresher, batch pre-gen, Procurement Risk Signals, more
  WIP/                                 #   Work-in-progress artifacts — not yet finalized
    agent-pipeline/                    #     Pipeline design docs and interactive explorers
      README.md                        #       Index + data architecture docs
    prompts/                           #     Agent prompts and interactive workflow playground
      README.md                        #       Index + data architecture docs
      intel-report-workflow-v2.html    #       Interactive 18-step pipeline explorer (open in browser)
      intel-report-workflow.html       #       Earlier v1 (superseded by v2)
      intel-report-agent-directions.md #       Written agent execution spec (14 steps)
      intel-report-prompts.md          #       Agent prompt templates per phase
```

**Why it's organized this way**: `context/` (stable company knowledge) is separated from `workflows/` (operational processes that change weekly). `systems/` has per-tool subdirectories so debugging goes straight to the right place. `playbooks/` are operator-facing SOPs; `templates/` are copy-paste artifacts — they evolve independently. `decisions/` prevents re-litigating architectural choices. `roadmap/` has an explicit V1/V2 split because the trial has a deadline.

## Working Guidelines

1. **Placeholders**: Gaps are tagged with `{{UNKNOWN:}}`, `{{UNVERIFIED:}}`, or `{{TBD:}}`. Run `grep -rn '{{UNKNOWN\|{{UNVERIFIED\|{{TBD' .` to find all open items.
2. **Two data sources**: Supabase (signals, Kushagra) and Starbridge API (buyer attributes, Yurii). They're complementary, not redundant.
3. **DM-later flow**: V1 ships without DM info. DM contact card is a meeting hook, not a giveaway. See decisions/003-dm-later-flow.md.
4. **Datagen over Clay-only**: Complex multi-step logic lives in Datagen. Clay is the router. See decisions/002-datagen-cloud-agents.md.
5. **Gamma is being replaced**: Non-deterministic, unbranded, manual. See systems/deliverables/gamma-legacy.md.
6. **52% of PRs from email 2+**: Multi-signal sequences work, but only in the same thread. This drives Kushagra's allocation framework.
7. **QA scripts**: When building or modifying code that has a UI counterpart or config layer, create/update QA scripts in a `qa/` subfolder. QA scripts verify alignment between code, UI, config, and DB — run them after changes. See `agent/qa/CLAUDE.md`.

## Critical Path for V1

1. ✅ Document the system (this repo)
2. ⬜ Kushagra meeting → Supabase schema → Datagen can query signals
3. ⬜ Explore Clay workspace → webhook config → routing logic
4. ✅ Build intel pipeline → Starbridge API → LLM → Notion (`agent/`)
5. ⬜ Connect Clay ↔ pipeline webhook → Slack dispatch
6. ✅ End-to-end test with sample accounts (VMock — 15+ successful runs, ~47s per run)
7. ⬜ Rollout — production webhook integration, Slack #intent-reports dispatch, monitoring

## Key Metrics

| Metric | Before | Current (Pipeline) | V1 Target |
|---|---|---|---|
| PR → intel delivery time | 20-60 min | **~47s** (automated) | < 60s end-to-end |
| PR → meeting conversion | ~50% | TBD | Maintain or improve |
| PR rate (prospect → positive reply) | ~0.7% | ~0.7% | Not Jeremy's scope |
| Monthly email volume target | Ramping | Ramping | 3.3M/month at scale |
| Pipeline automation rate | 0% | Steps 5-10 automated | > 95% |

## Intel Brief Pipeline (`agent/`)

The core automation. Takes a webhook payload (prospect domain + product info), queries Starbridge's buyer database via Datagen-hosted custom tools, generates a branded intel report via Claude LLM sub-agents, and publishes to Notion — all in ~47 seconds.

**Full docs**: `agent/README.md` (architecture, 18-step reference, scoring algorithm, validation checks, running instructions).

### Quick Architecture

```
webhook JSON → pipeline.py orchestrator (18 steps, 7 phases)
                ├── llm.py    — 5 Claude sub-agents via `claude -p` CLI
                ├── tools.py  — Starbridge API (REST) + Notion (Datagen SDK)
                ├── db.py     — SQLite persistence + audit logging
                └── config.py — tunables + metadata + runtime editing + run snapshots
```

### The 7 Phases

| Phase | Steps | Type | What Happens |
|---|---|---|---|
| I-II SOURCE/INPUT | s0, s1 | Python + SQLite | Parse webhook, validate, create DB run stub, load cache |
| III ANALYZE | s2 | **LLM** | Product → SLED segments, keywords, buyer types, opp types |
| IV DISCOVER | s3a, s3b, s3c, s3d | **API** (parallel) | Opportunity search (primary + alternate) + buyer type search + buyer geo search |
| V SELECT | s4, s5 | Python | Deterministic scoring (6 factors), select featured + 4 secondary |
| VI ENRICH | s6→s9, s7→s10, s8, s11 | **API + LLM** (4 parallel branches) | Profile, contacts, AI chat, generate sections |
| VII ASSEMBLE | s12, s13, s14 | **LLM** + API | LLM assembles report from s8/s9/s10/s11 sections + publishes to Notion, fact-check, save + respond |

### Key Design Decisions

- **Hard-fail, no fallbacks**: Every step either succeeds or the pipeline fails. Partial state is persisted to SQLite for debugging. No graceful degradation.
- **s12 assembles from sections**: The report is assembled by the LLM from pre-generated sections: SECTION_FEATURED (s9), SECTION_SECONDARY (s10), SECTION_EXEC_SUMMARY (s8), SECTION_CTA (s11). s12 does NOT receive raw data — raw data is processed upstream by specialized sub-agents in Phase VI.
- **Deterministic scoring (s4)**: Buyer ranking uses 6 weighted factors (type match 25%, signals 20%, recency 20%, urgency 15%, dollar 10%, keyword 10%) — no LLM involved.
- **Anti-hallucination**: s9/s10 prompts explicitly separate what the LLM CAN infer from what it CANNOT. s12 assembler is instructed not to add, remove, or alter facts from sections. s13 validates with deterministic checks + LLM internal consistency check on the assembled report.
- **Run isolation via config snapshotting**: Config is deep-copied at run submission time. Each pipeline run applies its snapshot before executing, so mid-run config changes in the UI only affect the _next_ run. `apply_config_to_modules()` pushes snapshot values into pipeline/tools/llm cached bindings via `setattr()`.
- **Runtime config editing**: All 31 tunables editable via UI config panel or `PATCH /api/config`. Changes are in-memory only (lost on restart). Factory reset via `POST /api/config/reset`.

### Running

```bash
# Full end-to-end test (real API + LLM calls → Notion report)
python agent/run_vmock.py

# Pipeline monitor (web UI on port 8111)
python -m agent.server

# Q&A sub-agent
python -m agent.llm "What SLED buyer types does Starbridge support?"
```

### Environment Requirements

| Variable | Purpose | Required |
|---|---|---|
| `DATAGEN_API_KEY` | Starbridge custom tools + Notion MCP via Datagen | Yes |
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude CLI authentication for LLM sub-agents | Yes |
| `NOTION_PARENT_PAGE_ID` | Notion page where reports are published as children | Has default |
| `LLM_MODEL` | Claude model override (default: `claude-opus-4-6`) | No |

## Datagen — Two Tool Layers

Datagen hosts two types of tools, accessed differently. This distinction is critical.

### Layer 1: Starbridge Custom Tools (REST)

Custom deployments on Datagen's platform. Called via direct REST, NOT via the SDK.

```python
# Sync: POST https://api.datagen.dev/apps/{uuid}
httpx.post(url, headers={"x-api-key": DATAGEN_API_KEY}, json={"input_vars": params})

# Async (buyer_chat): POST /apps/{uuid}/async → poll GET /apps/run/{run_uuid}/output
```

| Tool | UUID (first 8) | Endpoint |
|---|---|---|
| `opportunity_search` | `c15b3524` | Sync REST |
| `buyer_search` | `e69f8d37` | Sync REST |
| `buyer_profile` | `74345947` | Sync REST |
| `buyer_contacts` | `b81036af` | Sync REST |
| `buyer_chat` | `043dc240` | **Async** (POST → poll) |

All wrapped in `agent/tools.py` — use those functions, not raw REST.

### Layer 2: Standard MCP Tools (SDK)

Connected MCP servers (Notion, Gmail, etc.) accessed via the Datagen Python SDK.

```python
from datagen_sdk import DatagenClient
client = DatagenClient()
result = client.execute_tool("mcp_Notion_notion_create_pages", params)
```

Notion tools used by the pipeline: `notion_create_page`, `notion_search`, `notion_fetch`, `notion_update_page` — all wrapped in `agent/tools.py`.

### SDK Prerequisites

- Install: `pip install datagen-python-sdk`
- Auth: set `DATAGEN_API_KEY` in the environment

### Discovery (for adding new tools)

```python
client = DatagenClient()
tools = client.execute_tool("listTools")                                    # list all
matches = client.execute_tool("searchTools", {"query": "send email"})       # search by intent
details = client.execute_tool("getToolDetails", {"tool_name": "alias"})     # get schema
```

Always be schema-first: confirm params via `getToolDetails` before calling a tool from code.

## CRITICAL RULES

### **Git: ALWAYS merge directly to main.**
- No feature branches. No PRs for internal work.
- Commit frequently, push immediately.
- This is a living system—updates flow continuously.
- When told to push code to GitHub (or "gh", etc.), push ALL untracked/modified files (except .gitignore'd). Don't skip anything.

### **Data: HubSpot is source of truth.**
- Account data syncs from HubSpot via DataGen
- Changes to accounts should flow back to HubSpot
- Use the custom tools, not direct API calls

### **Code Execution: Prefer local over DataGen MCP tools.**
- Use local Bash/Python execution whenever possible
- Only use DataGen `executeCode` when you need secrets not available locally (e.g., `HUBSPOT_API_KEY`)
- Local execution is faster, has no rate limits, and keeps data on-machine
- For file operations, git, and shell commands: always use local Bash

### **Accuracy: Verify before asserting.**
- Don't state things as fact unless you've read the code/data or have strong evidence
- If you're reasoning from memory or pattern-matching, say so — "I believe X based on Y" not just "X"
- When comparing systems or making claims about what code does, read it first
- It's fine to be direct and confident when you've done the work; just don't bluff

### **Performance: Look for parallelism.**
- When writing or reviewing code, always consider what can run concurrently
- Examples:
  - API calls for independent records → `ThreadPoolExecutor` (e.g., fetching engagement data for 50 deals in 5 threads instead of one-by-one)
  - Long-running scripts + local file reads → kick off the script in the background, read files while it runs, collect results after
  - Independent data sources → fetch them simultaneously rather than waiting for one before starting the next
- Don't over-parallelize: respect rate limits, keep thread counts reasonable (5-10 for API work), and make sure shared state is thread-safe