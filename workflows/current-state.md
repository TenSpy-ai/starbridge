# Current State — Hagel's Manual Fulfillment Process

## Overview

This is the process being replaced. Hagel Alejandro (Philippines-based fulfillment operator) manually handles every positive reply. The process works but is slow, error-prone, and doesn't scale.

## Step-by-Step (Observed from Slack + Onboarding Notes)

### Step 1: Detect Positive Reply
- Hagel monitors the Smartlead inbox for positive replies
- No automation — he's watching manually {{UNVERIFIED: inferred from workflow description — confirm with Hagel if he has any alerts/filters}}
- Philippines timezone creates lag (most prospects are US-based)

### Step 2: Extract Domain + Context
- Hagel takes the replying company's domain from the email
- Notes the prospect name, email, and any context from their reply (quote, request type, constraints)

### Step 3: Pull Intent Signals
Hagel uses **two Slack-based tools** to pull data:

**Tool 1: endgame-lookup (Kushagra's Slack bot)**
- Hagel inputs a domain into the Slack bot
- Bot pings Supabase
- Returns: all intent signals aligned to that account/domain
- Example query: "pull all signals for X domain related to this SLED account"

**Tool 2: Starbridge Slack app**
- Hagel uses the native Starbridge Slack integration
- Returns: custom data from the Starbridge platform (DM info, buyer attributes)
- Example query: "for this SLED account, given these minutes, give me the DM info"

### Step 4: Process Signals into Intel Bullets
- Hagel takes the raw signal data (often a CSV export from the tools)
- Feeds it into **Gemini** (Google's LLM)
- Neil Daiksel helped design the prompts for succinct intel bullet formatting
- Output: summarized, readable intel bullets

### Step 5: Generate Gamma Report
- Hagel uploads the processed intel into **Gamma**
- Gamma generates a visual report/deck for the prospect
- Output: a Gamma link (URL to the report)

### Step 6: Find Decision Maker (Sometimes)
- For Tier 2+ responses, Hagel identifies the relevant SLED-side decision maker
- Sources: Starbridge platform, Slack app, manual research
- Output: Name, Title, Email, Phone

### Step 7: Post Dispatch in #intent-reports
**Message 1: "New positive response"**
```
@{BDR} — new positive response from {ProspectName} of {Company}, {ProspectEmail}!
Custom intel and intent report coming your way shortly.
"{reply quote}"
Notes: {territory/scheduling/demo request}
```

### Step 8: Post Intel Ready in #intent-reports
**Message 2: "Custom intel is ready"**
```
@{BDR} — custom intel is ready for {ProspectName} of {Company}, {ProspectEmail}.
Gamma Link: {URL}

Custom Intel:
- Name: {DMName}
- Title: {DMTitle}
- Email: {DMEmail}
- Phone: {DMPhone}

IR Notes (if applicable):
- Relevancy: {analysis}
- Pitch angle: {suggestion}
- Gameplan: {talk track}
```

### Step 9: BDR Takes Over
- BDR sends payload email (often via Apollo in a separate thread)
- BDR calls using Nooks
- BDR converts to meeting

## Known Problems with Current State

| Problem | Impact | Severity |
|---|---|---|
| **Time to respond** | Philippines hours = multi-hour lag on US business hours replies | High |
| **Human error at volume** | Manual copy-paste across 4+ tools; mistakes compound | High |
| **Report quality** | Gamma output is non-deterministic (same inputs → different reports) | High |
| **Limited data in reports** | Only uses signal bullets; doesn't include budget, logo, DM, procurement nav, AI adoption scores | Medium |
| **No branding** | Gamma reports look generic, not Starbridge-branded | Medium |
| **Data snapshot** | Gamma report reflects data at creation time only; no live updates | Low |
| **Single point of failure** | Hagel is the bottleneck; if he's offline, replies pile up | High |
| **No tracking** | No automated measurement of time-to-response or fulfillment completeness | Medium |

## Tools in Current Workflow

```
Smartlead (inbox monitoring - manual)
  → Slack bot: endgame-lookup (Supabase signals)
  → Slack app: Starbridge (DM info, buyer data)
  → Gemini (signal → bullet processing)
  → Gamma (report generation)
  → Slack #intent-reports (dispatch)
  → Apollo (BDR follow-up sequencing)
  → Nooks (phone calls)
```

## What the Current Process Gets Right

- The #intent-reports channel as the dispatch hub works well — clear, visible, everyone knows where to look
- Hagel's two-message format (dispatch + intel ready) is clean and should be preserved in automation
- The tiered approach (Tier 1/2/3) is smart — not every reply needs full treatment
- DM contact cards when available are immediately actionable for BDRs
- Relevancy analysis + gameplan (Tier 3) is genuinely enabling, not just data dumping

## What to Preserve in the Automated Version

1. **#intent-reports as the single dispatch channel** — don't fragment
2. **Two-message pattern** (notification first, intel second) — BDRs know the rhythm
3. **Tiered intel depth** — automate the tiers, don't flatten everything to one level
4. **Operator context** (territory, scheduling, packaging notes) — find a way to capture these automatically or make it easy to add manually
5. **Speed of BDR response** — "drop what you're doing" urgency culture
