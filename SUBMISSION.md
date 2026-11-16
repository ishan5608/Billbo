# Idea submission text (Tech4Bharat, Round 1)

**Theme:** MSME Finance and Compliance
**Problem statement:** 3.1 Micro enterprises lose time and profit to compliance paperwork (Agentic AI)

**Project Title**

Billbo: no more bag of bills. WhatsApp AI agents that prepare GST paperwork and never file it

**Brief about your idea**

Every small trader has a bag of bills waiting for the accountant. Billbo empties it daily. It is a team of AI agents inside WhatsApp: the owner forwards a bill photo or speaks a voice note in Kannada, Hindi or English, and Billbo reads it, keeps the books, warns when a supplier's filing puts input credit at risk, prepares e-way bill drafts before goods leave, explains notices in plain language, and reminds about due dates. At month end the accountant gets a sorted, checked, filing-ready pack. Billbo prepares; the owner or accountant files. Our target: 15-20 hours of monthly paperwork down to under 3, and accountants able to serve many more clients.

**Detailed explanation of the idea**

WHAT BILLBO IS
Billbo is a team of AI agents that lives inside WhatsApp and does a micro business's GST paperwork as it happens, not at month end. The owner sends a bill photo or a voice note in Kannada, Hindi or English. Billbo does the rest and hands the accountant a filing-ready pack. Billbo prepares; it never files.

THE PROBLEM
Micro enterprises just above the GST threshold pay Rs 1,500-3,000 per filing and lose 15-20 hours a month to paperwork. Bills pile up in a bag or a WhatsApp chat, e-way bills are made at the last minute, and the first sign of trouble is often a notice. Input credit now depends on what suppliers report (GSTR-2B and the Invoice Management System), so one careless supplier quietly costs the owner real money.

A DAY WITH BILLBO
Ramesh runs a plastics trading shop. At 11 am he forwards a photo of a purchase bill. Billbo replies: "Saved. Mahadev Plastics, Rs 40,120." At 4 pm he sends a voice note about a Rs 74,500 order going to Pune. Billbo: "This needs an e-way bill. Draft is ready, send the vehicle number." On the 12th: "Mahadev Plastics has not reported two invoices. Rs 8,280 of your credit is at risk. Shall I draft a reminder?" On the 18th his accountant opens a dashboard where the month is already sorted and reconciled, and Ramesh gets a 60-second voice note explaining what he is about to sign.

HOW IT WORKS
Six agents, coordinated by an orchestrator that logs every decision and sends doubtful items to the accountant:
1. Intake: reads bill photos, PDFs and voice notes, checks the arithmetic, and asks one short question when unsure instead of guessing.
2. Ledger: posts each bill to the sales and purchase registers the same day.
3. ITC Guard: matches purchases with supplier filings, shows the rupees of credit at risk, drafts supplier reminders, and keeps a Supplier Scorecard of who files on time.
4. Dispatch: prepares the e-way bill draft and checks documents before the truck leaves.
5. Returns and Deadlines: tracks GSTR-1, GSTR-3B and TDS dates, drafts return summaries and explains them by voice.
6. Notice Helper: explains a photographed notice in plain language and gathers the papers the accountant needs.

HOW IT STAYS CORRECT AND SAFE
- The AI reads, routes and explains, but never calculates tax. Every rate, limit and due date comes from a deterministic rule engine built from versioned "rule cards", each with its source and effective date. A rule change is a one-card update plus a plain-language alert to affected owners.
- Filing stays with the owner or a professional, and is simulated on our mock GST portal in the hackathon.
- Anything that leaves the chat needs the owner's approval.
We have already built and tested this core (rule cards, credit reconciliation, e-way check) on synthetic data.

BUILT FOR BHARAT
No new app, no typing, no English needed. Voice-first, works on a low-cost Android phone, light on data, and asynchronous so patchy networks do not break it. Existing billing apps expect the owner to enter data; Billbo needs none.

BUSINESS MODEL
The owner uses Billbo; the accountant pays for it.
1. Free for owners: bill capture, registers and reminders, so there is no barrier to starting.
2. Accountant plan, our main revenue: a target of Rs 99 per client per month. Sorted, reconciled books let him serve more clients in the same hours, and he already earns Rs 1,500-3,000 per filing, so the fee pays for itself.
3. Billbo Plus for owners: a target of Rs 149 per month for credit alerts, e-way drafts and notice help, sold by showing the rupees of credit protected that month.
One accountant brings his whole client list, so we grow accountant by accountant, starting in Mangaluru near our campus. Later, with consent, a verified compliance record can help owners get loans, with a referral fee from lenders. The market is about 1.67 crore active GST registrations (June 2026), roughly three in four of them proprietorships. Prices are targets we will test in field interviews.

TECH STACK
Lyzr agents, a vision LLM for bill reading, Indian-language speech (Bhashini / open ASR-TTS), Python rule engine, FastAPI and PostgreSQL, WhatsApp Cloud API, an accountant web dashboard, and a mock GST and e-way bill sandbox.

PLAN AND IMPACT
Week 1: bill intake and registers on WhatsApp. Week 2: ITC Guard, Supplier Scorecard and e-way drafts on the mock portal. Week 3: return pack, Notice Helper, accountant dashboard and a field test with local traders and an accountant. We will measure hours of paperwork per month (target: 15-20 down to under 3), input credit saved, late fees avoided, consignments held, and clients per accountant.
