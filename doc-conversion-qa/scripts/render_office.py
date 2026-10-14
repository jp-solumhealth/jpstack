#!/usr/bin/env python3
"""Render a PPTX or DOCX to per-page PNGs via LibreOffice + pdftoppm.

Usage: render_office.py <input.pptx|input.docx> <out_dir> [dpi]
"""
import sys, os, shutil, subprocess, tempfile

SOFFICE_CANDIDATES = [
    "soffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "/usr/bin/soffice",
    "/usr/local/bin/soffice",
]

def find_soffice():
    for c in SOFFICE_CANDIDATES:
        if shutil.which(c) or os.path.exists(c):
            return c
    sys.exit("LibreOffice (soffice) not found. Install with: brew install --cask libreoffice")


def main(src, out_dir, dpi=150):
    os.makedirs(out_dir, exist_ok=True)
    soffice = find_soffice()
    base = os.path.splitext(os.path.basename(src))[0]
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", td, src],
            check=True,
        )
        pdf_path = os.path.join(td, base + ".pdf")
        if not os.path.exists(pdf_path):
            sys.exit(f"LibreOffice did not produce {pdf_path}")
        prefix = os.path.join(out_dir, base)
        subprocess.run(
            ["pdftoppm", "-jpeg", "-r", str(dpi), pdf_path, prefix],
            check=True,
        )
    for f in sorted(os.listdir(out_dir)):
        if f.startswith(base):
            print(os.path.join(out_dir, f))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("usage: render_office.py <input.pptx|.docx> <out_dir> [dpi]")
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 150
    main(sys.argv[1], sys.argv[2], dpi)
