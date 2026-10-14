# Multi-agent coding with Claude + Codex: best practices (research, 2026-10-13)

Question: how should multiple agents (Claude, Codex) work on each other's output, with plan mode always in the loop? What roles, what flow, what cadence?

Sources are listed at the bottom with IDs [S1]..[S9]. Anything not backed by a source is labeled ASSUMPTION.

---

## 1. What the sources agree on

| # | Practice | Who says it |
|---|---|---|
| 1 | **Plan first, and write the plan to a file.** A plan on disk survives crashed sessions, can be reviewed before code exists, and lets a different (even cheaper) agent implement it. Quality bar: an agent with no access to the planning chat can implement it. | S2, S5, S7 |
| 2 | **Skip planning for small changes.** "If you could describe the diff in one sentence, skip the plan." Plan when the approach is uncertain, many files change, or the code is unfamiliar. | S1 |
| 3 | **Verification is the biggest quality lever.** Give the agent a check it can run (tests, build, linter, screenshot). Boris Cherny: this "will 2-3x the quality of the final result." Strongest form is a Stop hook that blocks the turn until the check passes. | S1, S2 |
| 4 | **One writer per workspace.** Parallel agents each get their own git worktree. If they share a checkout, partition files so no two agents own the same file. | S1, S3, S5, S7 |
| 5 | **Writes stay single-threaded; extra agents add intelligence, not actions.** Cognition (makers of Devin) moved from "don't build multi-agents" to this rule: multi-agent works when only one agent writes at a time per thread of work, and the others review, research or critique. | S8 |
| 6 | **Delegation needs a full brief.** Each sub-agent needs an objective, output format, tools to use, and a clear boundary ("don't do X, that's another agent's job"). Vague briefs caused duplicated work and gaps in Anthropic's own system. | S6 |
| 7 | **Fresh context beats long context.** Use a fresh session for the implementer of each chunk; `/clear` between unrelated tasks; after 2 failed corrections, clear and re-prompt with what you learned. | S1, S7 |
| 8 | **Human review is the real bottleneck.** Willison: parallel agents only help if you can review the output; code that started from your own spec is much cheaper to review. | S4 |
| 9 | **CLAUDE.md is short and grows from mistakes.** Add a line every time the agent errs; delete any line whose removal wouldn't cause a mistake; convert rules into hooks where possible. One Codex user found Codex silently stopped reading a 70 KB AGENTS.md partway through. | S1, S2, S9 |
| 10 | **Share one instruction file across tools.** Codex reads `AGENTS.md`, Claude reads `CLAUDE.md`; point one at the other (e.g. `@AGENTS.md` inside CLAUDE.md). | S9 |

## 2. The surprising finding: cross-model review is not free

A July 2026 controlled study (116 LiveCodeBench problems, Claude Opus 4.7 and Codex GPT-5.5) [S10]:

| Setup | Pass rate | Change vs writer alone |
|---|---|---|
| Claude alone | 91.4% | baseline |
| Claude writes, Claude reviews | 91.4% | 0 |
| **Claude writes, Codex reviews** | **82.8%** | **-8.6 pts** (broke 13 correct solutions, fixed 3) |
| Codex alone | 71.6% | baseline |
| Codex writes, Claude reviews | 89.7% | +18.1 pts |
| Codex writes, Codex reviews | 84.5% | +12.9 pts |

Paper's recommendation: review Codex drafts (Claude as reviewer when accuracy matters); a strong Claude draft did best submitted as is.

**Caveat (important):** in that study the reviewer rewrote the program and could not run tests. In a real repo the reviewer only *reports findings*, and the writer *verifies each finding against code and tests* before fixing. That is exactly the guard that stops a reviewer from breaking correct code. Takeaway: let Codex review, never let a review auto-apply. Your `codex-review` skill already does "verify every finding before fixing", which is the right design.

## 3. Recommended setup for you

### Roles

| Role | Agent | Plan mode | Writes code? |
|---|---|---|---|
| Architect | Main Claude session + JP | Always | No. Writes `plans/<task>.md` |
| Plan critic | Codex, adversarial | n/a | No. Comments on the plan |
| Builder (1 per slice) | Fresh Claude session or subagent, own worktree | Reads the plan; no re-planning | Yes, only its slice |
| Code reviewer | Codex (`codex-review`) | n/a | No. Findings only |
| Verifier | Scripts: tests, 3 gates, `review_pr_checks.py` via hook | n/a | No |
| Merger | JP | n/a | No. Reads diff, merges |

Why the plan critic is Codex and plan mode sits at the top: correcting a plan is cheaper than correcting a diff [S5], and a critic adds intelligence without adding a second writer [S8]. ASSUMPTION: the S10 regression effect is smaller on plans than on code, since a plan critique gets judged by the architect, not applied blindly.

### Flow for one task

1. JP writes a 1-paragraph spec: goal, done-when, out of scope.
2. Size check: one-sentence diff? Skip to step 5 with a single agent [S1].
3. Architect (plan mode) writes `plans/<task>.md`: slices with no shared files, each with its own verify command.
4. Codex critiques the plan; architect verifies each point, revises; JP approves.
5. Builders run in parallel worktrees, each with a full brief (objective, files, verify command, boundary) [S6]. Rule from S7: do the first few steps, stop if confused, do not deviate from the plan.
6. Builder runs the verify command until green (hook enforced) [S1, S2].
7. Codex reviews each diff; builder verifies findings against code/tests before changing anything [S10 caveat].
8. JP reads the diff and merges, one branch at a time.
9. Any mistake becomes a CLAUDE.md line or, better, a script check [S2].

Escape hatch: 2 failed attempts on the same problem, clear and re-prompt, or hand to `/codex:rescue` [S1].

### Cadence

| When | What | Time |
|---|---|---|
| Morning | Specs + plans for 2-3 tasks (planning in sequence) | 30 min |
| Day | Builders run in parallel; JP checks in on notifications [S2] | async |
| Afternoon | Review diffs, merge, record lessons | 30-45 min |
| Friday | Retro; prune CLAUDE.md; rerun skill evals | 30 min |

Limits: 3-5 parallel builders max. Boris Cherny runs 5 local plus 5-10 web sessions [S2], but he reviews code full time; Willison says he can only review and land one significant change at a time [S4]. ASSUMPTION: as a CEO with limited review time, 2-3 builders is your realistic ceiling.

Good parallel work that needs little review [S4]: research spikes, proofs of concept, "send out a scout" runs whose code you throw away, small maintenance (warnings, deprecations).

## 4. Setup actions (in order)

1. `.claude/settings.json` per repo: `"permissions": {"defaultMode": "plan"}` (or launch with `claude --permission-mode plan`) [S1].
2. Stop hook or pre-commit hook running the 3 landing-page gates [S1].
3. One instructions file: `AGENTS.md` as source, `CLAUDE.md` containing `@AGENTS.md` [S9]. Keep it short [S1, S9].
4. `plans/` folder convention per repo; plans are committed.
5. A `/ship-task` skill in jpstack that runs steps 3-8.

## 5. Triage: size the setup to the task (avoid overengineering)

Every task gets two scores, 1 to 100. They control different things:

- **Complexity** decides **how much planning and how many agents.**
- **Impact** decides **how much review and verification.**

A one-line pricing claim fix is low complexity but high impact: it needs no plan and no parallel agents, but it does need careful review. Using a single combined score would get that wrong.

### Scoring (5 factors, 0 to 20 each, add them up)

| Complexity factor | 0 | 10 | 20 |
|---|---|---|---|
| Files / systems touched | 1 file | a few files, 1 system | many files or several systems |
| Approach certainty | obvious | 2 to 3 options | unknown, needs research |
| Familiarity with the code | well known | partly | never opened |
| Coupling | isolated | some shared code | shared CSS / schema / data model |
| How hard to verify | a script says pass/fail | needs a manual look | no good check exists |

| Impact factor | 0 | 10 | 20 |
|---|---|---|---|
| Who sees it | only you | internal team | customers, investors, public |
| Reversibility | one-click revert | revert plus cleanup | can't undo (sent, deleted, published) |
| Sensitive data | none | business data | PHI, money, legal |
| Public claims | none | wording | product claims, numbers, pricing |
| Cost of a bug | annoying | lost time or a lead | lost deal, compliance, trust |

### What each score turns on

| Complexity | Planning | Agents | Roles |
|---|---|---|---|
| **1 to 20** | None. Just do it | 1 | Builder |
| **21 to 45** | Plan mode, plan stays in chat | 1 | Architect + builder (same session) |
| **46 to 70** | Plan written to `plans/<task>.md` | 1 builder (+1 read-only explore subagent if the code is unfamiliar). 2 builders only if slices share no files | Architect, builder(s) |
| **71 to 100** | Written plan + Codex plan critique. Over 85: first split into smaller tasks | 2 to 3 builders in worktrees, one PR each | Architect, plan critic, builders |

| Impact | Verification and review |
|---|---|
| **1 to 20** | Automated checks only (tests, gates) |
| **21 to 45** | Checks + JP skims the diff |
| **46 to 70** | Checks + Codex review (findings only, each verified before fixing) + JP reads the diff |
| **71 to 100** | Checks + adversarial Codex review + JP reads the full diff + see it running (preview) + a written rollback step |

### Rules

1. **State the triage in one line before starting**, e.g. `Triage: C 35 / I 60 → plan in chat, 1 agent, Codex review.`
2. **When unsure, pick the lower tier.** Escalate one tier if the agent fails twice on the same thing.
3. **Never more than 3 builders**, whatever the score (review time is the limit, see S4).
4. **Repeated tasks with a skill** (e.g. `add-glossary-entry`) drop one complexity tier: the skill is the plan.

### Ranking: worked examples (ASSUMPTION: scores are my estimates, adjust as you use it)

| Rank | Task | C | I | Run |
|---|---|---|---|---|
| 1 | Prior-auth tool: feature that touches PHI | 75 | 90 | Split first; written plan + Codex critique; 2 builders; adversarial review; full diff read; rollback plan |
| 2 | Investor report numbers | 35 | 85 | Plan in chat, 1 agent; every number traced; adversarial review; you read everything |
| 3 | Bulk HubSpot / Instantly update | 30 | 80 | Plan in chat, 1 agent; dry run on 5 records first; Codex review of the script |
| 4 | New landing-page tool page with JS | 60 | 55 | Written plan; 1 builder; gates + Codex review; preview check |
| 5 | Homepage section redesign | 45 | 60 | Plan in chat; 1 agent; gates + Codex review; check all 3 pages that load home.css |
| 6 | Site-wide markup sweep (500 files) | 65 | 50 | Written plan; `/batch` or 2 to 3 builders by folder; gates; Codex reviews a sample |
| 7 | New glossary entry (has a skill) | 15 after skill drop | 30 | Run the skill, 1 agent; gates; skim diff |
| 8 | Research spike / proof of concept, code thrown away | 40 | 5 | Plan in chat; 1 agent in a worktree; no review |
| 9 | Typo or copy tweak | 5 | 10 | Just do it; gates |

### How heavy each run is

| Run | Sessions | Your time |
|---|---|---|
| Just do it | 1 | 2 to 5 min |
| Plan in chat, 1 agent | 1 | 10 to 20 min |
| Written plan, 1 builder, Codex review | 2 to 3 | 30 to 60 min |
| Full pipeline, 2 to 3 builders | 4 to 6 | 1.5 to 3 hrs over a day |

ASSUMPTION: times are rough estimates, not measured. Track a few real runs and correct them.

## 6. Not verified

- Alexandr Wang: no public source found describing a personal coding-agent workflow. Not included.
- Exact Codex MCP-server command: check `codex --help` locally before wiring it.

## Sources

| ID | Source | URL |
|---|---|---|
| S1 | Claude Code docs, Best practices | https://code.claude.com/docs/en/best-practices |
| S2 | Boris Cherny (creator of Claude Code), setup thread, Jan 2, 2026 (gist copy) | https://gist.github.com/eldermoraes/9bc426c67410081e1881b1b5127764b5 |
| S3 | Claude Code docs, Run agents in parallel | https://code.claude.com/docs/en/agents |
| S4 | Simon Willison, Embracing the parallel coding agent lifestyle, Oct 2025 | https://simonwillison.net/2025/Oct/5/parallel-coding-agents/ |
| S5 | Villoro, A multi-agent setup that learns | https://villoro.com/blog/multi-agent-setup/ |
| S6 | Anthropic, How we built our multi-agent research system | https://www.anthropic.com/engineering/multi-agent-research-system |
| S7 | Jesse Vincent, How I'm using coding agents in September 2025 | https://blog.fsck.com/2025/10/05/how-im-using-coding-agents-in-september-2025/ |
| S8 | Cognition, Multi-agents: what's actually working | https://cognition.com/blog/multi-agents-working |
| S9 | Rafferty Uy, Claude Code, Copilot & Codex cross-compatibility | https://raffertyuy.com/raztype/claude-copilot-codex-cross-compatibility/ |
| S10 | arXiv 2607.21656, Cross-model LLM code review | https://arxiv.org/html/2607.21656v1 |
