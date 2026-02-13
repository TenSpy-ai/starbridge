# Template: Slack Dispatch (Message 1 — New Positive Reply)

## Standard Dispatch

```
@{BDR} — new positive response from {ProspectName} of {Company}, {ProspectEmail}!

Custom intel and intent report coming your way shortly.

"{ReplySnippet}"
```

## Dispatch with Operator Notes

```
@{BDR} — new positive response from {ProspectName} of {Company}, {ProspectEmail}!

Custom intel and intent report coming your way shortly.

"{ReplySnippet}"

Notes:
- {Note1}
- {Note2}
```

### Common Operator Notes (Copy/Adapt)

**Territory:**
```
Not CA; focus on MD/WV/VA/TN/KY
```

**Scheduling:**
```
Availability 12:30–3:00 EST — propose times in that window
```

**Demo request:**
```
They asked for a demo — move fast, lead with scheduling
```

**Forward expected:**
```
Likely to forward internally — reply in original thread, make email self-contained
```

**Urgency:**
```
High-value account — prioritize this one
```

## Variable Reference

| Variable | Source | Example |
|---|---|---|
| `{BDR}` | BDR assignment logic | `@Jorge Salas` |
| `{ProspectName}` | Smartlead webhook: first_name + last_name | `Sarah Chen` |
| `{Company}` | Smartlead webhook: company_name | `GovTech Solutions` |
| `{ProspectEmail}` | Smartlead webhook: email | `sarah@govtech.com` |
| `{ReplySnippet}` | Smartlead webhook: reply body (truncated) | `This looks interesting — can you send more details?` |

## Clay Automation Notes

In the automated pipeline, this message is sent by Clay's Slack action immediately when the Smartlead webhook arrives. The Clay formula needs to:
1. Map the correct BDR @-mention {{UNKNOWN: Slack user IDs needed for @-mentions in API}}
2. Extract and truncate the reply snippet (first 1–2 sentences)
3. Determine if any automated notes apply (e.g., if reply text contains "demo" → add demo note)
