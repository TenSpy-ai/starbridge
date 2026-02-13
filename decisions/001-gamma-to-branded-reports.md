# ADR 001: Replace Gamma with Branded Report Pages

## Status
**Accepted** — confirmed during onboarding (Henry, Justin, team consensus)

## Context
Starbridge uses Gamma (gamma.app) to generate per-prospect intel reports delivered after positive replies. The reports are the primary sales asset sent directly to SLED prospects. Hagel manually feeds signal data through Gemini, then uploads to Gamma, which generates a visual page.

Five problems have emerged:
1. **Non-deterministic output** — same inputs produce different layouts and phrasing
2. **Limited data** — only includes what Hagel manually feeds in (no buyer attributes, no DM info, no budget)
3. **No branding control** — Gamma's default aesthetic, not Starbridge's brand
4. **Manual process** — every report requires 20-60 minutes of Hagel's time
5. **Single point of failure** — Hagel offline = no reports

## Decision
Replace Gamma with programmatically generated, branded report pages using a phased approach:
- **V1**: Notion pages (fastest to implement, deterministic template)
- **V1.5**: Super.so layer for custom domain + CSS branding
- **V2**: Webflow CMS with Nastia's designed template

## Reasoning
- Notion API allows deterministic template-based generation (fixed structure, variable content)
- Phased approach avoids blocking V1 on design decisions
- Datagen cloud agents handle the generation, eliminating the manual bottleneck
- Each phase is additive — V1 content carries forward, only the presentation layer upgrades

## Consequences
**Positive:**
- Reports become deterministic and consistent
- Generation time drops from 20-60 min to < 30 seconds
- Richer data (buyer attributes, DM info in V2) enriches the deliverable
- Brand consistency increases trust with SLED buyers
- Pipeline can scale with volume (no human bottleneck)

**Negative / Risks:**
- V1 Notion URLs look unprofessional (mitigated by Super.so in V1.5)
- Nastia's design work is a dependency for V2 (could delay branding upgrade)
- Need to confirm Notion workspace setup and API access
- Loss of Hagel's contextual judgment in report content (mitigated by operator override capability)

**Trade-offs:**
- Speed over polish in V1 — acceptable because current Gamma output isn't polished either
- Template rigidity vs. flexibility — deterministic templates lose Gamma's adaptive layout, but gain consistency

## Dependencies
- Nastia: brand assets (logo, colors) for V1.5+; template design for V2
- Henry: approve Notion as V1 format
- Engineering: custom domain (intel.starbridge.ai) for Super.so/Webflow
