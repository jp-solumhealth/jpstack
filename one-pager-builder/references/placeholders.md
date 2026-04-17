# Template Placeholders

Fill these in `templates/opportunity-brief.html` before rendering.

## Header

| Placeholder | Example | Notes |
|---|---|---|
| `{{TARGET_NAME}}` | `FYZICAL` | Uppercase or brand-cased as the target uses it. |
| `{{DATE}}` | `April 17, 2026` | Today's date, spelled out. |

## Hero

| Placeholder | Example |
|---|---|
| `{{HERO_NUMBER}}` | `$20&ndash;35M a year` |
| `{{HERO_HEADLINE_TAIL}}` | `is sitting in<br/>FYZICAL's front offices.` |
| `{{HERO_SUBHEAD}}` | `Across 500+ locations, the gap between referral received and visit paid is where enterprise value quietly leaks. Below is what it takes to recover it.` |

## What Solum Runs

| Placeholder | Example |
|---|---|
| `{{STAT1_VALUE}}` | `Multi-location PT, Rehab &amp; Therapy` |
| `{{STAT1_SUB}}` | `Runs on top of your EHR. Referrals, intake, verification, prior auth, scheduling, and waitlist.` |

Stat 2 and 3 are fixed ($247K, Deploys in weeks) unless a specific context requires change.

## Trust strip

| Placeholder | Example |
|---|---|
| `{{TRUST_SUBLABEL}}` | `Multi-location PT, ABA &amp; Therapy` |
| `{{CLIENT_LOGOS}}` | (7 `<img>` tags, see below) |

Client logo block example:
```html
<img src="client-logos/rise-pt.avif" alt="Rise Physical Therapy" />
<img src="client-logos/bespoke.avif" alt="Bespoke Treatments" />
<img src="client-logos/golden-hand.avif" alt="Golden Hand Therapy" />
<img src="client-logos/akp.avif" alt="Always Keep Progressing" />
<img src="client-logos/brighter-strides.avif" alt="Brighter Strides" />
<img src="client-logos/hi5-aba.avif" alt="Hi5 ABA" />
<img src="client-logos/slea.avif" alt="SLEA Therapies" />
```

Pick logos matching the prospect's vertical from `references/client-logos.md`.

## Opportunities

| Placeholder | Example |
|---|---|
| `{{OPPS_PILL}}` | `Ordered by size of prize &middot; ~500 locations` |
| `{{OPP_CARDS}}` | 5 opp-card `<div>` blocks |

One opp card:
```html
<div class="opp">
  <div class="opp-head">
    <div class="chip">01</div>
    <div class="kicker">Prior Authorization</div>
  </div>
  <h3>Hours, not weeks</h3>
  <div class="desc">Auth work eats close to 1 FTE per clinic. Solum submits, tracks, and escalates automatically.</div>
  <div class="metrics">
    <span class="metric">$15&ndash;25K / location</span>
    <span class="metric net">$8&ndash;12M / yr</span>
  </div>
</div>
```

Order largest-dollar first. Descriptions: exactly one sentence.

## Thesis callout

| Placeholder | Example |
|---|---|
| `{{THESIS_BADGE}}` | `The Franchise Thesis` |
| `{{THESIS_HEADLINE}}` | `The front office is where the playbook breaks.` |
| `{{THESIS_BODY}}` | `FYZICAL's moat is replicable unit economics across 500+ independently-owned locations. Every owner hires, trains, and loses admins on their own cycle, and every location drifts from the playbook. Solum collapses that variance. One operational layer corporate owns.` |
| `{{THESIS_CLOSE}}` | `What you standardize, you scale.` |

Use "Franchise Thesis" for franchise models, "Scale Thesis" for roll-ups/MSOs, "Growth Thesis" for single-owner groups.

## Totals band

| Placeholder | Example |
|---|---|
| `{{TOTALS_TITLE}}` | `The Network Number` |
| `{{TOTALS_SUB}}` | `Conservative. 5&ndash;9% of estimated system revenue. Owned by corporate, not split across 500 P&amp;Ls.` |
| `{{TOTAL_REVENUE}}` | `$8&ndash;13M` |
| `{{TOTAL_SAVED}}` | `$12&ndash;22M` |
| `{{TOTAL_COMBINED}}` | `$20&ndash;35M+` |

Totals must equal the sum of the 5 opportunity network numbers within rounding.

## Footer CTA

| Placeholder | Example (Mode 1 — Opportunity Brief) | Example (Mode 2 — Website Assessment) |
|---|---|---|
| `{{FOOTER_CTA}}` | `Happy to walk the model. 30 minutes, peer to peer.` | `Happy to walk the audit. 30 minutes, no strings.` |
| `{{BOOKING_URL}}` | `https://getsolum.com/book` | `https://getsolum.com/book` |
| `{{BOOKING_LABEL}}` | `Book a call with JP` | `Book your assessment call` |

The booking button is a primary CTA (Solum Blue pill, white text) sitting directly under the peer-to-peer line, above the confidentiality note.

## Character notes

- Use `&ndash;` for en dashes in number ranges (`$10&ndash;20K`).
- Use `&middot;` for middots (`Ordered &middot; ~500 locations`).
- Use `&amp;` for ampersands in HTML text.
- Use `<br/>` for explicit line breaks in the hero headline.
- No em dashes (`—`). Period.
