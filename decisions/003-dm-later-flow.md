# ADR 003: Decouple DM Lookup from Intel Report Delivery (DM-Later Flow)

## Status
**Accepted** — emerged from pipeline design discussions; confirmed as the Tier 1 → Tier 2 upgrade path

## Context
The intel report pipeline has two distinct data sources:
1. **Supabase** (Kushagra) — intent signals. Accessible, schema pending.
2. **Starbridge API** (Yurii) — buyer attributes, DM info. Dev-gated, access pending.

In the current manual process, Hagel pulls both signal data and DM info before assembling the intel package. This bundles two tasks with different dependencies, timelines, and failure modes.

The question: should V1 block on getting DM info, or should we ship signal-only reports first and add DM info later?

## Decision
Decouple DM lookup from intel report delivery. Ship Tier 1 reports (signals only) immediately in V1. Add DM info (Tier 2) when Starbridge API access is unblocked.

The "DM-later" flow:
1. V1 delivers the intel report without DM info (Tier 1)
2. DM info is added to the Slack dispatch separately when available — either via the existing Starbridge Slack bot (manual) or via Datagen + SB API (V2 automated)
3. The BDR uses "happy to share the decision maker's contact info on a call" as a meeting hook — the DM card becomes the incentive to book, not a giveaway

## Reasoning

**Timing risk**: Starbridge API access depends on Yurii, who we haven't met yet. If V1 blocks on API access, the entire trial deliverable is at risk. The 2/17 deadline doesn't allow for this dependency.

**The DM card is actually more valuable as a meeting hook**: Justin confirmed that BDRs offer to "share DMs on a call" — the DM info isn't given away for free. Withholding it from the report and using it as a conversation incentive is the intended strategy, not a limitation.

**Two independent failure domains**: Supabase could be up while the SB API is down (or vice versa). Bundling them means both must work for any report to ship. Decoupling means partial delivery is always possible.

## Consequences
**Positive:**
- V1 ships on time with no SB API dependency
- DM info becomes a meeting incentive (aligned with the sales strategy)
- Each pipeline component can fail independently without blocking the other
- Iterative value delivery: Tier 1 immediately, Tier 2 when ready, Tier 3 later

**Negative / Risks:**
- Tier 1 reports are less impressive than a full intel package
- BDRs may feel the report is "incomplete" without DM info (requires framing)
- Two separate lookup processes (Supabase + SB API) need to be maintained until V2 unifies them

**Mitigations:**
- Frame Tier 1 reports as deliberately focused on signals (the prospect cares about their own procurement context, not our contact data)
- BDR training: "the DM card is your meeting hook, not a report feature"
- Hagel can manually add DM info via Starbridge Slack app as a bridge until V2

## Timeline
| Phase | DM Info Source | Delivery Method |
|---|---|---|
| V1 (now) | Not included in report | BDR offers on call; Hagel can add via Slack bot manually |
| V2 (post-Yurii meeting) | Starbridge API via Datagen | Automated DM card in report + Slack dispatch |
| V3 (scale) | Fully automated | DM card + procurement influence scoring |
