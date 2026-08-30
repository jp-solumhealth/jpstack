---
date: 2026-05-08
task: Convert pages 3-4 of a Solum proposal PDF into editable PPTX, text editable, images preserved, on-brand (Montserrat)
outcome: succeeded after 3 iterations
tags: [pdf-to-pptx, document-conversion, fonts, color-fidelity, pymupdf, python-pptx, visual-qa]
---

## What the user asked for

"Take slides 3 and 4 of the v3 proposal PDF and convert into editable .pptx for only the text. Images can stay as-is." Then on iteration: "use montserrat … please confirm everything the same before publishing." Then: "letter is not white, font its black, it doesn't match."

## What I did first (the wrong path)

- v1: Placed each PDF text span as its own text box at exact PDF coordinates. Visible gaps between every word ("BACKED   BY"). Looked like AI garbage.
- v2: Switched to one text box per logical line. Stripped whitespace-only spans, lost spaces ("Themosttrustedfunds"). Re-fixed. Still names like "Immad Akhund" mashed together because the source PDF stores them as two spans with positional gap and no space character.
- v2 also: trusted the Montserrat .ttf files already in `~/Library/Fonts` — they were corrupted HTML downloads.
- v2 used `span['color']` from PyMuPDF as the text color. PyMuPDF reported `0` (black) for the headline, but the rendered PDF actually paints those glyphs white. Result: black text on navy bg — invisible / wrong.
- Trusted that installing Montserrat in `~/Library/Fonts` would make PowerPoint render it. PowerPoint substituted with a serif anyway.

## Why it was wrong

Three independent root causes I should have anticipated:

1. **Trusted PDF metadata over rendered pixels.** Type 3 / subsetted fonts in modern decks frequently have `span.color` that disagrees with the painted color (color comes from a graphics-state override, not the span). PyMuPDF returns the metadata color, not the visual one.
2. **Trusted system font install to propagate to PowerPoint.** PowerPoint on macOS does not always pick up newly-installed `~/Library/Fonts/*.ttf` for already-running app instances and won't help recipients who don't have the font at all. The PPTX must carry the font itself.
3. **Trusted local font files without verifying.** A `.ttf` extension on disk is not proof of a TrueType file. Always `file <path>` to confirm magic bytes.

## What actually worked

- **Color**: render the original PDF page to a PNG, then for each text line crop the bbox, find background color from the top/bottom strips, take the dominant pixel that's far from background as the text color. Source of truth = pixels, not metadata.
- **Fonts on disk**: download Montserrat from `https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Regular.ttf` (and `-Bold.ttf`). Verify with `file` — must read `TrueType Font data`, not HTML.
- **Font in PPTX**: embed the TTF inside the .pptx by:
  - Adding `ppt/fonts/Montserrat-Regular.fntdata` (raw TTF bytes, `.fntdata` extension).
  - Adding an `embeddedFontLst` block in `ppt/presentation.xml` with `regular` and `bold` references.
  - Adding font Relationships in `ppt/_rels/presentation.xml.rels`.
  - Ensuring `[Content_Types].xml` has a `Default Extension="fntdata" ContentType="application/x-fontdata"`.
- **Spaces between mashed spans**: detect horizontal gap between consecutive spans on the same line; if `gap > 0.20 * font_size` and neither side already ends/starts with whitespace, insert a single space run.
- **Don't strip interior whitespace spans.** Only trim leading and trailing whitespace-only spans; keep them between words.
- **One text box per PyMuPDF line**, not per span. Use multiple runs inside the paragraph for color/weight changes.
- **Visual QA loop**: render output back to images and side-by-side diff against source. Don't declare done without it.

## Round 3 — bold detection

Type 3 subsetted fonts in modern decks give no weight info in the font name (everything is "Unnamed-T3"), so `is_bold(span.font)` always returned False and headlines + card titles rendered as regular weight. Fix: combine three signals:
- Source font name says bold/black/heavy → bold.
- Font size ≥ 14pt → bold (always headlines).
- **Ink density** (distinct-pixels / bbox-area in the rendered original) ≥ 0.16 → bold. Catches small bold runs that share a font name with regular siblings (e.g. card titles vs. card descriptions, both at 9.75pt but different weights).

Reuse the color-sampling pass to also count ink pixels — same loop, no extra render.

## Round 2 (slide 11 — security)

Three more sharp edges showed up converting the security slide:

- **Icon-font glyphs.** Cards used a Lucida Grande `✓` (U+2713). Montserrat doesn't have that codepoint, so PowerPoint rendered missing-glyph boxes. Fix: detect "icon-like" spans (`ord(c) > 0x2010` or font family ≠ the body font) and skip them entirely from BOTH the redaction and the overlay so they survive in the background image.
- **Multi-color line ("Built for PHI from day one." with blue accent).** Per-line color sampling averaged into white. Fix: sample color **per span**, not per line.
- **Text occluded by drawn rectangles.** The PDF stored "GETSOLUM.COM | HELLO@GETSOLUM.COM" and "CONFIDENTIAL" at coordinates that the original PDF later painted a navy footer rectangle over — invisible in the rendered PDF but still present in the text extraction. My code re-painted them on top of the navy strip in the output. Fix: after rendering the original at high DPI, check the text bbox: if < 4% of the bbox pixels differ meaningfully from the surrounding background, the text is occluded — skip the overlay AND skip the redaction (leave it hidden under the graphic).

## The rule for next time

For any PDF→PPTX/DOCX where visual fidelity matters:

1. **Pixel-sample colors.** Never use `span.color` from PyMuPDF as the source of truth. Render the original page, sample inside the text bbox, subtract background.
2. **Embed the font in the output file.** Don't rely on the recipient (or PowerPoint instance) having it installed.
3. **Verify font files with `file`** before trusting any `.ttf` on disk.
4. **One text box per logical line, multi-run for styles.** Never one box per word.
5. **Preserve interior whitespace spans; insert spaces on visual gaps.**
6. **Render output → diff against source before declaring done.**
7. **Skip icon-font glyphs** from redaction + overlay. Detect by codepoint range or font family.
8. **Detect occlusion**: if < 4% of the rendered bbox pixels are distinct from background, the text is hidden by a graphic — leave it alone.
9. **Render the actual output via Keynote** (`osascript` export to slide images) when LibreOffice isn't available. Do NOT trust Quick Look for full-deck QA.
10. Use the `doc-conversion-qa` skill — it codifies the checklist.

## Signals to watch for

- User says "looks the same" / "letters not white" / "font is black/serif" → trusted metadata, not pixels.
- PowerPoint shows serif when you set sans-serif → font is not embedded; recipient doesn't have it.
- Words mashed together → dropped whitespace spans or didn't insert space on positional gap.
- File looks fine in Quick Look but wrong in PowerPoint → Quick Look uses macOS rendering; PowerPoint enforces font availability differently. Always render via LibreOffice or open in target app.
- `file foo.ttf` outputs `HTML document` → the download was an HTML page (rate-limited / login wall), not the font.
