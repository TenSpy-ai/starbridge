# Playbook: Operator Checklist (Hagel)

## Purpose
Daily operating checklist for the fulfillment operator. Currently Hagel runs this. As automation replaces manual steps, this checklist shrinks — but monitoring responsibilities grow.

---

## Current State Checklist (Manual)

### Morning Routine (Philippines timezone — starts before US business hours)
- [ ] Check Smartlead for overnight positive replies
- [ ] For each positive reply:
  - [ ] Run endgame-lookup for the domain
  - [ ] Run Starbridge Slack app for DM info
  - [ ] Process signals through Gemini
  - [ ] Generate Gamma report
  - [ ] Post Message 1 + Message 2 to #intent-reports
- [ ] Check #intent-reports for any unacknowledged dispatches from previous day
- [ ] Flag stale dispatches to Henry

### Throughout the Day
- [ ] Monitor Smartlead for new positive replies (continuous)
- [ ] Fulfill each reply within target SLA {{UNKNOWN: what's the current SLA? 1 hour? Same business day?}}
- [ ] Respond to BDR questions in #intent-reports threads
- [ ] Update Henry on any issues or unusual patterns

### End of Day
- [ ] Confirm all positive replies for the day have been fulfilled
- [ ] Note any pending items (e.g., DM info still being researched)
- [ ] {{UNKNOWN: any reporting or logging Hagel does?}}

---

## V1 Future State Checklist (Automated + Monitoring)

### Morning Routine
- [ ] Check #intent-reports for overnight automated dispatches — confirm they look correct
- [ ] Spot-check 1–2 report links for quality (signals relevant? formatting correct?)
- [ ] Check for any error messages from the pipeline ("report generation failed", "zero signals found")
- [ ] Fulfill any failed/skipped reports manually using fallback procedure

### Throughout the Day
- [ ] Monitor #intent-reports for anomalies (wrong BDR tagged, bad data, broken links)
- [ ] Handle edge cases the pipeline can't (territory adjustments, packaging notes, Henry's overrides)
- [ ] Respond to BDR questions about intel content
- [ ] Add operator context to automated dispatches where needed (threading in Slack)

### Weekly
- [ ] Review report quality trends — are LLM-generated bullets as good as Gemini+manual?
- [ ] Track pipeline reliability — how many failures/fallbacks this week?
- [ ] Report to Henry: volume, quality, issues, improvement ideas

---

## V3 Future State (Fully Automated — Monitoring Only)

### Daily
- [ ] Review the daily digest {{TBD: automated summary of pipeline activity}}
- [ ] Investigate any flagged anomalies
- [ ] Handle exceptional cases that require human judgment

### Hagel's Role Evolution

| Phase | Primary Role | Time per Reply |
|---|---|---|
| Current | Full manual fulfillment | 15–60 min |
| V1 | Monitoring + fallback + edge cases | 2–5 min (most are automated) |
| V2 | Quality assurance + operator context | 1–2 min |
| V3 | Exception handling only | < 1 min (most need zero intervention) |

As automation matures, Hagel's value shifts from execution to quality control and exception handling. He becomes the "air traffic controller" — not flying the planes, but making sure none crash.

---

## Quality Control Checks

When spot-checking automated reports:

| Check | What to Look For | Action if Wrong |
|---|---|---|
| Signal relevance | Are the top signals actually relevant to this account? | Flag for LLM prompt tuning |
| Signal freshness | Are signals recent or stale? | Check Supabase data freshness |
| Bullet quality | Do SLED Signal Bullets make sense? Are they specific or generic? | Compare to Gemini baseline; adjust prompts |
| Report formatting | Does the page render correctly? Any broken sections? | File bug for report generation |
| DM accuracy (V2) | Is the DM info correct? Right person, right contact details? | Cross-check with Starbridge platform |
| BDR assignment | Is the right BDR tagged? | Check assignment logic in Clay |
| Link functionality | Does the report URL work? | Regenerate if broken |
