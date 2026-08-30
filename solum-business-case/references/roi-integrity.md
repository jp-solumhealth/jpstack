# ROI Integrity — how to make the return defensible, not impressive

The failure mode of a business case is not "the ROI was too low." It is **the CFO finds one number
they don't believe and stops trusting the whole model.** Every rule here exists to prevent that.

> **The test every claimed dollar must pass:** *"If this is true, what line on my P&L changes, by how
> much, and when?"* If you can't answer all three, it does not go in the headline.

---

## 1. Value tiers — what may be headlined

Classify every driver before modeling it. The tier determines where it is allowed to appear.

| Tier | What it is | Evidence required | Allowed in headline ROI? |
|------|-----------|-------------------|--------------------------|
| **1 — Hard cash** | Cost that stops being incurred: an avoided hire, a cancelled vendor/tool, eliminated overtime, retired outsourcing spend | Named req, contract, or invoice | **Yes** |
| **2 — Recovered revenue** | Cash that was leaking and now doesn't: permanently-denied claims now paid, visits that previously never started | Client's own denial/leakage data, at margin | **Yes** |
| **3 — Capacity** | Hours freed with no committed use | Time study, FTE math | **No — show separately, never in the headline** |

Tier 3 is real value and belongs in the case. It is not ROI. Label it **"Capacity created (not
modeled as cash)"** and keep it out of the ROI numerator unless the client commits it to a Tier 1 or 2
outcome — and if they do, quote them committing to it.

**Default posture:** headline Tier 1 + Tier 2. If that alone doesn't clear the platform fee, the honest
answer is that the deal is scope- or price-limited — say so rather than promoting Tier 3 to fix it.

---

## 2. The ten anti-exaggeration rules

1. **No value without a measured baseline.** State the current-state number *and how the client
   measured it.* "They think it's about a day" is not a baseline; it's a hypothesis to be labeled as one.
2. **Capacity is not cash.** Freed hours convert only via (a) an avoided hire — name the req, or
   (b) new billable work — name the constraint that was actually binding. No named mechanism, no dollars.
3. **Margin, not gross revenue.** Value new billable volume at contribution margin. If the client
   insists on full reimbursement, model both and headline margin, with the delivery cost shown.
4. **Recover only the recoverable slice.** For denials, the value is *(permanently-lost %) × revenue
   per claim* **plus** *(reworked %) × rework labor cost* — never gross denial rate × revenue. Claims
   that get paid on appeal were never lost; only the rework was.
5. **Apply an attribution haircut.** Solum is rarely the only cause of an improvement. If other
   factors contribute, apply an explicit attribution % and disclose it. An undisclosed 100% claim is
   the fastest way to lose a CFO.
6. **No stacked percentages.** "Fewer denials," "less admin time," and "faster intake" frequently
   describe the *same* dollars arriving by different routes. See the overlap map (§3).
7. **Cap every driver by physics.** Hours saved can never exceed
   `FTEs actually on the task × ~160 hrs/mo × automation coverage %`. Cross-check against
   `volume × minutes per unit`. If the two disagree by more than 20%, you have the wrong input — stop
   and resolve it, don't average them.
8. **Ramp is real.** Value accrues only after go-live, and phased go-lives earn phased value. Never
   let Month 1 carry full value.
9. **One-time costs live in payback.** They may leave the recurring-ROI denominator (that's the
   documented default), but they must never leave the model. Payback always includes them.
10. **The conservative case is a floor, and it must be honest.** If Conservative doesn't clear the
    platform fee, print that fact. Lead with Expected, but never quietly delete the floor.

---

## 3. Double-count overlap map

Before finalizing, check every pair of drivers that commonly collide. If two drivers touch the same
dollars, keep the value in **one** of them and set the other's overlap to zero, with a note.

| Driver A | Driver B | The collision | Resolution |
|----------|----------|---------------|------------|
| Admin hours saved | Denial rework reduction | Rework *is* admin labor — usually already inside the hours-saved figure | Keep in admin hours; zero the rework labor line, or carve rework out of the admin baseline explicitly |
| Admin/clinical hours freed | Extra billable delivered | The same freed hour cannot be both redeployed to ops *and* billed to a patient | Split the hours between the two uses; the split must sum to ≤ 100% |
| Faster intake / auth turnaround | Extra billable delivered | Faster starts *are* the mechanism that produces extra billable visits | Model once, as incremental visits × margin |
| Denials recovered | Net collection rate lift | Same cash counted two ways | Pick the one the client's finance team actually tracks |

State in the Assumptions tab which overlaps were checked and how each was resolved. A CFO who sees
you policing your own double-counts will trust the numbers you kept.

---

## 4. Smell tests — thresholds that force a re-check

These are not hard limits; they are tripwires. Any trip must be either **fixed** or **explained in
writing** on the Assumptions tab.

| Signal | Threshold | What it usually means |
|--------|-----------|-----------------------|
| Recurring ROI | `> 5×` | Double-count, Tier 3 in the headline, or gross revenue used instead of margin |
| Payback | `< 1 month` | Ramp missing or one-time excluded from payback |
| Single driver share of total value | `> 50%` | Model rests on one assumption — stress-test it explicitly |
| Hours saved vs. team capacity | `> 60%` of the relevant team's total hours | Automation coverage over-claimed |
| Value per unit vs. price per unit | `> 10×` | Either the price is far too low or the value is inflated |
| Conservative case | `< 1.0× cost` | Legitimate — but must be printed, not buried |
| Any rate ($/hr, $/claim) | not client-specific | Generic benchmark — flag yellow, ask before headlining |

---

## 5. Baseline integrity

- **Client-measured beats benchmark.** Use industry figures only to sanity-check, never as the base.
- **Units must match the question asked.** Visits ≠ cases ≠ episodes ≠ claims ≠ authorizations. A unit
  mismatch is the single most common source of an order-of-magnitude error. Restate the unit next to
  every volume in the model.
- **Ratios must reconcile.** Auths ÷ visits, auths ÷ new patients, staff ÷ auths — compute these and
  make sure they're plausible. An implausible ratio means an input is wrong, not that the client is
  unusual.
- **"TBD" stays TBD.** Never fill a gap with a plausible-looking estimate to keep the model moving.
  Model it as a range, mark it yellow, and list it as an open ask.

---

## 6. QA gate — run before showing JP anything

Numbers:
- [ ] Every driver is tier-classified; no Tier 3 value sits in the headline ROI.
- [ ] Every headline number traces to a row in the Verified Inputs table.
- [ ] Two-source minimum met on pricing and core volumes; single-source items flagged.
- [ ] Overlap map (§3) run; each collision resolved and noted.
- [ ] Physics cap (§2 rule 7) computed for every hours-based driver.
- [ ] Both cross-checks for hours agree within 20%, or the discrepancy is resolved.
- [ ] Every smell test (§4) either passes or has a written explanation.
- [ ] Units labeled on every volume; ratios computed and plausible.
- [ ] Conservative case stated even when it's thin.

Mechanics:
- [ ] Excel: 0 broken refs, `fullCalcOnLoad` set, formulas (not pasted values) drive every result.
- [ ] Recomputed independently — the spreadsheet's answer matches a hand calculation.
- [ ] Deck figures identical to Excel; no stale tokens from a prior version.
- [ ] Assumptions tab lists every estimate in yellow with its owner and the question that resolves it.

Presentation:
- [ ] The write-up leads with the cash number, not the biggest number.
- [ ] Attribution haircuts and margin-vs-revenue choices are stated, not implied.
- [ ] A short "what would make this wrong" list accompanies the headline — the 2–3 assumptions that,
      if false, break the case.

---

## 7. How to report it

Give JP, in this order:

1. **Headline** — recurring ROI (Tier 1+2 only), net monthly, payback, annual and 3-year value.
2. **What's hard vs. soft** — the cash line, then the capacity line, clearly separated.
3. **Open asks** — the specific questions that would move a soft number to hard, named and prioritized.
4. **CFO watch-items** — where this model will get challenged, and the answer you'd give.

A defensible 2× that survives scrutiny closes deals. An 8× that collapses under one question loses
them, and costs the relationship.
