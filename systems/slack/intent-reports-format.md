# #intent-reports — Message Format Reference

## The Two Messages That Run the Machine

Every positive reply generates two Slack messages in `#intent-reports`. This is the confirmed pattern from observing the channel. The automated pipeline must replicate this exact rhythm.

---

## Message 1: "New Positive Response" (Dispatch)

**Purpose**: Alert the BDR that a hot reply came in. Create urgency. Provide enough context for immediate action.

**When sent**: As soon as the positive reply is detected (currently: when Hagel sees it. Future: when Smartlead webhook fires and Clay processes it).

### Template

```
@{BDR} — new positive response from {ProspectName} of {Company}, {ProspectEmail}!

Custom intel and intent report coming your way shortly.

"{ReplySnippet}"

Notes: {territory/scheduling/demo request/forwarding context}
```

### Field Reference

| Field | Source | Required? | Notes |
|---|---|---|---|
| `@{BDR}` | BDR assignment logic | Yes | {{UNKNOWN: how is BDR assignment determined? Round-robin? Territory? Account tier?}} |
| `{ProspectName}` | Smartlead webhook payload | Yes | Full name of the person who replied |
| `{Company}` | Smartlead webhook payload | Yes | Company name |
| `{ProspectEmail}` | Smartlead webhook payload | Yes | Prospect's email address |
| `"{ReplySnippet}"` | Smartlead webhook payload (reply text) | Optional but high-value | Direct quote from the reply. Changes urgency/tone. |
| `Notes` | Contextual — multiple sources | Optional | See operator context section below |

### Operator Context (Notes Field)

These are real patterns observed from Hagel's posts:

| Context Type | Example | When Included |
|---|---|---|
| Territory scoping | "Not CA; focus on MD/WV/VA/TN/KY" | When prospect's territory doesn't match default assumptions |
| Scheduling request | "Availability 12:30–3:00 EST" | When prospect specified time preferences in their reply |
| Demo request | "They asked for a demo — move fast" | When reply explicitly requests a demo |
| Forwarding likely | "They'll likely forward internally — also reply in original thread" | Henry's guidance when internal champions are involved |
| Urgency override | "Drop what you're doing" | High-value accounts or time-sensitive signals |

### Automation Notes for Message 1

In the automated pipeline, Message 1 fires from Clay immediately when the Smartlead webhook arrives — before Datagen has finished processing. This means:

- `{ProspectName}`, `{Company}`, `{ProspectEmail}` come from the webhook payload
- `"{ReplySnippet}"` comes from the webhook payload (reply text field)
- `Notes` are harder to automate — some context (territory, scheduling) could be extracted from reply text via LLM; others require human judgment
- {{TBD: should Message 1 include an automated note like "Intel report processing — ETA ~30 seconds"?}}

---

## Message 2: "Custom Intel Is Ready" (Delivery)

**Purpose**: Deliver the complete intel package so the BDR can send the payload email and start calling immediately.

**When sent**: After fulfillment is complete (currently: when Hagel finishes building the Gamma report. Future: when Datagen returns the report URL to Clay).

### Template

```
@{BDR} — custom intel is ready for {ProspectName} of {Company}, {ProspectEmail}.

Gamma Link: {ReportURL}

Custom Intel (if applicable):
- Name: {DMName}
- Title: {DMTitle}
- Email: {DMEmail}
- Phone: {DMPhone}

IR Notes (if applicable):
- Relevancy: {specific initiative/signal connection}
- Pitch angle: {suggested framing}
- Gameplan: {what to say, what to lead with}

Packaging note (if applicable): {set expectations / scope}
```

### Field Reference

| Field | Source | Required? | Tier |
|---|---|---|---|
| `@{BDR}` | Same as Message 1 | Yes | All |
| `{ProspectName}`, `{Company}`, `{ProspectEmail}` | Carried from Message 1 | Yes | All |
| `{ReportURL}` | Datagen → Clay (report URL from webhook return) | **Yes — always** | All |
| `{DMName}`, `{DMTitle}`, `{DMEmail}`, `{DMPhone}` | Starbridge API via Datagen (V2) | Optional | Tier 2+ |
| Relevancy / Pitch angle / Gameplan | LLM-generated via Datagen (V3) | Optional | Tier 3 |
| Packaging note | Contextual | Optional | Any |

### Tier-Specific Formatting

**Tier 1 — Report only:**
```
@Jorge Salas — custom intel is ready for Sarah Chen of GovTech Solutions, sarah@govtech.com.

Intel Report: https://starbridge-intel.notion.site/govtech-solutions-abc123
```

**Tier 2 — Report + DM card:**
```
@Joseph Williams — custom intel is ready for Mike Rivera of EduPlatform, mike@eduplatform.com.

Intel Report: https://starbridge-intel.notion.site/eduplatform-abc456

Custom Intel:
- Name: Holly Varner
- Title: Director of Special Education
- Email: hvarner@austinisd.org
- Phone: (512) 555-0147
```

**Tier 3 — Report + DM + analysis + gameplan:**
```
@Glenn Williams — custom intel is ready for Lisa Park of Attendance Point, lisa@attendancepoint.com.

Intel Report: https://starbridge-intel.notion.site/attendance-point-abc789

Custom Intel:
- Name: Dr. James Morrison
- Title: Deputy Superintendent
- Email: jmorrison@district.edu
- Direct Phone: (703) 555-0293

IR Notes:
- Relevancy: Board signal shows K-1 chronic absenteeism initiative; "Attendance Awareness" 
  campaign active; currently using public information officers + social media campaigns. 
  Attendance Point's platform directly addresses this.
- Pitch angle: Lead with the district's own language about "Attendance Awareness" — show 
  how Attendance Point operationalizes what they're already trying to do manually.
- Gameplan: Reference the board discussion, mention the specific initiative, offer to show 
  how similar districts automated attendance tracking. DM has procurement influence.

Packaging note: Prospect expected 12 signals; we surfaced 5 in the report. Frame the demo 
as where we'll unpack the full depth.
```

### Real Examples from Slack (Confirmed Patterns)

**DM contacts actually delivered:**
- Point Quest Group → Holly Varner, Director of Special Education (email + phone)
- OxBlue → Holly Harris, Health Services Director (email + phone)
- SwiftComply → Tom Coppola, Director (Commissioner) of Public Works (email + direct phone)

**Relevancy analysis delivered (Attendance Point example):**
- Specific board signal: K-1 chronic absenteeism
- Named initiative: "Attendance Awareness"
- Current approach described: using public information officers + social media campaigns
- This gives the BDR an extremely specific opening for the conversation

---

## Operator Checklists

### Before Posting Message 1 (Dispatch)

- [ ] Correct BDR tagged
- [ ] Prospect name, company, and email included
- [ ] Reply quote included if it changes urgency/tone
- [ ] Constraints captured (territory, scheduling, demo request)

### Before Posting Message 2 (Intel Ready)

- [ ] Report link works and matches the correct company (click-test it)
- [ ] Custom Intel contact card is formatted cleanly (if included)
- [ ] Territory/scope notes included if relevant
- [ ] If prospect expectation differs from report content (e.g., "expected 12 signals"), add a packaging note framing the demo as where deeper depth happens

---

## Automation Implementation Notes

### Clay Slack Message Configuration

{{UNKNOWN: how Clay's Slack action is configured — native integration, webhook, or API. Need to check the workspace.}}

For the automated pipeline, Clay needs to send two separate Slack messages with a time gap between them:

1. **Message 1** fires immediately from Clay when Smartlead webhook arrives
2. **Message 2** fires from Clay when Datagen webhook returns with report URL

This naturally creates the time gap (Datagen processing takes ~15-30 seconds), which mirrors the current human pattern where Hagel posts "coming shortly" then delivers the intel a few minutes later.

### BDR Assignment Logic

{{UNKNOWN: how BDR assignment works — need to determine:}}
- Is it round-robin?
- Territory-based?
- Account-tier-based (T0 accounts go to senior BDRs)?
- Time-of-day-based (who's online)?
- Manual (Hagel picks)?

Whatever the logic is, it needs to be replicated in Clay so the correct @-mention goes in Message 1. Options:
- Clay formula based on account attributes
- Round-robin counter in Clay
- Default to a specific BDR with manual override
- {{TBD: pick approach after understanding current assignment logic}}

### Reply Snippet Extraction

The `"{ReplySnippet}"` in Message 1 requires extracting the prospect's reply text from the Smartlead webhook. Considerations:
- May need to strip email signatures, disclaimers, and quoted text
- Should truncate long replies to the most relevant sentence(s)
- {{TBD: extract via simple text parsing, or use LLM to pull the key sentence?}}

### Report URL Format

The `{ReportURL}` in Message 2 depends on the report generation tool:

| Tool | URL Format | Notes |
|---|---|---|
| Notion | `https://notion.so/{workspace}/{page-slug}` | Not branded, but functional for V1 |
| Super.so | `https://intel.starbridge.ai/{slug}` | {{TBD: requires custom domain setup}} |
| Webflow | `https://intel.starbridge.ai/{slug}` | {{TBD: requires Webflow CMS + template}} |
