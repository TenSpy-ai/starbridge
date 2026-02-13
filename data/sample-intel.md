# Sample Intel — Redacted Examples

Real patterns from #intent-reports Slack dispatches and delivered intel. Used as reference for:
- LLM prompt engineering (few-shot examples)
- Report template validation
- Quality benchmarking ("at least as good as" current output)

Names and domains are redacted. Signal content is preserved as-is since it's derived from public procurement records.

---

## Example 1: Tier 2 — Report + DM Card

**Company type**: School District (Texas)
**Prospect product**: Compliance/inspection technology

### Slack Dispatch (Message 2)

```
@[BDR] — custom intel is ready for [ProspectName] of [CompanyName], [email].

Gamma Link: [URL]

Custom Intel:
- Name: [DMName]
- Title: Director of Special Education
- Email: [dm_email]
- Phone: [dm_phone]
```

**What this shows**: Clean Tier 2 delivery. DM card is specific (title, email, phone). Report link is the centerpiece. No relevancy analysis (that's Tier 3).

---

## Example 2: Tier 2 — Report + DM Card (Multi-Contact)

**Company type**: School District (Texas)
**Prospect product**: Health services technology

### Slack Dispatch (Message 2)

```
@[BDR] — custom intel is ready for [ProspectName] of [CompanyName], [email].

Gamma Link: [URL]

Custom Intel:
- Name: [DMName]
- Title: Health Services Director
- Email: [dm_email]
- Phone: [dm_phone]
```

**What this shows**: Same Tier 2 pattern. Title specificity matters — "Health Services Director" tells the BDR exactly which conversation to have.

---

## Example 3: Tier 2 — Report + DM Card (Municipal)

**Company type**: City/Municipality
**Prospect product**: Infrastructure compliance

### Slack Dispatch (Message 2)

```
@[BDR] — custom intel is ready for [ProspectName] of [CompanyName], [email].

Gamma Link: [URL]

Custom Intel:
- Name: [DMName]
- Title: Director (Commissioner) of Public Works
- Email: [dm_email]
- Direct Phone: [dm_direct_phone]
```

**What this shows**: Title includes parenthetical "(Commissioner)" — titles in SLED are non-standard. The LLM needs to preserve unusual title formats, not normalize them. Also note "Direct Phone" vs. "Phone" — both fields may be present.

---

## Example 4: Tier 3 — Full Intel Package (Attendance Technology)

**Company type**: School District
**Prospect product**: Attendance tracking platform

### Slack Dispatch (Message 2)

```
@[BDR] — custom intel is ready for [ProspectName] of [CompanyName], [email].

Gamma Link: [URL]

Custom Intel:
- Name: [DMName]
- Title: Deputy Superintendent
- Email: [dm_email]
- Direct Phone: [dm_direct_phone]

IR Notes:
- Relevancy: Board signal shows K-1 chronic absenteeism initiative; 
  "Attendance Awareness" campaign active; currently using public information 
  officers + social media campaigns.
- Pitch angle: Lead with the district's own language about "Attendance Awareness" — 
  show how [CompanyName]'s platform operationalizes what they're already trying 
  to do manually.
- Gameplan: Reference the board discussion, mention the specific initiative, offer 
  to show how similar districts automated attendance tracking.
```

**What this shows**: This is the gold standard. The Tier 3 analysis:
- References a **specific board signal** (not generic "they discussed education")
- Names a **specific initiative** ("Attendance Awareness")
- Describes their **current approach** (manual — PIOs + social media)
- Connects **prospect's product** to the **buyer's language** (not vendor jargon)
- Gives the BDR a **concrete opening** ("reference the board discussion")

This is what the LLM needs to replicate in V3.

---

## Example 5: Dispatch with Operator Context (Scheduling)

### Slack Dispatch (Message 1)

```
@[BDR] — new positive response from [ProspectName] of [CompanyName], [email]!

Custom intel and intent report coming your way shortly.

"[Reply quote about being interested in seeing more information]"

Notes: Availability 12:30–3:00 EST
```

**What this shows**: Operator extracted scheduling preferences from the reply text and added them as notes. The automated pipeline should either:
- Parse scheduling info from reply text via LLM
- Surface the raw reply text so operators can add context manually

---

## Example 6: Dispatch with Operator Context (Territory)

### Slack Dispatch (Message 1)

```
@[BDR] — new positive response from [ProspectName] of [CompanyName], [email]!

Custom intel and intent report coming your way shortly.

Notes: Not CA; focus on MD/WV/VA/TN/KY
```

**What this shows**: Territory scoping. The prospect's product isn't relevant to California — BDR should focus the intel on Mid-Atlantic/Southeast states. This kind of context is hard to automate — it requires knowing the prospect's business geography.

---

## Example 7: Tier 3 — Full Intelligence Report (Notion Format)

**Company type**: Higher Education System (California)
**Prospect product**: VMock (AI career services platform)
**Source**: Notion sample — canonical Tier 3 reference for the updated report template

This is the gold standard for the new report format. All sections are populated. Used as the reference when building [templates/intel-report-template.md](../templates/intel-report-template.md).

### Full Report

---

# 📊 California Community Colleges — Intelligence Report for VMock

### Buyer Snapshot

> 🏛️
>
> **California Community Colleges (CCC)** | Higher Education System
>
> **State:** California | **City:** Sacramento | **Enrollment:** 2,108,927 students
>
> **Procurement Score:** 58/100 | **Fiscal Year Start:** July 1
>
> **Website:** [cccco.edu](http://cccco.edu) | **Phone:** (916) 445-8752
>
> **Parent Org:** State of California

---

### 🎯 Relevancy Analysis

> 🔥
>
> **Use Case Archetype:** Scale & Equity — Career Services Access

The CCC system's **Vision 2030** framework explicitly targets workforce development and student success outcomes across all 116 community colleges. Several signals point to a strong VMock fit:

- The Board of Governors is prioritizing **Career Technical Education (CTE)** pathways and workforce alignment, with a Senior Advisor to the Chancellor specifically focused on "Workforce Development, Strategic Partnerships, and GenAI."
- The system is investing in a **Common Cloud Data Platform** designed to unify student analytics. This infrastructure would make VMock integration seamless — plugging AI-powered career tools into a centralized student data layer.
- The Chancellor's Office has identified that decentralized, college-level systems create inequity: smaller rural colleges lack the resources to build modern career services at scale. VMock's platform-as-a-service model solves this by giving every college the same AI career tools regardless of local IT capacity.

---

### 📋 Gameplan

> 🎯
>
> **Primary DM Target:** Don Harjo Daves-Rougeaux — Senior Advisor to the Chancellor on Workforce Development, Strategic Partnerships, and GenAI
>
> **Email:** ddaves-rougeaux@cccco.edu

**Why this contact:** His role literally spans the three pillars that VMock addresses — workforce outcomes, partnership procurement, and GenAI adoption. He's the bridge between the Chancellor's strategic vision and the technology stack that delivers it.

**Secondary contacts:**

- **Anthony Cordova** — Vice Chancellor, Workforce and Economic Development (acordova@cccco.edu)
- **Allison Beer** — Dean of Student Services (abeer@cccco.edu)
- **Gary W. Adams** — Dean, Workforce and Economic Development (gadams@cccco.edu)

#### Outreach Script

"I saw CCC is standing up a common cloud data platform across all 116 colleges — are you looking at career services tooling as part of that rollout? VMock could plug directly into that infrastructure as the AI career acceleration layer, so every college gets the same resume optimization and pathway mapping without building it locally. Curious whether that's on the roadmap or if workforce dev is being handled separately."

#### Procurement Path

**Recommended:** Cooperative purchasing via **CollegeBuys** (Foundation for California Community Colleges). This is CCC's preferred procurement channel for system-wide technology agreements.

**Sole Source Threshold:** <$114,500 per district

**Key Resellers:** CDW-G, SHI International, Carahsoft, Connection (GovConnection)

**Procurement Score:** 58/100 — moderate difficulty. Co-op route strongly recommended.

---

### 👥 Key Contacts

| **Name** | **Title** | **Email** | **Phone** | **Verified** |
| --- | --- | --- | --- | --- |
| Don Harjo Daves-Rougeaux | Sr. Advisor — Workforce, Partnerships & GenAI | ddaves-rougeaux@cccco.edu | — | ✅ |
| Anthony Cordova | Vice Chancellor, Workforce & Economic Dev | acordova@cccco.edu | (916) 327-4592 | ✅ |
| Allison Beer | Dean of Student Services | abeer@cccco.edu | (916) 323-9478 | ✅ |
| Gary W. Adams | Dean, Workforce & Economic Development | gadams@cccco.edu | (916) 322-7079 | ✅ |
| Sonya Christian | Chancellor | sonya.christian@cccco.edu | (916) 445-8752 | ✅ |
| Christopher Ferguson | Exec VP of Finance & Strategic Initiatives | chris.ferguson@cccco.edu | (916) 324-9508 | ✅ |

*45 total contacts available in Starbridge. Showing top matches for VMock engagement.*

---

### 📡 Recent Strategic Signals

#### Vision 2030 — Common Cloud Data Platform

The Board of Governors approved a "demonstration project" in November 2025 to create a shared data infrastructure across all 116 colleges. This platform will enable near-real-time student analytics and automated data sharing — a natural integration point for VMock's AI career tools. *(Board of Governors meeting, November 13-14, 2025)*

#### CCCApply Modernization

A major digital transformation to upgrade the system-wide application portal, approved in the FY2025-26 technology roadmap. Goal: reduce student "drop-off" rates through streamlined workflows and better outreach analytics. VMock could complement this by adding career pathway discovery to the onboarding experience. *(Chancellor's Office technology review, January 2026)*

#### Automated Identity Verification & Fraud Prevention

CCC is deploying AI-powered spam filters and identity verification to combat enrollment fraud, initiated Q4 2025. This signals comfort with AI-powered tooling at the system level — reducing the "AI adoption friction" barrier for VMock. *(Board agenda item, December 2025)*

#### ERP & SIS Modernization

Transitioning from fragmented, college-level systems to a collaborative model, with a planning committee formed in October 2025. This modernization creates the technical foundation for system-wide tool deployments like VMock. *(Strategic Planning Committee, October 2025)*

---

*Generated Starbridge Intelligence February 2026*

*Data source: Starbridge buyer profile, contacts, AI analysis, and opportunity database*

---

**What this shows**: The full Tier 3 format with all sections populated. Key patterns:
- **Buyer Snapshot** as a callout card (not a table) — scannable in 5 seconds
- **Relevancy Analysis** builds an argument, not just a summary — connects specific initiatives to specific product capabilities
- **Gameplan** gives the BDR everything: who to call, why them, what to say, and how to buy
- **Contacts table** with verification status — BDR knows which contacts are confirmed
- **Signals as paragraphs** (not bullets) — each signal gets enough context to be conversational on a call
- **Procurement Path** is a differentiator — most BDRs never have this intel

---

## LLM Few-Shot Template

These examples can be adapted into few-shot prompts for the Datagen LLM processing step. Structure:

```
EXAMPLE INPUT:
Domain: [domain]
Signal count: 8
Signals:
1. Contract expiration: LMS platform ($250K, expiring June 2026)
2. Board meeting: Discussed chronic absenteeism initiative (Jan 2026)
3. Budget: $1.2M IT infrastructure allocation (FY2026)
4. Purchase order: Chromebook fleet ($800K)
5. Board meeting: Strategic plan mentions "digital transformation" (Dec 2025)
6. Leadership change: New CIO appointed (Jan 2026)
7. Conference: CTO attending CoSN 2026
8. Grant: $5M ESSER III for learning recovery

EXAMPLE OUTPUT:
Top 5 signals selected: [1, 2, 3, 6, 8]

SLED Signal Bullets:
1. "Austin ISD's LMS platform contract expires in 5 months ($250K annual). 
    Districts typically begin vendor evaluation 90-120 days before expiration, 
    putting the procurement timeline right now."
2. "The board discussed chronic absenteeism in K-1, with an active 'Attendance 
    Awareness' initiative. This signals organizational priority and potential 
    budget allocation for attendance solutions."
3. "$1.2M has been allocated for IT infrastructure in FY2026. This new budget 
    creates purchasing capacity that didn't exist last fiscal year."
4. "New CIO Dr. Sarah Chen started January 1. New technology leaders typically 
    review the vendor stack within their first 90 days — a natural window for 
    new conversations."
5. "$5M in ESSER III funding has been earmarked for learning recovery and 
    intervention programs. Federal grant money often has use-it-or-lose-it 
    timelines that accelerate procurement."
```

---

## Quality Benchmarks

Use these examples to validate V1 output:

| Dimension | Current (Gamma/Gemini) | V1 Target |
|---|---|---|
| Signal selection | Hagel selects manually | LLM selects top 5-10 by relevance |
| Bullet quality | Neil's Gemini prompts — succinct, contextual | At least equivalent — contextual, specific, actionable |
| DM info accuracy | Hagel verifies manually | V1: not included. V2: SB API (accuracy TBD) |
| Tier 3 analysis | Hagel/Henry write manually | V3: LLM generates (quality TBD) |
| Formatting consistency | Variable (Gamma non-deterministic) | Deterministic template — always consistent |
