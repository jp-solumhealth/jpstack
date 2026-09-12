# Category Map

Every category in the database, the tax line it maps to, what actually deducts, and the
rule for what belongs in it. Seeded by `taxdb.py init`; inspect live with
`taxdb.py categories` or `taxdb.py categories --grep <word>`.

Line numbers are **Schedule C (Form 1040)**. A partnership (1065), S-corp (1120-S) or
C-corp (1120) keeps the same categories and totals — the line numbering differs and the
reports say so.

## Schedule C, Part II — the deduction lines

| Line | Code | Deducts | The rule |
|---|---|---|---|
| 8 | `advertising` | 100% | Ads, sponsorships, design, swag, PR. **Political contributions are never deductible**, however business-adjacent. |
| 9 | `car-truck` | 100% | Use `mileage add` for the standard rate. Standard rate and actual costs are mutually exclusive for the same vehicle in the same year. |
| 10 | `commissions` | 100% | Referral, finder and affiliate fees to non-employees. 1099-reportable. |
| 11 | `contract-labor` | 100% | Non-employee services. **W-9 before the first payment.** Invoice required at any amount. |
| 13 | `depreciation`, `capital-asset` | via schedule | Capitalized property. Never a current-year expense row — use `asset add`. |
| 14 | `benefits` | 100% | Non-health fringe benefits for W-2 employees. Owner benefits follow different rules. |
| 15 | `insurance` | 100% | E&O, cyber, GL, D&O. Health premiums are **not** here. |
| 16a/16b | `interest-mortgage`, `interest-other` | 100% | Business loan and business card interest. Interest on a personal card is not deductible even when the charge on it was. |
| 17 | `legal-professional` | 100% | Lawyers, CPAs, fractional CFO. **Reportable even when the firm is a corporation.** |
| 18 | `office` | 100% | Consumables under the de minimis threshold. |
| 19 | `pension` | 100% | Employer contributions **for employees**. The owner's own SEP/solo-401k is Schedule 1. |
| 20a/20b | `rent-equipment`, `rent-property` | 100% | Rent to an **individual** landlord is 1099-MISC box 1 reportable — routinely missed. |
| 21 | `repairs` | 100% | Keeps property working. An improvement that betters or restores it is capital. |
| 22 | `supplies` | 100% | Consumed within a year. |
| 23 | `taxes-licenses` | 100% | Employer payroll tax, state registration, licenses, franchise tax. **Not** federal income tax, **not** SE tax. |
| 24a | `travel` | 100% | Away from your tax home overnight. Keep the itinerary — a hotel folio proves spend, not purpose. |
| 24b | `meals` | **50%** | Applied automatically. Record who was there and what was discussed. |
| 25 | `utilities` | 100% | At a business location. Home utilities belong to the home-office computation. |
| 26 | `wages` | 100% | Gross W-2 wages. Never also list the same person under contract labor. |
| 27a | `software`, `dues-subscriptions`, `education`, `bank-fees`, `conferences`, `phone-internet`, `shipping`, `research` | 100% | Part V "other expenses". Each is a separate category here so the CPA sees the composition. |
| 30 | `home-office` | computed | `home-office set`, never expense rows. |

### Line 27a categories, individually

- **`software`** — per-seat tooling. Seats for people who left are still billed and
  still deducted, and still wasted. Audit them quarterly.
- **`dues-subscriptions`** — trade associations, research subscriptions. **Country-club
  dues are non-deductible** regardless of who you meet there.
- **`education`** — maintains or improves skills in your **current** business. Training
  that qualifies you for a new trade does not count.
- **`bank-fees`** — wire fees, Stripe fees, account fees.
- **`conferences`** — booth, registration, sponsorship. Travel there → `travel`; meals
  there → `meals` at 50%.
- **`phone-internet`** — business-use percentage only. A single family line is
  essentially never 100%, and the gap report flags it when you claim it is.
- **`research`** — **§174 costs may have to be capitalized and amortized rather than
  expensed.** This is live for any company paying engineers to build product. Do not
  book these as ordinary expenses without the CPA.

## Not on Schedule C

| Code | Where it goes | Note |
|---|---|---|
| `health-insurance` | Schedule 1, line 17 | Above the line, capped at net self-employment income. |
| `retirement-owner` | Schedule 1, line 16 | The owner's SEP/solo-401k. Deducting it on Schedule C **and** Schedule 1 is a classic solo-founder error. |
| `charitable` | Schedule A, or 1120 | A sole prop **never** deducts charity on Schedule C. |

## Tracked but not deductible

These exist so the number can be recorded honestly and then correctly excluded. The
reports show them in their own block.

| Code | Why zero |
|---|---|
| `entertainment` | 0% since the 2017 Act. Kept separate so it can never be swept into `meals`. |
| `fines-penalties` | §162(f) — government fines and penalties are never deductible. |
| `owner-draw` | Moving your own money is not an expense. |
| `estimated-tax` | A prepayment of tax, not a deduction. Record with `estimate add`. |
| `personal` | Personal spend that touched a business account. Booking it honestly is what makes the rest of the ledger defensible. |
| `uncategorized` | Parking space for imports. Nothing here reaches a return. |

## Where founders misfile

- **Contractor vs employee.** If you control *how* the work is done, not just the
  result, the IRS may call them an employee — and the exposure is back payroll tax plus
  penalties, far larger than the deduction. Long-term full-time "contractors" are the
  risk case.
- **A laptop is not supplies.** Over $2,500 per item it is an asset (`asset add`).
- **Meals at a conference** are `meals` (50%), not `conferences` (100%). Splitting a
  conference invoice that bundles catering is worth the ten minutes.
- **Coffee alone while working** is not a business meal. There is no counterparty.
- **The home-office category is not for rent you pay on an office.** That is
  `rent-property`, at 100%.
- **Software bought for a client project** is still `software` — use `--client` to tag
  it so you can see project profitability without distorting the tax category.

## Adding a category

```bash
sqlite3 "$TAXDB" "INSERT INTO category
  (code,label,form,line,deductible_pct,capital,nec_reportable,corp_exempt,
   receipt_required_over_cents,guidance)
  VALUES ('franchise-fees','Franchise fees','Schedule C','27a',100,0,0,1,7500,
          'Ongoing franchise royalties. The initial fee is capital.');"
```

Set `nec_reportable=1` if paying someone in this category can create a 1099 duty, and
`corp_exempt=0` only for the attorney case. Then re-run `selftest`.
