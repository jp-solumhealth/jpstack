---
name: buy-vs-build-underwriter
description: >
  Use when deciding whether to BUY existing residential/small-multifamily or BUILD
  ground-up (duplex/triplex/fourplex/BTR/SFR) in a target market, or when a contractor
  construction budget (xlsx) needs to become an institutional financial model.
  Triggers: "buy vs build", "should I build or buy", "does this pencil",
  "underwrite this development", "build-to-rent", "BTR", "build-to-sell vs
  build-to-hold", "duplex/fourplex pro forma", "development feasibility",
  "construction budget model", "DSCR refi model", "30-year hold projection",
  a contractor budget spreadsheet dropped in with intent to model it, or any
  ground-up small-residential development decision.
---

# Buy-vs-Build Underwriter

## Overview

Turns market research + a real contractor budget into a verified buy-vs-build
decision: a fully formula-linked Excel model (Build-to-Sell vs Build-to-Hold)
plus a decision-first recommendation.

**Core principle: check the entitlement gate and value-vs-cost BEFORE modeling
returns.** Most small-MF build theses die on zoning (cheap lots are usually
single-family-only) or on stabilized value landing below all-in cost. If
`NOI / total cost < market cap rate`, building to hold destroys value — no
financing structure fixes that.

## Workflow

1. **Market research fan-out** — parallel agents: (a) macro/housing, (b) rents +
   cap rates, (c) sold comps + submarkets, (d) **zoning, min-lot rules, impact
   fees, utilities (septic/sewer), construction cost, loan rates**. Tag every
   figure `[REFRESHED <date>]`, `[FILE <date>]`, or `[ESTIMATE]`. (d) is
   decision-critical — run it first if you must sequence.
2. **Entitlement gate** — is the product buildable by-right on the target lots?
   Zoning class, min lot per unit (septic vs central sewer thresholds differ),
   rezoning path + timeline. What production builders actually build there is
   the ground truth of what's financeable.
3. **Model** — `scripts/build_model.py --config deal.json --out model.xlsx`
   builds a 13-tab linked workbook (Dashboard, Sell, Hold, Comparison, 30-yr,
   Construction loan, P&L, Cash flow, Dev budget, Market summary, Assumptions,
   Sensitivity, Charts). One input cell (`Assumptions!Units`) flips duplex ↔
   quadplex; appliances scale per unit.
4. **Verify — mandatory** — `scripts/validate_model.py model.xlsx` must report
   zero formula errors, AND recompute headline outputs (TPC, net profit, NOI,
   value, DSCR) independently in plain Python before quoting any number.
5. **Deliver decision-first** — verdict (buy / build-to-sell / build-to-hold /
   wait) with the 2–3 needle-movers, then the detail. Flag every estimate.

## Quick reference

| Check | Rule of thumb |
|---|---|
| Build-to-hold viability | Yield-on-cost (NOI/TPC) must beat market cap rate |
| Construction LTV | Loan ÷ stabilized value > 100% = value destruction |
| Sell breakeven | TPC ÷ (1 − commission − closing) |
| Refi shortfall | Refi loan (LTV × value) < construction payoff → cash-in at refi |
| Biggest levers | Achieved rent, land basis, impact fees — sensitize these first |

## Common mistakes

See `references/underwriting-traps.md` for the full list with fixes. The top
four: double-counting financing in equity; adding county impact fees on top of
a contractor "plans & permits" line without reclassifying; using distressed/
tax-deed/manufactured "sold" scrapes as retail comps; assuming duplexes are
buildable by-right on cheap platted lots.

## Files

- `scripts/build_model.py` — workbook generator (defaults = worked Marion County
  FL example; override via JSON config, see `--help`)
- `scripts/validate_model.py` — zero-formula-error scan (needs `pip install formulas`)
- `references/underwriting-traps.md` — domain traps + reconciliation rules
