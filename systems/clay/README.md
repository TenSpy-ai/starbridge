# Clay — System Overview

## Role in the Stack

Clay is the **orchestration hub** for Project Endgame. It sits at the center of the pipeline: receiving webhooks from Smartlead, routing data to Datagen for processing, receiving report URLs back, enriching contacts, and dispatching notifications to Slack.

## Workspace

- **Workspace ID**: `484780`
- **Workspace URL**: [https://app.clay.com/workspaces/484780/home/f_0t6nh48BDBiBnAvajMt](https://app.clay.com/workspaces/484780/home/f_0t6nh48BDBiBnAvajMt)

## Key Workbooks

| Workbook | Purpose | Details |
|---|---|---|
| **Project Endgame** | Main workbook. Positive reply pipeline, signal matching, webhook routing. | [project-endgame.md](./project-endgame.md) |
| **Boiler Room** | Converts signals into concise intel snippets for BDRs hammering the phones via Nooks. | [boiler-room.md](./boiler-room.md) |

## How Clay Fits in the Positive Reply Flow

```
Smartlead (positive reply webhook)
  → Clay receives in webhook source column 1
  → Clay pushes domain + context to Datagen
  → [Datagen does processing]
  → Datagen sends report URL back to Clay via webhook
  → Clay receives URL in webhook source column 2
  → Clay sends Slack message to #intent-reports
```

Clay is the **router**, not the processor. Heavy lifting (Supabase queries, LLM processing, report generation) happens in Datagen. Clay handles:
- Receiving inbound data (webhooks)
- Enrichment (waterfall for contacts)
- Routing to downstream systems
- Slack dispatch

## What Clay Does Well Here

- Webhook ingestion and table management
- Multi-provider enrichment waterfalls (FullEnrich → Clay providers)
- Slack integration for dispatch
- Conditional logic for routing (which BDR, which tier, which campaign)
- HTTP request actions (calling Datagen endpoints)

## What Clay Doesn't Do (Hence Datagen)

- Complex multi-step orchestration (query Supabase → LLM → SB API → generate report)
- LLM processing of signals (ranking, summarization, bullet generation)
- Dynamic page/report generation (Notion/Webflow)
- Polling or async workflows (Clay is synchronous per row)

## Clay in the Enrichment Stack

For contact enrichment (workstream 3), Clay plays a specific role:

```
FullEnrich (initial, cheaper)
  → Clay waterfall (fills gaps, more expensive but more providers)
    → Manual research (edge cases)
```

Clay has ~65% LinkedIn coverage due to enterprise API restrictions. The team supplements with custom scrapers from smaller vendors to get closer to 100%. {{UNVERIFIED: 65% figure from Henry's state of the union — may vary by segment}}

## Access & Permissions

- Jeremy has workspace access via the link above
- Kushagra is the primary Clay builder (Clay Cup semi-finalist)
- Need to explore: table structures, column headers, automation configs, webhook endpoints

## Key Things to Document (As Discovered)

- [ ] All tables in Project Endgame workbook
- [ ] Column headers and types for each table
- [ ] Webhook source configurations (inbound URLs, payload mapping)
- [ ] Automation/action configs (what triggers what)
- [ ] Enrichment waterfall setup (which providers, in what order)
- [ ] Slack integration config (which channel, message template)
- [ ] Any Clay formulas or AI prompts in use
- [ ] Boiler Room table structure and how it differs from Project Endgame
