# Intel Report Workflow Playground

## Background

Starbridge monitors 296K+ government and education (SLED) buyers and has indexed 107M+ board meetings and procurement records. When a prospect replies positively to an outbound email, the GTM pipeline generates a personalized intel report — a branded page showing relevant procurement signals, buyer contacts, and strategic context for that prospect's organization.

This pipeline is being automated through **Datagen**, a cloud agent orchestration platform. It replaces a manual process (20-60 min per report) with a fully automated one (target: < 30 sec).

## What This Playground Is

An interactive, single-file HTML tool for **designing and reviewing** the 19-step Datagen agent pipeline. It's a spec/design artifact, not the pipeline itself.

Open `intel-report-workflow-v2.html` in any browser — no build step, no server, no dependencies.

## Key Terms

| Term | Meaning |
|---|---|
| **SLED** | State/Local government + Education — Starbridge's target market |
| **Clay** | Routing hub that receives webhooks and dispatches work to Datagen |
| **Datagen** | Cloud agent platform that orchestrates the pipeline (Supabase → LLM → report) |
| **Supabase** | Signal database — stores procurement intent signals by domain |
| **Starbridge API** | Internal API for buyer attributes (contacts, budget, logos) |
| **Notion** | Where the final report page gets published |
| **Signal** | A procurement event (contract expiration, board mention, RFP, budget line item, etc.) |
| **Featured buyer** | The top-ranked buyer organization for a given prospect's domain |

## Files in This Directory

| File | Description |
|---|---|
| `intel-report-workflow-v2.html` | Current interactive playground (this README documents it) |
| `intel-report-workflow.html` | Earlier v1 (superseded by v2) |
| `intel-report-agent-directions.md` | Written agent execution spec (14 steps) |
| `intel-report-prompts.md` | Agent prompt templates per phase |

## How to Use the Playground

1. Open `intel-report-workflow-v2.html` in a browser
2. **List view** (default): left panel shows all steps, click one to see its detail panel on the right
3. **Diagram view**: toggle at top — shows a node graph with arrows representing data flow between steps
4. For any step, the detail panel shows:
   - **Data In** — input variables, grouped by which step produces them
   - **Data Out** — output variables with JSON schema showing field structure
   - **Feeds Into** — which downstream steps consume this step's outputs
   - **Prompt** — the LLM prompt template (for LLM steps)
   - **Detail** — implementation notes (API calls, logic, etc.)
   - **Quality Rules** — validation checks the step must pass
   - **Edge Cases** — failure modes and how they're handled
5. In diagram view, hover arrows to see which variables flow along that edge
6. Filter by phase using the buttons at top

## The Pipeline End-to-End

The pipeline takes a positive email reply and produces a published intel report. Here's what happens at each phase:

**Source → Input** (s0–s1): A prospect replies positively to an outbound email. Smartlead fires a webhook to Clay, which sends the prospect's info (company, domain, email) to Datagen. Datagen validates the fields and loads any prior context from SQLite (previous runs, existing insights for this domain).

**Analyze** (s2): An LLM analyzes the prospect's company and the campaign signal to determine a search strategy — which SLED segments to target, what keywords to search, and what an ideal buyer looks like.

**Discovery** (s3a–s3c): Three parallel Starbridge API searches find relevant government/education buyers — one using primary keywords, one using alternate keywords, and one searching by buyer type. These return raw signal matches.

**Select** (s4–s5): The discovered buyers are ranked by signal relevance. The pipeline picks one featured buyer (deepest intel) and up to 3 secondary buyers. Results are persisted to SQLite.

**Intel** (s6–s7): Deep enrichment for the featured buyer — profile, contacts, opportunities, and AI-generated strategic context (4 parallel API calls). Secondary buyers get lighter enrichment (profile + contacts).

**Generate** (s8–s12): Five parallel LLM calls generate the report sections — executive summary, featured buyer deep-dive, secondary buyer cards, Starbridge CTA, and footer. Each has specific quality rules.

**Assemble** (s13–s16): Sections are concatenated, validated (5 deterministic checks + 3 LLM checks — with a retry loop back to s11 if validation fails), published to Notion, and the final response is saved to SQLite and returned to Clay as JSON.

## Pipeline Steps Reference

| ID | Phase | Step |
|---|---|---|
| s0 | Source | Webhook input from Clay |
| s1 | Input | Validate & load SQLite context |
| s2 | Analyze | LLM determines SLED search strategy |
| s3a | Discovery | Primary signal search (parallel) |
| s3b | Discovery | Alternate signal search (parallel) |
| s3c | Discovery | Buyer type search (parallel) |
| s4 | Select | Rank & select featured + secondary buyers |
| s5 | Select | Persist discovery to SQLite |
| s6 | Intel | Featured buyer deep intel (4 API calls, parallel) |
| s7 | Intel | Secondary buyers intel (parallel) |
| s8 | Generate | Executive summary (parallel) |
| s9 | Generate | Featured buyer section (parallel) |
| s10 | Generate | Secondary buyer cards (parallel) |
| s11 | Generate | Starbridge CTA (parallel) |
| s12 | Generate | Footer template (parallel) |
| s13 | Assemble | Concatenate all sections |
| s14 | Assemble | 8-point validation (5 deterministic + 3 LLM) |
| s15 | Assemble | Publish to Notion |
| s16 | Assemble | Save to SQLite & return JSON to Clay |

## Data Architecture (for modifying the playground)

### Step Definition Properties

Each step in the `STEPS` array has:

- `id`, `phase`, `num`, `name`, `type`, `meta`
- `inputs[]` — variable names consumed
- `outputs[]` — variable names produced
- `outputSchema{}` — JSON structure for each output (camelCase fields)
- `tools[]` — external tool calls
- `prompt` — LLM prompt template (null for non-LLM steps)
- `detail` — implementation notes for non-LLM logic (null for pure LLM steps)
- `qualityRules[]` — acceptance criteria (what must be true)
- `edgeCases[]` — `{ label, action, severity }` — failure modes and fallbacks
- `conditionalRun` — `{ type, rule }` — whether/how the step executes (see below)

**prompt vs detail**: Non-LLM steps have `detail` only. Pure LLM steps (s2, s8–s11) have `prompt` only — the prompt is the spec. Hybrid steps (s4: logic+llm, s14: validate+llm) have both — `detail` for the deterministic part, `prompt` for the LLM part.

### Conditional Run Rules

Each step has a `conditionalRun` property indicating whether it runs, can abort the pipeline, or branches on input. Rendered as a color-coded badge in the detail panel.

| Type | Badge Color | Meaning | Steps |
|---|---|---|---|
| `always` | green | Runs unconditionally | s3a, s3b, s3c, s5, s6, s8, s9, s13, s15, s16 |
| `stop` | red | Runs but may abort the pipeline | s0 (missing fields), s1 (missing identifiers), s4 (0 buyers) |
| `skip` | orange | Skips or produces empty output | s7 (no secondaries), s10 (no secondaries) |
| `branch` | purple | Always runs, output varies by condition | s2 (prior runs), s11 (retry loop), s12 (AI context flag), s14 (triggers retry) |

### Derived Data Flow (computed at startup)

- `INPUT_SOURCES` — maps each variable to its producing step
- `COMPUTED_EDGES` — maps source→target pairs to variable lists
- `VALIDATION_LOOPS` — bidirectional retry edges (s14↔s11)

All four views (Data In, Data Out, Feeds Into, diagram arrows) derive from these — no edges are manually defined.

### Naming Conventions

| Scope | Convention | Example |
|---|---|---|
| Pipeline variables | ALL_CAPS | `FEATURED_BUYER_ID`, `SEARCH_STRATEGY` |
| Webhook inputs | lowercase | `target_company`, `prospect_email` |
| JSON field names (outputSchema) | camelCase | `buyerId`, `topSignalSummary` |
| SQLite columns | snake_case | `featured_buyer_id`, `report_markdown` |

### Node Types & Colors

Steps can have multiple types (e.g., s1 is `['validate', 'sqlite']`, s16 is `['sqlite', 'logic']`). Multi-type nodes show a split color in the diagram.

| Type | Color | Meaning |
|---|---|---|
| source | white | Webhook entry point |
| validate | red | Field validation |
| sqlite | yellow | Database operations |
| llm | purple | LLM generation |
| tool | teal | External API calls |
| logic | gray | Deterministic computation — assembles or transforms data (e.g., s13 concatenates sections, s16 builds response JSON) |
| template | gray | Fixed text with placeholder substitution — no computation (only s12: picks a static footer string, fills in date) |
