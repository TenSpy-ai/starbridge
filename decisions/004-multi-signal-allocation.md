# ADR 004: Signal Allocation Strategy for Multi-Signal Campaigns

## Status
**Proposed** — Kushagra is building the framework; design not finalized

## Context
Starbridge's multi-signal campaigns send multiple emails per prospect, each surfacing a different intent signal in the same Smartlead thread. Henry's data shows 52% of positive replies come from email 2+, but only if emails are in the same thread (separate campaigns for the same prospect don't compound).

This creates a signal allocation problem: with N signals available for a domain and M email positions in a sequence, which signals go in which positions?

Additionally, when a prospect replies positively, the intel report pipeline needs to know:
- Which signals have the prospect already seen (emails 1 through K)?
- Which signals are new (for the report to add value)?

## Decision
{{TBD: Kushagra is designing the allocation framework. This ADR captures the constraints and options.}}

## Constraints

1. **Same thread required** — multi-signal value only compounds in the same Smartlead thread
2. **Each email needs a distinct signal** — can't repeat the same signal across positions
3. **Signal quality varies** — some signals are stronger hooks than others
4. **Signals have temporal relevance** — contract expiring in 30 days is more urgent than one expiring in 365 days
5. **Prospect context matters** — a signal about LMS is only relevant if the prospect sells LMS-related products
6. **Reply context needs tracking** — when a PR comes in at email K, the pipeline needs to know signals 1 through K

## Options Under Consideration

### Option A: Ranked Allocation (Strongest First)
- Rank all signals for a domain by strength/urgency
- Signal 1 (strongest) → email 1, Signal 2 → email 2, etc.
- **Pro**: Maximizes open/reply rates on email 1
- **Con**: If they reply to email 3, the "best" signals are already spent

### Option B: Escalating Allocation (Weakest First)
- Weakest/broadest signal in email 1, strongest in the last email
- **Pro**: Reserves the best intel for later touches when prospect is warmer
- **Con**: Email 1 open rates may suffer; prospect may not reach the strong signals

### Option C: Category Rotation
- Each email surfaces a different signal TYPE (contract → board meeting → budget → RFP)
- **Pro**: Shows breadth of intelligence; each email feels different
- **Con**: Some signal types may be weak for a given domain; rigid structure

### Option D: Relevance-Scored (LLM-Assisted)
- LLM scores each signal's relevance to the specific prospect (based on their company, product, role)
- Allocate by relevance score, not just signal strength
- **Pro**: Most personalized; highest theoretical conversion
- **Con**: Requires LLM call at allocation time (scale concern at 412K prospects); may not be feasible for V1

## Impact on Intel Report Pipeline

Whichever option is chosen, the intel report pipeline needs:

1. **Signal history per prospect**: Which signals were allocated to which email positions for this prospect?
2. **Reply position tracking**: Which email did the prospect reply to? (From Smartlead webhook)
3. **New signal prioritization**: When generating the report, surface signals NOT already seen by the prospect

This data flow:
```
Smartlead webhook includes: sequence_step = 3
  → Pipeline knows: prospect saw signals in emails 1, 2, 3
  → Pipeline queries: which signals were in emails 1-3 for this prospect?
  → Pipeline prioritizes: signals NOT in emails 1-3 for the report
```

{{UNKNOWN: where is signal allocation data stored? Supabase? Clay? A separate system? This is a key question for Kushagra — see /systems/supabase/queries.md Query 5.}}

## Dependencies
- Kushagra: owns the allocation framework design and implementation
- Smartlead: must include sequence_step in the webhook payload
- Supabase or Clay: must store the allocation mapping (which signal → which prospect → which email position)

## Next Steps
- [ ] Kushagra presents his allocation framework
- [ ] Confirm where allocation data is stored
- [ ] Align on which option (A/B/C/D) or hybrid
- [ ] Build the "signals already seen" query for the intel report pipeline
- [ ] Test with a sample campaign
