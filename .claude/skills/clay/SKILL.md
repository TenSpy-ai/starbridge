---
name: clay
description: "Clay MCP integration for company and contact enrichment. TRIGGERS: (1) Finding contacts/people at companies by role, title, or name, (2) Company research—funding, headcount, tech stack, competitors, customers, news, (3) Lead generation and prospecting, (4) Getting emails or phone numbers, (5) Open jobs and hiring signals, (6) Any explicit 'Clay' mention. CRITICAL: Every Clay operation costs real credits—always estimate before calling, collect ALL returned data, and export to CSV at natural resting points and session end."
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - mcp__claude_ai_Clay__*
  - Read
  - Write
  - Bash
argument-hint: "[company domain or name]"
---

# Clay MCP Integration

## Core Principle

> **If data was surfaced, collect it. Credits are already spent—never waste them.**

At session end, ALWAYS offer CSV export of ALL collected data, regardless of whether explicitly requested.

---

## Tool Selection

| User Intent | Tool | Notes |
|-------------|------|-------|
| "Tell me about [company]" | `find-and-enrich-company` | Single company lookup |
| "What's [company]'s funding/tech stack?" | `find-and-enrich-company` + dataPoints | Add enrichments |
| "Find engineers at [company]" | `find-and-enrich-contacts-at-company` | Role-based search |
| "Find VPs in California at [company]" | `find-and-enrich-contacts-at-company` + filters | Filtered search |
| "Find John Smith at [company]" | `find-and-enrich-list-of-contacts` | Named person lookup |
| "Get their emails" (after search) | `add-contact-data-points` | Enrich existing search |
| "What's their tech stack?" (after search) | `add-company-data-points` | Enrich existing search |
| "Check credits" | `get-credits-available` | FREE - no credits |
| Retrieve previous results | `get-existing-search` | FREE - no credits |

---

## Session Workflow

### 1. Before ANY Operation—Estimate Credits

```
Credit estimate for [action]:

| Operation | Count | Est. Each | Total |
|-----------|-------|-----------|-------|
| Company lookup | 3 | ~1 | ~3 |
| Open Jobs enrichment | 3 | ~2 | ~6 |
| **TOTAL** | | | **~9 credits** |

Proceed? [Yes / No]
```

### 2. During Operations
- Store ALL `searchId` values for later retrieval
- Track enrichments with `state: "in-progress"`—re-fetch with `get-existing-search` after 30 seconds

### 3. At Natural Resting Points—Offer CSV Export

**Trigger CSV prompts when:**
- Completed multi-company lookup
- Completed contact search + enrichments
- Before asking "What's next?"
- At session end (MANDATORY)

```
📊 **Checkpoint: Save your data?**

This batch collected:
| Type | New Rows | Total in CSV |
|------|----------|--------------|
| Companies | 3 | 8 |
| Contacts | 47 | 89 |

→ [Append to CSVs] / [Customize columns] / [Skip for now]
```

See [csv-export.md](references/csv-export.md) for complete field reference and export patterns.

---

## MCP Tools Reference

### find-and-enrich-company
Single company lookup. Returns company profile + 20 bundled contacts.

```python
companyIdentifier: "anthropic.com"  # Domain or LinkedIn URL (NOT company name)
companyDataPoints: [{"type": "Headcount Growth"}, {"type": "Open Jobs"}]  # Optional
```

### find-and-enrich-contacts-at-company
Find contacts at a company with optional filters.

```python
companyIdentifier: "anthropic.com"
contactFilters: {
    "job_title_keywords": ["VP Finance"],      # Compound titles as ONE string
    "job_title_exclude_keywords": ["Intern"],
    "locations": ["California"],
    "current_role_max_months_since_start_date": 6  # New hires only
}
dataPoints: {
    "contactDataPoints": [{"type": "Email"}],
    "companyDataPoints": [{"type": "Tech Stack"}]
}
```

### find-and-enrich-list-of-contacts
Look up specific named people. **TRUE BATCH**—most efficient for known names. **MAX 20 contacts per call** (21+ returns "Internal error").

```python
contactIdentifiers: [
    {"contactName": "Dario Amodei", "companyIdentifier": "anthropic.com"},
    {"contactName": "Sam Altman", "companyIdentifier": "openai.com"}
]
dataPoints: {
    "contactDataPoints": [{"type": "Email"}, {"type": "Summarize Work History"}]
}
```

**Bonus:** Returns full company profiles for ALL matched contacts' employers—can be used as a batch company lookup trick.

### add-company-data-points / add-contact-data-points
Add enrichments to existing search. Requires `searchId` from previous search.

```python
searchId: "cgas-search-id_abc123..."
dataPoints: [{"type": "Recent News"}, {"type": "Revenue Model"}]
```

### get-existing-search (FREE)
Retrieve previous search results by `searchId`. Use to check `in-progress` enrichments.

### get-credits-available (FREE)
Returns: `{ hasWorkspaceCredits: boolean, hasPlatformCredits: boolean }`

### track-event (Internal)
Track analytics events. Generally not needed for user workflows.

```python
eventName: "search_completed"
properties: {"company": "anthropic.com", "contacts_found": 20}
```

---

## Contact Filter Reference

| Filter | Type | Example | Notes |
|--------|------|---------|-------|
| `job_title_keywords` | string[] | `["VP Finance"]` | Keep compound titles as ONE string |
| `job_title_exclude_keywords` | string[] | `["Intern", "Assistant"]` | Exclude titles |
| `headline_keywords` | string[] | `["AI", "ML"]` | LinkedIn headline |
| `about_keywords` | string[] | `["startup founder"]` | About section |
| `profile_keywords` | string[] | `["python", "sales"]` | **Undocumented**—searches whole profile |
| `certification_keywords` | string[] | `["AWS", "CPA"]` | Certifications |
| `languages` | string[] | `["Spanish"]` | Profile languages |
| `school_names` | string[] | `["Stanford", "MIT"]` | Schools attended |
| `current_role_min_months_since_start_date` | int | `12` | Tenured employees |
| `current_role_max_months_since_start_date` | int | `3` | New hires |
| `locations` | string[] | `["California", "United States"]` | Include locations |
| `locations_exclude` | string[] | `["India", "Philippines"]` | Exclude locations |

**Filter Logic:**
- Multiple filters combine with **AND**
- Values within arrays combine with **OR**
- ❌ WRONG: `["VP", "Finance"]` → matches ALL VPs OR ALL Finance
- ✅ RIGHT: `["VP Finance", "VP of Finance"]` → matches VP Finance titles only

**Follow-up Interpretation:**

| User Signal | Action |
|-------------|--------|
| "also", "too", "as well" | ADD to existing filters |
| "only", "just" | NARROW within current context |
| "actually", "instead" | REPLACE filters entirely |
| Ambiguous | ASK for clarification |

**CRITICAL:** ANY search modification requires re-calling the tool. Never filter results in chat.

---

## Available Enrichment Types

### Company Enrichments

| Type | Provider | Est. Credits | Data Returned |
|------|----------|--------------|---------------|
| Headcount Growth | LinkedIn | ~1-2 | Growth % at 1/3/6/9/12/24/36/48 months |
| Open Jobs | LinkedIn/PredictLeads | ~2-3 | Full job listings with salary |
| Website Traffic | Semrush | ~2-3 | Monthly visitors |
| Tech Stack | BuiltWith | ~2-3 | Technologies by category |
| Latest Funding | PredictLeads | ~1-2 | Round, amount, investors |
| Annual Revenue | Various | ~1-2 | Revenue range |
| Revenue Model | Claygent | ~3-5 | Business model analysis |
| Recent News | Claygent | ~3-5 | News with analysis |
| Company Competitors | Claygent | ~2-4 | Competitor list |
| Company Customers | Claygent | ~2-4 | Known customers |
| Investors | Claygent | ~2-4 | Investor list |
| Custom | Claygent | ~3-5 | Any research question |

### Contact Enrichments

| Type | Provider | Est. Credits | Data Returned |
|------|----------|--------------|---------------|
| Email | Waterfall | ~2-5 | Verified email |
| Summarize Work History | Claygent | ~2-3 | Career summary |
| Find Thought Leadership | Claygent | ~2-3 | Podcasts, articles, talks |
| Custom | Claygent | ~3-5 | Any research question |

**Note:** Phone is NOT in standard enum—use Custom type for phone lookups.

### Custom Data Points (Claygent)

```python
# Current schema:
{"type": "Custom", "dataPointName": "Recent Blog Posts", "dataPointDescription": "Find blog posts from 2024-2025"}

# Deprecated (still works):
{"type": "Custom", "customDataPoint": "..."}
```

---

## CRITICAL: Data Quality Issues

### Issue #1: Bundled Contacts Include Non-Employees

**Problem:** The 20 contacts bundled with company lookups include former employees, investors, and advisors.

**Real Example:**
```
Company searched: OpenAI
Contact returned: Mira Murati
latest_experience_company: "Thinking Machines Lab"  ← She LEFT OpenAI
```

**Impact:** 20-40% of bundled contacts may NOT be current employees.

**Solution—ALWAYS filter contacts:**

```python
def is_current_employee(contact, target_company, target_domain):
    """Check if contact is currently employed at target company."""
    company = contact.get('latest_experience_company', '').lower()
    domain = contact.get('domain', '').lower()
    return (target_company.lower() in company or 
            domain == target_domain.lower())

current_employees = [c for c in contacts if is_current_employee(c, "Anthropic", "anthropic.com")]
```

### Issue #2: employee_count vs size Mismatch

**Problem:** LinkedIn's `size` field is a category that RARELY updates.

| Company | employee_count | size | Discrepancy |
|---------|---------------|------|-------------|
| OpenAI | 7,119 | "201-500 employees" | **14x off** |
| Anthropic | 3,571 | "501-1,000 employees" | 3.5x off |

**Solution:** ALWAYS use `employee_count`. NEVER trust `size`.

### Issue #3: Enrichments Return "in-progress"

**Problem:** Claygent enrichments take time to process.

**Solution:**
```
Initial call → state: "in-progress"
Wait 30 seconds
get-existing-search → state: "complete" (or retry)
```

### Issue #4: Title Keywords Match Too Broadly

❌ WRONG: `{"job_title_keywords": ["Engineer"]}` → Matches Sales Engineer, Support Engineer, etc.
✅ RIGHT: `{"job_title_keywords": ["Software Engineer", "Staff Engineer"]}` → Specific matches

See [data-schemas.md](references/data-schemas.md) for complete response schemas and field trust levels.

---

## Multi-Company Batch Patterns

| Tool | Batching | Use Case |
|------|----------|----------|
| `find-and-enrich-list-of-contacts` | ✅ TRUE BATCH | Specific named people |
| `find-and-enrich-company` | ❌ Parallel calls | Multiple companies |
| `find-and-enrich-contacts-at-company` | ❌ Parallel calls | Roles at multiple companies |

### Pattern: Multiple Companies
Run parallel `find-and-enrich-company` calls—all execute simultaneously.

### Pattern: Specific Named People (TRUE BATCH)
Single `find-and-enrich-list-of-contacts` returns ALL contacts + ALL company profiles in one call.

See [advanced-patterns.md](references/advanced-patterns.md) for detailed batching strategies and error recovery.

---

## Workspace Business Context

Every Clay response includes `workspaceBusinessContext` with pre-configured business info:

```json
{
  "companyDescription": "What the user's company does",
  "idealCustomerProfile": "ICP criteria (company size, industries)",
  "idealBuyerPersonas": "Target personas (titles, pain points)",
  "outboundEmailInstructions": "Email writing guidelines"
}
```

**Use this for:**
- Auto-personalizing suggestions ("Anthropic has 3,571 employees—within your ICP range")
- Filtering/flagging companies that match ICP
- Suggesting relevant contact filters
- Following email guidelines if user asks for drafts

---

## Proactive Suggestions

Periodically remind users about capabilities they may not know.

**When to suggest:**
- After completing a task, before asking "What's next?"
- When user seems unsure
- NOT when it would delay a CSV checkpoint (CSV always takes priority)

**Format:** `💡 **Did you know?** Clay can also [capability]. Want to try it?`

| User Did | Suggest |
|----------|---------|
| Company lookup only | "Clay can also find contacts at this company—VPs, engineers, new hires, etc." |
| Contact search without emails | "Want to enrich these contacts with verified emails?" |
| Single company research | "I can compare this against competitors—want a competitor analysis?" |
| Found contacts | "I can find their thought leadership (podcasts, articles, talks) or summarize their work history." |
| Looking at jobs | "Clay can show headcount growth trends to see if they're actively expanding." |
| Researching startups | "Clay can pull funding history, investors, and revenue estimates." |
| General browsing | "Clay can research almost anything about companies: tech stack, customers, news, revenue model..." |

**Capability reminders (rotate through):**

1. **Contact filters**: "You can filter by location, tenure, certifications, languages, schools, or even search their full profile with `profile_keywords`."

2. **Custom research**: "Clay's Claygent can answer custom questions like 'What's their go-to-market strategy?' or 'Find recent product announcements.'"

3. **Batch operations**: "I can research multiple companies at once—just give me a list of domains."

4. **Named lookups**: "Know specific people? I can look up 'John Smith at Anthropic' directly."

5. **New hire detection**: "Filter for people who started in the last 3 months to find new decision makers."

6. **Historical data**: "Headcount Growth shows employee counts going back 48 months—great for trend analysis."

**Priority order:**
1. CSV checkpoint (if at resting point) — ALWAYS FIRST
2. Answer user's question
3. Proactive suggestion (if natural pause)

---

## Error Recovery

### "No results found"
1. Remove title keywords (too specific)
2. Remove location filter (too narrow)
3. Remove tenure filter
4. Verify company domain is correct

### "Domain not found"
- Ambiguous company name ("Delta" → delta.com? deltadental.com?)
- Different domain (Alphabet → google.com not alphabet.com)
- **Solution:** Always use explicit domains

### "Enrichment failed"
- Company too small/new for data
- Private company with limited info
- **Recovery:** Accept null, note in export

---

## End-of-Session Checklist

1. ☐ Retrieve any `in-progress` enrichments with `get-existing-search`
2. ☐ Filter contacts for current employees
3. ☐ Deduplicate contacts by `profile_id`
4. ☐ Extract jobs from Open Jobs enrichments
5. ☐ Offer FINAL CSV export with summary counts
6. ☐ Confirm file locations with user

```
Session complete! Final data summary:

| CSV File | Total Rows |
|----------|------------|
| clay_companies.csv | 12 |
| clay_contacts.csv | 156 |
| clay_jobs.csv | 67 |

Files saved to: [output_directory]
→ [Open folder] / [Done]
```

---

## Reference Files

- **[inputs-reference.md](references/inputs-reference.md)** - Complete input parameters for all 8 MCP endpoints, batch limits, summary table
- **[data-schemas.md](references/data-schemas.md)** - Complete JSON schemas, field trust levels, enrichment value formats
- **[csv-export.md](references/csv-export.md)** - Growing CSV approach, field reference, header customization, Python exporter
- **[advanced-patterns.md](references/advanced-patterns.md)** - Multi-company batching, parallelization, error handling patterns
