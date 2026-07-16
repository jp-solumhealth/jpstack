# Underwriting traps — small-residential buy-vs-build

Each trap below was hit (and fixed) on a real deal. Check every one before
quoting numbers.

## Cost-side traps

**1. Equity double-count.** If `equity = TPC − construction_loan` and TPC
already includes financing costs, do NOT add financing cost to equity again.
Define once: `TPC = TDC_ex_financing + origination + accrued interest`;
`equity = TPC − loan`. Every downstream IRR/CoC uses that single equity figure.

**2. Contractor "plans & permits" vs county impact fees.** Contractor budgets
bundle a small plans/permits line (e.g. $17k) that almost never covers real
county impact fees (often ~$9k+/door → a 2-door duplex exceeds the whole line).
Fix: strip the contractor line out of hard cost, then itemize soft costs
explicitly — design/engineering, building permit, impact fees × units, utility
connection. Never both keep the contractor line AND add itemized fees.

**3. Utility connection double-count.** If the budget builds well + septic
(they'll be line items), central water/sewer connection fees are an
*alternative*, not an addition. Set connection = $0 unless switching to county
utilities.

**4. Sheet totals that omit their own percentages.** Contractor sheets
routinely show "TOTAL" formulas that skip the overhead % and contractor-fee %
rows sitting right above them. Recompute the sum yourself; flag the diff.

**5. Per-unit scaling.** Appliances (and anything per-kitchen/per-unit) scale
by unit count even when the rest of the budget is per-building. A "duplex
budget" often carries only ONE appliance set. Make `units` a single driver
cell and hang appliances, impact fees, rent, and reserves off it.

## Value-side traps

**6. Distressed scrapes ≠ retail comps.** Scraped "sold" datasets blend
tax-deed auctions, quitclaims, manufactured-on-land, and lot sales. Symptom:
sold $/sf at 35–45% of active-listing $/sf. Underwrite exit/ARV to verified
retail arm's-length comps only; keep the distressed set for acquisition
hunting.

**7. Value < cost is a stop sign.** Stabilized value = NOI ÷ market cap. If
that lands under all-in cost, build-to-hold manufactures negative equity and
the "75% LTC" construction loan is fiction (lenders cap at ARV). Check
construction LTV = loan ÷ stabilized value; >100% means the refi requires
cash-IN, not cash-out.

**8. Listed price/unit ≠ cap-rate value.** Small-MF listings are often priced
for owner-users, well above `unit NOI ÷ cap`. Compare three numbers: build
cost/unit, listing price/unit, cap-rate value/unit — the ranking decides
buy vs build vs pass.

## Entitlement traps

**9. Cheap platted lots are usually single-family-only.** R-1 = one dwelling.
Duplex needs a rezone (discretionary, months, deniable) AND a min lot per
unit that typically shrinks only with central water+sewer. On septic, small
lots fail even after rezoning. Verify: zoning class, min-lot table, septic
sizing, and what production builders actually pull permits for.

**10. 3–4 units effectively need central sewer.** DOH septic sizing makes
multi-unit drainfields impractical. Sewer-availability maps gate the fourplex
thesis, not preference.

## Process rules

- Tag every figure: `[REFRESHED <date>]` / `[FILE <date>]` / `[ESTIMATE]`.
- Recompute the workbook's headline outputs independently (plain Python)
  before quoting them — the model and the oracle must agree.
- Zero formula errors, verified by tooling (`validate_model.py`), not by eye.
- Sensitize rent, land, impact fees, exit cap first; they dominate.
- End with the county phone calls that close open items (zoning, utilities,
  impact-fee schedule) — name numbers and departments.
