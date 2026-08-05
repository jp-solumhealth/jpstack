---
name: waalaxy-prospecting
description: Turn a raw prospect or attendee list into a Waalaxy-ready LinkedIn outreach CSV — company ICP gate, role/title resolution, email waterfall and verification, first-name hygiene for personalisation tokens. Use when handed a list of names and companies (conference attendees, exhibitor roster, scraped export, webinar signups, association directory) that needs filtering to real decision makers and loading into Waalaxy or another LinkedIn automation tool. Triggers - "check this list of attendees", "who on this list is ICP", "enrich this list", "get titles for these people", "find their LinkedIn and email", "make it Waalaxy friendly", "build a Waalaxy import", "only C-level", "exclude the clinicians", "prospect this roster", "clean this list for outreach". Produces CSVs only, never a PDF or slide deck. For the curated conference agenda document, use conference-prep instead.
---

# Waalaxy Prospecting & Enrichment

Takes a list whose only reliable columns are **name** and **company**, and returns a CSV that
imports cleanly into Waalaxy with every row a plausible buyer. The whole skill exists to answer
one question per row: *is this a decision maker, and can I reach them?*

Output is **CSV only**. No PDF, no deck, no agenda document.

## When to use

- A list of names + companies arrived and someone asked "who here is worth contacting"
- Titles are missing, wrong, or buried inside the name field as credentials
- You need LinkedIn URLs and emails, verified, for a LinkedIn automation sequence
- A previous export produced broken personalisation ("Hi lan," "Hi GUY,")

**Do not use** for: a single known contact (just look them up), building a conference agenda
document (`conference-prep`), or writing the outreach copy itself (`cold-email`).

## The one rule that saves the most money

**Gate on company BEFORE spending a single API call.** Classify every company first, from the
name alone. Enrich only the ICP buckets. On a 336-row list this removed 123 rows for free — 37%
of the file — before any credit was spent.

Enriching first and filtering after is the default instinct and it is always wrong here.

## Pipeline

```
0 Ingest ......... parse names, strip credentials, salvage inline titles
1 COMPANY GATE ... classify every company; ICP buckets vs excluded  <- no API calls yet
2 Roles .......... waterfall until every ICP row has a title
3 Role filter .... decision maker vs clinician / HR / individual contributor
4 Email .......... find, then VERIFY; never ship a guess
5 Export ......... Waalaxy CSV + QA + audit trail
```

### 0 — Ingest

Names arrive dirty. Split on commas and classify each fragment as a credential or a title:

- `"Julie Adcock, M.S., LBA, BCBA"` -> name + credentials
- `"Dan Dube, Founder and CEO"` -> name + **a free title, keep it**
- `"Paul \"Paulie\" Gavoni, Ed.D"` -> strip the quoted nickname

Inline titles are free role data. Always harvest them before enriching.

### 1 — Company gate

Classify every unique company into a bucket. Buckets and the default verdict:

| Bucket | Enrich? | Notes |
|---|---|---|
| Provider (the service org) | YES | the core buyer |
| RCM / billing / credentialing | YES | buyer and partner |
| Platform/EHR **with a billing component** | YES | partner/channel |
| Consultant serving the buyer | ASK | in or out depends on the ask — confirm |
| Platform with **no** billing component | NO | clinical-software-only |
| **Competitor** | NO | see below |
| HR / staffing / payroll / recruiting | NO | not a buyer |
| Academic, school district, research | NO | |
| Everything else (camps, IT, law, marketing, diagnostics, investors) | NO | |
| No company listed | NO | cannot be qualified — report the count |

**Detect competitors explicitly and by function, not by name.** A vendor selling the same
workflow you sell is not a prospect. Write the competing function into the gate so the next run
catches new entrants. Missing this puts a competitor into an outreach sequence.

**Reuse the buyer's own prior standard when one exists.** If an earlier list on the same
population already split "platform with billing" from "clinical software only", inherit that
split rather than inventing a new one.

Report the gate before moving on: N companies, M rows kept, and the row count per excluded
reason. Never let exclusions be invisible.

### 2 — Role resolution waterfall

Run in this order, keeping a ledger so no contact is looked up twice:

1. **Prior enrichment files** — free. Match across every earlier CSV in the project.
2. **Apollo `people/bulk_match`** — 10 per call, name + organization_name.
3. **Apollo re-match by company domain** — resolve the company's domain, retry with
   `first_name` + `last_name` + `domain`. Recovers a chunk of step-2 misses.
4. **Hunter `domain-search`** — returns position **and** email. Name-match inside the result.
5. **Manual web / LinkedIn search** — for whoever is left.

Step 5 is not a fallback to skip. On a real run Apollo had no title for 57 of 213 gated rows,
and manual search found **16 genuine decision makers** among them, including a Chief Development
Officer and two co-founders. Small-company owners are exactly who Apollo misses and exactly who
buys. Budget for it.

See `references/enrichment-waterfall.md` for per-API limits and the calls that do not work.

### 3 — Role filter

The order of the checks matters more than the checks themselves. See
`references/role-filter.md` for the full ruleset, the regex traps, and the title vocabulary.

Short version: C-level / owner / founder / president in; HR, practising clinicians, clinical
leadership below C-level, individual contributors and site-level deputies out. Decide
credential-vs-role explicitly with the requester, and carry a flag column either way.

### 4 — Email

- Verify **every** address, whatever its source.
- Keep `valid`. Keep `accept_all` but label it unconfirmed — a catch-all domain cannot confirm a
  mailbox, so never call it verified.
- Drop `invalid`: blank the email, keep the person, route them to LinkedIn.
- A pattern-derived address (`{first}@domain`) is a hypothesis. Verify it before use — in
  practice these fail more often than they land.
- Never carry an email whose domain contradicts the company on the list without flagging it.
  It usually means the person changed employer.

### 5 — Waalaxy export

Column order, matching what Waalaxy expects:

```
LinkedIn URL, Email, First Name, Last Name, Company, Title[, Category, Priority]
```

**A row without a LinkedIn URL is useless to Waalaxy.** Split it out to its own email-only file
rather than shipping dead rows.

**`First Name` is a personalisation token, not a label.** It renders straight into
`Hi {{firstName}}`. Every one must be a single correctly-capitalised token.

Run the export through the script — it enforces all of this and fails loudly:

```bash
python3 scripts/waalaxy_export.py --selftest           # run this first, always
python3 scripts/waalaxy_export.py --in list.csv --outdir ./out --segment providers
```

## Quick reference

| Need | Do |
|---|---|
| Cut cost | Company gate before any API call |
| Missing titles | Waterfall step 3 (domain re-match), then step 5 (manual) |
| Reuse an older list | `scripts/match_names.py` — fuzzy, survives spelling variants |
| Build + QA the export | `scripts/waalaxy_export.py` |
| Prove the scripts work | `--selftest` on both |

## Common mistakes

**Enriching before gating.** Burns credits on camps, universities and staffing vendors.

**Exact-string name matching against prior files.** Lists contain OCR damage — `lan Santus` for
`Ian Santus` (lowercase L for capital I). Exact matching silently loses the join, so the contact
looks new and their known email gets re-bought or missed entirely. Use edit-distance-1.

**Trusting a resolved company domain.** Apollo returned a Canadian construction firm for "BBLC"
and a Max Planck domain for an ABA clinic. Always name-match a person inside the domain result
before accepting anything from it.

**Writing `\bpresident\b` in the exec pattern.** It matches inside *Vice* President, promoting
an HR VP and a clinical-ops VP into the top-priority bucket. Every seniority regex needs a
negative check for the modifier in front of it.

**Silently dropping the unresolvable.** Anyone cut must land in an audit file with a reason.
"Role unconfirmed" is a legitimate, reportable outcome; a vanished row is not.

**Reporting `accept_all` as verified.** It means the domain accepts everything, which confirms
nothing about the mailbox.

**Shipping a guessed email.** Pattern-derived addresses bounce; bounces damage the sending
domain. Verify or omit.

## Deliverables

```
<project>/
  waalaxy_<segment>.csv                  <- import to Waalaxy, all rows have LinkedIn
  <segment>_NO_linkedin_email_only.csv   <- no LinkedIn; email or in-person only
  <segment>_full_detail.csv              <- same people, every column
  excluded-audit-trail.csv               <- cut after gating, with reasons
  out-of-scope-by-company.csv            <- cut at the gate, before enrichment
  README-<segment>.txt                   <- counts, method, limits, revisions in order
```

Always state the reconciliation: rows in = kept + cut-after-gate + cut-at-gate. If it does not
add up, something was lost.

When the requester revises scope ("drop the EHRs", "exclude vendor X"), append a dated revision
block to the README rather than rewriting history, park removed rows in their own file instead
of deleting them, and match every spelling variant of a company name when excluding it.
