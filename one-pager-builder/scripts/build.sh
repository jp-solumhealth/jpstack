#!/bin/bash
# Build one-pager PDF + screenshot from filled HTML.
# Usage: build.sh <html-file-path>
# Assumes the HTML sits in the final output folder with logo-solumhealth-dark.svg
# and client-logos/ already in place.

set -e

HTML="${1:?Usage: build.sh <html-file-path>}"
DIR=$(dirname "$HTML")
BASE=$(basename "$HTML" .html)
PDF="$DIR/$BASE.pdf"
PNG="/tmp/$BASE-preview.png"

if [ ! -f "$HTML" ]; then
  echo "HTML file not found: $HTML"
  exit 1
fi

echo "Rendering $HTML -> $PDF"

"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless \
  --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf="$PDF" \
  "file://$HTML" 2>&1 | tail -1

PAGES=$(mdls -name kMDItemNumberOfPages "$PDF" | awk -F'= ' '{print $2}')
echo "Pages: $PAGES"

if [ "$PAGES" != "1" ]; then
  echo "WARNING: PDF is $PAGES pages. Tighten copy before sending."
fi

# Optional screenshot via gstack if available
if [ -x "$HOME/.claude/skills/gstack/browse/dist/browse" ]; then
  B="$HOME/.claude/skills/gstack/browse/dist/browse"
  $B goto "file://$HTML" >/dev/null 2>&1
  $B viewport 850x1100 >/dev/null 2>&1
  $B screenshot "$PNG" >/dev/null 2>&1
  echo "Screenshot: $PNG"
fi

echo "Done. Open $PDF to review."
