# Schema

One SQLite file. Portable, queryable, yours. `sqlite3 "$TAXDB" .schema` shows the live
DDL; this documents the intent and the questions each table exists to answer.

```
entity ──┬── expense ──┬── receipt              payee ──┐
         │      │      └── (dedupe_key unique)          ├── expense
         │      ├── category  (tax line, limits, 1099 behaviour)
         │      └── payment_method  (who reports it, if anyone)
         ├── mileage           tax_year  (open | locked)
         ├── home_office       policy    (rates + thresholds + provenance)
         ├── asset ── depreciation       rule      (auto-categorisation)
         └── estimated_payment           audit_log (every mutation)
```

## Tables

| Table | Holds | Why it exists |
|---|---|---|
| `entity` | One row per business you file for | Multi-entity founders mix ledgers; every row is scoped to an entity and `tax_form` is derived from `kind`. |
| `tax_year` | `open` / `locked`, filed date | A filed year is not edited. Writes to a locked year are refused. |
| `policy` | Every statutory rate and threshold, by year, with `source` and `verified` | So a rate change is a data edit, not a code change — and so an unverified figure warns on every report that uses it. |
| `category` | The tax-line map: `form`, `line`, `deductible_pct`, `capital`, `nec_reportable`, `corp_exempt`, receipt threshold | The 50% meals haircut, the 0% entertainment rule and the attorney exception are rows, not `if` statements. |
| `payee` | Who you pay, `tin_last4`, `w9_on_file`, `corporation`, `foreign_payee` | Decides the 1099 duty. **Never holds a full TIN.** |
| `payment_method` | How you pay, and `issues_1099k` | The single field that decides whether the network reports a payment or you do. |
| `expense` | The ledger. Integer cents, `business_purpose`, `business_use_pct`, `status`, `dedupe_key` | Cash basis: `paid_on` is the date money moved. |
| `receipt` | Path + SHA-256 + size, one row per file | Proves the evidence has not changed since capture. |
| `mileage` | Per-drive log with the rate applied | Contemporaneous, per §274 substantiation. |
| `home_office` | One row per entity-year, both methods | Recomputed in place, not accumulated. |
| `asset` / `depreciation` | Capitalized purchases and their schedule | Keeps capital spend out of the current-year total. |
| `estimated_payment` | Quarterly prepayments | Not deductions — they tie out against the quarterly report. |
| `rule` | Regex → category | Imports get categorised; they are never auto-confirmed. |
| `audit_log` | Every create/confirm/exclude/lock | Answers "when did this row change, and to what". |

## Views

| View | Rows |
|---|---|
| `v_expense` | Every expense, flattened with payee/category/method, plus computed `deductible_cents` and a receipt count. **Includes drafts.** |
| `v_deduction` | What actually reaches a return: `status='confirmed'`, categorised, non-capital, deducts more than zero. Every filing total is built from this. |
| `v_1099_candidate` | Payments that create a filing duty for *you*: service categories, non-1099-K methods, non-corporate (or attorney) US payees. |

## Invariants

- **Money is `INTEGER` cents.** Never float. `deductible_cents` is computed in the view
  as `amount × business_use_pct × category.deductible_pct`, rounded half-up.
- **`business_use_pct` is constrained to 0–100** by the schema, not by the CLI.
- **`dedupe_key`** = `entity|date|amount|payee|ref`, `UNIQUE`. Re-importing a statement
  is safe; a genuine second identical payment needs `--force`.
- **`status`** is `draft` → `confirmed` → (or) `excluded`. Only `confirmed` counts.
- **Foreign keys are on.** A category or payee in use cannot be deleted out from under a
  row.

## SQL recipes

```sql
-- What did contractors cost me this year, per person?
SELECT payee, SUM(amount_cents)/100.0 usd, COUNT(*) n
FROM v_deduction WHERE year=2026 AND category='contract-labor'
GROUP BY payee_id ORDER BY usd DESC;

-- Every dollar with no evidence attached
SELECT id, paid_on, amount_cents/100.0 usd, payee, category
FROM v_expense
WHERE year=2026 AND status='confirmed' AND receipts=0
  AND amount_cents >= receipt_required_over_cents;

-- Monthly burn by category, as a pivot the CPA can read
SELECT strftime('%Y-%m', paid_on) month, category, SUM(amount_cents)/100.0 usd
FROM v_deduction WHERE year=2026 GROUP BY month, category ORDER BY month;

-- Which payees am I one payment away from owing a 1099?
SELECT payee, SUM(amount_cents)/100.0 usd, MAX(w9_on_file) w9
FROM v_1099_candidate WHERE year=2026
GROUP BY payee_id
HAVING SUM(amount_cents) BETWEEN 100000 AND 199999;

-- Software spend, largest first — the subscription audit
SELECT payee, SUM(amount_cents)/100.0 usd, COUNT(*) charges
FROM v_deduction WHERE year=2026 AND category='software'
GROUP BY payee_id ORDER BY usd DESC;

-- What changed on this row, and when?
SELECT at, action, detail FROM audit_log
WHERE table_name='expense' AND row_id=42 ORDER BY at;

-- Effective deduction rate: how much of what I spent actually deducts
SELECT SUM(amount_cents)/100.0 spent, SUM(deductible_cents)/100.0 deducted,
       ROUND(100.0*SUM(deductible_cents)/SUM(amount_cents),1) pct
FROM v_deduction WHERE year=2026;
```

## Backup

The database and the `receipts/` vault beside it are the evidence. Losing them loses the
deductions, not just the convenience.

```bash
sqlite3 "$TAXDB" ".backup '$HOME/backups/taxdb-$(date +%F).db'"
```

Back up the vault with it, to storage you control and can still read in three years.

## Migrating

`meta.schema_version` tracks the shape. Adding a category, a payment method or a policy
row needs no migration — they are data. Adding a **column** means an `ALTER TABLE`, a
bump of `SCHEMA_VERSION` in `taxdb.py`, and a new assertion in `selftest()`.

A change without a self-test assertion is a change you cannot trust at filing time.
