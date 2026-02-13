# Clay MCP Inputs Reference

Complete reference of all inputs across all Clay MCP endpoints.

---

## 1. `find-and-enrich-company`

Single company lookup by domain or LinkedIn URL.

```python
companyIdentifier: str     # REQUIRED - Domain ("stripe.com") or LinkedIn URL

companyDataPoints: [       # OPTIONAL - Enrichments to add
  {"type": "Headcount Growth"},
  {"type": "Recent News"},
  {"type": "Investors"},
  {"type": "Company Competitors"},
  {"type": "Company Customers"},
  {"type": "Tech Stack"},
  {"type": "Website Traffic"},
  {"type": "Open Jobs"},
  {"type": "Revenue Model"},
  {"type": "Annual Revenue"},
  {"type": "Latest Funding"},
  {"type": "Custom", "customDataPoint": "any research question"}
]
```

---

## 2. `find-and-enrich-contacts-at-company`

Find contacts at a company with optional filters.

```python
companyIdentifier: str     # REQUIRED - Domain or LinkedIn URL

contactFilters: {          # OPTIONAL - All filters below
  # TITLE FILTERS
  "job_title_keywords": ["VP Finance"],           # Include titles (OR logic within array)
  "job_title_exclude_keywords": ["Intern"],       # Exclude titles

  # PROFILE CONTENT FILTERS
  "headline_keywords": ["AI", "ML"],              # LinkedIn headline search
  "about_keywords": ["startup founder"],          # About section search
  "profile_keywords": ["python"],                 # UNDOCUMENTED - whole profile search

  # CREDENTIALS & BACKGROUND
  "certification_keywords": ["AWS", "CPA"],       # Certifications
  "languages": ["Spanish"],                       # Profile languages
  "school_names": ["Stanford", "MIT"],            # Schools attended

  # TENURE FILTERS
  "current_role_min_months_since_start_date": 12, # Tenured employees (min months in role)
  "current_role_max_months_since_start_date": 3,  # New hires (max months in role)

  # LOCATION FILTERS
  "locations": ["California", "United States"],   # Include locations
  "locations_exclude": ["India", "Philippines"]   # Exclude locations
}

dataPoints: {              # OPTIONAL - Enrichments for contacts AND company
  "contactDataPoints": [
    {"type": "Email"},
    {"type": "Summarize Work History"},
    {"type": "Find Thought Leadership"},
    {"type": "Custom", "customDataPoint": "any research question"}
  ],
  "companyDataPoints": [
    # Same types as find-and-enrich-company
    {"type": "Tech Stack"},
    {"type": "Open Jobs"},
    # etc.
  ]
}
```

### Filter Logic Notes

- Multiple filters combine with **AND**
- Values within arrays combine with **OR**
- WRONG: `["VP", "Finance"]` → matches ALL VPs OR ALL Finance people
- RIGHT: `["VP Finance", "VP of Finance"]` → matches VP Finance titles only

---

## 3. `find-and-enrich-list-of-contacts`

Look up specific named people. **TRUE BATCH** - max 20 per call.

```python
contactIdentifiers: [      # REQUIRED - Array of contacts (MAX 20)
  {
    "contactName": "Dario Amodei",           # Full name
    "companyIdentifier": "anthropic.com"     # Domain or LinkedIn URL
  },
  {
    "contactName": "Sam Altman",
    "companyIdentifier": "openai.com"
  }
  # ... up to 20 total
]

dataPoints: {              # OPTIONAL - Same structure as above
  "contactDataPoints": [
    {"type": "Email"},
    {"type": "Summarize Work History"},
    {"type": "Find Thought Leadership"},
    {"type": "Custom", "customDataPoint": "..."}
  ],
  "companyDataPoints": [
    {"type": "Tech Stack"},
    {"type": "Latest Funding"},
    # etc.
  ]
}
```

### Batch Limits (Confirmed Jan 2026)

- **Max 20 contacts per call** - 21+ returns "Internal error"
- Returns company profiles for ALL matched contacts' employers
- Can be used as batch company lookup trick (see SKILL.md)

---

## 4. `add-company-data-points`

Add enrichments to companies in an existing search.

```python
searchId: str              # REQUIRED - From previous search ("cgas-search-id_...")

dataPoints: [              # REQUIRED - Company enrichment types
  {"type": "Headcount Growth"},
  {"type": "Recent News"},
  {"type": "Investors"},
  {"type": "Company Competitors"},
  {"type": "Company Customers"},
  {"type": "Tech Stack"},
  {"type": "Website Traffic"},
  {"type": "Open Jobs"},
  {"type": "Revenue Model"},
  {"type": "Annual Revenue"},
  {"type": "Latest Funding"},
  {"type": "Custom", "customDataPoint": "any research question"}
]
```

---

## 5. `add-contact-data-points`

Add enrichments to contacts in an existing search.

```python
searchId: str              # REQUIRED - From previous search

dataPoints: [              # REQUIRED - Contact enrichment types
  {"type": "Email"},
  {"type": "Summarize Work History"},
  {"type": "Find Thought Leadership"},
  {"type": "Custom", "customDataPoint": "any research question"}
]
```

---

## 6. `get-existing-search`

Retrieve previous search results (FREE - no credits).

```python
searchId: str              # REQUIRED - From previous search
```

---

## 7. `get-credits-available`

Check workspace credits (FREE - no credits).

```python
# No parameters

# Returns:
{
  "hasWorkspaceCredits": bool,
  "hasPlatformCredits": bool
}
```

---

## 8. `track-event`

Track analytics events. Generally not needed for user workflows.

```python
eventName: str             # REQUIRED - Event name
properties: {}             # OPTIONAL - Any metadata object
```

---

## Summary Table

| Endpoint | Required Params | Optional Params |
|----------|-----------------|-----------------|
| `find-and-enrich-company` | companyIdentifier | companyDataPoints |
| `find-and-enrich-contacts-at-company` | companyIdentifier | contactFilters, dataPoints |
| `find-and-enrich-list-of-contacts` | contactIdentifiers | dataPoints |
| `add-company-data-points` | searchId, dataPoints | — |
| `add-contact-data-points` | searchId, dataPoints | — |
| `get-existing-search` | searchId | — |
| `get-credits-available` | — | — |
| `track-event` | eventName | properties |

---

## All Enrichment Types

### Company Enrichments

| Type | Provider | Est. Credits |
|------|----------|--------------|
| Headcount Growth | LinkedIn | ~1-2 |
| Recent News | Claygent | ~3-5 |
| Investors | Claygent | ~2-4 |
| Company Competitors | Claygent | ~2-4 |
| Company Customers | Claygent | ~2-4 |
| Tech Stack | BuiltWith | ~2-3 |
| Website Traffic | Semrush | ~2-3 |
| Open Jobs | LinkedIn/PredictLeads | ~2-3 |
| Revenue Model | Claygent | ~3-5 |
| Annual Revenue | Various | ~1-2 |
| Latest Funding | PredictLeads | ~1-2 |
| Custom | Claygent | ~3-5 |

### Contact Enrichments

| Type | Provider | Est. Credits |
|------|----------|--------------|
| Email | Waterfall | ~2-5 |
| Summarize Work History | Claygent | ~2-3 |
| Find Thought Leadership | Claygent | ~2-3 |
| Custom | Claygent | ~3-5 |

**Note:** Phone is NOT in the standard enum—use Custom type for phone lookups.

---

## Custom Data Points

For any research question not covered by standard types:

```python
# New schema (preferred):
{"type": "Custom", "dataPointName": "Recent Blog Posts", "dataPointDescription": "Find blog posts from 2024-2025"}

# Old schema (still works):
{"type": "Custom", "customDataPoint": "recent blog posts from 2024-2025"}
```
