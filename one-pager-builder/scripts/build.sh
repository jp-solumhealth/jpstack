#!/bin/bash
# Build one-pager PDF + optional screenshot from filled HTML.
# Usage: build.sh <html-file-path>
# Requires Python 3 and Chrome/Chromium; CHROME_BIN can select the executable.
# Keep logo-solumhealth-dark.svg and client-logos/ beside the HTML.

set -euo pipefail

fail() { echo "ERROR: $*" >&2; exit 1; }
HTML="${1:?Usage: build.sh <html-file-path>}"
[ -f "$HTML" ] || fail "HTML file not found: $HTML"
command -v python3 >/dev/null 2>&1 || fail "Python 3 is required to encode the local file URL."

# Resolve relative paths and encode spaces, #, %, ? and Unicode for file:// URLs.
HTML=$(python3 -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$HTML")
URI=$(python3 -c 'import pathlib, sys; print(pathlib.Path(sys.argv[1]).as_uri())' "$HTML")
DIR=$(dirname "$HTML")
BASE=$(basename "$HTML" .html)
PDF="$DIR/$BASE.pdf"
PNG="/tmp/$BASE-preview.png"
[ ! -d "$PDF" ] || fail "PDF destination is a directory: $PDF"

CHROME="${CHROME_BIN:-}"
if [ -z "$CHROME" ]; then
  for candidate in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
      google-chrome google-chrome-stable chromium chromium-browser; do
    if command -v "$candidate" >/dev/null 2>&1; then
      CHROME="$candidate"
      break
    fi
  done
fi
[ -n "$CHROME" ] && command -v "$CHROME" >/dev/null 2>&1 \
  || fail "Chrome/Chromium not found. Set CHROME_BIN to its executable path."

# A new directory beside the final PDF prevents an old output from passing checks.
# Only replace the previous deliverable after Chrome succeeds with a fresh PDF.
WORK_DIR=$(mktemp -d "$DIR/.one-pager-build.XXXXXX")
trap 'rm -rf "$WORK_DIR"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
TEMP_PDF="$WORK_DIR/render.pdf"

echo "Rendering $HTML -> $PDF"
if ! "$CHROME" --headless --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$TEMP_PDF" "$URI" >"$WORK_DIR/chrome.log" 2>&1; then
  cat "$WORK_DIR/chrome.log" >&2
  fail "Chrome failed; the previous PDF has been preserved."
fi
if [ ! -s "$TEMP_PDF" ] || [ "$(head -c 5 "$TEMP_PDF")" != '%PDF-' ]; then
  cat "$WORK_DIR/chrome.log" >&2
  fail "Chrome did not produce a nonempty PDF; the previous PDF has been preserved."
fi
mv "$TEMP_PDF" "$PDF"

# Page-count tools are optional. Missing metadata still requires manual review.
PAGES=""
if command -v pdfinfo >/dev/null 2>&1; then
  PAGES=$(LC_ALL=C pdfinfo "$PDF" 2>/dev/null | awk '/^Pages:/ {print $2}') || PAGES=""
fi
if ! [[ "$PAGES" =~ ^[1-9][0-9]*$ ]] && command -v mdls >/dev/null 2>&1; then
  PAGES=$(mdls -raw -name kMDItemNumberOfPages "$PDF" 2>/dev/null) || PAGES=""
fi
if [[ "$PAGES" =~ ^[1-9][0-9]*$ ]]; then
  echo "Pages: $PAGES"
  if [ "$PAGES" != "1" ]; then
    echo "WARNING: PDF is $PAGES pages. Tighten copy before sending." >&2
  fi
else
  echo "WARNING: Could not determine PDF page count. Open the PDF and verify one page." >&2
fi

# Optional gstack preview. A screenshot failure does not invalidate the PDF.
B="${BROWSE_BIN:-$HOME/.claude/skills/gstack/browse/dist/browse}"
if [ -x "$B" ]; then
  if "$B" goto "$URI" >"$WORK_DIR/browse.log" 2>&1 \
      && "$B" viewport 850x1100 >>"$WORK_DIR/browse.log" 2>&1 \
      && "$B" screenshot "$WORK_DIR/preview.png" >>"$WORK_DIR/browse.log" 2>&1 \
      && [ -s "$WORK_DIR/preview.png" ] \
      && mv "$WORK_DIR/preview.png" "$PNG"; then
    echo "Screenshot: $PNG"
  else
    cat "$WORK_DIR/browse.log" >&2
    echo "WARNING: Optional screenshot failed. Open the PDF to review it." >&2
  fi
fi

echo "Done. Open $PDF to review."
