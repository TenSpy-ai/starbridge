# Starbridge API — Endpoint Reference

**Base URL**: `https://dashboard.starbridge.ai/api`

{{UNVERIFIED: endpoints below were captured from observing the Starbridge platform's network traffic. They are real endpoints the platform calls, but we have not tested them directly via API. Payload schemas, auth requirements, and response shapes need Yurii to confirm.}}

## Authentication

{{UNKNOWN: exact auth mechanism — the platform has an API Keys page at `/settings/api-keys` for creating "Secret Keys", suggesting bearer token auth. Need Yurii to confirm.}}

```bash
# Hypothesized auth pattern
curl 'https://dashboard.starbridge.ai/api/...' \
  -H "Authorization: Bearer YOUR_SECRET_KEY"
```

## Organization Context

Most endpoints are scoped to an organization: `/organization/{orgId}/...`

{{UNKNOWN: Starbridge's own orgId — get from Yurii or from the platform URL when logged in}}

---

## Core Data APIs

### Bridges (Triggers)

Bridges are the core organizational unit — saved searches/workflows that surface signals.

| Endpoint | Method | Description |
|---|---|---|
| `/organization/{orgId}/trigger` | GET | List all Bridges with filters |
| `/organization/{orgId}/trigger/{triggerId}` | GET | Get specific Bridge details |
| `/organization/{orgId}/trigger/{triggerId}/entry/metadata` | GET | Bridge entry metadata |
| `/organization/{orgId}/trigger/{triggerId}/entry/totals` | PUT | Get entry totals (counts) |
| `/organization/{orgId}/trigger/{triggerId}/entry/v2` | PUT | Paginated Bridge entries (the actual signal results) |
| `/organization/{orgId}/trigger/{triggerId}/filters-sorts` | GET | Bridge filter and sort configuration |

**Pipeline relevance**: Bridge entries (`/entry/v2`) could be an alternative to Supabase for signal retrieval — if a Bridge is configured for a specific domain or category, its entries ARE the signals. {{TBD: use Bridge entries vs. Supabase as signal source? Depends on coverage and query flexibility.}}

### Opportunity / Search APIs

These are the primary search endpoints for Starbridge's data.

| Endpoint | Method | Description |
|---|---|---|
| `/opportunity/v3` | PUT | **Search opportunities** — meetings, RFPs, purchases. This appears to be the main multi-type search endpoint. |
| `/buyer/search` | PUT | Search buyers |
| `/buyer/search/v2` | PUT | Search buyers (v2 — likely enhanced) |
| `/buyer/type` | GET | Buyer type definitions (Higher Ed, School District, City, etc.) |

**Pipeline relevance**: These are likely the **highest-value endpoints** for the intel report pipeline.

`/opportunity/v3` (PUT) — {{UNKNOWN: request body schema. Likely accepts:}}
- Search query (natural language, OR-based — consistent with platform UI)
- Filters: buyer type, date range, opportunity type (meeting/RFP/purchase)
- Pagination parameters
- Sort order

`/buyer/search/v2` (PUT) — {{UNKNOWN: request body schema. Key question: can we search by domain?}}
- If yes: this is how we get buyer info for a domain from a positive reply
- If no: we need another way to map domain → buyer ID first

### Feed APIs

| Endpoint | Method | Description |
|---|---|---|
| `/organization/{orgId}/feed/subscription/new-count` | POST | Count of new feed items |
| `/organization/{orgId}/feed/item/status/counts` | GET | Feed item status counts |
| `/organization/{orgId}/feed/item/v3` | GET | Paginated feed items |

**Pipeline relevance**: Low. Feed is the personalized home dashboard — not useful for per-domain lookups.

### Conversation APIs (Ask Starbridge)

| Endpoint | Method | Description |
|---|---|---|
| `/organization/{orgId}/conversation` | GET | Get chat conversations from Ask Starbridge |

**Pipeline relevance**: Potentially interesting as a fallback. If direct API queries are hard, we could potentially use Ask Starbridge's chat interface programmatically to research a buyer. {{UNVERIFIED: feasibility unknown — may not support programmatic use}}

### RFP Proposal APIs

| Endpoint | Method | Description |
|---|---|---|
| `/organization/{orgId}/rfp-proposal-draft` | GET | Get RFP proposal drafts |

**Pipeline relevance**: Low for intel reports. Could be useful for future RFP-related campaigns.

### Tag APIs

| Endpoint | Method | Description |
|---|---|---|
| `/organization/{orgId}/tag` | GET | List tags |
| `/organization/{orgId}/tag/usage` | GET | Tag usage statistics |

**Pipeline relevance**: Low. Tags are organizational metadata.

### Buyer Filter APIs

| Endpoint | Method | Description |
|---|---|---|
| `/organization/{orgId}/buyer-filter` | GET | Buyer filter configurations |

**Pipeline relevance**: Medium. Understanding how buyers are filtered in the platform could inform how we query for specific buyer types.

### Integration APIs

| Endpoint | Method | Description |
|---|---|---|
| `/organization/{orgId}/data/integration/connection` | GET | Get integration connections (Salesforce, HubSpot, Slack, etc.) |
| `/organization/{orgId}/data/integration` | GET | Integration configuration |
| `/organization/{orgId}/nango/login` | POST | Nango integration auth |

**Pipeline relevance**: Low for intel reports. Relevant if we need to push data to CRM.

### Data Store APIs

| Endpoint | Method | Description |
|---|---|---|
| `/organization/{orgId}/data/store` | GET | Data store status |
| `/organization/{orgId}/data/file` | GET | Data files |

**Pipeline relevance**: {{UNKNOWN: what's in the data store? Could be useful.}}

### Credit Usage APIs

| Endpoint | Method | Description |
|---|---|---|
| `/organization/{orgId}/credit-usage` | GET | Organization credit usage |
| `/organization/{orgId}/user/{userId}/credit-usage` | GET | User credit usage |

**Pipeline relevance**: Important for monitoring — API calls likely consume credits. Need to understand credit costs per call type.

### User APIs

| Endpoint | Method | Description |
|---|---|---|
| `/organization/{orgId}/user/filter-settings` | GET | User filter preferences |

---

## Admin APIs

{{UNVERIFIED: admin endpoints may require elevated permissions — confirm with Yurii}}

| Endpoint | Method | Description |
|---|---|---|
| `/admin/user` | GET | List all platform users |
| `/admin/buyer/file/campaign/name` | GET | Campaign names for buyer files |
| `/admin/foia/campaign` | GET | FOIA campaigns |
| `/admin/foia/campaign-name` | GET | FOIA campaign names |
| `/buyer-file` | GET | Buyer files list |

**Pipeline relevance**: FOIA campaign data could be interesting for signal enrichment (which FOIA campaigns are active for which buyers?), but this is a stretch goal.

---

## Priority Endpoints for the Pipeline

### P0 — Must Have for V2

| Endpoint | Why | What We Need to Learn |
|---|---|---|
| `/buyer/search/v2` | Look up buyer by domain → get name, type, location, logo | {{UNKNOWN: can it search by domain? Request/response schema?}} |
| `/opportunity/v3` | Search meetings/purchases for a specific buyer → get DM info, budget, contract details | {{UNKNOWN: request schema, how to filter by buyer/domain}} |

### P1 — High Value

| Endpoint | Why | What We Need to Learn |
|---|---|---|
| `/organization/{orgId}/trigger/{triggerId}/entry/v2` | Pull Bridge results for enriched signal data | {{UNKNOWN: which Bridges exist and what they contain}} |
| `/buyer/type` | Buyer type definitions for report formatting | Simple GET — likely low-risk |

### P2 — Nice to Have

| Endpoint | Why |
|---|---|
| `/organization/{orgId}/credit-usage` | Monitor API credit consumption |
| `/organization/{orgId}/conversation` | Explore Ask Starbridge as a data source |

---

## URL Structure Reference (Platform Pages)

For reference when navigating the platform UI to understand what data is available:

| Page | URL |
|---|---|
| Home/Feed | `/` |
| Bridges List | `/bridge` |
| Bridge Detail | `/bridge/{bridgeId}` |
| Ask Starbridge | `/ask-starbridge` |
| RFP Writer | `/proposal` |
| Meetings | `/board-meetings-strategic-plans` |
| Meeting Detail | `/board-meetings-strategic-plans/board-meeting/{meetingId}` |
| Purchases | `/purchases-contracts` |
| RFPs | `/rfp` |
| Conferences | `/conferences` |
| Buyers | `/accounts/buyers` |
| Settings | `/settings/{section}` |
| API Keys | `/settings/api-keys` |
| Admin Dashboard | `/admin-dashboard/{section}` |
