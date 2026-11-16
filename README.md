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

## Run the prototype

A working prototype is in `prototype/`. It needs only Python 3.8+ (standard library, nothing to install).

```
cd prototype
python run.py
```

Then open http://127.0.0.1:8000. There are three screens:

| Screen | Who it is for | What you can do |
|---|---|---|
| Owner chat | The shop owner | Send sample bill photos, voice notes and notices; Billbo's agents reply |
| Accountant dashboard | The accountant | See every client sorted, clear the review queue, download the filing-ready pack, see the Billbo fee |
| Mock GST portal | The government side | Make a supplier report an invoice, generate an e-way bill, file a return (all simulated, all done by a person) |

The home page has a 2-minute demo script. `python run.py --reset` reloads the demo data.

**What is real:** the six agents, the orchestrator and its routing, the rule engine, credit matching, the Free / Plus plan limits, accountant billing and the audit trail.
**What is simulated:** bill photos and voice notes are samples standing in for a vision and speech model, the chat stands in for WhatsApp, and the GST portal is a mock with synthetic data.

Tests (16, including the rule that no agent code can file a return):

```
cd prototype
python -m unittest discover -s tests
```

There is also a smaller command-line demo of just the rule engine: `python demo/billbo_demo.py`.

## Business model in the prototype

| Plan | Who pays | Target price | In the prototype |
|---|---|---|---|
| Free | Nobody | ₹0 | Bill capture, registers, due dates, safety warnings |
| Accountant plan | The accountant | ₹99 per client per month | Dashboard, review queue, filing-ready pack |
| Billbo Plus | The owner | ₹149 per month | Credit alerts and reminders, supplier scorecard, e-way drafts, notice explanations |

Prices live in `rules/rule_cards.json` and are targets to test in field interviews.

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
prototype/           working prototype: agents, server, three web screens, tests
  billbo/agents/     intake, ledger, itc_guard, dispatch, returns, notice, orchestrator
  billbo/            db, rules, plans, i18n, server
  web/               owner chat, accountant dashboard, mock GST portal
  data/              sample bills, voice notes, notices and seed data (all synthetic)
rules/               rule cards (JSON): limits, due dates, GST rates, prices, notice explanations
demo/                small command-line demo of the rule engine + tests
docs/PLAN.md         hackathon plan
SUBMISSION.md        Round 1 idea submission text
Billbo_Deck.pdf      presentation deck
```
