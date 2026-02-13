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

**Current state**: Steps 1-11 are done manually by Hagel (fulfillment operator) in 20-60 minutes.
**V1 target**: Steps 3-10 are fully automated, completing in < 30 seconds.

## Starbridge's Moat

Starbridge monitors 296K+ government/education buyers and has indexed 107M+ board meetings and procurement records. Their intelligence is sourced from public records, FOIA requests, and institutional documents — data that's technically public but practically inaccessible at scale. No competitor has this dataset.

## Key Systems

| System | Role | Owner | Status |
|---|---|---|---|
| **Smartlead** | Outbound email + reply detection | Gurmohit (deliverability) | Active — webhook config TBD |
| **Clay** | Routing hub (webhook intake → Datagen → Slack) | Jeremy | Active — workspace 484780 |
| **Datagen** | Orchestration (Supabase → LLM → report → webhook) | Jeremy | Being built |
| **Supabase** | Signal database (intent signals by domain) | Kushagra | Active — schema pending |
| **Starbridge API** | Buyer attributes (DM info, budget, logo) | Yurii | Dev-gated — V2 dependency |
| **Slack** | Dispatch hub (#intent-reports) | All | Active |
| **Notion/Webflow** | Report hosting | Jeremy / Nastia | TBD |
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

data/                                  # Reference data — what signals and buyers look like
  README.md                            #   What lives here
  signal-taxonomy.md                   #   Signal types (contract expiration, board mention, budget, RFP, leadership change, grant)
  buyer-attributes.md                  #   Attributes from SB API — budget (most valuable per Justin), logo, location, type, etc.
  sample-intel.md                      #   Redacted examples of all 3 intel tiers — real patterns from Slack

roadmap/                               # What ships when — V1 deadline vs. future vision
  README.md                            #   Current priorities + sequencing
  v1-mvp.md                           #   V1 spec — deadline, scope in/out, critical path, blockers, acceptance criteria
  v2-scale.md                         #   V2 — multi-signal, multi-channel, branded reports, SB API integration
  ideas-parking-lot.md                 #   Future ideas — Signal Refresher, batch pre-gen, Procurement Risk Signals, more
```

**Why it's organized this way**: `context/` (stable company knowledge) is separated from `workflows/` (operational processes that change weekly). `systems/` has per-tool subdirectories so debugging goes straight to the right place. `playbooks/` are operator-facing SOPs; `templates/` are copy-paste artifacts — they evolve independently. `decisions/` prevents re-litigating architectural choices. `roadmap/` has an explicit V1/V2 split because the trial has a deadline.

## Working Guidelines

1. **Placeholders**: Gaps are tagged with `{{UNKNOWN:}}`, `{{UNVERIFIED:}}`, or `{{TBD:}}`. Run `grep -rn '{{UNKNOWN\|{{UNVERIFIED\|{{TBD' .` to find all open items.
2. **Two data sources**: Supabase (signals, Kushagra) and Starbridge API (buyer attributes, Yurii). They're complementary, not redundant.
3. **DM-later flow**: V1 ships without DM info. DM contact card is a meeting hook, not a giveaway. See decisions/003-dm-later-flow.md.
4. **Datagen over Clay-only**: Complex multi-step logic lives in Datagen. Clay is the router. See decisions/002-datagen-cloud-agents.md.
5. **Gamma is being replaced**: Non-deterministic, unbranded, manual. See systems/deliverables/gamma-legacy.md.
6. **52% of PRs from email 2+**: Multi-signal sequences work, but only in the same thread. This drives Kushagra's allocation framework.

## Critical Path for V1

1. ✅ Document the system (this repo)
2. ⬜ Kushagra meeting → Supabase schema → Datagen can query signals
3. ⬜ Explore Clay workspace → webhook config → routing logic
4. ⬜ Build Datagen agent → Supabase → LLM → Notion → webhook
5. ⬜ Connect Clay ↔ Datagen ↔ Slack
6. ⬜ End-to-end test with sample accounts
7. ⬜ Rollout (target: Tuesday 2/17)

## Key Metrics

| Metric | Current | V1 Target |
|---|---|---|
| PR → intel delivery time | 20-60 min | < 30 sec |
| PR → meeting conversion | ~50% | Maintain or improve |
| PR rate (prospect → positive reply) | ~0.7% | Not Jeremy's scope (deliverability team) |
| Monthly email volume target | Ramping | 3.3M/month at scale |
| Pipeline automation rate | 0% | > 95% |

## Datagen Python SDK (how to use)

### Purpose

Use the Datagen Python SDK (`datagen-python-sdk`) when you need to run DataGen-connected tools from a local Python codebase (apps, scripts, cron jobs). Use Datagen MCP for interactive discovery/debugging of tool names and schemas.

### Prerequisites

- Install: `pip install datagen-python-sdk`
- Auth: set `DATAGEN_API_KEY` in the environment

### Mental model (critical)

- You execute tools by alias name: `client.execute_tool("<tool_alias>", params)`
- Tool aliases are commonly:
  - `mcp_<Provider>_<tool_name>` for connected MCP servers (Gmail/Linear/Neon/etc.)
  - First-party DataGen tools like `listTools`, `searchTools`, `getToolDetails`
- Always be schema-first: confirm params via `getToolDetails` before calling a tool from code.

### Recommended workflow (always follow)

1) Verify `DATAGEN_API_KEY` exists (if missing, ask user to set it)
2) Import and create the SDK client:
   - `from datagen_sdk import DatagenClient`
   - `client = DatagenClient()`
3) Discover tool alias with `searchTools` (don't guess)
4) Confirm tool schema with `getToolDetails`
5) Execute with `client.execute_tool(tool_alias, params)`
6) Handle errors:
   - 401/403: missing/invalid API key OR the target MCP server isn't connected/authenticated in DataGen dashboard
   - 400/422: wrong params → re-check `getToolDetails` and retry

### Minimal example

```python
import os
from datagen_sdk import DatagenClient

if not os.getenv("DATAGEN_API_KEY"):
    raise RuntimeError("DATAGEN_API_KEY not set")

client = DatagenClient()
result = client.execute_tool(
    "mcp_Gmail_gmail_send_email",
    {
        "to": "user@example.com",
        "subject": "Hello",
        "body": "Hi from DataGen!",
    },
)
print(result)
```

### Discovery examples (don't skip)

```python
from datagen_sdk import DatagenClient

client = DatagenClient()

# List all tools
tools = client.execute_tool("listTools")

# Search by intent
matches = client.execute_tool("searchTools", {"query": "send email"})

# Get schema for a tool alias
details = client.execute_tool("getToolDetails", {"tool_name": "mcp_Gmail_gmail_send_email"})
```

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