# Playbook: Campaign Launch

## Trigger
A new outbound campaign is being planned for Smartlead. This playbook covers the upstream setup — everything that needs to happen before emails start sending.

## Who Executes
- **Kushagra**: Signal allocation, sequence structure, Clay enrichment tables
- **Henry**: Campaign strategy, messaging, approvals
- **Hagel**: Operational setup in Smartlead, list loading
- **Jeremy**: Pipeline configuration (Clay/Datagen) for any new campaign type

---

## Campaign Types

### Evergreen Intent Campaigns (Always-On)
- Triggered by persistent signals (contract expirations, budget cycles)
- 4 currently running {{UNKNOWN: campaign names and IDs}}
- Continuous — new prospects added as signals are detected
- Signal changes but messaging framework stays constant

### Event Campaigns (One-Off)
- Triggered by time-bound events (conference, board vote, RFP deadline)
- Finite duration — campaign ends when event passes
- Messaging is event-specific

### Net New Source Campaigns (Planned)
- Website traffic → outbound
- Closed-lost reactivation
- Competitor displacement (new deal signal)
- LinkedIn engagement → outbound
- {{UNKNOWN: which of these are closest to launch?}}

---

## Pre-Launch Checklist

### 1. Account & Prospect Selection
- [ ] Define target accounts (tier, buyer type, geography, signal criteria)
- [ ] Pull prospect lists from Clay / enrichment stack
- [ ] Verify email validity (ZeroBounce or similar — 15% monthly decay means stale lists hurt deliverability)
- [ ] Deduplicate against active campaigns (don't email someone already in a live sequence)
- [ ] {{UNKNOWN: what's the deduplication process? Manual in Smartlead? Automated in Clay?}}

### 2. Signal Allocation (Kushagra)
- [ ] For multi-signal campaigns: assign which signals go to which email position
- [ ] Core constraint: follow-up emails must be in the SAME THREAD to compound (52% of PRs come from email 2+, but only if same thread)
- [ ] Ensure each prospect gets signals they haven't seen before
- [ ] Document allocation logic so intel reports can reference what was already sent
- [ ] {{UNKNOWN: where is signal allocation tracked? Supabase? Clay? Spreadsheet?}}

### 3. Sequence Structure
- [ ] Define number of emails in the sequence (typically 3–5?)
- [ ] Each email surfaces a different signal (multi-signal approach)
- [ ] Determine cadence (days between emails)
- [ ] Write email copy per position — each referencing its assigned signal
- [ ] {{UNKNOWN: who writes the copy? Henry? AI-generated? Templates?}}
- [ ] {{UNKNOWN: does Smartlead support dynamic content per prospect for the signal variable, or is it fixed per campaign?}}

### 4. Enrichment & Data Prep
- [ ] Ensure all prospects have: first name, last name, email, company name, domain
- [ ] Run enrichment through the Clay waterfall if data is thin (FullEnrich → Clay → ZeroBounce)
- [ ] Populate any custom fields needed for personalization
- [ ] Verify domain health for sending (check with Gurmohit)

### 5. Pipeline Configuration
- [ ] Confirm Clay Project Endgame is configured to handle this campaign's positive replies
- [ ] If new campaign type: update Clay webhook routing or Datagen agent if signal context differs
- [ ] Ensure Smartlead webhook is active and pointing to Clay
- [ ] Test with 1–2 sample sends before full launch

### 6. Deliverability Check
- [ ] Confirm sending domains are warm enough for planned volume
- [ ] Align with Gurmohit on batch sizing
- [ ] Check bounce rate from previous campaigns on similar domains
- [ ] {{UNKNOWN: what's the current domain infrastructure? How many domains? Warmup status?}}

### 7. Approvals
- [ ] Henry reviews messaging and target list
- [ ] Campaign name and ID logged
- [ ] Launch date confirmed
- [ ] BDR team briefed on what to expect (new campaign = new positive reply patterns)

---

## Multi-Signal Campaign Specifics

The multi-signal approach is Kushagra's workstream and a major differentiator. Key mechanics:

### The Compounding Effect
- Email 1 surfaces Signal A
- Email 2 surfaces Signal B (same thread)
- Email 3 surfaces Signal C (same thread)
- The prospect sees a building case of intelligence, not a single data point
- 52% of positive replies come from email 2+ — this is why the multi-signal approach works

### The Signal Allocation Problem
With 412K+ prospects and even more signals, assigning the right signal to the right prospect at the right sequence position is a combinatorial challenge:

| Constraint | Why It Matters |
|---|---|
| Relevance | Signal must be relevant to the prospect's account/role |
| Novelty | Each email must surface a NEW signal (no repeats) |
| Strength | Strongest signals should lead (email 1), supporting signals follow |
| Thread continuity | All emails must be in the same Smartlead thread |
| No cross-campaign collision | If prospect is in Campaign A, Campaign B shouldn't surface the same signals |

{{UNKNOWN: how Kushagra is solving this — his framework is actively being built. Critical to understand before launching new multi-signal campaigns.}}

### Impact on Intel Reports
When a prospect replies to a multi-signal campaign, the intel report needs to know:
- Which signals were already sent (emails 1, 2, 3...)
- Which email they replied to (tells us which signal resonated)
- What signals are left (for the report to surface new intel, not repeat what was emailed)

This is why signal allocation tracking (Query 5 in /systems/supabase/queries.md) is important.

---

## Volume Ramp Plan

Target: 3.3M emails/month, ramping in batches.

| Phase | Volume | Campaigns | Notes |
|---|---|---|---|
| Current | {{UNKNOWN}} | 4 evergreen + event-based | Holiday timing depressed early results |
| Near-term | {{UNKNOWN}} | + net new source campaigns | Depends on domain warmup |
| Target | 3.3M/month | 7+ campaigns | Full capacity across all domains |

{{UNKNOWN: batch timeline and current capacity — ask Gurmohit/Henry}}

---

## Post-Launch Monitoring

### First 48 Hours
- [ ] Monitor bounce rates — if above 5%, pause and investigate
- [ ] Check reply rates vs. baseline (0.7% PR rate benchmark)
- [ ] Confirm positive replies are flowing through the pipeline correctly
- [ ] BDR feedback: are dispatches clear? Is intel quality sufficient?

### Ongoing
- [ ] Weekly: reply rate by email position (is the multi-signal compounding working?)
- [ ] Weekly: positive reply → meeting conversion rate
- [ ] Monthly: deliverability health check with Gurmohit
- [ ] Monthly: signal allocation review with Kushagra (are we running out of fresh signals for any accounts?)

---

## The Monday 10x Campaign

{{UNKNOWN: Henry mentioned a "10x campaign" launching Mondays. Details:}}
- Is this a specific campaign type or a volume scaling initiative?
- How does it relate to the multi-signal framework?
- Does it have special pipeline requirements?
- Is this the same as "Monday campaign" mentioned in onboarding notes?
