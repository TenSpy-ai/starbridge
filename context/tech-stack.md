# Tech Stack — Starbridge GTM

## System Architecture (How Everything Connects)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        OUTBOUND ENGINE                              │
│                                                                     │
│  Starbridge Platform ──→ Signal Data ──→ Supabase (Kushagra's DB)  │
│                                              │                      │
│                                              ▼                      │
│  Clay (Project Endgame) ◄── Signal matching + enrichment            │
│       │                                                             │
│       ▼                                                             │
│  Smartlead ──→ Sends outbound emails at scale                       │
│       │                                                             │
│       │  [positive reply webhook]                                   │
│       ▼                                                             │
│  Clay (receives webhook) ──→ Datagen (cloud agents)                 │
│                                   │                                 │
│                                   ├── Pings Supabase (signals)      │
│                                   ├── Hits SB API (buyer attrs)     │
│                                   ├── LLM processing (top signals)  │
│                                   ├── Generates intel report        │
│                                   └── Sends URL back to Clay        │
│                                              │                      │
│                                              ▼                      │
│  Clay ──→ Slack (#intent-reports) ──→ BDR responds + calls          │
│                                                                     │
│  Apollo ──→ Hosts sequences for Nooks (dialer)                      │
│  Nooks ──→ BDR phone outreach                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Tool-by-Tool Breakdown

### Clay
- **Role**: Orchestration hub. Enrichment, webhook routing, signal matching, Slack dispatch.
- **Workspace ID**: `484780`
- **Key workbooks**:
  - **Project Endgame** — Main workbook. Receives Smartlead webhooks, processes domains, routes to Datagen, receives report URLs back. [Link](https://app.clay.com/workspaces/484780/home/f_0t6nh48BDBiBnAvajMt)
  - **Boiler Room** — Converts signals into intel snippets for BDRs on phones.
- **Key columns** (known): "SLED Signal Bullets" (LLM-generated), two webhook source columns (inbound from Smartlead, return URL from Datagen)
- **Status**: Active, primary orchestration tool

### Smartlead
- **Role**: Outbound email sending at scale. Positive reply detection via webhooks.
- **Scale target**: 3.3M emails/month (ramping in batches)
- **Key feature**: Positive reply webhook triggers the entire fulfillment loop.
- **Data point**: 52% of positive replies come from email 2+ (same thread). Separate campaigns don't compound.
- **Status**: Active. Gurmohit managing deliverability + domain health.

### Supabase
- **Role**: Signal database built by Kushagra. Stores intent signals aligned to accounts/domains.
- **Key queries**: "Pull all signals for X domain related to this SLED account"
- **Schema**: {{UNKNOWN: full schema — need Kushagra meeting to document tables, columns, relationships}}
- **How it's used**: Kushagra's Slack bot pings Supabase for relevant intent signals. In future state, Datagen queries it directly.
- **Status**: Active, central to signal pipeline

### Starbridge Platform / API
- **Role**: The product itself. Source of buyer attributes, DM info, meeting transcripts, contract data, purchase orders, RFPs.
- **API base**: `dashboard.starbridge.ai/api`
- **Access**: Internal-only, dev-gated. "Not easy — only devs can really use it." {{UNKNOWN: auth method, rate limits, access credentials — need Yurii meeting}}
- **Key data**: Decision maker info ("for this SLED account, given these minutes, give me the DM info"), buyer attributes (budget, location, type), meeting summaries, contract details.
- **Status**: Need Yurii to unblock access. Critical dependency for buyer attribute enrichment.

### Datagen
- **Role**: Cloud agents for pipeline orchestration. Sits between Clay and all the data sources.
- **What it does in the pipeline**:
  1. Receives domain from Clay
  2. Pings Supabase for all signals
  3. Feeds signals into LLM → returns top 10 + context
  4. Hits SB API for DM info + buyer attributes
  5. Evaluates what's most relevant for the report
  6. Generates branded intel report (Notion/Webflow/Super.so)
  7. Sends report URL back to Clay via webhook
- **Pricing note**: Start at $50/mo, jump to $500 after 1 month {{UNVERIFIED: this was from onboarding notes — confirm current Datagen pricing}}
- **Status**: Being set up. Need to expense $50 and configure.

### Slack
- **Role**: Dispatch and handoff hub. Where fulfillment meets BDRs.
- **Key channels**:
  - `#intent-reports` — Operational dispatch channel. All positive reply notifications + intel delivery happen here.
  - `#gtm-eng` — GTM engineering team channel
  - `#proj-endgame` — Project Endgame coordination
- **Slack bots**:
  - **endgame-lookup** (Kushagra) — Pings Supabase for intent signals by domain
  - **Starbridge app** — Pulls data from SB platform
- **Status**: Active. Both bots used by Hagel in current manual workflow.

### Apollo
- **Role**: Hosts sequences to activate Nooks (dialer). Some BDR follow-up emails sent through Apollo.
- **Note**: Not the primary outbound tool (that's Smartlead). Apollo is specifically for phone-call activation and some sequenced follow-ups.
- **Status**: Active

### Nooks
- **Role**: Phone dialer for BDRs. Used for calling prospects after positive replies and for top 5-10% of prospects by priority.
- **Status**: Active

### Gamma (Legacy — Being Replaced)
- **Role**: Current intel report generation tool. Hagel feeds context into it to create per-prospect reports.
- **Problems**:
  - Non-deterministic output (same inputs → different reports)
  - Limited branding control
  - Data limited to a snapshot at creation time
  - Manual process
- **Status**: Being replaced by Notion/Webflow/Super.so pipeline

### Gemini
- **Role**: Used by Philippines team to process CSV of signals into intel bullets. Neil helped design the prompts.
- **Status**: Active in current manual workflow. Will be replaced by LLM processing in Datagen pipeline.

### Salesforce
- **Role**: CRM {{UNVERIFIED: mentioned in tech stack list but unclear if primary CRM or secondary — confirm with Henry}}
- **Status**: Active

### HubSpot
- **Role**: CRM / lifecycle management {{UNVERIFIED: mentioned alongside Salesforce — may be dual-CRM or migrating — confirm with Henry}}
- **Status**: Active

### Google Vertex
- **Role**: Used by dev team to process Starbridge data
- **Status**: Active (engineering side)

## Enrichment Stack (For Contact Data)

| Tool | Role | Notes |
|---|---|---|
| **Clay** | Primary enrichment + waterfall | ~65% LinkedIn coverage due to enterprise API restrictions. Expensive but powerful. |
| **FullEnrich** | Initial coverage for email enrichment | Cheaper than Clay. Plan: FullEnrich first, Clay waterfall for gaps. |
| **ZeroBounce** | Monthly email validation across entire TAM | Cheap. Catches ~15% monthly data decay. |
| **Custom scrapers** | Near-100% LinkedIn coverage | Working with {{UNKNOWN: specific vendor names — described as "scrappier early stage startups and agencies"}} with custom web scrapers to get 7-10 prospects/company (up from 3-5). |

## Multi-Channel Stack (Current + Planned)

| Channel | Coverage | Tool | Status |
|---|---|---|---|
| Email | 100% of prospects | Smartlead | Active |
| Phone | Top 5-10% | Apollo → Nooks | Active |
| Paid Ads | Top XX% {{TBD: spend level not decided}} | {{TBD: tool not selected — Jenn Jiao / Mike Shieh owning}} | Planned |
| Snail Mail | Top 0.1-0.5% | Manual → scaled later | Planned (enterprise accounts) |

## Third-Party Services (Detected in Platform)

*Detected via network traffic and script analysis of the Starbridge platform at dashboard.starbridge.ai.*

| Service | Purpose |
|---|---|
| Firebase/Firestore | Real-time data sync |
| Google Analytics | Tracking (G-59CLWXM5MM) |
| LaunchDarkly | Feature flags |
| Sentry | Error monitoring |
| Microsoft Clarity | Session recording |
| Nango | Integration orchestration |
| Google Cloud Storage | Static assets |
