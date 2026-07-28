---
name: postmortem
description: Capture and consult lessons from past failures so the same mistake never happens twice. AUTO-TRIGGER (1) before starting any non-trivial task — read INDEX.md and load lessons whose tags match the task; (2) whenever the user expresses frustration, says "this doesn't match", "not the same", "why so long", "this is wrong", "not good", "didn't work", asks for a retry on the same artifact, or any task requires more than 2 iterations to land — write a new lesson. Also trigger on phrases "postmortem", "post mortem", "lessons learned", "what went wrong", "review what happened", "retro for this task". Lessons live at ~/Documents/Claude/Skills/jpstack/postmortem/lessons/ and are indexed in INDEX.md by tag.
---

# Postmortem Skill

A persistent failure log. The whole point: never repeat a mistake.

## Two modes

**READ mode (consult before work).** Before starting any non-trivial task — especially file conversions, design work, API integrations, sales doc generation, anything that touched a sharp edge before — open `INDEX.md`, scan for tags that match the task, and read the matching lesson files. Apply what you learned BEFORE writing code, not after the user pushes back.

**WRITE mode (capture after a struggle).** If the user expressed frustration, the task took multiple iterations, you delivered something wrong before getting it right, or the user asked "why did this take so long" — stop and write a postmortem. Do this even if the task ultimately succeeded. Successful-after-three-tries is still a failure mode worth recording.

## When to write (auto-trigger conditions)

Write a new postmortem entry when ANY of these happen:

- User says: "doesn't match", "not the same", "this is wrong", "not good", "didn't work", "still off", "look like garbage", "you missed", "broken", or any clearly unhappy tone about the output.
- User asks the same task twice with corrections.
- You needed ≥ 3 iterations to land the deliverable.
- You delivered, declared done, and the user pushed back.
- Tooling did something surprising (extracted wrong data, silent fallback, library bug).
- A heuristic or assumption you made turned out wrong.
- You used the wrong tool, font, color, endpoint, or path.
- A skill or library you trusted gave you false metadata (e.g., PDF reports color X but actually renders Y).

If you're unsure whether to write one, write one. The cost of an extra entry is tiny; the cost of repeating a mistake is real frustration.

## When to read (auto-trigger conditions)

Read relevant lessons BEFORE starting work when:

- The task is a document conversion (PDF/DOCX/PPTX/XLSX in or out).
- The task involves fonts, colors, layout, or visual fidelity.
- The task touches an external API, integration, or service the team uses.
- The task touches an area where a postmortem tag matches.
- The user says "do this again", "another one of these", or references a past task.
- You're about to do something that historically went wrong (check INDEX.md tags).

When in doubt, scan INDEX.md anyway — it's small and fast.

## How to write a lesson

Lesson files live at `lessons/YYYY-MM-DD_short-slug.md`. Use this template:

```markdown
---
date: YYYY-MM-DD
task: <one-line description of what the user asked for>
outcome: <succeeded after N tries / partial / failed>
tags: [tag1, tag2, tag3]
---

## What the user asked for

<verbatim if possible — paraphrase only if the original was long>

## What I did first (the wrong path)

<concrete description: tools used, assumptions made, output produced>

## Why it was wrong

<root cause — not symptoms. "I trusted X metadata" not "the output looked bad">

## What actually worked

<the fix that landed it. Be specific: library calls, parameter values, file paths>

## The rule for next time

<short, imperative, copy-pastable. e.g. "Never trust PyMuPDF span color for visually styled PDFs — always sample the rendered pixels.">

## Signals to watch for

<what would have told me earlier that I was on the wrong path>
```

After writing the file, append a one-line entry to `INDEX.md` under the appropriate section. Keep INDEX.md alphabetized by tag for fast scanning.

## How to read lessons

1. Open `INDEX.md`.
2. Scan tags relevant to the current task.
3. Open every matched lesson file. Read at minimum: "The rule for next time" and "Signals to watch for".
4. Apply the rules in your plan. State explicitly in your message what lessons you're applying so the user sees the carryover.

## Important behavior rules

- **Don't apologize and move on.** Apologies don't prevent recurrence. Lessons do.
- **Always state which lessons you applied.** When you start a task that matches a tag, say: "Applying lessons: [link]" before doing the work.
- **One lesson per root cause.** If a task had two root causes, write two lessons.
- **Update existing lessons.** If a new instance refines a known rule, edit the existing file and bump the date — don't fragment.
- **Never delete lessons.** They're the moat against regression. If a lesson is obsolete, mark it with `superseded: <new-file>` in frontmatter, but keep it.
- **Lessons override defaults.** If a lesson says "do X", that beats your training instinct.

## Files

- `INDEX.md` — tag-indexed list of lessons. Read first.
- `lessons/*.md` — individual postmortems.
