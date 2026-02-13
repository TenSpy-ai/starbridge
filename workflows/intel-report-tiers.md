# Intel Report Tiers

## Overview

Not every positive reply gets the same level of intel. The depth of the report depends on data availability, account value, and time constraints. Intel comes in three tiers.

## Tier Definitions

### Tier 1 — Report Only

**Contents:**
- Branded intel report link (Gamma today, Notion/Webflow future)

**When used:**
- DM contact isn't required for the conversation
- DM info isn't available quickly
- The report itself is enough to move the conversation forward
- Time-critical: better to send something fast than wait for full enrichment

**Slack message format:**
```
@{BDR} — custom intel is ready for {ProspectName} of {Company}, {Email}.
Gamma Link: {URL}
```

### Tier 2 — Report + Decision Maker Contact Card

**Contents:**
- Branded intel report link
- Decision maker contact card:
  - Name
  - Title
  - Email
  - Phone (sometimes "Direct Phone")

**When used:**
- Standard fulfillment for most positive replies
- DM info is available from Starbridge platform or API
- Prospect is interested in knowing who to talk to on the SLED side

**Slack message format:**
```
@{BDR} — custom intel is ready for {ProspectName} of {Company}, {Email}.
Gamma Link: {URL}

Custom Intel:
- Name: Holly Varner
- Title: Director of Special Education
- Email: hvarner@district.edu
- Phone: (555) 123-4567
```

**Real examples from Slack:**
- Point Quest Group → Holly Varner, Director of Special Education
- OxBlue → Holly Harris, Health Services Director
- SwiftComply → Tom Coppola, Director (Commissioner) of Public Works

### Tier 3 — Report + DM + Relevancy Analysis + Gameplan

**Contents:**
- Everything in Tier 2, plus:
- Written relevancy analysis connecting signals to the prospect's situation
- Suggested pitch angle
- Gameplan / talk track for the BDR

**When used:**
- High-value accounts
- Complex signals that need interpretation
- When the BDR needs more than just "here's a link and a name"

**Slack message format:**
```
@{BDR} — custom intel is ready for {ProspectName} of {Company}, {Email}.
Gamma Link: {URL}

Custom Intel:
- Name: {DMName}
- Title: {DMTitle}
- Email: {DMEmail}
- Phone: {DMPhone}

IR Notes:
- Relevancy: {specific initiative/signal connection}
- Pitch angle: {suggested framing}
- Gameplan: {what to say, what to lead with}
```

**Real example (Attendance Point):**
- Relevancy Analysis: K-1 chronic absenteeism, "Attendance Awareness" initiative, currently using public information officers + social media campaigns
- This tells the BDR exactly what pain point to reference and what the district is already doing

## Operator Additions (Any Tier)

Hagel sometimes includes additional context regardless of tier:

| Addition | Example | Purpose |
|---|---|---|
| **Territory scoping** | "Not CA; focus on MD/WV/VA/TN/KY" | Prevents BDR from targeting wrong region |
| **Scheduling request** | "Availability 12:30–3:00 EST" | Prospect stated time preferences |
| **Packaging expectations** | "Wanted 12 signals; we sent 5; rest in demo" | Sets expectations for what's in-report vs. saved for the call |
| **Prospect quote** | Direct snippet from the reply email | Changes urgency/tone of BDR response |
| **Response guidance** | "Respond in original thread since they'll forward internally" | From Henry — situational override of default separate-thread approach |

## How Tiers Map to the DM-Later Flow

With the new DM-Later approach (as of 2/4/26):

| Stage | Tier Used | What Happens |
|---|---|---|
| First response to positive reply | **Tier 1** | Send intel report + screenshot + "want more like this?" |
| If prospect engages / books call | **Tier 2** during call prep | DM info gathered and shared with BDR before the call |
| If no reply to initial intel | **Tier 2 or 3** | Send DM info + ask for a call + deeper analysis |
| High-value enterprise accounts | **Tier 3** from the start | Full treatment regardless of flow stage |

## Implications for Automation

### V1 (MVP)
- Automate **Tier 1** fully: signal-based report, auto-generated and dispatched
- DM info added manually by Hagel if needed (until SB API is wired up)

### V2
- Automate **Tier 2**: Datagen hits SB API for DM info, includes in Slack dispatch
- Automate tier assignment logic: account value / signal strength → auto-select tier

### V3
- Automate **Tier 3**: LLM generates relevancy analysis + pitch angle based on signal content + prospect context
- Potentially: BDR never needs to think about which tier — system decides and delivers

## What Goes in the Intel Report Itself (Future State)

Content the report should include (from onboarding discussions):

| Section | Source | Priority |
|---|---|---|
| Top 5–10 intent signals (summarized) | Supabase → LLM | Must have |
| SLED Signal Bullets | LLM-generated in Clay | Must have |
| Decision maker(s) | Starbridge API {{UNKNOWN: blocked on Yurii access}} | V2 |
| Account logo | Starbridge API {{UNKNOWN: confirm field exists in API}} | V2 |
| Budget / spend data | Starbridge API | V2 (most valuable attribute per Justin) |
| Location / map | Starbridge API {{UNKNOWN: confirm field availability}} | V2 |
| AI Adoption Score | {{UNKNOWN: derived metric — methodology not defined}} | V3 |
| How to Navigate Procurement (for this buyer) | Starbridge data + LLM {{UNVERIFIED: feasibility not confirmed}} | V3 |
| Similar customers | {{UNKNOWN: account matching logic not designed}} | Future idea |
| Branding (consistent with Starbridge brand) | Nastia's design {{TBD: format and template not created}} | V2 |
