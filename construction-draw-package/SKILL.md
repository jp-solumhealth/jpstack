---
name: construction-draw-package
description: Build and check the funding package on a construction loan — Florida ch. 713 lien waivers, the draw request, the schedule of values, and the reconciliations behind them. Use when preparing or reviewing a construction draw, generating or amending lien waivers, sizing an advance, or checking whether a contractor should sign a release. Triggers - "lien waiver", "waiver and release of lien", "partial release", "unconditional waiver", "draw request", "draw package", "request a draw", "next draw", "schedule of values", "how much can we draw", "advance rate", "holdback", "construction reserve", "is the reserve sufficient", "the contractor needs to sign", "release of lien for the bank", "what does the lender need to fund". For the closing itself and the loan documents, use real-estate-closing-check. For the title company's settlement statement, use title-closing-review.
---

# Construction Draw Package

Generates the two documents a construction draw runs on — the lien waivers and the draw
request — from one deal config, and recomputes every figure against the source ledger before
anything is signed or submitted.

## When to use

- Preparing a draw request, or checking one before it goes to the lender.
- Generating lien waivers for a contractor, or amending a set already drafted.
- Deciding how much to advance, and proving the reserve stays sufficient.
- Answering "can the contractor sign this yet".

**Not for:** the closing itself, Note/Mortgage/Guaranty review → `real-estate-closing-check`.
The title company's settlement statement → `title-closing-review`.

## The engine

`scripts/draw_calc.py` and `scripts/build_waivers.js`, both driven by a deal config in
`deals/`. **Run both self-tests first, every time.**

```bash
python3 scripts/draw_calc.py selftest        # must print ALL PASS
node scripts/build_waivers.js --selftest     # must print ALL PASS
```

The self-tests reproduce the RBI Ocala Draw 1 package as delivered on 5 Aug 2026 — the three
waiver amounts, the 91.0285% advance rate, all four draws, the holdback exhausting to zero,
and the known $2,609.36 divergence between the two schedules. If either fails, a figure in
the config has drifted. Fix that before generating anything.

```bash
python3 scripts/draw_calc.py waivers   --deal rbi-ocala   # amounts + unpaid exposure
python3 scripts/draw_calc.py draw      --deal rbi-ocala --number 1
python3 scripts/draw_calc.py schedule  --deal rbi-ocala   # all remaining draws
python3 scripts/draw_calc.py reconcile --deal rbi-ocala   # ledger vs draw schedule

node scripts/build_waivers.js --deal rbi-ocala --out /abs/waivers.docx
node scripts/build_waivers.js --deal rbi-ocala --exclude-unpaid   # release only paid work
node scripts/build_waivers.js --deal rbi-ocala --unexecuted       # leave dates blank too
node scripts/build_waivers.js --deal rbi-ocala --form final       # final, not progress
```

`--activities 1 2 3` overrides which activities a draw covers.

## The four rules this skill exists to enforce

**1 — Never release a lien for money the contractor has not received.** Check the payment
ledger before generating, every time. `draw_calc.py waivers` prints the exposure per property
and the reduced amount; `--exclude-unpaid` cuts the consideration and adds a visible deduction
line so the appendix still foots. A lender's requirement for unconditional waivers does not
override this — it means the deal needs a conditional-then-swap sequence, which is in
`references/fl-lien-waivers.md`.

**2 — Advance at the pro-rata rate, never at 100% of completed work.** Holdback ÷ total
construction cost. Drawing 100% leaves the reserve visibly short of remaining cost, which is
exactly the condition that lets a lender refuse the next disbursement and call the deficiency
in cash. The pro-rata rate keeps *remaining reserve ÷ remaining cost* equal to the advance
rate at every draw; the tool asserts that identity and prints PASS.

**3 — Reconcile the schedules, do not pick one.** The cost ledger, the contract schedule of
values and the lender's draw schedule will disagree. Report the delta. Two documents making
different claims about the same work *is* the finding, and the borrower certification in the
draw rests on the same facts as the waivers — they cannot contradict each other.

**4 — The signing copy carries no internal commentary.** Preparation notes, ranked flags and
do-not-send lists are for the owner and counsel. They do not go in the document the
contractor signs or the package the lender receives. Keep them in a separate file — and
remember that removing them takes the warnings out of the document, so surface them in the
covering message instead.

## What is always left blank

Fill everything that is the company's to state. Exactly four fields stay open on every
waiver:

| Field | Completed by |
|---|---|
| `By: ______` | The signatory, in the notary's presence |
| Notary signature | The notary |
| Personally Known / Produced Identification | The notary |
| Type of Identification Produced | The notary |

FS 117.05 requires the notary to complete their own jurat. `build_waivers.js` will not
produce those filled and the selftest asserts it. The jurat *date* is different — pre-filling
it is normal, but if the signing slips, change it in the config and regenerate; never edit
the document.

## Adding a deal

Copy `deals/rbi-ocala.json` and replace. The shape:

| Key | What it carries |
|---|---|
| `contractor` | Legal name, address, licence, principal, `principal_title` and `title_source` |
| `loan` | Face, disbursed at close, holdback, inspection fee and its basis, rate |
| `period` / `execution` | Work period; the DATED line and the jurat day/month/year |
| `waiver` | Form, activities covered in full, partial activities and their factor |
| `properties[].ledger` | Itemised cost per activity — what the **waivers** release |
| `properties[].draw_schedule` | Per-activity totals — what the **draw request** claims |
| `properties[].unpaid` | What the payment tracker still marks outstanding |

Both schedules are deliberately separate so the tool can reconcile them. Then add assertions
to `cmd_selftest` against the real delivered figures — **a deal config with no self-test
assertion is not trustworthy**, and the assertions are what catch a transposed digit.

## Traps

- **The unpaid figure is the one that gets skipped.** It is the only number in the package
  that argues against sending it. Print it, do not bury it.
- **Placeholder costs in later activities.** If Activities 3–5 are identical across
  properties whose Activities 1–2 vary, those are contract placeholders, not costed work.
  Only draw against activities with real per-property variance.
- **Inspection fee basis.** Per advance or per property changes a three-property, four-draw
  loan by $2,800. Read the schedule, do not assume.
- **The GC waivers are not the requirement.** Subcontractor and supplier waivers are a
  separate, much larger set and are the long pole on funding. Start them when the draw is
  scoped.
- **Dates move in threes.** DATED line, jurat date, and the work-through date. Change them
  in the config together.
- **No LibreOffice on this Mac.** To render the docx for proofing, export via Pages
  AppleScript and read the pages with PyMuPDF; `soffice --convert-to pdf` fails.

## Reference

`references/fl-lien-waivers.md` — the four statutory ch. 713 forms, the conditional vs
unconditional conflict and the swap sequence that resolves it, the exceptions paragraph,
commission on in-progress activities, who must sign, execution and notarisation rules.

`references/draw-mechanics.md` — the pro-rata advance rate and the reserve sufficiency proof,
the three schedules and how to reconcile them, conditions precedent that kill draws, payment
allocation across multiple properties, and what goes in the submission.
