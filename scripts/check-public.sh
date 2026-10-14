#!/bin/bash
# Blocks confidential content from reaching this PUBLIC repo.
# Runs as a git pre-push hook (install: ln -s ../../scripts/check-public.sh .git/hooks/pre-push)
# and can be run by hand. Checks the files tracked in HEAD.
#
# Confidential names (investors, customers, prospects, people) are NOT listed here,
# since this file is public. Put them one per line in ./private-terms.txt (gitignored).
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
fail=0

# 1. Skills that must only live in the private repo
PRIVATE_SKILLS="contract-review baa-review title-agency-calculator title-closing-review
real-estate-closing-check construction-draw-package buy-vs-build-underwriter
property-investment-analyzer property-appraisal-co jpm-equities-pm client-welcome-email
detecting-medical-groups proposal-personalizer offer-letter investor-report pricing-coach
sow-builder business-case-builder solum-business-case post-call precall-brief auth-tracker
waalaxy-prospecting cfo-review tax-deductions"
for s in $PRIVATE_SKILLS; do
  if git ls-tree -d --name-only HEAD "$s" | grep -q .; then
    echo "BLOCKED: private skill '$s' is in the public repo"; fail=1
  fi
done

# 2. Secrets and confidential patterns
check() {
  local label="$1" pattern="$2" hits
  hits=$(git grep -I -n -i -E -e "$pattern" HEAD -- . ':!scripts/check-public.sh' 2>/dev/null | head -5)
  if [ -n "$hits" ]; then echo "BLOCKED: $label"; echo "$hits" | sed 's/^/    /'; fail=1; fi
}
check "API key or token" '(sk-[A-Za-z0-9_-]{20,}|sk-ant-|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|github_pat_|xox[bap]-|AIza[0-9A-Za-z_-]{30}|pat-na1-)'
check "Investor list" '(investors?|backed by)[^a-z]{0,3}(:|include|are)'
check "Internal financials" '\b(ARR|MRR)\b[^a-z]{0,5}\$?[0-9]|burn (rate )?(of|was|is|moved)[^.]{0,20}\$[0-9]|runway[^.]{0,15}[0-9]+ months'
check "Pricing / rate card" '\$[0-9.,]+ ?/ ?(mo|month|unit|auth|check)\b'

# 3. Local confidential term list
if [ -f private-terms.txt ]; then
  while IFS= read -r term; do
    [ -z "$term" ] && continue; case "$term" in \#*) continue;; esac
    hits=$(git grep -I -n -i -w -F -e "$term" HEAD -- . ':!scripts/check-public.sh' 2>/dev/null | head -3)
    if [ -n "$hits" ]; then echo "BLOCKED: private term"; echo "$hits" | sed 's/^/    /'; fail=1; fi
  done < private-terms.txt
else
  echo "WARNING: private-terms.txt not found; only generic patterns were checked"
fi

[ $fail -eq 0 ] && echo "check-public: OK" || echo "check-public: FAILED. Nothing confidential may be pushed to this public repo."
exit $fail
