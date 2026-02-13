# Intel Report Agent Prompts

Prompts for a Datagen AI agent with access to the 8 Starbridge tools. The agent receives a buyer identifier + prospect product info, gathers data via tool calls, then generates each Notion section.

## Inputs (from Clay webhook)

```
buyer_name        — "California Community Colleges" (from Smartlead/Clay)
buyer_domain      — "cccco.edu" (from positive reply email domain)
prospect_product  — "VMock" (the vendor's product)
product_description — "AI-powered career services platform for resume optimization, interview prep, and career pathway mapping"
campaign_signal   — "Board discussion: workforce development and CTE pathways" (the signal from the outbound email that triggered the reply)
prospect_name     — "Jane Smith" (who replied)
prospect_email    — "jsmith@company.com"
tier              — 3 (1, 2, or 3)
```

---

## Phase 1: Data Gathering

The agent should make these tool calls. Steps 1-3 can run in parallel after buyer resolution.

### Step 0: Resolve Buyer

```
Tool: starbridge_buyer_search
Inputs:
  query: "{buyer_name}"        # or buyer_domain if name is unavailable
  page_size: 5

→ Save: resolved_buyer_id, resolved_buyer_name
→ If multiple matches: pick the one whose state/type best matches the prospect context
```

### Step 1: Full Profile

```
Tool: starbridge_buyer_profile
Inputs:
  buyer_id: "{resolved_buyer_id}"

→ Save entire profile object
```

### Step 2: Contacts

```
Tool: starbridge_buyer_contacts
Inputs:
  buyer_id: "{resolved_buyer_id}"
  page_size: 100

→ Save contacts array + totalContacts
```

### Step 3: Opportunities (Meetings + Purchases + RFPs + Contracts)

```
Tool: starbridge_opportunity_search
Inputs:
  search_query: "{resolved_buyer_name}"
  types: ["Meeting", "Purchase", "RFP", "Contract"]
  buyer_ids: ["{resolved_buyer_id}"]
  page_size: 40
  sort_field: "SearchRelevancy"

→ Save opportunities array + totalItems
```

### Step 4: AI Chat (Strategic Context)

```
Tool: starbridge_buyer_chat
Inputs:
  buyer_id: "{resolved_buyer_id}"
  question: "What are {resolved_buyer_name}'s key strategic priorities, recent technology initiatives, major procurement activity, and any leadership changes in the past 12 months? Include specific initiative names, dollar amounts, and dates where available."

→ Save ai_response string
```

**Shortcut**: Steps 0-4 can be collapsed into a single `starbridge_full_intel` call if the simplified opportunity output is sufficient. Use separate calls when you need the full opportunity detail (rfps[], purchaseOrders[], createdAt, parentBuyerId).

---

## Phase 2: Section Generation

Each section below is a standalone LLM generation prompt. The agent fills the template variables by reasoning over the gathered data.

---

### SECTION 1: Header

No LLM needed. Template fill:

```
# 📊 {resolved_buyer_name} — Intelligence Report for {prospect_product}
```

---

### SECTION 2: Buyer Snapshot

**Prompt:**

```
You are generating the Buyer Snapshot card for a Starbridge intelligence report.

BUYER PROFILE DATA:
{profile_json}

RULES:
- Pick the correct emoji for buyer type:
  🏛️ = HigherEducation or StateAgency
  🏫 = SchoolDistrict or School
  🏙️ = City
  🏢 = County
- Pick the correct size metric:
  HigherEducation → "Enrollment" (use profile.extraData.enrollment or profile.metadata.enrollment)
  SchoolDistrict → "Enrollment" (use profile.extraData.schoolDistrictTotalStudents or totalEnrollment)
  City → "Population" (use profile.extraData.population)
  County → "Population" (use profile.extraData.population)
  StateAgency → "Employees" (if available, otherwise omit)
- Format numbers with commas (2108927 → "2,108,927")
- Procurement Score: use profile.extraData.procurementHellScore (0-100). If missing, omit the line.
- Fiscal Year Start: use profile.extraData.fiscalYearStartDate. If missing, omit.
- Website: use profile.url. Strip "http://" and "https://" for display text.
- Phone: use profile.metadata.address.phone. If missing, omit.
- Parent Org: use profile.extraData.parentName. If missing, omit the line entirely.

OUTPUT exactly this markdown (omit any line where data is unavailable):

> {emoji}
>
> **{buyer_name}** | {buyer_type_label}
>
> **State:** {state} | **City:** {city} | **{size_label}:** {size_value}
>
> **Procurement Score:** {score}/100 | **Fiscal Year Start:** {fiscal_year}
>
> **Website:** [{website_display}]({website_url}) | **Phone:** {phone}
>
> **Parent Org:** {parent_org}
```

---

### SECTION 3: Relevancy Analysis

**Prompt:**

```
You are a SLED procurement intelligence analyst writing the Relevancy Analysis for an intel report.

PROSPECT PRODUCT: {prospect_product}
PRODUCT DESCRIPTION: {product_description}
CAMPAIGN SIGNAL (what triggered the reply): {campaign_signal}

BUYER: {resolved_buyer_name}
BUYER TYPE: {buyer_type}

STRATEGIC CONTEXT FROM AI CHAT:
{ai_response}

OPPORTUNITIES (meetings, purchases, RFPs, contracts):
{opportunities_json}

BUYER PROFILE EXTRA DATA:
{profile_extraData_json}

YOUR TASK:
1. Identify a Use Case Archetype — a 3-6 word label capturing why this buyer is a fit for this product. Format: "{Theme} — {Specific Application}". Examples:
   - "Scale & Equity — Career Services Access"
   - "Modernization Window — LMS Replacement Cycle"
   - "Compliance Gap — Attendance Reporting"
   - "New Leadership — Vendor Stack Review"

2. Write a 1-2 sentence opening paragraph connecting the buyer's strategic context to the product.

3. Write exactly 3 bullets. Each bullet MUST:
   - Reference a SPECIFIC signal, initiative, or data point (not generic claims)
   - Name the initiative, quote board language, or cite dollar amounts where available
   - Explain WHY it creates an opening for {prospect_product} specifically
   - Be usable by a BDR on a phone call — concrete enough to reference in conversation

BAD bullet: "They are investing in technology upgrades."
GOOD bullet: "The Board of Governors is prioritizing Career Technical Education (CTE) pathways and workforce alignment, with a Senior Advisor to the Chancellor specifically focused on 'Workforce Development, Strategic Partnerships, and GenAI.'"

OUTPUT FORMAT:

> 🔥
>
> **Use Case Archetype:** {archetype}

{opening_paragraph}

- {bullet_1}
- {bullet_2}
- {bullet_3}
```

**Tier gating:** Only generate for Tier 3. Skip for Tier 1 and 2.

---

### SECTION 4: Gameplan

**Prompt:**

```
You are a SLED sales strategist writing the Gameplan section for an intel report.

PROSPECT PRODUCT: {prospect_product}
PRODUCT DESCRIPTION: {product_description}

BUYER: {resolved_buyer_name}
BUYER TYPE: {buyer_type}
BUYER STATE: {buyer_state}

CONTACTS (with titles, normalizedTitles, and verification status):
{contacts_json}

STRATEGIC CONTEXT FROM AI CHAT:
{ai_response}

KEY SIGNALS FROM RELEVANCY ANALYSIS:
{relevancy_bullets}

BUYER PROFILE:
- Procurement Score: {procurement_score}/100
- Budget: {budget_amount} ({budget_year})
- Fiscal Year Start: {fiscal_year_start}

YOUR TASK:

1. PRIMARY DM TARGET: Select the single best contact to reach first. Criteria:
   - Role directly overlaps with {prospect_product}'s use case
   - Has procurement influence (Director+, VP, C-suite, Superintendent, Dean)
   - Has verified email (emailVerified = true)
   - Prefer contacts with normalizedTitles that match the product category
   Priority order for role matching:
   - Direct category owner (e.g., "Director of Career Services" for a career platform)
   - Technology leader (CIO, CTO, VP of IT)
   - Budget authority (CFO, VP of Finance, Superintendent)
   - Strategic leader (Deputy Superintendent, Provost, City Manager)

2. WHY THIS CONTACT: 1-2 sentences explaining why this person specifically. Reference their role's overlap with the product AND a signal from the relevancy analysis.

3. SECONDARY CONTACTS: Pick 2-3 alternates. Include name, title, and email.

4. OUTREACH SCRIPT: Write a 2-3 sentence talk track the BDR can use on a cold call or email. Rules:
   - OPEN with the buyer's situation, not the product ("I saw CCC is standing up a common cloud data platform...")
   - Reference a specific signal or initiative by name
   - Frame the product as solving THEIR stated need
   - End with a question, not a pitch
   - NO jargon, NO "leverage", NO "synergy"

5. PROCUREMENT PATH:
   - Recommended channel (cooperative purchasing programs by state/type, direct RFP, sole source)
   - Sole source threshold (varies by state and entity type — use your knowledge of SLED procurement)
   - Key resellers for this buyer type (CDW-G, SHI, Carahsoft, Connection, etc.)
   - Procurement score interpretation (low = easy, high = difficult)

OUTPUT FORMAT:

> 🎯
>
> **Primary DM Target:** {name} — {title}
>
> **Email:** [{email}](mailto:{email})

**Why this contact:** {rationale}

**Secondary contacts:**

- **{name_2}** — {title_2} ([{email_2}](mailto:{email_2}))
- **{name_3}** — {title_3} ([{email_3}](mailto:{email_3}))
- **{name_4}** — {title_4} ([{email_4}](mailto:{email_4}))

#### Outreach Script

"{script}"

#### Procurement Path

**Recommended:** {channel}

**Sole Source Threshold:** {threshold}

**Key Resellers:** {resellers}

**Procurement Score:** {score}/100 — {interpretation}
```

**Tier gating:** Only generate for Tier 3. Skip for Tier 1 and 2.

---

### SECTION 5: Key Contacts Table

**Prompt:**

```
You are selecting and formatting the Key Contacts table for a Starbridge intel report.

PROSPECT PRODUCT: {prospect_product}
PRODUCT DESCRIPTION: {product_description}

ALL CONTACTS ({total_contacts} total):
{contacts_json}

RULES:
1. Select 5-10 contacts most relevant to {prospect_product}.
2. Ranking criteria:
   - normalizedTitles that match the product category (highest priority)
   - Title seniority (Director+ before Coordinator/Specialist)
   - Has verified email (emailVerified = true)
   - Has phone number
   - worksAtBuyer = true (current employees only)
3. Preserve non-standard SLED titles exactly as they appear. Do NOT normalize "Director (Commissioner) of Public Works" to "Director of Public Works".
4. For email: show the address or "—" if null.
5. For phone: show the number or "—" if null.
6. For verified: show ✅ if emailVerified is true, "—" otherwise.
7. If primary DM from Gameplan is in the list, put them first.

OUTPUT FORMAT:

| **Name** | **Title** | **Email** | **Phone** | **Verified** |
| --- | --- | --- | --- | --- |
| {name} | {title} | {email} | {phone} | {verified} |
...

*{total_contacts} total contacts available in Starbridge. Showing top matches for {prospect_product} engagement.*
```

**Tier gating:**
- Tier 1: Skip entirely
- Tier 2: Show only the primary DM contact (1 row) as a "DM card" instead of a table
- Tier 3: Full 5-10 row table

---

### SECTION 6: Recent Strategic Signals

**Prompt:**

```
You are a SLED procurement analyst writing the Strategic Signals section for an intel report.

PROSPECT PRODUCT: {prospect_product}
PRODUCT DESCRIPTION: {product_description}
CAMPAIGN SIGNAL: {campaign_signal}

BUYER: {resolved_buyer_name}

OPPORTUNITIES DATA (from Starbridge — meetings, purchases, RFPs, contracts):
{opportunities_json}

AI CHAT STRATEGIC CONTEXT:
{ai_response}

YOUR TASK:
Select the top 3-6 signals and write each as a titled paragraph.

SIGNAL SELECTION CRITERIA (rank by):
1. Recency — newer signals first
2. Urgency — signals with deadlines (contract expirations, RFP due dates) rank higher
3. Specificity — named initiatives, dollar amounts, specific product categories
4. Dollar value — signals with budget/contract amounts are more concrete
5. Reply relevance — signals related to campaign_signal rank higher (this is what got them to reply)
6. Type priority (tiebreaker): RFP > Contract Expiration > Budget > Board Discussion > Purchase > Leadership > Grant > Conference

SIGNAL TITLE: Short descriptive label (e.g., "Vision 2030 — Common Cloud Data Platform"). NOT the raw opportunity title from the API.

SIGNAL PARAGRAPH (2-4 sentences each):
- Sentence 1: What happened or is being planned. Include dates, dollar amounts, initiative names.
- Sentence 2: What it means for the buyer organization.
- Sentence 3-4 (optional): How it connects to {prospect_product} — only if the connection is natural, not forced.
- End with a parenthetical source attribution: *(Board of Governors meeting, November 2025)* or *(Purchase order, Q4 2025)*

QUALITY BAR:
- Each paragraph should give a BDR enough context to discuss this signal on a phone call
- Use the buyer's own language (initiative names, program names) not generic descriptions
- "The board discussed improving student outcomes" = TOO VAGUE
- "The Board of Governors approved a 'demonstration project' in November 2025 to create shared data infrastructure across all 116 colleges" = GOOD

OUTPUT FORMAT:

#### {signal_1_title}

{signal_1_paragraph}

#### {signal_2_title}

{signal_2_paragraph}

#### {signal_3_title}

{signal_3_paragraph}

(continue for 4-6 signals if available)
```

**Tier gating:**
- Tier 1: Generate bullet-form signals (1 sentence each, no paragraphs), 5-10 signals
- Tier 2: Same as Tier 1
- Tier 3: Full paragraphs as described above, 3-6 signals

**Tier 1/2 variant prompt (replaces the paragraph instructions above):**

```
OUTPUT FORMAT (Tier 1/2 — bullets only):

Write 5-10 SLED Signal Bullets. Each bullet is 1-2 sentences. Format:

1. "{signal_bullet_1}"
2. "{signal_bullet_2}"
...

Each bullet should:
- Lead with the specific fact (contract amount, board action, budget number)
- End with why it matters for procurement timing
- Be self-contained — readable without the other bullets

Example:
"Austin ISD's LMS platform contract expires in 5 months ($250K annual). Districts typically begin vendor evaluation 90-120 days before expiration, putting the procurement timeline right now."
```

---

### SECTION 7: Footer

No LLM needed. Template fill:

```
---

*Generated Starbridge Intelligence {current_month} {current_year}*

*Data source: Starbridge buyer profile, contacts, AI analysis, and opportunity database*
```

---

## Full Assembly Order

The agent assembles all sections into a single markdown document:

```markdown
{section_1_header}

{section_2_buyer_snapshot}

---

{section_3_relevancy_analysis}       ← Tier 3 only

---

{section_4_gameplan}                 ← Tier 3 only

---

{section_5_contacts_table}           ← Tier 2: DM card only. Tier 3: full table.

---

{section_6_strategic_signals}

---

{section_7_footer}
```

---

## Edge Cases

| Scenario | Handling |
|---|---|
| Buyer not found in search | Return error to Clay. Do not generate report. |
| 0 contacts | Omit Key Contacts section. Add note: "No contacts currently available in Starbridge." |
| 0 opportunities | Generate report with AI chat context only. Signals section uses AI response as source. |
| 100+ opportunities | Pre-filter: take top 40 by relevance. LLM selects top 3-6 from those. |
| No procurement score | Omit from Buyer Snapshot and Gameplan. |
| Contact has no email AND no phone | Exclude from table. |
| AI chat times out | Use opportunity data + profile data only. Note in footer: "AI analysis unavailable." |
| Ambiguous buyer match | Use first match. Include `alternative_matches` in a hidden metadata field for QA review. |
| Tier 1 request | Skip Relevancy Analysis, Gameplan, Contacts Table. Generate Header + Buyer Snapshot + Signal Bullets + Footer. |

---

## Token Budget Estimates

| Section | Input tokens (approx) | Output tokens (approx) |
|---|---|---|
| Buyer Snapshot | ~2K (profile JSON) | ~150 |
| Relevancy Analysis | ~8K (AI chat + opportunities + profile) | ~400 |
| Gameplan | ~6K (contacts + AI chat + signals) | ~600 |
| Key Contacts Table | ~4K (contacts JSON) | ~300 |
| Strategic Signals | ~8K (opportunities + AI chat) | ~800 |
| **Total (Tier 3)** | **~28K input** | **~2,250 output** |
| **Total (Tier 1)** | **~10K input** | **~500 output** |

These fit comfortably within a single Claude Sonnet context. No chunking needed.

---

## Quality Checklist (Post-Generation)

Before returning the report, validate:

- [ ] Buyer name in header matches resolved buyer (not the search query)
- [ ] Every bullet in Relevancy Analysis references a specific signal or initiative
- [ ] Primary DM has a verified email
- [ ] Outreach script opens with buyer's situation, not vendor pitch
- [ ] No contact rows with both email AND phone as "—"
- [ ] Signal paragraphs include dates or timeframes
- [ ] No hallucinated dollar amounts or dates not present in source data
- [ ] Procurement score matches between Buyer Snapshot and Gameplan
- [ ] Footer month/year matches current date
