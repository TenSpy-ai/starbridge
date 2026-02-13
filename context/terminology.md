# Terminology — Starbridge GTM

## Starbridge Platform Terms

| Term | Definition |
|---|---|
| **Bridge** | A saved search/workflow in Starbridge that automatically surfaces relevant business signals. Types: RFPs, Board Meetings, Purchase Orders, Conferences, Buyers, Contacts, Custom Web Signal, Job Changes. |
| **SLED** | State, Local, and Education — the government procurement sectors Starbridge targets. |
| **Buyer** | A government or institutional entity in Starbridge's database (e.g., a school district, city government, state agency). 296K+ in the system. |
| **Buyer Type** | Classification of a buyer: Higher Education, School District, City, County, State Agency, etc. |
| **Signal** | A piece of intelligence from Starbridge's data sources indicating buying intent or opportunity. Examples: contract expiring, board discussion mentioning a product category, budget allocation, new RFP, leadership change. |
| **Intent Signal** | A signal specifically indicating a prospect may be in-market for a solution. Stored in Supabase, aligned to accounts/domains. |
| **Board Signal** | Intelligence derived from board meeting minutes, agendas, or transcripts. Starbridge's AI summarizes these to surface buying intent. |
| **Ask Starbridge** | AI-powered chat interface in the platform for researching buyers (key contacts, procurement strategy, priorities, competitors). |
| **FOIA Campaign** | Starbridge's systematic Freedom of Information Act requests to government agencies. Creates a data flywheel — more FOIA requests → more unique proprietary data over time. |

## Project Endgame Terms

| Term | Definition |
|---|---|
| **Project Endgame** | The internal name for Starbridge's outbound engine. Also the name of the main Clay workbook. |
| **Boiler Room** | Secondary Clay workbook that converts signals into intel snippets for BDRs working the phones. |
| **Positive Reply** | A response to an outbound email indicating interest (curiosity, demo request, intel request, willingness to connect). Triggers the fulfillment loop. |
| **Fulfillment Loop** | The process triggered by a positive reply: dispatch → intel build → BDR payload → calls → meeting. |
| **Intel Report** | The deliverable sent to a prospect after a positive reply. Contains Starbridge signals, buyer attributes, and (optionally) decision maker info. Currently built in Gamma; migrating to Notion/Webflow. |
| **Gamma Report** | The current (legacy) intel report format, generated via Gamma. Being replaced due to non-deterministic output, limited branding, and manual process. |
| **Custom Intel** | The enriched payload delivered to a BDR alongside the intel report. Often includes a decision maker contact card (name, title, email, phone). |
| **Decision Maker (DM)** | The SLED-side buyer identified for a prospect account. E.g., "Holly Varner, Director of Special Education" with email + phone. |
| **DM-Later Flow** | New approach (as of 2/4/26): lead with intel report, offer DMs on the call instead of upfront. Decouples time-critical intel delivery from DM lookup. |
| **SLED Signal Bullets** | A Clay column containing LLM-generated summaries of the top signals for a prospect. Used in outbound copy and intel reports. |
| **Relevancy Analysis** | A Tier 3 intel component: written rationale connecting Starbridge signals to the prospect's specific situation, with a suggested pitch angle and gameplan. |

## Campaign & Outbound Terms

| Term | Definition |
|---|---|
| **Evergreen Campaign** | An always-on campaign triggered by persistent signals (e.g., contract expirations, ongoing budget patterns). Starbridge runs ~4 at a time. |
| **Event Campaign** | A one-off campaign triggered by a time-bound signal (conference, board vote, RFP deadline). |
| **Multi-Signal Campaign** | A campaign where each follow-up email surfaces a different signal for the same prospect. Currently being built by Kushagra. |
| **Signal Allocation** | The logic for assigning signals to prospects across a sequence. {{UNKNOWN: Kushagra is building the framework + fallback rules — details not yet shared}} |
| **Net New Sources** | Additional campaign angles beyond core signals: website traffic, closed-lost, new deal (competitor displacement), LinkedIn engagement. |

## Roles & Process Terms

| Term | Definition |
|---|---|
| **Fulfillment Operator** | The person (currently Hagel) who turns positive replies into intel packages for BDRs. Monitors replies, builds reports, dispatches via Slack. |
| **Dispatch** | The first Slack message in #intent-reports notifying a BDR of a positive reply. Includes prospect name, company, email, and often a quote from the reply. |
| **Payload Email** | The email a BDR sends to a prospect containing the intel report link, screenshot, and offer to discuss further. |
| **Separate Thread** | Default BDR follow-up approach: send the payload in a new email thread (often via Apollo) to enable sequencing + call tasks. |
| **Original Thread** | Alternative approach: reply in the original outbound thread. Used when the prospect is likely to forward internally. |

## Infrastructure Terms

| Term | Definition |
|---|---|
| **Datagen Cloud Agent** | A serverless workflow running on Datagen (MCP-as-a-Service platform). In the Starbridge pipeline, the Datagen agent handles: Supabase query → LLM signal ranking → report page generation → webhook URL return to Clay. Pricing: $50/mo month 1, $500/mo after. |
| **Operator** | Shorthand for Fulfillment Operator (see Roles & Process Terms). Used throughout playbooks and workflows to mean "the person (or future automation) responsible for fulfillment." |
| **Webhook Source Column** | A Clay column that receives data from an external webhook. Project Endgame has two: (1) inbound from Smartlead, (2) return URL from Datagen. |
| **endgame-lookup** | Kushagra's Slack bot that pings Supabase for intent signals by domain. Used by Hagel in the current manual workflow. |
| **Data Decay** | ~15% monthly turnover in GTM contact data. Managed by monthly ZeroBounce validation + web scrapes for bounced contacts. |
| **Waterfall Enrichment** | Sequential enrichment strategy: try cheaper/faster providers first, fall back to more expensive/comprehensive ones for gaps. E.g., FullEnrich → Clay. |

## Tier System (Intel Reports)

| Tier | Contents | When Used |
|---|---|---|
| **Tier 1** | Report link only | DM not needed or not available quickly |
| **Tier 2** | Report link + DM contact card (name, title, email, phone) | Standard fulfillment |
| **Tier 3** | Report + DM + relevancy analysis + pitch angle + gameplan | High-value accounts |

## Account Segmentation

| Term | Definition |
|---|---|
| **T0–T3** | Account tiers in Starbridge's TAM (33K accounts total). T0 = highest priority. {{UNKNOWN: tier criteria and distribution — how are accounts classified?}} |
| **TAM** | Total Addressable Market. 33K accounts, 412K+ prospects. |
| **PR** | Positive Reply. Current rate: ~0.7% (prospect → PR), up from 0.25% in FY25. |
