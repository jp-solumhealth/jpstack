# Substantiation, 1099s and the Traps

What evidence each deduction needs, what paying people obliges you to file, and the
mistakes this database is built to make impossible.

Not tax advice. Every judgment call below goes to your CPA with the flag attached.

---

## 1. The evidence standard

A deduction has to survive three questions: **how much**, **to whom**, and **why it was
business**. A bank line answers the first two. Only you can answer the third, and only
at the time — which is why `--purpose` is required to confirm a row.

| Deduction | What proves it |
|---|---|
| Any expense | Amount, date, payee, business purpose |
| Over $75 (and lodging at any amount) | A receipt as well |
| Meals | Receipt + **who was present** + the business discussed |
| Travel | Itinerary + lodging folio + the purpose of the trip |
| Mileage | A **contemporaneous** log: date, miles, destination, purpose |
| Contract labor | Invoice + W-9 + proof of payment |
| Home office | Square footage, exclusivity, and the costs if using the actual method |
| Assets | Invoice, date placed in service, business-use percentage |

The $75 floor is the statutory receipt threshold, not a deduction threshold — the
expense below it still needs the date, amount, payee and purpose. This database sets
`receipt_required_over_cents` to 7500 for most categories and to **0** (always) for
contract labor, legal, travel, meals and conferences, where a receipt is the only thing
that separates a deduction from an assertion.

**Reconstructed records lose.** Mileage rebuilt in April from a calendar has been
thrown out repeatedly. A log written the day you drove has not.

**Digital copies are fine.** Rev. Proc. 97-22 accepts electronic records that are
legible, complete and retrievable. The vault stores each receipt with a SHA-256 so you
can show the file has not changed since capture.

**Keep everything three years** from the filing date (six if income was understated by
more than 25%; indefinitely for property records, which run until three years after you
dispose of the asset).

---

## 2. Paying people: the obligation nobody sends you a reminder about

Paying a contractor creates a **filing duty for you**. Miss it and the penalty is per
form, per year, and it scales with how late you are — plus the deduction itself gets
harder to defend.

### Does this payment create a 1099?

All five must be true:

1. **For services** (not goods), in the course of your business.
2. **Total for the calendar year is at or above the threshold** — see below.
3. **The payee is not a corporation** — *except attorneys, who are reportable however
   they are organized*.
4. **The payee is a US person** — a foreign contractor gets a W-8BEN instead; a 1099 is
   wrong.
5. **The payment settled over a network that reports nothing for you.**

That last one is the one founders get wrong, and it is decided entirely by *how you
paid*:

| How you paid | Who reports it | Your duty |
|---|---|---|
| **Zelle** | **Nobody** — a bank-to-bank message network, not a settlement organization. It never issues a 1099-K. | **You file the 1099-NEC** |
| ACH, wire, check, cash | Nobody | **You file the 1099-NEC** |
| Business credit/debit card | The merchant acquirer, on 1099-K | **File nothing** |
| PayPal goods & services, Venmo business, Stripe | The TPSO, on 1099-K | **File nothing** |

Issuing a 1099-NEC for a card payment is **double reporting**: the contractor gets taxed
on the same money twice on paper and has to fight it. The `payment_method` table carries
an `issues_1099k` flag per method, and `report 1099` splits the two populations for you.

A Venmo **friends-and-family** payment is not settled as a business transaction and gets
no 1099-K — if you pay contractors that way, add a separate method row with
`issues_1099k` off, because the duty is yours.

### The threshold

`$600` for decades under §6041/§6041A. **P.L. 119-21 (2025) raised it to $2,000 for
payments made after 31 December 2025**, indexed for inflation thereafter. State filing
thresholds did not all follow.

The database ships 2023–2025 at $600 marked **verified**, and 2026 at $2,000 marked
**UNVERIFIED** — every report that uses it prints a warning until you confirm the live
figure and mark it verified. Do that with the CPA, not from memory:

```bash
taxdb.py policy set --year 2026 --key 1099_threshold_cents --value 200000 \
    --source "Instructions for Forms 1099-MISC and 1099-NEC (2026)" --verified
```

### Which box, which form

- **1099-NEC box 1** — fees for services. Due to the recipient **and** the IRS by
  **31 January**. There is no extended paper deadline for NEC.
- **1099-MISC box 1** — rent paid to an individual landlord.
- **1099-MISC box 10** — gross proceeds paid to an attorney (a settlement routed
  through their trust account). Fees for the firm's own legal services are NEC box 1.
  If a payment to a law firm could be either, ask which it was.

### W-9s and backup withholding

Collect the W-9 **before the first payment**. Afterwards you have no leverage and they
have no incentive.

Without a TIN you are required to withhold **24%** and remit it. If you did not, the IRS
can assess it against you — you pay the contractor's tax out of your own pocket and then
try to collect. `report 1099` prints that exposure in dollars for exactly this reason.

Store the W-9 in an encrypted store and reference it by path (`payee add --w9-path`).
**Never put a full SSN or EIN in this database** — the schema holds `tin_last4` only.

---

## 3. The computed deductions

### Mileage

Standard rate × business miles. The rate lives in `policy` per year with its IRS notice;
the engine refuses to compute a year whose rate it does not hold rather than guess.

Commuting from home to a regular office is **not** deductible. If your home is your
principal place of business, trips from it to clients are. Log every drive the day it
happens.

Standard rate or actual costs — one or the other for a vehicle, for the year. Starting
with actual costs in year one generally locks out the standard rate for that vehicle's
life.

### Home office

Two methods, recomputed with `home-office set`:

- **Simplified** — $5.00/sqft, maximum 300 sqft, so $1,500 at the cap (Rev. Proc.
  2013-13). No depreciation, no recapture on sale, almost no records.
- **Actual** — the office's share of rent/mortgage interest, property tax, utilities,
  insurance and repairs. Usually larger, needs the bills, and depreciation taken on an
  owned home is recaptured when you sell.

Both require the space be used **regularly and exclusively** for business, and that it
is your principal place of business. A desk in the living room does not qualify, however
much work happens there. A spare room used only for work does.

An S-corp or C-corp owner does **not** take a home-office deduction personally — the
company reimburses under an accountable plan. Ask the CPA which applies to you.

### Assets and §179

Above the **$2,500 per-item de minimis safe harbour** (Reg. §1.263(a)-1(f), without an
applicable financial statement), a purchase is an asset, not an expense.

- **§179** — expense it in year one, limited by the annual cap **and** by business
  taxable income. Business use must stay above 50% or the deduction is recaptured.
- **Bonus depreciation** — a percentage in year one, no taxable-income limit.
- **Straight line / MACRS** — over the recovery period.

`asset add` records the asset and a **planning** schedule. The return uses MACRS tables
with a half-year or mid-quarter convention; hand the CPA the asset list, not the
schedule.

---

## 4. Traps this tool is built around

- **A screenshot is not a record.** A payment confirmation proves an amount and a
  recipient. It does not prove the date — the app shows a clock, not a calendar — nor
  the purpose, nor that the money was yours to deduct. Ask for all three.
- **The purpose written in April is worth less than the one written on the day.** Rows
  without a purpose stay drafts and never reach a total.
- **Paying by Zelle does not make a payment invisible; it makes it unreported.** The
  duty just moves to you.
- **Personal and business on the same card.** Deductible if genuinely business, but the
  mixing is what turns a routine question into a full examination. Separate accounts,
  and reimburse personal-card business spend through an accountable plan.
- **100% business use on a phone, a car or a home utility** is the claim that invites
  scrutiny. `report missing` flags it.
- **Round numbers everywhere** read as estimates because they usually are.
- **Deducting the same dollar twice** — the owner's retirement contribution on both
  Schedule C and Schedule 1; a contractor under both wages and contract labor; a laptop
  as both supplies and an asset.
- **Cash basis means the date the money moved**, not the invoice date. A December
  invoice paid in January is a January deduction.
- **A locked year is locked.** Once filed, `lock --year` refuses writes. If you amend,
  `unlock` deliberately and note why — the audit log keeps both.
- **§174.** Paying engineers to build product may be a capitalize-and-amortize item
  rather than a current deduction. It is the single largest swing item for a software
  startup's return. Raise it with the CPA before year end, not after.

---

## 5. The calendar

| When | What |
|---|---|
| At each payment | Log it with its purpose and receipt |
| Before the first payment to anyone new | Collect the W-9 |
| Quarterly | `report missing` and clear the gaps; `report quarter` against estimated payments |
| 15 Apr / 15 Jun / 15 Sep / 15 Jan | Estimated tax due — record with `estimate add` |
| Early January | `report 1099`, collect the last W-9s |
| **31 January** | 1099-NEC to recipients **and** the IRS |
| Before filing | `export --year` to the CPA, with the receipt vault |
| After filing | `lock --year --filed <date>` |
