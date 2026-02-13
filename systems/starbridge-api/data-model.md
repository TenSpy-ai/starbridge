# Starbridge API — Data Model

This documents how data is structured in the Starbridge platform, based on the platform UI observations and API endpoint patterns from doc 3. This is what the API serves — understanding the data model helps us query the right endpoints for the right data.

## Core Entities

### Buyers (Accounts)

Buyers are government and institutional entities. This is the "account" concept in Starbridge.

**Count**: 296K+ in the database

**Known fields** (from platform UI):

| Field | Type | Example | Notes |
|---|---|---|---|
| Name | text | "Austin Independent School District" | Human-readable buyer name |
| Logo | image URL | — | Served from Google Cloud Storage |
| Website | URL | "www.austinisd.org" | {{UNKNOWN: does this include the domain we can match against?}} |
| Location | text / geo | "Austin, TX" | City, state at minimum |
| Type | enum | "School District", "Higher Education", "City", "County", "State Agency" | Defined by `/buyer/type` endpoint |

**Buyer types available** (from platform):
- Higher Education
- School District
- City
- County
- State Agency
- {{UNKNOWN: full list — get from `/buyer/type` endpoint}}

**Key question**: Can we look up a buyer by domain? The pipeline receives a domain from Smartlead (e.g., "acmegov.com") and needs to find the corresponding Starbridge buyer. If the `website` field is searchable via `/buyer/search/v2`, we can map domain → buyer. If not, we need another mapping strategy. {{UNKNOWN: confirm with Yurii}}

### Meetings (Board Meetings & Strategic Plans)

Board meetings, agendas, minutes, and strategic plans. This is where Starbridge's "listening" moat lives.

**Count**: 107M+ records

**Known fields** (from platform UI):

| Field | Type | Example | Notes |
|---|---|---|---|
| Buyer | reference | "Austin ISD" | Which buyer this meeting belongs to |
| Buyer Type | enum | "School District" | Inherited from buyer |
| Buyer Location | text | "Austin, TX" | Inherited from buyer |
| Type | text | "Board Meeting Minutes" | {{UNKNOWN: what types exist beyond minutes?}} |
| Posted Date | date | "2026-01-15" | When the record was posted/detected |
| Summary | text | AI-generated summary of the meeting | **This is gold for intel reports** |
| Files | file references | Downloadable PDFs, docs | Original source documents |

**Pipeline relevance**: HIGH. Meeting summaries contain:
- What was discussed (product categories, vendor mentions, budget discussions)
- Who was involved (potential DM names mentioned in minutes)
- What decisions were made or are pending
- Specific initiatives and priorities

**Search**: Natural language search with OR operators, filterable by buyer, date range, document type, relevance sort.

### Purchases & Contracts

Purchase orders and contract records. Key for contract expiration signals and spend intelligence.

**Count**: 107M+ records

**Known fields** (from platform UI):

| Field | Type | Example | Notes |
|---|---|---|---|
| Title | text | "LMS Platform Annual License" | Contract/PO description |
| Type | enum | "Purchase Order" | {{UNKNOWN: what other types? "Contract"?}} |
| Effective Date | date | "2024-01-01" | When the contract started |
| Expiration Date | date | "2026-06-30" | **Key signal: contracts expiring soon** |
| Status | text | Active, Expired, etc. | {{UNKNOWN: full status values}} |
| Price | numeric | "$250,000" | **Budget data — most valuable attribute per Justin** |
| Buyer | reference | "Austin ISD" | Which buyer |

**Pipeline relevance**: HIGH for V2 reports. Contract data provides:
- What they're spending money on (validates signals from Supabase)
- How much they're spending (budget context for the report)
- When contracts expire (timing urgency for outreach)
- Vendor displacement opportunities (who they currently use)

### RFPs

Active procurement opportunities.

**Count**: 44.3K+ records

**Known fields** (from platform UI):

| Field | Type | Example | Notes |
|---|---|---|---|
| Title | text | "Request for Proposal: Student Information System" | RFP description |
| Buyer | reference | "Austin ISD" | Which buyer |
| Posted Date | date | "2026-01-20" | When the RFP was published |
| Due Date | date | "2026-02-28" | Submission deadline |
| Status | enum | "Available" | {{UNKNOWN: other statuses?}} |

**Pipeline relevance**: MEDIUM. Active RFPs are strong signals but may already be in Supabase. Useful for enriching Tier 3 reports with "there's an active RFP due on X date."

### Conferences

Tracked conferences relevant to SLED procurement.

**Count**: 1,314+ conferences

**Known fields** (from platform UI):

| Field | Type | Example | Notes |
|---|---|---|---|
| Organizer | text + logo | "CoSN" | Conference organizer name |
| Start Date / End Date | date | "2026-03-15" / "2026-03-17" | Conference dates |
| Description | text | — | Conference description |
| City / State | text | "San Antonio, TX" | Location |
| Buyer Types | enum[] | ["School District", "Higher Education"] | Which buyer types attend |
| Personas | text[] | {{UNKNOWN: what persona categories exist?}} | Role-based targeting |
| Attendee Count | numeric | — | Size of conference |
| Price | numeric | — | Registration cost |

**Pipeline relevance**: LOW for intel reports. Could be useful for future event-based campaigns.

### Contacts

{{UNKNOWN: the platform lists "Contacts" as a Bridge type for "building contact lists for campaigns." However, the API endpoint structure doesn't show a dedicated contacts endpoint. Contact/DM info may be:}}
- Embedded in meeting records (names mentioned in minutes)
- Derived from buyer records
- Available only through Ask Starbridge's AI chat
- Accessible through a Bridge configured for contacts
- Available through an undocumented internal endpoint

**This is the biggest open question for V2**: Where exactly does DM info come from in the API?

From the Slack observations, DM info includes:
- Full name (e.g., "Holly Varner")
- Title (e.g., "Director of Special Education")
- Email (e.g., "hvarner@district.edu")
- Phone / Direct Phone (e.g., "(555) 123-4567")

{{UNKNOWN: which API endpoint returns this data — ask Yurii}}

## Entity Relationships

```
Buyer (296K+)
  │
  ├── has many → Meetings (107M+)
  │                └── contains → Summaries, Files, (potentially DM mentions)
  │
  ├── has many → Purchases/Contracts (107M+)
  │                └── contains → Price, Dates, Status
  │
  ├── has many → RFPs (44K+)
  │                └── contains → Due dates, Status
  │
  └── attends → Conferences (1.3K+)

Bridges (user-configured)
  │
  └── surfaces → Entries (filtered views across meetings, purchases, RFPs, etc.)
```

## How the Platform Queries Data

From the platform UI behavior, the search pattern is:
1. User enters natural language query with OR operators
2. Platform searches across the relevant entity type (meetings, purchases, RFPs)
3. Results are filtered by: buyer type, buyer location, date range
4. Results are sorted by relevance
5. Individual records link to detail pages with full data + downloadable files

The `/opportunity/v3` endpoint (PUT) appears to be the unified search across meetings, RFPs, and purchases. {{UNVERIFIED: this is inferred from the endpoint name and the platform's unified search behavior — confirm with Yurii}}

## Credits System

Starbridge uses a credit-based usage model:
- Organization credit balance (annual credits)
- Per-user credit tracking
- {{UNKNOWN: credit cost per API call type — are searches more expensive than lookups?}}
- {{UNKNOWN: what's Starbridge's own internal credit allocation? Will pipeline queries burn credits?}}

## Data Freshness

| Entity | Source | Freshness |
|---|---|---|
| Meetings | Board meeting scraping + FOIA | {{UNKNOWN: how often updated?}} |
| Purchases/Contracts | Government procurement databases + FOIA | {{UNKNOWN}} |
| RFPs | Procurement portals | {{UNKNOWN: likely near-real-time for new postings}} |
| Conferences | Conference aggregation | {{UNKNOWN: likely periodic batch updates}} |
| Buyers | Aggregated from all sources | {{UNKNOWN}} |

## Mapping to Intel Report Sections

| Report Section | Data Source | Entity/Endpoint |
|---|---|---|
| Top intent signals | Supabase (primary) | N/A — from Kushagra's DB |
| SLED Signal Bullets | LLM-generated from Supabase signals | N/A |
| Decision maker(s) | Starbridge API | {{UNKNOWN: which endpoint}} |
| Budget / spend data | Starbridge API | `/opportunity/v3` (purchases) or buyer record |
| Account logo | Starbridge API | Buyer record → logo field |
| Location / map | Starbridge API | Buyer record → location field |
| Buyer type | Starbridge API | Buyer record → type field, or `/buyer/type` |
| Meeting context | Starbridge API | `/opportunity/v3` (meetings) → summaries |
| Contract timeline | Starbridge API | `/opportunity/v3` (purchases) → dates |
