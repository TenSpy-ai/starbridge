# Template: Follow-Up Sequence (Post Intel Delivery)

{{UNVERIFIED: Follow-ups 1-3 below are drafted frameworks, not sourced from existing team templates. Only Follow-Up 4's DM-later pattern is sourced from the 2/4 onboarding notes. All need Henry/BDR review before use.}}

After the initial payload email, if the prospect doesn't respond, a follow-up sequence keeps the thread alive. This is currently manual (BDR judgment); future state may be partially automated via Smartlead.

---

## Follow-Up 1 — Nudge (Day 2-3 after payload)

**Subject**: RE: (same thread)

```
Hi {FirstName},

Just checking in — did you get a chance to look at the 
intelligence report we put together for {Company}?

{ReportURL}

Happy to walk through the highlights on a quick call.

{BDRName}
```

**Notes:** Short, low-pressure. Just re-surface the link.

---

## Follow-Up 2 — New Value (Day 5-7)

**Subject**: RE: (same thread)

```
Hi {FirstName},

Wanted to flag — we're seeing {NewSignalOrUpdate} related to 
{Company}'s procurement activity.

This adds to what we shared in your intel report: {ReportURL}

Worth a 15-minute conversation to walk through what we're seeing?

{BDRName}
```

**Notes:** Introduce a new data point. Can pull from:
- A new signal that appeared since the report was generated
- A different angle on an existing signal (budget → timeline → DM)
- A relevant industry/peer benchmark

{{TBD: can this be automated? If the Datagen Signal Refresher agent (V3) detects new signals, it could trigger this follow-up with fresh content.}}

---

## Follow-Up 3 — Social Proof (Day 10-14)

**Subject**: RE: (same thread)

```
Hi {FirstName},

{SimilarBuyerType} like {PeerOrganization} have been using 
intelligence like this to get ahead of their procurement cycles.

Your report is still available here: {ReportURL}

Would love to show you how this looks in practice — 15 minutes?

{BDRName}
```

**Notes:** Shift from "here's your data" to "here's what peers are doing." {{UNKNOWN: do we have social proof examples? Case studies? Customer references?}}

---

## Follow-Up 4 — Break-Up (Day 21+)

**Subject**: RE: (same thread)

```
Hi {FirstName},

I don't want to keep following up if the timing isn't right. 
Your intel report will stay live if you want to revisit: {ReportURL}

If anything changes on your end, I'm here.

{BDRName}
```

**Notes:** Graceful close. Leaves the door open without pressure.

---

## Automated Mini-Sequence (Future — V2)

From the onboarding notes, Henry mentioned the idea of an automated mini follow-up sequence in Smartlead after intel delivery. This would replace manual BDR follow-ups for non-responsive prospects.

```
Day 0:  Payload email (BDR manual — triggered by dispatch)
Day 3:  Auto follow-up 1 — nudge (Smartlead automated)
Day 7:  Auto follow-up 2 — new angle (Smartlead automated, content from Datagen?)
Day 14: Auto follow-up 3 — social proof (Smartlead automated)
Day 21: Auto break-up (Smartlead automated)
```

{{TBD: should the automated sequence pull dynamic content from Datagen (new signals, updated intel) or use static templates?}}

{{UNKNOWN: can Smartlead trigger automated follow-ups based on a webhook or API call (i.e., "start sequence X for prospect Y"), or does this need to be set up manually per prospect?}}

---

## Phone Follow-Up Cadence

Parallel to email follow-ups, BDRs should be calling via Nooks:

| Timing | Call Action |
|---|---|
| Day 0 (with payload) | Call immediately after sending email |
| Day 1 | Call if no response to email |
| Day 3 | Call with follow-up 1 |
| Day 7 | Call if still no engagement |
| After Day 7 | Reduce to weekly attempts |

{{UNKNOWN: is this the actual cadence, or does the team use a different rhythm?}}
