# Mode 1 — Research a name (deep single-name fundamental research)

Goal: understand the business well enough to form a falsifiable view on whether it's worth owning,
and at what price. Output is a lean Markdown research note + (via the valuation step) an XLSX model.
This is the front half; the valuation half lives in `valuation.md` — do that step after the business
is understood. **You cannot value what you don't understand.**

## Workflow

1. **Frame & fetch.** Confirm the ticker and what the user wants (full initiation vs a quick read).
   Run `scripts/fetch.py TICKER` to pull EDGAR fundamentals + yfinance price/β/shares. Note today's
   date and the as-of date of every figure. Pull the latest 10-K and most recent 10-Q/8-K and the
   last earnings transcript from EDGAR / company IR. If a fetch fails, ask for paste-in.
2. **Write the note** using the section structure below. Quote real numbers with sources. Keep it
   lean — this is a working note, not a 40-page bank initiation. Aim for substance over length.
3. **Hand to valuation** (`valuation.md`) once the business, drivers, and risks are clear.
4. **Form the thesis** (last section) — falsifiable pillars + invalidation triggers + a pre-mortem.
5. **Save** to `portfolio/research/<TICKER>_research_<YYYY-MM-DD>.md`. Report path + 3-bullet take.

## Research note structure (lean version of the institutional 9-section skeleton)

Scale each section to what matters for *this* business. Don't pad. Every figure gets a source/tag.

1. **Snapshot** — ticker, price (as-of date), market cap, EV, basic multiples (P/E, EV/EBITDA, FCF
   yield), 1-line of what they do, and your one-line conclusion up front (lead with the answer).
2. **Business model** — how they make money. Revenue by segment/geography (%). Pricing model
   (subscription/transactional/usage). Who pays and why. Recurring vs one-time. For consumer/SaaS,
   compute **unit economics** where data allows: gross margin, LTV/CAC, net revenue retention,
   CAC payback, churn. Tag estimates.
3. **Industry & TAM** — market size (TAM/SAM/SOM with source), growth rate, structure, secular
   tailwind/headwind, "why now." Cite the source for any market-size number or tag `[ESTIMATE]`.
4. **Moat / competitive position** — run **Porter's five forces** briefly (rivalry, new entrants,
   supplier power, buyer power, substitutes) and name the **economic moat type** if any: network
   effects, switching costs, cost advantage, intangibles/brand, efficient scale. Name 5–10 real
   competitors and where this company sits. Is the moat **widening or narrowing**? Evidence:
   market-share trend, pricing power (gross-margin trend), returns on capital (ROIC vs WACC).
5. **Financial analysis** (the quantitative core — from EDGAR, 3–5y history):
   - Growth: revenue CAGR; is growth accelerating/decelerating; organic vs acquired.
   - Margins: gross, operating/EBIT, FCF margin — trend and vs peers.
   - Returns: **ROIC** (and ROIC − WACC spread = value creation/destruction), ROE (DuPont if useful).
   - Capital intensity: CapEx & D&A as % of revenue; working-capital efficiency (CCC).
   - Balance sheet & liquidity: net debt, net-debt/EBITDA, interest coverage, maturities, current ratio.
   - Cash generation & quality: FCF conversion (FCF/net income), accruals red flags, SBC as % of revenue.
   - Capital allocation: what they do with cash (reinvest, buybacks at what price, dividends, M&A) and
     whether it's created value.
6. **Management & governance** — key execs (short, factual bios from DEF 14A), tenure, track record,
   insider ownership %, recent insider buying/selling, incentive alignment, related-party flags, any
   accounting/governance concerns.
7. **Risk assessment** — 8–12 specific, ranked risks across **exactly four buckets**:
   - *Company-specific* (execution, key-person, customer concentration, product)
   - *Industry/market* (competition, disruption, demand cyclicality)
   - *Financial* (leverage, refinancing, liquidity, FX)
   - *Macro/regulatory* (rates, policy, geopolitics)
   For each: likelihood × impact, and whether it's already priced in.
8. **Thesis** (the payoff — make it falsifiable):
   - **Statement:** 1–2 sentences. Why this is mispriced / why it compounds.
   - **Pillars (3–5):** the things that must be true for the thesis to work. Each with the metric
     you'd watch to confirm/deny it (e.g. "NRR stays >115%", "gross margin expands to 60%+").
   - **Invalidation triggers (3–5):** the disconfirming evidence that would kill the thesis. Track
     these as rigorously as the bull points.
   - **Catalysts:** what re-rates it, and roughly when.
   - **Pre-mortem:** "It's two years later and this was a bad buy — what happened?" Answer honestly.
9. **Valuation summary** — filled in from `valuation.md`: fair-value range, current price, implied
   up/downside, margin of safety, and the **BUY / HOLD / SELL** call with the price levels that would
   change it. Stop here and surface to the user — do not treat the rating as an instruction to act.
10. **Sources** — every filing, page, URL, and data pull with its as-of date. Make URLs clickable.

## What separates a good note from a bad one

- **Leads with the conclusion**, then supports it. The reader knows your call in the first 3 lines.
- **Quantifies everything.** "Strong margins" is noise; "gross margin expanded from 41% to 58% over
  five years (10-K FY20–FY24)" is signal.
- **Tracks disconfirming evidence** as hard as confirming evidence. A note that only argues one side
  is marketing, not research.
- **Knows what it doesn't know.** Tag estimates. Flag the 2–3 things you'd need to confirm to raise
  conviction. Name the bear case fairly.
- **Connects to a decision.** Ends in a rating with explicit price levels and what would change the view.
