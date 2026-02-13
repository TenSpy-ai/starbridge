# Project Endgame — Overview

## What It Is

Project Endgame is Starbridge's outbound engine — the full system that turns proprietary SLED signals into pipeline. It spans signal sourcing, campaign construction, email delivery, reply handling, intel fulfillment, and meeting conversion.

The name also refers to the **main Clay workbook** that orchestrates much of this.

## The Engine in One Sentence

Starbridge runs a high-volume outbound machine where signals drive campaigns via Smartlead, and every positive reply triggers a rapid-response fulfillment loop in `#intent-reports`: **dispatch → intel build → BDR payload email → calls → meeting**.

## Scale {{UNVERIFIED: metrics below from Henry's "state of the union" Slack post and onboarding — confirm if current}}

| Metric | Current | Target |
|---|---|---|
| Accounts in TAM | 33K (T0–T3) | — |
| Prospects | 412K+ | — |
| Signals | More signals than prospects | 1 signal per prospect (minimum) |
| Monthly email volume | Ramping | 3.3M/month |
| Prospect → Positive Reply | ~0.7% | 2–3x with improvements below |
| Positive Reply → Meeting | ~50% | Maintain or improve |
| Monthly campaigns | 7 | Scale with automation |

## The Five Workstreams

Henry's "state of the union" laid out five workstreams. I own #1. The others are context for how #1 fits.

### 1. Intelligence Reports / Post-Positive Reply Automations ← I OWN THIS
The biggest lever. Automate the flow from positive reply → intel report → BDR handoff. Replace manual Gamma process with branded, automated, faster delivery.

See: [positive-reply-flow.md](./positive-reply-flow.md)

### 2. Multi-Signal Campaigns (Kushagra)
Currently: one email per prospect with one signal. Building toward: multiple signals per sequence, each follow-up surfaces a new signal in the same thread.

Why it matters: 52% of positive replies come from email 2+, but only if they're in the same thread.

Why it's hard: Requires signal allocation logic, dynamic prompt selection in Clay by signal type and email position, and standardized Smartlead sequence structure.

See: [multi-signal-campaigns.md](./multi-signal-campaigns.md)

### 3. Contact Enrichment / Build Out (Team)
Three sub-problems: pulls (getting contacts), enrichment (getting emails/phones), and data decay (~15%/month turnover).

Strategy: Multiple scraper vendors for near-100% LinkedIn coverage → FullEnrich for initial email coverage → Clay waterfall for gaps → ZeroBounce monthly validation.

See: [contact-enrichment.md](./contact-enrichment.md)

### 4. Multi-Channel Outreach (Team)
Expanding beyond email + phone to include paid ads and automated snail mail for top accounts.

Channel coverage:
- Email: 100% of prospects (Smartlead)
- Phone: top 5-10% (Apollo → Nooks)
- Paid ads: top XX% (TBD spend, Jenn/Mike)
- Snail mail: top 0.1-0.5% (manual first for enterprise, then scaled)

Post-positive-reply: go full tilt on all channels for anyone who replies positively.

### 5. Deliverability (Gurmohit)
Building capacity to 3.3M emails/month in batches. Domains have been stressed by aggressive sending + two subpar providers. Now working with "the best on the market."

## Campaign Structure (Monthly Cadence)

**Short term (current):**
- 4 evergreen intent campaigns (always-on, triggered by persistent signals)
- 1-off event campaigns (conference, board vote, RFP deadline)
- Net new campaign sources: website traffic, closed-lost, new deal (competitor displacement), LinkedIn engagement

**Long term (planned automations):**
- Inbound handling
- Ongoing enrichments
- Multi-signal sequences

## Key Performance Data

- First campaign ran during holidays (likely distorted average downward)
- 2.8x better conversion vs. FY25 averages (0.7% vs. 0.25%)
- "Tons of very positive responses" — more than currently shared in channels
- Job change campaigns were highest performing in FY25 (and that was with Clay's limited 65% visibility)
- Domains were stressed by aggressive sending — now being rehabilitated

## Operating Philosophy

From Henry's state of the union:

> "We want rock solid systems and infrastructure before aggressively scaling. We don't want to be in a situation where we generate thousands of positive replies, respond to prospects late, send subpar intelligence reports, deliver a mediocre experience, and harm our reputation."

This is why I was brought in — build the machine right before pouring gasoline on it.
