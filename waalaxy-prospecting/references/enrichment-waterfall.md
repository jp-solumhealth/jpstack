# Enrichment waterfall — what works, what doesn't

Keys live in `~/.claude/.api-keys.json`. Read them from the file; never hard-code or echo them.

## Order

| Step | Source | Cost | Returns |
|---|---|---|---|
| 1 | Prior enrichment CSVs already in the project | free | title, email, LinkedIn, phone |
| 2 | Apollo `people/bulk_match` (name + organization_name) | credits | title, email, LinkedIn, seniority, org size |
| 3 | Apollo `people/bulk_match` (first + last + **domain**) | credits | same; recovers step-2 misses |
| 4 | Hunter `domain-search` | credits | email **+ position**, and the domain's email pattern |
| 5 | Manual web / LinkedIn search | time | title, sometimes LinkedIn URL |

Keep a ledger keyed by person so nothing is looked up twice. Record `done` / `no_match` /
`failed` per source, and persist it to disk after every batch so an interrupted run resumes.

## Apollo

**Auth:** header `x-api-key: <key>`. Not a bearer token.

**Rate limit:** `people/bulk_match` allows **20 calls per minute**. At 10 people per call that is
200 people/minute. Exceeding it returns HTTP 429 with an upsell message and the whole batch is
lost. Pace at ~18/min and retry the failures after a 60-second sleep.

**Company domain lookup:** `POST /api/v1/mixed_companies/search` with `q_organization_name`.
Returns `primary_domain`. It does **not** reliably return keywords, description or headcount, so
you cannot use it to sanity-check the match.

**It returns wrong domains for short or ambiguous names.** Observed: "BBLC" resolved to a
Canadian construction firm, an ABA clinic resolved to `mpl.mpg.de` (Max Planck), "AWARE" resolved
to an unrelated `aware.com`. Resolution rate was 39 of 62 companies, and some of those 39 were
wrong.

**Mitigation:** never consume a domain result directly. Require a person-name match inside
whatever the domain returns. If no name matches, discard the domain silently — it is more likely
wrong than the person is absent.

## Hunter

**Auth:** `api_key=<key>` query parameter.

- `email-verifier` — **works.** Statuses: `valid`, `accept_all`, `invalid`, `unknown`,
  `disposable`. Add ~1s between calls on runs of 50+.
- `domain-search` — **works.** Pass `limit=100`. Returns per-address `first_name`, `last_name`,
  `position`, `confidence`, plus the domain's `pattern` (e.g. `{first}`, `{f}{last}`). The
  position field makes this a title source, not just an email source.
- `email-finder` — **403 / error 1010 blocked on this account.** Do not build it into the
  waterfall. Use `domain-search` + name match instead.

**Catch-all domains:** when a domain accepts everything, the verifier returns `accept_all` and
cannot confirm any individual mailbox. Deliverable-ish, but never label it verified.

**Pattern-derived addresses are hypotheses.** Composing `{first}@domain` from the returned
pattern then verifying is legitimate. Of three such candidates tried on one run, one came back
`valid` and two `invalid` — so always verify, never assume.

## Crustdata — not usable for name lookup

`POST /screener/person/search` does **not** accept a person-name filter. Valid `filter_type`
values are only:

```
CURRENT_COMPANY, CURRENT_TITLE, PAST_TITLE, SCHOOL, COMPANY_HEADQUARTERS,
COMPANY_HEADCOUNT, REGION, INDUSTRY, PROFILE_LANGUAGE, SENIORITY_LEVEL,
YEARS_AT_CURRENT_COMPANY, YEARS_IN_CURRENT_POSITION
```

Passing name filters returns `400 Invalid filter_type`. `/screener/people/search` returns 404.
Its person *enrich* endpoint needs a LinkedIn URL or business email — precisely what is missing
for the people Apollo failed to match, so it cannot fill that gap.

**Conclusion: skip Crustdata for this pipeline.** Older documentation that lists it as waterfall
step 2 is wrong; Hunter `domain-search` belongs in that slot.

## Cross-file matching

Prior project CSVs are the cheapest source and the easiest to under-use. Two rules:

1. **Match on last name + fuzzy first name**, allowing edit distance 1. A list read by OCR
   contained `lan Santus` for `Ian Santus`; exact matching lost the join and with it an already-
   verified email.
2. **Validate the recovered email's domain against the company on the current list.** A prior
   file had a contact at a different employer; reusing that address would have mailed the wrong
   company. Where the domain contradicts, keep the LinkedIn URL, flag the email, do not ship it.

`scripts/match_names.py` implements both.

## Expected yield

Rough shape from a 336-row conference list, useful for estimating:

| Stage | Result |
|---|---|
| Company gate | 213 of 336 kept, 123 removed for free |
| Prior files | 83 matched, 66 with a usable title |
| Apollo bulk_match | 129 of 213 matched |
| Apollo domain re-match | +11 titles |
| Hunter domain-search | 0 name matches (the domains were wrong) |
| Manual web search | 16 decision makers recovered from 57 title-less rows |
| After role filter | 101 contacts |
| Email verification | 73 valid, 8 accept-all, 7 invalid |

The manual step produced the highest-value finds. Do not cut it to save time.
