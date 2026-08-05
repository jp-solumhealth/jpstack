# Role filter — who is a decision maker

The filter runs as an ordered cascade. **Order is the whole design.** A title can match several
patterns at once, so whichever check runs first wins, and getting the order wrong silently
promotes the wrong people.

## The cascade

Evaluate in exactly this order. First match decides.

| # | Check | Verdict | Why it sits here |
|---|---|---|---|
| 1 | Exec: `chief`, CEO/COO/CFO/CRO/CTO, `founder`, `co-founder`, `owner`, `managing partner`, `managing director`, `executive vice president`, `principal`, bare `president` | **IN** | Must precede the clinician check, or `Owner/BCBA` and `BCBA | Founder & Visionary Director` get thrown out as clinicians |
| 2 | HR: `human resources`, `hr`, `people`, `talent`, `recruit*`, `culture`, `employee relations`, `benefits` | OUT | Must precede the senior-business check, or `Vice President Human Resources` reads as a business VP |
| 3 | Practising clinician: `bcba`, `bcba-d`, `bcaba`, `rbt`, `board certified behavior analyst`, `behavior analyst`, `clinician`, `clinical fellow`, `therapist`, `adjunct`, `professor`, `instructor`, `faculty`, `thesis supervisor`, `member`, `student` | OUT | Only when no senior-business token is also present |
| 4 | Clinical leadership below C-level: a clinical word (`clinical`, `behavioral services`, `aba`, `quality`, `training`, `professional standards`, `compliance`) **plus** a seniority word | OUT | Catches `Clinical Director`, `Regional Clinical Director`, `VP of Clinical Operations`, `Director of ABA`, `Head BCBA` |
| 5 | Individual contributor: `account executive`, `account manager`, `customer success`, `sales development`, `bdr`, `sdr`, `solutions engineer`, `product specialist`, `territory account`, `sales advisor`, `coordinator`, `specialist`, `associate`, `representative`, `consultant`, `host`, `coach` | OUT | Only when no seniority word is present |
| 6 | Site/deputy leadership: `assistant|associate|deputy|interim` + `director|vice president` | OUT | A single-site assistant director does not buy |
| 7 | Senior business: `vice president`, `vp`, `svp`, `head of`, `director`, `senior director`, `general manager` | **IN** (lower priority) | Ops, revenue, growth, BD leadership |
| 8 | Anything else | OUT | Below decision-maker level |
| 9 | Empty title | OUT, unless the firm is plainly the person's own | See eponymous rule |

C-level clinical (`Chief Clinical Officer`, `Chief Clinical Operating Officer`,
`Chief Professional Standards Officer`) is caught by check 1 and stays **IN**. That is usually
correct and intended — confirm it matches the ask.

## Regex traps that have actually bitten

**`\bpresident\b` matches inside "Vice President".** This promoted a VP of Human Resources and a
VP of Clinical Operations straight into the top-priority bucket. Guard it:

```python
PRES = re.compile(r"(?<!vice )(?<!vice-)(?<!svp )(?<!assistant )\bpresident\b", re.I)
```

**`\bdirector\b` matches "Assistant Director".** Hence check 6 before check 7.

**`\bmanager\b` matches "General Manager".** Decide which you mean and order accordingly.

**`\bhead\b` matches "Head BCBA".** Use `head of` for the business sense.

## The eponymous rule

An empty title plus a firm carrying the person's surname is strong evidence of ownership:
`Kristina Shiao` at *Shiao Management LLC*, `Crystal Peterson Barker` at *CPB Behavioral*,
`Miladys Rodriguez Silveira` at *Silveira Behavior Consultants*.

Include these at lowest priority with the role flagged unconfirmed. When later verified by web
search, two of the three above were confirmed **Owner / Managing Partner** and **Founder** — so
the heuristic earns its place, but it stays a heuristic. Require surname length > 3 to avoid
coincidental substring hits.

## Credential vs role — decide explicitly

"Exclude BCBAs" is ambiguous and the two readings produce very different lists.

- **Role over credential** (usually intended): exclude *practising* BCBAs, clinical directors and
  RBTs. Keep a CEO/owner/founder who happens to hold the credential. In fields like ABA most
  founders hold it, so a literal credential filter deletes the best targets.
- **Literal credential**: drop anyone holding the credential at all.

Do not silently pick one. Apply role-over-credential as the default, **carry a
`Holds <credential>` flag column** so the literal reading is one filter away, and say which you
applied. On a real run this was 46 of 101 kept contacts — far too many to leave implicit.

## Priority tiers

| Tier | Meaning |
|---|---|
| P1 | C-level / owner / founder |
| P2 | Senior business / ops / revenue |
| P3 | Owner inferred, role unconfirmed |

Spell the tier out in the exported column (`P1 - C-LEVEL / OWNER / FOUNDER`), not as a bare
code. The person reading the CSV should not need a legend.

## Vendor-side nuance

At a platform, RCM or consulting firm, the buying-committee logic inverts: you want their
C-level and function heads (`Head of Sales`, `Head of Strategy`, `Chief Revenue Officer`), not
their AEs and CSMs — those are selling *to* you. Directors and above in a business function are
worth keeping at P2; anyone at IC level is noise.

## Always emit the reason

Every excluded row carries the check that removed it. That audit file is what lets the requester
disagree with a judgment call in seconds instead of re-running the pipeline.
