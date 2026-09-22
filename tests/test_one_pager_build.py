"""Offline regression tests for the one-pager build script (standard library only).

Run: python3 -m unittest discover -s tests -p 'test_one_pager_build.py' -v
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "one-pager-builder/scripts/build.sh"
FRESH_PDF = b"%PDF-1.4\nfresh test output\n%%EOF\n"
OLD_PDF = b"%PDF-1.4\nprevious deliverable\n%%EOF\n"


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="one-pager-test-")
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.html = self.root / (self.root.name + ".html")
        self.html.write_text("<!doctype html><p>Example</p>", encoding="utf-8")
        self.pdf = self.html.with_suffix(".pdf")
        self.png = Path("/tmp") / (self.html.stem + "-preview.png")
        self.args_log = self.root / "chrome-args.json"
        chrome = self.executable("fake chrome", '''
import json, os, pathlib, sys
pathlib.Path(os.environ["ARGS_LOG"]).write_text(json.dumps(sys.argv[1:]))
output = pathlib.Path(next(a.split("=", 1)[1] for a in sys.argv if a.startswith("--print-to-pdf=")))
mode = os.environ.get("RENDER_MODE", "success")
if mode == "no-output":
    sys.exit(0)
if mode == "empty":
    output.touch()
elif mode == "invalid":
    output.write_bytes(b"not a PDF")
else:
    output.write_bytes(b"%PDF-1.4\\nfresh test output\\n%%EOF\\n")
if mode == "fail":
    print("renderer diagnostic", file=sys.stderr)
    sys.exit(42)
''')
        self.executable("pdfinfo", '''
import os, sys
mode = os.environ.get("PDFINFO_MODE", "1")
if mode == "fail":
    sys.exit(1)
print("Pages:          " + mode)
''')
        self.executable("mdls", '''
import os, sys
mode = os.environ.get("MDLS_MODE", "(null)")
if mode == "fail":
    sys.exit(1)
print(mode)
''')
        self.env = os.environ.copy()
        self.env.update(
            CHROME_BIN=str(chrome),
            BROWSE_BIN=str(self.root / "not-installed"),
            ARGS_LOG=str(self.args_log),
            PATH=str(self.bin) + os.pathsep + self.env.get("PATH", ""),
            RENDER_MODE="success", PDFINFO_MODE="1", MDLS_MODE="(null)",
        )

    def tearDown(self):
        self.png.unlink(missing_ok=True)
        self.temp.cleanup()

    def executable(self, name, body):
        path = self.bin / name
        path.write_text("#!" + sys.executable + "\n" + body, encoding="utf-8")
        path.chmod(0o755)
        return path

    def build(self, html=None, **environment):
        env = dict(self.env, **environment)
        result = subprocess.run(
            ["bash", str(SCRIPT), str(html if html is not None else self.html)],
            cwd=self.root, env=env, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(list(self.root.rglob(".one-pager-build.*")), [], "temporary build directory leaked")
        return result

    def assert_failed_without_replacing(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("Done.", result.stdout)
        self.assertEqual(self.pdf.read_bytes(), OLD_PDF)

    def test_renderer_failure_preserves_previous_pdf_even_if_it_wrote_output(self):
        self.pdf.write_bytes(OLD_PDF)
        result = self.build(RENDER_MODE="fail")
        self.assert_failed_without_replacing(result)
        self.assertIn("renderer diagnostic", result.stderr)

    def test_success_without_output_does_not_reuse_old_pdf(self):
        self.pdf.write_bytes(OLD_PDF)
        self.assert_failed_without_replacing(self.build(RENDER_MODE="no-output"))

    def test_empty_output_preserves_previous_pdf(self):
        self.pdf.write_bytes(OLD_PDF)
        self.assert_failed_without_replacing(self.build(RENDER_MODE="empty"))

    def test_invalid_pdf_signature_preserves_previous_pdf(self):
        self.pdf.write_bytes(OLD_PDF)
        self.assert_failed_without_replacing(self.build(RENDER_MODE="invalid"))

    def test_failed_first_build_does_not_create_a_deliverable(self):
        result = self.build(RENDER_MODE="fail")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.pdf.exists())
        self.assertNotIn("Done.", result.stdout)

    def test_success_atomically_replaces_previous_pdf(self):
        self.pdf.write_bytes(OLD_PDF)
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.pdf.read_bytes(), FRESH_PDF)
        self.assertIn("Pages: 1", result.stdout)
        self.assertIn("Done.", result.stdout)
        args = json.loads(self.args_log.read_text())
        render_path = Path(next(a.split("=", 1)[1] for a in args if a.startswith("--print-to-pdf=")))
        self.assertEqual(render_path.parent.parent, self.pdf.parent)
        self.assertNotEqual(render_path, self.pdf)

    def test_relative_paths_are_absolute_and_url_encoded(self):
        folder = self.root / "folder # ? % ü"
        folder.mkdir()
        html = folder / "prospect's brief # ? %.html"
        html.write_text("<!doctype html><p>Example</p>", encoding="utf-8")
        result = self.build(html.relative_to(self.root))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(html.with_suffix(".pdf").read_bytes(), FRESH_PDF)
        self.assertEqual(json.loads(self.args_log.read_text())[-1], html.as_uri())

    def test_missing_input_is_an_error(self):
        result = self.build(self.root / "missing.html")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.args_log.exists())
        self.assertIn("HTML file not found", result.stderr)

    def test_missing_browser_is_an_error_without_replacing_pdf(self):
        self.pdf.write_bytes(OLD_PDF)
        result = self.build(CHROME_BIN=str(self.root / "missing-chrome"))
        self.assert_failed_without_replacing(result)
        self.assertIn("Chrome/Chromium not found", result.stderr)

    def test_pdf_destination_directory_is_rejected(self):
        self.pdf.mkdir()
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination is a directory", result.stderr)
        self.assertFalse(self.args_log.exists())

    def test_multi_page_pdf_warns_without_discarding_output(self):
        result = self.build(PDFINFO_MODE="2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.pdf.read_bytes(), FRESH_PDF)
        self.assertIn("PDF is 2 pages", result.stderr)

    def test_mdls_fallback_counts_pages(self):
        result = self.build(PDFINFO_MODE="fail", MDLS_MODE="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Pages: 1", result.stdout)

    def test_unknown_page_count_warns_but_successful_render_survives(self):
        result = self.build(PDFINFO_MODE="fail", MDLS_MODE="fail")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Could not determine PDF page count", result.stderr)
        self.assertEqual(self.pdf.read_bytes(), FRESH_PDF)

    def test_optional_screenshot_failure_warns_but_preserves_pdf(self):
        browse = self.executable("fake browse", '''
import sys
print("screenshot service unavailable", file=sys.stderr)
sys.exit(2)
''')
        result = self.build(BROWSE_BIN=str(browse))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.pdf.read_bytes(), FRESH_PDF)
        self.assertIn("Optional screenshot failed", result.stderr)
        self.assertNotIn("Screenshot:", result.stdout)

    def test_optional_screenshot_success_without_file_is_a_warning(self):
        browse = self.executable("fake browse", "pass\n")
        result = self.build(BROWSE_BIN=str(browse))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Optional screenshot failed", result.stderr)
        self.assertNotIn("Screenshot:", result.stdout)

    def test_optional_screenshot_success(self):
        browse = self.executable("fake browse", '''
import pathlib, sys
if sys.argv[1] == "screenshot":
    pathlib.Path(sys.argv[2]).write_bytes(b"test screenshot")
''')
        result = self.build(BROWSE_BIN=str(browse))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.png.read_bytes(), b"test screenshot")
        self.assertIn("Screenshot:", result.stdout)


if __name__ == "__main__":
    unittest.main()
