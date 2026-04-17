---
name: one-pager-builder
description: Build a single-page branded PDF brief for a Solum Health prospect or customer. Two modes. Mode 1 (opportunity brief) triggers on "build a one pager", "opportunity brief", "deal brief", "sales one-pager", "C-suite brief", "one pager for [company]". Mode 2 (website assessment) triggers on "website assessment", "website audit", "CEO/COO website review", "growth assessment", "conversion audit for [company]". Both produce a beautifully designed, on-brand PDF with the Solum design system, client logo trust strip, and a prominent CTA to book at https://getsolum.com/book. Output goes to ~/Documents/Claude/<project>/prospects/<target>/ as both .pdf and .html.
---

# One-Pager Builder

Branded one-page PDF for sending directly to a prospect's C-suite. Two modes, same brand system, same render pipeline.

## Modes

**Mode 1 — Opportunity Brief** (default)
Revenue-opportunity brief. Solum workflows × prospect scale = conservative $ upside. Used for deal briefs, C-suite sales docs, post-research prospect write-ups.

**Mode 2 — Website Assessment**
CEO/COO website growth assessment. Conversion and operational gaps scored, with a 30-day action plan. Used as cold outreach hook, pre-meeting leave-behind, or conference follow-up.

Pick the mode based on the trigger. If the user says "opportunity brief" or "deal brief", run Mode 1. If they say "website assessment", "website audit", "conversion audit", or "CEO/COO review", run Mode 2. If ambiguous, ask.

Both modes end with a prominent CTA to book a call at **https://getsolum.com/book** (primary button, Solum Blue, footer right). Button label: "Book your assessment call" in Mode 2; "Book a call with JP" in Mode 1.

## When to invoke

Mode 1 triggers:
- "Build a one pager for [company]"
- "Opportunity brief for [company]"
- "Deal brief", "C-suite brief", "sales one-pager"
- "Write up [company] as a prospect"

Mode 2 triggers:
- "Website assessment for [company]"
- "Website audit", "conversion audit"
- "CEO/COO website review"
- "Growth assessment for [company]"
- "Assess [company]'s website"

## Required inputs (ask if missing)

1. **Target company** — website URL so we can read their services, scale, positioning
2. **Audience** — default is "C-suite"; ask if it's a specific exec (CCO, COO, CFO)
3. **What Solum runs for them** — which of Solum's workflows apply (referrals, intake, verification, prior auth, eligibility, waitlist, labor)
4. **Scale assumption for their network** — location count + rough system revenue (e.g., 500 locations × $700K avg = $350M). Critical for conservative modeling.
5. **Which verticals/clients to name-drop** — pick Solum clients that map to the prospect's segment (PT → Rise PT, ABA → Hi5/Blossom, therapy → SLEA/Brighter Strides)

## Variants

- **Opportunity brief** (default) — the FYZICAL pattern. Hero = dollar stake, 5 opportunity cards, thesis, totals band. Use when pitching a prospect on Solum's offering.
- **Site & intake audit** — use the prompt at `prompts/website-assessment.md`. Hero = worst finding, audit scorecard, 5 findings, thesis, 30-day plan. Use when doing a website assessment for a CEO/COO.

Both render into the same HTML template with different section content.

## Workflow

### Step 1 — Research

- Browse the target's website via gstack to pull their service lines, scale, franchise/company model
- Note their largest/most admin-heavy service lines (these drive the opportunities)
- Pull their estimated location count and annual revenue; if unclear, model conservatively

### Step 2 — Model (conservative numbers)

Anchor ALL estimates to the prospect's estimated system revenue. Never exceed 5–10% of their total revenue as combined annual upside.

Standard ranges (adjust by vertical):
- **Prior Auth:** $15–25K/location (0.5–1 FTE savings + faster revenue)
- **Referral Capture:** $10–18K/location (10–15% of lost referrals recovered, not 30%)
- **Front-Office Labor:** $8–12K/location (20–30% admin time, not 40%)
- **Insurance Verification:** $6–10K/location (1–2% revenue recovery)
- **Eligibility/Caps:** $4–6K/location (mid-plan denial prevention)

Combined network target: **5–9% of estimated system revenue**. If your sum exceeds 10% of their revenue, cut numbers.

Split the combined:
- Recaptured revenue: ~40% of combined
- Cost + leakage saved: ~60% of combined

### Step 3 — Write copy

Follow `references/copy-rules.md`:
- No em dashes (—). Use periods and commas.
- No buzzwords: "leverage", "synergy", "unlock", "partner", "journey", "solution".
- Peer-to-peer tone (CEO-to-CEO), not vendor-to-buyer.
- Lead the hero with the network $ number, not the product.
- Order the five opportunities by size of prize, largest first.
- Sign off as JP Montoya personally; avatar + clear contact block.

### Step 4 — Render

1. Start from `templates/opportunity-brief.html`.
2. Fill placeholders with target-specific copy + numbers.
3. Copy client logos from `references/client-logos.md` URLs into `<target>/client-logos/`.
4. Copy Solum wordmark SVG from `~/Documents/Claude/landing-page/logo-solumhealth-dark.svg` to the output folder.
5. Run `scripts/build.sh <output-folder>` to generate PDF and screenshot.

### Step 5 — Verify

- `mdls -name kMDItemNumberOfPages <file>.pdf` must return `1`.
- Read the screenshot and confirm: logo prominent, cards aligned, trust strip visible, totals band clean, JP contact readable.
- If content overflows, tighten copy (cards to 1 sentence), not design.

## Output structure

```
~/Documents/Claude/<project>/prospects/<target>/
├── <target>-opportunities.pdf     # deliverable
├── <target>-opportunities.html    # source
├── <target>-opportunities.txt     # plain text fallback
├── logo-solumhealth-dark.svg
└── client-logos/
    ├── rise-pt.avif
    ├── hi5-aba.avif
    └── ...
```

## Design rules (brand system)

Full brand reference: `~/Documents/Claude/Skills/jpstack/solum-health-brand/SKILL.md`.

Quick rules:
- Font: DM Sans via Google Fonts (400, 500, 700)
- Page: 8.5in × 11in, padding 0.3in × 0.42in, section gap 10px
- Navy (#011C40) hero, teal→blue→purple gradient totals band
- Navy franchise/thesis callout between opportunities and totals
- 5 opp cards in 3 (top row) + 2 (centered bottom row) layout, all with identical Solum Blue left border + blue numbered chip
- Grayscale client logo strip with `filter: grayscale(100%) opacity(0.78)`
- Logo: 38px height in header, paired with "CONFIDENTIAL · For [TARGET] Leadership" meta

See `references/print-rules.md` for print-correct CSS and Chrome headless command.

## Common pitfalls

- **Overflow to page 2** → tighten card copy to one sentence; reduce section gaps to 8px; never shrink hero.
- **Numbers too aggressive** → always anchor to prospect's estimated revenue; if summed opportunities exceed 10% of their revenue, cut.
- **Generic client logos** → match clients to prospect's vertical. PT prospect → lead with Rise PT.
- **Em dashes slip in** → use en dashes only inside number ranges ($15–25K); everywhere else use periods.
- **Logo looks tiny** → header logo must be ≥36px height, not a favicon.
- **Boilerplate company snapshot** → NEVER include "Acme is a company that does X." The C-suite reader knows who they are.

## Don't

- Don't say "pilot" unless the user explicitly asks for one.
- Don't include long company-snapshot paragraphs about the prospect.
- Don't use "Annie" in the headline; lead with the economic stake, defer the product name.
- Don't claim nine-figure EV multiples unless the user confirms they'll defend the math on a call.
- Don't add generic "Industries We Serve" sections; the trust strip earns the same signal visually.
