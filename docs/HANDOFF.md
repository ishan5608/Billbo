# Billbo handoff notes

Read this first if you are picking the project up (a teammate, or an AI assistant on any model).

## What this is
Billbo is team welovefrontshots' entry for Tech4Bharat (GAVS Hackathon 2026), theme MSME Finance and Compliance, problem 3.1. Team: Ishan Ahirwar, Jaideep Mudigolam, Kush Saraogi, NIT Karnataka, Surathkal. Tagline: "No more bag of bills." Billbo is a set of WhatsApp AI agents that prepare a micro business's GST paperwork and never file it.

## Dates
- 20 Nov 2026, 11:59 PM IST: idea submission closes on HackCulture
- 23 Nov: shortlist; prototype round runs to 15 Dec, 11:59 PM
- 27 Dec: finale at Bangalore Palace

## Where everything is
Local folder: `C:\Users\ITS Laptop\Desktop\Hackathon\T4B\billbo` (a git repo, branch `main`).
GitHub: https://github.com/ishan5608/Billbo (public; renamed by Ishan, the local `origin` points here).

| Path | What |
|---|---|
| `SUBMISSION.md` | Title, brief and detailed explanation for the HackCulture form |
| `Billbo_Deck.pdf` | 6-slide deck for the form's upload box (an editable Slides copy exists in Claude) |
| `docs/PLAN.md` | Week-by-week plan, roles, risks |
| `prototype/` | Working prototype (run `python run.py`, open http://127.0.0.1:8000) |
| `rules/rule_cards.json` | Every limit, due date, GST rate, price and notice explanation |
| `demo/` | Small command-line demo of the rule engine |

The claude.ai project "T4B" holds copies of the plan and submission text.

## Decisions already made (do not change without asking the team)
- Name Billbo; palette "Ledger green" (cream `#FAF6EE`, ink `#1E2B25`, green `#1F7A5A`, amber `#F2B441`), with a matching dark theme.
- Business model: Free for owners; Accountant plan at a target of Rs 99 per client per month (main revenue); Billbo Plus for owners at a target of Rs 149 per month. First town: Mangaluru.
- Six agents: Intake, Ledger, ITC Guard, Dispatch, Returns & Deadlines, Notice Helper, plus an orchestrator.

## Rules the code must keep
1. Prepare, never file. No agent code may write to `filings` or generate a real e-way bill; only a person on the mock portal does. A test enforces this.
2. No AI arithmetic on tax. Numbers come from `rules/rule_cards.json` through `prototype/billbo/rules.py`.
3. Anything that leaves the chat needs the owner's approval (for example supplier reminders are drafted, the owner forwards them).
4. Free-plan owners still get safety warnings (e-way limit, notice deadline); only the convenience features are held back.
5. Standard library only in the prototype, so it runs with plain Python and no installs.
6. Synthetic data only.

## How to check your work
```
cd prototype
python -m unittest discover -s tests      # 16 tests must pass
python run.py --reset                      # then click through the demo script on the home page
```
Check both light and dark themes after any change to `prototype/web/`.

## What is simulated in the prototype
- Bill photos and voice notes are samples from `prototype/data/samples.json`. Plug a real vision model into `read_photo()` in `prototype/billbo/agents/intake.py`.
- The chat stands in for WhatsApp; the GST portal is a mock.
- Hindi and Kannada replies in `prototype/billbo/i18n.py` cover only the most common messages and need a native speaker's review.

## Open items
- The HackCulture form is not confirmed as filled and saved. Paste from `SUBMISSION.md`, upload `Billbo_Deck.pdf`, save before 20 Nov.
- Keep GitHub up to date: push new local commits, and add https://github.com/ishan5608/Billbo to the form's links field.
- Field interviews (3 owners, 1 accountant) to replace target numbers with real ones: prices, hours saved, clients per accountant.
- Rule cards, GST rates and notice explanations are illustrative; an accountant must review them.
- Numbers labelled "target" (Rs 99, Rs 149, "under 3 hours") are assumptions. Keep them labelled as targets.
- Known git quirk when an assistant commits through the desktop bridge: lock files under `.git` cannot be deleted, so move them aside (`stale-*`) after each commit.

## Next build steps (from PLAN.md)
1. Connect the orchestrator to a WhatsApp Cloud API test number.
2. Real bill reading and speech in the Intake agent.
3. Extend rule cards; accountant review of every card.
4. Field test and a 3-minute demo video.
