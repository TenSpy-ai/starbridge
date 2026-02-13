# Positive Reply Flow — The Core Workflow

This is the workflow I'm automating. It's the single biggest lever Starbridge can pull right now.

## Current State vs. Future State (Summary)

| Aspect | Current (Manual) | Future (Automated) |
|---|---|---|
| **Detection** | Hagel monitors Smartlead inbox | Smartlead webhook fires automatically |
| **Signal lookup** | Hagel uses Slack bots (endgame-lookup + SB app) | Datagen queries Supabase + SB API directly |
| **Processing** | Hagel feeds CSV into Gemini manually | Datagen feeds signals into LLM, returns top 10 |
| **Report generation** | Hagel uploads to Gamma | Datagen generates branded Notion/Webflow page |
| **Dispatch** | Hagel posts in #intent-reports manually | Clay sends Slack message automatically |
| **Response time** | Hours (Philippines timezone lag) | Minutes |
| **Quality** | Non-deterministic Gamma output, limited data | Branded, deterministic, richer buyer attributes |

## Future State Flow (What I'm Building)

```
STEP 1: DETECTION
Smartlead detects positive reply
  → Fires webhook to Clay (Project Endgame workbook)
  → Clay receives in webhook source column 1
  → {{UNKNOWN: exact webhook payload fields — check Smartlead docs or ask team}}

STEP 2: CLAY → DATAGEN HANDOFF
Clay pushes domain + context to Datagen cloud agent
  → Simultaneously: Clay sends Slack notification to #intent-reports
    ("New positive reply from {Name} at {Company} — intel incoming")

STEP 3: DATAGEN PIPELINE
Datagen cloud agent executes:
  a) Pings Supabase → retrieves ALL intent signals for that domain
  b) Feeds signals into LLM {{TBD: Claude vs. Gemini — Neil's existing Gemini prompts are starting point}} → returns top signals {{UNVERIFIED: source docs say both "top 5" and "top 10" — confirm target count with team}}
     + generates "SLED Signal Bullets" (contextual summaries)
  c) Hits Starbridge API for auxiliary buyer attributes: {{UNKNOWN: requires Yurii to unblock API access}}
     - Decision maker info (name, title, email, phone)
     - Budget data
     - Account logo
     - Location / G-map
     - Other attributes {{UNKNOWN: full attribute list — ask Justin for scope beyond budget}}
  d) Evaluates what's most relevant for this specific lead
     (sorting logic: {{UNKNOWN: "what will the lead care about?" — not yet defined, needs team input}})
  e) Assembles intel report content
  f) Generates branded landing page {{TBD: Notion vs. Super.so vs. Webflow — needs Nastia/Henry alignment}}

STEP 4: DATAGEN → CLAY RETURN
Datagen sends report URL back to Clay via webhook
  → Clay receives in webhook source column 2

STEP 5: SLACK DISPATCH
Clay sends full Slack message to #intent-reports:
  - @BDR — intel is ready for {Name} at {Company}
  - Report link
  - DM contact card (if available)
  - Any context/constraints

STEP 6: BDR RESPONSE
Operator (Hagel) or BDR jumps into Smartlead and replies with:
  1) The intel report link
  2) A screenshot of the report
  3) Offer: "Happy to give you decision maker info on a call"

STEP 7: FOLLOW-UP + CONVERSION
BDR loops in for calls and follow-up sequence
  → If no reply to intel: send DM info + ask for call
  → If reply: book meeting
```

## Decision Points & Forks

### Fork A: Prospect asked for meeting/demo directly
- Skip to scheduling immediately
- Intel report is prepared in parallel ("throw a placeholder on the calendar and have Hagel put together a Gamma" — Henry)

### Fork B: Prospect will forward internally
- Send intel in the **original thread** too (not just separate thread)
- Intel needs to be self-contained and impressive for internal forwarding

### Fork C: DM-Later Flow (New Default as of 2/4)
- Campaign copy says "Want more intel like this?" (not "here's your DM info")
- Intel report goes first, DM info offered on the call
- If no reply after intel → THEN send DMs and ask for a call
- This decouples the time-critical intel delivery from the slower DM lookup

## Open Technical Questions

| Question | Who to Ask | Impact |
|---|---|---|
| What's the exact Smartlead webhook payload structure? | Team / Smartlead docs | Need to know what fields Clay receives |
| Supabase schema: what tables/columns exist for signals? | Kushagra | Core to Datagen's query logic |
| SB API auth: how do we authenticate? What are rate limits? | Yurii | Determines if DG can hit it directly |
| SB API: what's the exact endpoint for DM info per account? | Yurii | Needed for buyer attribute enrichment |
| Report format: Notion vs. Webflow vs. Super.so? | Nastia / Henry | Determines generation pipeline |
| Signal scoring: how do we rank "top 10" from all signals? | Kushagra / team | LLM prompt engineering piece |
| What determines "what the lead will care about"? | Team | Sorting logic for report content |

## V1 MVP vs. Full Vision

### V1 (Ship by Friday 2/7)
- Smartlead webhook → Clay → Datagen
- Datagen queries Supabase for signals
- Datagen uses LLM to pick top signals + generate bullets
- Datagen creates Notion page (simplest to generate)
- URL returns to Clay → Slack notification to #intent-reports
- Hagel/BDR manually responds with the link
- **No SB API integration yet** (blocked on Yurii)
- **No buyer attributes yet** (dependent on SB API)
- ~10 sample accounts to validate

### Full Vision (Weeks 2–6)
- Add SB API for DM info + buyer attributes
- Add branding (Nastia's design → Webflow or Super.so)
- Add automatic screenshot generation
- Add similar customers section in report
- Add mini follow-up sequence in Smartlead after intel delivery
- Add multi-timezone operator coverage
- Potential: API endpoint where input = domain, response = poll-able report URL

## Dependencies & Risks

| Risk | Severity | Mitigation |
|---|---|---|
| SB API access blocked/slow | High | V1 works without it (signals from Supabase only). DM info added later. |
| Report format not aligned with Nastia/Henry | Medium | Start with Notion (simplest), iterate to Webflow after alignment. |
| Supabase schema is more complex than expected | Medium | Kushagra meeting is first priority. |
| Smartlead webhook doesn't fire reliably | Medium | Test with manual triggers first. |
| LLM signal scoring is inconsistent | Low | Iterate on prompts with sample accounts. Neil's Gemini prompts are a starting point. {{UNKNOWN: get Neil's current prompts}} |
| Volume spike on Monday (10x campaign launch) | High | V1 must be live by Friday or manual process handles overflow. |
