# Reference: SLED Competitor Search Prompt

> Extracted from GTM Process Flow for Project Prospect Org. Saved for future use — not yet integrated into the pipeline.

# \[ULTRA\] Competitor Search

\#\# Task Description

Competitive intelligence in the SLED market (State, Local, and Education sectors) involves identifying and analyzing companies that compete directly with a given organization for government contracts, RFPs, and client relationships. Understanding competitors helps companies position their offerings, anticipate market moves, and develop effective sales strategies. Competitors are validated through evidence of active competition, overlapping customers, similar product offerings, or shared bid history in the SLED space.

Your task is to identify the specified company's top 10 direct competitors within the SLED market based on verifiable public information.

\#\# Instructions

\- All identified competitors must be verifiable through public information, ideally sourced from the provided company URL or other reliable web sources. Never invent competitors.  
\- Prioritize the most useful and relevant competitors based on the provided criteria.  
\- Focus exclusively on competitors with SLED alignment. Do not include companies that focus only on federal, private, or international markets unless they also demonstrably sell into the SLED segment.  
\- Your results must be grounded in reliable web-based evidence including:  
  \* Government procurement databases (e.g. BidNet, GovWin, state procurement portals)  
  \* Company websites and case studies  
  \* RFP award documents and press releases  
  \* Industry write-ups or customer reviews demonstrating real competitive activity in the SLED space  
\- Return only competitors that have been directly validated through:  
  \* Active competition  
  \* Overlapping customers  
  \* Comparable product offerings  
  \* Bid history in the SLED market  
  Prioritize high-confidence matches over quantity — if you cannot find 10 with confidence, return only those you can validate.  
\- Your output must consist only of a JSON object with a single key "competitors" containing a list of competitor names as strings. Do not include introductory text, conjunctions, or trailing punctuation.  
\- Use the most natural-sounding brand names for each company — be concise, but never ambiguous. Avoid using full legal names like "LLC" or "Inc." unless absolutely necessary for clarity.

Here are 5 examples with clear reasoning:

Example 1:

Company: Tyler Technologies  
Company Website: https://www.tylertech.com/  
Company Description: Tyler Technologies provides software and services designed for government and schools, empowering the public sector to create smarter, safer, and stronger communities. Their broad solution and product offering helps deliver better and faster assistance to the public, including greater transparency and accessibility, sustainable office practices, secure data management, and faster results across public administration, courts & public safety, health & human services, K-12 education, and transformative technology.

Output:  
\`\`\`json  
{  
  "competitors": \[  
    "CentralSquare",  
    "Oracle",  
    "SAP",  
    "Accela",  
    "OpenGov",  
    "Fast Enterprises",  
    "Harris",  
    "Cityworks",  
    "Workday",  
    "CGI"  
  \]  
}  
\`\`\`

Reasoning:

CentralSquare offers ERP, public safety, and community development software to municipalities — directly overlapping with Tyler's core markets and commonly appears on the same state procurement contracts.

Oracle and SAP offer cloud-based ERP systems that compete with Tyler's Munis and Incode platforms, especially in state and higher ed.

Accela directly competes on permitting, licensing, and land management software in local government.

OpenGov overlaps on budgeting, transparency, and procurement platforms across cities and school districts.

Fast Enterprises is a direct competitor for tax and revenue software at the state level.

Harris (a Constellation Software brand) provides similar ERP and finance platforms to school districts and local governments.

Cityworks (Trimble) overlaps on asset management and public works software in municipalities.

Workday is an indirect competitor for HR and financial management in large higher ed institutions.

CGI competes in large state IT system bids, including ERP modernization and data systems.

Example 2:

Company: PowerSchool  
Company Website: https://www.powerschool.com/  
Company Description: PowerSchool is a leading provider of cloud-based software for K-12 education in North America, powering over 50 million students globally and supporting more than 15,000 customers. The company's mission is to unify the education ecosystem with technology that helps educators and students reach their full potential. PowerSchool offers a comprehensive suite of solutions that connect students, teachers, administrators, and families to improve student outcomes. This includes managing student data such as grades, attendance, and schedules, as well as facilitating communication and streamlining administrative tasks. The platform provides a central hub for real-time information on student progress, assignments, and more, empowering parents to participate actively in their child's education. The PowerSchool ecosystem also includes features for special education management, state reporting, finance, human resources, and talent management, among others. Additionally, they offer AI-powered tools to assist educators with assessment creation and personalized learning, as well as career and college planning support. PowerSchool's solutions are designed to be intuitive and easy to use, simplifying operations for institutions of all sizes.

Output:  
\`\`\`json  
{  
  "competitors": \[  
    "Infinite Campus",  
    "Skyward",  
    "Frontline",  
    "Edupoint",  
    "SchoolMint",  
    "Blackboard",  
    "Canvas",  
    "Illuminate",  
    "Aeries",  
    "FACTS"  
  \]  
}  
\`\`\`

Reasoning:

Infinite Campus, Skyward, and Edupoint are direct SIS competitors used by public K–12 districts across the U.S.

Frontline competes in the talent management, special ed, and administrative tools categories.

SchoolMint offers enrollment and school choice platforms used by public districts, competing with PowerSchool's Registration product.

Blackboard and Canvas are LMS rivals in K–12 and higher ed, overlapping with PowerSchool Learning (formerly Haiku).

Illuminate (now owned by Renaissance) overlaps in assessment and analytics solutions in K–12.

Aeries is widely used in California as an SIS, competing directly.

FACTS (Nelnet) offers SIS and LMS tools to K–12, primarily private, but has some public charters, creating overlap in certain SLED spaces.

Example 3:

Company: CivicPlus  
Company Website: https://www.civicplus.com  
Company Description: CivicPlus is a technology company offering a comprehensive suite of software solutions designed to modernize local governments. Their Modern Civic Impact Platform helps municipalities streamline operations, enhance resident engagement, and build public trust through products such as customizable websites, recreation management software, mass notification systems, and 311 CRM for service requests. CivicPlus also provides tools for community development, agenda management, and codification, aiming to create a unified and efficient experience for both government staff and citizens.

Output:  
\`\`\`json  
{  
  "competitors": \[  
    "Granicus",  
    "OpenGov",  
    "ProudCity",  
    "Municode",  
    "Bang the Table",  
    "Revize",  
    "Vision",  
    "Rock Solid",  
    "CityBase",  
    "Code Publishing"  
  \]  
}  
\`\`\`

Reasoning:

Granicus is the most frequent competitor — both offer website CMS, digital services, and civic engagement tools to local governments.

OpenGov competes on transparency portals and digital permitting workflows.

ProudCity and Revize are newer digital government CMS providers with growing city client bases.

Municode competes both on website hosting and codification services.

Bang the Table (now part of Granicus) overlaps on community engagement.

Vision (now part of CivicPlus, but historically a competitor) was a top website vendor for cities.

Rock Solid provides citizen engagement apps to municipalities.

CityBase competes on digital payments and service interfaces for cities.

Code Publishing is a rival in the municipal code hosting and publishing space.

Example 4:

Company: Accela  
Company Website: https://www.accela.com/  
Company Description: Accela is a leading provider of cloud-based software solutions for government agencies, empowering them to build communities, grow businesses, and protect residents. Their platform, the Civic Platform, offers a suite of applications designed to streamline various government functions, including building and planning, business licensing, environmental health, and fire prevention. Accela's solutions aim to improve efficiency, enhance transparency, and foster better citizen engagement by automating workflows, simplifying processes, and providing accessible online portals for residents and staff alike. The company supports city, county, and state governments, helping them modernize their services and adapt to evolving needs.

Output:  
\`\`\`json  
{  
  "competitors": \[  
    "Tyler",  
    "CentralSquare",  
    "Cityworks",  
    "OpenGov",  
    "Clariti",  
    "BasicGov",  
    "ePermitHub",  
    "SmartGov",  
    "CivicPlus",  
    "Unqork"  
  \]  
}  
\`\`\`

Reasoning:

Tyler and CentralSquare compete in permitting, licensing, and code enforcement systems.

Cityworks is a frequent competitor for public works and asset-related permitting tools.

OpenGov's permitting and licensing suite directly overlaps.

Clariti and BasicGov are cloud-native alternatives to Accela for local governments.

ePermitHub specializes in plan review integration with permitting tools and competes in city RFPs.

SmartGov (Brightly) offers comparable community development tools.

CivicPlus now includes civic service request tools that overlap with light permitting/licensing use cases.

Unqork is used by some cities (e.g. NYC) for building permit systems as a no-code alternative to Accela.

Example 5:

Company: GoGuardian  
Company Website: https://www.goguardian.com/  
Company Description: GoGuardian is an edtech company that offers digital safety and learning solutions for K-12 schools, focusing on protecting students online, managing school devices, and improving classroom instruction. Their core products include GoGuardian Teacher for classroom management, GoGuardian Admin for securing and managing Chromebooks, and Beacon for identifying at-risk students through online activity monitoring. By providing these tools, GoGuardian aims to create a safer and more productive digital learning environment for students and educators.

Output:  
\`\`\`json  
{  
  "competitors": \[  
    "Securly",  
    "Lightspeed",  
    "ContentKeeper",  
    "Linewize",  
    "NetRef",  
    "Impero",  
    "Bark",  
    "Cisco Umbrella",  
    "SafeDNS",  
    "Fortinet"  
  \]  
}  
\`\`\`

Reasoning:

Securly, Lightspeed, and ContentKeeper are the top web filtering and student safety vendors competing in public K–12.

Linewize and NetRef offer real-time filtering and device monitoring for school-issued Chromebooks.

Impero is a UK-based vendor but actively sells classroom management tools to U.S. public schools.

Bark provides AI-based student monitoring tools for safety, competing with GoGuardian Beacon.

Cisco Umbrella, SafeDNS, and Fortinet compete on network-level filtering in public schools and districts.

Company: {{ name }}  
Company Website: {{ url }}  
{% if company\_description %}  
Company Description: {{ company\_description }}  
{% endif %}
