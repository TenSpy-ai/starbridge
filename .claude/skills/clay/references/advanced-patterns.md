# Advanced Patterns Reference

Multi-company batch patterns, parallelization strategies, credit optimization, and error recovery.

---

## Table of Contents
- [Batching Strategy](#batching-strategy)
- [Multi-Company Batch Patterns](#multi-company-batch-patterns)
- [Optimal Batch Sizes](#optimal-batch-sizes)
- [Credit Cost Reference](#credit-cost-reference)
- [Error Recovery](#error-recovery)

---

## Batching Strategy

**DO THIS:**
1. Collect all company domains first
2. Run `find-and-enrich-contacts-at-company` for ALL at once (parallel)
3. Add enrichments to existing search (reuses searchId)
4. Export everything at session end

**DON'T DO THIS:**
- ❌ Lookup company → enrich → lookup next → enrich (wasteful)
- ❌ Forget to collect data before moving on
- ❌ Re-run searches instead of using `get-existing-search`

---

## Multi-Company Batch Patterns

**Understanding batch capabilities:**

| Tool | Batching | What It Returns |
|------|----------|-----------------|
| `find-and-enrich-list-of-contacts` | ✅ TRUE BATCH | Multiple contacts + ALL their companies in one call |
| `find-and-enrich-company` | ❌ Single only | One company per call |
| `find-and-enrich-contacts-at-company` | ❌ Single only | One company's contacts per call |

### Pattern 1: "Research these 10 competitors"

**Best approach:** Parallel `find-and-enrich-company` calls

```
User: "Research Stripe's competitors: Adyen, Square, Checkout.com, Braintree"

DO THIS (parallel calls):
┌─────────────────────────────────────────────────────────┐
│  Call 1: find-and-enrich-company(adyen.com)             │
│  Call 2: find-and-enrich-company(squareup.com)          │  ← All 4 run
│  Call 3: find-and-enrich-company(checkout.com)          │    simultaneously
│  Call 4: find-and-enrich-company(braintreepayments.com) │
└─────────────────────────────────────────────────────────┘
Result: ~4 credits, all company data in one round-trip

DON'T DO THIS (sequential):
Call 1 → wait → Call 2 → wait → Call 3 → wait → Call 4
Result: Same credits, 4x slower
```

### Pattern 2: "Find decision makers at these 5 accounts"

**Best approach:** Parallel `find-and-enrich-contacts-at-company` calls with filters

```
User: "Find VPs at Anthropic, OpenAI, Mistral, Cohere, and Inflection"

DO THIS (parallel calls with same filters):
┌─────────────────────────────────────────────────────────────────────┐
│  Call 1: find-and-enrich-contacts-at-company(anthropic.com,         │
│          contactFilters: {job_title_keywords: ["VP", "Director"]})  │
│  Call 2: find-and-enrich-contacts-at-company(openai.com, ...)       │  ← All run
│  Call 3: find-and-enrich-contacts-at-company(mistral.ai, ...)       │    in parallel
│  Call 4: find-and-enrich-contacts-at-company(cohere.com, ...)       │
│  Call 5: find-and-enrich-contacts-at-company(inflection.ai, ...)    │
└─────────────────────────────────────────────────────────────────────┘
Result: 5 searches, each with filtered contacts
```

### Pattern 3: "Find these specific people" (TRUE BATCH)

**Best approach:** Single `find-and-enrich-list-of-contacts` call

```
User: "Find Sam Altman at OpenAI, Satya Nadella at Microsoft, and Sundar Pichai at Google"

DO THIS (one call):
┌────────────────────────────────────────────────────────────────────┐
│  find-and-enrich-list-of-contacts(                                 │
│    contactIdentifiers: [                                           │
│      {contactName: "Sam Altman", companyIdentifier: "openai.com"}, │
│      {contactName: "Satya Nadella", companyIdentifier: "microsoft.com"}, │
│      {contactName: "Sundar Pichai", companyIdentifier: "google.com"}     │
│    ]                                                               │
│  )                                                                 │
└────────────────────────────────────────────────────────────────────┘
Result: ONE call returns ALL contacts + ALL company profiles + auto-enrichments
```

**Pro tip:** `find-and-enrich-list-of-contacts` is the most efficient when you know names—it returns full company data for every contact's employer as a bonus.

### Pattern 4: Hybrid - "Research companies, then find key people"

```
Phase 1: Parallel company lookups (get company data + bundled contacts)
  └→ 5x find-and-enrich-company calls

Phase 2: Review bundled contacts, identify gaps

Phase 3: Single batch call for specific people found in research
  └→ 1x find-and-enrich-list-of-contacts (names discovered in Phase 1)

Phase 4: Add enrichments to existing searches (reuse searchIds)
  └→ add-contact-data-points for emails
  └→ add-company-data-points for tech stack, funding, etc.
```

### Pattern 5: Batch Company Lookup Trick

**Use `find-and-enrich-list-of-contacts` to get multiple company profiles in ONE call.**

Since this endpoint returns full company data for every matched contact's employer, you can use it as an efficient batch company lookup—but with specific rules:

**Confirmed Rules (Jan 2026):**
- ✅ Max 20 contacts per call (21+ returns "Internal error")
- ✅ Need **REAL names** (generic titles like "CEO" return empty companies)
- ✅ Company data only returns when contacts ARE found
- ✅ Tested: 20 real CEO names → 17 companies + 19 contacts in ONE call

**Example:**
```python
# Want company data for 15 companies? Use known executive names:
find-and-enrich-list-of-contacts(
  contactIdentifiers: [
    {"contactName": "Dario Amodei", "companyIdentifier": "anthropic.com"},
    {"contactName": "Sam Altman", "companyIdentifier": "openai.com"},
    {"contactName": "Satya Nadella", "companyIdentifier": "microsoft.com"},
    # ... up to 20 total
  ]
)
# Returns: ALL contact profiles + ALL company profiles in one call
```

**When to use:**
- You know at least one real person at each target company
- You want both contact AND company data
- You're hitting rate limits with parallel `find-and-enrich-company` calls

**When NOT to use:**
- You don't know any real names at the companies
- You only need company data (no contacts)—parallel calls may be simpler

### Parallelization Summary

| Scenario | Strategy | Why |
|----------|----------|-----|
| Multiple companies, no specific people | Parallel `find-and-enrich-company` | No batch option exists |
| Multiple companies, find role types | Parallel `find-and-enrich-contacts-at-company` | Same filters, different companies |
| Specific named people | Single `find-and-enrich-list-of-contacts` | TRUE batch—most efficient |
| Multiple companies + know executive names | `find-and-enrich-list-of-contacts` with real names | Batch company lookup trick (see Pattern 5) |
| Follow-up enrichments | `add-*-data-points` on existing searchIds | Reuses data, no new lookups |

---

## Optimal Batch Sizes

*Last tested: January 2026*

| Operation | Hard Limit | Recommended | Notes |
|-----------|------------|-------------|-------|
| Named contacts (`find-and-enrich-list-of-contacts`) | **20** | 15-20 | 21+ returns "Internal error" |
| Company lookups (parallel calls) | **None found** | 10-15 | Tested 20 simultaneous—no hard limit |
| Enrichments per search | Unknown | 3-5 | Add incrementally if needed |

---

## Credit Cost Reference

| Operation | Provider | Est. Credits | Notes |
|-----------|----------|-------------|-------|
| Company lookup | — | ~1 | Includes 20 bundled contacts |
| Contact search (filtered) | — | ~1-2 | Per company |
| Named contact lookup | — | ~1 | Per person |
| **Company Enrichments:** | | | |
| Headcount Growth | LinkedIn | ~1-2 | Employee counts over time |
| Open Jobs | LinkedIn/PredictLeads | ~2-3 | Full job listings |
| Website Traffic | Semrush | ~2-3 | Monthly visitors |
| Tech Stack | BuiltWith | ~2-3 | Technologies by category |
| Latest Funding | PredictLeads | ~1-2 | Round, amount, investors |
| Annual Revenue | Various | ~1-2 | Revenue range estimate |
| Revenue Model | Claygent | ~3-5 | AI-generated analysis |
| Recent News | Claygent | ~3-5 | AI-generated analysis |
| Company Competitors | Claygent | ~2-4 | AI-generated list |
| Company Customers | Claygent | ~2-4 | AI-generated list |
| Investors | Claygent | ~2-4 | AI-generated list |
| **Contact Enrichments:** | | | |
| Email | Waterfall | ~2-5 | Verified email |
| Phone | Waterfall | ~3-5 | Via Custom type |
| Work History Summary | Claygent | ~2-3 | AI-generated summary |
| Thought Leadership | Claygent | ~2-3 | Podcasts, articles, talks |
| Custom enrichment | Claygent | ~3-5 | Any research question |

### Free Operations (No Credits)
- `get-credits-available` - Check remaining credits
- `get-existing-search` - Retrieve previous results by searchId

---

## Error Recovery

### "No results found"

Recovery steps (in order):
1. Remove title keywords (too specific)
2. Remove location filter (too narrow)
3. Remove tenure filter
4. Verify company domain is correct

**Example:**
```
Original: {"job_title_keywords": ["VP Engineering"], "locations": ["Austin"]}
Step 1: {"job_title_keywords": ["VP Engineering"]}  # Remove location
Step 2: {"job_title_keywords": ["VP", "Director"]}  # Broaden titles
Step 3: {}  # No filters, get all contacts
```

### "Domain not found"

**Common causes:**
- Ambiguous company name ("Delta" → delta.com? deltadental.com? deltaair.com?)
- Company uses different domain (Alphabet → google.com not alphabet.com)
- Typo in domain

**Solution:** Always use explicit domains, not company names. Confirm with user if ambiguous.

### "Enrichment failed"

**Common causes:**
- Company too small/new for data
- Private company with limited public info
- Provider outage

**Recovery:**
- Accept null value
- Note in export as "not available"
- Try alternative enrichment type if applicable

### "in-progress" enrichments

**Problem:** Claygent enrichments take time to process.

**Solution:**
```python
import time

def wait_for_enrichments(search_id, max_attempts=6):
    """Wait for enrichments to complete, polling every 30 seconds."""
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
    
    return result  # Return what we have after max attempts
```

### Timeout errors

**Problem:** Large batch calls may timeout.

**Recovery:**
1. Reduce batch size (10 companies → 5)
2. Run in smaller parallel batches
3. Check for partial results with `get-existing-search`

### Rate limiting

**Problem:** Too many calls in short period.

**Recovery:**
1. Add delays between batches (2-5 seconds)
2. Process results before next batch
3. Consolidate into fewer, larger searches when possible
