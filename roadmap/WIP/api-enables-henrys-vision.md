# How the Starbridge API Enables Henry's Vision

Written 2026-02-13. Based on Henry's [Feb 4 Slack messages](https://starbridgeai.slack.com/archives/C0ACXMNMVHS/p1770237473006119) and tested API capabilities from [complete-guide.md](../../systems/starbridge-api-datagen/complete-guide.md).

## The Situation Henry Described

Henry outlined two approaches:

**Original plan (API-dependent):**
1. Positive response → webhook → Datagen
2. Datagen queries Supabase for signals
3. Datagen queries Starbridge API for buyer attributes (budget, DMs, logo)
4. Datagen creates intel report landing page

**Fallback plan (CSV-only, what Henry pivoted to):**
> "Justin (CEO) said the API might not be viable... so we're going to consider now getting all of the 'auxiliary data' in that initial export"

The fallback: Yurii pre-exports everything into a massive CSV → Supabase. No API needed at runtime.

**What's changed:** We've now tested all 8 Starbridge API tools extensively. The API works. Every endpoint is reliable. This document maps exactly what the API unlocks vs. what the CSV gives you.

---

## What the CSV Export Gives You

Per Henry's description, the export includes one row per signal with columns for:
- Intent signal (meeting summary, contract, RFP, etc.)
- Account name / domain
- Budget (if Yurii includes it)
- Other attributes Yurii adds to the export

**Limitations of CSV-only:**
1. **Stale the moment it's generated.** Yurii does periodic exports. A positive reply on day 15 of a 30-day export cycle is working with 15-day-old data.
2. **Fixed columns.** You get whatever Yurii defined at export time. Need a new attribute? Wait for the next export.
3. **No DM contacts.** Henry's screenshot showed he wanted "decision maker with title, email, phone" — but mapping the *right* DM to the *specific signal context* (e.g., the cybersecurity decision-maker for a cybersecurity signal) requires runtime intelligence, not a static column.
4. **No on-demand depth.** The CSV has breadth (33K-50K companies) but shallow data per account. The API has depth (83+ attributes, 121 contacts, 20+ board meetings per buyer).
5. **33K-50K rows in Supabase.** That's the export size. Starbridge has 296K+ buyers. The other 250K+ are only reachable via API.

---

## What the API Adds — Mapped to Henry's Intel Report Vision

### Signal Enrichment (Henry's Steps 3-4: "sift through and identify top 10 signals")

The CSV gives you Supabase signals. The API gives you **the original source material** those signals came from.

**What you can do now:**

```
# For each signal's account, pull the actual board meeting or contract
opportunity_search {
  "search_query": "cybersecurity",
  "types": ["Meeting", "Contract"],
  "buyer_ids": ["c279ef27-..."],  # from signal's buyer
  "from_date_relative_period": "LastYear"
}
```

**Real result:** Dallas ISD returns 5 board meetings with AI-generated summaries. Coastal Bend College returns 20 opportunities including $1.1M Ellucian contract, $93K Salesforce/Tableau deal, and Element451 AI CRM deployment.

**Why this matters for intel reports:** Instead of "Dallas ISD discussed technology" (signal), the report can say "Dallas ISD's board discussed IT modernization on [date], specifically [summary excerpt]. They currently spend $X with [vendor] on [product]." That's the difference between a cold email and a credible one.

---

### Buyer Attributes (Henry's Step 5: "pulls: budgets; decision makers; account logo")

Every attribute Henry listed is available via `buyer_profile`. Tested and verified:

| Henry Wants | API Tool | Real Field | Real Example |
|---|---|---|---|
| **Budget** | `buyer_profile` | `extraData.budgetAmount` | City of Austin: $5.9B (verified) |
| **Account logo** | `buyer_profile` | `extraData.logoPath` | `https://storage.googleapis.com/starbridge-fe-static/logo/...` |
| **Buyer type** | `buyer_profile` | `type` | `"SchoolDistrict"`, `"HigherEducation"`, `"City"` |
| **Location** | `buyer_profile` | `metadata.address.*` | `"9400 N Central Expy, Dallas, TX 75231"` |
| **Website** | `buyer_profile` | `url` | `"http://www.dallasisd.org"` |
| **Enrollment** | `buyer_profile` | `extraData.totalEnrollment` | Dallas ISD: 139,802 |
| **LMS/SIS** | `buyer_profile` | `extraData.lmsArray`, `extraData.sis` | `["GoogleClassroom", "Schoology"]`, `"Powerschool"` |

**Bonus attributes NOT in any CSV export** (proprietary AI-generated scores):

| Attribute | Real Example | Intel Report Use |
|---|---|---|
| `procurementHellScore` (0-100) | Dallas ISD: 42, Austin: 48 | "Moderate procurement friction — co-op purchasing is the fastest path" |
| `aiAdoptionScore` (0-100) | Austin: 83 (Enthusiastic), Coastal Bend: 31 (Open) | "This buyer is actively piloting AI tools" |
| `propensityToSpend` | Dallas: "HighlyCautious" (16), Coastal Bend: "OpenToSpend" (73) | "Budget is tight — lead with ROI" vs "Active purchasing window" |
| `startupFriendlinessScore` (0-100) | Austin: 95, Baylor: 78, Coastal Bend: 15 | "Very receptive to new vendors" vs "Stick to established channels" |
| `propensityToSpendSummary` | Full paragraph with budget analysis, fiscal year context | Drop directly into report as "Budget Context" section |
| `procurementHellSummary` | Full procurement playbook with co-op recommendations | Drop into report as "How to Sell to This Buyer" section |

**These scores don't exist in any CSV.** They're computed by Starbridge's AI and only available via the profile endpoint. They're also incredibly actionable — a BDR calling an account with `propensityToSpend: "HighlyCautious"` needs a completely different pitch than one with `"OpenToSpend"`.

---

### Decision Makers (Henry's "DM with title, email, phone for that specific signal")

This is the hardest part of Henry's vision. The CSV can include *a* DM per account, but Henry wants the DM **contextual to the signal** — the cybersecurity decision-maker for a cybersecurity signal.

**What the API gives you:**

```
buyer_contacts { "buyer_id": "c279ef27-...", "page_size": 50 }
```

**Real result for Dallas ISD:** 121 contacts, all verified, including:
- Robert Abel — Chief of Human Capital Management — rabel@dallasisd.org — (972) 925-4200
- Brent Anthony Alfred — Chief Construction Officer — balfred@dallasisd.org — (972) 925-7210
- Patricia Alvarado — Director of Library and Media Services — palvarado@dallasisd.org

**For contextual DM matching**, the pipeline would:
1. Get all contacts via `buyer_contacts`
2. Get the signal context (e.g., "cybersecurity budget discussion")
3. Use LLM to match: "Given these 121 contacts and a cybersecurity signal, who's the most relevant DM?" → probably the CIO or CISO
4. Include that person in the report with their verified contact info

A CSV gives you one static DM. The API gives you 121 contacts to intelligently choose from per signal.

---

### AI-Powered Intel (Not in Henry's original plan — new capability)

`buyer_chat` and `full_intel` go beyond what any CSV can do:

```
full_intel {
  "search_query": "Coastal Bend College",
  "ai_question": "What are their key technology priorities and who is the CIO?"
}
```

**Real result (21 seconds):**
- AI identified **Michael Rowlett** as Director of IT and CISO (not in the contacts list with that framing)
- Extracted 5 strategic priorities from the 2025-2030 Strategic Plan
- Found specific tech initiatives: Barracuda cybersecurity training, Element451 AI CRM, Blackboard LMS
- Listed active contracts: Ellucian ($1.1M), Salesforce/Tableau ($93K), Element451 ($60K)

**This is a full account dossier in one call.** No CSV can replicate this — it's real-time AI synthesis across board meetings, contracts, and strategic plans.

---

## Prescriptive Recommendation: Hybrid Approach

Don't choose between CSV and API. Use both.

### V1 (Ship by 2/17): CSV + Supabase Only

Henry's fallback plan. Works now, no API dependency.

```
1. Positive reply → Smartlead webhook → Clay → Datagen
2. Datagen queries Supabase (where Yurii's CSV exports live)
3. Datagen LLM ranks top 10 signals
4. Datagen generates Notion landing page (Tier 1: signals only)
5. Datagen posts to Slack #intent-reports
```

**What's in the report:** Signal bullets, account name, basic firmographics from CSV columns.
**What's missing:** Logo, budget, DM contacts, procurement scores, meeting excerpts.

### V2 (Week 2-3): Add API for Buyer Attributes

After V1 is live and stable, add one API call per positive reply:

```
# After Supabase gives you the signals + buyer name:
buyer_profile { "search_query": "Dallas Independent School District" }
```

**What this adds to the report (zero additional complexity):**
- Account logo URL → embed in report header
- Budget amount + fiscal year → "Budget Context" section
- Buyer type + location → report subheading
- `propensityToSpendSummary` → "Spending Outlook" section (verbatim from API)
- `procurementHellScore` → "Ease of Sale" indicator
- `aiAdoptionScore` → "Tech Readiness" indicator

**Cost:** Free (no credits). ~200ms per call.

### V2.5 (Week 3-4): Add API for Contacts + Contextual DM

```
buyer_contacts { "buyer_id": "...", "page_size": 50 }
```

Then LLM picks the most relevant DM given the signal context.

**What this adds:** DM contact card in the report — name, title, verified email, phone. Contextually matched to the signal (cybersecurity signal → CISO, not the librarian).

**Cost:** Free. ~200ms.

### V3 (Week 4-6): Add Opportunity Search for Deep Intel

```
opportunity_search {
  "buyer_ids": ["..."],
  "types": ["Meeting", "Contract", "StrategicPlan"],
  "from_date_relative_period": "LastYear"
}
```

**What this adds:**
- Recent board meeting excerpts with AI summaries
- Active contracts with vendor names, amounts, expiration dates
- Strategic plans with multi-year technology roadmaps
- Specific document excerpts via `highlights.content`

**Cost:** Free. ~2-10 seconds (content_search + ai_pruned makes it slower but higher quality).

### V3+ (Optional): Full Intel for High-Value Accounts

For Tier 3 accounts (highest value), run the full composite:

```
full_intel {
  "search_query": "...",
  "ai_question": "Who is the CIO, what is their tech budget, what are their top IT priorities, and what contracts are expiring soon?"
}
```

**Cost:** Credits (~1 credit per call). 15-45 seconds. Reserve for top-tier accounts only.

---

## What the CSV Can Never Do

| Capability | CSV | API |
|---|---|---|
| Real-time data (today's board meeting) | Stale by design | Live |
| 296K buyers (vs 33-50K in export) | Fixed subset | Full database |
| 83+ attributes per buyer | Fixed columns from Yurii | All attributes on demand |
| 121 contacts per buyer | 1 DM per row (if any) | Full contact list with verification |
| AI-generated procurement playbook | Not possible | `procurementHellSummary` |
| AI-generated budget analysis | Not possible | `propensityToSpendSummary` |
| Contextual DM matching | Static | LLM + full contact list |
| Board meeting excerpts | Not in CSV | `highlights.content` with search terms bolded |
| Contract expiration dates | Maybe a column | Full contract records with amounts and dates |
| On-demand depth for any buyer | Only if in export | Any of 296K+ buyers |

---

## Bottom Line

Henry pivoted to CSV-only because "Justin said the API might not be viable." The API is viable — we've tested every endpoint with real data and documented everything in [complete-guide.md](../../systems/starbridge-api-datagen/complete-guide.md).

The CSV is still the right V1 path (it's faster to ship, no API dependency for launch). But V2 should absolutely use the API. The data it adds — especially the AI-generated scores (`procurementHellScore`, `aiAdoptionScore`, `propensityToSpend`) and the full contact lists — are the difference between a generic signal summary and an intel report that makes BDRs sound like they've done hours of research.

**Recommended next conversation with Henry:** "The API works. V1 ships on CSV as planned. But for V2, here's what the API adds to every report for free in < 1 second: [show Baylor profile, Dallas contacts, Coastal Bend full_intel]. Should we plan V2 integration for week 2?"
