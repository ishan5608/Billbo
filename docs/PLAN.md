# Tech4Bharat hackathon plan: Billbo (Problem 3.1)

## Key dates

| Date | Milestone |
|---|---|
| 20 Nov 2026, 11:59 PM | Registration, team formation and idea submission close |
| 23 Nov 2026 | Shortlist announced; prototype round opens |
| 15 Dec 2026, 11:59 PM | Prototype submission closes |
| 27 Dec 2026, 9 AM–6 PM | Grand finale and pitch, Bangalore Palace |

Team size 1–4. Judged on technical merit and entrepreneurial potential. Prizes: ₹1,00,000 / ₹50,000 per theme, ₹3,00,000 grand prize.

## Phase 0: before 20 Nov (now)

- [ ] Confirm all team members are registered and added on HackCulture
- [ ] Review and save the idea submission (SUBMISSION.md)
- [ ] Push this folder to GitHub and paste the link in the form (the demo in `demo/` runs with plain Python)
- [ ] Field visits: 3 shop owners / traders + 1 accountant. Ask the six field questions from the problem sheet, plus "how many more clients could you carry if half the sorting arrived done?"
- [ ] Add one real quote and one real number from the field to the submission before the deadline
- [ ] Optional: 5-slide deck (problem, solution, how it works, business model, plan)

## Phase 1: prototype, 23 Nov – 15 Dec

**Week 1 (23–29 Nov): capture and books**
- WhatsApp webhook + FastAPI gateway (use WhatsApp Cloud API test number)
- Intake Agent: bill photo → structured JSON, GSTIN and arithmetic validation
- Ledger Agent: sales / purchase registers in PostgreSQL
- 30 synthetic bills (printed, handwritten, blurry) as a test set; track extraction accuracy

**Week 2 (30 Nov – 6 Dec): the money features**
- Mock GST portal with synthetic GSTR-2B / IMS data
- ITC Guard: reconciliation, credit-at-risk amount, supplier reminder draft
- Dispatch Agent: e-way bill draft and document check on mock sandbox
- Extend the rule engine (already working in `demo/`) with more rule cards; Supplier Scorecard

**Week 3 (7–15 Dec): finish and prove**
- Return & Deadline Agent: draft GSTR-1 / 3B summary, voice explainer in Kannada / Hindi
- Notice Helper: notice photo → plain-language explanation
- Accountant dashboard: client list, flagged items, download pack
- Field test with the same 3 owners and accountant; record time saved
- Demo video (3 min), README, submit by 13 Dec with a 2-day buffer

## Phase 2: finale prep, 16 – 26 Dec

- Pitch deck: problem → live demo → field results → business model → ask
- Rehearse a 5-minute pitch and a 2-minute demo that works offline (recorded fallback)
- Prepare answers: "why won't accountants resist this?", "what if the AI is wrong?", "how do you handle rule changes?", "why you, not Tally / Vyapar / ClearTax?"

## Suggested roles (4 people)

| Role | Owns |
|---|---|
| Agent / backend lead | Orchestrator, agents, rule engine |
| Data / AI | Bill extraction, speech, accuracy test set |
| Frontend | Accountant dashboard, mock portal UI |
| Product / field | Interviews, business model, pitch, demo video |

## Minimum demo (if time runs short)

Bill photo on WhatsApp → entry in register → ITC-at-risk alert → e-way draft → month-end pack on accountant dashboard. Everything else is a bonus.

## Risks

| Risk | Mitigation |
|---|---|
| Handwritten bills read wrongly | Confidence score, ask-back question, accountant review queue |
| WhatsApp API approval delays | Use the Cloud API test number; Telegram bot as fallback for demo |
| No real GST API access | Mock portal with synthetic data (filing is simulated by the rules anyway) |
| Tax rules wrong or outdated | Rule cards with sources, reviewed by a practising accountant |
| Scope creep | Build the minimum demo first, in order |
