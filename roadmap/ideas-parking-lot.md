# Ideas Parking Lot

Captured ideas that are interesting but not committed to any version. Prevents scope creep by giving ideas a home without blocking progress. Revisit after V2 is stable.

---

## Pipeline Enhancements

### Signal Refresher Agent
Re-check Supabase for new signals on accounts with existing reports. Auto-update reports with fresh intel. Trigger follow-up sequences when new high-value signals appear.
**Source**: Pipeline design discussions
**Effort**: Medium — new Datagen agent
**Value**: Keeps reports current; enables "we found something new" follow-ups

### Batch Report Pre-Generation
For top-tier accounts, pre-generate reports BEFORE positive replies arrive. When a PR comes in, the report is already built — response time drops to near-zero.
**Source**: Scaling discussion
**Effort**: Medium — scheduling + storage
**Value**: Instant response for highest-value accounts (T0/T1)

### AI Adoption Score
Score each SLED account on their AI/technology adoption readiness based on meeting transcripts, purchase history, and signals. Include in Tier 3 reports.
**Source**: Henry's vision for differentiated intelligence (1/12 call)
**Effort**: High — requires scoring model design + validation
**Value**: Unique competitive differentiator

### Procurement Risk Signals Index
Flag procurement patterns that indicate irregularities or risk (e.g., RFP bids that seem pre-wired, unusual sole-source awards, patterns suggesting bid-rigging). Frame as "risk flags / irregularities" — avoid calling it a "corruption index" even though that was the original idea.
**Source**: Henry's 1/12 call — "corruption index? via RFP bids that came in and seemed shady." Reframed per pre-trial AI analysis to avoid compliance risk.
**Effort**: High — requires careful methodology design + legal review
**Value**: Highly differentiated; no competitor offers this. Could be a content/brand moat alongside AI Adoption Score.

### Similar Customers Section
"Buyers like you also..." section in reports, matching the prospect's buyer type and signal profile against Starbridge's customer base.
**Source**: intel-report-v2 design
**Effort**: Medium — requires customer data + matching logic
**Value**: Social proof specific to SLED vertical

---

## Channel Expansion

### Phone Channel Integration (Nooks/Apollo)
Auto-generate call scripts or talk tracks from signal data. Feed intent intelligence into Nooks so BDRs have context before they dial.
**Source**: Multi-channel roadmap (currently at 5-10% coverage)
**Effort**: Medium — Nooks/Apollo integration + script generation
**Value**: BDR effectiveness on calls; currently "boiler room" does a simpler version

### Paid Ads Retargeting
Use signal data to build audience segments for paid ads. Prospect sees Starbridge ad after receiving intel report → reinforces the message.
**Source**: Multi-channel roadmap (TBD coverage)
**Effort**: High — ad platform integration + audience sync
**Value**: Multi-touch reinforcement

### Snail Mail
Physical mail for ultra-high-value accounts. Intel report as a printed booklet or branded one-pager.
**Source**: Multi-channel roadmap (0.1-0.5% coverage target)
**Effort**: Low-Medium — PDF generation + print fulfillment service
**Value**: Pattern interrupt for CIOs/superintendents who ignore email

### LinkedIn Touchpoints
Automated LinkedIn connection requests or InMails referencing signal data. Could use existing tools like Dripify or HeyReach.
**Source**: Channel strategy discussions
**Effort**: Medium — LinkedIn automation tool integration
**Value**: Multi-channel presence

---

## Reporting & Analytics

### Automated Time-to-Response Tracking
Timestamp between Slack dispatch and BDR first action. Surface slow responses. Gamify speed.
**Source**: Operational efficiency discussion
**Effort**: Low — Slack timestamp comparison
**Value**: Accountability + optimization data

### Daily Digest
Morning summary in Slack: how many PRs yesterday, how many fulfilled, how many converted, pipeline impact.
**Source**: Henry's visibility needs
**Effort**: Low — scheduled Datagen agent querying metrics
**Value**: Exec visibility without asking for updates

### Signal-to-Meeting Attribution
Track which signal types most frequently lead to booked meetings. Feed back into signal ranking algorithm.
**Source**: Optimization loop
**Effort**: Medium — requires meeting outcome data flowing back to signal records
**Value**: Data-driven signal prioritization

---

## Platform & Process

### Ask Starbridge as Data Source
Use Starbridge's AI chat interface programmatically to research buyers when the API is limited. Could be a V2 fallback or supplementary data source.
**Source**: Starbridge API exploration (doc 3)
**Effort**: Medium — requires understanding the conversation API
**Value**: Alternative path to buyer intelligence if API access remains limited

### Prospect Self-Service Portal
Prospects receive a personalized portal URL (not just a report) where they can explore signals, request more intel, and book meetings directly.
**Source**: Future product vision
**Effort**: High — requires frontend development + auth
**Value**: Transforms a one-time report into an ongoing relationship touchpoint

### FOIA Campaign Integration
Connect FOIA campaign data to signal pipeline. FOIA requests generate new data → new signals → new campaigns.
**Source**: Starbridge admin API endpoints
**Effort**: Medium-High — FOIA data pipeline
**Value**: Proprietary data generation → unique signals competitors can't replicate

### GIF/Visual Collateral for Post-PR Email
Animated GIF that teases the intel report content, included in the payload email as a visual hook.
**Source**: Henry mention during 2/4 onboarding ("Gif with link to CSV")
**Effort**: Low-Medium — GIF template + dynamic data
**Value**: Higher email click-through rates

---

## Pre-Trial Creative Game Plans (Historical)

These ideas were developed during the pre-trial planning phase (Jan 2026) as potential trial scopes. The trial ultimately narrowed to Part 1 (Post-Positive Reply Automations), but these remain valid future plays:

### Boardroom → Pipeline Listening Post
Weekly "Boardroom Brief" (Bloomberg-style) surfacing decision signals from board agendas/transcripts — 1 page with "why it matters" + "who to call." Doubles as premium lead magnet and outbound opener.
**Source**: Pre-trial game plan proposals

### RFP Counter-Programming Kits
Pre-built enablement kits prospects can use internally (cybersecurity maturity checklist, LMS renewal scorecard, AI governance policy template). Each kit pairs to a Starbridge signal trigger.
**Source**: Pre-trial game plan proposals

### Public Money Heatmap
Physical wall map + digital microsite showing where spend is moving or contracts are expiring by state/county/district. Makes reps' outreach instantly credible.
**Source**: Pre-trial game plan proposals

### The Evidence Locker (Deal Rooms)
Per-account deal rooms (Notion/Drive) containing board excerpts, budget lines, prior RFP docs, contract renewal dates, and outreach snippets. "Here's the receipts."
**Source**: Pre-trial game plan proposals

### The Starbridge Challenge (Gamified Outbound)
10-account wager with a public scoreboard tracking accounts targeted, signals detected, assets sent, replies, meetings, and pipeline created. Clear trial with unambiguous outcomes.
**Source**: Pre-trial game plan proposals

### Procurement Whisperer (Live Hotline)
Weekly live "GTM Clinic" webinar/office hours where Starbridge team helps prospects with procurement problems using the platform. Record + clip into content + knowledge base.
**Source**: Pre-trial game plan proposals

### Starbridge Partner Pack (Co-Sell Channel)
Partner-targeting list (top 50 resellers/consultants/MSPs) plus outreach kit, co-selling narrative, and partner enablement doc. Small number of partners = huge territory coverage in SLED.
**Source**: Pre-trial game plan proposals

---

## Rules for This List

1. **Don't build it yet** — if it's here, it's not in V1 or V2 scope
2. **Revisit monthly** — after V2 is stable, review and promote to roadmap
3. **Anyone can add** — drop ideas here instead of inserting them into active sprint
4. **Kill freely** — if an idea doesn't hold up on revisit, delete it
