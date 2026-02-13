# Starbridge API — Assumption Test Plan

Every claim in the complete guide traced to its evidence, with a test to verify or bust it.

**How to read this:** Each assumption is tagged with its current evidence level and a concrete test. Run the tests top-down by priority — P0 assumptions block the pipeline, P1 assumptions affect data quality, P2 are nice-to-know.

**Evidence levels:**
- ✅ **Verified** — tested via Datagen tool, got expected results
- 👁️ **Observed** — seen in network traffic curls, not tested via our tools
- 🔮 **Inferred** — assumed from patterns, never directly confirmed
- ❌ **Busted** — tested and failed

---

## P0 — Pipeline Blockers

### 1. Domain → Buyer Lookup Does NOT Work

| | |
|---|---|
| **Claim** | `buyer_search` query field only does Name Contains matching on the `name` field. Searching by domain (e.g., `"lausd.org"`) returns 0 results. |
| **Evidence** | ✅ Verified — tested `"lausd.org"` → 0 results, then `"Los Angeles Unified School District"` → correct match |
| **Impact** | Pipeline receives domains from Smartlead. No automated domain→buyer mapping. |
| **Test** | `buyer_search { "query": "dallasisd.org" }` → expect 0 results. Then `buyer_search { "query": "Dallas Independent School District" }` → expect match. |
| **What would bust it** | If Yurii confirms there's a hidden field or endpoint that searches by domain/website. Or if `buyer_search` has an undocumented `website` filter param. |
| **Workarounds to test** | (a) Search opportunity_search with domain as keyword — does it match `buyerWebsite`? (b) Does `buyer_search` match on the `website` field if you strip `http://`? (c) Is there a `/buyer/search/v2` param we're missing? |

### 2. `buyer_search` Returns the `website` Field

| | |
|---|---|
| **Claim** | Each buyer result includes a `website` field (e.g., `"http://www.lausd.org"`). |
| **Evidence** | ✅ Verified — LAUSD returned `"website": "http://www.lausd.org"` |
| **Impact** | If true, we could build a reverse-lookup table: fetch all buyers in batches, index by domain, map incoming domains. Expensive but possible. |
| **Test** | `buyer_search { "query": "", "buyer_types": ["SchoolDistrict"], "states": ["CA"], "page_size": 100 }` → check that most results have a `website` field populated. What % have it? |
| **What would bust it** | If `website` is null/empty for most buyers — then a reverse-lookup table is useless. |

### 3. Auth via `STARBRIDGE_API_KEY` Secret

| | |
|---|---|
| **Claim** | All API calls authenticate with `Authorization: Bearer <token>` from the Datagen secret. |
| **Evidence** | ✅ Verified — all 8 tools work with it |
| **Impact** | If the token expires or rotates, everything breaks. |
| **Test** | `reference { "action": "user_me" }` → should return user/org info. If it 401s, the key is dead. |
| **Open question** | Is this a long-lived API key or a short-lived JWT? The curl shows a JWT structure (`eyJ...`). JWTs typically expire. If it's a JWT, who refreshes it? |

### 4. Rate Limits / Quotas Exist

| | |
|---|---|
| **Claim** | Unknown. We assume no hard rate limits exist because we haven't hit any. |
| **Evidence** | 🔮 Inferred — no 429 errors seen in any testing |
| **Impact** | If rate limits exist, the automated pipeline could get throttled. |
| **Test** | Run `buyer_search` 20 times in rapid succession (different queries). Do any return 429? Does latency degrade? |
| **What would bust it** | A 429 response or sudden timeout increase after N calls. |

---

## P0 — Opportunity Search (Core Data Endpoint)

### 5. `aiPruned` and `contentSearch` Go Inside `filters`

| | |
|---|---|
| **Claim** | Both flags must be inside the `filters` object, not top-level body. |
| **Evidence** | ✅ Verified — (a) observed in all 4 curls, (b) tested in v9.4, results match curl output exactly (4 Dallas ISD results, same IDs) |
| **Test** | Already passing. Compare `_debug.filters_sent` against expected structure. |

### 6. `aiPruned: true` Reduces Result Count

| | |
|---|---|
| **Claim** | Setting `aiPruned: true` filters out low-relevance results, reducing `totalItems`. |
| **Evidence** | 🔮 Inconclusive — tested `"technology infrastructure"` with CA/LastYear, both on and off returned identical 5 results with same IDs and same totalItems=5. May only affect broader queries. |
| **Impact** | If it doesn't change results, it's a no-op. If it aggressively filters, we might miss relevant records. |
| **Test** | Tested 2026-02-13: Narrow query showed no difference. Need to retest with a broader query (e.g., no state filter, common keyword) to observe filtering effect. |

### 7. `contentSearch: true` Searches Inside Documents

| | |
|---|---|
| **Claim** | Enables full-text search within document content, not just titles/metadata. |
| **Evidence** | 🔮 Inconclusive — tested `"technology infrastructure"` with CA/LastYear, both on and off returned identical 5 results with same IDs and same totalItems=5. May only affect queries where matching content exists inside documents but not in titles. |
| **Impact** | Critical for finding mentions of specific vendors, products, or topics buried inside board meeting minutes. |
| **Test** | Tested 2026-02-13: Narrow query showed no difference. Need a targeted test: search for a term that ONLY appears inside a document body, not in any title. Compare counts with contentSearch on vs. off. |

### 8. `StrategicPlan` Is a Separate Type from `BoardMeeting`

| | |
|---|---|
| **Claim** | These are distinct opportunity types. Searching `["Meeting"]` does NOT return strategic plans. |
| **Evidence** | ✅ Verified — Dallas ISD curl returned 3 BoardMeeting + 1 StrategicPlan with `["BoardMeeting", "StrategicPlan"]`. Our StrategicPlan-only test returned only strategic plans. |
| **Test** | Already confirmed. |

### 9. `buyerFilter.terms` with `field: "Id"` Works for Direct Filtering

| | |
|---|---|
| **Claim** | You can filter opportunities to a specific buyer by passing their UUID via `buyerFilter.terms` with `{"field": "Id", "value": [id], "operation": "Any"}`. |
| **Evidence** | ✅ Verified — LAUSD test returned only LAUSD results. Dallas ISD curl returned only Dallas ISD results. |
| **Test** | Already confirmed. |

### 10. All Opportunity Types Validated

| | |
|---|---|
| **Claim** | The API accepts: `BoardMeeting`, `StrategicPlan`, `Selling`, `PurchaseOrder`, `Contract`. ❌ `Conference` is **NOT valid**. |
| **Evidence** | ✅ `BoardMeeting` — tested, works. ✅ `StrategicPlan` — tested, works. ✅ `Selling` — tested, works. ✅ `PurchaseOrder` — tested 2026-02-13, works. Returns POs with amounts, sorted by OpportunityPurchaseAmount. Top amounts: $856M, $729M. No AI summaries for POs. ✅ `Contract` — tested 2026-02-13, works. Returns contracts with AI summaries, vendor names, amounts, dates. Different from PurchaseOrder. ❌ `Conference` — tested 2026-02-13, **BUSTED**. Returns 400: `"ai.starbridge.model.OpportunityType does not contain element with name 'Conference'"`. Removed from TYPE_MAP in v9.5. |
| **Test** | Completed. 5 valid types: `BoardMeeting`, `StrategicPlan`, `Selling`, `PurchaseOrder`, `Contract`. |

### 11. `fromDateRelativePeriod` Values Are Complete

| | |
|---|---|
| **Claim** | Valid values: `LastOneDay`, `LastThirtyDays`, `LastThreeMonths`, `LastSixMonths`, `LastYear`, `Past`. |
| **Evidence** | ✅ `LastSixMonths` — tested, works. ✅ `LastYear` — tested, works. 🔮 Others — assumed from API patterns. |
| **Test** | `opportunity_search { "types": ["Meeting"], "from_date_relative_period": "LastOneDay", "page_size": 5 }` → should return results from last 24h. Try `Past` too — does it mean "all historical"? |

### 12. `untilDateRelativePeriod` Values Work

| | |
|---|---|
| **Claim** | Valid values: `LastOneDay`, `LastThirtyDays`, `Future`. |
| **Evidence** | ✅ `Future` — tested 2026-02-13, works. Returns RFPs/solicitations with future due dates (all untilDate: "2026-02-13"). OpportunityUntilDate sort works correctly with this filter. |
| **Test** | Completed for `Future`. `LastOneDay` and `LastThirtyDays` still untested. |

### 13. `purchaseAmountFrom` / `purchaseAmountTo` Filter Works

| | |
|---|---|
| **Claim** | Filters purchase orders by dollar amount range. Values passed as strings inside filters. |
| **Evidence** | ✅ Verified — tested 2026-02-13 with $100K–$500K range. All 5 results had purchaseAmount between $130K–$339K. All from City of El Monte. |
| **Test** | Completed. Filter works correctly — amounts are within the specified range. |

### 14. Sort Fields All Work

| | |
|---|---|
| **Claim** | 4 valid sort fields: `SearchRelevancy`, `OpportunityFromDate`, `OpportunityUntilDate`, `OpportunityPurchaseAmount`. |
| **Evidence** | ✅ All 4 verified (2026-02-13). `SearchRelevancy` — default, works. `OpportunityFromDate` — works. `OpportunityPurchaseAmount` — works, top amounts $856M, $729M DESC. `OpportunityUntilDate` — works, correctly orders by due/expiration date ASC. |
| **Test** | Completed. All 4 sort fields functional. |

---

## P1 — Buyer Data Quality

### 15. Buyer Profile Returns 83+ Attributes

| | |
|---|---|
| **Claim** | The profile endpoint returns rich firmographic data including AI scores, budget, enrollment, etc. |
| **Evidence** | ✅ Verified for LAUSD — got AI scores, enrollment, budget, LMS arrays, etc. |
| **Impact** | Data richness varies by buyer type and size. |
| **Test** | Test across buyer types: (a) large school district (LAUSD), (b) small city, (c) state agency, (d) higher ed. Compare which fields are populated vs. null. |

### 16. AI Scores Exist for Most Buyers

| | |
|---|---|
| **Claim** | `procurementHellScore`, `aiAdoptionScore`, `startupFriendlinessScore` are available. |
| **Evidence** | ✅ Verified for LAUSD |
| **Test** | Pull profiles for 5 diverse buyers (big city, small county, state agency, school, higher ed). Check how many have non-null AI scores. |

### 17. `buyerLogoUrl` Is Populated for Most Buyers

| | |
|---|---|
| **Claim** | Buyer logos come from `buyer.logoPath` in opportunity results and from the profile. |
| **Evidence** | ✅ Verified — Dallas ISD returned `logoPath` from Google Cloud Storage |
| **Impact** | Intel reports need logos. If coverage is low, need a fallback. |
| **Test** | `buyer_search { "buyer_types": ["SchoolDistrict"], "states": ["TX"], "page_size": 50 }` → for each buyerId, check `buyer_profile` for logo. What % have one? |

### 18. Contact `emailVerified` Is Accurate

| | |
|---|---|
| **Claim** | `emailVerified: true` means the email is currently deliverable. |
| **Evidence** | 🔮 Inferred — the field exists and has recent `emailLastChecked` dates |
| **Test** | Pull contacts for a known buyer. Send a test email to a `emailVerified: true` address. Does it bounce? (Or: cross-reference with ZeroBounce.) |

### 19. Contact `worksAtBuyer` Is Accurate

| | |
|---|---|
| **Claim** | `worksAtBuyer: true` means the person currently works there. |
| **Evidence** | 🔮 Inferred — field exists, haven't validated |
| **Test** | Pull LAUSD contacts. Spot-check 3-5 names against LinkedIn. Are the `worksAtBuyer: true` contacts actually still there? |

### 20. Large Buyer Contact Counts Are Stable

| | |
|---|---|
| **Claim** | LAUSD has 175+ contacts. Large orgs have 100+. |
| **Evidence** | ✅ Verified at one point in time (175 for LAUSD) |
| **Test** | Re-run `buyer_contacts { "buyer_id": "35617ceb-...", "page_size": 1 }` → check `totalContacts`. Has it changed from 175? |

---

## P1 — Buyer Chat & Full Intel

### 21. Buyer Chat Costs Credits

| | |
|---|---|
| **Claim** | Each `buyer_chat` or `full_intel` (chat portion) call consumes Starbridge credits. Profile/contacts/search are free. |
| **Evidence** | 🔮 Inferred — the guide says so, credit_usage endpoint exists, but we haven't measured before/after |
| **Test** | `reference { "action": "credit_usage" }` → note `creditsUsedSoFar`. Run `buyer_chat`. Check credit_usage again. Did it increase? By how much? |

### 22. Buyer Chat SSE Failures Are Intermittent (~20%)

| | |
|---|---|
| **Claim** | The Starbridge SSE chat endpoint intermittently returns 500 errors. |
| **Evidence** | ✅ Verified — observed at least once during testing. Estimated 20% failure rate. |
| **Test** | Run `buyer_chat` 5 times for the same buyer (LAUSD). Count failures. Is 20% approximately right, or is it higher/lower? |
| **Note** | Expensive test — costs credits. Only do this if you need to quantify reliability for pipeline SLA. |

### 23. `full_intel` Populates Non-Chat Sections Even When Chat Fails

| | |
|---|---|
| **Claim** | If AI chat errors, profile/contacts/opportunities still return. The `ai_intel` field gets an error string. |
| **Evidence** | ✅ Verified — observed during testing |
| **Test** | When a chat failure naturally occurs, confirm the other fields are populated. |

---

## P1 — Bridges

### 24. Bridge Entries Contain Enrichment Columns

| | |
|---|---|
| **Claim** | Bridge entries have up to 152 enrichment columns (from `metadata` action). Data is keyed by `phaseId` UUIDs and `op:` prefixed attribute keys. |
| **Evidence** | ✅ Verified — metadata returned 152 columns, entries returned data keyed by phaseId |
| **Test** | `bridges { "action": "entries", "trigger_id": "<any bridge>", "page_size": 5 }` → verify entries have `phases` and `dataAttributes` populated. |

### 25. Bridge Entry Filters Work

| | |
|---|---|
| **Claim** | You can filter entries by phaseId with operators like `equals`, `contains`, etc. |
| **Evidence** | 🔮 Inferred — documented in the tool but not tested with real filters |
| **Test** | Get a bridge's metadata → pick a phaseId with known values → filter entries by it → confirm results are filtered. |

---

## P2 — Edge Cases & Unknowns

### 26. `extendedPagination=false` Affects Results

| | |
|---|---|
| **Claim** | The `extendedPagination` query param exists. Unknown effect. |
| **Evidence** | 👁️ Observed in curls (always `false`) |
| **Test** | Same query with `extendedPagination=true` vs `false`. Compare `totalItems` and `totalPages`. If different, document the behavior. |
| **Note** | Can't test via our Datagen tool (hardcoded to `false`). Would need a direct curl. |

### 27. `buyer_search` City/County/Population Filters Work

| | |
|---|---|
| **Claim** | v9 added `city`, `county`, `parent_name`, `min_population`, `max_population` filters. |
| **Evidence** | 🔮 Inferred — code sends them, never tested |
| **Test** | `buyer_search { "city": "Austin", "states": ["TX"], "page_size": 10 }` → should return buyers in Austin, TX. `buyer_search { "min_population": 500000, "buyer_types": ["City"], "page_size": 10 }` → should return large cities only. |

### 28. Feed API Requires Bridge/Subscription Setup

| | |
|---|---|
| **Claim** | The Feed API (`/organization/{orgId}/feed/item/v3`) returned 0 results in both curls. |
| **Evidence** | 👁️ Observed — 0 results for both buyer-scoped and global feed queries |
| **Test** | Ask Yurii: does the Feed API require active Bridge subscriptions to populate? Or is the org just empty? |
| **Alternative test** | If we have a Bridge with known entries, try the Feed API with that Bridge's buyer IDs. |

### 29. `Contract` Is a Valid Opportunity Type

| | |
|---|---|
| **Claim** | `Contract` is a valid API opportunity type. |
| **Evidence** | ✅ Verified — tested 2026-02-13. Returns contracts with AI summaries, vendor names, amounts, dates, status fields. Different from PurchaseOrder — contracts have richer summary text with vendor names and terms. |
| **Test** | Completed. Contract type works and returns distinct data from PurchaseOrder. |

### 30. Opportunity `highlights` Field Populates with Search Queries

| | |
|---|---|
| **Claim** | The `highlights` field in opportunity results contains search term highlighting. |
| **Evidence** | ✅ Verified — tested 2026-02-13 with `"cybersecurity"` search. `highlights.content` populated with `<b>` tags around matching terms, showing document excerpts where search terms appear (e.g., `"<b>cybersecurity</b> plan"`). Works both with and without aiPruned. |
| **Test** | Completed. Highlights are populated when a `search_query` is provided. Empty `{}` when no query. |

### 31. JWT Token Expiration

| | |
|---|---|
| **Claim** | The auth token may be a JWT with an expiration. |
| **Evidence** | 👁️ Observed — curl shows JWT structure with `exp` claim |
| **Test** | Decode the JWT in `STARBRIDGE_API_KEY` (base64 decode the middle segment). Check the `exp` field. Is it already expired? When does it expire? If it's an API key (not JWT), this is a non-issue. |
| **Impact** | If the token expires and no refresh mechanism exists, all tools break silently. |

---

## Test Execution Order

Run these in this order to maximize learning with minimum credit spend:

**Round 1 — Free, fast, high-value (10 min)**
1. Test #10 — Validate `PurchaseOrder` and `Conference` types
2. Test #6 — Compare `aiPruned` on vs off (same query)
3. Test #7 — Compare `contentSearch` on vs off (same query)
4. Test #11 — Try `LastOneDay` and `Past` date filters
5. Test #12 — Try `untilDateRelativePeriod: "Future"` with RFPs
6. Test #13 — Try purchase amount range filter
7. Test #14 — Try `OpportunityPurchaseAmount` and `OpportunityUntilDate` sort
8. Test #27 — Try city/population filters on buyer_search
9. Test #29 — Try `Contract` type
10. Test #30 — Check highlights field with a search query

**Round 2 — Free, slower, data quality (20 min)**
11. Test #2 — Bulk buyer_search to check website field coverage
12. Test #15 — Profile across 4 buyer types
13. Test #16 — AI score coverage across buyer types
14. Test #17 — Logo coverage check
15. Test #20 — Re-check LAUSD contact count
16. Test #25 — Bridge entry filtering

**Round 3 — Costs credits (budget accordingly)**
17. Test #21 — Measure credit cost per chat call
18. Test #3 — Check if API key is a JWT, decode expiration

**Round 4 — Requires Yurii / external**
19. Test #4 — Rate limit stress test (maybe hold until Yurii confirms)
20. Test #18 — Email deliverability spot-check
21. Test #19 — LinkedIn verification of contacts
22. Test #28 — Feed API question for Yurii
23. Test #31 — JWT expiration check

---

## Running the Tests

All tests use the Datagen custom tools. Quick reference:

```
Tool                         UUID
buyer_search                 e69f8d37-6601-4e73-a517-c8ea434b877b
buyer_profile                74345947-2f94-4eed-97a3-d10b2b2e3ad9
buyer_contacts               b81036af-1c0f-4b9a-a03b-4c301927518f
opportunity_search           c15b3524-cd08-4f7a-ae78-d73f6a6c2bad
buyer_chat                   043dc240-4517-4185-9dbb-e24ae0abf04d
full_intel                   711d57c2-cf2e-40a5-a505-e0a5e0ee8947
bridges                      ceb785ae-5506-4982-9a1f-7e9e28de4cca
reference                    211f4e80-7a3b-4760-8752-770a22b03c2d
```

For each test, record:
- **Input** — exact params sent
- **Output** — key fields from response
- **Verdict** — ✅ Confirmed / ❌ Busted / ⚠️ Partially confirmed / 🔮 Inconclusive
- **Notes** — anything unexpected

After running, update the complete-guide.md with any busted assumptions or new findings.

---

## Reliable API Chaining Patterns

Tested 2026-02-13. All chains verified with real data — Dallas ISD (SchoolDistrict) and Coastal Bend College (HigherEducation).

### Chain 1: buyer_search → buyer_profile ✅ RELIABLE

```
buyer_search { "query": "Dallas Independent School District", "states": ["TX"] }
  → buyerId: "c279ef27-a88d-4422-802d-ee6bf1e1e466"

buyer_profile { "buyer_id": "c279ef27-..." }
  → Full 83+ attribute profile with AI scores, enrollment, budget, procurement data
```

**Tested with:** Dallas ISD → 83+ attributes, procurementHellScore: 42, enrollment: 139,802, lmsArray, budget data.

**Join key:** `buyer_search.buyers[].buyerId` → `buyer_profile.buyer_id` input → `buyer_profile.profile.id`

**Gotcha:** Field name differs: search returns `buyerId`, profile returns `id`. Values are identical UUIDs.

---

### Chain 2: buyer_search → buyer_contacts ✅ RELIABLE

```
buyer_search { "query": "Dallas Independent School District" }
  → buyerId: "c279ef27-..."

buyer_contacts { "buyer_id": "c279ef27-...", "page_size": 10 }
  → 121 contacts with emails, phones, titles
```

**Tested with:** Dallas ISD → 121 contacts, all @dallasisd.org, all worksAtBuyer=true, emailVerified=true.

**Join key:** `buyer_search.buyers[].buyerId` → `buyer_contacts.buyer_id` input → `buyer_contacts.resolved_buyer_id`

**Gotcha:** None — clean chain. Contacts are alphabetical by last name by default.

---

### Chain 3: buyer_search → opportunity_search (buyer_ids filter) ✅ RELIABLE

```
buyer_search { "query": "Dallas Independent School District" }
  → buyerId: "c279ef27-..."

opportunity_search { "types": ["Meeting"], "buyer_ids": ["c279ef27-..."], "from_date_relative_period": "LastYear" }
  → 5 board meetings, ALL for Dallas ISD only
```

**Tested with:** Dallas ISD → 5 BoardMeeting results. All have `buyerId: "c279ef27-..."`, `buyerName: "Dallas ISD"`, `buyerType: "SchoolDistrict"`. Debug confirms `buyer_id_filter_applied: true`.

**Join key:** `buyer_search.buyers[].buyerId` → `opportunity_search.buyer_ids[]` input

**Gotcha:** Max 20 buyer_ids per request. If you need more, paginate the buyer IDs.

---

### Chain 4: opportunity_search → buyer_profile ✅ RELIABLE

```
opportunity_search { "search_query": "technology infrastructure", "types": ["Meeting"], "states": ["TX"] }
  → uniqueBuyerIds: ["75689faf-...", "f1199cf6-...", ...]

buyer_profile { "buyer_id": "75689faf-..." }  (Coastal Bend College from opps)
  → Full profile with AI scores, enrollment, budget
```

**Tested with:** Coastal Bend College buyerId from opportunity results. Profile returned matching name, type, tags, website, logo.

**Cross-tool consistency verified:**

| Field | opportunity_search | buyer_profile |
|-------|-------------------|---------------|
| Name | `buyerName: "Coastal Bend College"` | `name: "Coastal Bend College"` ✅ |
| Type | `buyerType: "HigherEducation"` | `type: "HigherEducation"` ✅ |
| Tags | `buyerTags: ["CommunityCollege", "HigherEducation"]` | `tags: ["CommunityCollege", "HigherEducation"]` ✅ |
| State | `buyerState: "TX"` | `stateCode: "TX"` ✅ |
| Website | `buyerWebsite: "http://www.coastalbend.edu"` | `url: "http://www.coastalbend.edu"` ✅ |
| Logo | `buyerLogoUrl: "https://storage.googleapis.com/..."` | `extraData.logoPath: "https://storage.googleapis.com/..."` ✅ |

**Join key:** `opportunity_search.uniqueBuyerIds[]` OR `opportunity_search.opportunities[].buyerId` → `buyer_profile.buyer_id` input

**Gotcha:** Field names differ across tools (see Field Name Mapping below). Values are always consistent.

---

### Chain 5: opportunity_search → buyer_contacts ✅ RELIABLE

```
opportunity_search { "search_query": "technology infrastructure", "types": ["Meeting"], "states": ["TX"] }
  → uniqueBuyerIds: ["75689faf-...", ...]

buyer_contacts { "buyer_id": "75689faf-...", "page_size": 10 }
  → 35 contacts for Coastal Bend College
```

**Tested with:** Coastal Bend College from opportunity results → 35 contacts, all @coastalbend.edu, all worksAtBuyer=true, emailVerified=true.

**Join key:** Same as Chain 4.

**Gotcha:** Small orgs may have few contacts (Coastal Bend College: 35). Large districts have 100+ (Dallas ISD: 121, LAUSD: 175+).

---

### Chain 6: Full Pipeline (search → opps → contacts) ✅ RELIABLE

```
1. buyer_search { "query": "Dallas Independent School District" }
     → buyerId: "c279ef27-..."

2. opportunity_search { "buyer_ids": ["c279ef27-..."], "types": ["Meeting", "Contract"], "from_date_relative_period": "LastYear" }
     → meetings with AI summaries, contract data

3. buyer_contacts { "buyer_id": "c279ef27-...", "page_size": 50 }
     → 121 contacts with verified emails

4. buyer_profile { "buyer_id": "c279ef27-..." }
     → AI scores, enrollment, budget, procurement analysis
```

**This is the recommended pipeline flow for intel reports.** Steps 2-4 can run in parallel once you have the buyerId.

---

### Chain 7: Global opp search → multi-buyer contacts ✅ RELIABLE (with caveats)

```
1. opportunity_search { "search_query": "cybersecurity", "types": ["RFP"], "states": ["TX"], "until_date_relative_period": "Future" }
     → uniqueBuyerIds: ["abc...", "def...", "ghi...", ...]

2. FOR EACH buyerId in uniqueBuyerIds:
     buyer_contacts { "buyer_id": buyerId, "page_size": 20 }
       → contacts for each buyer with active cybersecurity RFPs
```

**Caveat:** Each buyer_contacts call is a separate API request. With 20 unique buyers, that's 20 sequential calls. No batch contacts endpoint exists. Use `ThreadPoolExecutor(max_workers=5)` for parallelism.

**Caveat:** Some buyers may have 0 contacts. Handle empty results gracefully.

---

## Cross-Tool Field Name Mapping

**This is the #1 gotcha when chaining tools.** Values are always consistent, but field names differ across tools.

| Concept | buyer_search | buyer_profile | buyer_contacts | opportunity_search |
|---------|-------------|---------------|----------------|-------------------|
| **Buyer ID** | `buyerId` | `id` | `resolved_buyer_id` | `buyerId` |
| **Name** | `name` | `name` | *(not returned)* | `buyerName` |
| **Type** | `type` | `type` | *(not returned)* | `buyerType` |
| **State** | `stateCode` | `stateCode` | *(not returned)* | `buyerState` |
| **Website** | `website` | `url` | *(not returned)* | `buyerWebsite` |
| **Logo** | *(not returned)* | `extraData.logoPath` | *(not returned)* | `buyerLogoUrl` |
| **Tags** | *(not returned)* | `tags` | *(not returned)* | `buyerTags` |
| **County** | `county` | `extraData.county` | *(not returned)* | *(not returned)* |
| **ZIP** | `zip` | `extraData.address.zip` | *(not returned)* | *(not returned)* |

**Key pattern:** `buyer_search` uses flat field names. `buyer_profile` nests under `extraData`/`metadata`. `opportunity_search` prefixes with `buyer*`. `buyer_contacts` only returns the `resolved_buyer_id` — no buyer metadata.

---

## Chaining Limitations & Gotchas

### 1. No batch contacts endpoint
You can't pass multiple buyer IDs to `buyer_contacts` at once. Each buyer requires a separate call. For 20 buyers, that's 20 API calls. Parallelize with `ThreadPoolExecutor(max_workers=5)`.

### 2. No domain → buyer lookup
The pipeline receives domains from Smartlead (e.g., "acmegov.com") but `buyer_search` only does Name Contains matching. Domain search returns 0 results. **Workaround needed:** Either build a reverse-lookup table from bulk buyer exports, or have a manual mapping step.

### 3. buyer_contacts returns no buyer metadata
When chaining from opportunity_search → buyer_contacts, you lose the buyer name/type/state context. If you need it, also call buyer_profile or carry the data forward from the opportunity results.

### 4. buyer_chat costs credits and is slow
buyer_chat (and full_intel) are the only credit-costing tools. They also take 30-90 seconds and fail ~20% of the time. **Don't include them in automated chains unless you have retry logic and credit budget.**

### 5. opportunity_search uniqueBuyerIds can be stale
The `uniqueBuyerIds` array is computed from the current page of results only. If page 1 has 40 results from 15 buyers, you only get those 15 IDs — not all buyers matching the query. Paginate if you need comprehensive coverage.

### 6. Max 20 buyer_ids per opportunity_search
The buyer_ids filter is capped at 20 UUIDs per request. If you have more, split into multiple requests.

### 7. Auto-resolve (search_query) in profile/contacts is fragile
Tools 2, 3, 5 accept `search_query` for auto-resolution, but this uses buyer_search internally and picks the top match. If the name is ambiguous (e.g., "Springfield"), you may get the wrong buyer. **Always prefer passing explicit `buyer_id` when chaining.**

---

## Round 1 Test Results Summary (2026-02-13)

| # | Assumption | Verdict | Notes |
|---|-----------|---------|-------|
| 5 | aiPruned/contentSearch inside filters | ✅ Confirmed | Fixed in v9.4, verified against curl data |
| 6 | aiPruned reduces result count | 🔮 Inconclusive | Same results on/off for narrow query |
| 7 | contentSearch searches inside docs | 🔮 Inconclusive | Same results on/off for narrow query |
| 10 | PurchaseOrder type | ✅ Confirmed | Works, returns amounts, no summaries |
| 10 | Conference type | ❌ BUSTED | 400 error, removed from TYPE_MAP in v9.5 |
| 10 | Contract type | ✅ Confirmed | Works, returns AI summaries + vendor names |
| 12 | untilDateRelativePeriod: Future | ✅ Confirmed | Returns future-dated RFPs |
| 13 | purchaseAmountFrom/To | ✅ Confirmed | All results within specified range |
| 14 | OpportunityPurchaseAmount sort | ✅ Confirmed | Correct descending order by amount |
| 14 | OpportunityUntilDate sort | ✅ Confirmed | Correct ordering by due/expiration date |
| 29 | Contract is valid type | ✅ Confirmed | Rich data distinct from PurchaseOrder |
| 30 | Highlights field | ✅ Confirmed | `<b>` tags around matching search terms |

### Chaining Test Results (2026-02-13)

| Chain | Pattern | Verdict | Test Buyers |
|-------|---------|---------|-------------|
| 1 | buyer_search → buyer_profile | ✅ Reliable | Dallas ISD |
| 2 | buyer_search → buyer_contacts | ✅ Reliable | Dallas ISD (121 contacts) |
| 3 | buyer_search → opp_search (buyer_ids) | ✅ Reliable | Dallas ISD (5 meetings) |
| 4 | opp_search → buyer_profile | ✅ Reliable | Coastal Bend College |
| 5 | opp_search → buyer_contacts | ✅ Reliable | Coastal Bend College (35 contacts) |
| 6 | Full pipeline (search→opps→contacts→profile) | ✅ Reliable | Dallas ISD |
| — | Cross-tool data consistency | ✅ Consistent | All field values match across tools |
