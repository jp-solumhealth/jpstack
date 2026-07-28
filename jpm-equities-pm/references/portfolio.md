# Mode 3 — Construct & size the portfolio

Goal: turn researched ideas into a coherent portfolio that matches the user's goals and risk
tolerance, with deliberate position sizes and concentration limits. The anchor is the **IPS**.

## A. The IPS (Investment Policy Statement) — the constitution

Before sizing anything, make sure `portfolio/ips.md` exists and is filled in (scaffold from
`templates/ips-template.md`). The IPS sets the rules so decisions are made in calm, not in a drawdown.
It defines:

- **Objectives** — return goal, time horizon, what this capital is for.
- **Risk tolerance** — max acceptable drawdown, volatility comfort, behavioral honesty ("would I sell
  at −30%?"). Tie sizing to this.
- **Target asset allocation** — across asset classes (equities / bonds / cash / alternatives) and,
  within equities, any sub-targets (geography, sector caps, factor tilt).
- **Constraints** — liquidity needs, tax situation (account types), things you won't own
  (ethical/knowledge constraints), single-name and sector **caps**.
- **Rebalancing policy** — drift bands (e.g. ±5% absolute / ±25% relative) and cadence.
- **Sell discipline** — the rules for trimming/exiting (thesis broken, valuation stretched, better
  use of capital, stop-loss). Pre-committing avoids selling winners early and holding losers.

If no IPS exists, **build it first** with the user — sizing without one is guessing.

## B. Asset allocation

Top-down: set the asset-class mix to the IPS targets first; security selection happens **within** the
equity sleeve. A simple, defensible grid (illustrative — set to the user's IPS):

| Asset class | Role |
|-------------|------|
| Equities (core index + select single names) | growth engine |
| Bonds / cash | ballast, dry powder, liquidity |
| Alternatives (optional) | diversification |

For a stock-picking personal portfolio, a common structure is a **core (broad index/ETF) + satellite
(high-conviction single names)** — the core controls overall risk; satellites are where research adds
value. Decide the core/satellite split explicitly.

## C. Position sizing (the discipline that protects you)

Size on **conviction + risk + correlation**, capped by the IPS. Combine these lenses:

1. **Conviction tiers** — map research conviction to a base weight (e.g. high 5–8%, medium 3–5%,
   starter 1–2%). Conviction = quality of business × margin of safety × how well you understand it.
2. **Risk-based sizing** — size so that hitting your **invalidation/stop level** costs an acceptable
   slice of the portfolio. If you'd exit at −25% and you'll risk ~1.5% of the portfolio on being
   wrong, the position ≈ 1.5% / 25% = **6%**. This ties size to where the thesis breaks, not to a hunch.
3. **Kelly as a ceiling, not a target** — full Kelly (`f* = edge/odds`) is famously too aggressive and
   assumes you know your edge precisely (you don't). Use **fractional Kelly (¼–½)** as an upper bound
   and a sanity check, never as the literal size.
4. **Concentration caps** (hard limits from the IPS):
   - Single name ≤ a stated max (e.g. 8–10%).
   - Sector ≤ a stated max.
   - Watch **correlation** — five names that all rise/fall together are one bet. Check overlap.
   - Track **HHI** and **top-5 weight** (via `scripts/portfolio.py`) as concentration gauges.

A starter position you'll add to on weakness is a legitimate sizing tool — define the add levels up front.

## D. Asset location (which account holds what — free alpha)

- **Tax-deferred (Traditional/401k):** bonds, REITs, high-turnover / high-income assets (defer the tax).
- **Roth:** highest-expected-growth assets (tax-free compounding).
- **Taxable:** tax-efficient broad index ETFs, low-turnover, qualified-dividend payers, and any
  tax-loss-harvest candidates. Hold long-term winners here to defer gains.

Match each holding to the right account in `portfolio.csv` (the `account` column).

## E. Output

- If building/updating the IPS: write to `portfolio/ips.md` (confirm changes with the user first).
- For a sizing decision: a `sizing_<YYYY-MM-DD>.md` showing, per name, conviction tier, the risk-based
  size, the cap check, and the proposed $ / share count and target weight — then the resulting
  portfolio weights and concentration check. **Stop and surface; the user places any trades.**
