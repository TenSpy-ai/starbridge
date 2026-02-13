# Smartlead — System Overview

## Role in the Stack

Smartlead is the **outbound email sending and reply management tool**. It's where campaigns go out, where positive replies land, and where BDRs respond to prospects. It is the entry point to the entire fulfillment loop — the positive reply webhook from Smartlead is what kicks off the intel report pipeline.

Apollo is NOT the primary outbound tool. Apollo only hosts sequences to activate Nooks (the dialer) and handles some BDR follow-up threading. Smartlead owns the email channel end-to-end.

## What Smartlead Does in This System

1. **Sends outbound email campaigns at scale** — the initial touchpoint with prospects
2. **Detects positive replies** — fires a webhook to Clay when a prospect responds positively
3. **Manages email threads** — BDRs reply to prospects in Smartlead (either in-thread or separate thread)
4. **Houses sequence logic** — campaign structure, follow-up cadence, send timing
5. **Tracks reply data** — positive reply rates, which email in the sequence got the reply, etc.

## Key Data Points

| Metric | Value | Source |
|---|---|---|
| Target email volume | 3.3M emails/month (ramping in batches) | Henry's state of the union |
| Current positive reply rate | ~0.7% (prospect → PR) | {{UNVERIFIED: from Henry's state of the union — may have shifted}} |
| FY25 average PR rate | ~0.25% | Henry's state of the union |
| % of PRs from email 2+ | 52% (but only if in same thread) | Smartlead data, confirmed by Henry |
| Monthly campaigns | 7 target | Onboarding notes |
| First campaign timing | Ran during holidays (likely depressed average) | Henry's state of the union |

## Campaign Structure

**Short-term (current):**
- 4 evergreen intent campaigns (always-on, triggered by persistent signals like contract expirations)
- 1-off event campaigns (conference, board vote, RFP deadline)
- {{UNKNOWN: exact campaign names and Smartlead campaign IDs}}

**Net new sources (planned):**
- Website traffic
- Closed-lost
- New deal (competitor displacement)
- LinkedIn engagement

**Multi-signal sequences (being built by Kushagra):**
- Each follow-up email surfaces a different signal in the same thread
- Requires standardized Smartlead sequence structure
- Critical insight: separate campaigns for the same prospect don't compound — must be same thread
- {{UNKNOWN: what the standardized sequence structure looks like — ask Kushagra}}

## Deliverability

Owned by Gurmohit Ghuman.

- Domains have been stressed by aggressive sending + using two subpar email infrastructure providers
- Now working with someone they believe is "the best on the market" {{UNKNOWN: who the new provider is}}
- Building capacity in batches toward 3.3M/month — {{UNKNOWN: exact batch timeline and current capacity}}
- Domain health is a real constraint — can't just turn on volume without warming

## How BDRs Use Smartlead

When a positive reply is dispatched via `#intent-reports`, the BDR:

1. Opens the prospect's thread in Smartlead
2. Replies with: the intel report link, a screenshot of the report, and an offer to share DMs on a call
3. Default: respond in a **separate thread** (enables Apollo sequencing + call tasks)
4. Exception: respond in the **original thread** if the prospect is likely to forward internally (Henry's situational guidance)

Future idea from onboarding: mini follow-up sequence in Smartlead after intel delivery (automated, not manual BDR action).

## Current Pain Points

| Problem | Detail |
|---|---|
| Manual positive reply detection | Hagel monitors the Smartlead inbox manually {{UNVERIFIED: confirm with Hagel if he has any alerts/filters}} |
| No webhook automation (current) | The webhook to Clay is part of the future-state pipeline being built now |
| Thread management complexity | Separate vs. original thread is a judgment call per reply, not automated |
| Domain health risk | Aggressive past sending damaged domains; recovering now |
| Sequence rigidity | Multi-signal sequences need dynamic content per position — {{UNKNOWN: does Smartlead support this natively or does it need Clay-side logic?}} |

## Integration Points

| System | Direction | Method | Status |
|---|---|---|---|
| Clay (Project Endgame) | Outbound → Clay | Webhook (positive reply trigger) | {{UNKNOWN: webhook configuration details — is this already set up or being built?}} |
| Apollo | Smartlead → Apollo | {{UNKNOWN: how are leads pushed to Apollo for Nooks activation?}} | Active |
| Slack | Indirect | Via Clay (not direct Smartlead → Slack) | Planned (V1 pipeline) |

## Things to Investigate

- [ ] Is the positive reply webhook already configured, or does it need to be set up?
- [ ] What is the exact webhook payload schema? See [webhook-spec.md](./webhook-spec.md)
- [ ] How are campaigns structured in Smartlead? (names, IDs, sequence steps)
- [ ] What does "positive reply" detection actually trigger on? (keyword matching? manual tagging? AI classification?)
- [ ] How does the Smartlead → Apollo handoff work for Nooks activation?
- [ ] What's the current domain/sender infrastructure? (how many domains, warmup status)
- [ ] Can Smartlead sequences accept dynamic content per email position (for multi-signal)?
- [ ] What's the current batch timeline for scaling to 3.3M/month?
