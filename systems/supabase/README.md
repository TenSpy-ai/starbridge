# Supabase — System Overview

## ⚠️ V1 CRITICAL BLOCKER

**The Supabase schema is the single biggest V1 blocker.** Without it, Datagen cannot query signals, and the entire automated pipeline is dead. The Kushagra meeting to obtain the schema is the highest-priority onboarding task. Everything in this directory is scaffolding until that meeting happens.

## Role in the Stack

Supabase is the **signal database** — the central store for intent signals that have been extracted from Starbridge's platform and aligned to accounts/domains. It's built and maintained by Kushagra.

Supabase answers the question: **"What procurement signals exist for this company?"**

It does NOT store buyer attributes (DM info, budget, logo, etc.) — those come from the Starbridge API/platform. The two data sources are complementary:

| Data Source | What It Has | Key Query |
|---|---|---|
| **Supabase** (Kushagra) | Intent signals aligned to accounts | "Pull all signals for X domain" |
| **Starbridge API** (Yurii) | Buyer attributes, DM info, meeting docs | "For this SLED account, give me the DM info" |

## How It's Accessed Today (Current State)

Two Slack-based interfaces, both used by Hagel in the manual fulfillment process:

### 1. endgame-lookup (Kushagra's Slack bot)
- Hagel inputs a domain
- Bot pings Supabase
- Returns: all intent signals for that account/domain
- This is the primary signal retrieval mechanism today

### 2. Starbridge Slack app
- Separate from endgame-lookup
- Pulls data from the Starbridge platform (not Supabase directly)
- Returns: custom data including DM info
- Hagel uses BOTH tools together to assemble intel

## How It Will Be Accessed (Future State)

Datagen cloud agents will query Supabase directly via API — no Slack bot intermediary.

```
Smartlead positive reply → Clay → Datagen
  │
  ├── Datagen queries Supabase API directly
  │     → Returns all signals for the domain
  │     → Datagen feeds into LLM for ranking/summarization
  │
  └── Datagen queries Starbridge API (separate)
        → Returns buyer attributes, DM info
```

## What "Signals" Are

From the onboarding context, signals are Starbridge-sourced intelligence items that indicate procurement intent. They're extracted from Starbridge's data (board meetings, contracts, purchases, RFPs) and stored in Supabase aligned to account domains.

Examples of signal types {{UNVERIFIED: inferred from docs — need Kushagra to confirm the full taxonomy}}:
- Contract expiring for a specific tool category (e.g., LMS)
- Board meeting discussion mentioning a product category
- Budget allocation or change
- New RFP posted
- Purchase order issued
- Leadership change (new CIO, superintendent, etc.)
- Grant/funding event

Each signal appears to have:
- An association to an account/domain
- Some kind of content or summary
- {{UNKNOWN: what other fields exist per signal — timestamp? source? category? relevance score?}}

## Signal Volume

- Starbridge currently has **more signals than prospects** (412K+ prospects)
- Goal: send at least one signal per prospect
- For the intel report pipeline: retrieve ALL signals for a domain, then use LLM to pick the top 5–10

## CSV Export Capability

The onboarding notes mention "intent signal bucket CSV export (corresponds to accounts)" — suggesting Supabase data can be exported as CSV, which is how Hagel currently gets signal data into Gemini for processing.

## What Kushagra Has Built

- The Supabase signal database itself
- The endgame-lookup Slack bot (queries Supabase by domain)
- Signal allocation framework for multi-signal campaigns (assigning which signals go to which prospects)
- {{UNKNOWN: any additional tooling, views, or functions in Supabase}}

## Key Dependencies

| Dependency | Impact | Status |
|---|---|---|
| Kushagra meeting | Need schema walkthrough to build Datagen queries | {{UNKNOWN: pending meeting}} |
| Supabase access | Need direct access (not just via Slack bot) for Datagen integration | {{UNKNOWN: pending — requested during onboarding}} |
| Signal-to-domain mapping | Core to the pipeline — if mappings are incomplete, reports will have gaps | {{UNKNOWN: coverage/completeness}} |

## Things to Learn from Kushagra

Priority order:

1. **Schema**: Tables, columns, relationships — see [schema.md](./schema.md)
2. **Query patterns**: How to pull all signals for a domain, how to filter by type/date/relevance — see [queries.md](./queries.md)
3. **API access**: Connection string, auth method, any RLS (Row Level Security) policies
4. **Signal taxonomy**: Full list of signal types and what fields each has
5. **Data freshness**: How often does new data flow in from Starbridge? Is it real-time, daily, batch?
6. **Signal allocation logic**: How does his framework assign signals to prospects for multi-signal campaigns? (This affects what signals have already been "used" when a positive reply comes in)
7. **endgame-lookup bot**: How it works internally (useful as a reference for Datagen queries)
8. **Edge cases**: Domains with no signals, domains with hundreds of signals, signal deduplication
