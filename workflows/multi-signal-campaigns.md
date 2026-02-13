# Multi-Signal Campaigns (Workstream 2 — Kushagra)

> I don't own this workstream, but it's tightly coupled to mine. The signal infrastructure I consume is what Kushagra is building.

## What It Is

Currently, Starbridge sends **one email per prospect with one signal**. Multi-signal campaigns send a sequence where **each follow-up surfaces a different signal** in the same thread.

## Why It Matters

- Smartlead data: **52% of positive replies come from email 2+**, but only if they're in the same thread
- Separate campaigns for the same prospect don't compound — the prospect sees disconnected messages
- Multiple signals in one thread builds a narrative: "we keep finding relevant things for you"

## Why It's Hard

Three technical challenges:

### 1. Signal Allocation
- How do you assign which signals go to which prospects? {{UNKNOWN: Kushagra's algorithm — ask in meeting}}
- What if a prospect has 8 signals but you only send 3 emails? {{UNKNOWN: priority logic}}
- What if a prospect only has 1 signal? {{UNKNOWN: fallback rules}}
- Kushagra is building the assignment framework for this

### 2. Dynamic Prompt Selection
- Each email in the sequence needs different copy based on:
  - The signal type (contract expiration vs. board mention vs. budget event)
  - The email position (email 1 framing is different from email 3)
- This requires Clay logic that selects the right prompt template per signal per position

### 3. Standardized Sequence Structure
- Smartlead sequences need a consistent structure that the dynamic content slots into
- Can't have different sequence lengths per prospect (or can you?)

## Current State

- One signal per email, one email per prospect per campaign
- Signals outnumber prospects (they "have more signals than prospects")
- Goal: send at least one signal per prospect, ideally multiple

## How This Connects to My Work

| Their output | My input |
|---|---|
| Signal allocation framework determines which signals map to which accounts | When a positive reply comes in, I pull ALL signals for that domain — not just the one that was in the email |
| Multi-signal sequences mean a prospect may have seen 2-3 signals before replying | My intel report should reference what they've already seen AND surface new signals |
| Kushagra's Supabase schema stores signal-to-account mappings | My Datagen agents query this same schema |

## Open Questions (For Kushagra)

- What's the allocation algorithm? Random? Priority-scored? Chronological?
- How are fallback rules structured when signals run low for a prospect?
- Is there a "signal exhaustion" state where a prospect has seen everything?
- How does the Clay workbook track which signals have been sent to which prospect?
- What's the Supabase schema for signal-to-prospect-to-email mapping?

## Impact on Intel Reports

If a prospect replies to email 3, my intel report should:
1. Acknowledge the signal from email 3 (what they responded to)
2. Surface the signals from emails 1-2 (what they've already seen)
3. Add NEW signals they haven't seen (the "there's more where that came from" value)
4. Include buyer attributes that go beyond signals (DM, budget, procurement nav)

This makes the report feel like a continuation, not a cold start.
