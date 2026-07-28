# Legal & document QA — closing package review

Checklists distilled from the RBI Ocala closing (July 2026, 172-page Lightning Docs package).
Use after the numbers QA passes. Quote actual clause text for every finding; never paraphrase-only.

## 1. Document inventory (flag anything referenced but missing)

Core: Promissory Note · Mortgage/Deed of Trust + ALR + fixture filing · Loan/Construction Loan &
Security Agreement + draw procedures/reserve forms · Guaranty(ies) · Environmental indemnity ·
UCC-1s · Closing instructions · Balloon disclosure · Compliance agreement · Settlement statement.
Support: title commitment + CPL · insurance binders · entity docs + resolutions · appraisals ·
payoff letters · wire instructions. **Missing is not presumed favorable — say "unable to confirm."**

## 2. Promissory Note checklist

- Principal matches settlement statement to the cent (a 7-cent mismatch happens).
- Rate, day count (30/360 vs actual/360 — actual/360 = quoted rate × 365/360 effective), stub math.
- Payment: verify the stated monthly amount = disbursed × rate ÷ 12 (proves non-Dutch) or face × rate ÷ 12 (Dutch).
- Maturity date + balloon disclosure consistency.
- Late charge: % , grace days, and **whether it reaches the balloon** ("any payment due" = it does; ≈5% of face exposure).
- Default rate: %, trigger (notice/cure or "sole discretion without notice"), prospective vs retroactive, capitalization of unpaid interest (compounding), usury ceiling (FL criminal usury 25%).
- Prepayment: penalty/lockout/minimum interest/exit fee (compare to term sheet).
- Due-on-sale scope: does "transfer of any interest in Borrower" have a materiality floor? PACE/junior liens?
- Payment mechanics: ACH auto-debit? **Is account status itself a Default?** (classic trap)
- Acceleration notice waivers, usury savings clause.

## 3. Loan Agreement / construction mechanics checklist

- Reserve custody: escrowed or **lender-retained/net-funded** (Lightning Docs standard: lender keeps it,
  no segregation duty — borrower carries lender performance risk; note it plainly).
- Draw mechanics: reimbursement-only? per-draw inspection fee, lead time, lien waivers, photos/receipts,
  subcontract approval thresholds, Authorized Borrower Representative list required pre-draw.
- **Schedule EoDs**: start-by date, permits-by date, stoppage > N aggregate days, defect cure days,
  Action Items at lender discretion, **final-draw conditions ≥90 days pre-maturity as an EoD** (double
  punishment — flag), post-completion appraisal reserve sweep.
- Reserve replenishment (margin call): fuse length, calculation requirement, internal inconsistencies
  (check §2.8.3 vs §7.1.x — different clocks for the same duty).
- **Partial release**: right vs sole discretion · "no EoD ever" vs "no continuing EoD" · fixed vs
  adjustable prices · price as % of allocation (115–125% is market) · last-property exclusion ·
  what's due at release (price + interest + actual costs only?) · turnaround.
- Cross-default scope: bounded to debts owed to this lender/affiliates, or all debts anywhere?
- Extension: exists? fee? conditions? (No extension right + hard balloon = the schedule wall.)
- POA: pre-default or post-default only.
- Events of Default matrix: for each trigger — notice? cure? materiality floor (judgments!)?
  subjective (MAC "sole judgment", insecurity, tenant/gov violations without notice)?

## 4. Guaranty checklist

- Type: payment / performance / **completion** (construction adds completion = personal overrun funding).
- Cap? burn-off at CO? continuing/reinstatement?
- **Modification without guarantor consent** while liability unaffected (standard form; flag anyway).
- **Subrogation AND contribution waivers** → inter-guarantor rights erased → a private
  **contribution agreement among guarantors is mandatory** (needs no lender consent).
- Guarantor addresses individually correct (notices → cure clocks).

## 5. Shark-clause sweep (verdict each: NOT PRESENT / PRESENT-BOUNDED / PRESENT-FLAG)

Confession of judgment · equity/profit participation · interest on undisbursed funds · minimum
interest/exit/yield maintenance · open-ended fees · insecurity/MAC at sole judgment · unilateral
discretion (draws, budgets, valuations) · aggressive springing recourse · bankruptcy waivers &
affiliate-bankruptcy EoDs · unlimited indemnities (lender's own negligence? post-repayment?) ·
pre-default POA · dragnet/all-debts collateral clauses · jury waiver (customary; note it).

## 6. Priority framework for findings

- **MUST FIX (data, not language)**: notice addresses, per-diem day counts, amount mismatches,
  P.O.C. notations. Lenders who refuse redlines cannot refuse these.
- **HIGH (negotiate before signing)**: release-as-a-right; guaranty consent/burn-off; late charge on
  balloon; default rate without notice; no non-monetary cure; subjective MAC/code defaults.
- **MEDIUM (push, accept if refused)**: judgment floors, replenishment fuse, ACH clause, POA timing.
- Rank by dollars and by "does this block the exit"; the release mechanics outrank everything when
  repayment = selling collateral piecemeal.

## 7. Lender-refusal playbook ("we don't change our documents")

Standard for form lenders (docs are resale templates). Do not re-argue language. Fall back to:
1. **Side letter / written confirmation of administration** — "confirms, does not amend"; use
   "does not intend to" instead of "shall not"; even an email reply is course-of-dealing evidence.
   For releases confirm: prices honored while current · cured defaults don't disqualify ·
   amounts due limited to price + interest + actual costs · turnaround days · last-property payoff process.
2. **Data-field corrections** — always still available.
3. **Internal substitutes**: contribution agreement (guaranty), autopay + funded account (ACH default),
   compliance calendar (schedule EoDs), plan-B refinance quote before completion (release risk —
   free prepayment is the escape hatch; verify prepay is free before relying on this).
4. Decide close/walk on economics + lender conduct, not on form aggressiveness — landmine clauses
   only fire on default.

## 8. Borrower-side legal requirements (independent of the lender)

- **Entity authority**: manager/member consents matching the operating agreements (check
  manager-managed vs member-managed vs signature-block capacity); unanimous consent cures ambiguity.
- Foreign LLC qualification where entity ≠ property state (e.g., WY LLC + FL realty → Sunbiz).
- Good standings; brand-new entities need resolutions + incumbency.
- **FL NOC sequencing** (construction underway = live issue): old NOCs terminated before mortgage
  records; NEW Notice of Commencement records AFTER the mortgage, posted on site — wrong order lets
  construction liens prime the mortgage.
- Deed doc-stamps basis in writing when re-vesting at $0 consideration.
- Affidavit accuracy (owner/no-lien, SB 264, business-purpose): false statements = fraud exposure +
  springing recourse.
- Insurance binders sighted before closing: both borrowers named, lender as mortgagee/loss payee,
  limits ≥ construction value, term ≥ maturity.
- Wire-verification callback on a known number before funds move.
- Contribution agreement signed at/near closing.

## 9. Communication standards

Negotiation emails follow JP's saved tone standard (memory: email-negotiation-tone-standard): warm
open/close, asks attributed to "our attorney," per-item {current-state one-liner + "Proposed wording:"
quote}, mutual-benefit + market-standard framing, soft deadline, plain text. When standing firm,
state ONE signing condition clearly and keep the rest as requests. Deliverables: clause revision
schedule as standalone HTML (current clause / plain comment / proposed language / priority badge);
legal review as standalone HTML report with priority dashboard.
