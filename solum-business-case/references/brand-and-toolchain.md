# Brand & Toolchain

## Brand (Solum Health)

- **Navy** `#011C40` — headers, footers, dark cards. (The bundled logo's background is exactly this
  navy, so it blends seamlessly on a navy band.)
- **Solum Blue** `#468AF7` — accents, key figures, the recommended-path highlight.
- **Teal** `#70D3C6` — secondary accent (e.g., the validation window on the timeline, gradient bars).
- **Light bg** `#F2F2F9`, **alt row** `#F5F7FA`, **ink** `#0F1B2D`.
- **Font** `DM Sans` (Google Fonts). In Excel it falls back gracefully; in HTML it's imported.
- **Logo**: `assets/solum_logo.png` (white SolumHealth wordmark on navy). Use on navy bands. The deck
  cover and every slide header use it.
- Always sanity-check output against the `solum-health-brand` skill if unsure.

## Toolchain (this Mac — no Homebrew/LibreOffice; works in background jobs)

- **Excel**: `openpyxl`. Use formulas, not hardcoded values. Set `wb.calculation.fullCalcOnLoad=True`
  so Excel/Numbers recalculates on open (LibreOffice `recalc.py` is unavailable — no `soffice`).
  Verify math independently in Python and scan for `#REF!`/bad cross-sheet refs.
- **Slides → PDF**: author in HTML+CSS, render with **Chrome headless**:
  ```bash
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
    --no-pdf-header-footer --print-to-pdf=out.pdf "file://<abs.html>"
  ```
  Use `@page{size:13.333in 7.5in}` for 16:9 slides. Best design fidelity available here.
- **PDF page → PNG (visual QA)**: render via Quartz in Python (no poppler/`pdftoppm`):
  `CGPDFDocumentCreateWithURL` → `CGBitmapContextCreate` (scale 1.3–2.0) → `CGContextDrawPDFPage` →
  `CGImageDestination`. Multi-page, unlike `sips`. The deck builder writes `slideN.png` for review.
- **PPTX (editable)**: build with `python-pptx` by placing one **full-bleed 2× PNG render per slide**
  (`add_picture(img,0,0,width=Inches(13.333),height=Inches(7.5))`). This guarantees the design renders
  identically on any machine (no font-not-installed breakage) and is presentable directly.
- **GUI automation** (`osascript`/Numbers/Keynote) fails in background jobs (-609). Don't rely on it;
  use the headless paths above.

## Output location

Save artifacts under `~/Documents/Claude/solum-ops/clients/<slug>/` (create if missing). Never write
loose files outside `~/Documents/Claude/`.
