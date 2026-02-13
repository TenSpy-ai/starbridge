# Gamma — Legacy Intel Report Format

## What Gamma Is

Gamma (gamma.app) is a presentation/document generation tool. Starbridge currently uses it to create per-prospect intel reports — the deliverable that BDRs send to prospects after a positive reply.

## Current Process

Hagel's workflow for creating a Gamma report:

1. Pull intent signals via Slack bots (endgame-lookup + Starbridge app)
2. Export signals as CSV or copy/paste from bot responses
3. Feed the signal data into **Gemini** (Google's LLM)
4. Neil Daiksel's prompts format the output into **succinct intel bullets**
5. Upload the formatted output into Gamma
6. Gamma generates a visual report/page
7. Output: a Gamma link (URL) — this is what gets posted in #intent-reports and sent to prospects

## What a Gamma Report Contains (Current)

{{UNVERIFIED: inferred from Slack observations and onboarding — need to see actual Gamma reports to confirm exact structure}}

Based on the Slack dispatch patterns, current reports include:
- Intent signal summaries (the bullets processed through Gemini)
- Some contextual framing around the signals
- {{UNKNOWN: does it include company branding? Starbridge logo? Prospect name?}}
- {{UNKNOWN: exact visual layout — is it a deck? A single page? Multiple pages?}}

What current reports generally do NOT include:
- Decision maker contact info (this is sent separately in the Slack message, not in the Gamma report)
- Budget data
- Account logos
- Procurement navigation guidance
- Branded Starbridge design

## Why Gamma Is Being Replaced

Five confirmed problems:

### 1. Non-Deterministic Output
Same inputs → different reports. Gamma's AI generation introduces randomness in layout, phrasing, and structure. Henry's team explicitly called this out: "Gamma outputs are non-deterministic." This means:
- Reports look inconsistent across prospects
- QA is hard because you can't predict what it'll produce
- Can't build a reliable brand experience

### 2. Limited Data
Gamma only renders what Hagel manually feeds in. The current process only uses signal bullets from Gemini — it doesn't pull in buyer attributes, DM info, budget data, or other enrichments. The data is "limited to a data snapshot at that time" — no live updates, no supplementary data.

### 3. No Branding Control
Gamma has its own aesthetic. Starbridge can't apply their brand (colors, logo, fonts, layout) in a fully controlled way. For a report that goes directly to SLED buyers, brand consistency matters.

### 4. Manual Process
Every report requires Hagel to manually: pull data → process through Gemini → upload to Gamma → generate → copy the link. No step is automated. This is the core bottleneck the pipeline replaces.

### 5. Single Point of Failure
If Hagel is offline (Philippines timezone, sick day, overloaded), reports don't get made. There's no fallback operator and no automation to fill the gap.

## What Gamma Gets Right (Preserve in Replacement)

Despite its problems, the Gamma approach established some patterns worth keeping:

| Pattern | Why It Works | How to Preserve |
|---|---|---|
| **Visual format** (not just text) | SLED buyers are used to RFP documents and formal presentations — a visual deliverable feels appropriate | New format should be visually polished, not a plain text dump |
| **Signal bullets** (not raw data) | Gemini/Neil's prompts translate raw signals into "what this means for you" summaries — this is the value-add | LLM processing step in Datagen preserves and improves this |
| **One link per prospect** | Simple to share via email, Slack, or forward internally | New format produces one URL per report |
| **Hagel's contextual additions** | Territory notes, packaging expectations, relevancy analysis for Tier 3 — these make reports actionable, not generic | Automate where possible (LLM for relevancy), support manual additions where needed |

## Gemini Prompts (Neil's Contribution)

Neil Daiksel helped design the Gemini prompts that format raw signals into succinct intel bullets. These prompts are a key asset:

{{UNKNOWN: the actual prompts — need to get from Neil}}

What we know about them:
- Input: raw signal data (CSV or text from Slack bot output)
- Output: formatted intel bullets that are "succinct" and ready for the report
- They translate procurement jargon into business-relevant summaries
- They've been iterated on and are considered "working" by the team

**Action**: Get Neil's prompts. They're the starting point for the LLM processing step in Datagen. Even if we switch from Gemini to Claude, the prompt structure and output format are valuable.

## Transition Plan

| Phase | Report Format | How Generated |
|---|---|---|
| **Now** | Gamma | Hagel manually (endgame-lookup → Gemini → Gamma) |
| **V1** | {{TBD: Notion / Super.so / Webflow}} | Datagen automated (Supabase → LLM → page generation) |
| **Transition** | Both may coexist briefly | Automated pipeline for new replies; Hagel uses Gamma as fallback for edge cases |
| **V2+** | Branded landing page | Datagen fully automated with buyer attributes |

During transition, Hagel should still know how to make Gamma reports. Don't kill the fallback until V1 is proven reliable.

## Gamma Links in Existing #intent-reports History

All historical intel deliveries in #intent-reports reference Gamma links. These are:
- Still accessible (Gamma links don't expire {{UNVERIFIED: confirm Gamma link persistence}})
- Useful as reference for what prospects have already received
- A benchmark for "at least as good as" quality testing of V1
