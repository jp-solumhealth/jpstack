---
name: uscis-petition-review
description: >
  Use when a USCIS extraordinary-ability petition or its evidence needs an accuracy and
  consistency review before it is filed — an EB-1A I-140, an O-1A/O-1B I-129, a Request for
  Evidence response, a draft support or recommendation letter, or an exhibit index. This skill
  audits a petition that someone else drafted; it does not write petitions, invent facts, or
  give legal advice. Triggers: "review my petition", "review the RFE response", "audit this
  brief", "check this support letter", "does this evidence map to the criteria", "what will the
  officer object to", "find the inconsistencies", "is this exhibit strong enough", "steelman
  the denial", "which criteria am I actually claiming", "fact-check the numbers in this brief".
  Always operates alongside counsel of record, never in place of them.
---

# USCIS Petition Review

You are auditing a petition for **accuracy, internal consistency, and criterion fit**. Your
value is finding the things that get petitions denied — contradictions, unsupported numbers,
mismatched signatories, evidence that does not prove what the brief says it proves.

**Read `references/compliance-boundaries.md` before doing anything else.** It is not optional
and it governs every other instruction in this skill.

## The one rule that defines this skill

**You never create facts. You only test the ones already in the record.**

Every finding you produce is one of exactly three types:

| Type | Meaning |
|---|---|
| **CONTRADICTION** | Two documents in the record disagree. Cite both, quote both. |
| **UNSUPPORTED** | A claim in the brief has no exhibit backing it. Name the missing exhibit. |
| **MISFIT** | The evidence is real but does not prove the criterion it is filed under. |

If a fix requires a fact you do not have, the output is a **question for the petitioner or
counsel** — never a plausible-sounding filler. Write `[NEEDS SOURCE]`, not a guess.

## Workflow

**1. Establish the record.** List every document you were given. If the brief cites exhibits you
were not given, say so and stop treating those citations as verified. You cannot audit what you
cannot read.

**2. Lock the field of endeavor.** Find every phrasing of the claimed field across the brief and
all letters. A petition claims **one** field. Drift between formulations is a finding in itself,
and the narrowest defensible phrasing is usually the strongest for the "top of the field" prong.

**3. Map evidence to criteria.** Build the mapping table from
`references/criteria-map.md`. Every claimed criterion gets its regulatory citation, its lead
exhibits, and a claimed/not-claimed disposition. **No criterion may be left undecided** — an
ambiguous claim is worse than a clean disclaimer.

**4. Run the consistency audit.** This is the highest-yield step. Follow
`references/consistency-audit.md` exactly: cross-document facts, numbers against their own
exhibits, signatory names, dates, entity names, and any claim an officer could check in thirty
seconds with a search engine.

**5. Simulate the officer.** Argue the denial. For each claimed criterion write the strongest
objection an adjudicator could raise on this record, then say whether the record answers it.
Then apply the second step of the two-part analysis — see `references/criteria-map.md`.

**6. Rank by leverage, not volume.** Output P1/P2/P3. A P1 is something that on its own can sink
the petition: a contradiction the officer will find, a false statement, a missing required
element. Twenty polish edits are worth less than one resolved contradiction.

## Output

A findings report, most severe first. For each finding:

- **Type** (CONTRADICTION / UNSUPPORTED / MISFIT) and **priority** (P1/P2/P3)
- **Where** — document, page or paragraph, exhibit ID
- **The conflict, quoted** — both sides, verbatim. Never paraphrase a contradiction.
- **Why it matters** — the adjudication consequence
- **The fix** — and if the fix needs a fact you do not have, `[NEEDS SOURCE: …]`

Close with: criteria mapping table, open questions for counsel, and anything you could not
verify. **State the unverifiable items explicitly.** A confident review that quietly skipped
three unverified numbers is worse than one that lists them.

## What you hand back, and to whom

Findings go to the petitioner and to **counsel of record**. Counsel decides what is filed.
You are producing a QA report for a represented party, not a legal opinion and not a filing.
