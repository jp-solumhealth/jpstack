# Construction draw mechanics

The lender side of the package: how much to ask for, what has to be attached, and the
reconciliations that keep a request from being refused.

## Never draw 100% of completed work

The advance rate is **holdback ÷ total construction cost to be funded**, not 100%.

On the RBI Ocala loan: $485,900.91 reserve ÷ $533,790.15 construction = **91.0285%**. The
borrower's equity funds the other 8.97% as it goes.

Why this matters more than it looks. Drawing 100% of completed work front-loads the reserve
against early activities and leaves it visibly short of the remaining cost. A typical
construction loan (RBI §2.8.3) lets the administrator refuse further disbursements the
moment the reserve looks insufficient, *and* demand the shortfall in cash within days, with
its own judgment "final and conclusive". Drawing pro rata keeps

    remaining reserve ÷ remaining cost  ==  the advance rate

true at every single draw, which is a one-line answer to that objection. `draw_calc.py draw`
asserts this identity and prints PASS; if it ever fails, the schedule has drifted.

The same rate also exhausts the holdback to exactly $0.00 at the final activity, so there is
no stranded reserve and no final-draw shortfall. `draw_calc.py schedule` asserts the
residual is under a cent.

## Reconcile against the contract schedule of values, not just the ledger

There are usually three schedules and they do not agree:

| Schedule | What it is | Used for |
|---|---|---|
| Cost ledger | What was actually spent, per line item | The **waivers** |
| Contract schedule of values | The GC agreement's phase pricing (Exhibit D) | The independent cross-check |
| Draw schedule | What the request claims | The **lender package** |

Running actual cost against contract phase pricing is the strongest single argument in a
submission — on RBI Draw 1, actual Activity 1+2 cost came in **2.02% under** the contract
phase price, which is the sentence that makes a lender stop reading.

When the draw schedule and the cost ledger disagree, **report the delta, do not silently
pick one**. `draw_calc.py reconcile` prints it per property. On RBI Draw 1 the lender
schedule carried a $600 land survey the ledger had no value for, and roof cover at $3,400
against the ledger's $3,202.03 — $797.97 of hard cost per property, $869.79 with commission,
$2,609.36 across three houses. Two documents making different claims about the same work is
the finding; which one is right is a question for the file, not for the generator.

## Conditions precedent are where draws actually die

Read the disbursement section before building anything. The recurring ones:

- **A completed and signed draw request form.** Check whether the loan even defines one. On
  RBI, Schedule 1 — the "Disbursement Schedule" the agreement points to — is a single
  sentence about the inspection fee. No budget, no line items, no form. That means no agreed
  schedule of values to hold the lender to, and every advance sits in its discretion. The
  borrower must supply the form *and* get written confirmation that its schedule of values
  is the Disbursement Schedule.
- **Authorized Borrower Representative designated in writing, before any draw.** The lender
  is typically not required to honour a request without it. Easy to miss at closing and easy
  to fix, but only before the first request.
- **Lien waivers from the GC and every sub and supplier** for each work item. See
  `fl-lien-waivers.md`. This is the long pole.
- **Notice period.** Usually several business days between request and funding. Count in
  business days and diary it.
- **Inspection fee.** Read whether it is per advance or per property — the difference on a
  three-property, four-draw loan is $1,400 vs $4,200. RBI's Schedule 1 says per advance;
  the model originally assumed per property and overstated the cost by $2,800.
- **Bonds.** Many agreements let the lender require performance and payment bonds in its
  sole discretion as a condition precedent. If the lender's own contractor review flagged
  the GC as high credit risk, get written confirmation bonds are not required.
- **Final draw deadline.** Often all final-draw conditions must be satisfied by a date months
  before the balloon, or it is an event of default and no final draw is owed. Work backwards
  from that date, not from the maturity date.

## Payment allocation across multiple properties

A lender advances against work on **its** collateral. If the borrower runs several builds at
once and pays the contractor in unallocated lump sums, the bank record cannot prove which
property the money funded, and the draw cannot be evidenced.

Fix it at the source: one transfer per property, a `HOUSE | PHASE` memo convention on every
payment, and a contractor statement of account per property. Retrofitting the allocation
after the fact is the single most common blocker on these packages.

## What goes in the submission

1. Draw request form — schedule of values for the activities claimed, per property.
2. Reserve sufficiency test — the pro-rata arithmetic above.
3. Contract reconciliation — actual vs the GC contract schedule of values.
4. Borrower certification in the words the loan agreement requires.
5. ABR designation, if not already on file.
6. Lien waivers — GC plus subs and suppliers.
7. Invoices, workers' comp certificates, proof prior-phase vendors were paid.
8. Document index.

Keep the internal review — the ranked flags, the do-not-send list — as a **separate
document**. It does not go to the lender, and it should not be an appendix to something that
does. The same rule applies to waivers: preparation notes are for the owner and counsel, not
for the contractor's signing copy.

## Traps

- **The borrower certification binds you to the same facts as the waivers.** If the draw
  certifies costs as paid while the payment tracker marks them pending, both cannot be true,
  and the certification is the one with teeth. Resolve before submitting.
- **Placeholder costs.** Future activities in a cost model are often contract placeholders
  copied across every property — identical figures for houses whose earlier activities vary.
  Only draw against activities showing real per-property variance; identical numbers mean
  nobody has costed that phase yet.
- **Transposed digits survive review.** Foot every schedule against its source
  programmatically. `draw_calc.py selftest` exists because a $27 transposition sat in a
  model for weeks.
- **Interest accrues only on drawn principal** on most of these loans. The undrawn holdback
  is free. That is an argument for drawing later and smaller, and it belongs in the
  cash-flow model.
