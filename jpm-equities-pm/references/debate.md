# Mode 5 — Bull/Bear Debate & probabilistic position review

Goal: for each position (or candidate), run an **adversarial debate** — independent agents build the
strongest bull and bear cases, argue against each other, and a judge assigns **scenario probabilities**
and a **probability-weighted expected return**, ending in a decisive **HOLD / TRIM / SELL / ADD /
DOUBLE_DOWN** call. Then synthesize a portfolio-level action plan. This is how you decide what to do with
real money under uncertainty — never one analyst's view, always the argument between opposing views.

This mode uses **multi-agent orchestration** (the Workflow tool). It is the one mode that fans out
parallel agents; it requires the user to want that (they asked for "parallel agents arguing" / a debate /
"what should I do"). For a quick single-name read without the fan-out, use Mode 1 (research) instead.

## How to run it

Reusable workflow script: `scripts/position-debate.workflow.js`. Invoke with the Workflow tool:

```
Workflow({
  scriptPath: ".../jpm-equities-pm/scripts/position-debate.workflow.js",
  args: {
    today: "YYYY-MM-DD",
    context: "<portfolio framing: concentration, theme tilt, IPS caps, any thesis lens e.g. Situational Awareness>",
    positions: [ { ticker: "GOOG", name: "Alphabet", weightPct: 44.4 }, ... ]
  }
})
```

It runs in the background and notifies on completion; watch live with `/workflows`.

## The pipeline (per position)

1. **Bull & Bear research (parallel).** Two agents, one per stance. Each:
   - Pulls **current price + recent (≤3mo) analyst price targets from major banks** (GS, MS, JPM, BofA,
     Barclays, UBS, Wells, Citi…) and the **consensus** rating/mean target, via public web (no paid
     terminal). **Cites every source + date; tags unverifiable figures `[ESTIMATE]`; never fabricates a
     target.**
   - Builds the strongest honest case for its side: 12-month target, implied return, key points, catalysts.
   - States the **risks to its own view** (intellectual honesty — a bull who can't name the bear risk is useless).
2. **Judge & weight.** One adjudicator agent receives both cases and:
   - **Argues both ways** — the bull's best rebuttal to the bear, and the bear's best rebuttal to the bull.
   - Assigns **pBull + pBase + pBear = 1.0** with a return % per scenario; computes
     **EV return = Σ pᵢ·returnᵢ**.
   - Issues a recommendation + conviction, weighing **EV/skew AND portfolio fit** — a name over the
     single-name cap or piling onto an overweight theme leans TRIM/SELL even with positive EV.
3. **Synthesize.** A final agent turns all verdicts into a **portfolio action plan**: per-name
   current→target weight, an **order of operations** (trim the over-cap name first), how to fund the
   missing risk-balanced core, and the top portfolio risks.

## Scaling the debate
Default is 1 bull + 1 bear + 1 judge per name (decisive, economical). For higher-stakes names, raise to
2–3 agents per side (perspective-diverse: one fundamental, one technical/flows, one thesis-specific) and
have the judge weigh the panel. More agents per side = more robust, more tokens.

## Reading the output
- **EV return** ranks opportunity; **probability skew** (pBull vs pBear) shows asymmetry; **conviction**
  reflects how decisive the evidence is.
- A positive-EV name can still be a **TRIM** if it breaches concentration caps — risk management overrides
  a good thesis. That's the point of doing this inside a portfolio, not in isolation.

## Honesty & limits
- Analyst price targets are **third-party / secondary** and sometimes stale or hard to source on public
  web — they are cited and tagged, never invented. Treat them as one input, not truth.
- Probabilities are **judgment**, not measured frequencies — they make the reasoning explicit and
  falsifiable, not precise. Re-run after material news.
- Output is analysis; **you place every trade.** Stop-and-surface before acting.
