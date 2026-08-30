#!/usr/bin/env bash
# Symlink every skill in this repo into ~/.claude/skills/
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.claude/skills"
mkdir -p "$DEST"
for d in "$REPO"/*/; do
  name="$(basename "$d")"
  [ -f "${d}SKILL.md" ] || continue
  ln -sfn "${d%/}" "$DEST/$name"
  echo "linked $name"
done
