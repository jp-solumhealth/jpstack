---
name: eligibility-check
description: >
  Real-time insurance eligibility and benefits verification through Stedi (X12 270/271).
  Looks up payer IDs in the Stedi payer network, runs eligibility checks for a patient,
  and reports coverage status, copay, coinsurance, deductible remaining, and out-of-pocket
  max in plain English. Also runs batch checks from a CSV roster. Use this skill when the
  user says "check eligibility", "verify insurance", "is this patient covered", "what's the
  copay", "benefits check", "run a 270", "eligibility check", "find the payer ID", or
  mentions Stedi.
---

# Eligibility Check (Stedi)

## Overview

Stedi is a programmable clearinghouse. This skill wraps its healthcare APIs so an
eligibility check goes from "member ID on a fax" to a benefits summary in one step.

**What it answers:** Is coverage active on the date of service? Which plan? What does the
patient owe — copay, coinsurance, deductible remaining, out-of-pocket max? Does the payer
require prior auth or referral for this service type?

**Where it fits:** upstream of `/prior-auth-review`. Verify coverage before spending review
time on a request the plan does not cover, and before a demo where live payer data lands
better than a canned PDF.

---

## Prerequisites

### 1. API key

Set `STEDI_API_KEY` in the environment, or copy `.env.example` to `.env` at the repo root
and fill it in. `.env` is gitignored — **never commit a key, and never paste one into a
chat, a commit message, or a file in this repo.**

Two kinds of key, and the difference matters:

| Key type | What it does | Cost |
|----------|--------------|------|
| **Test** | Returns realistic mock benefits for a fixed set of predefined requests. No data leaves for a payer. | Free |
| **Live** | Sends a real 270 to a real payer with real PHI. | Billed per transaction |

Default to a test key while building or demoing. Only use a live key with real patient
data when the user has explicitly said so.

### 2. Access path — pick one

**MCP server (conversational).** `.mcp.json` in the repo root registers `stedi-healthcare`
at `https://mcp.us.stedi.com/2025-07-11/mcp`, reading the key from `$STEDI_API_KEY`. Claude
Code picks it up on the next start in this directory. It exposes payer search and
eligibility checks as tools, with payer-matching and retry logic built in. Best for
one-off, exploratory checks in conversation.

**Script (deterministic).** `scripts/stedi.py` — stdlib Python, no install. Best for
repeatable checks, batch runs, and anything that should produce a file. If the MCP server
is not connected, use the script; do not ask the user to configure MCP first.

---

## How to Use

### Verify the setup first

Payer search is the cheapest way to confirm the key works — it queries Stedi's payer
network, not a payer, so it costs nothing:

```bash
python3 eligibility-check/scripts/stedi.py payers "aetna"
```

A payer list back means auth is good. `HTTP 401`/`403` means the key is wrong or the
account lacks API access.

### Find the payer ID

The payer ID (`tradingPartnerServiceId`) is the one field users most often get wrong. Never
guess it — look it up. Stedi accepts the primary payer ID, the Stedi payer ID, or any alias
on the payer record.

```bash
python3 eligibility-check/scripts/stedi.py payers "blue cross michigan" --eligibility-only
```

### Run a check

```bash
python3 eligibility-check/scripts/stedi.py check \
  --payer 60054 \
  --npi 1999999984 --org "Solum Health" \
  --first Jane --last Doe --dob 19000101 --member-id W123456789 \
  --service-type 30 \
  --save outputs/jane-doe.json
```

- `--dry-run` prints the request body without sending it. Use it to confirm the shape
  before spending a live transaction.
- `--service-type` defaults to `30` (Health Benefit Plan Coverage), the broad "is this
  person covered" question. For cost share on a specific service, use the matching code
  from [references/service-type-codes.md](references/service-type-codes.md) — `98` for an
  office visit, `A6` for psychotherapy, `88` for pharmacy. **Send one code per request**
  unless the payer is known to support several; many reject multi-code requests outright.
- `--input request.json` sends a full body you assembled yourself, for fields the flags do
  not cover (dependents beyond one, provider identifiers other than NPI).
- Exit code is `0` on a clean response, `1` when the payer returned AAA errors, `2` on a
  local or transport failure.

### Batch a roster

```bash
python3 eligibility-check/scripts/stedi.py batch roster.csv \
  --npi 1999999984 --org "Solum Health" --out outputs/eligibility-batch.csv
```

CSV columns: `firstName,lastName,dateOfBirth,memberId,payerId` plus optional `npi`,
`organizationName`, `serviceTypeCode`. Each row is one real-time check — on a live key that
is one billed transaction per row, so confirm the row count with the user before running.

### Report the result

Lead with the answer, not the JSON:

1. **Coverage status and plan** — active or not, plan name, effective dates.
2. **Patient responsibility** — copay, coinsurance, deductible (annual and *remaining*),
   out-of-pocket max. Always say whether each figure is in- or out-of-network and
   individual or family; those qualifiers change the number the patient actually owes.
3. **Flags** — prior auth or referral required, non-covered services, benefit limits, a
   `R - Other or Additional Payor` line meaning another plan is primary.
4. **Errors** — an AAA code means the payer rejected the lookup, *not* that the patient is
   uninsured. Say which, and what to try next.

State plainly what a 271 cannot tell you. It is a snapshot of the payer's file at that
moment: deductible amounts lag unprocessed claims, and "Active Coverage" is not a payment
guarantee. Do not present it as one.

---

## Handling Errors

| Symptom | Cause | Next step |
|---------|-------|-----------|
| AAA `75` Subscriber/Insured Not Found | Payer cannot match the patient | Retry with a different field combination — member ID + DOB alone often matches when the name does not. Check for a maiden/married name or a member ID prefix. |
| AAA `72` / `73` Invalid or missing subscriber ID or name | Typo, or the prefix belongs on the ID | Re-read the card. Some plans need the alpha prefix; some reject it. |
| AAA `42` Unable to Respond at Current Time | Payer system down | Retry later. Do not hammer it — payers rate-limit and Stedi bills each attempt. |
| AAA `79` / `04` Invalid participant identification | Provider NPI not recognized by this payer | Confirm the NPI, and that the provider is enrolled with the payer. |
| HTTP 401 / 403 | Key missing, wrong, or lacking API access | Check `STEDI_API_KEY`. |
| Empty `benefitsInformation` with active status | Payer answered coverage but not cost share for that service type | Re-run with a more specific service type code. |

Never fabricate benefits when a check fails. Report the failure and the retry you would run.

---

## PHI Rules

Eligibility requests and responses are PHI.

- Saved responses go to `outputs/` — gitignored. Never commit one, and never paste a full
  response into a doc, an issue, a commit message, or a chat with a third party.
- Do not put patient names or member IDs in commit messages or file names checked into git.
- Use synthetic patients for demos and screenshots. A test key with mock data is the safe
  default.
- Before sharing a summary outside the care context, strip identifiers down to what the
  recipient needs.

---

## Reference

- [references/api-reference.md](references/api-reference.md) — endpoints, auth, request and
  response fields, error codes, test mode.
- [references/service-type-codes.md](references/service-type-codes.md) — service type codes
  worth knowing, mapped to what you would ask about them.
