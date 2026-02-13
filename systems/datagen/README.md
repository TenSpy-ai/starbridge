# Datagen — System Overview

## Role in the Stack

Datagen is the **orchestration and processing layer** between Clay and all the data sources. It handles the complex multi-step logic that Clay can't do natively: querying Supabase, running LLM processing, hitting the Starbridge API, assembling report content, generating the intel report page, and sending the result back to Clay.

Think of it as the "brain" of the pipeline. Clay is the router; Datagen is the processor.

## Why Datagen (Not Clay-Only)

Clay is great at row-level enrichment, webhook routing, and Slack dispatch. But the positive reply pipeline requires:

| Requirement | Why Clay Can't Do It Alone |
|---|---|
| Query Supabase for all signals by domain | Clay doesn't have native Supabase integration |
| Feed signals into an LLM and get structured output | Clay's AI columns are limited to single-prompt, single-response — not multi-step reasoning |
| Hit the Starbridge API with custom auth | Possible via Clay HTTP requests, but chaining multiple API calls with conditional logic is clunky |
| Rank and select top signals from a variable-length list | Requires dynamic logic, not static column formulas |
| Generate a branded Notion/Webflow page | Clay doesn't generate external pages |
| Handle async processing (pipeline takes seconds, not milliseconds) | Clay webhooks expect synchronous responses |

Datagen cloud agents solve all of these as a single orchestrated pipeline.

## What Datagen Is

Datagen is Jeremy's MCP-as-a-Service platform that converts AI conversations into production APIs. For Starbridge, it provides **cloud agents** — serverless functions that execute multi-step workflows on demand.

Key capabilities used in this pipeline:
- **Execute Python code** with access to external APIs (Supabase, Starbridge, LLMs)
- **Deploy as API endpoints** that Clay can call via HTTP request and receive results via webhook
- **MCP server integration** for connecting to tools and services
- **LLM orchestration** for signal processing and content generation

## Datagen in the Pipeline

```
Clay (receives positive reply webhook from Smartlead)
  │
  │  HTTP request with domain + context
  │
  ▼
Datagen Cloud Agent
  │
  ├── Step 1: Query Supabase
  │     → All intent signals for this domain
  │     → {{UNKNOWN: exact Supabase query — depends on schema from Kushagra}}
  │
  ├── Step 2: LLM Signal Processing
  │     → Input: all signals for the domain
  │     → Output: top 5-10 ranked signals + "SLED Signal Bullets"
  │     → {{TBD: Claude vs. Gemini — Neil's Gemini prompts are starting point}}
  │     → Logic includes: "what will the lead care about?" ranking
  │
  ├── Step 3: Query Starbridge API (V2)
  │     → Buyer attributes: DM info, budget, logo, location
  │     → {{UNKNOWN: blocked on Yurii API access}}
  │
  ├── Step 4: Evaluate & Assemble
  │     → Determine most relevant content for the report
  │     → Sorting logic: {{UNKNOWN: criteria not yet defined}}
  │     → Assemble: signals + bullets + buyer attributes + DM card
  │
  ├── Step 5: Generate Intel Report
  │     → Create branded landing page
  │     → {{TBD: Notion vs. Super.so vs. Webflow}}
  │     → Output: URL to the report
  │
  └── Step 6: Webhook Back to Clay
        → Payload: report URL (+ metadata: signal count, tier, DM info)
        → Clay receives in webhook source column 2
        → Clay triggers Slack dispatch to #intent-reports
```

## Cost

| Period | Cost | Notes |
|---|---|---|
| Month 1 | $50 | {{UNVERIFIED: from onboarding notes — confirm current Datagen pricing}} |
| Month 2+ | $500 | {{UNVERIFIED: same source}} |

Approved as a trial expense. Need to set up account and expense.

## Setup Status

{{UNKNOWN: current setup progress — from onboarding notes:}}
- [ ] Buy + expense Claude Max account ($200) — prerequisite for some Datagen features
- [ ] Set up Datagen account ($50 expense)
- [ ] Configure Datagen cloud agent for the pipeline
- [ ] Update Henry on Datagen timeline (was scheduled for Thursday)
- [ ] Deadline: Tuesday 2/17

## Technical Implementation

### Agent Architecture

The Datagen cloud agent for this pipeline will be a **deployed Python endpoint** that:

1. Receives an HTTP POST from Clay with the domain and positive reply context
2. Executes the multi-step pipeline (Supabase → LLM → SB API → report generation)
3. Sends the result back to Clay via webhook

### Input (From Clay)

```json
{
  "domain": "acmegov.com",
  "prospect_name": "John Smith",
  "prospect_email": "john@acmegov.com",
  "reply_text": "This looks interesting...",
  "campaign_id": "camp_abc123",
  "sequence_step": 2
}
```
{{UNVERIFIED: input schema above is designed based on pipeline needs — actual schema depends on what Clay sends, which depends on what Smartlead webhook provides}}

### Output (Back to Clay)

```json
{
  "report_url": "https://notion.so/starbridge-intel/acmegov-abc123",
  "signal_count": 8,
  "top_signals_used": 5,
  "tier": 1,
  "dm_info": null,
  "processing_time_seconds": 12
}
```
{{UNVERIFIED: output schema above is designed — will be refined during build}}

### Error Handling

The agent needs to handle:
- Domain with 0 signals in Supabase → {{TBD: skip? minimal report? notify operator?}}
- Supabase query timeout or failure → retry once, then fail gracefully with notification
- LLM processing failure → fall back to raw signal list without ranking
- SB API unavailable (expected in V1) → proceed without buyer attributes
- Report generation failure → send signals via Slack text instead of a page URL
- Extremely high signal count (100+) → pre-filter by date/relevance before LLM

## Datagen End Goal

From the onboarding notes:

> "Make an API where input is a domain, etc, and its response is an ID that, when polled, returns URL/content."

This is the ultimate abstraction: any system can request an intel report by domain and get back a branded, data-rich landing page URL. Datagen makes this possible because it can be deployed as a persistent API endpoint, not just a one-off script.

## Relationship to Kushagra's Claude Code

From onboarding notes: Jeremy should "join Kushagra's Claude Code." This suggests Kushagra is also using Claude Code for development. Coordination needed:
- {{UNKNOWN: what Kushagra has built in Claude Code — is it related to the Slack bots? Signal allocation? Something else?}}
- Avoid duplicating work — if Kushagra has Supabase query logic already built, reference it
- Datagen agents may eventually replace some of what Kushagra's Slack bots do (endgame-lookup becomes a Datagen query instead)

## Files in This Directory

- **[agents.md](./agents.md)** — Detailed spec for the Datagen cloud agents in the pipeline
