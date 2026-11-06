---
name: night-build
description: Set up and launch an unattended overnight build of a platform or app. Plans the work with JP (SPEC.md, TASKS.md, NIGHT.md, PROGRESS.md on an overnight branch), then starts a loop that runs one fresh Sonnet session per task, gated by tests, and commits each finished task. Also checks status, stops the run, and gives the morning report. Use when JP says "night build", "build this overnight", "leave it running tonight", "start the night run", "night production", "how did the night go", "night report", or "stop the night build".
---

# Night Build

Many short sessions, not one long one. Each shift does one task, runs the checks, commits only if green, and exits. The files carry the progress: `SPEC.md` (what), `TASKS.md` (queue), `NIGHT.md` (rules and checks), `PROGRESS.md` (log). The loop script is `run-night.sh` next to this file.

Pick the mode from what JP said: **setup + launch** (default), **status**, **stop**, or **morning report**.

## Mode 1: Setup + launch

### Step 1: Restate and confirm (one message)
Restate the deliverable in one sentence plus: project folder, stack, and what "done tonight" means. If the project folder or the core idea is missing, ask once. Otherwise recommend defaults and go:
- Folder: an existing Project Index folder, or a new one under `~/Documents/Claude/` (ask before creating a new top-level folder).
- Stack default: Next.js + TypeScript + Tailwind + Supabase (local or test project), Vitest for tests, Playwright only if UI flows matter.

### Step 2: Write the four files in the project root
Planning is the high-value part, so do it here in the main session, not in the loop.

**SPEC.md**: product in 3 lines, users, stack, data model, pages/endpoints, out of scope, and a "done" definition.

**TASKS.md**: the queue, ordered so each task builds on the previous. Rules:
- Each task is 30 to 60 minutes of work for one session, one line, `- [ ] <Area>: <outcome you can test>`.
- Task 1 is always the scaffold: repo, stack, test runner, lint, typecheck, and one passing smoke test.
- Every ~8 tasks add `- [ ] Cleanup: refactor duplication, fix lint warnings, keep tests green`.
- 15 to 35 tasks for one night. More than that, split across nights.
- No task may need a human decision, an external paid service signup, a production key, a deploy, or sending email/messages.

**NIGHT.md**: the shift rules. Fill in the real check commands for the stack:
```
# Night rules
- One task per shift. Do the first "- [ ]" in TASKS.md only.
- Checks that must all pass before a commit: <e.g. npm run lint && npm run typecheck && npm test>
- Stack and conventions: <short list from SPEC.md>
- Use test/local credentials only (from .env.example or local Supabase). Never read or write .env, never use production keys.
- Never push, deploy, run migrations against a remote database, or send anything outside this machine.
- No new dependencies unless the task needs them; prefer well known packages.
- If something in SPEC.md is ambiguous, pick the simplest reading and note it in PROGRESS.md.
```

**PROGRESS.md**: `# Progress` plus one line with the start date.

Add `.night/` to `.gitignore` (logs, lock, status live there).

### Step 3: Git
- `git init` if needed, commit the four files on the current branch.
- Create and switch to `overnight/<YYYY-MM-DD>`. Refuse to start with uncommitted changes that aren't ours; ask JP.

### Step 4: Show JP the plan, get a yes
Show the task list and the check command. Wait for an explicit go. This is the last human touchpoint of the night.

### Step 5: JP launches it from his own Terminal
Do not start the loop from this session. The session's environment cannot use JP's CLI login, so a loop started here fails on its first run. Create `.night/` (`mkdir -p .night`), then give JP these two commands, each in its own `bash` block, to run in Terminal:
```bash
claude auth status
```
(must show `"loggedIn": true`; if not, `claude auth login` first)
```bash
cd <project> && nohup caffeinate -i zsh ~/.claude/skills/night-build/run-night.sh "$PWD" > .night/nohup.log 2>&1 &
```
When JP says it's started, wait ~60 seconds, then confirm it is alive: `.night/status` says "running 1/..." and `.night/logs/run-01.log` exists. If the status file is missing, read `.night/nohup.log` and `.night/night.log` and tell JP why it stopped. Report to JP:
- the branch, the number of tasks, the log path
- laptop plugged in, lid open (`caffeinate -i` does not stop lid-close sleep unless an external display is attached)
- how to stop: `touch <project>/.night/STOP`

Tunables (env vars before the command): `MAX_ITERS` (40), `MAX_TURNS` (80), `MODEL` (sonnet), `PERMISSION_MODE` (auto), `LIMIT_SLEEP` (1800 seconds to wait after a failed run, usually a usage limit).

## Mode 2: Status
Read `.night/status`, the tail of `.night/night.log`, counts of `[x]`, `[ ]`, `[!]` in TASKS.md, and `git log --oneline overnight/<date> | head`. Three lines max.

## Mode 3: Stop
`touch <project>/.night/STOP`. The current shift finishes its task, then the loop exits. Only kill the process (`kill $(cat .night/lock)`) if JP says stop now.

## Mode 4: Morning report
1. Counts: done / open / blocked, number of commits, hours run (from `.night/night.log`).
2. Each `[!]` task with its reason, and what decision JP needs to make.
3. Run the checks from NIGHT.md once yourself and report the real result.
4. Diff size: `git diff --stat main...HEAD | tail -1` (use the real base branch).
5. Recommend the next step: `/codex-review` on the branch before merging, then requeue blocked tasks with clearer specs for tonight.

Never merge or push the overnight branch without JP's say-so.
