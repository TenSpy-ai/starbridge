# Starbridge API — System Overview

## Role in the Stack

The Starbridge API provides **buyer attributes and auxiliary data** that complement Supabase's intent signals. While Supabase answers "what signals exist for this company?", the Starbridge API answers "who's the decision maker, what's their budget, and what does this buyer look like?"

In the intel report pipeline, the Starbridge API is the **V2 enrichment layer** — V1 ships with Supabase signals only; V2 adds buyer attributes from this API.

## Access Status

**Internal-only and dev-gated.** From Henry's 1/12 call:
> "Starbridge API is only available internally at the moment — but not easy — only devs can really use it."

{{UNKNOWN: current access status for Jeremy — need Yurii meeting to determine:}}
- Can Datagen get API credentials?
- Is there an API key, or does it require internal service auth?
- Are there rate limits or usage restrictions?
- Which endpoints are stable vs. experimental?

**This is a critical dependency for V2.** If Yurii can't unblock access, DM info and buyer attributes are bottlenecked, and we stay at Tier 1 intel reports longer.

## API Base URL

```
https://dashboard.starbridge.ai/api
```

## What the API Provides (That Supabase Doesn't)

| Data Type | Value for Intel Reports | Priority |
|---|---|---|
| **Decision maker info** | Name, title, email, phone for the SLED-side buyer | High — core of Tier 2 reports |
| **Budget / spend data** | Most valuable buyer attribute per Justin | High |
| **Account logo** | Branding for the intel report | Medium |
| **Buyer location** | Geographic context, map embed potential | Medium |
| **Buyer type** | Higher Ed, School District, City, County, State Agency, etc. | Medium |
| **Meeting summaries** | AI-generated summaries of board meetings | Medium — enriches signal bullets |
| **Contract details** | Effective/expiration dates, price, status | Medium — validates signal data |
| **Purchase orders** | Purchase history for the buyer | Lower |
| **RFP details** | Active RFPs from the buyer | Lower |
| **Conference attendance** | Conferences the buyer attends | Lower |

## Two Data Sources, Two Purposes

```
SUPABASE (Kushagra)                  STARBRIDGE API (Yurii)
─────────────────────                ──────────────────────
Intent signals                       Buyer attributes
"What procurement signals            "Who's the decision maker?
 exist for this domain?"              What's their budget?
                                      What do they look like?"

Used in: V1 + V2                     Used in: V2+
Queried by: Datagen → Supabase       Queried by: Datagen → SB API
Status: Accessible (pending schema)  Status: Dev-gated (pending Yurii)
```

## Platform vs. API

The Starbridge platform at `dashboard.starbridge.ai` is the user-facing product. The API under `/api` powers that platform. Key distinction:

- **Platform UI**: What Starbridge's customers use. Has Bridges, signals, Ask Starbridge, RFP Writer, etc.
- **API**: The data layer behind the platform. What we want Datagen to query programmatically.
- **Ask Starbridge**: An AI chat interface in the platform — could potentially be used as an alternative to raw API calls if the API is too hard to access. {{TBD: explore Ask Starbridge as a workaround if API access is blocked}}

## Authentication

{{UNKNOWN: auth method — options observed from the platform:}}

The platform has an API Keys page at `/settings/api-keys` where users can "Create Secret Keys." This suggests:
- API key-based auth (bearer token or header)
- Possibly per-organization scoping (the API structure uses `organization/{orgId}` paths)

Things to determine with Yurii:
- [ ] Can we create an API key via the settings page?
- [ ] Does the API key grant access to all endpoints or just a subset?
- [ ] What's the orgId for Starbridge's own organization?
- [ ] Are there different permission levels (read-only vs. read-write)?
- [ ] Is there a separate internal auth system beyond the public API keys?

## Third-Party Services in the Stack

The platform uses several services that may affect API behavior:

| Service | Role | Relevance |
|---|---|---|
| **Firebase/Firestore** (`firestore.googleapis.com`) | Real-time data sync | Some data may live in Firestore, not the REST API |
| **Nango** | Integration orchestration | Handles OAuth for third-party integrations (Salesforce, HubSpot, etc.) |
| **LaunchDarkly** | Feature flags | Some API endpoints may be behind feature flags |
| **Google Cloud Storage** | Static assets | Logos and files served from GCS |

## Key Integration: Nango

The API has a Nango login endpoint (`/organization/{orgId}/nango/login`). Nango is an integration orchestration tool — Starbridge uses it to manage OAuth connections to CRMs and other tools. This means:
- Starbridge's integration layer is Nango-based
- If we ever need to push data TO Salesforce/HubSpot via Starbridge, it goes through Nango
- {{UNKNOWN: does this affect how Datagen authenticates?}}

## Priority Endpoints for the Pipeline

Ranked by value to the intel report pipeline:

| Priority | Endpoint Category | Why |
|---|---|---|
| **P0** | Buyer search / lookup | Get buyer info (name, type, location) for a domain |
| **P0** | Opportunity search (meetings) | Get meeting summaries that contain DM info and signal context |
| **P1** | Opportunity search (purchases/contracts) | Validate and enrich contract signals from Supabase |
| **P1** | Contact/DM lookup | {{UNKNOWN: is there a dedicated contact endpoint or is DM info extracted from meeting/buyer records?}} |
| **P2** | Trigger/Bridge entries | Access pre-configured Bridge results for signal enrichment |
| **P3** | Everything else | RFPs, conferences, FOIA campaigns — useful but not critical path |

## Files in This Directory

- **[endpoints.md](./endpoints.md)** — Full API endpoint reference captured from the platform
- **[data-model.md](./data-model.md)** — How data is structured: signals, buyers, meetings, purchases, RFPs, conferences

## Things to Learn from Yurii

1. **Access**: How to authenticate, what orgId to use, rate limits
2. **DM info extraction**: Which endpoint returns decision maker contact info for a given account?
3. **Buyer lookup by domain**: Can we search buyers by domain, or only by buyer name/ID?
4. **Meeting summary content**: How detailed are the AI-generated summaries? Do they include actionable intel?
5. **Endpoint stability**: Which endpoints are production-stable vs. experimental?
6. **Data freshness**: How current is the API data vs. what's in the platform?
7. **Rate limits and quotas**: Credits system implications for API usage
8. **Internal vs. external endpoints**: Are there internal-only endpoints not listed in the public API?

## Additional Platform Resources

### Help Center
Starbridge has an external documentation site at `hc.starbridge.ai` with sections covering: Consumers (Sales Reps), Building Bridges, Admins, RFP Writer, Data, Integrations, and Release Notes. May contain useful context for understanding API behavior and data model.

### Credits System
The platform uses a credit-based usage model:
- Organization Credit Balance (Annual Credits Used)
- Personal Credit Usage per user
- Individual credits contribute to the organization's total
{{UNKNOWN: how credits relate to API usage — are API calls credit-consuming? What's the credit cost per endpoint?}}
