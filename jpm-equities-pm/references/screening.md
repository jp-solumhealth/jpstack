# Mode 2 — Screen for ideas

Goal: turn a universe into a short, ranked list of names worth the deep-dive in `research.md`. A
screen is a **funnel and a hypothesis**, not a buy list — it surfaces candidates; research decides.

## Workflow

1. **Define the style/hypothesis** with the user (value, growth/quality compounder, special situation,
   or a custom thesis like "beneficiaries of X"). Each style has different screen criteria (below).
2. **Set the universe** — e.g. S&P 500, Russell 1000, a sector, or a user-provided list. On free data,
   you usually screen a known list (pull each name's fundamentals via `fetch.py`) rather than a live
   market-wide screener. Be explicit about the universe and **log what you excluded and why** — no
   silent truncation.
3. **Apply criteria**, rank, and trim to **3–5 names**.
4. **Write a one-line falsifiable hook** per name (the thesis in a sentence + the one risk).
5. **Save** to `portfolio/reviews/screen_<theme>_<YYYY-MM-DD>.md`. Offer to deep-dive the top name(s).

## Screen criteria by style (all computable from free data)

**Value**
- P/E < sector median, or EV/EBITDA below own 5y average
- FCF yield > 5%
- P/B < 1.5x (sector-dependent)
- Net debt / EBITDA < 3x
- Optional confirmation: recent insider buying (last 90d)

**Quality / compounder**
- ROIC > WACC by a wide margin (or ROE > 15%) sustained 5y+
- Gross-margin stability or expansion
- FCF conversion > 80% (FCF / net income)
- Low leverage (net debt/EBITDA < 2x), high interest coverage
- Reinvestment runway (long growth path) + disciplined capital allocation

**Growth (at a reasonable price)**
- Revenue CAGR > ~15% with improving or high gross margin
- Net revenue retention > 110% (where disclosed) / strong unit economics
- PEG or growth-adjusted EV/Revenue not extreme vs growth
- Path to / existing profitability (avoid pure cash-burners unless thesis demands)

**Special situations**
- Spin-offs, post-bankruptcy, recapitalizations, activist involvement
- Sum-of-the-parts discount (segments worth more separately)
- Forced/technical selling, index deletions, tax-loss-selling overhangs
- Catalyst with a defined timeline (these are event-driven — define the catalyst and the date)

## Idea one-pager (output per surviving name)

```
TICKER — Company                                   Price $X (as-of date) · Mkt cap $X · EV/EBITDA Xx
Hook (1 line): why this is potentially mispriced.
Metric            | Value     | vs peers / history
------------------|-----------|--------------------
[3–5 key metrics that earned it the spot on the list]
Thesis (2–3 bullets): ...
Key risk (1 line): the single thing most likely to break it.
Next step: full research note? (yes/no)
```

## Discipline

- A screen is **necessary, not sufficient** — cheap can be a value trap; quality can be overpriced.
  The screen earns a name a deep-dive; the deep-dive earns it a position.
- State the as-of date and source of every screened figure; tag estimates.
- Report the count: "screened N names, M passed, top K shown." Never imply full coverage you didn't do.
