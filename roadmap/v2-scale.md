# V2 Scale — Post-Trust Scope

## Timeline
**Weeks 2-6 of the engagement** (after V1 is live and proven)

V2 is what earns the full engagement extension and demonstrates the value of having Jeremy embedded. V1 proves the pipeline works; V2 proves it's transformative.

## V2 Additions (Ordered by Impact)

### 1. Starbridge API Integration (Buyer Attributes + DM Info)
**Unblocked by**: Yurii meeting + API access
**Impact**: Tier 1 → Tier 2 reports. DM contact card, budget data, logo, location, buyer type in every report.

Deliverables:
- Datagen agent Step 3 implemented (SB API query)
- DM contact card in report and Slack dispatch
- Buyer profile section in report
- Domain → buyer mapping confirmed and automated

### 2. Branded Report Template
**Unblocked by**: Nastia design + platform decision
**Impact**: Reports go from Notion pages to professional branded deliverables

Deliverables:
- Brand assets integrated (logo, colors, fonts)
- Super.so or Webflow template live
- Custom domain (intel.starbridge.ai) configured
- Report URL format is professional and memorable

### 3. Multi-Signal Campaign Integration
**Unblocked by**: Kushagra's allocation framework
**Impact**: Intel reports reference signals the prospect has already seen, adding new value instead of repeating

Deliverables:
- Signal allocation data accessible by Datagen
- "Signals already seen" logic in the LLM prompt
- Report explicitly builds on prior touches ("In addition to the contract expiration we mentioned...")

### 4. Automated Follow-Up Sequence
**Unblocked by**: V1 payload email template proven
**Impact**: Prospects who go dark after intel delivery get systematic follow-up

Deliverables:
- 4-email follow-up sequence in Smartlead (see /templates/follow-up-sequence.md)
- Automated triggers based on "no response within X days"
- Same-thread threading for continuity

### 5. Tier 3 Report Generation
**Unblocked by**: V2 items 1-3 being stable
**Impact**: Premium reports with relevancy analysis, pitch angles, procurement guidance

Deliverables:
- LLM generates Tier 3 content (relevancy analysis, suggested approach, gameplan)
- Template section for Tier 3 additions
- Criteria defined for which accounts get Tier 3 vs. Tier 2

## V2 Metrics Targets

| Metric | V1 Baseline | V2 Target |
|---|---|---|
| Pipeline success rate | > 95% | > 99% |
| Report generation time | < 30 sec | < 15 sec |
| Report content richness | Signals only | Signals + DM + buyer attrs |
| Positive reply → meeting rate | ~50% (current manual) | > 55% (richer intel = better conversion) |
| BDR time per dispatch | ~15 min (review + email + call) | < 10 min (better report = less prep) |
| Manual interventions per week | {{UNKNOWN}} | < 2 |

## What Success Looks Like for the Engagement

By end of V2:
- The positive reply pipeline runs fully automated, end-to-end
- Reports are branded, data-rich, and deterministic
- BDRs have everything they need in one Slack message + one report link
- Hagel's role shifts from "fulfillment operator" to "QA + exception handler"
- Henry can show the board: "we automated our intelligence engine"
- The system handles 3.3M emails/month worth of positive reply volume

## Dependencies Map

```
V2 Item 1 (SB API) ← Yurii meeting
V2 Item 2 (Branding) ← Nastia design + V2 Item 1 (need buyer data for template)
V2 Item 3 (Multi-signal) ← Kushagra framework + V1 stable
V2 Item 4 (Follow-up) ← V1 stable + Smartlead sequence config
V2 Item 5 (Tier 3) ← V2 Items 1-3 stable
```

Nothing in V2 can start until V1 is live and proven. Items 1 and 3 can run in parallel. Item 2 depends on Item 1. Item 5 depends on everything else.
