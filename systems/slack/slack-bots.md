# Slack Bots — endgame-lookup & Starbridge App

## Overview

Two Slack-based tools are used in the current manual fulfillment process. Hagel uses **both** to assemble intel for each positive reply. They serve different purposes and pull from different data sources.

In the future state, Datagen replaces both by querying Supabase and the Starbridge API directly. However, these bots remain useful as:
- Reference implementations (how Kushagra structured queries)
- Fallback tools (if Datagen pipeline is down)
- Discovery tools (for ad-hoc research outside the automated flow)

---

## Bot 1: endgame-lookup

**Built by**: Kushagra
**Data source**: Supabase (Kushagra's signal database)
**Channel**: {{UNKNOWN: is it used in a specific channel, or does it work via DM / any channel?}}

### What It Does

Takes a domain as input, queries Supabase, and returns all intent signals associated with that domain.

### How Hagel Uses It

1. Hagel identifies a positive reply in Smartlead
2. Takes the replying company's domain
3. Inputs the domain into endgame-lookup in Slack
4. Bot returns: all intent signals aligned to that account
5. Hagel takes this output and feeds it into Gemini for summarization

### Example Interaction

{{UNKNOWN: exact command syntax and response format — below is inferred from onboarding notes}}

```
Hagel:   /endgame-lookup acmegov.com

Bot:     Found 8 signals for acmegov.com:
         1. Contract expiration: LMS platform license expiring 2026-06-30 ($250K)
         2. Board meeting: Discussion of student information system modernization (2026-01-15)
         3. Budget: $1.2M allocated for IT infrastructure upgrades (FY2026)
         ...
```

### Technical Details

{{UNKNOWN: most implementation details — questions for Kushagra:}}

| Question | Why It Matters |
|---|---|
| What's the Slack command syntax? (`/endgame-lookup`? `@endgame-lookup`? plain text?) | Need to understand the UX if we keep it as a fallback |
| What's the exact Supabase query it runs? | This is the query Datagen needs to replicate |
| What format does it return results in? (text? JSON? file attachment? CSV?) | The output format tells us how signals are structured |
| Does it do any filtering/ranking, or does it return everything? | If it returns raw, all ranking is done downstream (Gemini/LLM) |
| Does it handle domains with 0 signals? | Need to know the edge case behavior |
| Is there rate limiting or queuing? | Matters if multiple positive replies come in simultaneously |
| Where does the bot run? (Slack app? Lambda? Kushagra's infra?) | Matters for reliability and uptime |

### Relationship to Datagen

endgame-lookup proves the core query works: domain → Supabase → signals. Datagen replicates this query programmatically without the Slack intermediary.

| endgame-lookup | Datagen Equivalent |
|---|---|
| Slack command input | HTTP POST from Clay with domain |
| Supabase query | Same query, via Supabase REST API or Python client |
| Returns signal list to Slack | Returns signals to LLM for processing, then to report generator |

**Key**: Get the exact Supabase query from Kushagra. If endgame-lookup works, Datagen should use the same query logic as its starting point.

---

## Bot 2: Starbridge Slack App

**Built by**: {{UNKNOWN: Starbridge internal team? Kushagra?}}
**Data source**: Starbridge platform (dashboard.starbridge.ai)
**Channel**: {{UNKNOWN: same question as endgame-lookup}}

### What It Does

Queries the Starbridge platform for buyer-level data. This is the tool that returns **decision maker info** and other buyer attributes that Supabase doesn't have.

### How Hagel Uses It

1. After getting signals from endgame-lookup, Hagel uses the Starbridge app for the "other half" of the intel
2. Queries for DM info: "for this SLED account, given these minutes, give me the DM info"
3. Returns: name, title, email, phone for the relevant public-sector decision maker
4. Also returns: other custom data from the platform (buyer attributes, meeting context, etc.)

### Example Interaction

{{UNKNOWN: exact command syntax and response format — below is inferred from the Slack observations and onboarding notes}}

```
Hagel:   /starbridge lookup acmegov.com

Bot:     Buyer: ACME Government Solutions
         Type: School District
         Location: Austin, TX
         
         Decision Maker:
         - Name: Holly Varner
         - Title: Director of Special Education
         - Email: hvarner@acmegov.com
         - Phone: (512) 555-0147
         
         Recent Meetings: 3 in last 90 days
         Active Contracts: 2 expiring in 2026
```

### Technical Details

{{UNKNOWN: implementation details — questions for Kushagra/Yurii:}}

| Question | Why It Matters |
|---|---|
| What's the command syntax? | Fallback usage |
| What Starbridge API endpoints does it call? | These are the same endpoints Datagen needs for V2 |
| How does it identify the decision maker? | The DM identification logic is critical — is it rule-based or AI-based? |
| Does it take the domain and map it to a Starbridge buyer, or does it need a buyer ID? | Domain → buyer mapping is a pipeline requirement |
| What's the response format? | Tells us what data fields are available |
| Does it use the public API keys from `/settings/api-keys` or internal auth? | Affects whether Datagen can replicate the auth |
| Is this the same Starbridge app listed in platform integrations (Slack integration)? | Clarifies whether it's a custom bot or a native platform feature |

### Relationship to Datagen

The Starbridge Slack app proves that buyer attributes + DM info can be queried programmatically. Datagen's V2 replicates this without Slack.

| Starbridge App | Datagen Equivalent (V2) |
|---|---|
| Slack command input | Datagen agent Step 3 (query SB API) |
| Queries Starbridge platform | Same endpoints via direct API call |
| Returns DM info + buyer attrs to Slack | Returns data to Datagen for report assembly |

**Key**: Understanding which Starbridge API endpoints this bot calls gives us the exact endpoints Datagen needs for V2. This may be the fastest path to answering the "where does DM info come from?" question — inspect the bot's code rather than reverse-engineering the API.

---

## Both Bots Together (Current Hagel Workflow)

```
Domain from positive reply
  │
  ├──→ endgame-lookup (Supabase)
  │      Returns: Intent signals
  │
  └──→ Starbridge Slack app (SB platform)
         Returns: DM info, buyer attributes
  
  Combined output → Gemini → Gamma report → #intent-reports
```

In the future state, Datagen replaces both bots + Gemini + Gamma in a single pipeline:

```
Domain from positive reply
  │
  └──→ Datagen cloud agent
         ├── Queries Supabase (replaces endgame-lookup)
         ├── Queries SB API (replaces Starbridge app)
         ├── LLM processing (replaces Gemini)
         └── Report generation (replaces Gamma)
```

## Preservation Strategy

Even after Datagen is live, keep both bots active:

| Reason | Detail |
|---|---|
| **Fallback** | If Datagen is down, Hagel can revert to manual process using these bots |
| **Discovery** | BDRs or Henry may want to do ad-hoc research on a domain outside the automated flow |
| **Validation** | Cross-check Datagen output against bot output during testing |
| **Kushagra's tooling** | He built them, he maintains them, they serve his other use cases (signal allocation, etc.) |

Don't break or deprecate these bots — just make sure Datagen doesn't depend on them.
