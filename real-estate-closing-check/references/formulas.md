# Closing-check formulas & rates

All figures verified against the RBI Ocala closing (14-Jul-2026). Swap state rates as noted.

## Florida statutory closing charges

| Charge | Formula | Notes |
|---|---|---|
| Doc-stamp tax (note) | `ceil(loan/100)*100 × 0.0035` | $0.35 per $100; base rounds UP to next $100. Mortgage/note only. |
| Intangible tax (mortgage) | `loan × 0.002` | 2 mills. Not rounded. |
| Deed doc-stamp (transfer) | `consideration × 0.0070` | $0.70/$100. **$0 if nominal/related-party** transfer — confirm FL DOR won't reassess. |
| Lender's title (original rate) | `575 + (base−100k)/1000 × 5.00` for base>100k; else `base/1000 × 5.75` | Promulgated. base = loan ↑$100. Reissue credit may apply if prior owner's policy. |
| ALTA endorsements | 8.1 ~$50 (flat); 9-06 ~% of premium; 14 ~$25 | 9-06 scales with loan. |

**Other states:** replace the three tax/title formulas. Title premiums are promulgated
(fixed by state) in FL/TX and filed/negotiable elsewhere. Doc-stamp/intangible/mortgage-tax
vary widely (e.g., NY mortgage recording tax, PA/transfer taxes). Always confirm the
current state rate before asserting a statutory number is "correct".

## Interest & per-diem

- **Actual/360** (hard-money standard): `per_diem = principal × rate ÷ 360`.
  Effective annual = `rate × 365/360` (e.g., 8.750% → 8.872%).
- **Stub / prepaid interest** at closing = `disbursed × rate ÷ 360 × days_to_1st_of_month`.
  This is INTEREST, not a fee — exclude it from the fee load in any all-in-rate calc.
- Non-Dutch = interest only on **drawn** funds (not the holdback). Dutch = on full commitment.

## All-in effective rate (interest-only bullet, fully drawn)

```
net_proceeds = face − fees            # fees EXCLUDE prepaid interest
monthly_interest = face × rate × 365/360 ÷ 12
cashflows = [+net_proceeds, −int, −int, …, −(int + face)]   # 12 months
effective_APR = 12 × monthly_IRR(cashflows)
```

Report two numbers:
- **All-in** = every closing cost as fee load (incl. FL tax/title/insurance).
- **Lender finance-charge only** = origination + UW + legal + appraisal + feasibility
  (strip third-party/statutory) — the rate the lender effectively earns.

**Caveat:** "fully drawn" is the standard basis (hard-money reserves are usually sized as
N months' interest on the *full* face — check: `reserve == face × rate × months/12` proves it).
If the loan draws slowly, interest is lower but fixed fees spread over a smaller average
balance → effective rate on money-actually-used rises *above* the fully-drawn figure.

## Cost-percentage lenses

- **Cost / loan face** — the headline ("closing costs are X% of the loan").
- **Cost / cash disbursed at close** and **/ cash-out to borrower** — the real out-of-pocket
  bite when most of the loan is construction holdback (much higher; always label the denominator).
- **Category split**: lender fees | title & settlement | govt/statutory (unavoidable) |
  insurance | recording. Separate **negotiable** (lender/soft-title) from **fixed** (statutory).

## Ratio / proportion benchmark (comparing draft versions)

- `loan_ratio = latest_loan / initial_loan`; `house_ratio = latest_houses / initial_houses`.
- Statutory & percentage fees should scale **exactly** with loan_ratio (and be
  percentage-identical across drafts) — that's the proof they're rate-locked, not padded.
- `cost_ratio / loan_ratio > 1` ⇒ costs grew faster than the loan → find the new scope
  (usually added insurance / deed conveyance), don't assume padding.
- Per-unit normalization (÷ houses): loan/ARV/construction per house should be within a few
  percent if the deal scaled cleanly.

## Discrepancy checklist

1. Entity name + **jurisdiction** consistent (Articles/EIN vs. settlement)? Foreign-LLC registered to hold the property?
2. **Property set** identical across term sheet → proposal → settlement? (A different collateral set ≠ "one more house".)
3. **House count** consistent across all docs?
4. **Origination** ≤ term-sheet rate? (Watch broker↔origination relabeling; compute % = fee/loan.)
5. **Deposit** credited (line 201 on the ALTA)? Blank + low appraisal/feasibility ⇒ prepaid, un-credited.
6. "Waived" fees that reappear under a new label.
7. Any fee whose ratio exceeds a defensible per-unit scale (soft title fees are the usual offenders).
8. Cross-collateralization / partial-release / extension / default-rate — in the Note, not the settlement.
