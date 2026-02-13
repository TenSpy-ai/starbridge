# Signal Taxonomy

Classification of procurement intent signals that flow through the pipeline. Used for LLM prompt engineering, signal ranking, and report generation.

{{UNVERIFIED: taxonomy below is inferred from onboarding docs, Slack observations, and platform data. Need Kushagra to confirm the full list and any signals not captured here.}}

---

## Signal Types

### Contract Expiration
**What it is**: An existing contract for a product/service is expiring within a defined window.
**Why it matters**: Expiring contracts = active procurement window. The buyer MUST make a decision (renew, replace, or go without).
**Urgency**: HIGH — time-bound. Urgency increases as expiration approaches.
**LLM guidance**: Lead with the timeline. "Contract expires in X months" creates natural urgency. Mention the product category being replaced.

**Example**: "Austin ISD's LMS platform license expires June 30, 2026 ($250K annual value)"

### Board Meeting Discussion
**What it is**: A specific topic was discussed in a government board meeting (school board, city council, county commission, etc.).
**Why it matters**: Board discussions signal organizational priorities. If the board is talking about it, budget and procurement follow.
**Urgency**: MEDIUM — signals intent but doesn't have a hard deadline.
**LLM guidance**: Reference the specific discussion topic and connect it to the vendor's product. "The board discussed X, which aligns with what you do."

**Example**: "Austin ISD board discussed chronic absenteeism in K-1 at their January 15 meeting. Attendance Awareness initiative mentioned."

### Budget Event
**What it is**: Budget allocation, approval, amendment, or change related to a product category or initiative.
**Why it matters**: Budget signals = money is available. Most SLED procurement is budget-driven — no budget, no purchase.
**Urgency**: MEDIUM-HIGH — budget allocated but not yet spent means there's a window.
**LLM guidance**: Include the dollar amount if available. "They allocated $X for Y" is one of the most powerful signal bullets.

**Example**: "$1.2M allocated for IT infrastructure upgrades in FY2026 budget"

### RFP Posted
**What it is**: A formal Request for Proposal has been published for a product/service category.
**Why it matters**: RFPs are the most explicit signal of active procurement. The buyer is literally asking vendors to respond.
**Urgency**: HIGH — RFPs have submission deadlines.
**LLM guidance**: Include the due date. If the prospect's product matches the RFP category, this is the #1 signal.

**Example**: "RFP for Student Information System posted by Austin ISD. Due: February 28, 2026."

### Purchase Order
**What it is**: A purchase order was issued for a product/service.
**Why it matters**: Shows what the buyer actually buys (not just discusses). If it's a competitor's product, it's a displacement opportunity. If it's an adjacent product, it signals tech maturity.
**Urgency**: LOW-MEDIUM — the purchase already happened, but it informs future strategy.
**LLM guidance**: Use for context, not urgency. "They bought X, which suggests they're also likely to need Y."

**Example**: "Purchase order issued for Chromebook fleet ($800K) — suggests 1:1 device initiative underway"

### Leadership Change
**What it is**: A new leader was appointed (CIO, superintendent, director, commissioner, etc.).
**Why it matters**: New leaders bring new priorities, new budgets, and new vendor relationships. The first 90 days of a new leader is a high-opportunity window.
**Urgency**: MEDIUM-HIGH — window is time-limited (new leaders make purchasing decisions early in tenure).
**LLM guidance**: Name the new leader and their likely priorities based on role. "New CIO typically reviews vendor stack in first quarter."

**Example**: "New CIO Dr. Sarah Chen appointed at Austin ISD effective January 1, 2026"

### Grant / Funding Event
**What it is**: The buyer received a grant, bond approval, or other funding event.
**Why it matters**: New funding = new budget that didn't exist before. Often earmarked for specific purposes.
**Urgency**: MEDIUM — funding received, but procurement process takes time.
**LLM guidance**: Connect the funding to what it enables. "The $5M ESSER grant for learning recovery creates budget for tools that address X."

**Example**: "$5M ESSER III funding allocated for learning recovery and intervention programs"

### Conference Attendance
**What it is**: The buyer is attending or speaking at a specific conference.
**Why it matters**: Conference attendance signals interest in a topic area. Speaking engagements signal the buyer is a thought leader.
**Urgency**: LOW — informational, not directly procurement-related.
**LLM guidance**: Use for personalization, not as a primary signal. "You'll be at CoSN next month — we'll be there too."

**Example**: "Austin ISD CTO registered for CoSN 2026 (San Antonio, March 15-17)"

### Additional Signal Types

{{UNKNOWN: Kushagra may have signal types not captured above. Potential additions:}}
- **FOIA response** — data from FOIA requests Starbridge has filed
- **Strategic plan mention** — specific mention in a published strategic plan
- **Vendor evaluation** — evidence the buyer is evaluating vendors (not just an RFP)
- **Compliance/regulatory** — mandated requirements that force procurement
- **Enrollment/demographic change** — student population shifts that drive resource needs

---

## Signal Ranking Framework

When the LLM receives multiple signals for a domain, it ranks them for the intel report. Default ranking criteria:

| Factor | Weight | Reasoning |
|---|---|---|
| **Recency** | High | Newer signals are more actionable. A 2-week-old contract expiration signal > a 6-month-old board discussion. |
| **Urgency** | High | Signals with hard deadlines (contract expiration, RFP due date) rank above open-ended signals. |
| **Specificity** | Medium | Named product categories or vendor mentions > generic "technology" discussions. |
| **Dollar value** | Medium | Signals with dollar amounts (budget, contract value) are more concrete. |
| **Reply relevance** | Medium | If the prospect replied to a campaign about LMS, LMS-related signals rank higher. |
| **Signal type priority** | Low | As a tiebreaker: RFP > Contract > Budget > Board > Purchase > Leadership > Grant > Conference |

{{TBD: should this ranking be hardcoded in the LLM prompt, or should it be a configurable scoring model?}}

---

## Signal Density by Account

From Henry's data:
- Starbridge has **more signals than prospects** (412K+ prospects)
- Goal: at least one signal per prospect
- For intel reports: retrieve ALL, then LLM selects top 5-10

Expected distribution:
| Signals per Domain | % of Accounts | Report Impact |
|---|---|---|
| 0 | {{UNKNOWN}} | Cannot generate report — exception case |
| 1-3 | {{UNKNOWN}} | Thin report — include all signals |
| 4-10 | {{UNKNOWN}} | Ideal range — LLM selects best subset |
| 10-50 | {{UNKNOWN}} | Rich data — LLM must be selective |
| 50+ | {{UNKNOWN}} | May need pre-filtering before LLM |

{{UNKNOWN: actual distribution — ask Kushagra for signal count distribution across domains}}
