# Financial Model — methodology

The model is **formula-driven** (never hardcode computed values) and shows **three scenario paths**
so a CFO sees the range, not a single optimistic point. Conservative uses the low end of every
value-driver range, Best the high end, Expected the midpoint.

## Inputs (all editable / "blue" cells)

- **Recurring pricing**: line items `volume × rate` → monthly platform cost. Sum → Grand Total.
- **One-time**: setup + integration fees.
- **Implementation ramp** (months): value doesn't accrue until go-live. Default `1` (Solum's go-live
  is ~Week 4). This is what keeps payback honest instead of an unbelievable sub-1-month figure.
- **Value drivers**: each has a `$/hr` rate and three monthly hour figures (Conservative/Expected/Best).
  Typical Solum drivers:
  - *Admin time saved & repurposed* — ops/billing hours eliminated × loaded admin rate.
  - *Clinical/BCBA time recovered* — clinician hours freed × loaded clinical rate.
  - *Extra billable care delivered* — additional billable hours × reimbursement (or margin) rate.

## Calculations (per scenario)

```
monthly_value      = Σ (driver.rate × driver.hours[scenario])
net_monthly        = monthly_value − monthly_platform_cost
recurring_ROI      = net_monthly ÷ monthly_platform_cost          # one-time EXCLUDED (default headline)
year1_value        = monthly_value × (12 − ramp_months)
year1_total_cost   = monthly_platform_cost × 12 + one_time_total
net_year1          = year1_value − year1_total_cost
year1_ROI          = net_year1 ÷ year1_total_cost                 # one-time INCLUDED (alternate framing)
payback_months     = ramp_months + (one_time_total + monthly_platform_cost × ramp_months) ÷ net_monthly
three_year_net     = monthly_value × (36 − ramp_months) − (monthly_platform_cost × 36 + one_time_total)
```

## Which ROI to headline (`roi_mode` in config)

- **`recurring`** (default — JP's preference): ROI = `net_monthly ÷ platform fee`, **excluding** the
  one-time. The one-time is then recovered via the **payback** figure (which includes it). Rationale:
  ROI should reflect ongoing economics; the setup is a one-off recovered separately. Label it clearly
  ("Recurring ROI, excl. one-time") so the two numbers don't look disconnected.
- **`year1`**: ROI = `net_year1 ÷ year1_total_cost`, with the one-time **inside** the denominator.
  More conservative; use if a CFO insists the upfront sits inside the return.

Whichever mode, **payback always includes the one-time + ramp** — that's where the setup cost lives,
and it's the honest answer to "when do I get my money back."

## Reading the numbers honestly (carry these into the CFO write-up)

- **Cash vs. capacity.** Hours-saved drivers are capacity unless they convert to an avoided hire or
  new billable revenue. Say so. Lead with cash where you can.
- **Margin vs. reimbursement.** If "extra billable hours" are valued at full reimbursement, note the
  delivery cost — contribution margin is the rigorous figure. Flag it; don't silently change a
  client-stated number.
- **Generic rates.** $/hr labor and reimbursement rates are often generic — confirm they're the
  client's actual figures or flag them.
- **Thin conservative case.** If the conservative path barely clears the cost, present it as the floor
  and lead with Expected — don't bury it, but don't anchor on it either.

## Workbook tabs (produced by `scripts/build_model.py`)

1. **Dashboard** — logo + headline cards (ROI, net monthly, net Year-1, payback, cost, value) +
   scenario mini-table + a value-vs-cost bar chart.
2. **Financial Impact** — pricing, one-time, ramp, value drivers (editable), and the full
   Conservative/Expected/Best results block. This is the engine.
3. **Timeline** — phased implementation Gantt (impl phases + the 30-day validation window).
4. **Assumptions & Guidelines** — every input with its source/confirmation status (yellow =
   estimate to replace), plus methodology notes.
