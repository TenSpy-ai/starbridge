# Playbook: Positive Reply SOP

## Trigger
A prospect replies positively to a Smartlead outbound email.

## Who Executes
- **Current state**: Hagel (manual, end-to-end)
- **V1 future state**: Automated pipeline (Smartlead → Clay → Datagen → Clay → Slack), with Hagel as fallback
- **V3 future state**: Fully automated, Hagel monitors only

---

## Current State Process (Hagel — Manual)

### Step 1: Detect the positive reply
- Monitor Smartlead inbox for new replies
- Identify which replies are genuinely positive vs. neutral/negative/OOO
- {{UNKNOWN: does Hagel have any filters/alerts, or is this pure manual scanning?}}

### Step 2: Pull intent signals
- Open Slack
- Use **endgame-lookup** bot: input the prospect's company domain
- Bot returns all intent signals from Supabase for that account

### Step 3: Pull buyer attributes
- Use **Starbridge Slack app**: input the domain
- Returns DM info, buyer attributes, custom data from the platform

### Step 4: Process through Gemini
- Take the signal output from Step 2
- Feed into Gemini using Neil's prompts
- Gemini produces succinct intel bullets

### Step 5: Generate Gamma report
- Take Gemini output
- Upload into Gamma
- Generate visual report/page
- Copy the Gamma link

### Step 6: Post Message 1 to #intent-reports
```
@{BDR} — new positive response from {Name} of {Company}, {Email}!
Custom intel and intent report coming your way shortly.
"{reply quote}"
Notes: {context}
```

### Step 7: Post Message 2 to #intent-reports
```
@{BDR} — custom intel is ready for {Name} of {Company}, {Email}.
Gamma Link: {URL}
Custom Intel: {DM card if available}
IR Notes: {relevancy/gameplan if Tier 3}
```

### Step 8: Monitor BDR response
- Confirm BDR has acknowledged the dispatch
- Answer questions in thread if BDR needs context
- Escalate to Henry if BDR is unresponsive

**Typical time**: 15–60 minutes per positive reply, depending on signal density and DM availability.

---

## Future State Process (Automated Pipeline — V1)

### Step 1: Smartlead detects positive reply
- Smartlead webhook fires automatically
- {{UNKNOWN: trigger condition — see /systems/smartlead/webhook-spec.md}}

### Step 2: Clay receives webhook
- Clay Project Endgame workbook, webhook source column 1
- Clay extracts domain and prospect info from payload

### Step 3: Clay sends Message 1 to Slack
- Immediate — before Datagen processing starts
- Tells BDR "positive reply incoming, intel on the way"
- {{TBD: BDR assignment logic — see /systems/slack/intent-reports-format.md}}

### Step 4: Clay calls Datagen
- HTTP POST to Datagen cloud agent with domain + prospect context
- Async — Clay doesn't wait for response

### Step 5: Datagen processes
- Queries Supabase for all signals (replaces endgame-lookup)
- LLM ranks and generates SLED Signal Bullets (replaces Gemini)
- Queries Starbridge API for buyer attributes (V2 — replaces Starbridge Slack app)
- Generates intel report page (replaces Gamma)
- Webhooks result back to Clay

### Step 6: Clay receives Datagen webhook
- Clay Project Endgame workbook, webhook source column 2
- Contains report URL + metadata

### Step 7: Clay sends Message 2 to Slack
- Report link + DM card + any metadata
- BDR can immediately act

### Step 8: BDR acts (human)
- Opens report link, takes screenshot
- Sends payload email in Smartlead
- Calls prospect via Nooks
- Books meeting

**Target time**: < 2 minutes end-to-end (vs. 15-60 minutes manual).

---

## Fallback Procedure

If the automated pipeline fails at any step:

| Failure Point | Detection | Fallback |
|---|---|---|
| Smartlead webhook doesn't fire | No Message 1 in Slack | Hagel monitors Smartlead manually, triggers process at Step 2 |
| Clay doesn't receive webhook | No activity in Clay | Check Smartlead webhook config, re-send manually |
| Datagen processing fails | Message 1 posted but no Message 2 within 5 minutes | Hagel uses endgame-lookup + Starbridge app + Gemini + Gamma (full manual process) |
| Report generation fails | Datagen returns error to Clay | Clay posts "report generation failed — manual fulfillment needed" to Slack. Hagel takes over. |
| Slack message fails | Pipeline completes but no Slack post | Check Clay Slack integration. Post manually with the report URL. |

**Rule**: Every positive reply gets fulfilled. If automation breaks, fall back to manual. Never let a positive reply go unfulfilled because of a technical issue.

---

## Edge Cases

| Scenario | Handling |
|---|---|
| **Negative reply misclassified as positive** | {{TBD: who catches this? If automated classification is wrong, the BDR gets a false dispatch. Need a quick "dismiss" action.}} |
| **OOO reply** | Don't trigger the pipeline. {{UNKNOWN: does Smartlead filter these out?}} |
| **Reply to an old campaign** | Still process — the prospect is showing interest regardless of timing |
| **Same prospect replies twice** | Process the most recent reply. Don't generate duplicate reports. {{TBD: deduplication logic in Clay?}} |
| **Domain has zero signals** | See zero-signal handling in /systems/datagen/agents.md |
| **Prospect replies after hours** | Pipeline runs 24/7. Report is ready when BDR starts their day. |
| **Multiple positive replies in a batch** | Pipeline processes each independently. {{UNKNOWN: any queuing/throttling needed?}} |
