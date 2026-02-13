# V1 MVP — Trial Deliverable

## Deadline
**Tuesday, February 17, 2026**

## What "Done" Looks Like

A positive reply in Smartlead automatically produces an intel report URL and Slack dispatch to #intent-reports — no human in the loop for the core pipeline. BDRs receive the same two-message pattern they're used to, but faster and with better content.

**End-to-end flow**: Smartlead webhook → Clay → Datagen (Supabase query + LLM + report generation) → Clay → Slack

## V1 Scope (In)

| Component | What Ships | Notes |
|---|---|---|
| **Smartlead webhook** | Positive reply fires to Clay | {{UNKNOWN: may need to configure from scratch}} |
| **Clay routing** | Receives webhook, sends to Datagen, receives return, dispatches to Slack | Two webhook source columns in Project Endgame |
| **Datagen agent** | Queries Supabase → LLM ranks signals → generates Notion page → returns URL | Core pipeline — see /systems/datagen/agents.md |
| **Supabase query** | All signals for a domain | Depends on Kushagra meeting for schema |
| **LLM processing** | Rank and select top 5-10 signals, generate SLED Signal Bullets | Start with Neil's Gemini prompts adapted for Claude |
| **Report generation** | Notion page with signal bullets | Tier 1 format — signals only, no DM, no branding |
| **Slack dispatch** | Message 1 (new PR) + Message 2 (intel ready) to #intent-reports | Same pattern as current, but automated |

## V1 Scope (Out — Explicitly Deferred)

| Component | Why Deferred | When |
|---|---|---|
| DM contact card in report | SB API access blocked on Yurii | V2 |
| Buyer attributes (budget, logo, location) | SB API dependency | V2 |
| Branded report template | Nastia design dependency | V2 |
| Multi-signal allocation integration | Kushagra still building framework | V2 |
| Follow-up email sequence automation | Not critical path; BDRs can follow up manually | V2 |
| Signal Refresher agent | V3 scope | V3 |
| Batch report pre-generation | V3 scope | V3 |
| Phone/snail mail channel integration | Multi-channel is V3 | V3 |

## Critical Path

```
Week of 2/4 (Wed start — onboarding):
  Wed:     Kushagra meeting (Supabase schema) — UNBLOCKS Datagen query
  Wed:     Explore Clay workspace (webhook config, table structure)
  Thu:     Build Datagen agent (Supabase → LLM → Notion)
  Thu:     Update Henry on Datagen timeline
  Thu:     Connect Clay ↔ Datagen (HTTP request + webhook return)
  Fri:     Connect Clay → Slack dispatch
  Fri:     End-to-end test with sample accounts
  Fri:     Continue building + testing

Week of 2/10–2/14:
  Mon-Fri: Build, test, iterate
  Fri:     End-to-end test with sample accounts

Week of 2/17:
  Tue 2/17: Deadline — V1 working + Rollout: first automated intel reports in production
  +        Yurii meeting (SB API access) — UNBLOCKS V2
  +        Nastia meeting (brand assets) — UNBLOCKS V2 design
```

## Blockers

| Blocker | Who Unblocks | Impact if Not Resolved |
|---|---|---|
| Supabase schema | Kushagra | Cannot build Datagen query — V1 dead |
| Clay workspace access | Henry / self-exploration | Cannot configure webhook routing |
| Neil's Gemini prompts | Neil | Must write LLM prompts from scratch (slower, lower quality baseline) |
| Smartlead webhook config | {{UNKNOWN: who configures this?}} | Must use a manual trigger instead of automated webhook |

## Acceptance Criteria

- [ ] Positive reply in Smartlead → automated Slack dispatch in < 60 seconds
- [ ] Intel report URL is live and contains relevant signals for the company
- [ ] Signals are ranked and summarized (not raw data dumps)
- [ ] Report page is deterministic (same domain → same structure)
- [ ] BDR @-mention is correct in Slack dispatch
- [ ] Pipeline handles errors gracefully (no silent failures)
- [ ] At least 3 successful end-to-end tests before rollout
- [ ] Hagel confirms the output is "at least as good as" Gamma
