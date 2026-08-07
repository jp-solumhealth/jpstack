# Valuation — DCF + comps, reconciled to a price target

Use after the business is understood (`research.md`). Two primary methods, **reconciled to a range,
never a single point**: DCF (intrinsic value) and trading comps (what the market pays for peers).
Precedent transactions are optional and low-value for a long-term personal investor (they price M&A
control premiums) — skip unless there's a live takeover angle.

Default weighting: **DCF 50–60% / comps 40–50%**, shifting toward comps when forecasts are low-confidence
(early-stage, cyclical) and toward DCF when cash flows are stable and predictable.

Build the model with `scripts/dcf.py` (formula-driven XLSX) and check it with `scripts/validate_model.py`.

## A. DCF (unlevered free cash flow method)

**Free cash flow build (per year of an explicit 5–10y forecast):**
```
EBIT × (1 − tax rate)            = NOPAT
+ D&A
− CapEx
− Δ Net working capital
= Unlevered Free Cash Flow (UFCF)
```
Use **unlevered** FCF (pre-financing) and discount at WACC — do not use net income.

**Discount rate — WACC:**
```
Cost of equity (CAPM) = Rf + β × ERP
  Rf  = current 10Y Treasury yield (^TNX / FRED), as-of dated
  β   = computed by regression of the stock vs SPY (fetch.py); sanity-check vs 1.0
  ERP = equity risk premium, 4.5–6.0% [ASSUMPTION] — state which you used
Cost of debt = after-tax (interest rate × (1 − tax))
WACC = E/(D+E) × cost of equity + D/(D+E) × after-tax cost of debt
  → use MARKET values of equity and debt, not book.
```

**Discounting:** use the **mid-year convention** (discount periods 0.5, 1.5, 2.5, …) — cash flows
arrive through the year, not at year-end.

**Terminal value** (the part most likely to be wrong — handle with care):
- Perpetuity growth: `TV = FCF_final × (1 + g) / (WACC − g)`, with **g ≤ long-run GDP (~2–3%)**.
  g must be **well below WACC** or the model explodes.
- Or exit multiple: `TV = final-year EBITDA × exit EV/EBITDA` (cross-check vs the perpetuity-implied multiple).
- Discount the TV back at the same mid-year-adjusted final period.

**EV → equity → per-share bridge:**
```
Enterprise Value = Σ PV(UFCF) + PV(Terminal Value)
− net debt
+ non-operating assets (excess cash, investments)
− minority interest, preferred
= Equity Value  ÷  DILUTED shares outstanding  =  intrinsic value per share
```

**Scenarios:** build **Bear / Base / Bull** driven by a single case-selector cell (revenue growth,
margin, WACC, terminal g differ per case). Report a probability-weighted value if you can assign
sensible probabilities, else show the three side by side.

**Sensitivity:** three 2-way tables, odd-dimension (5×5), base case dead-center and highlighted:
1. WACC × terminal growth
2. Revenue growth × EBIT margin
3. Beta × risk-free rate

## B. Trading comps

1. Pick **8–15 candidates**, trim to **5–10 truly comparable** (same business model, size, growth,
   margin profile — not just same sector).
2. Compute multiples LTM and NTM (NTM preferred; tag NTM estimates `[ESTIMATE]`): EV/Revenue,
   EV/EBITDA, EV/EBIT, P/E — plus sector-specific (P/B for financials, EV/EBITDAR, P/FFO for REITs).
3. **Mandatory statistical block** for each multiple: **Max / 75th pct / Median / 25th pct / Min.**
4. Apply the **median and 25th/75th** to the target's metric → a valuation range. Justify any
   premium/discount to peers by growth, margins, or competitive position — don't apply a premium "because."
5. Pick the right multiple for the company: EV/EBITDA for mature, EV/Revenue for high-growth/unprofitable,
   P/E for stable capital structures.

## C. Reconcile → target → rating

- Lay DCF range and comps range side by side (a "football field"). Reconcile to a **fair-value range**.
- Compare to current price → implied up/downside and **margin of safety** (how far below fair value
  you'd require to buy — bigger for lower-quality / higher-uncertainty names).
- **Rating:** BUY / HOLD / SELL with explicit price levels (buy below X, trim above Y) and the
  thesis link. **Stop and surface** — the rating is an input to the user's decision, not a trade order.

## 7-point DCF sanity checklist (run before trusting any output)

1. **Historical multiple check** — does the implied multiple sit in the stock's own historical range?
2. **Peer check** — is the implied multiple sensible vs comps; is any premium/discount justified?
3. **Implied-growth check** — reverse-engineer what growth the *current price* implies; is your base
   case more or less optimistic, and why?
4. **Market-cap reasonableness** — does the equity value pass a smell test vs current cap?
5. **Terminal-value share** — TV should be **< ~60–70% of EV**. If higher, the explicit forecast is
   too short or terminal assumptions too aggressive — extend the forecast or trim g.
6. **WACC band** — typically **8–14%** (lower for stable mature, higher for risky/high-growth). Outside
   this, re-examine inputs.
7. **Implied-return check** — what IRR does buying at today's price imply to your fair value, and does
   it match the rating?

`scripts/validate_model.py` automates the hard-fail subset: terminal g < WACC (critical), WACC in a
sane band, TV as % of EV in range, and scans every cell for `#REF!/#DIV/0!/#VALUE!/#NAME?/#NUM!/#N/A`.
**Fix all flags and re-run until clean before delivering.**

## Pitfalls to avoid (these silently break valuations)

- Terminal **g ≥ WACC** → infinite/absurd value.
- Using **net income** instead of unlevered FCF; double-counting the tax shield.
- Growing revenue without the **CapEx / working capital** needed to support it.
- **Book** instead of **market** values in WACC weights.
- Terminal value **dominating** (>70% of EV) — model is really just a TV guess.
- Ignoring **cyclicality** — valuing a peak-margin year as the new normal.
- Mid-year vs year-end discounting inconsistency.
- Comps that aren't actually comparable (same sector ≠ same business).
