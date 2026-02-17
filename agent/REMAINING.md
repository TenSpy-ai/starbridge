# Remaining Items — V1 Completion Scope

What's built, what's not, and what's needed to go from "works locally" to "production automation."

## What's Done (Built & Tested)

| Component | Status | Evidence |
|---|---|---|
| 19-step pipeline orchestrator | **Complete** | `pipeline.py` — 1,186 LOC |
| 5 LLM sub-agents (strategy, buyer profile summary, featured, secondary, fact-check) | **Complete** | `llm.py` — Claude CLI backend |
| 5 Starbridge custom tool integrations | **Complete** | `tools.py` — sync + async REST |
| Notion MCP publish | **Complete** | `tools.py` — Datagen SDK |
| Deterministic buyer scoring (6-factor) | **Complete** | `pipeline.py` s4 |
| SQLite persistence (4 tables) | **Complete** | `db.py` — runs, discoveries, contacts, audit_log |
| State preservation on failure | **Complete** | Run stub at s1, partial save on crash, run marked 'failed' |
| Audit logging per step | **Complete** | `StepTimer` context manager |
| Config centralization | **Complete** | `config.py` — all tunables with docs |
| Test runner (real data, end-to-end) | **Complete** | `run_vmock.py` — real Starbridge API + real LLM |
| Standalone Q&A sub-agent | **Complete** | `python -m agent.llm "question"` |
| Architecture docs + interactive explorer | **Complete** | `README.md`, `pipeline-explorer.html` |
| HTTP server + monitor UI | **Complete** | `server.py` — FastAPI, serves explorer, runs pipeline via POST |

**15 successful runs in SQLite. 859 discoveries. 339 contacts cached.**

---

## What's Remaining

### P0 — Required for V1 Launch

#### 1. Deploy as Cloud-Hosted Claude Code Agent
**What**: Release the pipeline on datagen.dev as a cloud-hosted Claude Code agent.
**Status**: Pipeline + HTTP server are built and tested locally. `server.py` provides the entry point.
**Effort**: Deployment configuration — Jeremy handling this directly.

#### 2. Completion Webhook → Clay → Slack
**What**: When the pipeline finishes (s16), push a webhook to Clay with the Notion URL + run metadata. Clay handles Slack dispatch to `#intent-reports`.
**Status**: Not yet built. Will be added as a new pipeline step (after s16 or as part of s16).
**Design**: Pipeline POSTs a completion webhook to Clay. Clay formats and routes to Slack — keeps Slack ownership in Clay where it already lives. Same pattern for failure alerts (#3 below).
**Effort**: ~1h for the pipeline webhook step. Clay-side routing is separate.

#### 3. Failure Alerts via Same Webhook → Clay → Slack Pattern
**What**: When the pipeline fails, push an error webhook to Clay. Clay posts failure details to `#gtm-eng`.
**Status**: Not yet built. Same webhook pattern as #2 — pipeline pushes, Clay routes.
**Effort**: ~30min (reuse the same webhook step with error payload).

#### 4. End-to-End Test with Real Positive Reply
**What**: Full loop test: trigger → pipeline → report → webhook → Clay → Slack.
**Status**: In progress. Pipeline runs end-to-end locally with real data. Remaining: test the full deployed loop.

---

### P1 — Important for Reliability

#### 5. Error Recovery + Retry Logic
**What**: When the pipeline fails partway (e.g., Starbridge API timeout), the run is saved as 'failed' with partial state. Currently there's no way to retry from where it left off.
**Options**:
- **a) Full retry** — Simple: re-run the entire pipeline for the same domain. Cached discoveries (from prior runs) speed up s1, but all API calls are repeated.
- **b) Partial retry from checkpoint** — More complex: deserialize the partial state from SQLite and resume from the failed step. Requires a `resume_pipeline(run_id)` function.
- **c) Manual retry via CLI** — Operator (Hagel) re-triggers via a command. Simplest, but requires monitoring.
**Effort**: 2-4 hours for full retry. 4-8 hours for checkpoint retry.

#### 6. Rate Limiting + Backoff
**What**: Datagen's custom tool endpoints may rate-limit above ~10 concurrent requests. Currently, we keep thread pools small (3-5 workers) as a safety net, but there's no explicit retry-on-429 logic.
**Gap**: If multiple pipelines run concurrently (e.g., 3 positive replies in 60 seconds), they could overwhelm the API.
**Options**:
- **a) Queue-based** — Incoming webhooks go into a queue (Redis, SQLite, or in-memory). A single worker processes them sequentially. Eliminates concurrency issues.
- **b) Retry with backoff** — Add exponential backoff (2s → 4s → 8s) in `tools._call_custom()` on HTTP 429 responses.
**Effort**: 2-4 hours.

---

### P2 — Nice to Have for V1

#### 7. Report Branding
**What**: The current Notion reports are plain markdown. V2 target is branded landing pages (Notion → Super.so or Webflow).
**Gap**: Nastia (Design Lead) hasn't delivered the branding yet. Current reports are functional but not branded.
**Effort**: Depends on design delivery. Implementing the branding in the template sections (s8, s11, s12) is 1-2 hours once the design exists.
**Dependency**: Nastia.

#### 8. DM Contact Card (Tier 2)
**What**: Add decision-maker contact card to the report — the "DM-later" flow from `decisions/003-dm-later-flow.md`.
**Gap**: Intentionally deferred. V1 ships without DM info. DM card is offered on the call as a meeting hook.
**Dependency**: Starbridge API access (Yurii). V2 scope.

#### 9. Multi-Signal Campaigns
**What**: Different campaigns target different signals. The pipeline currently takes one `campaign_signal` — it doesn't handle Kushagra's multi-signal allocation framework.
**Gap**: V1 handles single-signal campaigns. Multi-signal requires knowing which signal in the sequence triggered the reply.
**Effort**: 2-4 hours to add signal-sequence awareness. Depends on Smartlead webhook carrying the sequence/email number.

#### 10. Automated Test Suite
**What**: Unit tests for scoring logic, integration tests for API calls, end-to-end tests with mock data.
**Gap**: Only a manual test runner exists (`run_vmock.py` — real API calls). No pytest, no CI.
**Effort**: 4-8 hours for meaningful coverage.

#### 11. Supabase Integration
**What**: CLAUDE.md lists Supabase as the signal database (Kushagra). The pipeline currently uses Starbridge API directly — Supabase would be an additional/alternative signal source.
**Gap**: Schema unknown ("⬜ Kushagra meeting → Supabase schema"). Pipeline doesn't query Supabase.
**Dependency**: Kushagra meeting to get schema. This was listed as V1 blocker in CLAUDE.md but the pipeline works without it via direct Starbridge API.

---

## Critical Path to V1 Launch

```
Current state:  Pipeline + HTTP server built and tested locally.
                Deploying to datagen.dev as cloud-hosted Claude Code agent.

Required path:
  1. [DONE]   Build HTTP endpoint (FastAPI wrapper) — server.py
  2. [IN PROGRESS] Deploy on datagen.dev as cloud Claude Code agent
  3. [TODO]   Add completion webhook step (pipeline → Clay → Slack)
  4. [IN PROGRESS] End-to-end test with real positive reply
  5. [TODO]   Add failure webhook (same pattern as #3)
                                          ─────────
                                          ~2-3 hours of code remaining
```

Pipeline code is complete. Remaining work is the completion/failure webhooks and deployment.

## Dependencies Map

```
Datagen.dev deployment ─────→ Jeremy (handling directly)
Completion webhook → Clay ──→ Jeremy (pipeline step + Clay route)
Failure webhook → Clay ─────→ Same pattern as completion
Report branding ────────────→ Nastia (design) — V2
DM contact card ────────────→ Yurii (Starbridge API access) — V2
Supabase signals ───────────→ Kushagra (schema) — V2
```
