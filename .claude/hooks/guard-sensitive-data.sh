#!/usr/bin/env bash
# guard-sensitive-data.sh — PreToolUse(Bash) guard for jpstack.
#
# jpstack is a PUBLIC repository. This hook refuses any `git commit` or `git push`
# that carries financial, tax or personally-identifying data into it.
#
# It reads the Claude Code hook payload on stdin and inspects what is actually about
# to be written — staged content for a commit, the unpushed range for a push — not
# the whole working tree.
#
# Three checks, all deterministic:
#   1. FILE PATHS that are financial records by construction (databases, receipt
#      vaults, CPA exports, bank downloads).
#   2. CONTENT patterns that are unambiguous PII (SSN, EIN, card PAN, routing and
#      account numbers).
#   3. A LOCAL DENYLIST of real names and strings — .claude/private-terms.txt,
#      gitignored, never published. Add a contractor's name there once and it can
#      never be committed again.
#
# What this hook CANNOT catch: a real payee name paired with a real amount, written
# as ordinary prose. Regex does not know which names are real. That judgment lives in
# CLAUDE.md, which says placeholders only — this hook is the backstop, not the rule.
#
# Exit 0 with no output = allow. Deny is returned as PreToolUse JSON.
set -uo pipefail

payload=$(cat)
cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command // ""' 2>/dev/null) || exit 0

# Only gate the two commands that actually publish. Everything else passes untouched.
printf '%s' "$cmd" | grep -Eq '(^|[;&|[:space:]])git([[:space:]]+-[^[:space:]]+([[:space:]]+[^[:space:]]+)?)*[[:space:]]+(commit|push)([[:space:]]|$)' || exit 0

cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0

is_push=0
printf '%s' "$cmd" | grep -Eq '[[:space:]]push([[:space:]]|$)' && is_push=1

# ── what is about to be published ────────────────────────────────────────────────
if [ "$is_push" -eq 1 ]; then
  range=""
  if upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null); then
    range="$upstream..HEAD"
  else
    for base in origin/main origin/master; do
      git rev-parse --verify "$base" >/dev/null 2>&1 && { range="$base..HEAD"; break; }
    done
  fi
  # No resolvable base (a brand-new branch with no remote): inspect the whole tree.
  if [ -n "$range" ]; then
    names=$(git diff --name-only "$range" 2>/dev/null)
    added=$(git diff "$range" 2>/dev/null | grep '^+' | grep -v '^+++')
  else
    names=$(git ls-files)
    added=$(git ls-files -z | xargs -0 cat 2>/dev/null)
  fi
else
  names=$(git diff --cached --name-only 2>/dev/null)
  added=$(git diff --cached 2>/dev/null | grep '^+' | grep -v '^+++')
fi

[ -z "$names$added" ] && exit 0

hits=""
note() { hits="${hits}  - $1"$'\n'; }

# ── 1. file paths that are financial records by construction ─────────────────────
bad_paths=$(printf '%s\n' "$names" | grep -Ei \
  -e '\.(db|sqlite|sqlite3|ofx|qfx|qbo)$' \
  -e '(^|/)receipts?/' \
  -e '(^|/)cpa[-_][^/]*/' \
  -e '(1099|w-?9|w-?2|schedule-?c|expenses|deductions|payees|estimated-payments)[^/]*\.csv$' \
  -e '(^|/)(tax[-_ ]?return|tax[-_ ]?doc|1099|w-?9|w-?2|bank[-_ ]?statement|payslip|paystub)[^/]*\.(pdf|csv|xlsx?|docx?|png|jpe?g|heic)$' || true)
if [ -n "$bad_paths" ]; then
  while IFS= read -r p; do [ -n "$p" ] && note "financial record file: $p"; done <<<"$bad_paths"
fi

# ── 2. unambiguous PII in added lines ────────────────────────────────────────────
scan() { # <label> <extended-regex>
  printf '%s\n' "$added" | grep -Eqi -- "$2" && note "$1"
}
# SSN, ignoring all-same-digit placeholders (000-00-0000, 111-11-1111) so the
# documented fake values do not block every commit.
if printf '%s\n' "$added" \
    | grep -Eo '[0-9]{3}-[0-9]{2}-[0-9]{4}' \
    | tr -d '-' \
    | grep -Evq '^(.)\1{8}$' 2>/dev/null; then
  note "US Social Security number"
fi
scan "EIN (employer identification number)" '(ein|tax ?id|tin)[^0-9]{0,12}[0-9]{2}-[0-9]{7}'
scan "bank routing/account number"          '(routing|account)[ _-]?(number|no\.?|#)[^0-9]{0,12}[0-9]{6,17}'
scan "payment card number"                  '(^|[^0-9])(4[0-9]{12}([0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(011|5[0-9]{2})[0-9]{12})([^0-9]|$)'
scan "IBAN"                                 'iban[^A-Z0-9]{0,8}[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}'

# ── 3. local denylist of real names/strings (gitignored, never published) ────────
deny_file=".claude/private-terms.txt"
if [ -f "$deny_file" ]; then
  while IFS= read -r term; do
    case "$term" in ''|'#'*) continue ;; esac
    if printf '%s\n%s\n' "$names" "$added" | grep -Fqi -- "$term"; then
      note "denylisted private term (see $deny_file)"
    fi
  done < "$deny_file"
fi

[ -z "$hits" ] && exit 0

what=$([ "$is_push" -eq 1 ] && echo "push" || echo "commit")
reason="BLOCKED: this git $what carries financial/tax/PII data into a PUBLIC repository.

Found:
${hits}
jpstack is public. Financial and tax data must never be published here.
Keep it local (the deduction database and its receipt vault are gitignored for
this reason), or put it in a PRIVATE repository — never this one.

If this is a placeholder or an example and the match is wrong, use an obviously
fake value (Example Contractor, ABC123, 000-00-0000). Do not bypass the guard to
publish real data."

jq -n --arg r "$reason" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: $r
  },
  systemMessage: $r
}'
exit 0
