# Playbook: DM-Later Flow

## Trigger
A positive reply is fulfilled with a Tier 1 report (signals only), and DM info is not yet available. The DM info will be delivered later as a separate follow-up.

## Why This Flow Exists

DM info (decision maker name, title, email, phone) takes longer to source than intent signals. The core architectural decision: **don't delay the intel report waiting for DM info.** Ship the signals immediately, deliver DM info as a follow-up.

This matters because:
1. Response time is the #1 lever for converting positive replies to meetings
2. Signals alone are already valuable — the prospect gets intel they can act on
3. DM info can arrive minutes, hours, or a day later depending on source availability
4. Decoupling these two deliverables removes the slower dependency from the critical path

---

## The Flow

```
Positive reply detected
  │
  ├── IMMEDIATE (< 2 min)
  │   ├── Message 1: "New positive reply — intel incoming"
  │   └── Message 2: "Intel is ready" + report link (signals only, Tier 1)
  │         └── BDR sends payload email + calls immediately
  │
  └── DEFERRED (minutes to hours later)
      └── Message 3: "DM info ready for {Company}"
            ├── DM name, title, email, phone
            └── BDR sends follow-up email or uses info on next call
```

---

## Message 3 Template (DM Follow-Up)

```
@{BDR} — DM info is ready for {ProspectName} of {Company}:

- Name: {DMName}
- Title: {DMTitle}
- Email: {DMEmail}
- Phone: {DMPhone}

Notes: {any context about the DM — procurement influence, department, relationship to the signals}
```

### Current State (Manual)
Hagel posts Message 3 when he gets the info from the Starbridge Slack app. Sometimes this is in the same fulfillment session; sometimes it's hours later.

### Future State (V2 — Automated)
Two possible architectures:

**Option A: Deferred webhook**
- Datagen agent attempts SB API query for DM info during pipeline execution
- If DM info is found: include in Message 2 (Tier 2 report)
- If DM info is NOT found: return Tier 1 report immediately, schedule a retry
- Retry queries SB API again after a delay (15 min? 1 hour?)
- If found on retry: send Message 3 via Clay → Slack

**Option B: Separate agent**
- Intel report agent always returns Tier 1 (signals only) immediately
- A separate "DM lookup agent" runs in parallel or on a delay
- When DM info is found: triggers Message 3

{{TBD: which architecture — depends on SB API reliability and DM info availability patterns. If DM info is almost always available, Option A is simpler. If it's often delayed, Option B is cleaner.}}

---

## BDR Actions for DM-Later

### When you receive the Tier 1 report (no DM yet):

1. **Send the payload email immediately** — don't wait for DM info
2. Frame the report around signals: "We're tracking these procurement signals for your district..."
3. Offer to share DM contacts on a call: "Happy to also share the decision-maker contacts we've identified — do you have 15 minutes?"
4. This positions the DM info as a **reason to take the meeting**, not just free data

### When DM info arrives (Message 3):

1. **If you haven't connected yet**: Send a short follow-up email:
```
Hi {FirstName},

Quick follow-up — we also identified the key decision maker 
for this initiative at {Company}:

{DMName}, {DMTitle}
{DMEmail}

Happy to share more context on how to navigate this procurement 
process. Available for a quick call?
```

2. **If you're already in conversation**: Use DM info in your next call or email naturally. No need for a separate "DM delivery" email.

3. **If a meeting is already booked**: Add DM info to the meeting prep notes. Mention on the call: "We've also identified {DMName} as a key stakeholder for this initiative."

---

## Tracking

{{UNKNOWN: how is the DM-later flow tracked? Is there a status field in Clay? A tag in Smartlead? Or is it purely managed via Slack threads?}}

Ideal tracking (future state):
- Clay row has a "DM status" field: `pending` → `delivered` → `used`
- When Message 3 fires, status updates to `delivered`
- When BDR confirms they've used the info, status updates to `used`
- Reporting: "% of positive replies where DM info was delivered within 1 hour"

---

## Edge Cases

| Scenario | Handling |
|---|---|
| DM info never found | After 24 hours with no DM info, close the DM-later loop. BDR relies on signals only. {{TBD: is there a fallback for DM research — manual lookup?}} |
| Multiple DMs found | Include all in Message 3. Note which is most relevant to the signals. |
| DM info found but wrong person | Operator/Hagel quality-checks before posting. If automated, LLM confidence threshold. |
| Prospect already booked meeting before DM arrives | Add DM info to meeting prep, don't send a separate email. |
| Prospect went cold before DM arrives | Still deliver the DM info — BDR can use it for re-engagement. |
