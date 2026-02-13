# Intel Report V2 — Target Format & Generation

## Design Principles

The intel report is a **sales asset sent directly to SLED prospects**. It must:

1. **Feel like a gift, not a pitch** — prospects should think "this is useful" not "this is a sales email"
2. **Be source-backed** — Starbridge's moat is primary-source data (board transcripts, contracts, FOIA records). The report should show receipts, not just claims.
3. **Be deterministic** — same inputs → same output. No randomness from AI generation in layout or structure.
4. **Be scannable** — SLED buyers are busy. Key info must be visible in 10 seconds.
5. **Be forwardable** — prospects forward these to committees, CIOs, superintendents. The report must stand alone without explanation.
6. **Be branded** — consistent Starbridge look and feel. Nastia owns the design template.

## Platform Decision

{{TBD: Notion vs. Super.so vs. Webflow — needs Nastia/Henry alignment before V1 ships}}

| Option | Pros | Cons | Best For |
|---|---|---|---|
| **Notion** | Fastest to implement programmatically. Rich content blocks. Free. Easy to iterate. | Notion URLs look unprofessional. Limited branding. "Notion" in the URL signals internal tooling, not polished deliverable. | V1 MVP — get something live fast |
| **Super.so** (Notion + custom domain) | Notion speed + custom domain (intel.starbridge.ai) + CSS overrides for branding. Notion as CMS, Super as presentation. | Additional tool ($12-16/mo). Some styling limitations. Adds a dependency. | V1.5 — quick branding upgrade |
| **Webflow** (CMS) | Full branding control. Professional URLs. Nastia can design the template. CMS API for programmatic creation. | More setup time. Requires Webflow CMS collection structure. {{UNKNOWN: does Starbridge have a Webflow account?}} Template work needed from Nastia. | V2 — polished, branded deliverable |
| **Custom HTML** | Total control. No third-party dependency. Can host on Starbridge's own infra. | Slower to build. Need hosting. More engineering than GTM work. | V3 — if scale demands it |

**Recommendation**: Start with Notion (V1), upgrade to Super.so for quick branding (V1.5), migrate to Webflow when Nastia's template is ready (V2). This avoids blocking V1 on design decisions.

## Report Structure (Section by Section)

Section order and structure are modeled on the CCC/VMock Notion sample (see [data/sample-intel.md](../../data/sample-intel.md) Example 7). Full template with variables is in [templates/intel-report-template.md](../../templates/intel-report-template.md).

### 1. Header

```
📊 {BuyerName} — Intelligence Report for {ProspectProduct}
```

- Report title includes both the buyer (SLED account) and prospect (vendor/product)
- Starbridge logo: {{UNKNOWN: do we have an SVG/PNG asset? Ask Nastia}}

### 2. Buyer Snapshot

Callout block with key account attributes at a glance. Replaces the old "Buyer Profile" table — same data, more scannable.

```
🏛️ California Community Colleges (CCC) | Higher Education System

State: California | City: Sacramento | Enrollment: 2,108,927 students
Procurement Score: 58/100 | Fiscal Year Start: July 1
Website: cccco.edu | Phone: (916) 445-8752
Parent Org: State of California
```

**Data sources:** Starbridge API (buyer attributes) + Supabase (procurement score). V1 may use partial data if SB API isn't available yet.

### 3. Relevancy Analysis (Tier 3)

Two parts:
1. **Use Case Archetype** — one-line classification (e.g., "Scale & Equity — Career Services Access") rendered as a callout
2. **Relevancy bullets** — 3-4 LLM-generated bullets connecting specific signals/initiatives to the prospect's product

**Quality bar:** Each bullet must reference something concrete (a named initiative, a board resolution, a specific infrastructure project) — not generic statements about "investing in technology." The CCC sample connects Vision 2030, the Common Cloud Data Platform, and the equity gap for rural colleges. That's the standard.

### 4. Gameplan (Tier 3)

The actionable section — who to contact, what to say, and how to buy. Three sub-sections:

**Primary DM Target** — callout with name, title, email. Includes a "Why this contact" rationale explaining the overlap between their role and the prospect's product.

**Secondary contacts** — 2-3 alternate contacts with name, title, email.

**Outreach Script** — ready-to-use 2-3 sentence talk track. Should lead with the buyer's situation (not the vendor's product). Prefer questions or observations over pitch statements.

**Procurement Path** — recommended procurement channel, sole source threshold, key resellers, and procurement score interpretation.

**Example (from CCC/VMock):**
```
Recommended: Cooperative purchasing via CollegeBuys (Foundation for California Community Colleges)
Sole Source Threshold: <$114,500 per district
Key Resellers: CDW-G, SHI International, Carahsoft, Connection (GovConnection)
Procurement Score: 58/100 — moderate difficulty. Co-op route strongly recommended.
```

### 5. Key Contacts Table

Full table of 5-10 relevant contacts: Name, Title, Email, Phone, Verified status.

**Rules:**
- Do not include contacts with zero enrichment (no email AND no phone AND unverified) — either enrich them or drop them
- Preserve non-standard SLED titles as-is (e.g., "Director (Commissioner) of Public Works")
- Footer note: "{N} total contacts available in Starbridge. Showing top matches for {ProspectProduct} engagement."

### 6. Recent Strategic Signals

Top 3-6 signals, each with a heading and a 2-4 sentence contextual paragraph. These are richer than the SLED Signal Bullets used in the old format — each signal explains what's happening, what it means, and how the prospect could connect to it.

**Example (from CCC/VMock):**
```
## Vision 2030 — Common Cloud Data Platform

The Board of Governors has approved a "demonstration project" to create a shared
data infrastructure across all 116 colleges. This platform will enable near-real-time
student analytics and automated data sharing — a natural integration point for
VMock's AI career tools.
```

**Signal selection criteria (LLM-ranked):**
1. Creates a procurement window (contract expirations, budget events, RFPs)
2. Shows strategic alignment (board discussions, initiatives matching the product)
3. Indicates technology adoption readiness (modernization projects, AI adoption)

### 7. Footer

```
Generated Starbridge Intelligence February 2026
Data source: Starbridge buyer profile, contacts, AI analysis, and opportunity database
```

{{TBD: include a CTA? "Want to see more signals? Book a demo." — or keep it pure intel?}}
{{TBD: include a disclaimer about data freshness/accuracy?}}

## Screenshot Generation

BDRs include a screenshot of the report in their payload email (visual hook before the prospect clicks). This needs to be automated.

{{TBD: screenshot generation approach:}}

| Option | How | Complexity |
|---|---|---|
| **Puppeteer/Playwright** | Headless browser renders the page, takes a screenshot | Medium — need a rendering service |
| **Notion API export** | Notion has limited export capabilities | Low quality, limited control |
| **Manual** | BDR takes a screenshot themselves | Zero automation, but works for V1 |
| **OG image / social preview** | Set up Open Graph meta tags so link previews in email show a designed image | Medium — works for email clients that render previews |

**Recommendation for V1**: Manual screenshots. BDR opens the report link, takes a screenshot, pastes in email. Automate in V2.

## Template System

Reports must be **deterministic** — the template defines the structure, and data fills the slots. No AI-generated layout.

### Template Variables

Full variable reference is in [templates/intel-report-template.md](../../templates/intel-report-template.md). Summary:

```
# Header
{report_emoji}           — 📊 (default)
{buyer_name}             — Account name (from Starbridge / Clay)
{prospect_product}       — Vendor's product name (from Smartlead / Clay)

# Buyer Snapshot
{buyer_type_emoji}       — 🏛️/🏫/🏙️/🏢 by type
{buyer_type_label}       — Human-readable type
{buyer_state}, {buyer_city} — Location
{size_label}             — "Enrollment" / "Population" / "Employees"
{size_value}             — Size number
{procurement_score}      — 0-100
{fiscal_year_start}      — e.g., "July 1"
{buyer_website_display}  — Display URL
{buyer_website_url}      — Full URL
{buyer_phone}            — Main phone
{parent_org}             — Parent org (optional)

# Relevancy Analysis (Tier 3)
{use_case_archetype}     — One-line archetype (LLM-generated)
{relevancy_paragraph}    — Intro paragraph (LLM-generated)
{relevancy_bullet_1..N}  — 3-4 analysis bullets (LLM-generated)

# Gameplan (Tier 3)
{primary_dm_name}        — Primary DM name
{primary_dm_title}       — Primary DM title
{primary_dm_email}       — Primary DM email
{dm_rationale}           — Why this contact (LLM-generated)
{secondary_dm_N_*}       — 2-3 secondary contacts
{outreach_script}        — Talk track (LLM-generated)
{procurement_recommendation} — Procurement channel
{sole_source_threshold}  — Dollar threshold
{resellers}              — Key reseller list
{procurement_score_note} — Score interpretation

# Key Contacts Table
{contact_N_name}         — Contact name
{contact_N_title}        — Contact title
{contact_N_email}        — Contact email
{contact_N_phone}        — Contact phone
{contact_N_verified}     — ✅ or —
{total_contacts}         — Total in Starbridge

# Recent Strategic Signals
{signal_N_title}         — Signal heading
{signal_N_paragraph}     — 2-4 sentence contextual summary

# Footer
{report_month}           — e.g., "February"
{report_year}            — e.g., "2026"
```

### Notion Page Generation (V1)

Using the Notion API, the Datagen agent creates a page with blocks. Block mapping reference is in [templates/intel-report-template.md](../../templates/intel-report-template.md#notion-block-mapping).

```python
# {{UNVERIFIED: pseudocode — actual implementation depends on Notion API version and workspace setup}}

children = []

# 1. Header
children.append(heading_1(f"📊 {buyer_name} — Intelligence Report for {prospect_product}"))

# 2. Buyer Snapshot
children.append(callout(
    icon=buyer_type_emoji,
    rich_text=f"**{buyer_name}** | {buyer_type_label}\n\n"
              f"**State:** {buyer_state} | **City:** {buyer_city} | **{size_label}:** {size_value}\n\n"
              f"**Procurement Score:** {procurement_score}/100 | **Fiscal Year Start:** {fiscal_year_start}\n\n"
              f"**Website:** {buyer_website} | **Phone:** {buyer_phone}"
))

# 3. Relevancy Analysis (Tier 3 only)
if tier >= 3:
    children.append(heading_1("🎯 Relevancy Analysis"))
    children.append(callout(icon="🔥", rich_text=f"**Use Case Archetype:** {use_case_archetype}"))
    children.append(paragraph(relevancy_paragraph))
    for bullet in relevancy_bullets:
        children.append(bulleted_list_item(bullet))

# 4. Gameplan (Tier 3 only)
if tier >= 3:
    children.append(divider())
    children.append(heading_1("📋 Gameplan"))
    children.append(callout(
        icon="🎯",
        rich_text=f"**Primary DM Target:** {primary_dm_name} — {primary_dm_title}\n\n"
                  f"**Email:** {primary_dm_email}"
    ))
    children.append(paragraph(f"**Why this contact:** {dm_rationale}"))
    children.append(paragraph(f"**Secondary contacts:**"))
    for dm in secondary_dms:
        children.append(bulleted_list_item(f"**{dm.name}** — {dm.title} ({dm.email})"))
    children.append(heading_2("Outreach Script"))
    children.append(quote(outreach_script))
    children.append(heading_2("Procurement Path"))
    children.append(paragraph(
        f"**Recommended:** {procurement_recommendation}\n\n"
        f"**Sole Source Threshold:** {sole_source_threshold}\n\n"
        f"**Key Resellers:** {resellers}\n\n"
        f"**Procurement Score:** {procurement_score}/100 — {procurement_score_note}"
    ))

# 5. Key Contacts Table (Tier 2+)
if tier >= 2:
    children.append(divider())
    children.append(heading_1("👥 Key Contacts"))
    children.append(table(
        headers=["Name", "Title", "Email", "Phone", "Verified"],
        rows=[[c.name, c.title, c.email, c.phone, c.verified] for c in contacts]
    ))
    children.append(paragraph(f"_{total_contacts} total contacts available in Starbridge._", italic=True))

# 6. Recent Strategic Signals
children.append(divider())
children.append(heading_1("📡 Recent Strategic Signals"))
for signal in signals:
    children.append(heading_2(signal.title))
    children.append(paragraph(signal.paragraph))

# 7. Footer
children.append(divider())
children.append(paragraph(f"_Generated Starbridge Intelligence {report_month} {report_year}_", italic=True))
children.append(paragraph("_Data source: Starbridge buyer profile, contacts, AI analysis, and opportunity database_", italic=True))

# Create the page
page = notion.pages.create(
    parent={"database_id": INTEL_REPORTS_DB_ID},
    properties={"Name": {"title": [{"text": {"content": f"📊 {buyer_name} — Intelligence Report for {prospect_product}"}}]}},
    children=children
)
```

## Design Dependencies

| Dependency | Who | Status | Impact |
|---|---|---|---|
| Brand assets (logo, colors, fonts) | Nastia | {{UNKNOWN: have these been shared?}} | Needed for any branded output |
| Report template design | Nastia | {{UNKNOWN: has she started?}} | Needed for V2 (Webflow) |
| Webflow account + CMS setup | Nastia / Engineering | {{UNKNOWN: does Starbridge have Webflow?}} | Needed for V2 |
| Notion workspace for reports | Jeremy / team | {{TBD: use Starbridge's Notion or create a dedicated workspace?}} | Needed for V1 |
| Custom domain (intel.starbridge.ai) | Engineering | {{UNKNOWN: is this available?}} | Needed for Super.so or Webflow |

## Quality Benchmarks

The new report must be **at least as good as** current Gamma output on day 1, and measurably better by V2.

| Dimension | Gamma (Baseline) | V1 Target | V2 Target |
|---|---|---|---|
| Signal count | 5-12 per report | 5-10 (curated) | 5-10 (curated + enriched) |
| Signal quality | Raw bullets via Gemini | LLM-ranked + contextual | + source links + related data |
| DM info | Not in report (Slack only) | Not in report | In report (contact card) |
| Budget data | Not included | Not included | Included |
| Branding | Gamma default | Minimal (Notion) | Full Starbridge brand |
| Determinism | Non-deterministic | Deterministic template | Deterministic template |
| Generation time | 15-60 min (manual) | < 30 seconds | < 15 seconds |
| Consistency | Variable | Consistent template | Consistent + branded |

## Test Collateral Ideas (From 2/4 Onboarding)

Henry mentioned wanting test collateral to send post-positive response. Ideas discussed:
- GIF with link to the intel report {{UNVERIFIED: "Gif with link to CSV" mentioned in notes — clarify what this means}}
- {{UNKNOWN: other collateral formats being considered}}

These could supplement the report link in the BDR's payload email — a visual hook that makes the prospect want to click.
