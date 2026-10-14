---
name: mobile-audit
description: >
  Measured mobile-optimization audit of a deployed page using real Chromium at
  phone, large-phone and tablet widths. Reports horizontal scroll, unclipped
  overflow, touch targets under 44px, and text under 12px. Use when asked to
  "check mobile", "is it mobile optimized", "mobile audit", "responsive check",
  or before/after a landing page deployment.
---

# Mobile Audit

Renders a live URL in headless Chromium at three widths and reports **measured**
failures. Nothing here is inferred from reading CSS — every finding comes from
`getBoundingClientRect()` on the rendered page.

## Run it

```bash
node mobile-audit/scripts/audit.js https://your-url.com
node mobile-audit/scripts/audit.js https://your-url.com --json   # machine-readable
```

Requires Playwright. In this environment Chromium is preinstalled:

```bash
NODE_PATH=/opt/node22/lib/node_modules node mobile-audit/scripts/audit.js <url>
```

Exit code is **1** if any viewport has a blocking issue, so it can gate a deploy.

## Viewports tested

| Width | Device |
|-------|--------|
| 375px | iPhone SE / 13 mini |
| 390px | iPhone 14/15 |
| 768px | iPad portrait |

## What counts as blocking

- **Horizontal page scroll** — `scrollWidth > clientWidth`. Always a bug.
- **Unclipped overflow** — an element extending past the right edge with no
  `overflow:hidden|auto` ancestor.

## What is reported but not blocking

- **Touch targets under 44px tall** (Apple HIG minimum).
- **Text under 12px.**

These are judgement calls: chrome inside a product mockup can legitimately use
8–10px type, while a real nav link at 11px is a genuine problem.

## The false-finding trap

**Do not report an element as overflowing just because its right edge exceeds
the viewport.** Marquees, logo strips and testimonial carousels are *designed*
to extend past the viewport inside an `overflow:hidden` parent. The script
walks each element's ancestors and skips anything already clipped. Preserve
that check — removing it produces a report full of false alarms.

Likewise, a fixed `width` in the CSS is not automatically a bug. Decorative
glows are absolutely positioned inside clipped parents and never affect layout.
Measure the render; don't grep the stylesheet.

## Checks this does NOT cover

Run these by eye or add them if needed:

- Real-font metrics when webfonts are blocked by a proxy (text can be wider).
- JS-driven layout that needs interaction (tabs, accordions, modals).
- Color contrast, focus states, screen-reader semantics.
- Landscape orientation, foldables, very large phones.
