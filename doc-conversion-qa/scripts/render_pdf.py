#!/usr/bin/env python3
"""Render each page of a PDF to PNG."""
import sys, os, fitz

def main(pdf_path, out_dir, dpi=150):
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    for i, page in enumerate(doc, 1):
        out = os.path.join(out_dir, f"{base}_p{i:02d}.png")
        page.get_pixmap(dpi=dpi, alpha=False).save(out)
        print(out)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("usage: render_pdf.py <input.pdf> <out_dir> [dpi]")
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 150
    main(sys.argv[1], sys.argv[2], dpi)
