# Rental underwriting — metrics, rules of thumb, and traps

## The operating statement (get this right first)

```
Gross Scheduled Rent (GSR)        actual rent × 12  (use the rent roll)
− Vacancy & credit loss           5–8% of GSR (never 0%)
= Effective Gross Income (EGI)
− Operating expenses:
    Property management           8–10% of EGI (count it even if self-managing)
    Repairs & maintenance         5–8% of EGI (older stock → higher)
    Property taxes                actual; reassessed at sale price in many states
    Insurance                     actual; high in FL/coastal/high-cat
    Capital reserve               $250–500/unit/yr (roof, HVAC, turns)
    HOA / utilities / admin       actual
= Net Operating Income (NOI)      NOI excludes debt service and income tax
```

**50% rule sanity check:** for small residential, opex + reserves often run
~45–55% of EGI. If your opex ratio is under 40%, you've forgotten something
(reserves, real vacancy, management).

## In-place vs pro-forma — the discipline

- **In-place** = what the property earns *today* on actual rents. **Screen and
  price on this.**
- **Pro-forma / market** = what it *could* earn at market rent and stabilized
  occupancy. This is **upside**, not the basis for your offer. Paying pro-forma
  price hands the seller your value-add profit.

## Financing & leverage

```
Cash to close  = down payment + closing costs + rehab
Debt service   = PMT(rate/12, amort×12, loan)
DSCR           = NOI ÷ annual debt service
Cash-on-cash   = (NOI − annual debt service) ÷ cash to close
Breakeven occ  = (opex + debt service) ÷ GSR
```

- **DSCR < 1.0 = negative leverage** — the property does not cover its own
  mortgage; you feed it every month. Lenders want ≥1.20–1.25; DSCR loans price
  off it.
- Cash-on-cash can be negative even when the cap rate is "fine" if the loan rate
  exceeds the cap rate (Ocala-type low-cap markets). Negative leverage is a
  choice, not a surprise — make it knowingly.

## Returns over a hold

- Annual cash flow = NOI (growing at rent growth) − fixed debt service.
- **Exit value: appreciate the purchase price, don't re-cap it.** Modeling the
  sale as `NOI_exit ÷ a fixed exit cap` unfairly crushes any property bought
  below that cap (guarantees a paper loss). Use price × (1+appreciation)^years
  for the sale; reserve the exit-cap calc for the *value-add value-created*
  figure (NOI lift ÷ cap), where it belongs.
- Loan balance at year n: closed-form amortization; net sale proceeds = sale ×
  (1 − selling cost) − loan balance. IRR runs on the equity cash-flow series;
  equity multiple = total distributions ÷ cash invested.

## Max supportable offer (the number to negotiate to)

- **@ target cap:** NOI ÷ target cap.
- **@ target DSCR:** max loan = PV of (NOI ÷ target DSCR) at the loan rate;
  offer = max loan ÷ (1 − down %).
- **@ 1% rule:** monthly rent × 100.
- Take the **lowest** of these as your ceiling. If it's well under asking, either
  negotiate to it or pass. This reframes every deal from "can I afford the ask"
  to "what is it worth to me."

## Value-add levers (the property-management edge)

1. Raise below-market in-place rents to market (biggest lever; verify with comps).
2. Cut controllable expenses (management, insurance shopping, tax appeal, utility
   bill-back / RUBS).
3. Reduce vacancy / turn time; improve tenant quality.
4. Add income (parking, storage, laundry, pet rent).
   Each $1 of durable annual NOI adds ~$1÷cap of value (forced appreciation).

## Traps

| Trap | Fix |
|---|---|
| Underwriting to pro-forma rent | Price on in-place; pro-forma is upside |
| Vacancy or reserves set to 0 | Always include (5–8% vacancy, $250–500/unit reserve) |
| Taxes at seller's assessed value | Re-underwrite at reassessment on YOUR purchase price |
| Exit cap >> entry cap | Use appreciation-based exit; don't manufacture a loss |
| Ignoring DSCR < 1.0 | That's negative cash flow — flag it, don't bury it |
| "Cap rate looks fine" with negative CoC | Loan rate > cap = negative leverage |
| Rent estimates treated as fact | Tag estimates; verify with a rent survey |
| Deferred maintenance not in rehab | Inspect; add capex to cash-to-close and basis |
