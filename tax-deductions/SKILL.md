---
name: tax-deductions
description: Build and run the deduction database — record every business payment with its evidence the moment it happens, categorise it to a tax line, compute what actually deducts, and track the 1099 filing obligations you create by paying people. Use when logging a receipt or payment screenshot, asking "is this deductible", "how much did I deduct this year", "do I owe anyone a 1099", "what am I missing for taxes", importing a bank or card CSV, closing a quarter, or packaging the year for a CPA. Triggers - "log this receipt", "deduct this", "write this off", "is this a business expense", "tax deductions", "Schedule C", "1099", "W-9", "contractor payment", "mileage", "home office", "what do I owe my accountant", "close the books".
---

# Tax Deduction Database

A deduction you cannot evidence is a deduction you do not have. This skill keeps the
evidence and the arithmetic in one SQLite file you own, captured at the moment money
moves — because nobody reconstructs a year of business purposes in April.

It also tracks the obligation most solo founders discover too late: paying a person
creates a **filing duty for you**, and the payment app does not do it on your behalf.

## The engine

`scripts/taxdb.py` — Python 3 stdlib only, no packages, no services, one file on disk.

**Run the self-test first, every time.**

```bash
python3 scripts/taxdb.py selftest        # must print ALL PASS
```

The self-test asserts the money arithmetic (integer cents, half-up rounding, the 50%
meals haircut, business-use percentages) and every 1099 rule against hand-computed
numbers. If it does not print **ALL PASS**, do not file anything off this database.

```bash
python3 scripts/taxdb.py init --entity "Solum Health" --kind c-corp --state DE
python3 scripts/taxdb.py status
```

The database lives at `~/.claude/data/tax-deductions.db` unless `$TAXDB` or `--db`
says otherwise. Receipts are copied into a `receipts/` vault beside it. **Both are
the evidence. Back them up.**

## Logging a payment — the whole job

```bash
python3 scripts/taxdb.py add \
  --date 2026-03-04 --amount 500 \
  --payee "Example Contractor" --category contract-labor --method zelle \
  --purpose "March contract design work on the onboarding flow" \
  --ref "Zelle confirmation ABC123" \
  --receipt ~/Desktop/zelle-payment.png \
  --confirm
```

That one command: stores the row in cents, copies the screenshot into the vault with
its SHA-256, maps it to a tax line, computes the deduction — and tells you how far that
payee now is into a threshold that makes **you** the 1099 filer, with no W-9 on file.

**A screenshot is not a record.** A payment confirmation proves an amount and a
recipient. It does not prove the date (the app shows a clock, not a calendar), the
business purpose, or that the money was yours to deduct. Always ask the user for:

1. **The date the money moved** — never guess it from a screenshot timestamp.
2. **What the payment bought, specifically** — "September contract design work on the
   onboarding flow", not "contractor". This text is the deduction.
3. **Which entity paid** — if more than one exists.

Without a purpose the row stays a `draft`, is visible in every gap report, and reaches
no return. That is deliberate. `--confirm` is refused without `--purpose`.

## The daily loop

| You say | Command |
|---|---|
| "log this receipt" | `add --date … --amount … --payee … --category … --method … --purpose … --receipt … --confirm` |
| "what's deductible here?" | `categories --grep <word>` — the map, with the rule for each line |
| "pull in my card statement" | `import --csv stmt.csv --map date=…,amount=…,description=… --method biz-card --negative-is-spend` |
| "sort those imports" | `rule add --payee '(?i)aws' --category software` then `categorize --apply` |
| "I drove to a demo" | `mileage add --date … --miles … --purpose …` |
| "my home office" | `home-office --year 2026 --method simplified --office-sqft 180` |
| "I bought a laptop" | `asset --description … --date … --cost … --method section-179` |
| "how am I doing?" | `report schedule-c --year 2026` |
| "do I owe anyone a 1099?" | `report 1099 --year 2026` |
| "what am I missing?" | `report missing --year 2026` |
| "send it to my CPA" | `export --year 2026 --out ~/cpa-2026` |
| "we filed" | `lock --year 2026 --filed 2027-03-15` |

## The five rules this skill exists to enforce

**1 — No purpose, no deduction.** §162 deducts what is *ordinary and necessary* for
the business. The amount is the easy half; the purpose is the half that gets tested.
Write it at the moment of payment, naming people and projects — "Dinner with
&lt;name&gt;, &lt;practice&gt; — PA pilot scope" survives an audit, "Client dinner"
does not.

**2 — Paying by Zelle makes you the 1099 filer.** Zelle is a bank-to-bank message
network, not a third-party settlement organization. It files nothing. Nor does ACH, a
wire, a check or cash. Cross the threshold with a contractor on any of those and the
1099-NEC is yours to file. Pay the *same contractor by card, PayPal goods-and-services
or Stripe* and the network files a 1099-K — issuing your own 1099-NEC on top is double
reporting that lands on the payee. The `method` you record is what decides this, which
is why `--method` is worth getting right.

**3 — Get the W-9 before the money moves.** After payment you have no leverage and the
contractor has no incentive. Without a TIN you are exposed to 24% backup withholding on
everything you paid them — `report 1099` prints that number in dollars, because it is
usually the largest avoidable line in the whole database.

**4 — Rates are data, not code.** Every statutory figure lives in the `policy` table
with its source and a `verified` flag. The engine **refuses to guess a rate it does not
hold** — ask it for 2026 mileage before you have recorded the year's notice and it
stops and tells you to look it up. Anything unverified prints a warning on every report
that uses it. Check it against the IRS, then:

```bash
python3 scripts/taxdb.py policy set --year 2026 --key mileage_cents_per_mile \
    --value 70.0 --source "IRS Notice 2026-XX" --verified
python3 scripts/taxdb.py policy list --year 2026
```

The **2026 1099 threshold ships UNVERIFIED on purpose.** It was $600 for decades;
P.L. 119-21 (2025) raised it to $2,000 for payments made after 2025, indexed after
that, and state thresholds did not follow in lockstep. Confirm the live figure with
the CPA before relying on it. `/fact-check` is the sibling skill for exactly this.

**5 — Capitalize what must be capitalized.** A $3,200 laptop is not a $3,200 expense.
Above the $2,500 per-item de minimis safe harbour it is an asset that deducts over a
schedule (or all at once under §179, with limits and recapture). Capital categories are
structurally excluded from the deduction total; `asset` is the command that books them.

## Reading `report schedule-c`

```
  line  category                  n      gross  deduction
  11    contract-labor            2  $2,150.00  $2,150.00
  24b   meals                     1     $83.19     $41.60      <- 50% haircut, automatic
  27a   phone-internet            1    $200.00    $120.00      <- 60% business use
  30    home office (simplified)                    $900.00

  TOTAL — 2026:  $8,695.88
  ⚠ 3 DRAFT rows worth $103.99 are NOT in the total above.
```

`gross` is what left the bank. `deduction` is what reaches a return after the
business-use percentage and the category's own limit. The gap between them is the
point of the whole database. Drafts are never silently included.

Line numbers are the **Schedule C map** — the category grouping this database uses. An
1120 or 1120-S filer keeps the categories and the totals; the line numbers differ, and
the report says so.

## Never publish the data

This database holds real financial records about real people. Treat all of it as
private, always:

- **The database and the `receipts/` vault never go into a git repository.** Both are
  gitignored here. Keep them outside any working tree you push, and back them up to
  storage you control — not to a repo, a gist, or a shared drive that syncs to one.
- **Never put a real payee name, amount, account number or confirmation code into
  code, docs, commit messages, issues or PRs** — including this skill's own examples.
  Placeholders only: `Example Contractor`, `ABC123`, round invented amounts. A
  contractor's name paired with what you paid them is their private information as
  much as yours, and a public repo is forever.
- **Never store a full SSN or EIN.** The schema holds `tin_last4` only; the W-9 lives
  in an encrypted store, referenced by path.
- **Before sharing any output** — a report, an export, a screenshot of a table — check
  what is in it. `report 1099` and `export` both contain payee names and amounts by
  design.
- If real data does reach a repository, scrubbing the file is not enough: the old
  commit has to be rewritten and force-pushed, and on a public repo you should assume
  it was already cloned or indexed.

## What it will not do

It does not file anything, it does not compute your tax, and it is **not tax advice**.
It produces a defensible, evidenced, arithmetically exact record and an export your CPA
can work from in an hour instead of a week. Every judgment call it flags — §174 R&D
treatment, §179 limits, attorney payments, home-office eligibility, entity-specific
lines — goes to the CPA with the flag attached.

Never put a full SSN or EIN in this database. The schema holds `tin_last4` only; the
W-9 itself belongs in an encrypted store, referenced by path.

## Reference

- `references/category-map.md` — every category, its tax line, its limit, and the rule
  for what belongs in it.
- `references/substantiation.md` — what evidence each deduction needs, the 1099/W-9
  mechanics, the deadlines, and the traps this tool is built around.
- `references/schema.md` — the data model, the views, and SQL recipes for questions
  the CLI does not answer.
