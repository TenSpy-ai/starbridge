# Starbridge API Suite — Complete Guide

## What This Is

8 Datagen custom tools wrapping Starbridge's B2B government/institutional sales intelligence platform. Starbridge tracks procurement opportunities, board meetings, RFPs, purchases, and decision-maker contacts across 296K+ government buyers.

**Data Scale:**
- 114M+ opportunities (board meetings, RFPs, purchases, contracts, strategic plans)
- 296K+ buyers with 83 searchable attributes each
- 150+ contacts per large buyer (with verified emails)
- 152 enrichment columns available in Bridges

**Authentication:** All tools use the `STARBRIDGE_API_KEY` secret (contains `Bearer ...`). No auth handling needed in your code.

## Version History

| Date | Tools | Version | Changes |
|------|-------|---------|---------|
| 2026-02-13 | `opportunity_search` | v9.6 | Added `createdAt`, `parentBuyerId`, `rfps[]`, `purchaseOrders[]` to opportunity output |
| 2026-02-13 | `buyer_contacts`, `full_intel` | v3.0 | Added `normalizedTitles`, `source`, `middleName`, `salutation`, `foiaRequestContact`, `metadataV2`, `createdAt`, `updatedAt` to contact output. `full_intel` also gained `contactId`, `firstName`, `lastName`, `worksAtBuyer`, `emailLastChecked` it was previously missing. |
| 2026-02-12 | All 8 tools | — | Added domain→buyer resolution workaround via `opportunity_search` |
| 2026-02-05 | All 8 tools | v2.1 | Fixed buyer search to use terms array with Name Contains filter |

---

## Tool Inventory

| # | Tool | UUID | When to Use |
|---|------|------|-------------|
| 1 | `starbridge_buyer_search` | `e69f8d37-6601-4e73-a517-c8ea434b877b` | Find buyers by name/keyword. **Start here.** |
| 2 | `starbridge_buyer_profile` | `74345947-2f94-4eed-97a3-d10b2b2e3ad9` | Get full firmographic dossier on a buyer |
| 3 | `starbridge_buyer_contacts` | `b81036af-1c0f-4b9a-a03b-4c301927518f` | Get decision-maker contacts with emails/phones |
| 4 | `starbridge_opportunity_search` | `c15b3524-cd08-4f7a-ae78-d73f6a6c2bad` | Find board meetings, RFPs, purchases, conferences |
| 5 | `starbridge_buyer_chat` | `043dc240-4517-4185-9dbb-e24ae0abf04d` | Ask AI questions about a specific buyer |
| 6 | `starbridge_full_intel` | `711d57c2-cf2e-40a5-a505-e0a5e0ee8947` | Get everything about a buyer in one call |
| 7 | `starbridge_bridges` | `ceb785ae-5506-4982-9a1f-7e9e28de4cca` | Manage saved search workflows |
| 8 | `starbridge_reference` | `211f4e80-7a3b-4760-8752-770a22b03c2d` | Get buyer types, credits, filters, org info |

---

## Dependency Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    HOW DATA FLOWS BETWEEN TOOLS                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  starbridge_buyer_search (name/keyword)                         │
│       │                                                         │
│       ├──→ buyerId ──→ starbridge_buyer_profile                 │
│       │                                                         │
│       ├──→ buyerId ──→ starbridge_buyer_contacts                │
│       │                                                         │
│       ├──→ buyerId ──→ starbridge_buyer_chat                    │
│       │                                                         │
│       └──→ buyerId ──→ starbridge_opportunity_search            │
│                            (via buyer_ids → buyerFilter.terms)  │
│                                                                 │
│  starbridge_opportunity_search                                  │
│       └──→ uniqueBuyerIds[] ──→ starbridge_buyer_contacts       │
│                                  (for each buyerId)             │
│                                                                 │
│  starbridge_full_intel (COMPOSITE)                              │
│       └──→ Internally chains all of the above in parallel       │
│                                                                 │
│  starbridge_bridges                                             │
│       └──→ orgId (auto-bootstrapped) ──→ triggerId ──→ entries  │
│                                                                 │
│  starbridge_reference                                           │
│       └──→ orgId (auto-bootstrapped) ──→ credits, filters, etc  │
│                                                                 │
│  ⚡ Tools 2, 3, 5 accept EITHER buyer_id OR search_query        │
│     and auto-resolve internally (no need to call search first)  │
│     ⚠️ Auto-resolve uses buyer name only — domains don't work   │
│                                                                 │
│  🔑 DOMAIN → BUYER RESOLUTION (workaround)                      │
│     opportunity_search is the ONLY tool that can resolve a       │
│     domain to a buyerId. It does full-text content search, so    │
│     domains appearing in board meeting docs get matched.         │
│                                                                 │
│     domain (e.g. "riverhead.net")                                │
│       └──→ opportunity_search(search_query=domain)               │
│              └──→ results[0].buyerId + results[0].buyerName      │
│                     └──→ feed into any downstream tool            │
│                                                                 │
│     ⚠️ Not guaranteed — only works if the domain appears in      │
│        document content. But tested and confirmed working.       │
└─────────────────────────────────────────────────────────────────┘
```

---

# Tool 1: `starbridge_buyer_search`

**Purpose:** Search Starbridge's 296K+ buyer database. This is the **foundation tool** — the `buyerId` it returns feeds into all other tools.

## Inputs

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | No | `""` | Buyer name or keyword (e.g. `"University"`, `"Los Angeles Unified"`). Uses Name Contains matching. |
| `buyer_types` | string[] | No | `[]` | Filter by category (see valid values below) |
| `states` | string[] | No | `[]` | Two-letter state codes like `["CA", "NY"]` |
| `city` | string | No | `""` | Filter by city name (Contains match) |
| `county` | string | No | `""` | Filter by county name (Contains match) |
| `parent_name` | string | No | `""` | Filter by parent org name (Contains match) |
| `min_population` | int | No | — | Minimum population (cities/counties) |
| `max_population` | int | No | — | Maximum population (cities/counties) |
| `country_codes` | string[] | No | `["US"]` | Country filter |
| `page_size` | int | No | `25` | Results per page (max 1000) |
| `page_number` | int | No | `1` | 1-indexed pagination |

### Valid `buyer_types` Values

Must be **PascalCase with no spaces**:

```
StateAgency, PoliceDepartment, FireDepartment, Library, City, County,
HigherEducation, School, SchoolDistrict, SpecialDistrict, State,
IndigenousGovernment, Federal, Other
```

⚠️ **GOTCHA:** It's `HigherEducation` not `Higher Education`, `SchoolDistrict` not `School District`.

## Outputs

```json
{
  "totalItems": 295847,
  "pageNumber": 1,
  "pageSize": 25,
  "resultCount": 25,
  "termsApplied": [...],  // Exact filter terms sent to API (useful for debugging)
  "buyers": [
    {
      "buyerId": "2263ae7b-f103-4bc4-b65b-bea6f19c6d62",  // ← USE THIS DOWNSTREAM
      "name": "California Community Colleges",
      "type": "Local, HigherEducation",  // comma-separated tags
      "stateCode": "CA",
      "countryCode": "US",
      "website": "http://cccco.edu",
      "foiaRequestMethod": "Email",
      "city": "Sacramento",
      "zip": "95811",
      "street": "1102 Q Street"
    }
  ]
}
```

## Gotchas

1. **⚠️ Domain search DOES NOT work on this tool.** The `query` field does Name Contains matching only — it does NOT search the `website` field. `"lausd.org"` returns 0 results. `"riverhead.net"` returns 0 results. Use the full buyer name instead: `"Los Angeles Unified School District"`. If you only have a domain, use `opportunity_search` as a resolution bridge — see "Domain → Buyer Resolution" in Common Workflows.

2. **Fuzzy matching can miss:** Searching `"LAUSD"` may not match. Use the full official name for best results.

3. **totalItems can be huge:** With no filters, you'll see 295K+ results. Always filter or paginate.

4. **The `buyerId` UUID is everything:** Capture it — all downstream tools need it.

5. **Multiple buyer_types = OR logic:** `["City", "County"]` returns both cities AND counties.

6. **v9 added geo filters:** `city`, `county`, `parent_name`, `min_population`, `max_population` are available for targeted searches.

## Example

```json
{
  "query": "Los Angeles Unified School District",
  "buyer_types": ["SchoolDistrict"],
  "states": ["CA"],
  "page_size": 5
}
```

## More Examples

### Search by exact official name (most reliable)

```json
{
  "query": "Dallas Independent School District",
  "page_size": 5
}
```

### Search by keyword (returns many matches — always filter)

```json
{
  "query": "University",
  "buyer_types": ["HigherEducation"],
  "states": ["TX"],
  "page_size": 3
}
```

**Real response** (117 total results, showing first 3):
```json
{
  "totalItems": 117,
  "pageNumber": 1,
  "resultCount": 3,
  "buyers": [
    {
      "buyerId": "15d3bf13-faac-42ca-8f77-a22ea09c215a",
      "name": "Baylor University",
      "type": "HigherEducation",
      "stateCode": "TX",
      "website": "http://www.baylor.edu/",
      "city": "Waco",
      "county": "McLennan",
      "zip": "76798"
    },
    {
      "buyerId": "5486970f-7620-4666-9e30-0d4c786564ec",
      "name": "Lamar University",
      "type": "UndergraduateInstitution, HigherEducation",
      "stateCode": "TX",
      "website": "https://www.lamar.edu",
      "parentName": "Texas State University System"
    },
    {
      "buyerId": "4375ef14-9f88-47a9-8749-9f0fbee47dbc",
      "name": "University Of Houston",
      "type": "ResearchInstitution, HigherEducation",
      "stateCode": "TX",
      "website": "http://www.uh.edu",
      "county": "Harris",
      "parentName": "University of Houston System"
    }
  ]
}
```

### Browse all school districts in a state (no query needed)

```json
{
  "query": "",
  "buyer_types": ["SchoolDistrict"],
  "states": ["FL"],
  "page_size": 3
}
```

**Real response** (79 total results, showing first 3):
```json
{
  "totalItems": 79,
  "resultCount": 3,
  "buyers": [
    {
      "buyerId": "e552d768-3f6f-4857-b3c2-e10f626eca9b",
      "name": "Miami-Dade County Public Schools",
      "type": "SchoolDistrict",
      "stateCode": "FL",
      "website": "https://www.dadeschools.net",
      "city": "Miami",
      "county": "Miami-Dade"
    },
    {
      "buyerId": "e0374037-01a6-4536-ba3e-e015b90cd86e",
      "name": "Broward County Public Schools",
      "type": "SchoolDistrict",
      "stateCode": "FL",
      "website": "https://browardschools.com",
      "city": "Fort Lauderdale",
      "county": "Broward",
      "foiaRequestMethod": "Special"
    },
    {
      "buyerId": "564e0e9c-c558-4363-9fc0-1ad62f912f27",
      "name": "Hillsborough County Public Schools",
      "type": "SchoolDistrict",
      "stateCode": "FL",
      "website": "https://www.hillsboroughschools.org/",
      "city": "Tampa",
      "county": "Hillsborough",
      "foiaRequestMethod": "OnlineForm"
    }
  ]
}
```

### Filter by city (v9 geo filter)

```json
{
  "query": "",
  "city": "Austin",
  "buyer_types": ["City", "County", "SchoolDistrict"],
  "states": ["TX"],
  "page_size": 3
}
```

**Real response** (25 total results, showing first 3):
```json
{
  "totalItems": 25,
  "resultCount": 3,
  "buyers": [
    {
      "buyerId": "7c006d87-5a64-4452-a18c-51d7432bce34",
      "name": "Austin Independent School District",
      "type": "SchoolDistrict",
      "stateCode": "TX",
      "website": "http://www.austinisd.org",
      "city": "Austin",
      "county": "Travis"
    },
    {
      "buyerId": "c85deb59-edd4-4f92-ba33-7e89bd98aed9",
      "name": "Travis County",
      "type": "County",
      "stateCode": "TX",
      "website": "https://co.travis.tx.us",
      "city": "Austin",
      "population": 1363767,
      "parentName": "State of Texas"
    },
    {
      "buyerId": "3046ef35-c505-42a7-b318-4b2f05b7623f",
      "name": "City of Austin",
      "type": "Municipal, City",
      "stateCode": "TX",
      "website": "https://www.austintexas.gov/",
      "city": "Austin",
      "population": 993588,
      "parentName": "Travis County"
    }
  ]
}
```

### Large cities only (population filter)

```json
{
  "query": "",
  "buyer_types": ["City"],
  "min_population": 500000,
  "page_size": 3
}
```

**Real response** (40 total results, showing first 3):
```json
{
  "totalItems": 40,
  "resultCount": 3,
  "buyers": [
    {
      "buyerId": "b913b2e9-30fa-41fe-a225-880037c4c709",
      "name": "New York City",
      "type": "Municipal, City",
      "stateCode": "NY",
      "website": "https://nyc.gov",
      "population": 8478072,
      "parentName": "County of New York",
      "foiaRequestMethod": "OnlineForm"
    },
    {
      "buyerId": "78bbda9c-cfdc-4b6a-b5a9-00f8adcc0b3e",
      "name": "City of Los Angeles",
      "type": "Municipal, City",
      "stateCode": "CA",
      "website": "https://lacity.gov",
      "population": 3878704,
      "parentName": "County of Los Angeles"
    },
    {
      "buyerId": "f383c3dc-62de-45e3-bcd6-2a32de80ff82",
      "name": "City of Chicago",
      "type": "Municipal, City",
      "stateCode": "IL",
      "website": "http://www.cityofchicago.org",
      "population": 2721308,
      "parentName": "Cook County"
    }
  ]
}
```

### What NOT to search (these return 0 results)

```json
// ❌ Domain search does NOT work
{ "query": "lausd.org" }           // → 0 results
{ "query": "www.dallasisd.org" }   // → 0 results

// ❌ Abbreviations are unreliable
{ "query": "LAUSD" }               // → may return 0 results
{ "query": "NYC DOE" }             // → may return 0 results

// ✅ Use full official names instead
{ "query": "Los Angeles Unified School District" }   // → correct match
{ "query": "New York City Department of Education" }  // → correct match
```

---

# Tool 2: `starbridge_buyer_profile`

**Purpose:** Get full firmographic profile with 83+ attributes including AI-generated scores, enrollment, budgets, and procurement data.

## Inputs

Provide **ONE** of these:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `buyer_id` | string | No* | Direct buyer UUID (fastest) |
| `search_query` | string | No* | Buyer name to auto-resolve (⚠️ domain search does not work — use full name) |

*One is required. If both provided, `buyer_id` takes precedence.

## Outputs

```json
{
  "resolved_buyer_id": "2263ae7b-f103-4bc4-b65b-bea6f19c6d62",
  "search_query_used": "California Community Colleges",  // null if buyer_id was provided
  "profile": {
    "id": "2263ae7b-...",
    "name": "California Community Colleges",
    "commonName": "CCC",
    "type": "HigherEducation",
    "stateCode": "CA",
    "countryCode": "US",
    "url": "http://cccco.edu",
    "tags": ["Local", "HigherEducation"],
    "parentId": "3f2504e0-...",  // parent org UUID
    "foiaRequestMethod": "Email",
    
    "metadata": {
      "address": {
        "street1": "1102 Q Street",
        "city": "Sacramento",
        "state": "CA",
        "zip": "95811",
        "phone": "(916) 445-8752"
      },
      
      // AI-Generated Scores (0-100)
      "procurementHellScore": 58,      // Higher = harder to sell to
      "aiAdoptionScore": 71,           // Higher = more AI-forward
      "startupFriendlinessScore": 90,  // Higher = more open to startups
      
      // Enrollment & Budget
      "enrollment": { "total": 2108927 },
      "budgetAmount": 15000000,
      "budgetLatestYear": 2024,
      "budgetConfidence": "High",
      "fiscalYearStartDate": "07/01",
      
      // Higher Ed Specific
      "higherEducationSystem": true,
      "endowment": 500000000,
      "graduationRate": 0.45,
      "retentionRate": 0.72,
      "institutionType": "Community College",
      "levelOfInstitution": "2-year",
      "controlOfInstitution": "Public",
      "religiousAffiliation": null,
      "lmsArray": ["Canvas", "Blackboard"],
      "sisModernizationStatus": "In Progress",
      "recruitmentAdmissionsCrmArray": ["Slate"],
      
      // K-12 Specific
      "schoolDistrictType": "Unified",
      "schoolDistrictLocale": "Urban",
      "numberOfSchools": 785,
      
      // Government IDs
      "ipedsIdNumeric": 123456,        // Higher Ed
      "ncesId": "0622710",             // K-12
      "ncesStateDistrictId": "CA-1964733",
      "censusIdPid6": "...",
      "censusIdGidId": "...",
      "sgcId": "..."
    }
  }
}
```

## Gotchas

1. **Auto-resolution uses top match:** If `search_query` is ambiguous (e.g. `"Springfield"`), check `resolved_buyer_id` and `profile.name` to confirm you got the right one. **Domain names will return 0 results** — always use the full buyer name.

2. **Null fields vary by buyer type:**
   - `enrollment` is null for Cities
   - `endowment` is null for K-12
   - `schoolDistrictType` is null for Higher Ed
   - AI scores may be null for small/new buyers

3. **Higher Ed has the richest data.** K-12 and State Agencies are next. Cities and Counties have sparser profiles.

4. **AI scores are proprietary.** Starbridge generates these — not all buyers have them.

## Examples

### Get profile by buyer UUID (fastest — use when you have the ID from a previous search)

```json
{
  "buyer_id": "c279ef27-a88d-4422-802d-ee6bf1e1e466"
}
```

**Real response** (Dallas ISD — truncated to key fields):
```json
{
  "resolved_buyer_id": "c279ef27-a88d-4422-802d-ee6bf1e1e466",
  "search_query_used": null,
  "profile": {
    "id": "c279ef27-a88d-4422-802d-ee6bf1e1e466",
    "name": "Dallas Independent School District",
    "type": "SchoolDistrict",
    "url": "http://www.dallasisd.org",
    "stateCode": "TX",
    "tags": ["SchoolDistrict"],
    "metadata": {
      "address": {
        "street1": "9400 N Central Expy",
        "city": "Dallas",
        "state": "TX",
        "zip": "75231",
        "phone": "(972)925-3700"
      }
    },
    "extraData": {
      "commonName": "Dallas ISD",
      "totalEnrollment": 139802,
      "enrollmentTrend": "StronglyDecreasing",
      "yoyChangeInEnrollment": -4.08,
      "lmsArray": ["GoogleClassroom", "MicrosoftTeamsForEducation", "Schoology"],
      "sis": "Powerschool",
      "procurementHellScore": 42,
      "propensityToSpendScore": 16,
      "propensityToSpend": "HighlyCautious",
      "schoolDistrictType": "RegularLocalDistrict",
      "schoolDistrictLocale": "City",
      "schoolDistrictNumberOfSchools": 240,
      "schoolDistrictElementarySchools": 156,
      "schoolDistrictMiddleSchools": 42,
      "schoolDistrictHighSchools": 40,
      "schoolDistrictTotalStudents": 139246,
      "employeeFte": 21472.5,
      "fiscalYearStartDate": "07/01",
      "freeOrReducedLunchEligiblePercentage": 89,
      "englishLearners": 44.4,
      "schoolDistrictMedianHouseholdIncome": 64306
    }
  }
}
```

### Get profile by name (auto-resolves via buyer_search internally)

```json
{
  "search_query": "Dallas Independent School District"
}
```

Returns the same response as above, with `"search_query_used": "Dallas Independent School District"` instead of `null`.

### Get profile for a Higher Ed institution (richest data — endowment, graduation rate, LMS, AI scores)

```json
{
  "buyer_id": "15d3bf13-faac-42ca-8f77-a22ea09c215a"
}
```

**Real response** (Baylor University — truncated to key fields):
```json
{
  "resolved_buyer_id": "15d3bf13-faac-42ca-8f77-a22ea09c215a",
  "profile": {
    "name": "Baylor University",
    "type": "HigherEducation",
    "url": "http://www.baylor.edu/",
    "stateCode": "TX",
    "tags": ["HigherEducation"],
    "extraData": {
      "commonName": "Baylor University",
      "totalEnrollment": 20824,
      "enrollmentTrend": "ModeratelyDecreasing",
      "yoyChangeInEnrollment": -3.72,
      "lmsArray": ["InstructureCanvas"],
      "sis": "EllucianBanner",
      "aiAdoptionScore": 66,
      "startupFriendlinessScore": 78,
      "propensityToSpend": "Selective",
      "propensityToSpendScore": 40,
      "higherEdEndowment": 2100000000,
      "higherEdRetentionRate": 91,
      "higherEdGraduationRate": 80,
      "higherEdInstitutionType": "LargeResearchUniversity",
      "higherEdLevelOfInstitution": "FourYears",
      "higherEdControlOfInstitution": "Private",
      "higherEdReligiousAffiliation": "ChristianBaptist",
      "higherEdMascot": "Bears",
      "higherEdFullTimeEnrollment": 21235,
      "higherEdUndergradEnrollment": 15155,
      "higherEdNumberOfOnCampusResidents": 8044,
      "higherEdRecruitmentAdmissionsCrmArray": ["TechnolutionsSlate"],
      "higherEdAdvisingStudentSuccessCrmArray": ["EABNavigate"],
      "fiscalYearStartDate": "06/01",
      "employeeFte": 3410
    }
  }
}
```

### Get profile for a City (population, budget, procurement scores, startup friendliness)

```json
{
  "buyer_id": "3046ef35-c505-42a7-b318-4b2f05b7623f"
}
```

**Real response** (City of Austin — truncated to key fields):
```json
{
  "resolved_buyer_id": "3046ef35-c505-42a7-b318-4b2f05b7623f",
  "profile": {
    "name": "City of Austin",
    "type": "City",
    "url": "https://www.austintexas.gov/",
    "stateCode": "TX",
    "tags": ["Municipal", "City"],
    "extraData": {
      "commonName": "Austin",
      "population": 993588,
      "parentName": "Travis County",
      "budgetAmount": 5900000000,
      "budgetLatestYear": 2025,
      "budgetConfidence": "Verified",
      "budgetSbita": 85744000,
      "aiAdoptionScore": 83,
      "procurementHellScore": 48,
      "propensityToSpend": "Selective",
      "propensityToSpendScore": 30,
      "startupFriendlinessScore": 95,
      "employeeFte": 16195,
      "fiscalYearStartDate": "10/01",
      "mainPhoneNumber": "(512) 974-2000"
    }
  }
}
```

### Get profile for a State Agency (sparser data — budget, employee count, FOIA info)

```json
{
  "search_query": "California Department of Education"
}
```

**Real response** (auto-resolved to correct buyer):
```json
{
  "resolved_buyer_id": "77f978c9-68b0-40e0-9be0-7a6342027522",
  "search_query_used": "California Department of Education",
  "profile": {
    "name": "California Department of Education",
    "type": "StateAgency",
    "url": "https://www.cde.ca.gov",
    "stateCode": "CA",
    "tags": [],
    "extraData": {
      "commonName": "California Dept of Education",
      "parentName": "State of California",
      "budgetAmount": 158690000,
      "budgetConfidence": "Verified",
      "budgetLatestYear": 2024,
      "employeeFte": 2672,
      "fiscalYearStartDate": "07/01",
      "mainPhoneNumber": "(916) 319-0800"
    },
    "foiaRequestMethod": "Download"
  }
}
```

> **Note:** State Agencies have the sparsest profiles — no AI scores, no enrollment, no LMS/SIS data. Higher Ed has the richest data, followed by K-12 School Districts, then Cities/Counties, then State Agencies.

### What NOT to pass as search_query

```json
// ❌ Domain — will return 0 results or wrong match
{ "search_query": "dallasisd.org" }

// ❌ Abbreviation — may pick wrong buyer
{ "search_query": "Dallas ISD" }

// ✅ Full official name
{ "search_query": "Dallas Independent School District" }
```

---

# Tool 3: `starbridge_buyer_contacts`

**Purpose:** Get decision-maker contacts with verified emails, phone numbers, and LinkedIn URLs. Supports pagination for large orgs (LAUSD has 175+ contacts).

## Inputs

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `buyer_id` | string | No* | — | Direct buyer UUID |
| `search_query` | string | No* | — | Buyer name to auto-resolve (⚠️ domain search does not work) |
| `page_size` | int | No | `50` | Contacts per page |
| `page_number` | int | No | `1` | 1-indexed pagination |

*One of `buyer_id` or `search_query` required.

## Outputs (v3.0 — full raw API fields)

```json
{
  "resolved_buyer_id": "35617ceb-709a-45ef-af49-5c9707c3b164",
  "search_query_used": "Los Angeles Unified School District",
  "totalContacts": 175,
  "pageNumber": 1,
  "pageSize": 50,
  "contacts": [
    {
      "contactId": "7adc3921-...",
      "name": "Soheil Katal",
      "firstName": "Soheil",
      "lastName": "Katal",
      "middleName": null,
      "salutation": "Mr.",
      "title": "Chief Information Officer",
      "normalizedTitles": ["Chief Information Officer"],
      "email": "soheil.katal@lausd.net",
      "phone": "+1-213-241-4906",
      "linkedInUrl": "https://linkedin.com/in/soheilkatal",
      "worksAtBuyer": true,
      "emailVerified": true,
      "emailLastChecked": "2025-12-10T05:00:24Z",
      "source": "WebAgent",
      "foiaRequestContact": false,
      "metadataV2": {
        "findContactRunId": "trun_...",
        "worksAtBuyerRunId": "trun_...",
        "foundByWebAgentModel": "Pro"
      },
      "createdAt": "2025-08-15T10:30:00Z",
      "updatedAt": "2025-12-10T05:00:24Z"
    }
  ]
}
```

### Contact Field Reference

| Field | Type | Description | Pipeline Use |
|-------|------|-------------|-------------|
| `contactId` | UUID | Unique contact identifier | Dedup, tracking |
| `name` | string | Full display name | Report display |
| `firstName` / `lastName` | string | Name components | Email personalization |
| `middleName` | string\|null | Middle name/initial (e.g. `"F."`) | Formal correspondence |
| `salutation` | string\|null | `"Mr."`, `"Dr."`, `"Ms."`, etc. | Formal correspondence |
| `title` | string | Raw title as listed on buyer site | Display |
| `normalizedTitles` | string[] | **Standardized title variants** — key for role matching | **DM targeting** |
| `email` | string\|null | Email address | Outreach |
| `phone` | string\|null | Phone number | Outreach |
| `linkedInUrl` | string\|null | LinkedIn profile URL | Research |
| `worksAtBuyer` | boolean | Verified current employee | Filter |
| `emailVerified` | boolean | Email deliverability confirmed | Filter |
| `emailLastChecked` | ISO datetime | When email was last verified | Freshness |
| `source` | string | How contact was discovered: `"WebAgent"`, `"Manual"`, `"FOIA"` | Data quality signal |
| `foiaRequestContact` | boolean | Contact came from FOIA request | Data provenance |
| `metadataV2` | object | `foundByWebAgentModel` (`"Pro"` or `"Core"`), run IDs | Debug/audit |
| `createdAt` | ISO datetime | When contact was first discovered | Data freshness |
| `updatedAt` | ISO datetime | Last modification time | Data freshness |

### `normalizedTitles` — Why This Matters

`normalizedTitles` is the most important new field for the pipeline. Raw `title` values are inconsistent (e.g. `"Asst. Supt. for Business"` vs `"Assistant Superintendent for Business"`), but `normalizedTitles` provides standardized variants:

- `"Network Administrator"` → `["Administrator of Network"]`
- `"Assistant Principal"` → `["Assistant Principal"]`
- `"Interim Assistant Superintendent for Business"` → `["Interim Assistant Superintendent of Business", "Assistant Superintendent of Business"]`
- `"District Wide Director of Safety & Security"` → `["Director of Safety District Wide", "Director of Security District Wide", "Director of Safety", "Director of Security"]`

Use `normalizedTitles` for:
- **DM targeting**: Match contacts to roles like "Superintendent", "CIO", "Director of Technology"
- **Role deduplication**: Multiple title variants resolve to the same normalized form
- **Pipeline filtering**: Search across all variants to find relevant decision-makers

### `source` Values

| Source | Meaning |
|--------|---------|
| `"WebAgent"` | Discovered by Starbridge's AI web-crawling agents |
| `"Manual"` | Manually entered (rare) |
| `"FOIA"` | Sourced from FOIA/public records request |

Most contacts are `"WebAgent"` sourced. The `metadataV2.foundByWebAgentModel` field shows whether it was the `"Pro"` or `"Core"` agent model.

## Gotchas

1. **For outreach, filter on `emailVerified: true` AND `worksAtBuyer: true`.** This gives you current employees with deliverable emails.

2. **Not all contacts have phone/LinkedIn.** These fields can be null.

3. **Large orgs need pagination.** LAUSD has 175+ contacts, NYC DOE even more. Use `page_size: 100` and multiple pages.

4. **Title formats vary wildly:** `"CIO"`, `"Chief Information Officer"`, `"Director, IT"` are all common. Don't rely on exact matching — **use `normalizedTitles` instead for reliable role matching.**

5. **Some emails don't match buyer domain.** A contact might have a personal Gmail. Filter on the buyer's domain for highest quality.

6. **`emailLastChecked` tells freshness.** Recent date = more trustworthy. Old date = might have bounced since.

7. **`normalizedTitles` can have multiple entries.** A single contact may have 1-4 normalized title variants. Search across all of them.

8. **`foiaRequestContact` contacts may lack email.** FOIA-sourced contacts often only have phone/name.

## Examples

### Get contacts by buyer UUID (fastest — use when chaining from buyer_search or opportunity_search)

```json
{
  "buyer_id": "c279ef27-a88d-4422-802d-ee6bf1e1e466",
  "page_size": 3
}
```

**Real response** (Riverhead CSD — 30 total contacts, showing first 3, v3.0 with full fields):
```json
{
  "resolved_buyer_id": "bf7105f9-7827-46b6-a3f4-b8a0ee9ebd31",
  "search_query_used": null,
  "totalContacts": 30,
  "pageNumber": 1,
  "pageSize": 3,
  "contacts": [
    {
      "contactId": "89688bd9-71dd-4e88-8762-96329f0d7f0b",
      "name": "Joshua Brown",
      "firstName": "Joshua",
      "lastName": "Brown",
      "middleName": null,
      "salutation": null,
      "title": "Network Administrator",
      "normalizedTitles": ["Administrator of Network"],
      "email": "joshua.brown@riverhead.net",
      "phone": "+1-631-369-1998",
      "linkedInUrl": null,
      "worksAtBuyer": true,
      "emailVerified": true,
      "emailLastChecked": "2026-02-05T05:00:15.936230Z",
      "source": "WebAgent",
      "foiaRequestContact": false,
      "metadataV2": {
        "findContactRunId": "trun_047c230ba85e41649739f955ed851054",
        "worksAtBuyerRunId": "trun_bc61097a682847748b291330322f3d2c",
        "foundByWebAgentModel": "Pro"
      },
      "createdAt": "2025-10-06T18:30:11.416914Z",
      "updatedAt": "2025-10-22T07:33:54.736427Z"
    },
    {
      "contactId": "05d0450c-0636-4942-8811-14ef5ddea3be",
      "name": "Marianne F. Cartisano",
      "firstName": "Marianne",
      "lastName": "Cartisano",
      "middleName": "F.",
      "salutation": "Dr.",
      "title": "Interim Assistant Superintendent for Business",
      "normalizedTitles": [
        "Interim Assistant Superintendent of Business",
        "Assistant Superintendent of Business"
      ],
      "email": "marianne.cartisano@g.riverhead.net",
      "phone": "+1-631-369-6708",
      "linkedInUrl": null,
      "worksAtBuyer": true,
      "emailVerified": true,
      "emailLastChecked": "2025-12-28T05:00:57.856634Z",
      "source": "WebAgent",
      "foiaRequestContact": false,
      "metadataV2": {
        "findContactRunId": "trun_047c230ba85e41649a54476496220502",
        "worksAtBuyerRunId": "trun_219b05ab9e214f2cada053d3c1aca912",
        "foundByWebAgentModel": "Pro"
      },
      "createdAt": "2025-08-29T19:09:06.717793Z",
      "updatedAt": "2026-02-06T06:02:55.068904Z"
    },
    {
      "contactId": "b29da15a-46c1-4a14-9cb8-71ccd10e0773",
      "name": "Terrence Culhane",
      "firstName": "Terrence",
      "lastName": "Culhane",
      "middleName": null,
      "salutation": null,
      "title": "District Wide Director of Safety & Security",
      "normalizedTitles": [
        "Director of Safety District Wide",
        "Director of Security District Wide",
        "Director of Safety",
        "Director of Security"
      ],
      "email": "terrence.culhane@gmail.com",
      "phone": "+1-631-369-2279",
      "linkedInUrl": null,
      "worksAtBuyer": true,
      "emailVerified": true,
      "emailLastChecked": "2026-02-04T05:01:12.032334Z",
      "source": "WebAgent",
      "foiaRequestContact": false,
      "metadataV2": {
        "findContactRunId": "trun_047c230ba85e416498dfb6522ffce724",
        "worksAtBuyerRunId": "trun_b8617b9561414b0a90d9849e1261d6df",
        "foundByWebAgentModel": "Core"
      },
      "createdAt": "2025-10-05T06:45:09.005990Z",
      "updatedAt": "2026-01-13T06:09:08.520413Z"
    }
  ]
}
```

### Get contacts by name (auto-resolves via buyer_search internally)

```json
{
  "search_query": "Dallas Independent School District",
  "page_size": 50
}
```

Returns the same structure, with `"search_query_used": "Dallas Independent School District"` instead of `null`.

### Paginate for large orgs (LAUSD has 175+ contacts)

```json
{
  "buyer_id": "35617ceb-709a-45ef-af49-5c9707c3b164",
  "page_size": 100,
  "page_number": 1
}
```

Then page 2:

```json
{
  "buyer_id": "35617ceb-709a-45ef-af49-5c9707c3b164",
  "page_size": 100,
  "page_number": 2
}
```

### What NOT to pass as search_query

```json
// ❌ Domain — will return 0 results
{ "search_query": "lausd.org" }

// ✅ Full official name
{ "search_query": "Los Angeles Unified School District" }
```

## Best Practices for Outreach

```python
# Filter for high-quality contacts
quality_contacts = [
    c for c in contacts
    if c.get("emailVerified") == True
    and c.get("worksAtBuyer") == True
    and c.get("email", "").endswith("@lausd.net")  # match buyer domain
]
```

---

# Tool 4: `starbridge_opportunity_search`

**Purpose:** Search 114M+ procurement signals across board meetings, RFPs, purchases, and conferences. Returns AI-generated summaries and nested buyer data.

## Inputs

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search_query` | string | No | `""` | Natural language search. Supports OR: `"data center OR infrastructure"` |
| `types` | string[] | No | `["Meeting"]` | Opportunity types (see below). Auto-mapped to API enum values. |
| `buyer_types` | string[] | No | `[]` | Filter by buyer category (PascalCase) |
| `states` | string[] | No | `[]` | Two-letter state codes |
| `buyer_ids` | string[] | No | `[]` | Filter to specific buyer UUIDs. **v9.3: filters directly via `buyerFilter.terms` — no name resolution needed, fast and reliable.** |
| `ai_pruned` | int | No | `0` | Set to `1` to enable Starbridge AI pruning of low-relevance results. The platform UI sends this by default. |
| `content_search` | int | No | `0` | Set to `1` to enable full-text content search within documents (not just titles/metadata). The platform UI sends this by default. |
| `from_date_relative_period` | string | No | `""` | Posted date filter: `LastOneDay`, `LastThirtyDays`, `LastThreeMonths`, `LastSixMonths`, `LastYear`, `Past` |
| `until_date_relative_period` | string | No | `""` | Expiration date filter: `LastOneDay`, `LastThirtyDays`, `Future` |
| `purchase_amount_from` | int | No | — | Minimum purchase amount in dollars |
| `purchase_amount_to` | int | No | — | Maximum purchase amount in dollars |
| `relative_range` | string | No | `""` | ⚠️ Legacy — use `from_date_relative_period` instead |
| `date_from` / `date_to` | string | No | `""` | ⚠️ Legacy — likely ignored by API |
| `sort_field` | string | No | `"SearchRelevancy"` | Sort by: `SearchRelevancy`, `OpportunityFromDate`, `OpportunityUntilDate`, `OpportunityPurchaseAmount` (aliases `PostedDate`, `DueDate`, `Amount` auto-mapped) |
| `sort_direction` | string | No | `"DESC"` | `ASC` or `DESC` |
| `page_size` | int | No | `40` | Results per page |
| `page_number` | int | No | `1` | 1-indexed |

### Valid `types` Values

The tool accepts friendly names and auto-maps them to the API's internal enum:

| Input Value | API Enum | What It Searches |
|-------------|----------|------------------|
| `"Meeting"` | `BoardMeeting` | Board meetings and minutes |
| `"StrategicPlan"` or `"Strategic Plan"` | `StrategicPlan` | Strategic plans, roadmaps, multi-year plans |
| `"RFP"` | `Selling` | Requests for proposals |
| `"Purchase"` | `PurchaseOrder` | Purchase orders (amounts, no AI summaries) |
| `"Contract"` | `Contract` | Contracts (AI summaries, vendor names, amounts, dates) |

~~`"Conference"` is **NOT valid** — the API rejects it with 400 error.~~ Removed in v9.5.

You can use either the friendly name or the API enum directly.

## Outputs (v9.6)

```json
{
  "totalItems": 114261442,
  "pageNumber": 1,
  "pageSize": 40,
  "resultCount": 40,
  "uniqueBuyerIds": ["8d379568-...", "234978fa-...", ...],  // ← CHAIN THESE DOWNSTREAM
  "opportunities": [
    {
      "id": "18306511-b99c-4275-b4b8-c10c981d1fbf",
      "title": "Board Meeting - Technology Infrastructure Discussion",
      "summary": "This document outlines the objectives for IT modernization...",  // AI-generated, 500 chars max
      "type": "BoardMeeting",  // ⚠️ Note: different from input "Meeting"
      "status": "Future",      // v9.4: For StrategicPlans — null for most meetings
      "postedDate": "2025-08-15",
      "dueDate": "2026-02-16",    // Only for RFPs
      "untilDate": "2027-12-31",  // v9.4: End date for StrategicPlans
      "createdAt": "2025-04-10T20:34:37.846034Z",  // v9.6: When Starbridge indexed this record
      "purchaseAmount": 50000,     // Only for purchases

      "buyerId": "4592960f-...",
      "buyerName": "Florida Department of Health",
      "buyerType": "StateAgency",
      "buyerState": "FL",
      "buyerWebsite": "https://floridahealth.gov",
      "buyerTags": ["StateAgency"],
      "buyerLogoUrl": "https://storage.googleapis.com/starbridge-fe-static/logo/...",  // v9.4

      "parentBuyerId": "abc123-...",   // v9.6: Parent buyer UUID — chain to buyer_profile/contacts
      "parentBuyerName": "State of Florida",
      "parentBuyerType": "State",

      "documentType": "Board Meeting",
      "fileCount": 2,
      "files": [
        { "name": "Meeting Minutes.pdf", "url": "https://...", "contentType": "application/pdf" }
      ],

      // v9.6: Related records pre-linked to this opportunity (when present)
      "rfps": [                         // Only on opportunities with linked RFPs
        { "id": "...", "title": "...", "dueDate": "...", "status": "..." }
      ],
      "purchaseOrders": [               // Only on Purchase/Contract types
        { "id": "...", "title": "...", "purchaseAmount": 50000, "vendorName": "Acme Corp", "fromDate": "...", "untilDate": "..." }
      ]
    }
  ]
}
```

### v9.6 New Fields

| Field | Type | Description | Pipeline Use |
|-------|------|-------------|-------------|
| `createdAt` | ISO datetime | When Starbridge indexed the record (vs `postedDate` = when event happened) | Data freshness — recently indexed = more reliable |
| `parentBuyerId` | UUID | Parent buyer UUID (e.g. county for a city, state for a county) | Chain to `buyer_profile`/`buyer_contacts` for parent org |
| `rfps[]` | array | Related RFP records pre-linked to this opportunity | Cross-reference active procurement |
| `purchaseOrders[]` | array | Related purchase orders pre-linked | Cross-reference spend data |

`rfps[]` and `purchaseOrders[]` are only present when the API returns linked records. Most meetings won't have them. Purchase/Contract type results are most likely to have `purchaseOrders[]` populated.

## Gotchas

1. **⚠️ TYPE MAPPING:** Input `"Meeting"` → API `"BoardMeeting"`. Input `"RFP"` → `"Selling"`. Input `"Purchase"` → `"PurchaseOrder"`. Input `"Contract"` → `"Contract"`. Input `"StrategicPlan"` stays as-is. Output `type` field uses the API enum values. **`"Conference"` is NOT valid** — removed in v9.5.

2. **`StrategicPlan` is separate from `Meeting`.** Board meetings and strategic plans are different types. Use `["Meeting", "StrategicPlan"]` to search both, or `["StrategicPlan"]` alone for multi-year plans, roadmaps, and cybersecurity plans.

3. **114M+ records with no filters!** ALWAYS use at least one filter (types, states, search_query, or date range).

4. **AI summaries for meetings AND strategic plans.** RFPs and purchases have titles but usually no summary field.

5. **`dueDate` only for RFPs.** It's null for meetings and purchases.

6. **`purchaseAmount` only for purchases.** It's null for meetings and RFPs.

7. **Use `from_date_relative_period` for date filtering.** The legacy `relative_range` and `date_from`/`date_to` params may not work reliably. The v9 params (`from_date_relative_period`, `until_date_relative_period`) are placed correctly inside the API's `filters` object.

8. **Only 4 sort field values work:** `SearchRelevancy`, `OpportunityFromDate`, `OpportunityUntilDate`, `OpportunityPurchaseAmount`. Aliases like `PostedDate`, `DueDate`, `Amount` are auto-mapped. Use `OpportunityFromDate` when browsing without keywords.

9. **`uniqueBuyerIds` is your downstream key.** Feed these into `starbridge_buyer_contacts` to get decision-makers for matching opportunities.

10. **`buyer_ids` filter directly by ID (v9.3).** No more name resolution — buyer UUIDs are passed directly to `buyerFilter.terms` with `field:Id`. Fast and reliable. Max 20 IDs per request.

11. **`opportunity_search` is the ONLY tool that can resolve a domain to a buyerId.** Unlike all other tools (which use Name Contains on the buyer name field), opportunity_search does full-text search across 114M+ document contents. If a domain like `"riverhead.net"` appears anywhere in board meeting minutes, transcripts, or documents, it will match — and the results include `buyerId`, `buyerName`, and `buyerWebsite` for each hit. This makes it a viable **domain → buyer resolution bridge** for the pipeline. See "Domain → Buyer Resolution" in Common Workflows below for details.

12. **`ai_pruned` and `content_search` match platform behavior.** The Starbridge platform UI sends `aiPruned: true` and `contentSearch: true` by default. Set these to `1` to replicate platform-quality results. `content_search` searches inside document text (not just titles). `ai_pruned` filters out low-relevance matches.

## Examples

### Find RFPs for cybersecurity in Texas

```json
{
  "search_query": "cybersecurity OR information security",
  "types": ["RFP"],
  "states": ["TX"],
  "from_date_relative_period": "LastSixMonths",
  "sort_field": "OpportunityUntilDate",
  "sort_direction": "ASC",
  "page_size": 20
}
```

### Find strategic plans about cybersecurity in California

```json
{
  "search_query": "cybersecurity",
  "types": ["StrategicPlan"],
  "states": ["CA"],
  "content_search": 1,
  "ai_pruned": 1,
  "page_size": 10
}
```

### Search LAUSD meetings with platform-quality filtering

```json
{
  "search_query": "technology",
  "types": ["Meeting"],
  "buyer_ids": ["35617ceb-709a-45ef-af49-5c9707c3b164"],
  "ai_pruned": 1,
  "content_search": 1,
  "from_date_relative_period": "LastYear",
  "page_size": 10
}
```

### Find large purchase orders sorted by amount

```json
{
  "types": ["Purchase"],
  "states": ["TX"],
  "purchase_amount_from": 100000,
  "purchase_amount_to": 500000,
  "sort_field": "OpportunityPurchaseAmount",
  "sort_direction": "DESC",
  "page_size": 20
}
```

### Find contracts with vendor details

```json
{
  "search_query": "software license",
  "types": ["Contract"],
  "states": ["CA"],
  "from_date_relative_period": "LastYear",
  "page_size": 3
}
```

**Real response** (3 results — all Naval Information Warfare Center Pacific):
```json
{
  "totalItems": 3,
  "resultCount": 3,
  "typesResolved": ["Contract"],
  "opportunities": [
    {
      "id": "61d2d7bb-aa6a-4cc9-8a6c-6a7de69f8ca1",
      "type": "Contract",
      "title": "Order to AccessAgility LLC by Naval Information Warfare Center Pacific for FLYWAY SOFTWARE LICENSE",
      "summary": "FLYWAY SOFTWARE LICENSE",
      "status": "Future",
      "postedDate": "2025-08-15",
      "untilDate": "2026-09-14",
      "purchaseAmount": 44995,
      "buyerId": "278133d4-2260-4cb4-9cfe-2f8f0f7e5795",
      "buyerName": "Naval Information Warfare Center Pacific",
      "buyerType": "Federal",
      "buyerState": "CA",
      "highlights": {
        "title": [{"highlight": "...FLYWAY <em>SOFTWARE LICENSE</em>"}],
        "summary": [{"highlight": "FLYWAY <em>SOFTWARE LICENSE</em>"}]
      }
    },
    {
      "id": "4e5e7b5a-9184-4be6-9929-f9b1e5270026",
      "type": "Contract",
      "title": "Order to Accelera Solutions, Inc. by Naval Information Warfare Center Pacific for UNITY-INDUSTRY SOFTWARE LICENSE",
      "summary": "UNITY-INDUSTRY SOFTWARE LICENSE",
      "status": "Past",
      "postedDate": "2025-03-28",
      "untilDate": "2025-04-04",
      "purchaseAmount": 23475,
      "buyerName": "Naval Information Warfare Center Pacific",
      "buyerType": "Federal"
    },
    {
      "id": "f9d840ee-a531-4595-a54a-917e9f3ceca6",
      "type": "Contract",
      "title": "Order to FCN Inc. by Naval Information Warfare Center Pacific for METASPLOIT SINGE USER SOFTWARE LICENSE SUBSCRIPTION",
      "summary": "METASPLOIT SINGE USER SOFTWARE LICENSE SUBSCRIPTION",
      "status": "Past",
      "purchaseAmount": 15227,
      "buyerName": "Naval Information Warfare Center Pacific",
      "buyerType": "Federal"
    }
  ],
  "uniqueBuyerIds": ["278133d4-2260-4cb4-9cfe-2f8f0f7e5795"]
}
```

### Find RFPs due in the future (active solicitations)

```json
{
  "types": ["RFP"],
  "states": ["TX"],
  "until_date_relative_period": "Future",
  "sort_field": "OpportunityUntilDate",
  "sort_direction": "ASC",
  "page_size": 20
}
```

### Broad keyword search with OR operator and content search

```json
{
  "search_query": "data center OR cloud migration",
  "types": ["Meeting", "StrategicPlan"],
  "buyer_types": ["HigherEducation"],
  "content_search": 1,
  "ai_pruned": 1,
  "page_size": 3
}
```

**Real response** (3 results across 3 different institutions):
```json
{
  "totalItems": 3,
  "resultCount": 3,
  "typesResolved": ["BoardMeeting", "StrategicPlan"],
  "opportunities": [
    {
      "id": "3449f367-64e9-4bc2-a453-b3b33349e730",
      "type": "StrategicPlan",
      "title": "Georgia Highlands College Strategic Plan 2024-2027",
      "status": "Future",
      "summary": "The Information Technology Strategic Plan for Georgia Highlands College (GHC) outlines a technology roadmap aimed at optimizing IT resources to meet the future needs of faculty, staff, and students. Key areas of focus include diversifying technology platforms to reduce reliance on single vendors, optimizing software license usage to eliminate redundancies and reduce costs, and migrating on-premises services to multiple cloud vendors for scalability and enhanced security...",
      "untilDate": "2027-12-31",
      "buyerName": "Georgia Highlands College",
      "buyerType": "HigherEducation",
      "buyerState": "GA",
      "buyerLogoUrl": "https://storage.googleapis.com/starbridge-fe-static/logo/2c5f156f-...",
      "parentBuyerName": "University System Of Georgia",
      "highlights": {
        "content": [
          {"highlight": "3. Cloud Migration\n\n• Objective: Move on-premises services to multiple cloud vendors.\n• Actions:\n\no Assess workloads for cloud suitability.\no Develop a phased migration plan.\no Monitor costs and performance post-migration."},
          {"highlight": "Cloud platforms offer enhanced security features, including encryption, firewalls, and intrusion detection systems. Additionally, data centers are geographically dispersed, reducing the risk of localized disasters."}
        ]
      },
      "files": [{"name": "Georgia Highlands College Strategic Plan 2024-2027", "contentType": "application/pdf"}]
    },
    {
      "id": "c291963b-f1c1-4802-9362-4bc537dc9b09",
      "type": "BoardMeeting",
      "title": "Board of Trustees Special Meeting",
      "summary": "The meeting included a public comment session with no comments. The main action item was the consideration and approval of the Oracle Cloud Services Agreement.",
      "buyerName": "Peralta Community College System Office",
      "buyerType": "HigherEducation",
      "buyerState": "CA",
      "highlights": {
        "content": [
          {"highlight": "Phase I at a cost of $$ 1,437,631.95$ will consist of: * <b>Migration</b> to Oracle Database from Microsoft Sequel * <b>Migration</b> to Oracle <b>Cloud</b> Infrastructure"}
        ]
      }
    },
    {
      "id": "6c004a92-be85-481f-84f7-2a13b8dc51a6",
      "type": "BoardMeeting",
      "title": "Board Report",
      "summary": "The meeting included discussions on alternative revenue sources, state appropriations, and the impact of tax cuts on the University of Missouri system. ...The board also discussed data center operations and the Enterprise Resource Planning (ERP) project.",
      "buyerName": "University of Missouri-System Office",
      "buyerType": "HigherEducation",
      "buyerState": "MO",
      "highlights": {
        "content": [
          {"highlight": "we have decided to have a primary data center for administrative purposes here in Columbia and a secondary site to be located in Kansas City..."}
        ]
      }
    }
  ],
  "uniqueBuyerIds": ["132499ed-...", "b14cf809-...", "03b918b1-..."]
}
```

### Search a specific buyer's meetings and contracts together

```json
{
  "types": ["Meeting", "Contract"],
  "buyer_ids": ["c279ef27-a88d-4422-802d-ee6bf1e1e466"],
  "from_date_relative_period": "LastYear",
  "sort_field": "OpportunityFromDate",
  "sort_direction": "DESC",
  "page_size": 20
}
```

### Search with highlights (get document excerpts showing where terms match)

```json
{
  "search_query": "cybersecurity",
  "types": ["Meeting"],
  "states": ["CA"],
  "content_search": 1,
  "page_size": 10
}
```

Results will include `highlights.content` with `<b>` tags around matching terms, e.g.:
`"<b>cybersecurity</b> plan and incident response procedures"`

---

# Tool 5: `starbridge_buyer_chat`

**Purpose:** Ask AI-powered questions about a specific buyer. The AI has access to board meeting transcripts, contracts, contacts, budget info, and strategic plans.

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `buyer_id` | string | No* | Direct buyer UUID |
| `search_query` | string | No* | Buyer name to auto-resolve (⚠️ domain search does not work) |
| `question` | string | ✅ Yes | Question to ask about the buyer |

*One of `buyer_id` or `search_query` required.

## Outputs

```json
{
  "resolved_buyer_id": "35617ceb-...",
  "resolved_buyer_name": "Los Angeles Unified School District",
  "search_query_used": "Los Angeles Unified School District",
  "question": "Who is the CIO and what technology initiatives are they focused on?",
  "ai_response": "### Soheil Katal\n* **Title**: Chief Information Officer\n* **Email**: soheil.katal@lausd.net\n* **Phone**: +1-213-241-4906\n\nKey technology initiatives include:\n1. **IT Modernization** - Upgrading core infrastructure...\n2. **AI Integration** - Piloting AI tools in classrooms...",
  "chatId": "35617ceb-...",
  "messageId": "ef8cc968-..."
}
```

## Suggested Questions (These Work Well)

| Question Type | Example |
|---------------|---------|
| Key contacts | "Who are the key technology decision makers and their contact info?" |
| Budget | "What is their technology budget and major IT contracts?" |
| Priorities | "What are their strategic priorities for this fiscal year?" |
| Specific topics | "What recent board meeting discussions mention cybersecurity?" |
| AI adoption | "What is their AI adoption strategy?" |
| Vendor landscape | "Who are their top vendors and what do they spend on?" |
| Procurement | "What procurement challenges do they face?" |
| Process | "What is their procurement process and timeline?" |

## Gotchas

1. **Takes 30-90 seconds.** This endpoint uses SSE streaming. Complex questions take longer. Tested at ~72s for LAUSD.

2. **Each call costs Starbridge credits.** Don't spam the same buyer. Batch questions into one comprehensive ask.

3. **AI sometimes embeds contact info inline.** Parse the response carefully for emails/phones.

4. **Knowledge is scoped to Starbridge data.** The AI won't know things outside of government procurement, board meetings, and contracts.

5. **Sparse data = thin responses.** Large school districts and state agencies have rich data. Small cities may have little.

6. **This is NOT the global "Ask Starbridge" chat.** That uses Firestore. This is the buyer-specific REST endpoint.

## Best Practice: Batch Your Questions

Instead of:
```
Call 1: "Who is the CIO?"
Call 2: "What is their budget?"
Call 3: "What are their priorities?"
```

Do:
```
Call 1: "Who are the key technology decision makers, what is their technology budget, and what are their strategic priorities for this fiscal year?"
```

## Examples

### Ask about a buyer by UUID (fastest — use when you have the ID)

```json
{
  "buyer_id": "c279ef27-a88d-4422-802d-ee6bf1e1e466",
  "question": "Who are the key technology decision makers and their contact info?"
}
```

**Real response** (Dallas ISD — took ~42 seconds):
```json
{
  "resolved_buyer_id": "c279ef27-a88d-4422-802d-ee6bf1e1e466",
  "resolved_buyer_name": "",
  "search_query_used": null,
  "question": "Who are the key technology decision makers and their contact info?",
  "ai_response": "### No Verified Contacts Found\nMy search of the Starbridge-verified contact database did not yield any specific technology decision-makers for Dallas Independent School District at this time.\n\n### Next Steps\nWould you like me to search public web sources for this information? Please note that information found on the web may be less reliable or outdated compared to our verified database.",
  "chatId": "c279ef27-a88d-4422-802d-ee6bf1e1e466",
  "messageId": "e51cd769-ff76-43d4-a5c5-631e9ff8f1d4"
}
```

> **Note:** The AI may return "No Verified Contacts Found" even when `buyer_contacts` returns 121 contacts for the same buyer. The chat AI searches differently — it uses Starbridge's internal verified DB, not the contacts endpoint. For reliable contact data, always use `buyer_contacts` directly.

### Ask about a buyer by name (auto-resolves — use full official name)

```json
{
  "search_query": "Dallas Independent School District",
  "question": "What is their technology budget and what are their major IT contracts?"
}
```

### Ask about procurement strategy

```json
{
  "buyer_id": "35617ceb-709a-45ef-af49-5c9707c3b164",
  "question": "What is their procurement process, what cooperative purchasing vehicles do they use, and who are their top technology vendors?"
}
```

### Ask a comprehensive batched question (saves credits — combine multiple topics)

```json
{
  "buyer_id": "c279ef27-a88d-4422-802d-ee6bf1e1e466",
  "question": "Who is the CIO, what is their annual technology budget, what LMS and SIS platforms do they use, what are their top IT priorities for this fiscal year, and are there any upcoming technology-related RFPs or contract renewals?"
}
```

### Ask about AI and innovation

```json
{
  "search_query": "Coastal Bend College",
  "question": "What is their AI adoption strategy, are they piloting any AI tools, and what is their approach to educational technology innovation?"
}
```

### What NOT to pass as search_query

```json
// ❌ Domain — will resolve to wrong buyer or fail
{ "search_query": "lausd.org", "question": "..." }

// ✅ Full official name
{ "search_query": "Los Angeles Unified School District", "question": "..." }
```

---

# Tool 6: `starbridge_full_intel`

**Purpose:** Get EVERYTHING about a buyer in one call. Runs 4 API calls in parallel: profile, contacts, AI chat, and opportunities.

## Inputs

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search_query` | string | ✅ Yes | — | Buyer name to research (⚠️ domain search does not work — use full name) |
| `ai_question` | string | No | "What are their key priorities, recent technology initiatives, and procurement strategy?" | Question for AI |
| `contact_page_size` | int | No | `50` | Max contacts to retrieve |
| `include_opportunities` | bool | No | `true` | Also search recent opportunities? |
| `opportunity_types` | string[] | No | `["Meeting", "RFP"]` | Which types to search |
| `opportunity_query` | string | No | `""` | Keyword filter for opportunities |

## Outputs

```json
{
  "resolved_buyer_id": "35617ceb-...",
  "resolved_buyer_name": "Los Angeles Unified School District",
  "alternative_matches": [
    { "id": "abc123-...", "name": "LA County Office of Education" },
    { "id": "def456-...", "name": "LA Community College District" }
  ],
  
  "profile": { /* Full profile object — same as starbridge_buyer_profile */ },
  
  "contacts": {
    "totalContacts": 175,
    "contacts": [ /* Full contact objects with all v3.0 fields — same schema as starbridge_buyer_contacts:
      contactId, name, firstName, lastName, middleName, salutation, title, normalizedTitles,
      email, phone, linkedInUrl, worksAtBuyer, emailVerified, emailLastChecked,
      source, foiaRequestContact, metadataV2, createdAt, updatedAt */ ]
  },
  
  "ai_intel": "### Strategic Priorities\n1. Academic Excellence...\n\n### Key Contacts\n- Soheil Katal, CIO...",
  
  "opportunities": {
    "totalItems": 45,
    "opportunities": [
      {
        "title": "Board Meeting - Technology Update",
        "type": "BoardMeeting",
        "date": "2025-11-14",
        "dueDate": null,
        "amount": null,
        "summary": "Discussion of IT infrastructure modernization..."
      }
    ]
  }
}
```

## Gotchas

1. **Takes 15-45 seconds.** It's running 4+ API calls. The AI chat is the slowest leg.

2. **Check `alternative_matches`.** If `search_query` was ambiguous, the top match might be wrong.

3. **Sections can fail independently.** If AI chat errors, you'll get an error string in `ai_intel` but profile/contacts/opportunities still populate. The Starbridge SSE chat endpoint intermittently returns internal server errors — this is Starbridge-side and not fixable in our code.

4. **Credits:** The chat portion costs Starbridge credits. Profile/contacts/opportunities are generally free.

5. **Don't loop this for bulk research.** Use the individual tools instead. This is for deep-dive on a single account.

6. **Domain search does not work.** Use the full buyer name (e.g., `"Los Angeles Unified School District"` not `"lausd.org"`).

## Examples

### Basic full intel on a school district (all defaults)

```json
{
  "search_query": "Dallas Independent School District"
}
```

Returns: profile (83+ attributes), contacts (first 50), AI intel (priorities, tech, procurement), recent meetings and RFPs.

### Full intel with custom AI question

```json
{
  "search_query": "Los Angeles Unified School District",
  "ai_question": "Who is the CIO, what is their annual technology budget, and what cybersecurity initiatives are underway?"
}
```

### Full intel with contract and purchase opportunity focus

```json
{
  "search_query": "Coastal Bend College",
  "opportunity_types": ["Meeting", "Contract"],
  "contact_page_size": 5
}
```

**Real response** (Coastal Bend College — took ~21 seconds, truncated):
```json
{
  "resolved_buyer_id": "75689faf-e26e-4fcd-aca6-8556134549b3",
  "resolved_buyer_name": "Coastal Bend College",
  "alternative_matches": [
    {"id": "66d37dce-...", "name": "Coast Community College District Office"},
    {"id": "2263ae7b-...", "name": "California Community Colleges"},
    {"id": "f4f71b3e-...", "name": "Fort Bend Independent School District"}
  ],

  "profile": {
    "name": "Coastal Bend College",
    "type": "HigherEducation",
    "stateCode": "TX",
    "extraData": {
      "totalEnrollment": 3792,
      "lmsArray": ["Blackboard"],
      "sis": "EllucianColleague",
      "aiAdoptionScore": 31,
      "propensityToSpend": "OpenToSpend",
      "propensityToSpendScore": 73,
      "startupFriendlinessScore": 15,
      "higherEdEndowment": 2010000,
      "higherEdInstitutionType": "CommunityCollege",
      "higherEdLevelOfInstitution": "TwoYears",
      "higherEdControlOfInstitution": "Public"
    }
  },

  "contacts": {
    "totalContacts": 35,
    "contacts": [
      {
        "name": "Lazaro Barroso",
        "title": "Vice President of Student Affairs and Enrollment Management",
        "email": "lbarroso@coastalbend.edu",
        "phone": "+1-361-354-2532",
        "emailVerified": true
      },
      {
        "name": "Tara J. Boiles",
        "title": "Vice President of Finance & Business Operations/CFO",
        "email": "tjboiles@coastalbend.edu",
        "phone": "+1-361-354-2215",
        "emailVerified": true
      }
    ]
  },

  "ai_intel": "### Information Technology Leadership\n\nThe IT department is led by **Michael Rowlett**, Director of Information Technology and CISO.\n\n### Core Technology Priorities (2025–2030 Strategic Plan)\n- **Digital Resource Investment:** Expanding digital resources for online/hybrid learning\n- **Cybersecurity Modernization:** Staff/student training via Barracuda\n- **Obsolescence Replacement:** Replacing 15-year-old classroom machines\n- **Infrastructure Reliability:** Battery backups for power interruptions\n- **Enterprise Systems:** Implemented Strategic Planning Online (SPOL)",

  "opportunities": {
    "totalItems": 20,
    "opportunities": [
      {
        "type": "Contract",
        "title": "Respondus Inc. at Coastal Bend College",
        "date": "2025-08-01",
        "amount": 6140,
        "summary": "Fee agreement for Respondus 4 and LockDown Browser license renewal, Aug 2025–Jul 2026."
      },
      {
        "type": "Contract",
        "title": "Salesforce, Inc. at Coastal Bend College",
        "date": "2024-12-01",
        "amount": 92891,
        "summary": "Tableau Cloud services including Viewer, Premier Success Plan, Embedded Analytics, Dec 2024–Nov 2027."
      },
      {
        "type": "Contract",
        "title": "Ellucian Company LP at Coastal Bend College",
        "date": "2021-09-01",
        "amount": 1132572,
        "summary": "Managed Cloud Services renewal, Sep 2021–Aug 2026."
      },
      {
        "type": "Contract",
        "title": "Element451, Inc. at Coastal Bend College",
        "date": "2024-06-01",
        "amount": 60000,
        "summary": "Element451 CRM platform with AI & BoltBot, managed implementation."
      },
      {
        "type": "BoardMeeting",
        "title": "Coastal Bend College Special Meeting",
        "date": "2024-08-13",
        "amount": null,
        "summary": "Budget workshop for 2024-2025. Discussion of FLSA impacts on exempt employees."
      }
    ]
  }
}
```

> **Note:** `full_intel` returns ALL opportunity types matching the buyer — the `opportunity_types` filter controls which types are searched. The AI intel section identified the IT Director (Michael Rowlett) and extracted 5 strategic priorities from board meetings and the 2025-2030 strategic plan — data you'd have to piece together manually from multiple tool calls.

### Full intel with more contacts and no opportunities (faster)

```json
{
  "search_query": "Houston Independent School District",
  "contact_page_size": 100,
  "include_opportunities": false
}
```

### What NOT to pass as search_query

```json
// ❌ Domain — will resolve to wrong buyer or fail
{ "search_query": "houstonisd.org" }

// ❌ Abbreviation — may pick wrong buyer
{ "search_query": "HISD" }

// ✅ Full official name
{ "search_query": "Houston Independent School District" }
```

## Best For

- Account research before a sales call
- Building account dossiers
- Preparing for RFP responses
- Competitive intelligence on specific institutions

---

# Tool 7: `starbridge_bridges`

**Purpose:** Manage Starbridge Bridges — saved search workflows that combine opportunity/buyer data with AI-enriched columns.

## Inputs

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `action` | string | ✅ Yes | — | One of: `list`, `details`, `entries`, `metadata`, `totals` |
| `org_id` | string | No | Auto | Organization UUID (auto-discovered from /user/me) |
| `trigger_id` | string | Depends | — | Bridge UUID. Required for all actions except `list`. |
| `filter_types` | string | No | All types | Comma-separated for `list`: `"RFP,Meeting,Buyer"` |
| `page_size` | int | No | `25` | Results per page |
| `page_number` | int | No | `1` | 1-indexed |
| `entry_filters` | object[] | No | `[]` | Filters for `entries` action |
| `entry_sorts` | object[] | No | `[]` | Sorts for `entries` action |

## Actions

### `list` — Get All Bridges

```json
{ "action": "list" }
```

**Output:**
```json
{
  "orgId": "c5130505-...",
  "totalItems": 9,
  "bridges": [
    {
      "triggerId": "067d59ff-...",  // ← USE THIS FOR OTHER ACTIONS
      "name": "Active RFP Opportunities",
      "filterType": "RFP",          // Buyer, Meeting, RFP, Purchase, Signal, Contact, JobChange, Conference
      "type": "Play",               // Play = user-created, Original = template
      "status": "Open",
      "live": true,
      "entriesCount": 20,
      "updatedAt": "2026-02-04T04:03:07Z"
    }
  ]
}
```

### `details` — Bridge Configuration

```json
{ "action": "details", "trigger_id": "067d59ff-..." }
```

**Output:** Full bridge config including `triggerPhases` (columns with IDs, names, prompts, types, fieldFormats).

### `metadata` — Column Definitions

```json
{ "action": "metadata", "trigger_id": "067d59ff-..." }
```

**Output:** `dataAttributes` array with all 152 available columns, their types, and which are hidden/locked.

### `entries` — Data Rows

```json
{
  "action": "entries",
  "trigger_id": "067d59ff-...",
  "entry_filters": [
    { "phaseId": "df98db6b-...", "operator": "equals", "value": "New" }
  ],
  "entry_sorts": [
    { "phaseId": "c15de345-...", "direction": "DESC" }
  ]
}
```

**Filter operators:** `equals`, `notEquals`, `contains`, `notContains`, `greaterThan`, `lessThan`, `greaterThanOrEquals`, `lessThanOrEquals`, `isEmpty`, `isNotEmpty`, `in`, `notIn`

**Output:** Paginated entries with `phases` (keyed by phaseId) and `dataAttributes` (keyed like `op:rfp_title`).

### `totals` — Grouped Counts

```json
{
  "action": "totals",
  "trigger_id": "067d59ff-...",
  "entry_sorts": [{ "phaseId": "df98db6b-..." }]  // First phaseId = groupBy field
}
```

**Output:**
```json
{
  "total": 20,
  "totalAllBuyers": 20,
  "totalForBuyerList": 0,
  "groupsToTotals": { "New": 15, "In Progress": 5 }
}
```

## Gotchas

1. **Call `list` first** to get `triggerId` values. You need them for everything else.

2. **Call `metadata` or `details`** to get `phaseId` values. You need them for filtering/sorting entries.

3. **phaseIds are UUIDs, not names.** You can't filter by `"Status"` — you need `"df98db6b-61f0-4f2e-9533-911e991071a7"`.

4. **`filter_types` is comma-separated, not an array:** `"RFP,Meeting,Buyer"`.

5. **Data attribute keys have prefixes:** `op:rfp_title`, `op:buyer_name`, `op:buyer_state_code`.

## Typical Workflow

```
1. action=list                    → Get bridge triggerId
2. action=metadata (trigger_id)   → Get column phaseIds
3. action=entries (trigger_id, filters, sorts) → Get data
4. action=totals (trigger_id, groupBy phaseId) → Get summaries
```

---

# Tool 8: `starbridge_reference`

**Purpose:** Utility endpoints for system metadata, credit tracking, saved filters, and org info.

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string | ✅ Yes | One of 8 actions below |
| `org_id` | string | No | Auto-discovered. Provide explicitly if auto fails. |
| `user_id` | string | No | Only needed for `user_credits` action |

## Actions

### `buyer_types` — Valid Buyer Categories

```json
{ "action": "buyer_types" }
```

**Output:**
```json
{
  "buyer_types": {
    "result": [
      "StateAgency", "PoliceDepartment", "FireDepartment", "Library",
      "City", "County", "HigherEducation", "School", "SchoolDistrict",
      "SpecialDistrict", "State", "IndigenousGovernment", "Federal", "Other"
    ]
  }
}
```

### `credit_usage` — Org Credit Balance

```json
{ "action": "credit_usage" }
```

**Output:**
```json
{
  "orgId": "c5130505-...",
  "credits": {
    "creditsUsedSoFar": 228,
    "creditsUtilization": 0.15
  }
}
```

### `user_credits` — Individual User Credits

```json
{ "action": "user_credits", "user_id": "auth0|abc123..." }
```

### `buyer_filters` — Saved Buyer Lists

```json
{ "action": "buyer_filters" }
```

**Output:**
```json
{
  "orgId": "c5130505-...",
  "buyerFilters": [
    {
      "id": "filter-uuid",       // ← Use as buyerListId in searches
      "name": "Top 100 Higher Ed",
      "type": "Static",          // or "Dynamic"
      "status": "Completed",
      "buyerCount": 100
    }
  ]
}
```

### `rfp_proposals` — RFP Proposal Drafts

```json
{ "action": "rfp_proposals" }
```

### `tags` — Available Tags

```json
{ "action": "tags" }
```

### `integrations` — Connected Integrations

```json
{ "action": "integrations" }
```

**Output:** Connection status for Salesforce, HubSpot, Slack, Notion, Zendesk, Intercom, Sharepoint, Freshdesk.

### `user_me` — Bootstrap User/Org Info

```json
{ "action": "user_me" }
```

**Output:** User profile, `organizationId`, permissions, settings. **Call this first if you don't know orgId.**

## Gotchas

1. **`buyer_types` returns PascalCase.** Use these exact values in filters — `"HigherEducation"` not `"Higher Education"`.

2. **`credit_usage` is org-wide.** Use `user_credits` for individual tracking.

3. **`buyer_filters` only returns completed filters.** In-progress filters are excluded.

4. **`user_me` bootstraps everything.** If you don't have orgId or userId, call this first.

---

# Common Workflows

## 1. Quick Account Research

```
starbridge_buyer_search { "query": "Los Angeles Unified School District" }
  → Get buyerId from first result

starbridge_buyer_profile { "buyer_id": "..." }
  → Get firmographics, AI scores

starbridge_buyer_contacts { "buyer_id": "...", "page_size": 100 }
  → Get decision-makers with emails
```

## 2. Full Intel Dossier (One Call)

```
starbridge_full_intel { "search_query": "Los Angeles Unified School District" }
  → Get everything: profile + contacts + AI intel + opportunities
```

## 3. Opportunity → Contact Pipeline

```
starbridge_opportunity_search {
  "search_query": "cybersecurity",
  "types": ["RFP"],
  "states": ["TX"],
  "from_date_relative_period": "LastSixMonths"
}
  → Get uniqueBuyerIds from results

FOR EACH buyerId:
  starbridge_buyer_contacts { "buyer_id": "..." }
    → Get decision-makers for that opportunity
```

## 4. AI-Powered Prospecting

```
starbridge_buyer_search { "query": "community college", "states": ["CA"] }
  → Get list of target accounts
  
FOR EACH buyerId:
  starbridge_buyer_chat {
    "buyer_id": "...",
    "question": "Who is the CIO, what is their tech budget, and what are their top IT priorities?"
  }
    → Get AI intel
  
  starbridge_buyer_contacts { "buyer_id": "..." }
    → Get contact details for outreach
```

## 5. Domain → Buyer Resolution (Pipeline-Critical Workaround)

**Problem:** The positive reply pipeline receives a `domain` from Smartlead (e.g. `"riverhead.net"`), but every buyer-facing tool requires either a `buyerId` (UUID) or a `buyer name` (for Name Contains search). Domains return 0 results from `buyer_search`, `buyer_profile`, `buyer_contacts`, `buyer_chat`, and `full_intel`.

**Discovery:** `opportunity_search` is the ONE tool that can resolve a domain to a buyer. It does full-text content search across 114M+ documents (board meeting minutes, transcripts, PDFs). When a buyer's domain appears in document content — which is common for school districts and government agencies that reference their own website — the search matches, and the results include full buyer metadata.

**Tested on 2026-02-13 with `riverhead.net`:**

| Tool | Input | Result |
|---|---|---|
| `buyer_search` | `query: "riverhead.net"` | 0 results |
| `buyer_search` | `query: "https://riverhead.net"` | 0 results |
| `buyer_profile` | `search_query: "riverhead.net"` | No buyers found |
| `buyer_profile` | `search_query: "https://riverhead.net"` | No buyers found |
| `buyer_contacts` | `search_query: "riverhead.net"` | No buyers found |
| `buyer_contacts` | `search_query: "https://riverhead.net"` | No buyers found |
| `buyer_chat` | `search_query: "riverhead.net"` | No buyers found |
| `buyer_chat` | `search_query: "https://riverhead.net"` | No buyers found |
| `full_intel` | `search_query: "riverhead.net"` | No buyers found |
| `full_intel` | `search_query: "https://riverhead.net"` | No buyers found |
| **`opportunity_search`** | **`search_query: "riverhead.net"`** | **13 results** |
| **`opportunity_search`** | **`search_query: "https://riverhead.net"`** | **40 results** |

**What opportunity_search returned:**
- `buyerId: "bf7105f9-7827-46b6-a3f4-b8a0ee9ebd31"`
- `buyerName: "Riverhead Central School District"`
- `buyerWebsite: "https://riverhead.net"`
- `buyerType: "SchoolDistrict"`
- `buyerState: "NY"`

The domain matched because `riverhead.net` appeared in board meeting document content — as URLs in budget presentations, email addresses (e.g. `boe@g.riverhead.net`), and references to the district website.

**Resolution pattern:**

```
Step 1: opportunity_search({ search_query: domain })
  → Extract buyerId, buyerName from first result

Step 2: Use buyerId directly with any downstream tool:
  → buyer_profile({ buyer_id: "bf7105f9-..." })
  → buyer_contacts({ buyer_id: "bf7105f9-..." })
  → buyer_chat({ buyer_id: "bf7105f9-...", question: "..." })
  → opportunity_search({ buyer_ids: ["bf7105f9-..."] })  // scoped search
```

**Limitations:**
- Only works if the domain appears somewhere in Starbridge's 114M+ document corpus
- May return results from multiple buyers (e.g. neighboring districts referencing each other's websites) — need to pick the most frequent `buyerId` or the one where `buyerWebsite` matches
- `"https://riverhead.net"` returned more results (40) than bare `"riverhead.net"` (13) — the full URL matches more document references
- Not tested at scale — unknown what percentage of SLED buyer domains appear in document content
- Slower path than direct name search since opportunity_search returns full document data

**Pipeline implication:** This means the Datagen agent could implement a two-phase resolution strategy:
1. **Fast path:** If `company_name` is available from Smartlead webhook → use `buyer_search` directly (reliable, sub-second)
2. **Fallback path:** If only `domain` is available → use `opportunity_search` as a domain resolver, extract `buyerId`/`buyerName`, then proceed

Both paths converge on a `buyerId` that feeds all downstream tools.

## 6. Bridge Analytics

```
starbridge_bridges { "action": "list" }
  → Get available triggerId values

starbridge_bridges { "action": "metadata", "trigger_id": "..." }
  → Get column phaseIds

starbridge_bridges {
  "action": "entries",
  "trigger_id": "...",
  "entry_filters": [{ "phaseId": "...", "operator": "equals", "value": "New" }]
}
  → Get filtered data rows

starbridge_bridges {
  "action": "totals",
  "trigger_id": "...",
  "entry_sorts": [{ "phaseId": "..." }]
}
  → Get grouped counts
```

---

# API Endpoints

**Sync (wait for response):**
```
POST https://api.datagen.dev/apps/{uuid}
```

**Async (returns run_uuid immediately):**
```
POST https://api.datagen.dev/apps/{uuid}/async
```

**Check async status:**
```
GET https://api.datagen.dev/apps/run/{run_uuid}/status
```

**Auth header:**
```
x-api-key: YOUR_DATAGEN_API_KEY
```

---

# Error Handling

## Wrong Buyer Match

**Problem:** Auto-resolution picked the wrong buyer.

**Solution:** Check `resolved_buyer_name` or `alternative_matches`. If wrong, use explicit `buyer_id` or a more specific `search_query`. Use the full official buyer name — **domain search does not work** on buyer_search, buyer_profile, buyer_contacts, buyer_chat, or full_intel (they all use Name Contains matching).

**Domain-only workaround:** If you only have a domain and no buyer name, use `opportunity_search` with the domain as `search_query`. It does full-text content search and can resolve domains that appear in board meeting documents. Extract `buyerId` and `buyerName` from the results, then use those with the other tools. See "Domain → Buyer Resolution" in Common Workflows for the full pattern and test data.

## Empty Contacts

**Problem:** `contacts` array is empty.

**Solution:** Some small buyers have no contacts in Starbridge. Try AI chat instead — it may have intel from board meeting transcripts.

## AI Chat Timeout

**Problem:** `starbridge_buyer_chat` or `starbridge_full_intel` times out.

**Solution:** Use async endpoint. AI responses can take 30+ seconds for complex questions.

## Credit Errors

**Problem:** Credit limit reached.

**Solution:** Check `starbridge_reference { "action": "credit_usage" }` before running AI chat. Profile/contacts/search are generally free; AI chat costs credits.

## AI Chat SSE Failures

**Problem:** `starbridge_buyer_chat` or `starbridge_full_intel` returns an internal server error in the AI response.

**Solution:** This is a Starbridge-side SSE endpoint issue — intermittent and not fixable in our code. Retry after a minute. When using `full_intel`, the other sections (profile, contacts, opportunities) will still populate even if AI chat fails.

## Bridge Entry Filters Not Working

**Problem:** Filters return no results.

**Solution:** You need the exact `phaseId` UUID from `metadata` or `details`. Column names don't work. Also check operator — `equals` is case-sensitive.

## Opportunity Search Type Errors

**Problem:** `opportunity_search` returns 400 Bad Request.

**Solution:** The Starbridge API requires specific enum values for opportunity types: `BoardMeeting` (not `Meeting`), `Selling` (not `RFP`), `PurchaseOrder` (not `Purchase`), `StrategicPlan` (separate from `BoardMeeting`). The tool auto-maps friendly names, but if you see this error, check that the type mapping is working. The `typesResolved` field in the output shows what was actually sent.

## Buyer ID Filtering

**v9.3 change:** `buyer_ids` now filter directly via `buyerFilter.terms` with `{"field": "Id", "value": [...], "operation": "Any"}`. This replaced the old approach of resolving UUIDs to names and injecting them into the query string. Direct ID filtering is faster (no extra API calls) and more reliable (no name-matching ambiguity).

---

# Additional API Intelligence (From Network Traffic)

## Discovered Endpoint: Feed API

```
GET /organization/{orgId}/feed/item/v3?pageNumber=1&pageSize=25&extendedPagination=false
```

The Feed API surfaces per-org feed items with filters like `buyerId` and `relativeDatePeriodFrom`. It's separate from opportunity search — this is the home dashboard feed. Not yet wrapped in a Datagen tool.

**Observed parameters:**
- `buyerId` — filter feed items to a specific buyer (UUID)
- `filterType` — comma-separated types: `RFP,Purchase,Meeting,Signal,Conference`
- `relativeDatePeriodFrom` — date filter (e.g., `LastSixMonths`)
- `status` — filter by status (e.g., `New`)
- `subscribed` — boolean, filter subscribed items
- `extendedPagination` — `false` for standard pagination
- `pageNumber`, `pageSize` — standard pagination

**Note:** Both test curls returned 0 results, so this endpoint may require specific Bridge/subscription setup to populate.

## Discovered: Organization ID

The Starbridge org ID observed in network traffic: `7c6f52eb-0453-4cde-8dba-2ff77785b71d`

This is used in org-scoped endpoints like `/organization/{orgId}/feed/item/v3`. The Datagen tools auto-discover this via `/user/me`, so you rarely need it directly.

## API Pattern: buyerFilter.terms

The Starbridge API uses a consistent `buyerFilter.terms` array pattern for filtering. Each term has:
```json
{
  "field": "Id" | "Type" | "StateCode" | "Name",
  "value": ["value1", "value2"],
  "operation": "Any"
}
```

This is how opportunity_search filters by buyer type, state, and (as of v9.3) direct buyer ID. Multiple terms in the array are AND-ed together.

## API Pattern: filters Object Structure

From the curls, the `/opportunity/v3` body uses a `filters` object that contains **everything** — not just traditional filters but also behavioral flags:

```json
{
  "filters": {
    "opportunityTypes": ["BoardMeeting", "StrategicPlan"],
    "aiPruned": true,
    "contentSearch": true,
    "fromDateRelativePeriod": "LastSixMonths",
    "buyerFilter": {
      "terms": [{"field": "Id", "value": ["..."], "operation": "Any"}]
    }
  }
}
```

**v9.4 fix:** `aiPruned` and `contentSearch` must be **inside** the `filters` object, not at the top level of the body. The tool now does this correctly.

## Response Fields by Opportunity Type

| Field | BoardMeeting | StrategicPlan | Selling (RFP) | PurchaseOrder | Contract |
|-------|-------------|---------------|---------------|---------------|----------|
| `summary` | Yes (AI-generated) | Yes (AI-generated) | Rare | Rare | Yes (AI-generated, includes vendor names) |
| `status` | null | "Future" etc. | "Available" etc. | "Active" etc. | "Past" / "Active" etc. |
| `untilDate` | null | End date (e.g., "2027-12-31") | Due date | Expiration | Expiration |
| `purchaseAmount` | null | null | null | Dollar amount | Dollar amount |
| `buyerLogoUrl` | Yes | Yes | Yes | Yes | Yes |
| `files[].contentType` | "application/pdf" | "application/pdf" | varies | varies | varies |
| `files[].sourceUrl` | Original source URL | Original source URL | — | — | — |

**NOTE:** `Conference` is NOT a valid API type — removed in v9.5 (returns 400 error).

---

# Summary Table

| Tool | Input Shortcut | Returns | Credits |
|------|----------------|---------|---------|
| `starbridge_buyer_search` | `query` | buyerIds, names, types | Free |
| `starbridge_buyer_profile` | `buyer_id` OR `search_query` | 83+ attributes, AI scores | Free |
| `starbridge_buyer_contacts` | `buyer_id` OR `search_query` | Contacts with verified emails | Free |
| `starbridge_opportunity_search` | `search_query`, filters | 114M+ opps, AI summaries, strategic plans | Free |
| `starbridge_buyer_chat` | `buyer_id` OR `search_query` + `question` | AI-generated intel | **Costs credits** |
| `starbridge_full_intel` | `search_query` | Everything combined | **Costs credits** (chat portion) |
| `starbridge_bridges` | `action` + `trigger_id` | Bridge data/config | Free |
| `starbridge_reference` | `action` | System metadata | Free |
