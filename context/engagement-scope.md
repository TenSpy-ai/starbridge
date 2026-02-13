# Engagement Scope — Jeremy Ross at Starbridge

> **Jeremy Ross is the user.** All first-person references in this file ("I", "my", "me") refer to Jeremy.

## Terms

| Detail | Value |
|---|---|
| **Type** | Paid trial (path to full-time) |
| **Duration** | 3–6 weeks |
| **Compensation** | $20K over 6 weeks, paid weekly (~$3,333/wk). {{UNKNOWN: payment method — need to find out the platform or determine if invoice needed}} |
| **Start** | Late January 2026 |
| **Full-time potential** | Henry wants to hire full-time. Comp ceiling: {{UNVERIFIED: "above $205K base + $30K bonus + equity" — Henry said his own comp "is not the ceiling" on 1/12 call, but no explicit offer number given}}. |

## What I Own

**Part 1: Intelligence Reports / Post-Positive Reply Automations**

This is the single biggest lever Starbridge can pull right now. Henry's words: "couldn't be more excited about this."

### Specific deliverables:
1. **Automate the positive reply → intel report pipeline** (replace Hagel's manual Gamma process)
2. **Improve report quality** (branded, deterministic, richer data than current Gamma output)
3. **Reduce response time** (from hours/timezone-dependent to minutes)
4. **Make it scalable** (current process breaks at volume; new process must handle 3.3M emails/mo worth of replies)

### What I am NOT owning (at least initially):
- Multi-signal campaign logic (Kushagra)
- Contact enrichment / pulls strategy (team effort)
- Multi-channel outreach (Henry + team)
- Deliverability infrastructure (Gurmohit)
- Paid ads (Jenn / Mike)

## How I Got Here

- **July 2025**: Intro from Jordan. Met Henry Bell (Head of Growth). Originally scoped as Clay consulting at $8K–$15K/mo for 10-15 hrs/wk. Henry had originally been looking to hire a GTM Engineer at $150K–$180K (medium to long term).
- **January 12, 2026**: Call with Henry. He pivoted to wanting full-time hire. Open to paid trial first. Mentioned comp range and desire for me to help steer the product, not just execute. Also mentioned he might want a "$2K/mo GTME" for soft Clay work — if the consulting relationship worked well, he might forgo hiring a junior GTME separately.
- **January 20, 2026**: Trial terms agreed. $20K over 6 weeks. Scope: Part 1 of Project Endgame.
- **January 29, 2026**: Henry announced me in #gtm-eng and assigned stakeholder meetings.
- **February 4, 2026**: Onboarding huddles. Got lay of the land on systems, workflow, and team.

## What Starbridge Wants From the Trial

From Henry's emails and calls:

1. **A clear gameplan with outcomes** — "paid trial is ideal, but in an ideal world there's a clear gameplan for what you'd be focused on"
2. **Something "impactful + interesting"** — they don't want busywork; they want something that matters to growth AND is energizing enough that I'd go full-time
3. **An asset + system they can reuse forever** — "not just sequences"
4. **Speed** — too many positive replies, brittle current system, Philippines timezone lag

## What I Need From Them

| Need | Who | Status |
|---|---|---|
| Supabase access + schema walkthrough | Kushagra | {{UNKNOWN: pending meeting}} |
| Starbridge API access (internal, dev-gated) | Yurii | {{UNKNOWN: pending meeting}} |
| Clay workspace access (Project Endgame) | Kushagra / Henry | Have link, {{UNKNOWN: need to explore tables, columns, automations}} |
| Smartlead webhook payload spec | Team | {{UNKNOWN: need payload schema}} |
| Slack access (all relevant channels) | Henry | Done |
| Gong access | Henry | {{UNKNOWN: pending}} |
| GitHub access | Henry | {{UNKNOWN: pending}} |
| Starbridge platform access | Henry | {{UNKNOWN: need to request}} |
| Alignment on report format | Nastia / Henry | {{TBD: Notion vs. Webflow vs. Super.so — needs Nastia meeting}} |
| Claude Max account ($200 expense) | Self | Approved, need to buy |
| Datagen account ($50 expense) | Self | Approved, need to set up |

## Trial Rollout Timeline

| Date | Milestone |
|---|---|
| 2/4 (Wed) | Onboarding complete, context gathered |
| 2/5–2/14 | Build, test, iterate on V1 pipeline |
| 2/17 (Tue) | **Deadline**: V1 must be live + new campaign launches (10x) |
| Week 2–3 | Iterate on report quality, add buyer attributes, polish branding |
| Week 4–6 | Scale, optimize, document, hand off or convert to full-time |

## Expenses & Setup to Track

| Item | Cost | Status |
|---|---|---|
| Claude Max account | $200 | Approved, buy + expense |
| Datagen | $50 (month 1), $500 (month 2+) | Approved, set up + expense |
| Claude Code repo with Datagen | — | Set up (this repo is part of that) |

## Key Relationships to Manage

- **Henry**: Strategy alignment, trial outcomes, path to full-time. Update him Thursday on Datagen timeline.
- **Kushagra**: Technical peer. Join his Claude Code, understand his systems, collaborate on signal logic.
- **Hagel**: Current operator whose process I'm automating. Need his workflow details but also need to make his life easier, not threaten his role.
- **Nastia**: Design dependency. Get alignment on report format before building generation pipeline.
- **Yurii**: API access dependency. If he can't unblock SB API quickly, buyer attribute enrichment is bottlenecked.
