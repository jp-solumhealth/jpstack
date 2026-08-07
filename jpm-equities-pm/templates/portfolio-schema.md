# Data schemas for the portfolio data layer

These CSVs live in `~/Documents/Claude/hedge-fund-jpm/portfolio/` and are the system of record for what
you own and watch. Export from your brokerage and map columns to these headers, or paste rows and let
the skill normalize them.

## portfolio.csv (current holdings)

```
ticker,account,shares,cost_basis_per_share,purchase_date,asset_class,sector
AAPL,Roth,40,150.25,2023-02-14,equity,Technology
VTI,Taxable,100,210.00,2022-08-01,equity-core,Broad
CASH,Taxable,1,12500.00,2026-01-01,cash,Cash
```

| Column | Meaning |
|--------|---------|
| `ticker` | symbol (use `CASH` for a cash balance; `shares=1`, `cost_basis_per_share`=$ amount) |
| `account` | `Taxable` / `Traditional` / `Roth` / `401k` (drives tax-aware logic & asset location) |
| `shares` | units held |
| `cost_basis_per_share` | average cost (for tax/TLH); fine to approximate, flag if so |
| `purchase_date` | YYYY-MM-DD (drives ST vs LT holding period) |
| `asset_class` | `equity` / `equity-core` / `bond` / `cash` / `alt` (maps to IPS allocation) |
| `sector` | GICS-ish sector (drives concentration/exposure); `Broad` for index funds |

Live price, market value, and unrealized gain/loss are computed at runtime by `scripts/portfolio.py`
(via yfinance) — don't store them.

## watchlist.csv (names on deck)

```
ticker,added,why,trigger_price,notes
COST,2026-05-30,quality compounder; wait for pullback,800,re-rate on membership-fee hike
```

| Column | Meaning |
|--------|---------|
| `ticker` | symbol |
| `added` | date added |
| `why` | one-line reason it's on the list |
| `trigger_price` | price that would prompt action/deep-dive (blank if none) |
| `notes` | free text |
