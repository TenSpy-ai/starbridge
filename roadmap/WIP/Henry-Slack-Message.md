Henry Bell  [Jan 28th at 12:26 PM](https://starbridgeai.slack.com/archives/C0A3Z35GMAS/p1769624781887539)  

I put together a state of the union & gameplan on project endgame. this is 90% me writing this out -- shoutout Claude for helping with formatting / making it easier to read.

`**Updates / Thoughts / Highlights**`

*   We're seeing **2.8x better conversion rates vs. FY25 averages** (0.7% vs. 0.25%) and tons of very positive responses. We've shared some in the channel but there are a lot more.
*   Important caveats on current performance: 1) our first campaign ran during the holidays which likely distorted our average; and 2) we've put our domains through the ringer with aggressive sending & using two subpar providers. We are now working with someone we're confident is the best on the market.
*   Even if we assume conservative conversion rates across the board (i.e. if we changed nothing and discounted), this can be highly effective. See the super conservative funnel breakdown in the thread replies.
*   We expect to 2-3x our conversion rates by executing on what is detailed below.

`**Future State / Gameplan**`

> **We want rock solid systems and infrastructure before aggressively scaling.** We don't want to be in a situation where we generate thousands of positive replies, respond to prospects late, send subpar intelligence reports, deliver a mediocre experience, and harm our reputation. There's also risk of getting bad contact data, sending emails on premature infrastructure, and destroying our domains.

Here's what we're doing to drive up conversion rates & build a durable, scalable machine.

**1\. Intelligence Reports / Post-Positive Reply Automations**

This is arguably the biggest lever we can pull.

_Current state:_ Hagel sifts through Smartlead, identifies positive replies, extracts intent signals via Slack apps (Kushagra's endgame-lookup & Starbridge app), feeds them into Gemini, uploads to Gamma, and sends to BDRs. BDRs then send the intel in a separate thread so we can sequence it in Apollo.

_Current drawbacks:_  

*   Time to respond, particularly given Philippines hours
*   Risk of human error given the volume
*   Report quality. There's a lot more we can do here. We can make branding more consistent and supplement intel with buyer attributes (AI Adoption Score, How to Navigate Procurement, budgets, account logos, etc.) instead of just bullets summarizing the intent signal.

_Future approach:_  

*   Agent detects positive replies in Smartlead
*   Pushes the domain to Clay
*   Clay pings Supabase to score and retrieve top signals
*   Clay pings Starbridge API for auxiliary buyer attributes \[cc [@Yurii Talashko](https://starbridgeai.slack.com/team/U09RGJLD8DR) on feasibility\]
*   Clay pushes to Webflow to generate a branded landing page
*   Clay sends a Slack message to Hagel (and potentially a global team covering all timezones) notifying them that 1) there is a positive response; and 2) the intel is ready (with the Webflow link)
*   We respond directly in-thread with the intel + landing page and loop in the BDR. See the sample post-positive reply email in the thread replies.

This will be a team effort. We have a GTME candidate we are trying to bring in-house (he came very well recommended) who starts his trial tomorrow, [@kushagra](https://starbridgeai.slack.com/team/U0A03N54F1P), [@Nastia](https://starbridgeai.slack.com/team/U0A4AK12F55), and likely others who will help bring this to fruition.

**2\. Multi-Signal Campaigns**

Currently, we send one email per prospect with one signal. We're building the ability to include multiple signals in the same sequence, where each follow-up surfaces a new signal.

_Why it matters:_ Smartlead data shows 52% of positive replies come from emails 2+, but only if they're in the same thread. Separate campaigns don't compound.

_Why it's hard:_ This requires logic to allocate signals across prospects, dynamic prompt selection in Clay based on signal type and email position, and standardized Smartlead sequence structure. Kushagra is building the assignment framework and fallback rules for when signals run low.

**3\. Contact Enrichment / Build Out**

Three problems to solve: pulls, enrichment, and data decay.

_Pulls:_  

*   We want every GTM and RevOps person in our TAM
*   Clay and other larger tools only have ~65% coverage due to LinkedIn's enterprise API restrictions
*   There are scrappier early stage startups and agencies that have built custom web scrapers to get close to 100% coverage
*   Our plan is to work with a handful of them, get all of their contact pulls, consolidate, and dedupe. This is how we go from 3-5 prospects/company to 7-10.

_Enrichment:_  

*   This is fairly easy to do. There are a ton of providers that take name + domain, test email variations, and validate via process of elimination.
*   Clay is good at this but expensive. Our plan is to use FullEnrich for initial coverage, then Clay's waterfall for gaps.

_Data Decay:_  

*   GTM orgs are notorious for turnover. We estimate ~15% data decay monthly.
*   Our validation approach is to use ZeroBounce to verify every email in our TAM monthly (this is quite cheap). For any emails that bounce, we run web scrapes to find where they moved, then use FullEnrich/Clay for updated contacts.
*   Note: job change campaigns were our highest performing in FY25, and that was with Clay's limited 65% visibility.

**4\. Multi-Channel Outreach**

This is another lever we are bullish on. This should drive up conversion rates across the board. Right now we are only doing email & phone. We've added 5 BDRs over the past 6 weeks so we can cover a higher % of prospects over the phone.

_Channel coverage (based on volume/cost):_  

*   Email: 100% of prospects (low cost/email)
*   Phone: top ~5-10% of prospects (dependent on BDR headcount). Note: we convert the email into a custom script for them
*   Paid Ads: top XX% of prospects (dependent on desired spend & how targeted we can be) \[cc [@Jenn Jiao](https://starbridgeai.slack.com/team/U0842CQR93N) [@Mike Shieh](https://starbridgeai.slack.com/team/U0986RT7ES0)\]
*   Automated Snail Mail: top 0.1-0.5% of prospects. One idea: we print gorgeous intelligence reports, ship them to prospects, include a gift card to a fancy restaurant, and use "handwritten" notes saying a "strategy dinner" is on us if they want to dig into these accounts. Plan is to test this manually for our enterprise accounts before exploring a scaled version \[cc [@Neil Daiksel](https://starbridgeai.slack.com/team/U09QM6963UN) [@Ben Samuels](https://starbridgeai.slack.com/team/U0A2VAXR9BN)\]

_Post-positive reply:_ We should go full tilt on using these channels for anyone who replies positively.

_Note on show rates:_ We probably don't want to send too many emails leading up to the call, but we can send 1-2 high-quality emails with a new intelligence report (distinct from what got them to book) and flood their LinkedIn with paid ads so we're subconsciously top of mind. Could also explore low cost snail mail depending on the quality of the prospect.

**5\. Deliverability**

Brought this up earlier but we spent a lot of time interviewing/backchanneling to find the best person to own our deliverability/email infra. Shoutout [@Gurmohit Ghuman](https://starbridgeai.slack.com/team/U07BL2J7F38) for your amazing work so far. Our plan is to build out capacity to send 3.3M emails / mo. We are doing them in batches. See the volume timeline in the thread replies for how long it will take to get to max capacity—

**Example Response (Post Positive Reply)**

[FIRST] - appreciate you getting back to me. Here's the decision maker's info: XXX.

We also took the liberty of training a custom agent on [COMPANY] that sifted through millions of public records (board meetings, purchase orders, strategic plans, public chatter, etc), and identified the accounts with the highest propensity to invest in [SERVICE/PRODUCT] in the near term.

If you reach out to them, you can get in the door before an RFP gets published and be in pole position.

This is the tip of the iceberg. Happy to tee up a call with our team to show you how hundreds of teams that sell to [SLED ENTITY] are winning deals before their competitors know the opportunity exists.

Looping in my colleague, [BDR], who can help set that up.

[SENDER NAME]

---

> **TL;DR: This opportunity can be massive.** We have strong positive signal already and concrete steps to build the right foundations/infrastructure. Once in place, we can pour gasoline on this and get our AEs into diaper mode.