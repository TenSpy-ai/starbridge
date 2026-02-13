# Contact Enrichment / Build Out (Workstream 3 — Team)

> I don't own this workstream, but it feeds my pipeline. Better contact data = more prospects reached = more positive replies = more intel reports to generate.

## Three Sub-Problems

### 1. Pulls (Getting Contacts)

**Goal:** Every GTM and RevOps person in the TAM (currently 3-5 prospects/company → target 7-10).

**Challenge:** Clay and other major tools only have ~65% coverage due to LinkedIn's enterprise API restrictions.

**Strategy:**
- Work with multiple "scrappier early-stage startups and agencies" that have built custom web scrapers
- These get close to 100% LinkedIn coverage
- Get all their contact pulls, consolidate, and dedupe
- Result: 2-3x more prospects per company

**Note:** Job change campaigns were the highest performing in FY25, and that was with Clay's limited 65% visibility. Better pull coverage = even better job change signal utilization.

### 2. Enrichment (Getting Emails/Phones)

**Goal:** Valid email + phone for every prospect.

**Strategy (waterfall approach):**

```
FullEnrich (initial coverage, cheaper)
  → Clay waterfall (fills gaps, more expensive)
    → Manual research (edge cases)
```

- FullEnrich: takes name + domain, tests email variations, validates via process of elimination
- Clay: same capability but more data providers in the waterfall; used for gaps FullEnrich misses
- Both are standard enrichment approaches — "fairly easy to do"

### 3. Data Decay (Keeping Data Fresh)

**Problem:** GTM orgs have ~15% monthly turnover. {{UNVERIFIED: 15% figure from Henry's state of the union — described as an estimate}} Contacts leave, change roles, change emails.

**Strategy:**

```
Monthly: ZeroBounce validates every email in TAM (cheap)
  → Bounced emails flagged
    → Web scrapes find where the person moved
      → FullEnrich/Clay get updated contact info
        → Job change = new campaign opportunity
```

**Key insight:** Data decay isn't just a problem — it's a signal source. Every bounced email → person moved → potential job change campaign (their best-performing campaign type).

## How This Connects to My Work

| Their output | My impact |
|---|---|
| More prospects per company | More positive replies to handle (volume) |
| Better email validity | Fewer bounces, better deliverability, more replies reaching actual humans |
| Job change detection | Could trigger proactive intel reports (not just reactive to positive replies) |
| Enriched contact data (email + phone) | My pipeline may eventually include phone-based follow-up automation |

## Scale Context

| Metric | Value |
|---|---|
| Total accounts in TAM | 33K (T0-T3) |
| Total prospects | 412K+ |
| Current prospects/company | 3-5 |
| Target prospects/company | 7-10 |
| Email volume target | 3.3M/month |
| Estimated monthly data decay | ~15% |

## Tools Involved

| Tool | Role | Cost Sensitivity |
|---|---|---|
| Custom scrapers (vendor TBD) | Near-100% LinkedIn coverage | Variable |
| FullEnrich | Initial email enrichment | Lower cost |
| Clay | Waterfall enrichment for gaps | Higher cost |
| ZeroBounce | Monthly email validation | Cheap |
| Web scrapers (for bounced contacts) | Find where people moved | Variable |
