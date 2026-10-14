---
name: task-triage
description: Size the setup to the task before starting any build, code, data or document task, so work is never over- or under-engineered. Scores Complexity and Impact from 1 to 100, then sets plan depth, number of agents, their roles and how much review/QA the result needs. Use at the start of every non-trivial task, when the user says "triage this", "how big is this", "how many agents", "do we need a plan", and in every QA or review pass to check that the review depth matches the triage.
---

# Task Triage

Do the least setup that is safe. Two scores, 1 to 100, control different things:

- **Complexity** decides **planning depth and number of agents**.
- **Impact** decides **review and verification depth**.

A one-line pricing claim fix is low complexity, high impact: no plan, no parallel agents, careful review. A single combined score would get that wrong.

## Step 1: Score (5 factors, 0 to 20 each, sum)

| Complexity factor | 0 | 10 | 20 |
|---|---|---|---|
| Files / systems touched | 1 file | a few files, 1 system | many files or several systems |
| Approach certainty | obvious | 2 to 3 options | unknown, needs research |
| Familiarity with the code | well known | partly | never opened |
| Coupling | isolated | some shared code | shared CSS / schema / data model |
| How hard to verify | a script says pass/fail | needs a manual look | no good check exists |

| Impact factor | 0 | 10 | 20 |
|---|---|---|---|
| Who sees it | only the user | internal team | customers, investors, public |
| Reversibility | one-click revert | revert plus cleanup | can't undo (sent, deleted, published) |
| Sensitive data | none | business data | PHI, money, legal |
| Public claims | none | wording | product claims, numbers, pricing |
| Cost of a bug | annoying | lost time or a lead | lost deal, compliance, trust |

## Step 2: Pick the setup

| Complexity | Planning | Agents and roles |
|---|---|---|
| **1 to 20** | None. Just do it | 1 builder |
| **21 to 45** | Plan mode, plan stays in chat | 1 agent (architect + builder) |
| **46 to 70** | Plan written to `plans/<task>.md` | 1 builder (+1 read-only explore subagent if the code is unfamiliar). 2 builders only if slices share no files |
| **71 to 100** | Written plan + Codex plan critique. Over 85: split into smaller tasks first | Architect, plan critic, 2 to 3 builders in separate worktrees, one PR each |

| Impact | Review and QA |
|---|---|
| **1 to 20** | Automated checks only (tests, gates, scripts) |
| **21 to 45** | Checks + user skims the diff |
| **46 to 70** | Checks + Codex `review` (findings only, each verified before fixing) + user reads the diff |
| **71 to 100** | Checks + Codex `adversarial-review` + user reads the full diff + see it running (preview) + a written rollback step |

## Step 3: State it in one line before starting

```
Triage: C 35 / I 60 → plan in chat, 1 agent, Codex review + diff read.
```

Show the factor scores only if the user asks or the call is close to a boundary.

## Rules

1. **When unsure, pick the lower tier.** Escalate one tier if the agent fails twice on the same thing.
2. **Never more than 3 builders**, whatever the score. Human review time is the limit.
3. **A task with an existing skill drops one complexity tier.** The skill is the plan.
4. **Re-triage if scope changes** mid-task (new files, new system, now customer-facing).
5. **Impact never drops for convenience.** A small diff to public claims, PHI or money stays high impact.

## QA: check the triage was honored

Every QA or review pass (codex-review, review-pr, verify-site, fact-check, final check before delivery) starts here:

1. **Find the triage line.** If there is none, score the task now and say so.
2. **Re-score Impact from the actual diff/output**, not the plan. If the real impact is higher (e.g. it ended up touching pricing copy or PHI), raise the review tier before signing off.
3. **Check review depth matches the Impact tier.** Missing steps (no Codex review at 46+, no adversarial review or rollback step at 71+, no preview check at 71+) are QA findings. Do the missing step, don't just report it.
4. **Flag overengineering too.** A plan file, extra agents or a Codex review on a 1 to 20 task is a finding: note it for next time.
5. **End the QA report with:** `Triage check: planned C x / I y, actual I z, review tier met: yes/no`.

## Worked examples (estimates, adjust with use)

| Task | C | I | Run |
|---|---|---|---|
| Feature touching PHI | 75 | 90 | Split first; written plan + Codex critique; 2 builders; adversarial review; full diff read; rollback plan |
| Investor report numbers | 35 | 85 | Plan in chat, 1 agent; every number traced to source; adversarial review; user reads everything |
| Bulk CRM / outreach update | 30 | 80 | Plan in chat, 1 agent; dry run on 5 records first; Codex review of the script |
| New web page with JS | 60 | 55 | Written plan; 1 builder; checks + Codex review; preview check |
| Site-wide markup sweep (500 files) | 65 | 50 | Written plan; `/batch` or 2 to 3 builders by folder; checks; Codex reviews a sample |
| Glossary entry with a skill | 15 | 30 | Run the skill, 1 agent; checks; skim diff |
| Research spike, code thrown away | 40 | 5 | Plan in chat; 1 agent in a worktree; no review |
| Typo or copy tweak | 5 | 10 | Just do it; checks |

## How heavy each run is (rough, unmeasured)

| Run | Sessions | User time |
|---|---|---|
| Just do it | 1 | 2 to 5 min |
| Plan in chat, 1 agent | 1 | 10 to 20 min |
| Written plan, 1 builder, Codex review | 2 to 3 | 30 to 60 min |
| Full pipeline, 2 to 3 builders | 4 to 6 | 1.5 to 3 hrs over a day |

Background and sources: `research.md` in this folder.
