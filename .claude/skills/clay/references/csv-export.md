# CSV Export Reference

Complete guide for the growing CSV approach, field reference, header customization, and export patterns.

---

## Table of Contents
- [Growing CSV Approach](#growing-csv-approach)
- [When to Offer CSV Export](#when-to-offer-csv-export)
- [Complete Field Reference](#complete-field-reference)
- [Header Customization Flow](#header-customization-flow)
- [Export Schemas](#export-schemas)
- [Append-Mode Export Functions](#append-mode-export-functions)
- [Resting Point Prompt Template](#resting-point-prompt-template)
- [End-of-Session Checklist](#end-of-session-checklist)
- [Full Export Script](#full-export-script)

---

## Growing CSV Approach

CSVs are NOT exported after every single Clay operation (too noisy).
CSVs are NOT exported after N operations (too rigid).

**Instead, offer CSV append at NATURAL RESTING POINTS:**
- After completing a multi-call research loop
- Before asking the user for next steps
- When switching from one company/task to another
- At session end (MANDATORY)

**CSVs GROW across the session—new rows are appended, not overwritten.**

```
Session start:
  clay_companies.csv → (empty)
  clay_contacts.csv → (empty)
  clay_jobs.csv → (empty)

After first batch:
  clay_companies.csv → 5 rows
  clay_contacts.csv → 47 rows
  clay_jobs.csv → 23 rows

After second batch (APPENDED):
  clay_companies.csv → 8 rows (+3 new)
  clay_contacts.csv → 89 rows (+42 new)
  clay_jobs.csv → 45 rows (+22 new)
```

**File naming convention:**
- `clay_companies.csv` (single file, grows)
- `clay_contacts.csv` (single file, grows)
- `clay_jobs.csv` (single file, grows)
- `clay_enrichments.csv` (single file, grows)

---

## When to Offer CSV Export

| Situation | Trigger? | Example |
|-----------|----------|---------|
| Completed multi-company lookup | ✅ YES | "Looked up 5 companies—append to CSV?" |
| Completed contact search + enrichments | ✅ YES | "Found 47 contacts with emails—append to CSV?" |
| Before asking "What's next?" | ✅ YES | "Before we continue, want to save this batch?" |
| After single company lookup | ❌ NO | Too granular |
| After each enrichment call | ❌ NO | Too noisy |
| User explicitly asks | ✅ YES | Always honor explicit requests |
| Session end | ✅ MANDATORY | Always offer final export |

---

## Complete Field Reference

### Company Fields (18 available)

```
CORE FIELDS (always recommended):
  name                    - Company name
  domain                  - Primary domain
  linkedin_url            - LinkedIn company URL
  website                 - Official website
  employee_count          - Actual headcount (USE THIS, not 'size')

CLASSIFICATION:
  industry                - LinkedIn industry category
  type                    - Company type (Privately Held, Public, etc.)
  size                    - LinkedIn size bucket (STALE - prefer employee_count)

LOCATION:
  country                 - Country code (US, UK, etc.)
  locality                - City, State format
  hq_address              - Full HQ address (from locations array)
  hq_latitude             - HQ latitude
  hq_longitude            - HQ longitude

FINANCIALS:
  annual_revenue          - Revenue range
  total_funding           - Total funding range (e.g., "$250M+")

ENRICHMENT SUMMARIES:
  headcount_growth_12mo   - % growth over 12 months (from Headcount Growth)
  website_traffic         - Monthly visitors (from Website Traffic)
  open_jobs_count         - Number of open positions (from Open Jobs)

OTHER:
  description             - Company description (truncated to 500 chars)
  logo_url                - Logo image URL
```

### Contact Fields (12 available)

```
CORE FIELDS (always recommended):
  name                    - Full name
  title                   - Current job title
  company                 - Current employer name
  domain                  - Current employer domain
  linkedin_url            - LinkedIn profile URL

EMPLOYMENT DETAILS:
  start_date              - Role start date (YYYY-MM)
  location                - Location (format varies)
  profile_id              - LinkedIn profile ID (use for dedup)
  is_current_employee     - Boolean: verified current employee?

ENRICHMENT FIELDS (when requested):
  email                   - Verified email (from Email enrichment)
  work_history_summary    - Career summary (from Summarize Work History)
  thought_leadership      - Podcasts/articles/talks (from Find Thought Leadership)
  custom_enrichments      - Any custom Claygent research
```

### Job Fields (15 available)

```
CORE FIELDS:
  company_name            - Hiring company
  title                   - Job title
  normalized_title        - Standardized title
  location                - Job location

COMPENSATION:
  salary_min              - Minimum salary
  salary_max              - Maximum salary
  salary_currency         - Currency (USD, EUR, etc.)
  salary_unit             - Unit (YEAR, MONTH, HOUR)

CLASSIFICATION:
  seniority               - Level (Entry, Mid, Senior, etc.)
  functions               - Departments (Engineering, Sales, etc.)
  employment_type         - Type (Full-time, Contract, etc.)

LINKS:
  url                     - LinkedIn job URL
  application_url         - Direct application link

DATES:
  posted_at               - When posted
  closed_at               - When closed/filled
```

### Enrichment Fields (7 available)

```
company_domain            - Source company domain
company_name              - Source company name
enrichment_type           - Type (Headcount Growth, Open Jobs, etc.)
state                     - Status (complete, in-progress, failed)
value                     - Raw enrichment value (may be truncated)
provider                  - Data provider (LinkedIn, Semrush, Claygent, etc.)
timestamp                 - When enrichment was added
```

---

## Header Customization Flow

**First export of session—offer full options:**

```
First CSV export! Select your preferred fields:

COMPANIES (pick fields):
☑ Core: name, domain, linkedin_url, website, employee_count
☑ Location: country, locality
☑ Financials: annual_revenue, total_funding
☐ Enrichments: headcount_growth_12mo, website_traffic, open_jobs_count
☐ All fields

CONTACTS (pick fields):
☑ Core: name, title, company, domain, linkedin_url
☑ Employment: start_date, location
☐ Enrichments: email, work_history_summary
☐ All fields

JOBS (pick fields):
☑ Core: company_name, title, location
☑ Compensation: salary_min, salary_max, salary_currency
☐ All fields

→ [Use selected] / [All fields] / [Skip]
```

**Subsequent exports—use same headers, just confirm:**

```
Appending 12 new contacts to contacts.csv (using same columns).
→ [Append] / [Change columns] / [Skip]
```

---

## Export Schemas

**REQUIRED COLUMNS (always include):**
- `context` - Brief description of user's intent (e.g., "competitor research for pitch deck")
- `date_added` - ISO date when row was added (YYYY-MM-DD)

### companies.csv (default columns)
```
name,domain,linkedin_url,website,industry,type,employee_count,country,locality,annual_revenue,total_funding,context,date_added
```

### contacts.csv (default columns)
```
name,title,company,domain,linkedin_url,location,start_date,profile_id,is_current_employee,context,date_added
```

### jobs.csv (default columns)
```
company_name,title,location,salary_min,salary_max,salary_currency,seniority,employment_type,url,posted_at,context,date_added
```

### enrichments.csv (all columns)
```
company_domain,company_name,enrichment_type,state,value,provider,context,date_added
```

**Context examples:**

| User Intent | Context Value |
|-------------|---------------|
| "Find competitors to Stripe" | "Stripe competitor analysis" |
| "Get ML engineers at OpenAI" | "ML engineer recruiting - OpenAI" |
| "Research Series B companies in fintech" | "Series B fintech market scan" |
| "Find decision makers at target accounts" | "Sales outreach - target accounts" |

---

## Append-Mode Export Functions

Use these patterns to append to existing CSVs:

```python
import csv
import os

def append_to_csv(filepath, rows, fieldnames):
    """Append rows to CSV, creating with headers if new."""
    file_exists = os.path.exists(filepath)
    
    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)
    
    return len(rows)

def get_csv_row_count(filepath):
    """Get current row count (excluding header)."""
    if not os.path.exists(filepath):
        return 0
    with open(filepath, 'r', encoding='utf-8') as f:
        return sum(1 for _ in f) - 1  # Subtract header
```

---

## Resting Point Prompt Template

Use this template when offering CSV export at natural resting points:

```
---
📊 **Checkpoint: Save your data?**

This batch collected:
| Type | New Rows | Total in CSV |
|------|----------|--------------|
| Companies | 3 | 8 |
| Contacts | 47 | 89 |
| Jobs | 22 | 45 |

→ [Append to CSVs] / [Customize columns] / [Skip for now]
---
```

---

## End-of-Session Checklist

Before ending any Clay session:

1. ☐ Retrieve any "in-progress" enrichments with `get-existing-search`
2. ☐ Filter contacts for current employees (use `is_current_employee()`)
3. ☐ Deduplicate contacts by `profile_id`
4. ☐ Extract jobs from Open Jobs enrichments
5. ☐ Offer FINAL CSV append with summary counts
6. ☐ Confirm file locations with user

**Final session prompt:**

```
Session complete! Final data summary:

| CSV File | Total Rows |
|----------|------------|
| clay_companies.csv | 12 |
| clay_contacts.csv | 156 |
| clay_jobs.csv | 67 |
| clay_enrichments.csv | 34 |

Files saved to: [output_directory]
→ [Open folder] / [Done]
```

---

## Full Export Script

Use `scripts/export_clay_session.py` at session end to export all collected data.

**Usage:**
```bash
python scripts/export_clay_session.py <output_dir>
```

The script:
- Collects all companies, contacts, jobs, and enrichments
- Deduplicates contacts by `profile_id`
- Merges enrichments from multiple searches
- Extracts jobs from Open Jobs enrichments
- Exports to timestamped CSV files
- Includes `context` and `date_added` columns

See [export_clay_session.py](../scripts/export_clay_session.py) for full implementation.
