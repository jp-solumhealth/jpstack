---
name: codex-review
description: Get a second-model code review from OpenAI Codex on work Claude wrote, using the codex@openai-codex plugin. Commits a checkpoint first, picks plain vs adversarial review, never co-edits files with a running Codex job, and verifies every Codex finding against the code before fixing anything. Use when the user says "codex review", "have Codex review this", "get a second opinion from Codex", "review before shipping/deploying/merging", "adversarial review", "pressure-test this change", or before any production deploy of code Claude wrote. Also use to review code that Codex wrote (Claude becomes the reviewer).
---

# Codex Review

A cross-model code review. One model writes the code, and the other reviews it. A model reviewing its own work repeats its own blind spots, so this skill never treats self-review as the check.

## Three rules (never skip)

1. **Commit before any handoff to Codex.** A checkpoint commit records exactly what existed before Codex touched anything. Any later change then shows up in `git diff` and can be reverted.
2. **Never edit the same files as a running Codex job.** While Codex works in the background, either work on a different area of the code or wait. If Codex needs to write code, put it on its own git worktree.
3. **Cross-model review only.** Codex reviews code Claude wrote. Claude reviews code Codex wrote (see "Reverse direction" below).

## Requirements

- The `codex@openai-codex` plugin is installed, and `/codex:setup` reports `"ready": true`.
- The project is a git repo.
- Locate the companion script (its folder is versioned, so do not hardcode the version):

```bash
CODEX_COMPANION="$(ls -d ~/.claude/plugins/cache/openai-codex/codex/*/ | sort -V | tail -1)scripts/codex-companion.mjs"
```

If the script is missing or setup is not ready, stop and tell the user to run `/codex:setup`.

## Workflow

### Step 1: Checkpoint

1. Run `git status --short` and `git branch --show-current`.
2. **If there are uncommitted changes:**
   - On a feature branch, commit them with a normal message about the work, and say you did.
   - On `main`/`master`, or on a branch the user hasn't approved, ask before committing. Offer to create a branch first.
   - For a **public repo**, show the file list and get a yes before committing. A commit there is publication.
3. Record the **review base**, the commit the review compares against:
   - On a feature branch, use the default branch (`main`).
   - On `main`, use the last commit before this session's work (e.g. `HEAD~N`, or the SHA from `git log`). Confirm it with the user if unclear.

The plugin's `--base <ref>` reviews everything from the merge-base of `<ref>` and `HEAD` up to `HEAD`, so committed work is fully covered.

### Step 2: Pick the review type

First apply the `task-triage` skill's QA section: re-score Impact from the actual diff. Impact 1 to 20 needs no Codex review (say so and stop); 46 to 70 gets `review`; 71 to 100 gets `adversarial-review`. End the report with the `Triage check:` line.

| Situation | Command | Notes |
|---|---|---|
| Routine change, normal code quality check | `review` | Not steerable; takes no focus text |
| Before a production deploy, or a risky area (auth, data loss, payments, PHI, migrations, retries, race conditions) | `adversarial-review` + focus text | Questions the design itself, not just details |
| Both | Run `review` first, then `adversarial-review` on the riskiest part | |

Focus text must be **specific**. Good examples: "look for race conditions in the webhook handler and question the retry design", "check whether any Supabase query can leak another tenant's rows". Too vague: "find bugs".

### Step 3: Run it

Size the change with `git diff --shortstat <base>...HEAD`. Run 1 or 2 files in the foreground. Run anything larger, or of unclear size, in the background (the plugin's own recommendation, since reviews of changes spanning several files are slow).

```bash
# foreground
node "$CODEX_COMPANION" review --wait --base <base>
node "$CODEX_COMPANION" adversarial-review --wait --base <base> <focus text>

# background: use Bash with run_in_background: true
node "$CODEX_COMPANION" review --background --base <base>
```

While a background review runs, **do not edit files in the reviewed diff** (rule 2). Reviews are read-only, but editing the same files mid-review makes the findings stale. Check progress with `/codex:status` and get the output with `/codex:result`.

### Step 4: Verify every finding

Treat Codex output as **a list of suspicions, not a list of fixes**. For each finding:

1. Open the cited file and line, and read the surrounding code.
2. Classify it:
   - **CONFIRMED**: you can describe the concrete input or state that triggers the failure.
   - **PLAUSIBLE**: it might be real, but needs a test or runtime check to settle.
   - **FALSE POSITIVE**: say why (e.g. "guarded on line 40", "this path is unreachable").
3. Never fix a finding you haven't confirmed.

Report to the user as a table:

| # | File:line | Codex finding | Verdict | Why |
|---|---|---|---|---|

Show the raw Codex output first or link it (`/codex:result`), then the table, so the user can see what Codex actually said versus your judgment.

### Step 5: Fix confirmed issues only

- Ask before fixing unless the user already said "review and fix".
- Fix CONFIRMED issues only. List PLAUSIBLE ones with a suggested check.
- Fixes go in a **separate commit** from the checkpoint, so the review diff and the fix diff stay distinguishable.
- If the fixes are non-trivial, run one more `review --base <checkpoint sha>` on the fix commit only. Stop after that round. Don't loop.

## Reverse direction: Claude reviews Codex's work

When Codex wrote the code (via `/codex:rescue` or the `codex:codex-rescue` agent):

1. Before the rescue, make the checkpoint commit (rule 1). Record its SHA.
2. After Codex finishes, review `git diff <checkpoint sha>` yourself: correctness, scope creep (files Codex touched that it shouldn't have), deleted tests, and weakened assertions.
3. Use the same verdict table. Commit Codex's work only after it passes.

## Cost and usage guardrails

- Codex usage counts against the user's ChatGPT plan limits. Don't review trivial edits (typos, copy changes, config tweaks).
- Don't enable the review gate (`/codex:setup --enable-review-gate`) as part of this skill. The plugin warns it can loop and drain usage. Turning it on is the user's call.
- One adversarial pass per risk area is enough. Don't run the same review twice hoping for different results.
- Codex has none of Claude's connectors (CRM, email, docs). This skill is for code only.

## Quick routine

```
checkpoint commit → review (or adversarial-review on a specific risk) --base <base>
→ verify each finding → fix confirmed only, in a separate commit → ship
```
