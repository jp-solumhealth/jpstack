#!/bin/zsh
# Overnight build loop. Runs one fresh headless Claude session per task in TASKS.md.
# Usage: run-night.sh <project-dir>
# Stop it gracefully any time with: touch <project-dir>/.night/STOP

set -u

PROJECT="${1:?usage: run-night.sh <project-dir>}"
cd "$PROJECT" || exit 1

MAX_ITERS="${MAX_ITERS:-40}"            # hard cap on sessions per night
MAX_TURNS="${MAX_TURNS:-80}"            # cap per task
MODEL="${MODEL:-sonnet}"                # builders run on Sonnet
PERMISSION_MODE="${PERMISSION_MODE:-auto}"
LIMIT_SLEEP="${LIMIT_SLEEP:-1800}"      # wait for usage window reset after a failed run
MAX_FAILS="${MAX_FAILS:-4}"             # consecutive failed runs before giving up
MAX_STALLS="${MAX_STALLS:-3}"           # consecutive runs with no commit and no task change

NIGHT=".night"
LOGS="$NIGHT/logs"
mkdir -p "$LOGS"

# One loop per project
if [[ -f "$NIGHT/lock" ]] && kill -0 "$(cat $NIGHT/lock)" 2>/dev/null; then
  echo "Already running (pid $(cat $NIGHT/lock))"; exit 1
fi
echo $$ > "$NIGHT/lock"
rm -f "$NIGHT/STOP"
trap 'rm -f "$NIGHT/lock"' EXIT

for f in SPEC.md TASKS.md NIGHT.md PROGRESS.md; do
  [[ -f "$f" ]] || { echo "Missing $f. Run /night-build setup first."; exit 1; }
done
git rev-parse --git-dir >/dev/null 2>&1 || { echo "Not a git repo"; exit 1; }
claude auth status 2>/dev/null | grep -q '"loggedIn": true' || { echo "Claude CLI not logged in. Run: claude auth login"; exit 1; }

PROMPT='You are one shift of an unattended overnight build. Nobody is awake to answer questions.
Read NIGHT.md (rules), SPEC.md (what we are building), TASKS.md (the queue) and the last 40 lines of PROGRESS.md.
Do the FIRST task in TASKS.md marked "- [ ]" and nothing else.
1. Write or update tests for the task first.
2. Build it.
3. Run the checks listed in NIGHT.md. All must pass.
4. If green: change that task to "- [x]", append a short entry to PROGRESS.md (task, what you did, files touched, anything the next shift should know), then git add and git commit.
5. If you cannot get it green after 2 real attempts: revert your code changes (git checkout/clean only files you created or changed), change the task to "- [!]" with a one-line reason, log it in PROGRESS.md, commit only TASKS.md and PROGRESS.md, and stop.
Never ask questions, never push, never deploy, never touch .env files or production credentials.'

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$NIGHT/night.log"; }
status() { echo "$*" > "$NIGHT/status"; }

fails=0; stalls=0
log "Night build started on branch $(git branch --show-current)"

for i in $(seq 1 "$MAX_ITERS"); do
  [[ -f "$NIGHT/STOP" ]] && { log "STOP file found, ending"; break; }
  task=$(grep -m1 '^- \[ \]' TASKS.md)
  [[ -z "$task" ]] && { log "No open tasks left, done"; break; }

  before_head=$(git rev-parse HEAD 2>/dev/null || echo none)
  before_tasks=$(md5 -q TASKS.md)
  status "running $i/$MAX_ITERS: $task"
  log "Run $i: $task"

  claude -p "$PROMPT" \
    --model "$MODEL" \
    --max-turns "$MAX_TURNS" \
    --permission-mode "$PERMISSION_MODE" \
    --disallowedTools "Bash(git push:*)" "Bash(vercel:*)" "Bash(npx vercel:*)" "Bash(supabase db push:*)" "Bash(rm -rf /*)" \
    < /dev/null > "$LOGS/run-$(printf %02d $i).log" 2>&1
  rc=$?

  if (( rc != 0 )); then
    grep -q "Failed to authenticate" "$LOGS/run-$(printf %02d $i).log" && { log "Claude CLI login expired, ending. Run: claude auth login"; break; }
    fails=$((fails + 1))
    log "Run $i failed (exit $rc), likely a usage limit. Fail $fails/$MAX_FAILS"
    (( fails >= MAX_FAILS )) && { log "Too many failures, ending"; break; }
    status "sleeping ${LIMIT_SLEEP}s after failure"
    sleep "$LIMIT_SLEEP"
    continue
  fi
  fails=0

  if [[ "$(git rev-parse HEAD)" == "$before_head" && "$(md5 -q TASKS.md)" == "$before_tasks" ]]; then
    stalls=$((stalls + 1))
    log "Run $i made no progress. Stall $stalls/$MAX_STALLS"
    (( stalls >= MAX_STALLS )) && { log "Stalled, ending"; break; }
  else
    stalls=0
  fi
  sleep 20
done

done_n=$(grep -c '^- \[x\]' TASKS.md); open_n=$(grep -c '^- \[ \]' TASKS.md); blocked_n=$(grep -c '^- \[!\]' TASKS.md)
summary="Night build finished: $done_n done, $open_n open, $blocked_n blocked"
log "$summary"
status "finished: $summary"
osascript -e "display notification \"$summary\" with title \"Night build\"" 2>/dev/null
