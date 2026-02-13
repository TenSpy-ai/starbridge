Henry Bell  [Feb 4th at 2:37 PM](https://starbridgeai.slack.com/archives/C0ACXMNMVHS/p1770237473006119)  

At first we were thinking of making Jeremy's project something like this:

1. positive response comes in
2. smartlead webhook pings to DG
3. DG pings Supabase for all intent signals from that domain
4. DG sifts through to pull the top 5-10 signals
5. DG pings Starbridge API to pull the 5-10 accounts from said 5-10 signals. pulls: budgets; decision makers; account logo (and more as we go along)
6. DG creates a Notion landing page with a breakdown of the 5-10 accounts — the specific intent signal detailing why they are relevant right now (from part 3) + additional intel on the account (part 5)

But I talked to Justin (CEO) recently and he said the API might not be viable. so what we're going to consider now is setting it up so that we're getting all of the "auxiliary data" in that initial export. so there's gonna be one massive csv file, where each row represents an intent signal — e.g. row 1 is a meeting that university of michigan had where they discussed cyber security attacks; university of michigan's budget is another column; etc... so that way anytime we got a positive response everything is just in that massive csv file.

this actually makes it a lot easier for a v1 project for Jeremy. all we need to do is:

1. take a specific domain
2. search for it in supabase (this is where the csv exports yurii sends us are stored)
3. sift through and identify the top 10 signals
4. summarize the 10 signals in a super easy to read format (we can work on this together)
5. feed that into a simple notion landing page

so we basically don't need to do step 5 ("DG pings Starbridge API..."), from earlier in my message, since yurii is going to include all of that data in the export. 

Henry Bell  [Feb 4th at 2:52 PM](https://starbridgeai.slack.com/archives/C09S4P94146/p1770238334558169)  

To reiterate, Jeremy will own responding to our positive reply flow (when we send a sales prospect a summary of a meeting/whatever other signal). this means finding the top 10 signals from that account from the most recent export, and then feeding that information into a custom landing page for that specific prospect. we call those "intel reports"... our initial thinking was that we would rely on ops team (Yurii Talashko) exports to find the top signals and accounts, then ping our API to pull additional attributes that are not included in the export (e.g. the decision maker given the signal context; their budget; the account logo url)... touched base with Justin (CEO) and he thinks the better approach would be to define the additional attributes we would want for every account in the export we get from you vs. doing it retroactively after a positive response via an API (that sounds like doesn't really exist)... we have enough to run with with the current columns we aligned on for the upcoming export of the 33k co's and for the creation of the 50k co's. for the following export, I'm curious if we could add the following attributes (see screenshot) + the decision maker (with title, email, phone) for that specific intent signal (e.g. if it was a signal for a company that sells cybersecurity, whoever the person who makes decisions on cybersecurity at that SLED account).

