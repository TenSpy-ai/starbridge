# Agent Architecture — Intel Report Pipeline

## Pattern: Orchestrator + Specialized Subagents

A single orchestrator coordinates the 19-step pipeline, delegating parallel work and LLM generation to subagents. Deterministic steps (validation, persistence, assembly) stay in the orchestrator.

```
Main Orchestrator (Opus)
│  Owns: state, phase gating, branching, retry logic
│  Steps: s0, s1, s4, s5, s12, s13, s14, s15, s16
│
├─ Subagent: Search Strategist (Sonnet)
│  Step: s2 — LLM analysis → SEARCH_STRATEGY
│
├─ Subagent Group A: Discovery (3x Sonnet, parallel)
│  Step s3a — starbridge_opportunity_search (primary keywords)
│  Step s3b — starbridge_opportunity_search (alternate keywords)
│  Step s3c — starbridge_buyer_search (buyer type)
│
├─ Subagent Group B-Intel (2x Sonnet, parallel)
│  Step s6 — 4 Starbridge API calls on featured buyer
│  Step s7 — 2 API calls per secondary buyer
│
├─ Subagent Group B-Generate (4x Sonnet/Opus, parallel)
│  Step s8  — Executive Summary (Sonnet)
│  Step s9  — Featured Buyer Section (Opus — most complex)
│  Step s10 — Secondary Buyer Cards (Sonnet)
│  Step s11 — Starbridge CTA (Sonnet)
│
└─ Skill: SLED Signal Formatting
   Invoked by s8, s9, s10 for consistent bullet formatting
```

## Why This Split

### Orchestrator owns sequential/stateful steps

Steps s0, s1, s4, s5, s12, s13, s14, s15, s16 are either:
- **Validation** (s0, s1, s14) — need full pipeline context for branching decisions
- **Logic** (s4, s13) — merge data from multiple sources, require orchestrator state
- **Persistence** (s5, s16) — write to SQLite, need all accumulated data
- **Template** (s12) — pure string substitution, no LLM needed
- **External API** (s15) — Notion publish, needs orchestrator to handle failure gracefully

These run sequentially in the orchestrator's context window. No subagent overhead.

### s2 gets its own subagent

The strategy LLM call is self-contained: inputs in (company, domain, prior runs), structured JSON out (SEARCH_STRATEGY). Isolating it keeps the orchestrator context lean — the strategy prompt is ~500 tokens, and the orchestrator only needs the output, not the reasoning.

### Group A: 3 parallel discovery subagents

s3a, s3b, s3c are independent API calls with no shared state. Running them as parallel subagents means wall-clock time = max(s3a, s3b, s3c) ≈ 5s, not sum ≈ 15s.

Each subagent:
1. Takes search parameters from SEARCH_STRATEGY
2. Calls one Starbridge API endpoint
3. Extracts and returns structured results
4. No LLM reasoning needed — Sonnet is sufficient

### Group B splits into two waves

**Wave 1 — Intel (s6, s7):** Fetch enrichment data via Starbridge API. Parallel — s6 and s7 query different buyers.

**Wave 2 — Generate (s8-s11):** LLM generation that depends on Wave 1 outputs. s9 needs FEAT_PROFILE/FEAT_CONTACTS from s6. s10 needs SEC_PROFILES/SEC_CONTACTS from s7. So Wave 2 can't start until Wave 1 completes.

Within Wave 2, s8/s9/s10/s11 are independent and run in parallel.

s12 (Footer) is deterministic — the orchestrator handles it inline, no subagent.

### Validation loop stays in orchestrator

s14 needs access to:
- Source data from s6 (FEAT_PROFILE, FEAT_CONTACTS, etc.)
- Assembled report from s13 (REPORT_MARKDOWN)
- The branching decision: retry s11 or proceed

Only the orchestrator has all this context. The retry loop (s14 → s11 → s13 → s14) is coordinated by the orchestrator, re-spawning the s11 subagent with feedback.

## Execution Timeline

```
Phase I-II:   Orchestrator validates inputs, loads SQLite context
              s0 → s1 (sequential, ~2s)

Phase III:    Subagent: Search Strategist
              s2 (LLM, ~3s)

Phase IV:     Subagent Group A (parallel)
              s3a ─┐
              s3b ─┼─ (~5s wall-clock)
              s3c ─┘

Phase V:      Orchestrator ranks buyers, persists discovery
              s4 → s5 (sequential, ~5s)

Phase VI-A:   Subagent Group B-Intel (parallel)
              s6 ─┐
              s7 ─┘─ (~10-30s, bottleneck = s6's AI chat call)

Phase VI-B:   Subagent Group B-Generate (parallel)
              s8  ─┐
              s9  ─┤
              s10 ─┼─ (~5-10s wall-clock)
              s11 ─┘
              s12: orchestrator inline (~0s)

Phase VII:    Orchestrator assembles, validates, publishes, saves
              s13 → s14 → (retry s11?) → s15 → s16 (sequential, ~5-10s)

Total: ~35-65s (vs ~90-120s sequential)
Bottleneck: s6's starbridge_buyer_chat call (10-30s)
```

## Model Selection

| Component | Model | Rationale |
|---|---|---|
| Orchestrator | Opus | Complex branching, state management, 7-phase coordination |
| s2 (Strategy) | Sonnet | Structured output, well-defined task |
| s3a-c (Discovery) | Sonnet | API call + field extraction, no complex reasoning |
| s6-s7 (Intel) | Sonnet | API calls, data formatting |
| s8 (Exec Summary) | Sonnet | Short, templated output |
| s9 (Featured Section) | Opus | Most complex generation — 4 sub-sections, signal analysis, contact selection |
| s10 (Secondary Cards) | Sonnet | Compact, repeatable card format |
| s11 (CTA) | Sonnet | Personalized but formulaic |
| s12 (Footer) | N/A | Pure template — deterministic code, no LLM |
| s14 (Validation) | Sonnet | 3 LLM checks are judgment calls, not complex reasoning |

## Tools Required

```
MCP Servers / Tool Integrations:

Starbridge API (s3a, s3b, s3c, s6, s7)
├── starbridge_opportunity_search
├── starbridge_buyer_search
├── starbridge_buyer_profile
├── starbridge_buyer_contacts
└── starbridge_buyer_chat

SQLite (s1, s5, s16)
├── sqlite_query
└── sqlite_insert

Notion MCP (s15)
└── mcp_Notion_notion_create_pages

System
└── CURRENT_DATE (s12)
```

All tools are accessed via Datagen SDK: `client.execute_tool(tool_alias, params)`.

## Deterministic vs. LLM Steps

| Step | Type | Implementation |
|---|---|---|
| s0 | Webhook parse | Code — validate JSON fields |
| s1 | Validate + SQLite | Code — field checks + SQL query |
| s2 | LLM | Subagent — strategy analysis |
| s3a-c | API call | Subagents — Starbridge search |
| s4 | Logic + LLM | Orchestrator — deterministic scoring + LLM tiebreak |
| s5 | SQLite | Code — INSERT statements |
| s6-s7 | API calls | Subagents — Starbridge enrichment |
| s8-s11 | LLM | Subagents — content generation |
| s12 | Template | Code — string interpolation |
| s13 | Logic | Code — concatenation + cleanup |
| s14 | Validate + LLM | Orchestrator — 5 code checks + 3 LLM checks |
| s15 | API call | Code — Notion MCP tool call |
| s16 | SQLite + Logic | Code — UPDATE statement + JSON response |

## Error Handling Strategy

### Graceful degradation by severity

| Severity | Action | Example |
|---|---|---|
| **STOP** | Abort pipeline, return error JSON | s0: missing required fields |
| **DEGRADE** | Continue with reduced quality, note in metadata | s6: AI chat timeout → no FEAT_AI_CONTEXT |
| **SKIP** | Omit section, no error | s7: no secondary buyers → skip s10 |

### Retry policy

- **API calls** (s3a-c, s6, s7, s15): Retry once on timeout. If still fails, degrade.
- **LLM generation** (s8-s11): No retry unless s14 validation fails. s11 retries once max via validation loop.
- **SQLite** (s1, s5, s16): No retry. Persistence is non-blocking — pipeline continues on failure.

### Timeout budget

| Step | Timeout | Rationale |
|---|---|---|
| s3a-c | 10s each | API search, usually <5s |
| s6 (buyer_chat) | 35s | Known bottleneck: 10-30s |
| s6 (other 3 calls) | 10s each | Profile/contacts/opportunities |
| s7 | 15s total | 2 calls × N buyers, parallel |
| s8-s11 | 15s each | LLM generation |
| s15 | 10s | Notion API |

## Open Questions

1. **Local vs. Datagen execution?** CLAUDE.md says prefer local, but Starbridge API keys and Notion MCP are on Datagen. Options: (a) hybrid — local orchestrator, Datagen for API tools, (b) all-Datagen, (c) local with secrets from Datagen.
2. **SQLite location?** Datagen's `sqlite_query` tool? Or local SQLite file?
3. **Webhook trigger?** Clay sends to Datagen endpoint, or Clay sends to a local webhook server?
4. **s4 LLM tiebreak** — is the LLM portion of s4 a subagent call, or does the orchestrator handle it inline? Currently proposed: orchestrator inline (it needs all discovery data in context anyway).
