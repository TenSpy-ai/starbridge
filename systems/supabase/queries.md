# Supabase Key Queries

{{UNKNOWN: actual SQL queries — everything below uses hypothesized table/column names. Replace with real schema after Kushagra meeting. See [schema.md](./schema.md) for the schema template.}}

## Query 1: All Signals for a Domain (Core Pipeline Query)

**Used by**: Datagen cloud agent, immediately after receiving a domain from Clay
**Frequency**: Every positive reply (critical path)
**Purpose**: Retrieve every signal associated with a domain so the LLM can rank and select the top 5–10

```sql
-- {{UNKNOWN: actual table and column names}}
-- This is the fundamental query the entire pipeline depends on

SELECT *
FROM signals  -- {{UNKNOWN: actual table name}}
WHERE domain = 'acmegov.com'  -- {{UNKNOWN: actual column name for domain}}
ORDER BY date DESC;  -- {{UNKNOWN: ordering — by date? by relevance_score? both?}}
```

**Expected output**: All signal records for that domain — could be 1, could be 100+.

**What Datagen does with the result**:
1. Feeds all signals into LLM
2. LLM ranks and selects top 5–10
3. LLM generates "SLED Signal Bullets" (contextual summaries)
4. Top signals + bullets go into the intel report

**Edge cases to handle**:
- Domain has 0 signals → {{TBD: skip report generation? generate a minimal report? notify operator?}}
- Domain has 100+ signals → LLM context window management (may need pre-filtering or pagination)
- Domain doesn't exist in the database → same as 0 signals

## Query 2: Signals by Type for a Domain

**Used by**: Future — multi-signal campaign logic, Tier 3 report generation
**Purpose**: Filter signals by category when building specialized reports or allocating signals to sequence positions

```sql
-- {{UNKNOWN: actual table and column names}}

SELECT *
FROM signals
WHERE domain = 'acmegov.com'
  AND signal_type = 'contract_expiration'  -- {{UNKNOWN: actual type values}}
ORDER BY date DESC;
```

**Signal types to query for** {{UNKNOWN: full list — hypothesized from docs}}:
- `contract_expiration` — contract expiring for a tool category
- `board_mention` — board meeting discussion of a product/category
- `budget_event` — budget allocation, change, or approval
- `rfp_posted` — new RFP opportunity
- `purchase_order` — purchase order issued
- `leadership_change` — new CIO, superintendent, etc.
- `grant_funding` — grant or funding event

## Query 3: Signal Count per Domain

**Used by**: Reporting, tier assignment logic, campaign planning
**Purpose**: Quick check of signal density — helps determine Tier 1 vs. Tier 2 vs. Tier 3 treatment

```sql
-- {{UNKNOWN: actual table and column names}}

SELECT domain, COUNT(*) as signal_count
FROM signals
WHERE domain = 'acmegov.com'
GROUP BY domain;
```

## Query 4: Recent Signals (Time-Bounded)

**Used by**: Intel report generation — fresher signals are more valuable
**Purpose**: Prioritize recent signals over stale ones

```sql
-- {{UNKNOWN: actual table and column names, date column}}

SELECT *
FROM signals
WHERE domain = 'acmegov.com'
  AND date >= NOW() - INTERVAL '90 days'  -- {{TBD: what time window defines "recent"?}}
ORDER BY date DESC;
```

## Query 5: Signals Already Sent to a Prospect

**Used by**: Multi-signal campaign logic (Kushagra's framework)
**Purpose**: When a positive reply comes in, know which signals the prospect has already seen — so the intel report surfaces NEW information

```sql
-- {{UNKNOWN: this query depends on whether signal allocation is tracked in Supabase or Clay}}
-- If in Supabase:

SELECT s.*
FROM signals s
JOIN signal_allocations sa ON s.id = sa.signal_id  -- {{UNKNOWN: actual join}}
WHERE sa.prospect_email = 'john@acmegov.com'
  AND sa.sent = true;
```

**Why this matters**: If a prospect replied to email 3 of a multi-signal sequence, they've already seen 3 signals. The intel report should:
1. Acknowledge the signal from email 3 (what they responded to)
2. Reference signals from emails 1–2 (what they've seen)
3. Prioritize NEW signals they haven't seen

## Query 6: Top Domains by Signal Density

**Used by**: Campaign planning, account prioritization
**Purpose**: Find accounts with the richest signal data (best candidates for outbound)

```sql
-- {{UNKNOWN: actual table and column names}}

SELECT domain, COUNT(*) as signal_count
FROM signals
GROUP BY domain
ORDER BY signal_count DESC
LIMIT 100;
```

## Supabase API Patterns (For Datagen)

Datagen will query Supabase via the REST API (PostgREST) or the Supabase JS/Python client. Examples using the REST API:

### REST API (PostgREST)

```bash
# {{UNKNOWN: actual Supabase URL and table name}}

# All signals for a domain
curl 'https://YOUR_PROJECT.supabase.co/rest/v1/signals?domain=eq.acmegov.com' \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY"

# Signals by type
curl 'https://YOUR_PROJECT.supabase.co/rest/v1/signals?domain=eq.acmegov.com&signal_type=eq.contract_expiration' \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY"

# Signal count
curl 'https://YOUR_PROJECT.supabase.co/rest/v1/signals?domain=eq.acmegov.com&select=count' \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Prefer: count=exact"
```

### Python Client (For Datagen Cloud Agents)

```python
# {{UNKNOWN: actual table and column names}}

from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# All signals for a domain
result = supabase.table('signals') \
    .select('*') \
    .eq('domain', 'acmegov.com') \
    .order('date', desc=True) \
    .execute()

signals = result.data
```

## Performance Considerations

| Concern | Mitigation |
|---|---|
| High-signal domains (100+ records) | {{TBD: pre-filter by date/type before sending to LLM, or send all and let LLM handle?}} |
| Query latency on critical path | Index on `domain` column is essential — {{UNKNOWN: confirm index exists}} |
| Concurrent queries (during volume spikes) | Supabase handles connection pooling, but {{UNKNOWN: what's the project's tier/limits?}} |
| Rate limiting | {{UNKNOWN: Supabase rate limits on the current plan}} |

## Post-Meeting Action Items

After the Kushagra meeting, update this file:
- [ ] Replace all hypothesized table/column names with actual names
- [ ] Add any stored procedures or database functions available
- [ ] Document the exact Supabase client setup for Datagen (URL, key, any config)
- [ ] Test Query 1 (all signals for a domain) against real data and document response shape
- [ ] Determine how signal allocation is tracked (Supabase vs. Clay) — affects Query 5
- [ ] Document any filtering or ordering that endgame-lookup bot applies (it's a working reference implementation)
