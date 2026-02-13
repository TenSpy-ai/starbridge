# Smartlead Webhook — Positive Reply Trigger

## Purpose

The Smartlead positive reply webhook is the **entry point to the entire automated fulfillment pipeline**. When a prospect replies positively to an outbound email, this webhook fires and sends data to Clay, which kicks off the Datagen processing chain.

## Current Status

{{UNKNOWN: is this webhook already configured in Smartlead, or does it need to be set up from scratch? If it exists, what URL is it pointing to?}}

## What We Need the Webhook to Send

Based on the downstream pipeline requirements, the webhook payload needs to include enough data for Clay to:
1. Identify the prospect's company (domain) — for Supabase signal lookup
2. Identify the prospect (name, email) — for Slack dispatch and report personalization
3. Provide reply context — for operator/BDR situational awareness
4. Link back to the campaign/sequence — for tracking and multi-signal context

### Required Fields

| Field | Why It's Needed | Used By |
|---|---|---|
| **Prospect email** | Identify who replied; included in Slack dispatch | Clay → Slack |
| **Company domain** | Primary key for Supabase signal lookup and SB API queries | Clay → Datagen → Supabase |
| **Prospect name** (first + last) | Personalization in Slack dispatch and intel report | Clay → Slack |

### Highly Desired Fields

| Field | Why It's Needed | Used By |
|---|---|---|
| **Reply text / body** | Operator context — what did the prospect say? Changes BDR response tone and urgency | Clay → Slack dispatch |
| **Campaign ID / name** | Track which campaign generated the reply; multi-signal context (which signals were already sent?) | Clay, tracking |
| **Sequence step number** | Know which email they replied to (email 1 vs. email 3 = different context) | Clay, multi-signal logic |
| **Prospect company name** | Display name for Slack dispatch (domain alone isn't human-readable) | Clay → Slack |

### Nice to Have Fields

| Field | Why It's Needed | Used By |
|---|---|---|
| **Reply timestamp** | Time-to-response tracking | Reporting |
| **Prospect title** | Additional context for tier assignment | Clay |
| **Lead status / tags** | If Smartlead has any classification on the reply | Clay |
| **Thread ID / message ID** | Reference for BDR to find the thread in Smartlead | Slack dispatch |

## Expected Payload Structure

{{UNKNOWN: actual Smartlead webhook payload schema — the structure below is a best guess based on typical webhook patterns and what we need downstream. Must verify against Smartlead docs or test.}}

```json
{
  "event": "reply",
  "reply_type": "positive",
  "prospect": {
    "email": "john@acmegov.com",
    "first_name": "John",
    "last_name": "Smith",
    "company_name": "ACME Government Solutions",
    "company_domain": "acmegov.com"
  },
  "reply": {
    "body": "This looks interesting — can you send more details?",
    "timestamp": "2026-02-04T14:30:00Z"
  },
  "campaign": {
    "id": "camp_abc123",
    "name": "Q1 Contract Expiration - LMS",
    "sequence_step": 2
  },
  "metadata": {
    "thread_id": "thread_xyz",
    "message_id": "msg_789"
  }
}
```

## Webhook Destination

**Target URL**: Clay webhook endpoint for the Project Endgame workbook, webhook source column 1.

{{UNKNOWN: the exact Clay webhook URL — this is generated when the webhook source column is configured in Clay}}

## Trigger Conditions

{{UNKNOWN: what exactly triggers the "positive reply" classification in Smartlead? Options:}}
- Does Smartlead auto-classify reply sentiment? (positive/negative/neutral)
- Is it manual tagging by Hagel?
- Is it any reply to an outbound campaign (regardless of sentiment)?
- Is there keyword-based or AI-based filtering?

This matters because:
- If ALL replies trigger the webhook, Clay/Datagen needs filtering logic to only process genuinely positive ones
- If only "positive" replies trigger it, we need to understand Smartlead's classification accuracy
- If it's manual, the automation benefit is limited (Hagel still has to triage first)

## How This Fits in the Pipeline

```
Smartlead (positive reply detected)
  │
  │ webhook fires
  │
  ▼
Clay (Project Endgame, webhook source col 1)
  │
  │ Clay extracts domain from payload
  │ Clay sends HTTP request to Datagen with domain + context
  │ Clay simultaneously sends Slack notification: "New positive reply incoming"
  │
  ▼
Datagen (async processing begins)
```

## Smartlead Webhook Documentation

{{UNKNOWN: link to Smartlead's official webhook docs — search their docs/help center for webhook configuration}}

Things to look up:
- [ ] Available webhook events (is "positive reply" a built-in event type?)
- [ ] Payload schema per event type
- [ ] Authentication (does the webhook include a signing secret?)
- [ ] Retry behavior (what happens if Clay doesn't respond 200?)
- [ ] Rate limiting (if a campaign generates 100 positive replies in an hour, do all webhooks fire?)

## Fallback Plan

If Smartlead's native webhook doesn't provide what we need:
- **Option A**: Use Smartlead's API to poll for new replies on a schedule (less real-time, but more control over payload)
- **Option B**: Use a Zapier/Make intermediary to reshape the webhook payload before it hits Clay
- **Option C**: Have Hagel continue manual triage but with a simpler trigger (e.g., he just inputs a domain into a Slack command, which triggers the pipeline) — this is essentially the current flow with less manual work downstream

{{TBD: fallback approach if native webhook is insufficient — decide after investigating Smartlead's capabilities}}
