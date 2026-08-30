---
name: solum-business-case
description: >-
  Build a CFO-grade business case for a Solum Health prospect — a branded, variable-driven
  multi-tab Excel ROI model and (optionally) a matching slide deck. Use this skill whenever JP
  wants a "business case", "ROI", "ROI model/analysis", "decision doc", "make the case for [company]",
  "one-pager for [prospect]", "financial justification", or any cost/value/payback model for a Solum
  deal — even if he doesn't say the words "business case". The defining behavior: EVERY client-specific
  number (pricing, volumes, value drivers, hours, rates) is pulled from and cross-confirmed across
  Fathom, HubSpot, Gmail and Apollo before anything is built — never invent or assume a number.
  Always build the spreadsheet FIRST, then ask whether to also produce the .pptx deck.
---

# Solum Business Case

Build a decision-ready business case that a CFO will trust. Two things make it credible: every
number is **traced to a source** and **cross-confirmed**, and the model is **conservative and
transparent** about what's hard cash vs. a soft estimate.

## Core principles

1. **Source everything, confirm across sources.** A number that appears in only one place is a
   claim, not a fact. Pull pricing/volumes/value-drivers from Fathom call transcripts, confirm
   against HubSpot (deal amount, stage, notes), Gmail threads, and Apollo (company size/context).
   When two sources disagree, surface the discrepancy and ask — don't silently pick one. This mirrors
   JP's standing rule: never relay a number that isn't verified, and re-verify from source on pushback.
2. **Spreadsheet first, then ask about the deck.** Build and review the Excel model first. Only after
   the numbers are agreed do you ask: *"Want me to also build the .pptx deck?"* Don't auto-build slides.
3. **Conservative + honest.** Distinguish cash impact (recovered revenue, avoided hires) from capacity
   value (hours freed). Flag generic/assumed rates. A defensible 2× beats an unbelievable 8×.
   Every claimed dollar must answer: *what line on the CFO's P&L changes, by how much, and when?*
   The rules that enforce this — value tiers, the ten anti-exaggeration rules, the double-count
   overlap map, and the smell-test thresholds — are in `references/roi-integrity.md`. **Read it before
   modeling any value driver.** It is a gate, not background reading.
4. **On brand.** Solum navy `#011C40`, blue `#468AF7`, DM Sans, the SolumHealth logo. See
   `references/brand-and-toolchain.md`.

## Workflow

### 1. Identify the prospect and the deal
Get the company name. Find the HubSpot deal (id, stage, amount, owner) and the primary contact.
If ambiguous, confirm with JP before pulling data.

### 2. Gather and cross-confirm the data  →  read `references/data-sources.md`
Pull from every available source and assemble a **Verified Inputs table**: one row per number, with
the value and the source(s) that confirm it. Mark anything unconfirmed as `ESTIMATE — needs confirm`.
Show this table to JP before building. The model is only as good as this step.

Minimum to confirm before building:
- **Pricing**: per-unit rates and the monthly volumes they apply to (auths, eligibility checks,
  monitoring, etc.) — usually set on a pricing/SOW call and in the SOW deck.
- **Value drivers**: the hours saved / recovered / created and the $/hr applied to each. These are
  almost always client-stated on a call — quote them and attribute them.
- **One-time fees**: setup + integration.
- **A measured baseline for every driver** — the current-state number *and how the client measured
  it.* No baseline, no driver. Label the unit on every volume (visits ≠ cases ≠ claims ≠ auths); a
  unit mismatch is the most common order-of-magnitude error in these models.

Also classify each driver by value tier (`references/roi-integrity.md` §1) in the Verified Inputs
table: **Tier 1** hard cash, **Tier 2** recovered revenue, **Tier 3** capacity. Only Tiers 1–2 may
appear in the headline ROI. If the input set can't support a Tier 1/2 case, say that to JP **before**
building rather than filling the gap with capacity value.

### 2b. Separate what's needed from what's context
Not every number a client sends belongs in the model. Sort the inputs three ways and show JP the sort:
**drives the model** (a priced volume, a rate, a baseline), **scopes or validates it** (ratios,
payer mix, entity/NPI counts — these set the timeline, the setup fee, and the sanity checks), and
**not needed** (interesting, but touches no calculation). Carrying a number into the model that
nothing depends on invites a CFO question you gain nothing by answering.

### 3. Write the config
Translate the verified inputs into `config.json` (schema and an example are in
`assets/example_config.json`). The scripts are fully driven by this file, so the config IS the model.

### 4. Build the spreadsheet
```bash
python3 scripts/build_model.py /path/to/config.json
```
This produces `<Client>_BusinessCase.xlsx` with four tabs: **Dashboard**, **Financial Impact**
(all blue editable cells + Conservative/Expected/Best scenarios), **Timeline**, and
**Assumptions & Guidelines**. Then:
- Report the headline numbers (cost, ROI, payback, annual & 3-year value) for the Expected case.
- Re-show the Verified Inputs table and explicitly flag every soft/estimated assumption.
- Read `references/financial-model.md` for the ROI/payback methodology so you explain it correctly.

### 4b. Run the ROI integrity gate  →  `references/roi-integrity.md` §6
**Do not show JP a number until this passes.** Run the full QA gate: tier check, overlap map,
physics cap on every hours-based driver, the two independent hours cross-checks (agree within 20% or
resolve — never average), unit/ratio plausibility, and every smell-test threshold.

Any tripped threshold is either **fixed** or **explained in writing** on the Assumptions tab. The
common trips and what they actually mean:
`ROI > 5×` → double-count or Tier 3 in the headline · `payback < 1 month` → ramp or one-time missing ·
`one driver > 50% of value` → the model rests on a single assumption · `hours saved > 60% of team
capacity` → automation coverage over-claimed.

Then hand JP the four-part report from §7: headline → hard vs. soft → open asks → CFO watch-items,
including the short **"what would make this wrong"** list (the 2–3 assumptions that break the case
if false). Leading with that list is what makes the rest of the model credible.

### 5. Ask about the deck
Ask: **"Want me to also build the .pptx slide deck?"** Stop and wait. Do not build slides unless asked.

### 6. Build the deck (only if requested)
```bash
python3 scripts/build_deck.py /path/to/config.json
```
Produces a branded 5-slide deck as **PDF** (present-ready) and **PPTX** (editable, built from
high-res renders so fonts never break on the recipient's machine). Then **QA every slide**: render
each page to PNG and visually inspect (the script writes `slideN.png`); fix overflow/typos; confirm
no number differs from the Excel.

### 7. Finalize
Save all artifacts to the client's project folder under `~/Documents/Claude/` (create
`solum-ops/clients/<slug>/` if needed). Cross-check that every figure matches between the Excel and
the deck. Give JP the file paths, the headline numbers, and a short list of CFO-scrutiny watch-items.

## QA checklist (run before declaring done)
The authoritative gate is `references/roi-integrity.md` §6 — run it in full. Non-negotiables:
- Excel: 0 broken refs, `fullCalcOnLoad` set, formulas (not hardcoded values) drive every result.
- Numbers identical across Excel and deck (recompute independently; scan for stale tokens from prior edits).
- Every headline number traces to the Verified Inputs table, and every driver is tier-classified.
- No Tier 3 (capacity) value inside the headline ROI.
- Overlap map run; every double-count collision resolved and noted.
- Every smell-test threshold either passes or carries a written explanation.
- Soft assumptions and generic rates are flagged for JP, not buried.
- The "what would make this wrong" list is written before the case is called done.

## References
- `references/roi-integrity.md` — **the gate.** Value tiers, ten anti-exaggeration rules, double-count
  overlap map, smell-test thresholds, baseline integrity, full QA checklist, reporting format.
- `references/data-sources.md` — where each number comes from and how to cross-confirm it.
- `references/financial-model.md` — ROI/payback methodology and workbook structure.
- `references/brand-and-toolchain.md` — brand and build tooling.

## What the financial model contains  →  `references/financial-model.md`
Three scenario paths (Conservative/Expected/Best) driven by value-driver hour ranges; recurring ROI
(net value ÷ platform fee, **excluding** one-time by default — JP's preference); payback that
**includes** the one-time setup + a go-live ramp; Year-1 and 3-year value. All of it formula-driven
and editable.
