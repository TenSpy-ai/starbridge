# Slack — System Overview

## Role in the Stack

Slack is the **dispatch and handoff hub**. It's where the automated pipeline delivers intel to humans, where BDRs get notified and coordinated, and where operational decisions happen in real-time.

Slack is NOT a data source or processing tool — it's the human interface layer. Everything upstream (Smartlead → Clay → Datagen) exists to produce a clean Slack message that a BDR can act on immediately.

## Key Channels

| Channel | Purpose | Who's Active | Traffic |
|---|---|---|---|
| **#intent-reports** | Operational dispatch. Every positive reply notification and intel delivery happens here. THE source of truth for "hot replies." | Hagel, BDRs (Jorge, Joseph, Glenn, Jaime), Henry | High — every positive reply generates 2 messages |
| **#gtm-eng** | GTM engineering team coordination. Henry announced Jeremy here. Technical discussions and project updates. | Henry, Kushagra, Jeremy, Yurii, Neil, Hagel, Nastia | Medium |
| **#proj-endgame** | Project Endgame coordination. {{UNKNOWN: how active is this vs. #gtm-eng? Do they overlap?}} | {{UNKNOWN: members}} | {{UNKNOWN}} |

## How Slack Fits in the Pipeline

```
                                          AUTOMATED
Smartlead → Clay → Datagen → Clay ─────────────────→ Slack #intent-reports
                                                          │
                                                          │  Message 1: "New positive reply"
                                                          │  Message 2: "Intel is ready" + link
                                                          │
                                                     HUMAN TAKES OVER
                                                          │
                                                          ├── BDR responds in Smartlead
                                                          ├── BDR calls via Nooks
                                                          └── Thread updates in Slack
```

The Slack message is the **handoff point** between automated and human. Everything before it is machine; everything after it is people.

## Slack Integrations

### Clay → Slack (Automated Dispatch)

Clay sends messages to #intent-reports via its native Slack integration. Two message types:

1. **Immediate notification**: Fires when Clay receives the Smartlead webhook. "New positive reply from {Name} — intel incoming."
2. **Intel delivery**: Fires when Clay receives the Datagen webhook return (report URL). "Intel is ready — here's the link + DM card."

{{UNKNOWN: exact Clay Slack integration configuration — is it using Clay's native Slack action, a webhook URL, or the Slack API directly?}}

### Slack Bots (Current Manual Process)

Two bots used by Hagel in the current manual workflow. These may be partially or fully replaced by Datagen in the future state:

- **endgame-lookup** (Kushagra) — queries Supabase for intent signals by domain
- **Starbridge Slack app** — queries the Starbridge platform for buyer data / DM info

See: [slack-bots.md](./slack-bots.md)

## #intent-reports Operating Rules

These are confirmed from observing the channel and Henry's guidance:

### Rule 1: #intent-reports is the source of truth
If a positive reply isn't posted here, it's at risk of getting dropped. No other channel or tool replaces this.

### Rule 2: Two-message pattern is the standard
Message 1 (dispatch) and Message 2 (intel ready) are the expected rhythm. BDRs know to expect both. The automated pipeline should preserve this pattern.

### Rule 3: BDRs act immediately when tagged
The culture is "drop what you're doing." Response time matters. This is why automating the upstream (cutting hours off fulfillment) has such high leverage.

### Rule 4: Thread context matters
Operator notes (territory, scheduling, packaging expectations, prospect quotes) are included in the dispatch messages and change how BDRs respond. The automated pipeline needs to either extract these from the reply text or make it easy for an operator to add them.

### Rule 5: Henry provides situational overrides
Henry sometimes jumps into threads with guidance like "respond in original thread since they'll forward internally" or "throw a placeholder on the calendar." The system should support these ad-hoc human interventions.

## Message Format Reference

See: [intent-reports-format.md](./intent-reports-format.md) for detailed message templates and real examples.

## Future State for Slack

### What stays the same:
- #intent-reports remains the dispatch channel
- Two-message pattern preserved
- BDR @-mention tagging
- Thread-based coordination

### What changes:
- Messages are sent by Clay automatically (not Hagel manually)
- Response time drops from hours to minutes
- Report links go to branded Notion/Webflow pages (not Gamma)
- Intel quality is richer (more data, better formatting)
- {{TBD: will there be an automated "intel is processing" status message while Datagen runs? Could reduce anxiety about whether the system is working.}}

### Potential additions:
- Automated time-to-response tracking (timestamp between dispatch and BDR first action)
- Status reactions (BDR reacts with ✅ when they've responded, 📞 when they've called)
- Daily digest: how many positive replies, how many fulfilled, how many converted
- {{TBD: any of these worth building in V1 or save for V3?}}
