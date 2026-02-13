# Template: Slack Intel Ready (Message 2 — Report Delivery)

## Tier 1 — Report Only

```
@{BDR} — custom intel is ready for {ProspectName} of {Company}, {ProspectEmail}.

Intel Report: {ReportURL}
```

## Tier 2 — Report + DM Card

```
@{BDR} — custom intel is ready for {ProspectName} of {Company}, {ProspectEmail}.

Intel Report: {ReportURL}

Custom Intel:
- Name: {DMName}
- Title: {DMTitle}
- Email: {DMEmail}
- Phone: {DMPhone}
```

## Tier 3 — Report + DM + Analysis

```
@{BDR} — custom intel is ready for {ProspectName} of {Company}, {ProspectEmail}.

Intel Report: {ReportURL}

Custom Intel:
- Name: {DMName}
- Title: {DMTitle}
- Email: {DMEmail}
- Phone: {DMPhone}

IR Notes:
- Relevancy: {specific initiative or signal connection to the prospect}
- Pitch angle: {suggested framing for the conversation}
- Gameplan: {what to say, what to lead with, how to navigate}

Packaging note: {expectations management if needed}
```

---

# Template: DM Follow-Up (Message 3 — Deferred DM Delivery)

```
@{BDR} — DM info is ready for {ProspectName} of {Company}:

- Name: {DMName}
- Title: {DMTitle}
- Email: {DMEmail}
- Phone: {DMPhone}

{Optional: context about the DM's relevance to the signals}
```

---

# Template: Edge Case Notifications

## Zero Signals Found

```
⚠️ @{BDR} — No signals found in our database for {Company} ({Domain}).

Intel report could not be generated. Please proceed with standard follow-up — or flag to Henry if this is a high-priority account.
```

## Pipeline Failure / Fallback

```
⚠️ Pipeline alert — report generation failed for {ProspectName} of {Company}.

@Hagel — manual fulfillment needed. Domain: {Domain}
Error: {brief error description}
```

## Report Updated (V3 — Refresh)

```
📊 @{BDR} — intel report for {Company} has been updated with new signals.

Updated Report: {ReportURL}
New signals added: {count}
```
