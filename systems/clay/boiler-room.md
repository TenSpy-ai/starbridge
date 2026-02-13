# Boiler Room — Clay Workbook

## Overview

Boiler Room is the secondary Clay workbook focused on **phone outreach**. It converts Starbridge signals into concise intel snippets that BDRs can reference while cold calling via Nooks.

## Purpose

While Project Endgame handles the full positive-reply automation pipeline (email → intel report → Slack dispatch), Boiler Room serves a different use case: **giving BDRs something smart to say on the phone**.

The output isn't a full intel report — it's a quick-hit snippet: one or two sentences a BDR can glance at before dialing, so the call feels informed rather than generic.

## How It Connects to the Broader Engine

```
Project Endgame (email outbound + positive reply automation)
  │
  │  Shared signal data
  │
Boiler Room (phone outbound intel snippets)
  │
  └──→ BDRs on Nooks (top 5-10% of prospects by priority)
```

The two workbooks {{UNVERIFIED: assumed to share data — confirm with Kushagra}} share:
- Account/prospect data (same TAM)
- Signal data (same Supabase-sourced signals)
- Enrichment (same contact data)

They differ in:
- **Output format**: Boiler Room → short snippets; Project Endgame → full intel reports
- **Trigger**: Boiler Room → proactive (BDR is about to call); Project Endgame → reactive (prospect replied)
- **Audience**: Boiler Room → BDR on the phone; Project Endgame → prospect (via email/report)

## What BDRs Need on a Call

A BDR dialing into a SLED account through Nooks needs:

| Info | Why | Example |
|---|---|---|
| **Signal hook** | Something specific to open with | "I noticed your district's board discussed LMS renewals last month" |
| **Prospect context** | Who they are and why they'd care | "You're the IT Director overseeing procurement for the district" |
| **Ask** | What the BDR is proposing | "We put together a quick intel brief on the vendors in play — worth 15 minutes?" |

Boiler Room's job is to pre-package this so the BDR doesn't have to research each account manually.

## Known Details

{{UNKNOWN: most details below need workspace exploration — limited information from onboarding}}

- **Name**: Boiler Room
- **Location**: Same Clay workspace (484780) as Project Endgame
- **Mentioned by**: Henry in onboarding ("Boiler Room is converting the signals into intel snippets for our BDRs hammering the phones")
- **Builder**: {{UNVERIFIED: likely Kushagra — confirm}}

## Things to Explore

- [ ] Table structure: what columns exist? How are signals formatted into snippets?
- [ ] Data source: does it pull from Supabase directly or from Project Endgame?
- [ ] LLM usage: are there AI columns generating the phone snippets?
- [ ] How BDRs access it: do they look at Clay directly, or does it push to another tool (Nooks, Slack)?
- [ ] Volume: how many accounts/prospects are in Boiler Room vs. Project Endgame?
- [ ] Update cadence: is it static or does it refresh as new signals come in?
- [ ] Relationship to Apollo: Apollo hosts sequences to activate Nooks — does Boiler Room feed into Apollo?

## Lower Priority for My Scope

Boiler Room is not part of my immediate deliverable (Part 1: Post-Positive Reply Automations). However, understanding it matters because:

1. **Shared infrastructure**: If Boiler Room and Project Endgame share signal data / enrichment, changes to one may affect the other
2. **Future convergence**: In V3, a positive reply from a phone-sourced lead should trigger the same intel report pipeline
3. **BDR experience**: BDRs use both — the phone snippet (Boiler Room) and the intel report (#intent-reports). They should feel cohesive, not contradictory

I'll document this more thoroughly after exploring the workspace and talking to Kushagra.
