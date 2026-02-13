# Data Schemas Reference

Complete JSON schemas, field trust levels, and enrichment value formats for Clay MCP responses.

---

## Table of Contents
- [Top-Level Response Structure](#top-level-response-structure)
- [Company Object Schema](#company-object-schema)
- [Contact Object Schema](#contact-object-schema)
- [Enrichment Value Schemas](#enrichment-value-schemas)
- [Enrichment States](#enrichment-states)
- [Location Format Inconsistency](#location-format-inconsistency)

---

## Top-Level Response Structure

Every Clay search returns:

```json
{
  "searchId": "cgas-search-id_abc123...",
  "companies": { "<domain>": { /* company object */ } },
  "contacts": [ /* contact objects */ ],
  "contactEnrichmentMeta": [ /* enrichment type metadata */ ],
  "companyEnrichmentMeta": [ /* enrichment type metadata */ ],
  "workspaceBusinessContext": {
    "companyDescription": "What user's company does",
    "idealCustomerProfile": "ICP: industries, company size, characteristics",
    "idealBuyerPersonas": "Target titles, pain points, responsibilities",
    "outboundEmailInstructions": "Email tone, structure, CTA guidelines"
  },
  "timestampMs": 1769556353613
}
```

---

## Company Object Schema

```json
{
  "name": "Anthropic",
  "domain": "anthropic.com",
  "url": "https://www.linkedin.com/company/anthropicresearch",
  "website": "https://www.anthropic.com",
  "industry": "Research Services",
  "type": "Privately Held",
  "size": "501-1,000 employees",
  "employee_count": 3571,
  "country": "US",
  "locality": "San Francisco, California",
  "description": "Anthropic is an AI safety company...",
  "logo_url": "https://media.licdn.com/...",
  "annual_revenue": "200M-500M",
  "total_funding_amount_range_usd": "$250M+",
  "locations": [
    {
      "country": "US",
      "city": "San Francisco",
      "geographic_area": "California",
      "postal_code": "94103",
      "line1": "548 Market St",
      "is_hq": true,
      "latitude": 37.789,
      "longitude": -122.401
    }
  ],
  "entityId": "anthropic.com",
  "entityType": "company",
  "enrichments": { "<uuid>": { /* enrichment object */ } }
}
```

### Company Field Trust Levels

| Field | Trust | Notes |
|-------|-------|-------|
| `employee_count` | **HIGH** | Actual count—**USE THIS** |
| `size` | **LOW** | Stale LinkedIn category—**IGNORE** |
| `annual_revenue` | MEDIUM | Range estimate |
| `total_funding_amount_range_usd` | MEDIUM | Range from funding DBs |
| `locality` | HIGH | City, State format |
| `industry` | MEDIUM | LinkedIn classification |
| `domain` | HIGH | Primary domain |
| `url` | HIGH | LinkedIn company URL |

---

## Contact Object Schema

```json
{
  "name": "Dario Amodei",
  "profile_id": "dario-amodei-123456",
  "url": "https://www.linkedin.com/in/dario-amodei-123456",
  "latest_experience_company": "Anthropic",
  "latest_experience_title": "CEO",
  "latest_experience_start_date": "2021-01",
  "location_name": "San Francisco Bay Area",
  "domain": "anthropic.com",
  "entityId": "dario-amodei-123456",
  "entityType": "contact",
  "enrichments": {}
}
```

### Contact Field Trust Levels

| Field | Trust | Notes |
|-------|-------|-------|
| `name` | HIGH | Full name |
| `profile_id` | HIGH | Unique LinkedIn ID—**use for deduplication** |
| `url` | HIGH | May be null for private profiles |
| `latest_experience_company` | **CRITICAL** | **CHECK THIS for employee filtering** |
| `latest_experience_title` | MEDIUM | Format varies wildly |
| `latest_experience_start_date` | HIGH | YYYY-MM format |
| `location_name` | LOW | Format varies significantly |
| `domain` | HIGH | Current employer domain |

---

## Enrichment Value Schemas

### Headcount Growth (Stringified JSON)

```json
{
  "employee_count": 3571,
  "percent_employee_growth_over_last_1_month": 7.8,
  "employee_count_1_month_ago": 3312,
  "percent_employee_growth_over_last_3_months": 26.85,
  "employee_count_3_months_ago": 2815,
  "percent_employee_growth_over_last_6_months": 69.55,
  "employee_count_6_months_ago": 2106,
  "percent_employee_growth_over_last_9_months": 131.59,
  "employee_count_9_months_ago": 1542,
  "percent_employee_growth_over_last_12_months": 182.54,
  "employee_count_12_months_ago": 1264,
  "percent_employee_growth_over_last_24_months": 990.52,
  "employee_count_24_months_ago": 327,
  "percent_employee_growth_over_last_36_months": 4470.58,
  "employee_count_36_months_ago": 78,
  "percent_employee_growth_over_last_48_months": 10617.24,
  "employee_count_48_months_ago": 33
}
```

### Open Jobs (Stringified JSON)

```json
{
  "jobs": [
    {
      "company_name": "Anthropic",
      "company_id": 69007278,
      "title": "Staff Database Reliability Engineer",
      "normalized_title": "Reliability Engineer",
      "description": "<html content>",
      "location": "San Francisco Bay Area",
      "salary_min": 220800,
      "salary_max": 272700,
      "salary_currency": "USD",
      "salary_unit": "YEAR",
      "seniority": "Entry level",
      "functions": ["Engineering", "Information Technology"],
      "employment_type": "Full-time",
      "url": "https://linkedin.com/jobs/view/...",
      "application_url": "https://jobs.ashbyhq.com/...",
      "posted_at": "2025-12-30T11:30:48",
      "closed_at": "2026-02-19T09:27:07"
    }
  ],
  "count": 10
}
```

### Website Traffic

```json
{
  "value": "573,485,401 monthly visitors",
  "metadata": { "provider": "Semrush" }
}
```

### Tech Stack

```json
{
  "technologies": [
    { "name": "React", "category": "JavaScript Frameworks" },
    { "name": "AWS", "category": "Cloud Hosting" }
  ]
}
```

### Latest Funding

```json
{
  "round": "Series E",
  "amount": 4000000000,
  "currency": "USD",
  "date": "2025-01-15",
  "investors": ["Lightspeed Venture Partners", "Spark Capital", "Google"]
}
```

### Claygent Enrichments (Recent News, Revenue Model, Custom)

Returns markdown-formatted text:

```markdown
#### Key Results
- Company announced $4B funding round (Jan 2025)
- Launched Claude 3.5 model family
- Expanded enterprise partnerships

#### Research Summary
Anthropic has been actively expanding...

#### Sources
- https://techcrunch.com/...
```

---

## Enrichment States

| State | Meaning | Action |
|-------|---------|--------|
| `complete` | Data ready | Parse `value` field |
| `in-progress` | Still processing | Wait 30s, call `get-existing-search` |
| `failed` | Lookup failed | Check error, may retry |
| `not_found` | No data available | Accept as null |

### Waiting for In-Progress Enrichments

```python
import time

def wait_for_enrichments(search_id, max_attempts=6):
    for attempt in range(max_attempts):
        result = get_existing_search(search_id)
        
        all_complete = True
        for company in result['companies'].values():
            for enrichment in company.get('enrichments', {}).values():
                if enrichment.get('state') == 'in-progress':
                    all_complete = False
                    break
        
        if all_complete:
            return result
        
        time.sleep(30)
    
    return result  # Return what we have
```

---

## Location Format Inconsistency

**Problem:** Same physical location appears in many formats.

| Actual Location | Possible Formats |
|-----------------|------------------|
| San Francisco | "San Francisco, CA" |
| | "San Francisco, California" |
| | "San Francisco, California, United States" |
| | "San Francisco Bay Area" |
| | "SF Bay Area" |
| | "Greater San Francisco Area" |

**Solution—Use fuzzy matching:**

```python
def matches_location(contact_location, target):
    if not contact_location:
        return False
    contact_lower = contact_location.lower()
    target_lower = target.lower()
    return target_lower in contact_lower or contact_lower in target_lower
```

---

## Tool Results File Format

When responses exceed token limits, data is saved in wrapped format:

```json
[{"type": "text", "text": "{...actual JSON data...}"}]
```

**Parsing code:**

```python
import json

def parse_clay_response(filepath):
    """Parse Clay data from tool results file."""
    with open(filepath) as f:
        raw = json.load(f)
    
    # Unwrap if needed
    if isinstance(raw, list) and raw and 'text' in raw[0]:
        return json.loads(raw[0]['text'])
    elif isinstance(raw, dict) and 'text' in raw:
        return json.loads(raw['text'])
    return raw
```
