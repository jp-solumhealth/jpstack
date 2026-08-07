---
name: real-estate-closing-check
description: >
  Use for closing & ALTA QA review of a real-estate loan — reconciling the settlement statement /
  ALTA / Combined Grid / HUD-1 against the governing terms AND reviewing the loan document package
  (Note, Mortgage, Loan Agreement, Guaranty) as borrower's counsel before signing. Triggers:
  "check the term sheet and the ALTA", "closing QA", "review this closing", "settlement statement",
  "reconcile the loan", "is this closing ok", "review the loan documents", "shark clauses",
  "what's the all-in rate", "closing costs as % of loan", "compare initial vs latest draft",
  "release / partial release terms", "side letter", "the lender refused our changes",
  hard-money / construction / cash-out / bridge / fix-and-flip closings, or any Combined Grid /
  ALTA / loan-package PDF dropped in with intent to vet it before signing.
---

# Real-Estate Closing & ALTA QA Review

End-to-end QA of a loan closing: verify every number from the source PDFs, review the legal package
for traps, rank findings by risk, negotiate in the user's voice, and leave the borrower with the
protections they control. **Cite the primary PDF for every figure and quote actual clause text for
every legal finding. Never trust a summary; show the math.**

## When to use

- A settlement statement / ALTA / loan package arrives and needs vetting before signing.
- The user asks for the all-in rate, cost percentages, draft-vs-draft comparison, a legal review of
  loan documents, negotiation emails, or what to do when the lender refuses changes.
- Construction, cash-out, bridge, hard-money, fix-and-flip closings.

Not for: drafting the lender's documents, or routine conforming purchases with nothing to reconcile.

## Phase 1 — Identify the RIGHT documents

Multiple near-identical drafts circulate. Before anything: confirm each doc's loan amount, property
addresses, entity, and date. Discard stale term sheets, drafts for different properties, and
different transactions entirely. md5 files to catch "(1)" duplicates. Governing terms = the latest
term sheet / loan-results proposal; live closing = the newest settlement draft. If a PDF extracts
near-zero text it's a scan — request a text copy. `extract_text()` in the script reads PDFs.

## Phase 2 — Numbers QA (the engine)

`scripts/closing_check.py` — verified check functions + one-call `report(deal)`. Self-test (RBI
Ocala deal) must print ALL PASS: `python3 scripts/closing_check.py`. Hand-key figures into the deal
dict (see `EXAMPLE_RBI_OCALA`), then verify: footing to the penny · waterfall
(cash = loan − holdback − charges) · FL statutory (doc-stamp, intangible, promulgated title) ·
cost % of loan by line and category · all-in effective APR (exclude prepaid/stub interest from the
fee load — it double-counts) · ratio benchmark across draft versions (statutory items must be
percentage-identical; per-house normalization). Formulas: `references/formulas.md`.

## Phase 3 — Legal & document QA

Work `references/legal-review.md` top to bottom: document inventory (missing ≠ favorable) → Note →
Loan Agreement/construction mechanics (reserve custody, draws, schedule EoDs, replenishment,
**partial release mechanics** — the exit lives here) → Guaranty (completion scope, contribution
waiver → private contribution agreement is mandatory) → shark-clause sweep with verdicts → Events
of Default matrix (notice/cure/materiality per trigger).

## Phase 4 — Findings, ranked

Priority framework (legal-review.md §6): MUST FIX (data fields — survive any refusal) · HIGH
(negotiate before signing) · MEDIUM (push, accept if refused). Rank by dollars and by "does this
block the exit." Deliverables: legal-review HTML report (priority dashboard, doc-by-doc, EoD
matrix, redlines) and a clause revision schedule HTML (current clause / plain comment / proposed
language / priority badge). Plain language, no AI tells, legal wording only inside quoted clauses.

## Phase 5 — Negotiate; handle refusal

Emails in the user's saved tone standard (see legal-review.md §9). When the lender says "we don't
change our documents" — expected from form lenders — run the refusal playbook (§7): side letter /
written administration confirmation, data-field corrections, internal substitutes, close/walk
decision on economics + conduct, not form aggressiveness.

## Phase 6 — Borrower-side legal requirements

legal-review.md §8: entity consents matching the operating agreements, foreign qualification, FL
NOC sequencing, affidavit accuracy, insurance binders sighted, wire callback, contribution
agreement. These need no lender consent and carry the residual risk after a refusal.

## Phase 7 — Project economics (when asked)

Monthly cash-flow model on verified inputs: draws → interest on drawn balance → releases → payoff.
Report profit, ROI/ROA on total cost, cash-on-cash on peak equity, annualized IRR, break-even sale
price, and scenarios (model pace / actual historical pace / slip / price stress). State the sunk-
equity timing convention. Check every scenario against the draw-cutoff and maturity dates.

## Red flags — stop and confirm

- A draft whose property/entity/loan doesn't match the current deal → wrong doc.
- Blank "Deposit" line while appraisal/feasibility are far below estimate → prepaid, uncredited.
- "Waived" fees reappearing under a new label (broker ↔ origination); fee = exactly 1.00% of face.
- Per-diem days vs stated period mismatch (count the days; 15 ≠ 16).
- Release conditioned on "no EoD ever" + adjustable prices when repayment = piecemeal sales.
- Late charge on "any payment due" → reaches the balloon (≈5% of face).
- ACH account status itself a Default; MAC at "sole judgment"; no cure on non-monetary covenants.
- No extension right + final-draw-conditions-as-EoD ≥90 days pre-maturity → the schedule wall.
- Signature capacity ("Member" vs "Manager") contradicting the operating agreement.

## Output

Never inline-dump full deliverables. Save to the deal's project folder: CFO reconciliation memo
(MD), legal review + clause schedule (standalone HTML, print-styled, priority badges), financial
model (HTML). Lead every summary with a verdict, then flags ranked by dollars. Real worked example:
`~/Documents/Claude/Financials/rbi-ocala-construction-loan/` (July 2026).

## Common mistakes

- Reconciling against a stale/wrong-deal draft (identity-check first).
- Trusting near-equal totals — offsetting composition shifts hide behind a similar bottom line.
- Double-counting prepaid interest as fee AND interest in the rate.
- Treating a lender's form refusal as the end — the side letter and data fields survive it.
- Reviewing the ALTA but not the loan documents: the settlement statement carries the costs; the
  Note/Mortgage/Guaranty carry the risk.
