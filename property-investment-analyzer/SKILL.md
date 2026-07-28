---
name: property-investment-analyzer
description: >
  Use when analyzing existing rental / income properties as buy-and-hold
  investments, or screening and ranking a set of acquisition opportunities.
  Triggers: "is this a good rental", "analyze this rental / income property",
  "underwrite this deal", "cap rate", "cash-on-cash", "DSCR on this",
  "1% rule", "does this cash flow", "rent roll analysis", "value-add",
  "what should I offer", "max offer", "screen these listings", "which of
  these properties is best", "rank these deals", "buy-and-hold analysis",
  a rental listing / rent roll dropped in to vet, or any income-property
  acquisition or property-management investment decision. For ground-up
  development (build vs buy), use buy-vs-build-underwriter instead.
---

# Property Investment Analyzer

## Overview

Underwrites existing rental/income properties and screens acquisition
opportunities. Produces an Excel workbook: a ranked **Screening matrix** + a
full **Detail** underwriting tab per property + shared **Assumptions**.

**Core principle: underwrite to the number that works, not to the asking price.**
Screen on *in-place* income (what it earns today), size the deal by the *max
supportable offer* for your target return, and treat pro-forma/market rent as
upside — never as the basis for the price you pay.

## Workflow

1. **Intake** — for each property: price, units, SF, actual rent (rent roll) and
   market rent, taxes, insurance, HOA, rehab. Actuals beat estimates; tag any
   estimate. Pull rent comps if actuals are missing.
2. **Underwrite each** — in-place vs pro-forma operating statement → NOI, cap
   rate, GRM, 1% rule; then financing → DSCR, cash-on-cash, breakeven occupancy;
   then a hold pro-forma → IRR and equity multiple.
3. **Max supportable offer** — the deliverable buyers actually use: the price
   that hits your target cap, target DSCR, and 1% rule. If it's below asking,
   that's your negotiation number (or a pass).
4. **Value-add** — quantify the NOI lift from raising in-place rents to market /
   cutting expenses, and the forced value it creates (lift ÷ cap).
5. **Screen & rank** — one row per property, ranked by blended yield score,
   verdict Buy / Watch / Pass (green/amber/red).
6. **Decide** — lead with the 2–3 best deals and each one's max offer; say why
   the rest pass. Flag every estimate.

## Build it

```
python3 scripts/analyze_property.py --config deals.json --out deals.xlsx
python3 scripts/validate_and_fill.py deals.xlsx   # zero-error check + embeds values so it opens populated
```

Config is `{"assumptions": {...}, "properties": [ {name, price, units, sqft,
rent_actual, rent_market, taxes, insurance, hoa_mo, rehab}, ... ]}`. Defaults =
realistic Marion County FL rentals. Run `--help` for details.

## Quick reference — metrics & rules of thumb

| Metric | Formula | Screen |
|---|---|---|
| Cap rate (in-place) | NOI ÷ (price + rehab) | ≥ target (market cap) |
| Cash-on-cash | (NOI − debt service) ÷ cash to close | ≥ 8% (adjust) |
| DSCR | NOI ÷ annual debt service | ≥ 1.20–1.25 (lender floor) |
| 1% rule | monthly rent ÷ price | ≥ 1.0% |
| GRM | price ÷ annual gross rent | lower is better |
| Breakeven occupancy | (opex + debt service) ÷ gross rent | < ~85% |
| Max offer @ cap | NOI ÷ target cap | — |
| Value created | (pro-forma − in-place NOI) ÷ cap | — |

Exit is **appreciation-based**, not cap-expansion — don't punish a low-entry-cap
buy with a high exit cap (see `references/underwriting-metrics.md`).

## Common mistakes

Full list with fixes in `references/underwriting-metrics.md`. Top four:
underwriting to pro-forma rent instead of in-place; ignoring capital reserves and
real vacancy (the "50% rule" sanity check); exiting at a cap far above entry;
and forgetting that below-1.0 DSCR = negative leverage (the property loses money
every month even before you count your equity).

## Files

- `scripts/analyze_property.py` — workbook generator (screening + per-deal detail)
- `scripts/validate_and_fill.py` — zero-error validation + embeds cached values
- `references/underwriting-metrics.md` — metrics, rules of thumb, value-add levers, traps
