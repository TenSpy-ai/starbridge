# Supabase Schema

{{UNKNOWN: entire schema — this file is structured as a template to fill in during/after the Kushagra meeting. Everything below is scaffolding based on what we know the system needs to contain.}}

## Connection Details

| Detail | Value |
|---|---|
| Supabase project URL | {{UNKNOWN: get from Kushagra}} |
| API key (anon/service) | {{UNKNOWN: get from Kushagra — determine which key Datagen should use}} |
| Auth method | {{UNKNOWN: anon key? service role key? JWT? RLS policies?}} |
| Region | {{UNKNOWN}} |

## Known Data Requirements

Based on the pipeline, Supabase must store at minimum:

1. **Intent signals** — the core records (contract expirations, board mentions, budget events, etc.)
2. **Account/domain associations** — linking signals to company domains
3. **Signal metadata** — enough to rank, filter, and display signals in reports

## Expected Tables

{{UNKNOWN: actual table names — the structure below is hypothesized based on usage patterns described in onboarding}}

### Signals Table {{UNKNOWN: actual table name}}

The core table. Each row is one intent signal.

| Column | Type | Description | Confirmed? |
|---|---|---|---|
| id | uuid / serial | Primary key | {{UNKNOWN}} |
| domain | text | Company domain the signal relates to (e.g., "acmegov.com") | {{UNVERIFIED: domain is the lookup key used by endgame-lookup bot — confirm column name}} |
| signal_type | text / enum | Category: contract_expiration, board_mention, budget_event, rfp, purchase_order, leadership_change, etc. | {{UNKNOWN: what types exist and how they're stored}} |
| content / summary | text | The signal content or description | {{UNKNOWN: is this raw text? structured JSON? a summary?}} |
| source | text / reference | Where the signal came from in Starbridge (meeting ID, contract ID, etc.) | {{UNKNOWN}} |
| date / timestamp | timestamp | When the signal was detected or when the underlying event occurred | {{UNKNOWN: is there a detection date vs. event date distinction?}} |
| relevance_score | numeric | Pre-computed relevance score (if any) | {{UNKNOWN: does Kushagra pre-score signals or is that done at query time?}} |
| ... | ... | ... | Additional columns TBD |

### Accounts Table {{UNKNOWN: does a separate accounts table exist or are accounts just domains on the signals table?}}

| Column | Type | Description | Confirmed? |
|---|---|---|---|
| domain | text | Primary key or unique identifier | {{UNKNOWN}} |
| account_name | text | Human-readable company name | {{UNKNOWN}} |
| tier | text / enum | T0–T3 classification | {{UNKNOWN: is tier stored here or elsewhere?}} |
| ... | ... | ... | TBD |

### Signal Allocation Table {{UNKNOWN: does this exist? Kushagra is building signal allocation for multi-signal campaigns — may be stored in Supabase or in Clay}}

| Column | Type | Description | Confirmed? |
|---|---|---|---|
| signal_id | reference | Which signal | {{UNKNOWN}} |
| prospect_id / email | reference | Which prospect it was assigned to | {{UNKNOWN}} |
| campaign_id | text | Which campaign / sequence | {{UNKNOWN}} |
| sequence_position | integer | Which email in the sequence (1, 2, 3...) | {{UNKNOWN}} |
| sent | boolean | Whether this signal has been sent | {{UNKNOWN}} |

## Relationships

```
{{UNKNOWN: actual relationships — hypothesized below}}

accounts (1) ──→ (many) signals
  └── domain is the join key

signals (1) ──→ (many) signal_allocations  {{if this table exists}}
  └── signal_id is the join key
```

## Row Level Security (RLS)

{{UNKNOWN: are there RLS policies? Datagen will need appropriate access — service role key bypasses RLS, anon key respects it}}

## Indexes

{{UNKNOWN: what indexes exist? For pipeline performance, we need fast lookups on:}}
- `domain` (primary query pattern: "all signals for domain X")
- `signal_type` (if filtering by type)
- `date` (if filtering by recency)

## Data Volume

| Metric | Value |
|---|---|
| Total signal records | {{UNKNOWN}} |
| Signals per account (average) | {{UNKNOWN: but note "more signals than prospects" means likely >1 per account on average}} |
| Signals per account (max) | {{UNKNOWN: matters for LLM processing — if an account has 500 signals, we need to handle that}} |
| Data growth rate | {{UNKNOWN: how often are new signals ingested?}} |

## Data Freshness

| Question | Answer |
|---|---|
| How does data get into Supabase from Starbridge? | {{UNKNOWN: batch ETL? real-time? manual export?}} |
| How often is new data ingested? | {{UNKNOWN}} |
| Is there a lag between Starbridge detecting a signal and it appearing in Supabase? | {{UNKNOWN}} |
| Are old/expired signals cleaned up or do they persist? | {{UNKNOWN: e.g., does a contract expiration signal stay forever or get archived?}} |

## Fill-In Checklist (For Kushagra Meeting)

- [ ] Get Supabase project URL and appropriate API key
- [ ] List all tables with their actual names
- [ ] Document columns per table with types
- [ ] Understand the domain-based lookup pattern (exact query)
- [ ] Clarify signal types: full list + how they're categorized
- [ ] Ask about signal allocation: where is it tracked?
- [ ] Understand data flow: Starbridge → Supabase pipeline
- [ ] Ask about RLS policies and which key Datagen should use
- [ ] Get a sense of data volume and growth
- [ ] Ask about edge cases: domains with 0 signals, domains with 100+ signals
- [ ] Understand if/how signals are deduplicated
- [ ] Ask if there are any stored procedures or database functions we can call
