# ADR 002: Use Datagen Cloud Agents for Pipeline Orchestration

## Status
**Accepted** — proposed by Jeremy, accepted by Henry during onboarding

## Context
The positive reply → intel report pipeline requires multi-step logic: query Supabase, run LLM processing, query the Starbridge API, assemble content, generate a report page, and return the result. This needs an orchestration layer.

Two options were considered:
1. **Clay-only**: Use Clay's native features (HTTP requests, AI columns, automations) for all processing
2. **Clay + Datagen**: Clay handles routing and dispatch; Datagen handles complex multi-step processing

## Decision
Use Datagen cloud agents as the orchestration and processing layer. Clay remains the router (webhook intake, Slack dispatch) but Datagen handles all multi-step logic.

## Reasoning

Clay can't do several things the pipeline requires:
| Requirement | Clay Limitation |
|---|---|
| Query Supabase by domain | No native Supabase integration |
| Multi-step LLM reasoning | AI columns are single-prompt, single-response |
| Chain multiple API calls with conditional logic | HTTP request columns don't support branching |
| Rank/select from variable-length signal lists | Column formulas are static, not dynamic |
| Generate external pages (Notion/Webflow) | Clay doesn't create external content |
| Async processing (pipeline takes seconds) | Clay webhooks expect near-synchronous responses |

Datagen solves all of these as a single orchestrated Python endpoint. It also provides:
- **Deployable API endpoints** — Clay calls Datagen via HTTP, receives results via webhook
- **LLM orchestration** — native support for Claude/LLM calls within the pipeline
- **MCP integration** — connects to Supabase, Notion, and other tools
- **Error handling** — retry logic, fallback behavior, graceful degradation

## Consequences
**Positive:**
- Full pipeline automation with no human bottleneck
- Flexible Python environment handles any processing complexity
- Datagen agents are reusable — same agent can be called by other systems
- Jeremy owns and understands the tool (he's an experienced Datagen user)
- End-state abstraction: "input domain → get report URL" as a clean API

**Negative / Risks:**
- Additional infrastructure dependency (Datagen must be up for pipeline to work)
- Monthly cost ($50 month 1, $500 month 2+ — approved as trial expense)
- Team unfamiliarity — only Jeremy knows Datagen; bus factor risk if he leaves
- Need to manage two systems (Clay + Datagen) instead of one

**Mitigations:**
- Fallback to manual process (Hagel + Slack bots) if Datagen is down
- Document everything in this repo so another engineer could maintain it
- Datagen is the simpler dependency — it's a stateless API endpoint, not a stateful system
- Clay still owns the "routing" job and can be pointed at a different processor if needed

## Cost
| Item | Monthly | Approved? |
|---|---|---|
| Datagen | $50 (month 1), $500 (month 2+) | Yes — trial expense |
| Claude Max | $200 | Yes — trial expense |
