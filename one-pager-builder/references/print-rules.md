# Print Rules

One page. 8.5in × 11in. No exceptions.

## Required CSS

```css
@page {
  margin: 0;
  size: 8.5in 11in;
}

@media print {
  .page { box-shadow: none; }
}

.page {
  width: 8.5in;
  height: 11in;
  margin: 0 auto;
  padding: 0.3in 0.42in 0.24in;
  background: #FFFFFF;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
}

* {
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
```

Note the `height: 11in` (not `min-height`) plus `overflow: hidden`. This is what prevents a stray 2-line overflow from creating a second page.

## Budget (approximate heights at 96dpi)

- Total page: 1056px
- Top + bottom padding: 52px
- Header: 58px
- Hero: 110px
- What Solum Runs title + 3 stats: 95px
- Trusted By strip: 52px
- Opportunities title + 5 cards (2 rows): 230px
- Franchise callout: 72px
- Totals band: 95px
- Footer: 56px
- Gaps (10px × 8): 80px
- **Total**: ~900px, leaves ~100px of margin

If you exceed, cut copy before you cut design.

## Chrome headless command

```bash
cd <output-dir> && "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless \
  --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf=<name>.pdf \
  "file://$(pwd)/<name>.html"
```

## Verification

```bash
# Must return 1
mdls -name kMDItemNumberOfPages <file>.pdf

# Screenshot for visual check
B=~/.claude/skills/gstack/browse/dist/browse
$B goto "file://$(pwd)/<name>.html"
$B viewport 850x1100
$B screenshot /tmp/<name>-preview.png
# Then Read the screenshot and confirm alignment, logo size, card heights.
```

## Debugging overflow

If the PDF is 2 pages and you need to shave height, in priority order:

1. **Shorten opportunity card descriptions** to exactly one sentence (saves 20–40px)
2. **Reduce section gaps** from 10px to 7px (saves 24px)
3. **Reduce hero padding** from 14px to 10px (saves 8px)
4. **Shrink hero H1** from 20px to 18px (saves 6px)
5. **Reduce page padding** from 0.3in to 0.22in (saves 16px)

NEVER shrink:
- Logo below 36px height
- Body copy below 10px
- Card chip below 20px square
- Totals band font below 18px for the numbers

## AVIF images (client logos)

Chrome headless supports AVIF natively. No conversion needed.

If a logo does not render in PDF, verify:
- Path is relative to the HTML file (not absolute)
- File exists in the output folder
- File is not 0 bytes (curl sometimes gets rate-limited)
