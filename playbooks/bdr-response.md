# Playbook: BDR Response

## Trigger
BDR is @-mentioned in #intent-reports with a new positive reply dispatch.

## Who Executes
BDRs: Jorge Salas, Joseph Williams, Glenn Williams, Jaime Ruiz

---

## Response Sequence

### Step 1: Acknowledge immediately
- React to the Slack message (✅ or 👀) so the team knows you've seen it
- {{UNKNOWN: is there a formal acknowledgment protocol, or is this ad hoc?}}

### Step 2: Wait for Message 2 (if only Message 1 received)
- Message 1 = "positive reply incoming, intel on the way"
- Message 2 = "intel is ready" + report link + DM card
- Typical gap: < 2 minutes (automated) or 15-60 min (manual/Hagel)
- If Message 2 doesn't arrive within a reasonable time, ask in thread

### Step 3: Review the intel report
- Click the report link
- Scan the top signals — what does this prospect's buyer care about?
- Note any DM info (Tier 2+)
- Note any relevancy analysis or pitch angle (Tier 3)

### Step 4: Take a screenshot of the report
- Open the report link in browser
- Screenshot the most visually compelling section (signal summary or header)
- This becomes the visual hook in the payload email

### Step 5: Send the payload email in Smartlead
**Default: send in a separate thread** (enables Apollo sequencing + call tasks)
**Exception: send in the original thread** if Henry indicates the prospect will forward internally

Payload email includes:
1. The report link
2. The screenshot (visual hook — pasted inline)
3. An offer to share DMs on a call
4. {{UNKNOWN: is there a standard email template, or do BDRs freestyle?}}

Example framing:
```
Hi {FirstName},

Thanks for your reply — we put together a custom intelligence report 
for {Company} based on signals we're tracking.

[screenshot]

Here's the full report: {ReportURL}

Happy to walk through what we're seeing and share the decision-maker 
contacts we've identified. Do you have 15 minutes this week?

Best,
{BDRName}
```

### Step 6: Call the prospect via Nooks
- After sending the email, immediately call using Nooks (dialer)
- If prospect answers: reference the report, offer to walk through it live
- If voicemail: leave a brief message referencing the email and report
- Log the call outcome

### Step 7: Book the meeting
- If prospect engages: book directly during call or via calendar link
- Target: get the meeting on the calendar same day
- {{UNKNOWN: what calendar tool is used? Calendly? HubSpot meetings? Direct invite?}}

### Step 8: Update the thread
- Post in the #intent-reports thread with the outcome: "emailed + called, left VM" or "meeting booked for Thursday 2pm"
- {{UNKNOWN: is this expected, or does it only happen sometimes?}}

---

## Decision Tree: Separate Thread vs. Original Thread

```
Positive reply received
  │
  ├── Will prospect likely forward internally?
  │     │
  │     ├── YES → Reply in ORIGINAL thread
  │     │         (keeps context visible to the forwarded recipient)
  │     │
  │     └── NO → Reply in SEPARATE thread (default)
  │               (enables Apollo sequencing + call tasks)
  │
  └── Henry provided specific guidance?
        │
        ├── YES → Follow Henry's instruction
        │
        └── NO → Default to separate thread
```

**How to tell if they'll forward**: Look for cues in the reply text:
- "Let me loop in my team" → original thread
- "I'll share this with our CIO" → original thread
- "Send me more info" → separate thread (standard interest)
- "Can we set up a call?" → separate thread (direct engagement)
- When in doubt → separate thread

---

## DM-Later Flow

If Message 2 arrives without DM info (Tier 1 report — signals only, no contact card):

1. Send the payload email with the report link anyway — don't wait
2. The report is still valuable without DM info
3. DM info may arrive later via a follow-up Slack message
4. When DM info arrives: send a follow-up email or use it on the call

See: [dm-later-flow.md](./dm-later-flow.md)

---

## Handling Operator Notes

Operator notes in the Slack dispatch change your approach:

| Note Type | BDR Action |
|---|---|
| Territory scope ("Not CA; focus on MD/WV/VA/TN/KY") | Tailor conversation to specified region. Don't reference out-of-scope areas. |
| Scheduling constraint ("Availability 12:30–3:00 EST") | Propose meeting times within that window only. |
| Demo request ("They asked for a demo") | Lead with scheduling the demo, not intel discussion. Move fast. |
| Forward expected ("They'll forward internally") | Reply in original thread. Make the email self-contained (prospect won't add context when forwarding). |
| Packaging note ("Expected 12 signals; we surfaced 5") | Frame the demo as where deeper depth happens. Don't oversell the report; sell the conversation. |
| Urgency override ("Drop what you're doing") | Prioritize this over other tasks. Respond within minutes. |

---

## Response Time Expectations

| Priority | Target Response Time | Indicator |
|---|---|---|
| Urgent (Henry override) | < 15 minutes | "Drop what you're doing" in dispatch |
| Standard | < 1 hour during business hours | Normal dispatch |
| After hours | First thing next business day | Dispatch posted outside BDR's working hours |

{{UNKNOWN: are these SLAs confirmed, or aspirational? Get Henry to sign off.}}
