# Datagen Cloud Agents — Pipeline Spec

## Overview

This file specifies the Datagen cloud agents that power the positive reply → intel report pipeline. Each agent is a deployed Python endpoint callable via HTTP.

## Agent 1: Intel Report Generator (Primary Agent)

**Name**: `starbridge_intel_report` {{TBD: final deployment name}}
**Trigger**: HTTP POST from Clay when a positive reply is received
**Output**: Webhook back to Clay with report URL + metadata

### Pipeline Steps (Pseudocode)

```python
# Step 1: Receive input from Clay
domain = input["domain"]
prospect_name = input["prospect_name"]
prospect_email = input["prospect_email"]
reply_text = input.get("reply_text", "")
campaign_id = input.get("campaign_id", "")
sequence_step = input.get("sequence_step", 0)

# Step 2: Query Supabase for all signals
signals = query_supabase(domain)
# {{UNKNOWN: actual query — see /systems/supabase/queries.md}}

if len(signals) == 0:
    # {{TBD: handle zero-signal case}}
    # Options: skip, minimal report, notify operator
    pass

# Step 3: LLM Signal Processing
# Feed all signals to LLM, get back ranked top signals + bullets
llm_result = process_signals_with_llm(
    signals=signals,
    prospect_context={
        "name": prospect_name,
        "email": prospect_email,
        "reply": reply_text,
        "campaign": campaign_id,
        "email_number": sequence_step
    }
)
# llm_result contains:
#   - top_signals (list of 5-10 ranked signals)
#   - sled_signal_bullets (contextual summaries)
#   - relevance_reasoning (why these signals matter for this prospect)

# Step 4: Query Starbridge API for buyer attributes (V2)
# {{UNKNOWN: blocked on Yurii — skip in V1}}
buyer_attributes = None
if STARBRIDGE_API_ENABLED:  # V2 flag
    buyer_attributes = query_starbridge_api(domain)
    # buyer_attributes contains:
    #   - dm_name, dm_title, dm_email, dm_phone
    #   - budget / spend data
    #   - account logo URL
    #   - buyer location
    #   - buyer type

# Step 5: Determine tier
tier = determine_tier(
    signal_count=len(signals),
    has_dm=buyer_attributes is not None,
    # {{UNKNOWN: other tier criteria — account value? signal strength?}}
)

# Step 6: Assemble report content
report_content = assemble_report(
    top_signals=llm_result["top_signals"],
    bullets=llm_result["sled_signal_bullets"],
    buyer_attributes=buyer_attributes,
    prospect_name=prospect_name,
    domain=domain,
    tier=tier
)

# Step 7: Generate report page
report_url = generate_report_page(report_content)
# {{TBD: Notion vs. Super.so vs. Webflow generation}}

# Step 8: Webhook back to Clay
send_webhook_to_clay(
    report_url=report_url,
    signal_count=len(signals),
    top_signals_used=len(llm_result["top_signals"]),
    tier=tier,
    dm_info=buyer_attributes.get("dm") if buyer_attributes else None,
    processing_time=elapsed_time
)
```

### LLM Prompt Design (Step 3)

{{UNKNOWN: final prompt — below is a starting framework. Neil's existing Gemini prompts should be reviewed and incorporated.}}

**System prompt concept:**

```
You are an intelligence analyst for Starbridge, a SLED (State/Local/Education) 
procurement intelligence platform. 

You will receive a list of procurement signals for a specific government/education 
buyer account. Your job is to:

1. RANK the signals by relevance and urgency (most actionable first)
2. SELECT the top {N} signals (where N = 5-10 depending on signal quality)
3. GENERATE a "SLED Signal Bullet" for each selected signal:
   - 1-2 sentences that explain what the signal means in plain business English
   - Why it matters for a vendor selling to this buyer
   - What action it implies (e.g., "contract expiring = replacement opportunity")
4. PROVIDE a brief relevance summary connecting the signals to the prospect

Context about the prospect who replied:
- Name: {prospect_name}
- Company domain: {domain}
- They replied to email #{sequence_step} of a campaign
- Their reply: "{reply_text}"

Signal data:
{signals_json}

Respond in JSON format:
{
  "top_signals": [...],
  "sled_signal_bullets": [...],
  "relevance_summary": "..."
}
```

**Ranking criteria** {{TBD: define with team input}}:
- Recency (newer signals > older)
- Urgency (contract expiring soon > general budget discussion)
- Specificity (named vendor/product mention > generic category)
- Relevance to reply context (if they replied about LMS, LMS signals rank higher)
- Signal type priority {{UNKNOWN: is there a hierarchy? e.g., contract > board mention > RFP?}}

### Report Page Generation (Step 7)

{{TBD: final format — three options under consideration}}

**Option A: Notion (V1 — fastest to implement)**
```python
# Using Notion API to create a page
# Pros: fast to build, easy to iterate, supports rich content
# Cons: not branded, Notion URLs aren't professional-looking
# Can be upgraded to Super.so for custom domain + branding

page = notion_client.pages.create(
    parent={"database_id": NOTION_DB_ID},
    properties={
        "Name": {"title": [{"text": {"content": f"Intel Report: {domain}"}}]},
        # ... other properties
    },
    children=[
        # Header block
        # Signal bullets blocks
        # DM card block (V2)
        # Budget/attributes blocks (V2)
    ]
)
report_url = page["url"]
```

**Option B: Webflow (V2 — branded)**
```python
# Using Webflow CMS API to create a collection item
# Pros: fully branded, professional URLs, Nastia's design
# Cons: more setup, requires Webflow CMS collection, template work
# {{UNKNOWN: does Starbridge have a Webflow account?}}
```

**Option C: Super.so (V1.5 — Notion + branding)**
```python
# Notion page published via Super.so for custom domain + styling
# Pros: Notion speed + custom branding + professional URLs
# Cons: additional tool/cost, some styling limitations
# {{UNKNOWN: is Super.so already in the stack?}}
```

### Error Handling

| Error | Behavior | Notification |
|---|---|---|
| Supabase query fails | Retry once (2s delay). On second failure: send error to Clay webhook. | Slack message: "⚠️ Signal lookup failed for {domain} — manual process needed" |
| Zero signals returned | {{TBD: options below}} | — |
| LLM processing fails | Fall back to raw signal list (no ranking/bullets). Generate report with unprocessed signals. | Log warning, proceed |
| LLM returns malformed output | Retry with simplified prompt. On second failure: use raw signals. | Log warning, proceed |
| SB API fails (V2) | Skip buyer attributes. Proceed with Tier 1 report. | Log info (expected in V1) |
| Report generation fails | Send signal data to Clay as structured text instead of a page URL. Clay Slack dispatch includes text summary instead of link. | Slack message includes "[report generation failed — text summary below]" |
| Webhook back to Clay fails | Retry 3x with exponential backoff. On final failure: post directly to Slack via Datagen. | Slack fallback message |

**Zero signals handling** {{TBD: pick one}}:
- **Option A**: Skip entirely — don't generate a report, send Slack message "No signals found for {domain}" and let operator handle manually
- **Option B**: Generate a minimal report with buyer attributes only (V2, when SB API is live)
- **Option C**: Generate a report with a generic "we're researching this account" message and schedule a follow-up check

### Performance Targets

| Metric | V1 Target | V3 Target |
|---|---|---|
| End-to-end processing time | < 30 seconds | < 15 seconds |
| Supabase query | < 2 seconds | < 1 second |
| LLM processing | < 15 seconds | < 10 seconds |
| SB API query (V2) | N/A | < 5 seconds |
| Report generation | < 10 seconds | < 5 seconds |
| Webhook delivery | < 2 seconds | < 1 second |

## Agent 2: Signal Refresher (Future — V3)

{{TBD: not in V1 scope — placeholder for future development}}

**Purpose**: Periodically re-check Supabase for new signals on accounts that already have reports, and update existing reports with fresh intel.

**Use case**: A prospect received an intel report 2 weeks ago and hasn't booked a meeting. New signals have appeared since then. The refresher agent updates the report and triggers a follow-up sequence.

## Agent 3: Batch Report Generator (Future — V3)

{{TBD: not in V1 scope — placeholder for future development}}

**Purpose**: Generate intel reports in bulk for campaign launches (e.g., the Monday 10x campaign). Instead of waiting for positive replies, pre-generate reports for top-priority accounts so they're ready instantly when replies come in.

**Use case**: 10x campaign launches Monday. Pre-generate reports for T0 accounts so response time is near-zero for the highest-value prospects.

## Implementation Checklist

### Prerequisites
- [ ] Datagen account set up ($50 expense)
- [ ] Claude Max account active ($200 expense)
- [ ] Supabase access + schema confirmed (Kushagra meeting)
- [ ] {{TBD: Notion vs. Webflow vs. Super.so}} decision made
- [ ] Notion API key (if Notion chosen) or Webflow API key (if Webflow)

### V1 Build
- [ ] Create Datagen cloud agent: `starbridge_intel_report`
- [ ] Implement Supabase query (Step 2)
- [ ] Implement LLM signal processing (Step 3) — start with Neil's Gemini prompts adapted
- [ ] Implement Notion page generation (Step 7, Option A)
- [ ] Implement webhook back to Clay (Step 8)
- [ ] Test with 10 sample accounts
- [ ] Configure Clay HTTP request action to call the agent
- [ ] Configure Clay to receive return webhook
- [ ] End-to-end test: Smartlead webhook → Clay → Datagen → report → Clay → Slack

### V2 Additions
- [ ] Add Starbridge API queries (Step 4) — after Yurii unblocks access
- [ ] Add DM contact card to reports
- [ ] Add buyer attributes (budget, logo, location)
- [ ] Implement tier assignment logic (Step 5)
- [ ] Upgrade report template with Nastia's branding

### V3 Additions
- [ ] Signal Refresher agent
- [ ] Batch Report Generator agent
- [ ] Tier 3 auto-generation (relevancy analysis + pitch angle via LLM)
- [ ] Performance optimization (parallel queries, caching)
- [ ] API endpoint abstraction (input domain → poll for report URL)
  *END GOAL from onboarding notes: "make an API where input is a domain, etc, and its response is an ID that, when POLL'd, returns URL/content." This async polling pattern is the team's long-term architectural vision for the intel pipeline.*
