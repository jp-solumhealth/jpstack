# Mode 4 — Monitor & rebalance

Goal: keep the portfolio honest over time — track whether each thesis still holds, react to earnings
and catalysts with discipline, control drift and concentration, and rebalance tax-efficiently. This
is where most real return is won or lost (or given back). Run `scripts/portfolio.py` against
`portfolio.csv` for the quantitative pieces.

## A. Thesis tracking (the living scorecard)

Each owned name has `portfolio/theses/<TICKER>.md`. Maintain it, don't rewrite it:

- **Scorecard** — table of the thesis pillars: `Pillar | Original expectation | Current status | Trend (↑/→/↓)`.
- **Update log** — append-only: `Date | New data point | Thesis impact (strengthen / weaken / neutralize) | Action | Updated conviction (H/M/L)`.
- **Stop / invalidation triggers** — the pre-committed levels and conditions from the thesis. When one
  trips, say so plainly and propose the action — don't rationalize it away.
- **Rule:** track disconfirming evidence as rigorously as confirming. The job is to notice when you're
  wrong *before* the market forces it.

## B. Earnings review (each report for an owned/watched name)

**Date-check first** (earnings data is the most stale-prone). Pull the actual print (8-K/press
release + 10-Q) and **read the full transcript — not a summary**. Produce a variance table:

```
Metric    | Actual | Consensus [EST] | Prior est | Beat/Miss | Why
----------|--------|-----------------|-----------|-----------|-----
Revenue   |        |                 |           |           |
Gross mgn |        |                 |           |           |
EBIT/EBITDA|       |                 |           |           |
EPS       |        |                 |           |           |
```

Then: guidance change (raised / maintained / lowered, vs expectation), management tone, any questions
they dodged, and — the point — **does this strengthen, weaken, or neutralize each thesis pillar?**
Update the thesis scorecard. Quantify everything ("beat by $120M / 3%", not "strong").

## C. Catalyst calendar

`portfolio/reviews/catalyst-calendar.md`: `Date | Ticker | Event | Type (earnings/corporate/industry/macro) | Impact (H/M/L) | Our positioning | Notes`.
Weekly forward preview of what's coming. **Archive past catalysts with the actual outcome** — it builds
pattern recognition over time.

## D. Portfolio review (periodic — monthly/quarterly)

Run `scripts/portfolio.py`. Produce `portfolio/reviews/review_<YYYY-MM-DD>.md`:

- **Allocation vs IPS targets** — current vs target by asset class and (within equities) sector.
- **Concentration** — top-5 weight, HHI, any single name over its cap, correlation clusters.
- **Performance vs benchmark** — `Metric | YTD | 1Y | 3Y | Since inception` for portfolio return,
  benchmark (SPY/total-market) return, and **alpha**. Be honest about whether stock-picking is adding value.
- **Attribution** — top 3 contributors / top 3 detractors; any outsized single-position impact.
- **Thesis status roll-up** — which theses are intact, weakening, or broken (from the scorecards).
- **Actions** — what (if anything) to do, why, and the tax impact. Stop and surface.

## E. Rebalancing (tax-aware)

Only rebalance when drift breaches the IPS band — **don't rebalance for its own sake**; small drift
within bands is fine and trading has real costs (taxes, spreads, tracking error).

Drift table → trade list:
```
Asset/Name | Target % | Current % | Drift | $ over/under
Account | Action (buy/sell) | Security | Shares/$ | Reason | Tax impact
```

**Tax-aware rules (in priority order):**
1. Rebalance in **tax-advantaged accounts first** — no tax cost there.
2. **Direct new contributions / dividends to underweight** positions instead of selling — the cheapest
   rebalance is buying, not selling.
3. In taxable accounts, avoid realizing large **short-term** gains (taxed as ordinary income); prefer
   long-term, and compute the **breakeven**: does the tax cost outweigh the rebalancing benefit?
4. **Harvest losses** opportunistically while rebalancing (see TLH below).

## F. Tax-loss harvesting (TLH)

Candidate scan from `portfolio.csv`: `Cost basis | Current value | Unrealized loss | Holding period (ST/LT) | % loss`.
- Prioritize **largest absolute loss**, **short-term first** (offsets higher-taxed ST gains), then largest %.
- **Gain/loss budget:** offset realized gains, plus up to **$3,000 of ordinary income**; excess **carries
  forward**.
- **Wash-sale rule:** do **not** buy the same or "substantially identical" security within **30 days
  before or after** the sale — and check **all accounts** including IRAs and DRIP reinvestments. Use a
  not-substantially-identical replacement to keep market exposure (e.g. a different but similar ETF).
- Not all losses are worth harvesting — transaction costs and tracking error are real. Track harvested
  lots for 30+ days to manage the wash-sale window before repurchasing.

## G. Morning note (optional daily monitoring)

Lightweight: **Top call** → overnight developments (one line + "our take" per relevant holding) → key
events today → any trade ideas with "Risk: what would make this wrong." **"No news" is a valid morning
note** — don't manufacture activity.

## Discipline

- The hardest part is **inaction when warranted** and **action when a thesis breaks**. Pre-committed
  rules (IPS, stops, invalidation triggers) exist to override in-the-moment emotion. Surface them; let
  the user decide. Never execute.
