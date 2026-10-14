# Postmortem Index

Tag-indexed list of lessons. Read the rows whose tags match your task BEFORE starting work.

## How to use

1. Scan tags below. Open every lesson file that matches.
2. Read at least: "The rule for next time" and "Signals to watch for".
3. State in your message which lessons you applied.

---

## By tag

### color-fidelity
- [2026-05-08 — PDF→PPTX fidelity](lessons/2026-05-08_pdf-to-pptx-fidelity.md) — never trust PDF span metadata for text color; sample rendered pixels.

### document-conversion
- [2026-05-08 — PDF→PPTX fidelity](lessons/2026-05-08_pdf-to-pptx-fidelity.md)

### fonts
- [2026-05-08 — PDF→PPTX fidelity](lessons/2026-05-08_pdf-to-pptx-fidelity.md) — embed TTFs into .pptx; verify `.ttf` files with `file`; never assume PowerPoint sees newly-installed fonts.

### pdf-to-pptx
- [2026-05-08 — PDF→PPTX fidelity](lessons/2026-05-08_pdf-to-pptx-fidelity.md)

### pymupdf
- [2026-05-08 — PDF→PPTX fidelity](lessons/2026-05-08_pdf-to-pptx-fidelity.md) — `span['color']` lies for Type 3 / subsetted fonts; whitespace-only spans matter; one bbox per line not per span.

### python-pptx
- [2026-05-08 — PDF→PPTX fidelity](lessons/2026-05-08_pdf-to-pptx-fidelity.md)

### visual-qa
- [2026-05-08 — PDF→PPTX fidelity](lessons/2026-05-08_pdf-to-pptx-fidelity.md) — render output back to images and side-by-side diff; Quick Look ≠ PowerPoint.
