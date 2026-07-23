#!/usr/bin/env python3
"""Build a side-by-side QA report (HTML) for source vs output."""
import sys, os, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def render(path, out_dir, dpi=150):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        subprocess.run(["python3", os.path.join(HERE, "render_pdf.py"), path, out_dir, str(dpi)], check=True)
    elif ext in (".pptx", ".docx"):
        subprocess.run(["python3", os.path.join(HERE, "render_office.py"), path, out_dir, str(dpi)], check=True)
    else:
        sys.exit(f"Unsupported: {ext}")


def main(src, out, report_dir):
    os.makedirs(report_dir, exist_ok=True)
    src_dir = os.path.join(report_dir, "source_pngs")
    out_dir = os.path.join(report_dir, "output_pngs")
    render(src, src_dir)
    render(out, out_dir)

    src_files = sorted(f for f in os.listdir(src_dir) if f.endswith((".png", ".jpg")))
    out_files = sorted(f for f in os.listdir(out_dir) if f.endswith((".png", ".jpg")))

    html = ['<!doctype html><meta charset=utf-8><style>',
            'body{font-family:system-ui;background:#111;color:#eee;margin:0;padding:24px}',
            'h2{margin:24px 0 8px}',
            '.row{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px}',
            '.row img{width:100%;border:1px solid #333}',
            '.lbl{font-size:12px;opacity:.7;margin-bottom:4px}',
            '</style>']
    html.append(f'<h1>QA: {os.path.basename(src)} → {os.path.basename(out)}</h1>')
    n = max(len(src_files), len(out_files))
    for i in range(n):
        html.append(f'<h2>Page {i+1}</h2><div class=row>')
        if i < len(src_files):
            html.append(f'<div><div class=lbl>SOURCE</div><img src="source_pngs/{src_files[i]}"></div>')
        else:
            html.append('<div><div class=lbl>SOURCE</div><i>missing</i></div>')
        if i < len(out_files):
            html.append(f'<div><div class=lbl>OUTPUT</div><img src="output_pngs/{out_files[i]}"></div>')
        else:
            html.append('<div><div class=lbl>OUTPUT</div><i>missing</i></div>')
        html.append('</div>')

    report_path = os.path.join(report_dir, "qa_report.html")
    with open(report_path, "w") as f:
        f.write("\n".join(html))
    print(f"\nReport: {report_path}")
    print(f"Source pages: {len(src_files)}  Output pages: {len(out_files)}")
    if len(src_files) != len(out_files):
        print("⚠️  Page count mismatch")

    # text diff
    subprocess.run(["python3", os.path.join(HERE, "diff_text.py"), src, out])


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit("usage: qa_report.py <source> <output> <report_dir>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
