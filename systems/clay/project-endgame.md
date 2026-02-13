# Project Endgame — Clay Workbook

## Overview

Project Endgame is the main Clay workbook powering Starbridge's outbound engine. It's the central table where prospect data lives, signals get matched, webhooks flow in and out, and downstream actions get triggered.

**Workspace ID**: 484780
**Workbook URL**: [https://app.clay.com/workspaces/484780/home/f_0t6nh48BDBiBnAvajMt](https://app.clay.com/workspaces/484780/home/f_0t6nh48BDBiBnAvajMt)
*Note: this URL points to a specific workbook (`f_0t6nh48BDBiBnAvajMt`) within workspace 484780, not the workspace home. The workspace may contain other workbooks (e.g., Boiler Room).*

## Known Structure

### Tables

{{UNKNOWN: full table inventory — need to explore the Clay workspace with Kushagra}}

**Primary table (confirmed):**
- Contains prospect/account rows
- Receives Smartlead webhook data (positive replies)
- Houses the "SLED Signal Bullets" column
- Has two webhook source columns

### Known Columns

| Column | Type | Source | Purpose |
|---|---|---|---|
| **Webhook source column 1** | Webhook inbound | Smartlead | Receives positive reply data (domain, prospect name, email, reply content) |
| **Webhook source column 2** | Webhook inbound | Datagen | Receives intel report URL after Datagen completes processing |
| **SLED Signal Bullets** | Text (LLM-generated) | Datagen → Clay | Top signals summarized as contextual bullets for outbound copy and intel reports |

### Known Automations / Actions

| Trigger | Action | Destination |
|---|---|---|
| New row from webhook source 1 (positive reply) | HTTP request to Datagen | Datagen cloud agent |
| Webhook source 2 populated (report URL received) | Slack message | #intent-reports |

{{UNKNOWN: exact automation configurations — need to verify in workspace}}

## Data Flow Through the Workbook

```
INBOUND:
  Smartlead webhook → webhook source col 1
    Payload {{UNKNOWN: exact fields — check Smartlead docs or test}}: domain, prospect name, prospect email, reply text, campaign ID

PROCESSING:
  Clay triggers HTTP request to Datagen with domain + context
  [Datagen processes asynchronously]

RETURN:
  Datagen webhook → webhook source col 2
    Payload {{UNKNOWN: define during Datagen agent build}}: report URL, possibly signal count, tier, DM info

OUTBOUND:
  Clay sends Slack message to #intent-reports
    Contents: @BDR tag, prospect info, report link, DM card (if available)
```

## Integration Points

| System | Direction | Method |
|---|---|---|
| Smartlead | Inbound | Webhook (positive reply trigger) |
| Datagen | Outbound → Inbound | HTTP request out, webhook return |
| Slack | Outbound | Slack integration (message to #intent-reports) |
| Supabase | Indirect | Via Datagen (not queried directly from Clay) |
| Starbridge API | Indirect | Via Datagen (not queried directly from Clay) |

## Enrichment in This Workbook

The workbook likely includes enrichment columns for prospect/account data. {{UNKNOWN: which enrichment providers are configured and in what order — need to check workspace}} Standard Clay enrichment patterns that may be in use:

- Email verification (ZeroBounce or similar)
- Company data (firmographics, headcount, industry)
- Contact data (title, LinkedIn URL, phone)
- Waterfall enrichment (FullEnrich → Clay providers)

{{UNKNOWN: which enrichment providers are configured and in what order — check workspace}}

## Things to Explore in the Workspace

High priority (needed for V1):
- [ ] Exact webhook source column configurations and payload mapping
- [ ] What fields from Smartlead webhook are available (and what's the payload schema?)
- [ ] HTTP request action config: what URL does it hit? What payload does it send?
- [ ] Slack action config: what's the message template? How is the BDR tag determined?
- [ ] Are there views/filters that segment by campaign, tier, or status?

Medium priority (V2):
- [ ] Enrichment provider order and configuration
- [ ] Any AI/LLM columns (Clay AI prompts for signal processing)
- [ ] How account tier (T0-T3) is stored/determined
- [ ] Connection to Boiler Room workbook (shared data? separate tables?)

Lower priority:
- [ ] Historical data: how many rows? Date range?
- [ ] Any Clay formulas in use
- [ ] Export/reporting configurations
