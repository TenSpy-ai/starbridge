# Buyer Attributes

All data fields available for SLED buyer accounts across the two primary data sources. Used for report generation, prompt engineering, and pipeline logic.

---

## Source 1: Supabase (Kushagra)

**Available**: V1 (pending schema confirmation)

Supabase provides **intent signals**, not buyer profile data. Each signal is a record associated with a domain.

| Attribute | Confirmed? | Notes |
|---|---|---|
| Domain | {{UNVERIFIED}} | Primary lookup key |
| Signal type / category | {{UNKNOWN}} | See /data/signal-taxonomy.md |
| Signal content / summary | {{UNKNOWN}} | Raw text or structured |
| Signal date / timestamp | {{UNKNOWN}} | Detection date? Event date? |
| Signal source reference | {{UNKNOWN}} | Links back to Starbridge source record |
| Relevance score | {{UNKNOWN}} | Pre-computed or computed at query time |

**What Supabase does NOT have**: DM info, budget, logo, location, buyer type — all of this comes from the Starbridge API.

---

## Source 2: Starbridge API (Yurii)

**Available**: V2 (pending API access from Yurii)

The Starbridge API provides **buyer profile data** — attributes about the SLED account itself.

### Buyer-Level Attributes

| Attribute | Type | Example | Report Use | Priority |
|---|---|---|---|---|
| **Account name** | text | "Austin Independent School District" | Report header | P0 |
| **Logo** | image URL | GCS-hosted PNG | Report header, visual credibility | P1 |
| **Buyer type** | enum | School District, Higher Ed, City, County, State Agency | Report context, campaign segmentation | P1 |
| **Location** | text / geo | "Austin, TX" | Report context, map embed potential | P1 |
| **Website** | URL | "www.austinisd.org" | Domain mapping, report link | P1 |
| **Budget / annual spend** | currency | "$1.8B operating budget" | **Most valuable attribute per Justin** | P0 |
| **Active contracts count** | numeric | 47 | Context for contract signals | P2 |
| **Recent meetings count** | numeric | 12 in last 90 days | Signal density indicator | P2 |

### Decision Maker Attributes

{{UNKNOWN: exactly which endpoint returns DM data — see /systems/starbridge-api/README.md}}

| Attribute | Type | Example | Report Use | Priority |
|---|---|---|---|---|
| **DM full name** | text | "Holly Varner" | Tier 2 contact card | P0 |
| **DM title** | text | "Director of Special Education" | Tier 2 contact card | P0 |
| **DM email** | email | "hvarner@austinisd.org" | Tier 2 contact card + BDR outreach | P0 |
| **DM phone** | phone | "(512) 555-0147" | Tier 2 contact card + BDR call | P0 |
| **DM direct phone** | phone | "(512) 555-0148" | Sometimes different from main phone | P1 |
| **Procurement influence** | text / score | "High — oversees technology purchasing" | Tier 3 gameplan | P2 |

### Meeting / Opportunity Attributes

From the `/opportunity/v3` endpoint:

| Attribute | Type | Example | Report Use | Priority |
|---|---|---|---|---|
| **Meeting summary** | text (AI-generated) | "Board discussed absenteeism initiative..." | Enriches signal bullets | P1 |
| **Meeting date** | date | "2026-01-15" | Signal recency | P1 |
| **Meeting type** | text | "Board Meeting Minutes" | Context | P2 |
| **Files / attachments** | file refs | Downloadable PDFs | Source credibility | P3 |

### Contract Attributes

| Attribute | Type | Example | Report Use | Priority |
|---|---|---|---|---|
| **Contract title** | text | "LMS Platform Annual License" | Signal enrichment | P1 |
| **Effective date** | date | "2024-01-01" | Timeline context | P1 |
| **Expiration date** | date | "2026-06-30" | Urgency calculation | P0 |
| **Contract value / price** | currency | "$250,000" | Budget context | P0 |
| **Contract status** | enum | Active, Expired | Filtering | P1 |

### RFP Attributes

| Attribute | Type | Example | Report Use | Priority |
|---|---|---|---|---|
| **RFP title** | text | "Request for Proposal: SIS" | Signal enrichment | P1 |
| **Due date** | date | "2026-02-28" | Urgency | P0 |
| **Status** | enum | Available, Closed | Filtering | P1 |

---

## Attribute Availability by Report Tier

| Attribute | Tier 1 | Tier 2 | Tier 3 |
|---|---|---|---|
| Signal bullets (from Supabase) | ✅ | ✅ | ✅ |
| Signal ranking | ✅ | ✅ | ✅ |
| Account name | ✅ | ✅ | ✅ |
| Logo | — | ✅ | ✅ |
| Buyer type | — | ✅ | ✅ |
| Location | — | ✅ | ✅ |
| Budget / spend | — | ✅ | ✅ |
| DM name, title | — | ✅ | ✅ |
| DM email, phone | — | ✅ | ✅ |
| Meeting summaries | — | — | ✅ |
| Contract details | — | — | ✅ |
| Relevancy analysis | — | — | ✅ |
| Pitch angle / gameplan | — | — | ✅ |
| AI Adoption Score | — | — | {{TBD}} |

---

## Missing Attributes (Gaps to Fill)

| Attribute | Why We Want It | Where It Might Come From |
|---|---|---|
| T0-T3 account tier | Determines report tier and BDR prioritization | {{UNKNOWN: is tier assigned in Supabase? Clay? A separate system?}} |
| Prospect's product category | Needed for signal-to-prospect relevance matching | Campaign metadata from Smartlead? Clay enrichment? |
| Previous signals sent | Which signals the prospect already saw in multi-signal emails | Signal allocation table (Kushagra) |
| Competitor name (from contracts) | "They currently use X — position as replacement" | Starbridge contract data (vendor field) {{UNKNOWN: is vendor tracked?}} |
| Enrollment / population size | Scale indicator for school districts and agencies | Starbridge buyer data? Public data? |
