# BDR Handoff — How Intel Becomes Meetings

## The Handoff Point

Everything upstream (signal detection, report generation, Slack dispatch) exists to serve this moment: a BDR gets tagged in `#intent-reports` and needs to convert a warm prospect into a booked meeting.

## BDR Workflow (Step-by-Step)

### Step 1: Get Tagged in #intent-reports
- BDR sees notification: "new positive response from {Name} at {Company}"
- Expectation: act immediately. Culture is "drop what you're doing."

### Step 2: Acknowledge (Buy Time)
- Quick reply to the prospect (in Smartlead or directly): "I'll follow up shortly with details."
- Purpose: keep the thread warm while intel is being prepared
- If prospect asked for a meeting directly → skip to scheduling, intel prepared in parallel

### Step 3: Receive Intel
- Second Slack message arrives: "custom intel is ready" with Gamma/report link + DM card
- BDR reviews the intel and identifies the best angle

### Step 4: Send Payload Email
**Default approach (separate thread):**
- BDR sends a follow-up email (often via Apollo) in a new thread
- Includes: intel report link, screenshot, offer to discuss
- Separate thread enables sequencing + call tasks

**Alternative (original thread):**
- Used when prospect is likely to forward the email internally
- Intel needs to be in the thread they'll forward
- Henry's guidance: "respond in original thread since they'll pass internally"

### Step 5: Post-Positive Reply Email (DM-Later Flow)

The new default email structure (as of 2/4/26): {{UNVERIFIED: template below is drafted based on onboarding context, not an actual approved template — needs Henry/BDR review}}

```
Subject: [Intent report for {Company}]

Hi {Name},

Thanks for your interest — here's a custom intelligence report we put together 
for {Company} based on the procurement signals we're tracking:

[Report Link]
[Screenshot]

This covers the key buying signals, budget indicators, and opportunities 
we've identified in your space.

Happy to walk you through the details on a quick call — I can also share 
decision-maker contacts and deeper analysis for the accounts that matter 
most to you.

Would any of these times work? [scheduling link or times]

{BDR Name}
```

**If no reply to initial intel:**
```
Hi {Name},

Following up on the intelligence report I sent over. I also wanted to share 
a few key decision makers we've identified who may be relevant:

- {DM Name}, {DM Title} at {SLED Buyer}
  {DM Email} | {DM Phone}

Would it be helpful to hop on a quick call to dig into strategies for 
reaching these buyers?

{BDR Name}
```

### Step 6: Call
- BDR calls using Nooks
- Uses intel report + DM info as the talk track foundation
- For Tier 3 intel: relevancy analysis provides the specific pitch angle
- BDRs also use the Slack bot (endgame-lookup) to research further before the call — pulling additional context beyond what's in the report

### Step 7: Book Meeting / Follow-Up
- Meeting booked → transition to AE/demo
- "Forwarded internally" → pending, continue nurture
- No response → continue chase sequence
- Disqualified → tag and move on

## Operator Context That Changes BDR Behavior

| Context from Hagel | How BDR Should Adjust |
|---|---|
| Territory scoping ("not CA; focus on MD/WV/VA/TN/KY") | Only reference relevant regions in outreach |
| Scheduling request ("availability 12:30–3:00 EST") | Propose times in that window |
| Packaging note ("wanted 12 signals; we sent 5; rest in demo") | Frame: "We're keeping this digestible; we'll unpack the deeper set in the demo" |
| "Respond in original thread" | Don't use separate thread; reply in the chain they'll forward |
| Direct prospect quote in dispatch | Match tone/urgency to what the prospect said |

## Multi-Channel Post-Positive-Reply (Future)

Henry's vision: go full tilt on every channel for anyone who replies positively. {{UNVERIFIED: this is directional from Henry's state of the union — no implementation plan exists yet}}

| Channel | Action | Timing |
|---|---|---|
| Email | Intel report + DM-later follow-up | Immediate |
| Phone | Call using Nooks with intel as talk track | Same day |
| LinkedIn Ads | Flood their feed so Starbridge is subconsciously top of mind | {{TBD: requires Jenn/Mike to set up ad targeting}} |
| Snail mail | Printed intel report + gift card + "strategy dinner is on us" note | {{TBD: enterprise accounts only, manual test first — Neil/Ben owning}} |

**Pre-meeting nurture (for booked meetings):**
- 1-2 high-quality emails with a *new* intelligence report (distinct from what got them to book)
- LinkedIn ad retargeting
- Possibly low-cost snail mail depending on prospect quality
- Don't over-email — keep it valuable, not noisy

## Metrics to Track (Once Automated)

| Metric | What It Measures |
|---|---|
| Time: positive reply → Slack dispatch | Speed of automated pipeline |
| Time: Slack dispatch → BDR first response | BDR responsiveness |
| Time: positive reply → prospect receives intel | End-to-end fulfillment speed |
| Reply rate after intel delivery | Quality of intel + messaging |
| Intel → meeting conversion rate | Effectiveness of the full handoff |
| Tier distribution (1/2/3) | Are we doing enough Tier 2/3 for high-value accounts? |
| BDR follow-up completion rate | Are all dispatches getting acted on? |
