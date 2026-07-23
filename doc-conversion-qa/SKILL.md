---
name: doc-conversion-qa
description: Quality-guard for document format conversions. AUTOMATICALLY trigger before declaring success on any PDF→PPTX, PPTX→PDF, PDF→DOCX, DOCX→PDF, PDF→DOCX, or DOCX→PPTX conversion. Triggers on "convert this PDF to PPTX", "turn slides into editable", "PDF to Word", "DOCX to PDF", "export as PPTX", "reconstruct slides from PDF", "make this editable", or any request that produces a converted document. Validates visual fidelity (rendered output matches source), text completeness, no overlaps/clipping, font consistency, image preservation, and layout integrity. NEVER deliver a converted file without running this skill end-to-end first.
---

# Document Conversion QA Guard

Use this skill before declaring ANY document conversion done. The conversion is not complete until QA passes. If QA finds issues, fix them and re-QA. Repeat until clean.

## When to trigger (automatic)

Run this skill whenever a conversion produces one of these pairs:

- `.pdf` → `.pptx`
- `.pptx` → `.pdf`
- `.pdf` → `.docx`
- `.docx` → `.pdf`
- `.docx` → `.pptx`
- `.pptx` → `.docx`

Also trigger on natural-language asks like "convert this PDF to slides", "turn this deck into a PDF", "make these slides editable", "export to Word", "reconstruct as PowerPoint", "OCR this PDF into editable", "rebuild as DOCX".

## Hard rules

1. **Visual fidelity over speed.** A faster conversion that loses layout is a failure. Re-render until output matches source.
2. **No declaring success without rendered comparison.** You must convert the OUTPUT back to images and diff against the SOURCE rendered to images.
3. **No silent text loss.** Every paragraph in the source must appear in the output (modulo intentional edits).
4. **Fonts must be available.** If the source font isn't installed, install it or pick a brand-approved substitute (Solum default: Montserrat). Never let the renderer pick.
5. **Images and graphics preserved.** Backgrounds, photos, logos, icons, and shapes must survive the conversion.
6. **Editable means editable.** When the user asks for "editable text", every visible text run in the output must be selectable and modifiable in the target app.
7. **Confirm before publishing.** Show the user a side-by-side render (source vs output) and explicitly ask for sign-off before delivering the final file.

## QA checklist

For every conversion, run all of these. Treat each as a TaskCreate item.

### 1. Source inventory
- Count source pages/slides.
- Extract source text (all of it, including footers, headers, captions).
- Note source dimensions and aspect ratio.
- Identify all fonts used and check they are installed locally.

### 2. Output inventory
- Count output pages/slides — must equal source unless user asked for a subset.
- Extract output text.
- Diff text content: every non-trivial source string must appear in the output.

### 3. Visual diff
- Render source pages/slides to PNG at ≥150 DPI.
- Render output pages/slides to PNG at the same DPI.
  - Use `LibreOffice` (`soffice --headless --convert-to pdf`) + `pdftoppm` for PPTX/DOCX.
  - Use `pdftoppm` for PDF directly.
  - Use `qlmanage -t -s 1600` for first-slide quick check on macOS only when LibreOffice is unavailable; do NOT trust this alone for multi-page output.
- Visually compare each pair. Flag every discrepancy:
  - Overlapping elements (text through shapes, lines through words)
  - Text overflow or clipping at margins
  - Misaligned columns / cards / sections
  - Words mashed together (no spaces between concatenated tokens)
  - Wrong colors (light text on light bg, dark on dark)
  - Missing or stretched images
  - Blank regions where the source had content
  - Shifted positions > 0.1" from source
  - Wrong wrapping (line breaks in different places)

### 4. Editability check (for output to PPTX/DOCX)
- Open one slide / page in the target app conceptually: would each text element be selectable and editable?
- Confirm there are no rasterized text bitmaps where editable text was promised.

### 5. Brand check
- Default font is Montserrat unless source dictates otherwise.
- Solum brand colors preserved if source is a Solum doc (run the `solum-health-brand` skill in parallel).

### 6. Sign-off gate
- Produce a side-by-side preview image (`source_pN.png` vs `output_pN.png`) for each page.
- Show the user the previews.
- Wait for explicit "ship it" / "looks good" before copying the final file to its destination.

## Tooling

The skill ships with helper scripts under `scripts/`:

- `scripts/render_pdf.py <input.pdf> <out_dir>` — renders each PDF page to PNG.
- `scripts/render_pptx.py <input.pptx> <out_dir>` — converts to PDF via LibreOffice, then to PNGs.
- `scripts/render_docx.py <input.docx> <out_dir>` — same idea for DOCX.
- `scripts/diff_text.py <source> <output>` — extracts text from each side and diffs by paragraph.
- `scripts/qa_report.py <source> <output>` — full report: counts, diff, side-by-side preview index HTML.

Always run `qa_report.py` last and read the report before declaring done.

## Failure modes seen in the wild

| Symptom | Root cause | Fix |
|---|---|---|
| Words mashed together ("ImmadAkhund") | PDF stores words as separate spans with visual gap but no space char; converter dropped the gap | Detect horizontal gap between consecutive spans on the same line; insert a single space when gap > 0.2 × font_size and neither side has whitespace |
| Text shows through twice (image + editable overlay) | Used original page render as background plus overlay | Redact source text before rendering background, then add editable overlays |
| Headlines wrap to a different number of lines | Substitute font has different metrics than source | Install the actual source font OR widen text boxes by ~25% and disable autosize |
| Spacing looks "off" between every word | Each word was placed as its own text box at PDF coordinates | Group spans by PyMuPDF line, place ONE text box per line, preserve runs for color/weight |
| Output PPTX is one giant raster image | Conversion tool fell back to image mode | Switch tool; rebuild with python-pptx + per-line text boxes |
| Slide aspect ratio looks letterboxed | PPTX defaulted to 16:9 / 4:3 vs source | Set `prs.slide_width` / `slide_height` to source dimensions exactly |
| Source font not on system → ugly substitution at view time | Author didn't install brand fonts | Install Montserrat from `https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/` to `~/Library/Fonts/` and confirm with `file` (must be `TrueType Font data`, not HTML) |

## Refuse-to-ship triggers

Do NOT deliver if any of these are true:
- You haven't rendered the output and visually compared it to the source.
- Text is missing, mashed, or duplicated.
- Any image, logo, or icon from the source is absent in the output.
- The user asked for editable text and any visible text run is rasterized.
- Aspect ratio or page size differs from source without user consent.
- Fonts substitute to something off-brand.

If any of the above holds, fix it, re-render, re-diff, then re-ask the user.
