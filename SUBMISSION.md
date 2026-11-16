# Idea submission text (Tech4Bharat, Round 1)

**Theme:** MSME Finance and Compliance
**Problem statement:** 3.1 Micro enterprises lose time and profit to compliance paperwork (Agentic AI)

**Project Title**

Billbo: no more bag of bills. WhatsApp AI agents that prepare GST paperwork and never file it

**Brief about your idea**

Every small trader has a bag of bills waiting for the accountant. Billbo empties it daily. It is a team of AI agents inside WhatsApp: the owner forwards a bill photo or speaks a voice note in Kannada, Hindi or English, and Billbo reads it, keeps the books, warns when a supplier's filing puts input credit at risk, prepares e-way bill drafts before goods leave, explains notices in plain language, and reminds about due dates. At month end the accountant gets a sorted, checked, filing-ready pack. Billbo prepares; the owner or accountant files. Our target: 15-20 hours of monthly paperwork down to under 3, and accountants able to serve many more clients.

**Detailed explanation of the idea**

THE PROBLEM
Micro enterprises just above the GST threshold pay Rs 1,500-3,000 per filing and lose 15-20 hours a month to paperwork. Bills pile up in a bag or a WhatsApp chat, e-way bills are made at the last minute, and the first sign of trouble is often a notice. Input credit now flows only from what suppliers report (GSTR-2B and the Invoice Management System), so one careless supplier quietly costs the owner real money.

A DAY WITH BILLBO
Ramesh runs a plastics trading shop in Hubballi. At 11 am he photographs a purchase bill and forwards it to Billbo. In seconds: "Saved. Mahadev Plastics, Rs 40,120." At 4 pm he sends a voice note in Kannada about a Rs 74,500 order going to Pune. Billbo replies: "This needs an e-way bill. Draft is ready, send the vehicle number." On the 12th Billbo warns: "Mahadev Plastics has not reported two invoices. Rs 8,280 of your credit is at risk. Shall I draft a reminder?" On the 18th his accountant opens a dashboard where Ramesh's month is already sorted and reconciled, and Ramesh gets a 60-second voice note explaining what he is about to sign.

HOW IT WORKS: SIX AGENTS, ONE ORCHESTRATOR
1. Intake Agent: reads bill photos, PDFs and voice notes; extracts GSTIN, invoice number, HSN, value and tax; checks the arithmetic; asks one short voice question when unsure instead of guessing.
2. Ledger Agent: posts each bill to sales and purchase registers the same day.
3. ITC Guard Agent: matches purchases against supplier filings, shows rupees of credit at risk, drafts supplier reminders, and builds a Supplier Scorecard showing which suppliers file on time, so the owner knows whom it is safe to buy from.
4. Dispatch Agent: when a sale crosses the e-way bill limit for that route, prepares the draft and checks documents before the truck leaves.
5. Return and Deadline Agent: tracks GSTR-1, GSTR-3B and TDS dates, drafts return summaries, and explains them by voice.
6. Notice Helper Agent: the owner photographs a notice; Billbo explains what it means, how urgent it is, and prepares the papers the accountant will need.
The orchestrator routes each message, keeps an audit trail of every decision, and sends low-confidence items to the accountant.

WHY IT STAYS CORRECT WHEN RULES CHANGE
The AI reads, routes and explains. It never calculates tax. Every rate, limit and due date comes from a deterministic rule engine made of versioned "rule cards", each with its source and effective date. A rule change is a one-card update, and affected owners get a plain-language voice alert. We have already built and tested this core (rule cards, credit reconciliation, e-way check) on synthetic data.

THE LINE WE DO NOT CROSS
Billbo prepares, it never files. Filing stays with the owner or a professional and is simulated on our mock GST portal during the hackathon. Anything that leaves the chat needs the owner's approval.

BUILT FOR BHARAT
No new app to learn. Voice-first, vernacular, works on a low-cost Android phone, light on data, and asynchronous so patchy networks do not break it.

WHY NOT EXISTING APPS
Billing and accounting apps expect the owner to type entries into software. Our user will not. Billbo needs zero data entry, lives where the bills already are, and is designed to make the accountant faster instead of replacing him.

TECH STACK
Lyzr agents for orchestration, a vision LLM for bill reading, Indian-language speech (Bhashini / open ASR-TTS), Python rule engine, FastAPI + PostgreSQL, WhatsApp Cloud API, accountant web dashboard, mock GST and e-way bill sandbox.

BUSINESS MODEL
We sell through accountants, not against them: sorted, reconciled books let one accountant carry more clients, so he brings us his whole client list. Target price Rs 199-299 per business per month, well below one filing fee. India has about 1.67 crore active GST registrations (June 2026), roughly three in four of them proprietorships. Later: with consent, a verified compliance record that helps the owner get credit from MSME lenders.

WHAT WE WILL MEASURE
Hours of paperwork per month, input credit saved, late fees avoided, consignments held, clients per accountant.

PROTOTYPE PLAN
Week 1: bill intake and registers on WhatsApp. Week 2: ITC Guard, Supplier Scorecard and e-way drafts on the mock portal. Week 3: return pack, Notice Helper, accountant dashboard, and a field test with local traders and an accountant.
