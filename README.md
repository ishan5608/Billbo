# Billbo

**No more bag of bills.** WhatsApp AI agents that prepare a micro business's GST paperwork and never file it.

Tech4Bharat (GAVS Hackathon 2026) · Theme: MSME Finance and Compliance · Problem 3.1 (Agentic AI)

## The problem

Micro enterprises just above the GST threshold pay ₹1,500–3,000 per filing and lose 15–20 hours a month to paperwork. Bills pile up in a bag or a WhatsApp chat, e-way bills are made at the last minute, and notices arrive before anyone has noticed a problem. Input credit is lost when suppliers file badly.

## What Billbo does

The owner keeps using WhatsApp. Billbo's agents do the paperwork as it happens.

| Agent | Trigger | What it does | What the owner sees |
|---|---|---|---|
| Intake | Bill photo, PDF or voice note | Extracts GSTIN, invoice no., HSN, value, tax; validates; asks back if unsure | "Saved. Sri Traders, ₹18,400" |
| Ledger | Every accepted bill | Posts to sales / purchase registers | Weekly summary voice note |
| ITC Guard | Daily, and before the 14th | Matches purchases with GSTR-2B / IMS; Supplier Scorecard | "₹8,280 credit at risk. Remind supplier?" |
| Dispatch | Sale above the e-way limit | Prepares e-way bill draft, asks vehicle number, checks documents | Draft ready before the truck leaves |
| Return & Deadline | Calendar and rule changes | Drafts GSTR-1 / 3B summaries, reminders, "what you are signing" explainer | 60-second voice note |
| Notice Helper | Photo of a notice | Explains meaning and urgency, gathers papers for the accountant | Plain-language voice note |

An **orchestrator** routes messages, logs every decision, and escalates low-confidence items to the accountant.

## Try the demo

The deterministic core already runs. No AI keys, no network, Python 3.9+ standard library only.

```
python demo/billbo_demo.py
python -m unittest demo/test_billbo.py
```

It reads the rule cards in `rules/rule_cards.json` and synthetic data in `demo/data/`, then shows credit safe to claim, credit at risk with a supplier reminder draft, sales that need an e-way bill, and upcoming due dates. One test changes a single rule card and shows the behaviour change, which is how Billbo handles rule changes.

## Architecture

```
Owner (WhatsApp: photo / voice / text)
        │
WhatsApp Cloud API webhook ──► FastAPI gateway
        │
   Orchestrator (Lyzr)
   ├── Intake Agent ──► vision LLM + ASR (Kannada / Hindi / English)
   ├── Ledger Agent ──► PostgreSQL (registers, audit log)
   ├── ITC Guard ─────► Mock GST portal (GSTR-2B / IMS sandbox)
   ├── Dispatch Agent ► Mock e-way bill sandbox
   ├── Return & Deadline Agent
   └── Notice Helper Agent
        │
   Rule engine (deterministic, versioned rule cards with source + effective date)
        │
Accountant dashboard (web) ◄── filing-ready pack ──► owner / accountant files (simulated)
```

## Guardrails

1. **Prepare, never file.** Filing is done by the owner or a professional; simulated in the hackathon.
2. **No LLM arithmetic on tax.** Rates, thresholds and due dates come from the rule engine. The LLM reads, routes and explains.
3. **Rule cards.** Each rule has a source and an effective date, so a rule change is a one-card update plus a plain-language alert. The cards in this repo are illustrative and must be reviewed by a practising accountant.
4. **Human approval** for anything that leaves the chat.
5. **Synthetic data only** during the hackathon.

## Repo layout

```
demo/                working demo of the rule engine + tests + synthetic data
rules/               rule cards (JSON)
docs/PLAN.md         hackathon plan
SUBMISSION.md        Round 1 idea submission text
(planned) apps/gateway, apps/dashboard, agents/, sandbox/
```
