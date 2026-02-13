# Future State — Target Architecture

## The Vision (From Henry's "State of the Union" Post)

> "Agent detects positive replies in Smartlead → pushes domain to Clay → Clay pings Supabase → Clay pings SB API → Clay pushes to Webflow → Clay sends Slack message → we respond directly in-thread with intel + landing page and loop in the BDR."
>
> *— Synthesized from Henry's Slack post outlining the future approach*

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    AUTOMATED FULFILLMENT PIPELINE                 │
│                                                                   │
│  Smartlead                                                        │
│    │ positive reply webhook                                       │
│    ▼                                                              │
│  Clay (Project Endgame)                                           │
│    │                                                              │
│    ├──→ Slack #intent-reports: "New positive reply" (immediate)   │
│    │                                                              │
│    └──→ Datagen Cloud Agent                                       │
│           │                                                       │
│           ├── 1. Query Supabase: all signals for domain           │
│           │                                                       │
│           ├── 2. LLM Processing:                                  │
│           │      - Rank signals → top 10                          │
│           │      - Generate "SLED Signal Bullets"                 │
│           │      - Determine what lead will care about            │
│           │                                                       │
│           ├── 3. Query SB API: (V2)                               │
│           │      - Decision maker info                            │
│           │      - Budget, logo, location                         │
│           │      - Buyer attributes                               │
│           │                                                       │
│           ├── 4. Assemble report content                          │
│           │      - Top signals + bullets                          │
│           │      - DM contact card (if available)                 │
│           │      - Buyer attributes                               │
│           │      - Relevancy analysis (Tier 3)                    │
│           │                                                       │
│           ├── 5. Generate branded page                            │
│           │      {{TBD: Notion / Super.so / Webflow}}             │
│           │                                                       │
│           └── 6. Webhook: report URL → Clay                       │
│                     │                                             │
│                     ▼                                             │
│  Clay receives URL in webhook source column 2                     │
│    │                                                              │
│    └──→ Slack #intent-reports: "Intel ready" + link + DM card     │
│                                                                   │
│  Operator/BDR responds in Smartlead:                              │
│    1) Intel report link                                           │
│    2) Screenshot of report                                        │
│    3) "Happy to give DMs on a call"                               │
│                                                                   │
│  BDR follows up: calls + sequence                                 │
└──────────────────────────────────────────────────────────────────┘
```

## Phased Rollout

### V1 — MVP (Ship by Friday 2/6)

**Goal:** Replace the manual pipeline with a working automated version, even if incomplete.

**What's in:**
- Smartlead webhook → Clay receives positive reply data
- Clay pushes domain to Datagen
- Datagen queries Supabase for all signals
- Datagen LLM processes signals → top 10 + SLED Signal Bullets
- Datagen generates a Notion page with the intel
- Datagen webhooks report URL back to Clay
- Clay sends Slack message to #intent-reports with report link
- Hagel/BDR manually responds with the link in Smartlead

**What's NOT in V1:**
- Starbridge API integration (blocked on Yurii access)
- DM contact card (dependent on SB API)
- Buyer attributes beyond signals (budget, logo, etc.)
- Branded design (needs Nastia alignment)
- Automatic screenshot generation
- Automatic Smartlead reply

**Success criteria:**
- 10 sample accounts processed end-to-end
- Report quality is at least as good as current Gamma output
- End-to-end time < 5 minutes (vs. hours today)
- Hagel can use it without breaking

### V2 — Enriched Reports (Weeks 2–3)

**Goal:** Add buyer attributes and DM info. Make reports genuinely better than Gamma.

**Additions:**
- Starbridge API integration for DM info, budget, logo, location
- Branded report template (Nastia's design → Webflow or Super.so)
- Automatic tier assignment based on account value + signal strength
- Screenshot generation for Slack and email
- Operator context capture (territory, scheduling notes — either auto-extracted from reply text or easy manual input)

**Success criteria:**
- Reports include DM contact cards for Tier 2+
- Budget data appears in reports (most valuable attribute per Justin)
- Branded, consistent look and feel
- BDR feedback: "this is better than what we had"

### V3 — Full Automation + Scale (Weeks 4–6)

**Goal:** Hands-off pipeline that handles 10x campaign volume.

**Additions:**
- Auto-generated relevancy analysis + pitch angle (Tier 3 for qualifying accounts)
- Similar customers section in report
- Mini follow-up sequence in Smartlead after intel delivery
- Multi-timezone operator coverage support
- Tracking dashboard: time-to-response, fulfillment completeness, conversion by tier
- Potential: API endpoint (input = domain → response = poll-able report URL)

**Success criteria:**
- Zero manual steps between positive reply and Slack dispatch
- < 2 minute end-to-end for Tier 1
- < 5 minutes for Tier 2
- Handles Monday's 10x campaign volume without breaking

## Key Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Orchestration | Datagen cloud agents (not Clay-only) | Need LLM processing + Supabase queries + report generation in one pipeline. Clay can't do all of this natively. |
| Report generation | Notion (V1) → Webflow/Super.so (V2) | Notion is fastest to generate programmatically. Webflow gives branding control. {{TBD: final V2 format needs Nastia/Henry alignment}} |
| LLM for signal processing | {{TBD: Claude or Gemini}} | Neil's existing Gemini prompts are a starting point. Claude may be better for structured output. |
| Signal scoring | LLM-based ranking {{UNKNOWN: prompt and criteria not yet designed}} | "Pick top 10" + "determine what lead will care about" = prompt engineering, not rules engine. |
| DM info timing | DM-Later Flow | Decouple intel delivery (fast) from DM lookup (slower, SB API dependent). |

## What Changes for Each Role

### Hagel (Fulfillment Operator)
**Before:** Does everything manually. Single point of failure.
**After V1:** Reviews automated output, adds manual context (territory, scheduling), posts to Smartlead. Still in the loop but not the bottleneck.
**After V3:** Quality control role. Spot-checks reports, handles edge cases, manages BDR questions.

### BDRs
**Before:** Wait for Hagel's Slack posts, then act.
**After:** Same interaction model (#intent-reports), but notifications come faster and reports are richer. No change to their workflow — just better inputs, sooner.

### Kushagra
**Before:** Built the signal infrastructure (Supabase, Slack bots).
**After:** Supabase becomes a programmatic data source for Datagen instead of a Slack-bot-only interface. His signal allocation framework feeds into multi-signal campaigns (workstream 2).

### Henry
**Before:** Manages a brittle engine with timezone risk.
**After:** Has a scalable system with tracking. Can pour gasoline on volume without worrying about fulfillment breaking.

## End Goal (from Onboarding Notes)

> "Make an API where input is a domain, etc, and its response is an ID that, when polled, returns URL/content."

This is the ultimate abstraction: any system (Clay, Smartlead, Slack bot, internal tool) can request an intel report for any domain, and get back a branded, data-rich landing page URL.
