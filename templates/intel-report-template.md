# Template: Intel Report Page Structure

This is the structural template the Datagen agent uses to generate each intel report. It defines the section order, content blocks, and variable slots. The actual rendering depends on the platform (Notion, Super.so, Webflow).

Section order is modeled on the CCC/VMock sample — see [data/sample-intel.md](../data/sample-intel.md) Example 7 for a fully populated reference.

---

## Page Structure (Section Order)

```
┌─────────────────────────────────────────┐
│  HEADER                                 │
│  Report title + prospect product name   │
├─────────────────────────────────────────┤
│  BUYER SNAPSHOT                         │
│  Callout card: org name, type, state,   │
│  city, enrollment/size, procurement     │
│  score, fiscal year, website, phone,    │
│  parent org                             │
├─────────────────────────────────────────┤
│  RELEVANCY ANALYSIS                     │
│  Use case archetype + 3-4 bullets       │
│  connecting signals to prospect fit     │
├─────────────────────────────────────────┤
│  GAMEPLAN                               │
│  Primary DM target + why this contact   │
│  Secondary contacts + outreach script   │
│  Procurement path + co-op/threshold/    │
│  resellers                              │
├─────────────────────────────────────────┤
│  KEY CONTACTS TABLE                     │
│  Full table of relevant contacts with   │
│  name, title, email, phone, verified    │
├─────────────────────────────────────────┤
│  RECENT STRATEGIC SIGNALS               │
│  Top 3-6 signals with contextual        │
│  paragraphs (not just bullets)          │
├─────────────────────────────────────────┤
│  FOOTER                                 │
│  Starbridge branding + data source note │
└─────────────────────────────────────────┘
```

---

## Section Details

### Header

```markdown
# {report_emoji} {buyer_name} — Intelligence Report for {prospect_product}
```

**Variables:**
- `{report_emoji}` — 📊 (default)
- `{buyer_name}` — buyer/account name (e.g., "California Community Colleges")
- `{prospect_product}` — the vendor's product name (e.g., "VMock")

---

### Buyer Snapshot

Rendered as a callout/aside block with key account attributes at a glance.

```markdown
> {buyer_type_emoji}
>
> **{buyer_name}** | {buyer_type_label}
>
> **State:** {buyer_state} | **City:** {buyer_city} | **{size_label}:** {size_value}
>
> **Procurement Score:** {procurement_score}/100 | **Fiscal Year Start:** {fiscal_year_start}
>
> **Website:** [{buyer_website_display}]({buyer_website_url}) | **Phone:** {buyer_phone}
>
> **Parent Org:** {parent_org}
```

**Variables:**
- `{buyer_type_emoji}` — visual indicator by type:
  - 🏛️ Higher Education / State Agency
  - 🏫 School District
  - 🏙️ City / Municipality
  - 🏢 County
- `{buyer_name}` — full account name
- `{buyer_type_label}` — human-readable type (e.g., "Higher Education System", "School District")
- `{buyer_state}`, `{buyer_city}` — location
- `{size_label}` — context-appropriate size metric label ("Enrollment", "Population", "Employees")
- `{size_value}` — the number (e.g., "2,108,927 students")
- `{procurement_score}` — 0-100 score indicating procurement difficulty
- `{fiscal_year_start}` — e.g., "July 1"
- `{buyer_website_display}` — display text for link (e.g., "cccco.edu")
- `{buyer_website_url}` — full URL
- `{buyer_phone}` — main phone number
- `{parent_org}` — parent organization if applicable (e.g., "State of California"), or omit row

---

### Relevancy Analysis

Opens with a use case archetype callout, followed by 3-4 bullets connecting specific signals to prospect fit.

```markdown
## 🎯 Relevancy Analysis

> 🔥
>
> **Use Case Archetype:** {use_case_archetype}

{relevancy_paragraph}

- {relevancy_bullet_1}
- {relevancy_bullet_2}
- {relevancy_bullet_3}
```

**Variables:**
- `{use_case_archetype}` — one-line archetype label (e.g., "Scale & Equity — Career Services Access")
- `{relevancy_paragraph}` — optional 1-2 sentence intro connecting the buyer's strategic context to the prospect's product
- `{relevancy_bullet_1..N}` — LLM-generated bullets. Each should:
  - Reference a **specific signal or initiative** (not generic claims)
  - Explain **why it creates an opening** for the prospect's product
  - Use the **buyer's own language** where possible (board resolutions, initiative names)

**Quality bar:** Each bullet should give a BDR something concrete to say on a call. "They're investing in technology" is too vague. "The Board of Governors is prioritizing CTE pathways with a Senior Advisor specifically focused on Workforce Development and GenAI" is specific and usable.

---

### Gameplan

The actionable section — who to contact, what to say, and how to buy.

```markdown
## 📋 Gameplan

> 🎯
>
> **Primary DM Target:** {primary_dm_name} — {primary_dm_title}
>
> **Email:** [{primary_dm_email}](mailto:{primary_dm_email})

**Why this contact:** {dm_rationale}

**Secondary contacts:**

- **{secondary_dm_1_name}** — {secondary_dm_1_title} ([{secondary_dm_1_email}](mailto:{secondary_dm_1_email}))
- **{secondary_dm_2_name}** — {secondary_dm_2_title} ([{secondary_dm_2_email}](mailto:{secondary_dm_2_email}))

### Outreach Script

"{outreach_script}"

### Procurement Path

**Recommended:** {procurement_recommendation}

**Sole Source Threshold:** {sole_source_threshold}

**Key Resellers:** {resellers}

**Procurement Score:** {procurement_score}/100 — {procurement_score_note}
```

**Variables:**
- `{primary_dm_name}`, `{primary_dm_title}`, `{primary_dm_email}` — top contact
- `{dm_rationale}` — 1-2 sentences explaining why this person is the right entry point. Should reference their role's overlap with the prospect's product.
- `{secondary_dm_N_name}`, `{secondary_dm_N_title}`, `{secondary_dm_N_email}` — 2-3 alternate contacts
- `{outreach_script}` — ready-to-use 2-3 sentence talk track. Should lead with the buyer's situation, not the prospect's product. Prefer a question or observation over a pitch statement.
- `{procurement_recommendation}` — recommended procurement channel (e.g., "Cooperative purchasing via CollegeBuys")
- `{sole_source_threshold}` — dollar threshold for sole source purchasing (e.g., "<$114,500 per district")
- `{resellers}` — comma-separated list of relevant resellers (e.g., "CDW-G, SHI International, Carahsoft")
- `{procurement_score}` — same score as Buyer Snapshot
- `{procurement_score_note}` — brief interpretation (e.g., "moderate difficulty. Co-op route strongly recommended.")

---

### Key Contacts Table

Full table of relevant contacts at the buyer organization.

```markdown
## 👥 Key Contacts

| **Name** | **Title** | **Email** | **Phone** | **Verified** |
| --- | --- | --- | --- | --- |
| {contact_1_name} | {contact_1_title} | {contact_1_email} | {contact_1_phone} | {contact_1_verified} |
| {contact_2_name} | {contact_2_title} | {contact_2_email} | {contact_2_phone} | {contact_2_verified} |
| ... | ... | ... | ... | ... |

*{total_contacts} total contacts available in Starbridge. Showing top matches for {prospect_product} engagement.*
```

**Variables per row:**
- `{contact_N_name}` — full name
- `{contact_N_title}` — job title (preserve non-standard SLED titles as-is)
- `{contact_N_email}` — email or "—" if unavailable
- `{contact_N_phone}` — phone or "—" if unavailable
- `{contact_N_verified}` — ✅ if verified, "—" if not. Do not include unverified contacts with zero contact info (no email AND no phone) — either enrich them or drop them.

**Row count:** 5-10 contacts, prioritized by relevance to the prospect's product.

**Footer note variables:**
- `{total_contacts}` — total contacts Starbridge has for this buyer
- `{prospect_product}` — reused from header

---

### Recent Strategic Signals

Top 3-6 signals, each with a heading and a contextual paragraph. These are richer than the SLED Signal Bullets — each signal gets a full paragraph explaining what it is, what it means, and how the prospect could leverage it.

```markdown
## 📡 Recent Strategic Signals

### {signal_1_title}

{signal_1_paragraph}

### {signal_2_title}

{signal_2_paragraph}

### {signal_3_title}

{signal_3_paragraph}
```

**Variables per signal:**
- `{signal_N_title}` — short descriptive title (e.g., "Vision 2030 — Common Cloud Data Platform")
- `{signal_N_paragraph}` — 2-4 sentence contextual summary. Should:
  - State what happened or what's being planned
  - Explain what it means for the buyer's organization
  - Connect it to the prospect's product where natural (not forced)

**Signal selection:** LLM selects the top 3-6 from all available signals, ranked by relevance to the prospect's product. Prefer signals that:
1. Create a procurement window (contract expirations, budget events, RFPs)
2. Show strategic alignment (board discussions, initiatives matching the product)
3. Indicate technology adoption readiness (modernization projects, AI adoption)

---

### Footer

```markdown
---

*Generated Starbridge Intelligence {report_month} {report_year}*

*Data source: Starbridge buyer profile, contacts, AI analysis, and opportunity database*
```

**Variables:**
- `{report_month}` — e.g., "February"
- `{report_year}` — e.g., "2026"

---

## Notion Block Mapping

For V1 (Notion), each section maps to Notion API block types:

| Report Section | Notion Block Type |
|---|---|
| Header | `heading_1` |
| Buyer Snapshot | `callout` (with buyer type emoji as icon) |
| Relevancy Analysis heading | `heading_1` |
| Use Case Archetype | `callout` (🔥 icon) |
| Relevancy bullets | `paragraph` (intro) + `bulleted_list_item` (bullets) |
| Gameplan heading | `heading_1` |
| Primary DM Target | `callout` (🎯 icon) |
| DM rationale + secondary contacts | `paragraph` |
| Outreach Script subheading | `heading_2` + `quote` |
| Procurement Path subheading | `heading_2` + `paragraph` |
| Key Contacts heading | `heading_1` |
| Contacts table | `table` (5 columns) |
| Contacts footer note | `paragraph` (italic) |
| Recent Strategic Signals heading | `heading_1` |
| Per signal | `heading_2` (title) + `paragraph` (body) |
| Footer divider | `divider` |
| Footer text | `paragraph` (italic) |

---

## Naming Convention

Report pages should follow a consistent naming pattern for organization and lookup:

```
{report_emoji} {buyer_name} — Intelligence Report for {prospect_product}
```

Examples:
- `📊 California Community Colleges — Intelligence Report for VMock`
- `📊 Austin ISD — Intelligence Report for AttendancePoint`
- `📊 City of Phoenix — Intelligence Report for GovTech Solutions`

URL slug (for Super.so/Webflow):
```
{buyer-slug}-{prospect-slug}-{date}
```
Example: `california-community-colleges-vmock-2026-02-10`

---

## Tier Mapping

The template above represents a **Tier 3** (full) report. Lower tiers use subsets:

| Section | Tier 1 | Tier 2 | Tier 3 |
|---|---|---|---|
| Header | ✅ | ✅ | ✅ |
| Buyer Snapshot | ✅ (basic) | ✅ (full) | ✅ (full) |
| Relevancy Analysis | — | — | ✅ |
| Gameplan | — | — | ✅ |
| Key Contacts | — | ✅ (DM card only) | ✅ (full table) |
| Recent Strategic Signals | ✅ (bullets) | ✅ (bullets) | ✅ (full paragraphs) |
| Footer | ✅ | ✅ | ✅ |
