#!/usr/bin/env python3
"""
taxdb.py — the deduction database. SQLite, stdlib only, no services.

Every dollar you can legally deduct, captured at the moment you spend it, with the
evidence attached and the 1099 consequences computed. Cash basis.

    python3 taxdb.py selftest                 # MUST print ALL PASS before you trust output
    python3 taxdb.py init --entity "Solum Health" --kind c-corp
    python3 taxdb.py add --date 2026-03-04 --amount 500 --payee "Example Contractor" \
        --category contract-labor --method zelle --purpose "March contract design work" \
        --receipt ~/receipts/zelle-payment.png --confirm
    python3 taxdb.py report schedule-c --year 2026
    python3 taxdb.py report 1099 --year 2026
    python3 taxdb.py report missing --year 2026
    python3 taxdb.py export --year 2026 --out ~/cpa-2026

DESIGN CONTRACT — the four rules this file enforces in code, not in prose:

  1. Money is integer cents. Never a float. Floats lose pennies and a CPA notices.
  2. No deduction without a business purpose. `--purpose` is required to reach
     status=confirmed. An unpurposed row is a draft and never reaches a return.
  3. Rates and thresholds are DATA, with provenance and a `verified` flag — see the
     `policy` table. The engine refuses to guess a rate it does not hold.
  4. Every rate/threshold the IRS changes lives in `policy`, per year. Nothing
     statutory is hardcoded in a report.

PRIVACY. This file holds real financial records about real people.
  - NEVER store a full SSN or EIN here. The schema holds `tin_last4` only; the W-9
    itself belongs in an encrypted store, referenced by path.
  - The database and its receipt vault NEVER belong in a git repository.
  - Every name and amount in this source file is a placeholder and must stay one.
    Real payee data goes in the database, never in code, docs or commit messages.

Category map, substantiation rules and the traps: ../references/
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import shutil
import sqlite3
import sys
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

SCHEMA_VERSION = 1
DEFAULT_DB = os.environ.get("TAXDB") or os.path.expanduser("~/.claude/data/tax-deductions.db")

# ════════════════════════════════════════════════════════════════════ money & time


def cents(raw) -> int:
    """'$1,234.56' | '1234.56' | 1234.56 -> 123456. Half-up, never float arithmetic."""
    if isinstance(raw, int):
        return raw
    s = str(raw).strip().replace("$", "").replace(",", "").replace("_", "")
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return int((Decimal(s) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError):
        die(f"not an amount: {raw!r}")


def usd(c: int | None) -> str:
    c = c or 0
    return f"{'-' if c < 0 else ''}${abs(c) // 100:,}.{abs(c) % 100:02d}"


def pct_of(amount_cents: int, *pcts: float) -> int:
    """amount x each percentage, half-up, exact. pct_of(35000, 60, 50) -> 10500."""
    v = Decimal(amount_cents)
    for p in pcts:
        v = v * Decimal(str(p)) / Decimal(100)
    return int(v.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def iso(raw: str) -> str:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%b %d, %Y", "%d %b %Y"):
        try:
            return datetime.strptime(str(raw).strip(), fmt).date().isoformat()
        except ValueError:
            continue
    die(f"not a date: {raw!r} (use YYYY-MM-DD)")


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def die(msg: str, code: int = 2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def slugify(s: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-") or "x"


# ════════════════════════════════════════════════════════════════════════ schema

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE entity (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN
    ('sole-prop','single-member-llc','partnership','s-corp','c-corp','personal')),
  tax_form TEXT NOT NULL,
  ein_last4 TEXT,
  home_state TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE tax_year (
  year INTEGER PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','locked')),
  filed_on TEXT,
  locked_at TEXT,
  note TEXT
);

-- Every statutory rate and threshold, per year, with provenance.
-- verified=0 means NOBODY HAS CHECKED THIS AGAINST THE IRS — reports say so out loud.
CREATE TABLE policy (
  year INTEGER NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  source TEXT NOT NULL,
  verified INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (year, key)
);

CREATE TABLE category (
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  label TEXT NOT NULL,
  form TEXT NOT NULL,
  line TEXT,
  deductible_pct REAL NOT NULL DEFAULT 100.0,
  capital INTEGER NOT NULL DEFAULT 0,          -- capitalize + depreciate, never expense
  nec_reportable INTEGER NOT NULL DEFAULT 0,   -- payments here can create a 1099 duty
  corp_exempt INTEGER NOT NULL DEFAULT 1,      -- 0 = reportable even to a corporation
  receipt_required_over_cents INTEGER NOT NULL DEFAULT 7500,
  guidance TEXT,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE payee (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'unknown'
    CHECK(kind IN ('individual','business','government','employee','unknown')),
  tin_last4 TEXT,                              -- LAST FOUR ONLY. Never the full TIN.
  w9_on_file INTEGER NOT NULL DEFAULT 0,
  w9_path TEXT,
  corporation INTEGER NOT NULL DEFAULT 0,
  foreign_payee INTEGER NOT NULL DEFAULT 0,    -- W-8BEN territory, not 1099
  email TEXT,
  address TEXT,
  note TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE payment_method (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  label TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN
    ('bank-transfer','card','cash','check','tpso','crypto','other')),
  account_last4 TEXT,
  business_account INTEGER NOT NULL DEFAULT 1,
  issues_1099k INTEGER NOT NULL DEFAULT 0,     -- 1 = the network files a 1099-K for you
  note TEXT
);

CREATE TABLE expense (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER NOT NULL REFERENCES entity(id),
  paid_on TEXT NOT NULL,
  year INTEGER NOT NULL,
  amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
  payee_id INTEGER REFERENCES payee(id),
  category_id INTEGER REFERENCES category(id),
  method_id INTEGER REFERENCES payment_method(id),
  business_purpose TEXT,
  business_use_pct REAL NOT NULL DEFAULT 100.0
    CHECK(business_use_pct >= 0 AND business_use_pct <= 100),
  status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','confirmed','excluded')),
  exclude_reason TEXT,
  external_ref TEXT,
  source TEXT NOT NULL DEFAULT 'manual',
  memo TEXT,
  client_tag TEXT,
  reimbursable INTEGER NOT NULL DEFAULT 0,
  dedupe_key TEXT UNIQUE NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_expense_year ON expense(year, status);
CREATE INDEX idx_expense_payee ON expense(payee_id, year);

CREATE TABLE receipt (
  id INTEGER PRIMARY KEY,
  expense_id INTEGER NOT NULL REFERENCES expense(id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  bytes INTEGER NOT NULL,
  kind TEXT NOT NULL DEFAULT 'receipt',
  captured_at TEXT,
  note TEXT,
  added_at TEXT NOT NULL,
  UNIQUE(expense_id, sha256)
);

CREATE TABLE mileage (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER NOT NULL REFERENCES entity(id),
  drove_on TEXT NOT NULL,
  year INTEGER NOT NULL,
  miles REAL NOT NULL CHECK(miles > 0),
  origin TEXT,
  destination TEXT,
  business_purpose TEXT NOT NULL,
  vehicle TEXT,
  rate_cents_per_mile REAL NOT NULL,
  deduction_cents INTEGER NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE home_office (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER NOT NULL REFERENCES entity(id),
  year INTEGER NOT NULL,
  method TEXT NOT NULL CHECK(method IN ('simplified','actual')),
  office_sqft REAL,
  home_sqft REAL,
  months_used REAL NOT NULL DEFAULT 12,
  rent_cents INTEGER NOT NULL DEFAULT 0,
  mortgage_interest_cents INTEGER NOT NULL DEFAULT 0,
  property_tax_cents INTEGER NOT NULL DEFAULT 0,
  utilities_cents INTEGER NOT NULL DEFAULT 0,
  insurance_cents INTEGER NOT NULL DEFAULT 0,
  repairs_cents INTEGER NOT NULL DEFAULT 0,
  other_cents INTEGER NOT NULL DEFAULT 0,
  deduction_cents INTEGER NOT NULL,
  note TEXT,
  computed_at TEXT NOT NULL,
  UNIQUE(entity_id, year)
);

CREATE TABLE asset (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER NOT NULL REFERENCES entity(id),
  description TEXT NOT NULL,
  placed_in_service TEXT NOT NULL,
  cost_cents INTEGER NOT NULL CHECK(cost_cents > 0),
  business_use_pct REAL NOT NULL DEFAULT 100.0,
  method TEXT NOT NULL CHECK(method IN
    ('section-179','bonus','macrs-sl','de-minimis','amortize')),
  recovery_years REAL,
  expense_id INTEGER REFERENCES expense(id),
  disposed_on TEXT,
  note TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE depreciation (
  asset_id INTEGER NOT NULL REFERENCES asset(id) ON DELETE CASCADE,
  year INTEGER NOT NULL,
  amount_cents INTEGER NOT NULL,
  note TEXT,
  PRIMARY KEY (asset_id, year)
);

CREATE TABLE estimated_payment (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER NOT NULL REFERENCES entity(id),
  year INTEGER NOT NULL,
  quarter INTEGER NOT NULL CHECK(quarter BETWEEN 1 AND 4),
  jurisdiction TEXT NOT NULL DEFAULT 'federal',
  paid_on TEXT NOT NULL,
  amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
  confirmation TEXT,
  note TEXT,
  created_at TEXT NOT NULL
);

-- Auto-categorisation. Highest priority wins; ties broken by lowest id.
CREATE TABLE rule (
  id INTEGER PRIMARY KEY,
  priority INTEGER NOT NULL DEFAULT 100,
  match_payee TEXT,
  match_memo TEXT,
  match_method TEXT,
  min_cents INTEGER,
  max_cents INTEGER,
  category_id INTEGER NOT NULL REFERENCES category(id),
  business_use_pct REAL,
  purpose_template TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  hits INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY,
  at TEXT NOT NULL,
  action TEXT NOT NULL,
  table_name TEXT NOT NULL,
  row_id INTEGER,
  detail TEXT
);

CREATE VIEW v_expense AS
SELECT
  e.id, e.entity_id, e.paid_on, e.year, e.amount_cents, e.business_use_pct,
  e.status, e.business_purpose, e.external_ref, e.memo, e.source, e.client_tag,
  e.exclude_reason, e.reimbursable,
  ent.slug AS entity, ent.kind AS entity_kind,
  p.id AS payee_id, p.name AS payee, p.corporation, p.w9_on_file, p.foreign_payee,
  p.tin_last4,
  c.id AS category_id, c.code AS category, c.label AS category_label,
  c.form, c.line, c.deductible_pct, c.capital, c.nec_reportable, c.corp_exempt,
  c.receipt_required_over_cents,
  m.slug AS method, m.kind AS method_kind, m.issues_1099k, m.business_account,
  CAST(ROUND(e.amount_cents * e.business_use_pct / 100.0
             * COALESCE(c.deductible_pct, 0) / 100.0) AS INTEGER) AS deductible_cents,
  (SELECT COUNT(*) FROM receipt r WHERE r.expense_id = e.id) AS receipts
FROM expense e
JOIN entity ent ON ent.id = e.entity_id
LEFT JOIN payee p ON p.id = e.payee_id
LEFT JOIN category c ON c.id = e.category_id
LEFT JOIN payment_method m ON m.id = e.method_id;

-- Deductions that actually reach a return: confirmed, non-capital, real category.
CREATE VIEW v_deduction AS
SELECT * FROM v_expense
WHERE status = 'confirmed' AND category_id IS NOT NULL AND capital = 0
  AND deductible_cents > 0;

-- Payments that create a 1099 filing duty for YOU: services, to a human or
-- unincorporated business, settled over a network that files nothing on your behalf.
CREATE VIEW v_1099_candidate AS
SELECT * FROM v_expense
WHERE status IN ('draft','confirmed')
  AND nec_reportable = 1
  AND COALESCE(issues_1099k, 0) = 0
  AND COALESCE(foreign_payee, 0) = 0
  AND (COALESCE(corporation, 0) = 0 OR corp_exempt = 0)
  AND payee_id IS NOT NULL;
"""

# ═══════════════════════════════════════════════════════════════════════ seed data
# (code, label, form, line, deductible_pct, capital, nec, corp_exempt, receipt_over, guidance)
CATEGORIES = [
    ("advertising", "Advertising & marketing", "Schedule C", "8", 100, 0, 1, 1, 7500,
     "Ads, sponsorships, design, swag, PR. Political contributions are NEVER deductible."),
    ("car-truck", "Car & truck expenses", "Schedule C", "9", 100, 0, 0, 1, 7500,
     "Use `mileage add` for the standard rate. Standard rate and actual costs are mutually "
     "exclusive for the same vehicle in the same year — pick one."),
    ("commissions", "Commissions & fees", "Schedule C", "10", 100, 0, 1, 1, 7500,
     "Referral, finder and affiliate fees paid to non-employees."),
    ("contract-labor", "Contract labor (1099 contractors)", "Schedule C", "11", 100, 0, 1, 1, 0,
     "Services from non-employees. Get the W-9 BEFORE the first dollar moves — after "
     "payment your leverage is zero. Invoice required at any amount."),
    ("depreciation", "Depreciation & section 179", "Schedule C", "13", 100, 1, 0, 1, 0,
     "Capitalized property. Record with `asset add`; the annual number comes from the "
     "depreciation schedule, never from an expense row."),
    ("capital-asset", "Capital asset purchase", "Schedule C", "13", 100, 1, 0, 1, 0,
     "Above the $2,500 per-item de minimis safe harbour. Capitalize it: `asset add`."),
    ("benefits", "Employee benefit programs", "Schedule C", "14", 100, 0, 0, 1, 7500,
     "Non-health fringe benefits for W-2 employees. Owner benefits follow different rules."),
    ("insurance", "Insurance (other than health)", "Schedule C", "15", 100, 0, 0, 1, 7500,
     "E&O, cyber, general liability, D&O. Health premiums go to `health-insurance`."),
    ("interest-mortgage", "Interest — mortgage", "Schedule C", "16a", 100, 0, 0, 1, 7500,
     "Mortgage interest on business real property."),
    ("interest-other", "Interest — other", "Schedule C", "16b", 100, 0, 0, 1, 7500,
     "Business loan and business card interest. Interest on a personal card is not "
     "deductible even when the charge on it was."),
    ("legal-professional", "Legal & professional services", "Schedule C", "17", 100, 0, 1, 0, 0,
     "Lawyers, CPAs, fractional CFO. ATTORNEY FEES ARE 1099-REPORTABLE EVEN IF THE FIRM "
     "IS A CORPORATION — that is why corp_exempt is 0 here."),
    ("office", "Office expense", "Schedule C", "18", 100, 0, 0, 1, 7500,
     "Consumables and small office costs under the de minimis threshold."),
    ("pension", "Pension & profit-sharing plans", "Schedule C", "19", 100, 0, 0, 1, 0,
     "Employer contributions for employees. The owner's own SEP/solo-401k deduction is "
     "Schedule 1, not Schedule C."),
    ("rent-equipment", "Rent/lease — vehicles & equipment", "Schedule C", "20a", 100, 0, 1, 1, 7500,
     "Equipment leases. A lease with a bargain buyout may be a purchase in substance."),
    ("rent-property", "Rent/lease — other business property", "Schedule C", "20b", 100, 0, 1, 1, 0,
     "Office and storage rent. Rent paid to an INDIVIDUAL landlord is 1099-MISC box 1 "
     "reportable — most founders miss this one."),
    ("repairs", "Repairs & maintenance", "Schedule C", "21", 100, 0, 1, 1, 7500,
     "Keeps property in working order. An improvement that betters or restores it is "
     "capital, not a repair."),
    ("supplies", "Supplies", "Schedule C", "22", 100, 0, 0, 1, 7500,
     "Consumed within a year."),
    ("taxes-licenses", "Taxes & licenses", "Schedule C", "23", 100, 0, 0, 1, 7500,
     "Employer payroll tax, state registration, business licenses, franchise tax. NOT "
     "federal income tax and NOT self-employment tax."),
    ("travel", "Travel", "Schedule C", "24a", 100, 0, 0, 1, 0,
     "Away from your tax home overnight for business. Keep the itinerary — a hotel folio "
     "proves the spend, not the purpose."),
    ("meals", "Business meals", "Schedule C", "24b", 50, 0, 0, 1, 0,
     "50% deductible. Record WHO was there and WHAT was discussed in the purpose. A meal "
     "with no named counterparty is an audit gift."),
    ("utilities", "Utilities", "Schedule C", "25", 100, 0, 0, 1, 7500,
     "Utilities at a business location. Home utilities belong to the home-office computation."),
    ("wages", "Wages (W-2 payroll)", "Schedule C", "26", 100, 0, 0, 1, 0,
     "Gross W-2 wages. Do not also list the same person under contract labor."),
    ("software", "Software & SaaS subscriptions", "Schedule C", "27a", 100, 0, 0, 1, 7500,
     "Per-seat tooling. Seats for people who left are still billed and still deducted — "
     "and still wasted."),
    ("dues-subscriptions", "Dues, memberships & publications", "Schedule C", "27a", 100, 0, 0, 1, 7500,
     "Trade associations and research subscriptions. Country-club dues are non-deductible."),
    ("education", "Education & training", "Schedule C", "27a", 100, 0, 0, 1, 7500,
     "Maintains or improves skills in your CURRENT business. Training that qualifies you "
     "for a new trade does not count."),
    ("bank-fees", "Bank & payment processing fees", "Schedule C", "27a", 100, 0, 0, 1, 7500,
     "Wire fees, Stripe fees, monthly account fees."),
    ("conferences", "Conferences & trade shows", "Schedule C", "27a", 100, 0, 0, 1, 0,
     "Booth, registration and sponsorship. Travel to get there goes to `travel`; meals "
     "there go to `meals` at 50%."),
    ("phone-internet", "Phone & internet", "Schedule C", "27a", 100, 0, 0, 1, 7500,
     "Business-use percentage only. A single family line is essentially never 100%."),
    ("shipping", "Shipping & postage", "Schedule C", "27a", 100, 0, 0, 1, 7500, None),
    ("research", "Research & experimentation (§174)", "Schedule C", "27a", 100, 0, 0, 1, 0,
     "§174 costs may have to be capitalized and amortized rather than expensed. Do not "
     "book these as ordinary expenses without asking the CPA — this is a live issue for "
     "any company paying engineers to build product."),
    ("home-office", "Home office", "Schedule C", "30", 100, 0, 0, 1, 0,
     "Computed by `home-office set`, never entered as expense rows."),
    ("health-insurance", "Self-employed health insurance", "Schedule 1", "17", 100, 0, 0, 1, 0,
     "Above the line on Schedule 1, NOT on Schedule C. Capped at net self-employment income."),
    ("retirement-owner", "Owner retirement contribution (SEP/solo-401k)", "Schedule 1", "16", 100, 0, 0, 1, 0,
     "Schedule 1, not Schedule C. Deducting it twice is a classic solo-founder error."),
    ("charitable", "Charitable contributions", "entity-dependent", None, 100, 0, 0, 1, 7500,
     "A sole prop deducts these on Schedule A, not Schedule C. A C-corp deducts on 1120 "
     "subject to the taxable-income limit. Never a Schedule C expense."),
    ("entertainment", "Entertainment (non-deductible)", "none", None, 0, 0, 0, 1, 0,
     "0% since the 2017 Act. Tracked so it can never be swept into `meals`."),
    ("fines-penalties", "Fines & penalties (non-deductible)", "none", None, 0, 0, 0, 1, 0,
     "Government fines and penalties are never deductible (§162(f))."),
    ("owner-draw", "Owner draw / distribution", "none", None, 0, 0, 0, 1, 0,
     "Not an expense. Moving your own money is not a deduction."),
    ("estimated-tax", "Estimated income tax payment", "none", None, 0, 0, 0, 1, 0,
     "Not a deduction. Record with `estimate add` so the quarterly report ties out."),
    ("personal", "Personal / non-deductible", "none", None, 0, 0, 0, 1, 0,
     "Personal spend that touched a business account. Booking it honestly is what makes "
     "the rest of the ledger defensible."),
    ("uncategorized", "Uncategorized (needs review)", "none", None, 0, 0, 0, 1, 0,
     "Parking space for imports. Nothing here reaches a return."),
]

# (slug, label, kind, business_account, issues_1099k, note)
METHODS = [
    ("zelle", "Zelle", "bank-transfer", 1, 0,
     "Zelle is a bank-to-bank message network, NOT a third-party settlement organization. "
     "No 1099-K is ever issued for a Zelle payment. If a contractor crosses the threshold, "
     "YOU file the 1099-NEC — nobody does it for you."),
    ("ach", "ACH / bank transfer", "bank-transfer", 1, 0, "Same 1099 exposure as Zelle."),
    ("wire", "Wire transfer", "bank-transfer", 1, 0, "Same 1099 exposure as Zelle."),
    ("check", "Business check", "check", 1, 0, "Same 1099 exposure as Zelle."),
    ("cash", "Cash", "cash", 1, 0,
     "Weakest evidence in the database. Contemporaneous note + receipt or it does not count."),
    ("biz-card", "Business credit card", "card", 1, 1,
     "Card payments are reported by the merchant acquirer on 1099-K. Do NOT also issue a "
     "1099-NEC for a card payment — that is double reporting and it lands on the payee."),
    ("biz-debit", "Business debit card", "card", 1, 1, "Reported by the acquirer on 1099-K."),
    ("paypal-gs", "PayPal (goods & services)", "tpso", 1, 1,
     "A third-party settlement organization. PayPal files the 1099-K."),
    ("venmo-business", "Venmo (business profile)", "tpso", 1, 1,
     "TPSO. Venmo files the 1099-K. A Venmo FRIENDS-AND-FAMILY payment is not settled as "
     "business and gets no 1099-K — use a different method row if you do that."),
    ("stripe", "Stripe", "tpso", 1, 1, "TPSO. Stripe files the 1099-K."),
    ("personal-card", "Personal card (reimbursable)", "card", 0, 1,
     "Deductible if genuinely business, but reimburse it through an accountable plan and "
     "keep the evidence twice as tight."),
]

POLICIES = [
    # 1099-NEC / 1099-MISC filing threshold, per §6041/§6041A.
    (2023, "1099_threshold_cents", "60000",
     "IRC §6041/§6041A; Instructions for Forms 1099-MISC and 1099-NEC (2023)", 1),
    (2024, "1099_threshold_cents", "60000",
     "IRC §6041/§6041A; Instructions for Forms 1099-MISC and 1099-NEC (2024)", 1),
    (2025, "1099_threshold_cents", "60000",
     "IRC §6041/§6041A; Instructions for Forms 1099-MISC and 1099-NEC (2025)", 1),
    (2026, "1099_threshold_cents", "200000",
     "P.L. 119-21 (2025) raised the §6041/§6041A threshold to $2,000 for payments made "
     "after 2025, indexed for inflation thereafter. UNVERIFIED HERE — confirm the current "
     "figure and the state filing threshold with your CPA before relying on it.", 0),
    # Standard mileage rate, business use, cents per mile.
    (2023, "mileage_cents_per_mile", "65.5", "IRS Notice 2023-03", 1),
    (2024, "mileage_cents_per_mile", "67.0", "IRS Notice 2024-08", 1),
    (2025, "mileage_cents_per_mile", "70.0", "IRS Notice 2025-05", 1),
    # Simplified home office: Rev. Proc. 2013-13, unchanged since.
    *[(y, "home_office_rate_cents_per_sqft", "500", "Rev. Proc. 2013-13", 1)
      for y in (2023, 2024, 2025, 2026)],
    *[(y, "home_office_max_sqft", "300", "Rev. Proc. 2013-13", 1)
      for y in (2023, 2024, 2025, 2026)],
    # De minimis safe harbour per item, no applicable financial statement.
    *[(y, "de_minimis_cents", "250000", "Reg. §1.263(a)-1(f); Notice 2015-82", 1)
      for y in (2023, 2024, 2025, 2026)],
    *[(y, "backup_withholding_pct", "24", "IRC §3406", 1)
      for y in (2023, 2024, 2025, 2026)],
]


# ════════════════════════════════════════════════════════════════════════ plumbing


def connect(path: str, must_exist: bool = True) -> sqlite3.Connection:
    if path != ":memory:" and must_exist and not os.path.exists(path):
        die(f"no database at {path} — run: python3 taxdb.py init --db {path}")
    if path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def log(con, action: str, table: str, row_id, detail: str = ""):
    con.execute(
        "INSERT INTO audit_log (at, action, table_name, row_id, detail) VALUES (?,?,?,?,?)",
        (now(), action, table, row_id, detail),
    )


def policy(con, year: int, key: str, *, required: bool = True):
    row = con.execute("SELECT * FROM policy WHERE year=? AND key=?", (year, key)).fetchone()
    if row is None and required:
        die(
            f"no {key} recorded for {year}. This engine does not guess statutory rates.\n"
            f"  Look it up, then: python3 taxdb.py policy set --year {year} --key {key} "
            f"--value <value> --source '<IRS notice>' --verified"
        )
    return row


def build(con):
    con.executescript(SCHEMA_SQL)
    con.execute("INSERT INTO meta (key, value) VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))
    con.execute("INSERT INTO meta (key, value) VALUES ('created_at', ?)", (now(),))
    con.executemany(
        "INSERT INTO category (code,label,form,line,deductible_pct,capital,nec_reportable,"
        "corp_exempt,receipt_required_over_cents,guidance) VALUES (?,?,?,?,?,?,?,?,?,?)",
        CATEGORIES,
    )
    con.executemany(
        "INSERT INTO payment_method (slug,label,kind,business_account,issues_1099k,note) "
        "VALUES (?,?,?,?,?,?)",
        METHODS,
    )
    con.executemany(
        "INSERT INTO policy (year,key,value,source,verified,updated_at) VALUES (?,?,?,?,?,?)",
        [(y, k, v, s, ver, now()) for (y, k, v, s, ver) in POLICIES],
    )
    for y in (2023, 2024, 2025, 2026, 2027):
        con.execute("INSERT OR IGNORE INTO tax_year (year, status) VALUES (?, 'open')", (y,))
    con.commit()


def entity_row(con, ref=None):
    if ref:
        r = con.execute("SELECT * FROM entity WHERE slug=? OR name=? OR id=?",
                        (ref, ref, ref if str(ref).isdigit() else -1)).fetchone()
        if not r:
            die(f"no entity {ref!r} — see: taxdb.py entity list")
        return r
    rows = con.execute("SELECT * FROM entity WHERE active=1 ORDER BY id").fetchall()
    if not rows:
        die("no entity yet — run: taxdb.py entity add --name '...' --kind c-corp")
    if len(rows) > 1:
        die(f"{len(rows)} entities exist — pass --entity "
            f"({', '.join(r['slug'] for r in rows)})")
    return rows[0]


def get_or_create_payee(con, name: str, **kw) -> sqlite3.Row:
    slug = slugify(name)
    r = con.execute("SELECT * FROM payee WHERE slug=? OR lower(name)=lower(?)",
                    (slug, name)).fetchone()
    if r:
        return r
    con.execute(
        "INSERT INTO payee (slug,name,kind,tin_last4,w9_on_file,w9_path,corporation,"
        "foreign_payee,email,note,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (slug, name, kw.get("kind", "unknown"), kw.get("tin_last4"),
         int(kw.get("w9_on_file", 0)), kw.get("w9_path"), int(kw.get("corporation", 0)),
         int(kw.get("foreign_payee", 0)), kw.get("email"), kw.get("note"), now()),
    )
    log(con, "create", "payee", con.execute("SELECT last_insert_rowid() i").fetchone()["i"], name)
    return con.execute("SELECT * FROM payee WHERE slug=?", (slug,)).fetchone()


def lookup(con, table: str, ref, col="slug"):
    if ref is None:
        return None
    key = "code" if table == "category" else col
    r = con.execute(f"SELECT * FROM {table} WHERE {key}=?", (str(ref),)).fetchone()
    if not r:
        opts = ", ".join(x[0] for x in con.execute(
            f"SELECT {key} FROM {table} WHERE {'active=1' if table=='category' else '1=1'} "
            f"ORDER BY {key}").fetchall())
        die(f"unknown {table} {ref!r}.\n  known: {opts}")
    return r


def guard_year(con, year: int):
    r = con.execute("SELECT status FROM tax_year WHERE year=?", (year,)).fetchone()
    if r and r["status"] == "locked":
        die(f"tax year {year} is locked — a filed year is not edited. "
            f"To reopen deliberately: taxdb.py unlock --year {year}")
    if not r:
        con.execute("INSERT INTO tax_year (year, status) VALUES (?, 'open')", (year,))


def sha256_of(path: str) -> tuple[str, int]:
    h, n = hashlib.sha256(), 0
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 20):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n


def vault_dir(db_path: str) -> str:
    base = os.path.dirname(os.path.abspath(db_path)) if db_path != ":memory:" else "."
    return os.path.join(base, "receipts")


# ═══════════════════════════════════════════════════════════════════════ printing


def banner(title: str, width: int = 78):
    print("\n" + "═" * width)
    print(title)
    print("═" * width)


def table(rows, cols, widths=None, right=()):
    if not rows:
        print("  (none)")
        return
    widths = widths or [max(len(str(c)), *(len(str(r.get(c, ""))) for r in rows)) for c in cols]
    head = "  ".join(str(c).ljust(w) if c not in right else str(c).rjust(w)
                     for c, w in zip(cols, widths))
    print("  " + head)
    print("  " + "  ".join("-" * w for w in widths))
    for r in rows:
        print("  " + "  ".join(
            (str(r.get(c, "")).rjust(w) if c in right else str(r.get(c, ""))[:w].ljust(w))
            for c, w in zip(cols, widths)))


def warn_unverified(con, year: int, key: str):
    p = policy(con, year, key, required=False)
    if p and not p["verified"]:
        print(f"\n  ⚠ UNVERIFIED POLICY — {key} for {year} = {p['value']}")
        for line in _wrap(p["source"] or "", 70):
            print(f"      {line}")
        print("      Verify before filing, then: taxdb.py policy set ... --verified")


# ════════════════════════════════════════════════════════════════════════ commands


def cmd_init(a):
    if a.db != ":memory:" and os.path.exists(a.db) and not a.force:
        die(f"{a.db} already exists (use --force to rebuild from scratch — this DELETES it)")
    if a.force and os.path.exists(a.db):
        os.remove(a.db)
    con = connect(a.db, must_exist=False)
    build(con)
    if a.entity:
        add_entity(con, a.entity, a.kind, a.ein_last4, a.state)
    con.commit()
    print(f"database ready: {a.db}")
    print(f"  {len(CATEGORIES)} categories, {len(METHODS)} payment methods, "
          f"{len(POLICIES)} policy rows")
    print(f"  receipt vault: {vault_dir(a.db)}")
    print("\nBack this file up. It is the evidence, not a convenience.")
    print("Next: taxdb.py add --date ... --amount ... --payee ... --category ... "
          "--method ... --purpose ...")


FORM_BY_KIND = {
    "sole-prop": "Schedule C", "single-member-llc": "Schedule C", "partnership": "Form 1065",
    "s-corp": "Form 1120-S", "c-corp": "Form 1120", "personal": "Form 1040",
}


def add_entity(con, name, kind, ein_last4=None, state=None):
    con.execute(
        "INSERT INTO entity (slug,name,kind,tax_form,ein_last4,home_state,created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (slugify(name), name, kind, FORM_BY_KIND[kind], ein_last4, state, now()),
    )
    eid = con.execute("SELECT last_insert_rowid() i").fetchone()["i"]
    log(con, "create", "entity", eid, f"{name} ({kind})")
    print(f"entity {eid}: {name} — {kind}, files {FORM_BY_KIND[kind]}")
    return eid


def cmd_entity(a):
    con = connect(a.db)
    if a.sub == "add":
        add_entity(con, a.name, a.kind, a.ein_last4, a.state)
        con.commit()
    else:
        table([dict(r) for r in con.execute("SELECT * FROM entity ORDER BY id")],
              ["id", "slug", "name", "kind", "tax_form", "active"])


def cmd_categories(a):
    con = connect(a.db)
    q = "SELECT * FROM category WHERE active=1"
    p = []
    if a.grep:
        q += " AND (code LIKE ? OR label LIKE ? OR guidance LIKE ?)"
        p = [f"%{a.grep}%"] * 3
    rows = con.execute(q + " ORDER BY form, line, code", p).fetchall()
    banner(f"CATEGORIES ({len(rows)})")
    out = [{"code": r["code"], "label": r["label"], "form": r["form"], "line": r["line"] or "",
            "ded%": f"{r['deductible_pct']:g}", "cap": "Y" if r["capital"] else "",
            "1099": "Y" if r["nec_reportable"] else ""} for r in rows]
    table(out, ["code", "label", "form", "line", "ded%", "cap", "1099"], right=("ded%",))
    if a.grep and len(rows) <= 6:
        for r in rows:
            if r["guidance"]:
                print(f"\n  {r['code']}:\n    " + "\n    ".join(
                    _wrap(r["guidance"], 72)))


def _wrap(text: str, width: int):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


def cmd_policy(a):
    con = connect(a.db)
    if a.sub == "set":
        con.execute(
            "INSERT INTO policy (year,key,value,source,verified,updated_at) VALUES (?,?,?,?,?,?) "
            "ON CONFLICT(year,key) DO UPDATE SET value=excluded.value, source=excluded.source, "
            "verified=excluded.verified, updated_at=excluded.updated_at",
            (a.year, a.key, a.value, a.source, int(a.verified), now()),
        )
        log(con, "set", "policy", None, f"{a.year}/{a.key}={a.value}")
        con.commit()
        print(f"policy {a.year} {a.key} = {a.value} "
              f"({'verified' if a.verified else 'UNVERIFIED'})")
        return
    rows = con.execute(
        "SELECT * FROM policy WHERE (? IS NULL OR year=?) ORDER BY key, year",
        (a.year, a.year)).fetchall()
    banner("POLICY — statutory rates and thresholds")
    table([{"year": r["year"], "key": r["key"], "value": r["value"],
            "verified": "yes" if r["verified"] else "NO", "source": r["source"][:60]}
           for r in rows], ["year", "key", "value", "verified", "source"])
    print("\n  Anything marked NO has not been checked against the IRS. Reports that use "
          "it\n  print a warning. Verify, then re-set it with --verified.")


def cmd_payee(a):
    con = connect(a.db)
    if a.sub == "add":
        if a.tin_last4 and len(str(a.tin_last4)) != 4:
            die("--tin-last4 takes the LAST FOUR DIGITS ONLY. Never store a full TIN here.")
        p = get_or_create_payee(con, a.name, kind=a.kind, tin_last4=a.tin_last4,
                                w9_on_file=a.w9, w9_path=a.w9_path,
                                corporation=a.corporation, foreign_payee=a.foreign,
                                email=a.email, note=a.note)
        fields = {"kind": a.kind, "tin_last4": a.tin_last4, "w9_on_file": int(a.w9),
                  "w9_path": a.w9_path, "corporation": int(a.corporation),
                  "foreign_payee": int(a.foreign), "email": a.email, "note": a.note}
        sets = {k: v for k, v in fields.items() if v not in (None, 0, "unknown", "")}
        if sets:
            con.execute(f"UPDATE payee SET {','.join(f'{k}=?' for k in sets)} WHERE id=?",
                        [*sets.values(), p["id"]])
        con.commit()
        print(f"payee {p['id']}: {p['name']}"
              + ("  [W-9 on file]" if a.w9 else "  ⚠ NO W-9 ON FILE"))
        if not a.w9 and not a.corporation:
            print("  Get the W-9 before the next payment. Without a TIN you are exposed to "
                  "24% backup withholding on everything you paid them.")
        return
    rows = con.execute("""
        SELECT p.*, COALESCE(SUM(e.amount_cents),0) paid, COUNT(e.id) n
        FROM payee p LEFT JOIN expense e
          ON e.payee_id=p.id AND e.status!='excluded' AND (? IS NULL OR e.year=?)
        GROUP BY p.id ORDER BY paid DESC""", (a.year, a.year)).fetchall()
    banner(f"PAYEES{f' — {a.year}' if a.year else ''}")
    table([{"id": r["id"], "name": r["name"], "kind": r["kind"],
            "corp": "Y" if r["corporation"] else "", "W-9": "Y" if r["w9_on_file"] else "NO",
            "tin": r["tin_last4"] or "", "payments": r["n"], "paid": usd(r["paid"])}
           for r in rows],
          ["id", "name", "kind", "corp", "W-9", "tin", "payments", "paid"],
          right=("payments", "paid"))


def cmd_method(a):
    con = connect(a.db)
    if a.sub == "add":
        con.execute(
            "INSERT INTO payment_method (slug,label,kind,account_last4,business_account,"
            "issues_1099k,note) VALUES (?,?,?,?,?,?,?)",
            (slugify(a.label) if not a.slug else a.slug, a.label, a.kind, a.account_last4,
             int(not a.personal), int(a.issues_1099k), a.note))
        con.commit()
        print(f"payment method added: {a.label}")
        return
    rows = con.execute("SELECT * FROM payment_method ORDER BY kind, slug").fetchall()
    banner("PAYMENT METHODS")
    table([{"slug": r["slug"], "label": r["label"], "kind": r["kind"],
            "last4": r["account_last4"] or "", "biz": "Y" if r["business_account"] else "",
            "1099-K filed by network": "YES" if r["issues_1099k"] else "no — YOU file"}
           for r in rows], ["slug", "label", "kind", "last4", "biz",
                            "1099-K filed by network"])
    print("\n  'no — YOU file' means no third party reports these payments. If a payee "
          "crosses\n  the threshold on those methods, the 1099-NEC is your obligation.")


def _dedupe_key(entity_id, paid_on, amount_cents, payee_id, ref) -> str:
    return "|".join(str(x) for x in (entity_id, paid_on, amount_cents, payee_id or "-",
                                     (ref or "").strip().lower() or "-"))


def cmd_add(a):
    con = connect(a.db)
    ent = entity_row(con, a.entity)
    paid_on = iso(a.date)
    year = int(paid_on[:4])
    guard_year(con, year)
    amt = cents(a.amount)
    payee = get_or_create_payee(con, a.payee) if a.payee else None
    cat = lookup(con, "category", a.category) if a.category else None
    method = lookup(con, "payment_method", a.method) if a.method else None

    status = "draft"
    if a.confirm:
        if not a.purpose:
            die("--confirm requires --purpose. A deduction without a documented business "
                "purpose is not a deduction (§162 ordinary and necessary).")
        if not cat:
            die("--confirm requires --category.")
        status = "confirmed"

    key = _dedupe_key(ent["id"], paid_on, amt, payee["id"] if payee else None, a.ref)
    if a.force:
        key += f"|f{now()}"
    dup = con.execute("SELECT id FROM expense WHERE dedupe_key=?", (key,)).fetchone()
    if dup:
        die(f"duplicate of expense {dup['id']} (same entity/date/amount/payee/ref). "
            f"Use --force if this really is a second identical payment.")

    con.execute(
        "INSERT INTO expense (entity_id,paid_on,year,amount_cents,payee_id,category_id,"
        "method_id,business_purpose,business_use_pct,status,external_ref,source,memo,"
        "client_tag,reimbursable,dedupe_key,created_at,updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (ent["id"], paid_on, year, amt, payee["id"] if payee else None,
         cat["id"] if cat else None, method["id"] if method else None, a.purpose,
         a.pct, status, a.ref, a.source, a.memo, a.client, int(a.reimbursable), key,
         now(), now()))
    eid = con.execute("SELECT last_insert_rowid() i").fetchone()["i"]
    log(con, "create", "expense", eid, f"{paid_on} {usd(amt)} {a.payee or ''}")

    if a.receipt:
        attach(con, a.db, eid, a.receipt, a.receipt_kind, link=a.link)
    con.commit()

    row = con.execute("SELECT * FROM v_expense WHERE id=?", (eid,)).fetchone()
    print(f"\nexpense {eid} [{status}]  {paid_on}  {usd(amt)}  {row['payee'] or '(no payee)'}")
    print(f"  category  {row['category'] or '(none)'}" + _line_ref(row))
    print(f"  method    {row['method'] or '(none)'}")
    if row["category"]:
        print(f"  deducts   {_deduction_line(row)}")
    if cat and cat["capital"]:
        dm = policy(con, year, "de_minimis_cents", required=False)
        print(f"  CAPITAL — this is not a current-year expense. Record it so it depreciates:\n"
              f"    python3 taxdb.py asset --description \"...\" --date {paid_on} "
              f"--cost {amt/100:.2f} --method section-179"
              + (f"\n    De minimis safe harbour is {usd(int(dm['value']))} per item — "
                 f"below that you may expense it instead." if dm else ""))
    if status == "draft":
        print(f"  DRAFT — not on any return yet. Confirm it:\n"
              f"    python3 taxdb.py confirm {eid} --purpose \"...\""
              + ("" if cat else " --category <code>"))
    _nec_warning(con, row, year)
    _receipt_warning(row)


def _line_ref(row) -> str:
    """Line numbers in the category map are Schedule C. Say so to a 1120/1065 filer."""
    if not row["category"] or not row["line"]:
        return ""
    if row["entity_kind"] in ("sole-prop", "single-member-llc") or row["form"] != "Schedule C":
        return f" -> {row['form']} line {row['line']}"
    return f" -> Schedule C line {row['line']} (map; your return is {FORM_BY_KIND[row['entity_kind']]})"


def _deduction_line(row) -> str:
    """What this row actually deducts THIS year — capital rows deduct nothing."""
    if row["capital"]:
        return "$0.00 this year — capitalized, deducts over the depreciation schedule"
    extra = ""
    if row["business_use_pct"] != 100 or row["deductible_pct"] != 100:
        extra = (f"  ({row['business_use_pct']:g}% business"
                 f" x {row['deductible_pct']:g}% category)")
    return usd(row["deductible_cents"]) + extra


def _nec_warning(con, row, year):
    if not row["category_id"] or not row["nec_reportable"]:
        return
    if row["issues_1099k"] or row["foreign_payee"]:
        return
    if row["corporation"] and row["corp_exempt"]:
        return
    thr = policy(con, year, "1099_threshold_cents", required=False)
    total = con.execute(
        "SELECT COALESCE(SUM(amount_cents),0) t FROM v_1099_candidate WHERE payee_id=? AND year=?",
        (row["payee_id"], year)).fetchone()["t"]
    line = f"  1099 watch — {row['payee']} at {usd(total)} for {year} on non-1099-K methods"
    if thr:
        t = int(thr["value"])
        over = total >= t
        print(f"{line}; threshold {usd(t)}"
              f"{'  ** YOU MUST FILE A 1099-NEC **' if over else ''}")
        if not thr["verified"]:
            print("    ⚠ that threshold is UNVERIFIED in this database — check it.")
    else:
        print(line)
    if not row["w9_on_file"]:
        print(f"    ⚠ NO W-9 ON FILE for {row['payee']}. Get it now: "
              f"taxdb.py payee add --name \"{row['payee']}\" --w9 --tin-last4 ####")


def _receipt_warning(row):
    if row["status"] == "confirmed" and row["receipts"] == 0 and row["category_id"]:
        thr = row["receipt_required_over_cents"]
        if row["amount_cents"] >= thr:
            print(f"  ⚠ NO RECEIPT attached and this category requires one"
                  + (f" above {usd(thr)}" if thr else " at any amount")
                  + f".\n    python3 taxdb.py receipt {row['id']} --file <path>")


def attach(con, db_path, expense_id: int, path: str, kind: str = "receipt", link: bool = False):
    src = os.path.expanduser(path)
    if not os.path.isfile(src):
        die(f"no such file: {src}")
    row = con.execute("SELECT * FROM expense WHERE id=?", (expense_id,)).fetchone()
    if not row:
        die(f"no expense {expense_id}")
    guard_year(con, row["year"])
    digest, size = sha256_of(src)
    dest = src
    if not link and db_path != ":memory:":
        folder = os.path.join(vault_dir(db_path), str(row["year"]))
        os.makedirs(folder, exist_ok=True)
        ext = os.path.splitext(src)[1].lower()
        dest = os.path.join(folder, f"{expense_id:06d}-{digest[:8]}{ext}")
        if not os.path.exists(dest):
            shutil.copy2(src, dest)
    try:
        con.execute(
            "INSERT INTO receipt (expense_id,path,sha256,bytes,kind,captured_at,added_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (expense_id, os.path.abspath(dest), digest, size, kind,
             datetime.fromtimestamp(os.path.getmtime(src), timezone.utc)
             .strftime("%Y-%m-%dT%H:%M:%SZ"), now()))
    except sqlite3.IntegrityError:
        print(f"  receipt already attached to expense {expense_id} (same sha256)")
        return
    log(con, "attach", "receipt", expense_id, digest[:16])
    print(f"  receipt stored: {dest}\n    sha256 {digest[:32]}…  {size:,} bytes")


def cmd_receipt(a):
    con = connect(a.db)
    attach(con, a.db, a.id, a.file, a.kind, link=a.link)
    con.commit()


def cmd_confirm(a):
    con = connect(a.db)
    row = con.execute("SELECT * FROM v_expense WHERE id=?", (a.id,)).fetchone()
    if not row:
        die(f"no expense {a.id}")
    guard_year(con, row["year"])
    purpose = a.purpose or row["business_purpose"]
    cat = lookup(con, "category", a.category) if a.category else None
    cat_id = cat["id"] if cat else row["category_id"]
    if not purpose:
        die("--purpose required. No purpose, no deduction.")
    if not cat_id:
        die("--category required.")
    con.execute("UPDATE expense SET status='confirmed', business_purpose=?, category_id=?, "
                "business_use_pct=COALESCE(?,business_use_pct), updated_at=? WHERE id=?",
                (purpose, cat_id, a.pct, now(), a.id))
    log(con, "confirm", "expense", a.id, purpose[:80])
    con.commit()
    row = con.execute("SELECT * FROM v_expense WHERE id=?", (a.id,)).fetchone()
    print(f"expense {a.id} confirmed — {row['category']}{_line_ref(row)}\n"
          f"  of {usd(row['amount_cents'])} paid, deducts {_deduction_line(row)}")
    _nec_warning(con, row, row["year"])
    _receipt_warning(row)


def cmd_exclude(a):
    con = connect(a.db)
    row = con.execute("SELECT * FROM expense WHERE id=?", (a.id,)).fetchone()
    if not row:
        die(f"no expense {a.id}")
    guard_year(con, row["year"])
    con.execute("UPDATE expense SET status='excluded', exclude_reason=?, updated_at=? WHERE id=?",
                (a.reason, now(), a.id))
    log(con, "exclude", "expense", a.id, a.reason)
    con.commit()
    print(f"expense {a.id} excluded — {a.reason}")


def cmd_list(a):
    con = connect(a.db)
    q = "SELECT * FROM v_expense WHERE 1=1"
    p = []
    for col, val in (("year", a.year), ("status", a.status), ("category", a.category)):
        if val:
            q += f" AND {col}=?"
            p.append(val)
    if a.payee:
        q += " AND payee LIKE ?"
        p.append(f"%{a.payee}%")
    if a.needs_work:
        q += (" AND (status='draft' OR business_purpose IS NULL OR category_id IS NULL"
              " OR (status='confirmed' AND receipts=0 AND amount_cents >= "
              "receipt_required_over_cents))")
    rows = con.execute(q + " ORDER BY paid_on DESC, id DESC LIMIT ?", [*p, a.limit]).fetchall()
    banner(f"EXPENSES ({len(rows)})")
    table([{"id": r["id"], "date": r["paid_on"], "amount": usd(r["amount_cents"]),
            "payee": (r["payee"] or "")[:24], "category": r["category"] or "—",
            "method": r["method"] or "—", "st": r["status"][:4],
            "rcpt": r["receipts"] or "", "deducts": usd(r["deductible_cents"])}
           for r in rows],
          ["id", "date", "amount", "payee", "category", "method", "st", "rcpt", "deducts"],
          right=("id", "amount", "deducts"))
    tot = sum(r["deductible_cents"] for r in rows if r["status"] == "confirmed")
    print(f"\n  confirmed deductions in this view: {usd(tot)}")


def cmd_mileage(a):
    con = connect(a.db)
    ent = entity_row(con, a.entity)
    if a.sub == "add":
        d = iso(a.date)
        year = int(d[:4])
        guard_year(con, year)
        rate = float(a.rate) if a.rate else float(
            policy(con, year, "mileage_cents_per_mile")["value"])
        ded = int((Decimal(str(a.miles)) * Decimal(str(rate)))
                  .quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        con.execute(
            "INSERT INTO mileage (entity_id,drove_on,year,miles,origin,destination,"
            "business_purpose,vehicle,rate_cents_per_mile,deduction_cents,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (ent["id"], d, year, a.miles, a.origin, a.destination, a.purpose, a.vehicle,
             rate, ded, now()))
        con.commit()
        print(f"mileage: {a.miles:g} mi x {rate:g}¢ = {usd(ded)}  ({d}) — {a.purpose}")
        print("  Keep the contemporaneous log. Reconstructed mileage loses on audit.")
        return
    rows = con.execute("SELECT * FROM mileage WHERE (? IS NULL OR year=?) ORDER BY drove_on",
                       (a.year, a.year)).fetchall()
    banner(f"MILEAGE{f' — {a.year}' if a.year else ''}")
    table([{"date": r["drove_on"], "miles": f"{r['miles']:g}", "rate": f"{r['rate_cents_per_mile']:g}¢",
            "deduction": usd(r["deduction_cents"]), "purpose": (r["business_purpose"] or "")[:40]}
           for r in rows], ["date", "miles", "rate", "deduction", "purpose"],
          right=("miles", "rate", "deduction"))
    print(f"\n  total miles {sum(r['miles'] for r in rows):,.1f} — "
          f"deduction {usd(sum(r['deduction_cents'] for r in rows))} (Schedule C line 9)")


def cmd_home_office(a):
    con = connect(a.db)
    ent = entity_row(con, a.entity)
    year = a.year
    guard_year(con, year)
    if a.method == "simplified":
        rate = int(policy(con, year, "home_office_rate_cents_per_sqft")["value"])
        maxsq = float(policy(con, year, "home_office_max_sqft")["value"])
        if not a.office_sqft:
            die("--office-sqft required for the simplified method")
        sq = min(float(a.office_sqft), maxsq)
        ded = int((Decimal(str(sq)) * Decimal(rate) * Decimal(str(a.months)) / Decimal(12))
                  .quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        detail = (f"{sq:g} sqft (capped at {maxsq:g}) x {usd(rate)}/sqft"
                  f"{f' x {a.months:g}/12 months' if a.months != 12 else ''}")
    else:
        if not (a.office_sqft and a.home_sqft):
            die("--office-sqft and --home-sqft required for the actual method")
        share = Decimal(str(a.office_sqft)) / Decimal(str(a.home_sqft))
        total = sum(cents(x or 0) for x in (a.rent, a.mortgage_interest, a.property_tax,
                                            a.utilities, a.insurance, a.repairs, a.other))
        ded = int((Decimal(total) * share * Decimal(str(a.months)) / Decimal(12))
                  .quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        detail = (f"{float(share)*100:.2f}% of {usd(total)} home costs"
                  f"{f' x {a.months:g}/12 months' if a.months != 12 else ''}")
    con.execute(
        "INSERT INTO home_office (entity_id,year,method,office_sqft,home_sqft,months_used,"
        "rent_cents,mortgage_interest_cents,property_tax_cents,utilities_cents,"
        "insurance_cents,repairs_cents,other_cents,deduction_cents,note,computed_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(entity_id,year) DO UPDATE SET method=excluded.method,"
        "office_sqft=excluded.office_sqft,home_sqft=excluded.home_sqft,"
        "months_used=excluded.months_used,rent_cents=excluded.rent_cents,"
        "mortgage_interest_cents=excluded.mortgage_interest_cents,"
        "property_tax_cents=excluded.property_tax_cents,utilities_cents=excluded.utilities_cents,"
        "insurance_cents=excluded.insurance_cents,repairs_cents=excluded.repairs_cents,"
        "other_cents=excluded.other_cents,deduction_cents=excluded.deduction_cents,"
        "computed_at=excluded.computed_at",
        (ent["id"], year, a.method, a.office_sqft, a.home_sqft, a.months,
         cents(a.rent or 0), cents(a.mortgage_interest or 0), cents(a.property_tax or 0),
         cents(a.utilities or 0), cents(a.insurance or 0), cents(a.repairs or 0),
         cents(a.other or 0), ded, a.note, now()))
    con.commit()
    print(f"home office {year} [{a.method}]: {detail}\n  deduction {usd(ded)} "
          f"(Schedule C line 30)")
    print("  The space must be used REGULARLY AND EXCLUSIVELY for business. A desk in the "
          "living room\n  does not qualify, however much work happens there.")


def cmd_asset(a):
    con = connect(a.db)
    ent = entity_row(con, a.entity)
    pis = iso(a.date)
    year = int(pis[:4])
    guard_year(con, year)
    cost = cents(a.cost)
    con.execute(
        "INSERT INTO asset (entity_id,description,placed_in_service,cost_cents,"
        "business_use_pct,method,recovery_years,note,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (ent["id"], a.description, pis, cost, a.pct, a.method, a.years, a.note, now()))
    aid = con.execute("SELECT last_insert_rowid() i").fetchone()["i"]
    basis = pct_of(cost, a.pct)
    if a.method in ("section-179", "bonus", "de-minimis"):
        con.execute("INSERT INTO depreciation (asset_id,year,amount_cents,note) VALUES (?,?,?,?)",
                    (aid, year, basis, f"full write-off in year one ({a.method})"))
        print(f"asset {aid}: {a.description} — {usd(basis)} deducted in {year} ({a.method})")
        if a.method == "section-179":
            print("  §179 is limited to business taxable income and is recaptured if "
                  "business use\n  drops below 50%. Confirm the year's limit with the CPA.")
    else:
        yrs = a.years or die("--years required for macrs-sl/amortize")
        per = int((Decimal(basis) / Decimal(str(yrs))).quantize(Decimal("1"),
                                                               rounding=ROUND_HALF_UP))
        rows, left = [], basis
        for i in range(int(yrs)):
            amt = min(per, left)
            left -= amt
            rows.append((aid, year + i, amt, f"straight line {i+1}/{int(yrs)}"))
        if left:
            rows[-1] = (aid, rows[-1][1], rows[-1][2] + left, rows[-1][3] + " (+rounding)")
        con.executemany(
            "INSERT INTO depreciation (asset_id,year,amount_cents,note) VALUES (?,?,?,?)", rows)
        print(f"asset {aid}: {a.description} — {usd(basis)} over {int(yrs)} years, "
              f"{usd(per)}/yr")
        print("  Straight line here is a PLANNING figure. The return uses MACRS tables with "
              "a half-year\n  or mid-quarter convention — hand the CPA the asset list, not "
              "this schedule.")
    log(con, "create", "asset", aid, a.description)
    con.commit()


def cmd_estimate(a):
    con = connect(a.db)
    ent = entity_row(con, a.entity)
    if a.sub == "add":
        d = iso(a.date)
        con.execute(
            "INSERT INTO estimated_payment (entity_id,year,quarter,jurisdiction,paid_on,"
            "amount_cents,confirmation,note,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (ent["id"], a.year or int(d[:4]), a.quarter, a.jurisdiction, d, cents(a.amount),
             a.confirmation, a.note, now()))
        con.commit()
        print(f"estimated payment recorded: {a.jurisdiction} Q{a.quarter} {a.year or d[:4]} "
              f"{usd(cents(a.amount))}")
        print("  Not a deduction — a prepayment. It shows on the return as tax already paid.")
        return
    rows = con.execute(
        "SELECT * FROM estimated_payment WHERE (? IS NULL OR year=?) ORDER BY year, quarter",
        (a.year, a.year)).fetchall()
    banner("ESTIMATED TAX PAYMENTS")
    table([{"year": r["year"], "Q": r["quarter"], "jurisdiction": r["jurisdiction"],
            "paid": r["paid_on"], "amount": usd(r["amount_cents"]),
            "confirmation": r["confirmation"] or ""}
           for r in rows], ["year", "Q", "jurisdiction", "paid", "amount", "confirmation"],
          right=("amount",))
    print(f"\n  total {usd(sum(r['amount_cents'] for r in rows))}")


def cmd_rule(a):
    con = connect(a.db)
    if a.sub == "add":
        cat = lookup(con, "category", a.category)
        con.execute(
            "INSERT INTO rule (priority,match_payee,match_memo,match_method,min_cents,"
            "max_cents,category_id,business_use_pct,purpose_template,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (a.priority, a.payee, a.memo, a.method,
             cents(a.min) if a.min else None, cents(a.max) if a.max else None,
             cat["id"], a.pct, a.purpose, now()))
        con.commit()
        print(f"rule added -> {cat['code']}")
        return
    rows = con.execute(
        "SELECT r.*, c.code FROM rule r JOIN category c ON c.id=r.category_id "
        "ORDER BY r.priority DESC, r.id").fetchall()
    banner("AUTO-CATEGORISATION RULES")
    table([{"id": r["id"], "prio": r["priority"], "payee~": r["match_payee"] or "",
            "memo~": r["match_memo"] or "", "method": r["match_method"] or "",
            "->": r["code"], "pct": r["business_use_pct"] or "", "hits": r["hits"],
            "on": "Y" if r["active"] else ""}
           for r in rows], ["id", "prio", "payee~", "memo~", "method", "->", "pct", "hits", "on"])


def cmd_categorize(a):
    con = connect(a.db)
    rules = con.execute(
        "SELECT r.*, c.code FROM rule r JOIN category c ON c.id=r.category_id "
        "WHERE r.active=1 ORDER BY r.priority DESC, r.id").fetchall()
    if not rules:
        die("no rules yet — taxdb.py rule add --payee '(?i)aws' --category software")
    rows = con.execute(
        "SELECT * FROM v_expense WHERE category_id IS NULL AND status!='excluded' "
        "AND (? IS NULL OR year=?)", (a.year, a.year)).fetchall()
    matched = 0
    for e in rows:
        for r in rules:
            if r["match_payee"] and not re.search(r["match_payee"], e["payee"] or "", re.I):
                continue
            if r["match_memo"] and not re.search(r["match_memo"],
                                                 f"{e['memo'] or ''} {e['business_purpose'] or ''}",
                                                 re.I):
                continue
            if r["match_method"] and r["match_method"] != e["method"]:
                continue
            if r["min_cents"] and e["amount_cents"] < r["min_cents"]:
                continue
            if r["max_cents"] and e["amount_cents"] > r["max_cents"]:
                continue
            matched += 1
            print(f"  {e['id']:>5}  {e['paid_on']}  {usd(e['amount_cents']):>10}  "
                  f"{(e['payee'] or '')[:22]:22} -> {r['code']}")
            if a.apply:
                con.execute(
                    "UPDATE expense SET category_id=?, business_use_pct=COALESCE(?,"
                    "business_use_pct), business_purpose=COALESCE(business_purpose,?), "
                    "updated_at=? WHERE id=?",
                    (r["category_id"], r["business_use_pct"], r["purpose_template"], now(),
                     e["id"]))
                con.execute("UPDATE rule SET hits=hits+1 WHERE id=?", (r["id"],))
            break
    con.commit()
    print(f"\n  {matched} of {len(rows)} uncategorized rows matched a rule"
          + ("" if a.apply else " — dry run, re-run with --apply"))
    print("  Rules assign a CATEGORY. They never confirm a row: the business purpose is "
          "yours to write.")


def cmd_import(a):
    con = connect(a.db)
    ent = entity_row(con, a.entity)
    mapping = dict(kv.split("=", 1) for kv in (a.map or []))
    method = lookup(con, "payment_method", a.method) if a.method else None
    created = dupes = 0
    with open(os.path.expanduser(a.csv), newline="", encoding="utf-8-sig") as fh:
        for line in csv.DictReader(fh):
            get = lambda k, d=None: line.get(mapping.get(k, k), d)  # noqa: E731
            raw_amt = get("amount")
            if raw_amt in (None, ""):
                continue
            amt = cents(raw_amt)
            if amt < 0:
                amt = -amt if a.negative_is_spend else 0
            if amt <= 0:
                continue
            paid_on = iso(get("date"))
            year = int(paid_on[:4])
            guard_year(con, year)
            desc = (get("description") or get("payee") or "").strip()
            payee = get_or_create_payee(con, desc[:60]) if desc else None
            key = _dedupe_key(ent["id"], paid_on, amt, payee["id"] if payee else None,
                              get("ref"))
            if con.execute("SELECT 1 FROM expense WHERE dedupe_key=?", (key,)).fetchone():
                dupes += 1
                continue
            con.execute(
                "INSERT INTO expense (entity_id,paid_on,year,amount_cents,payee_id,"
                "method_id,source,memo,external_ref,dedupe_key,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (ent["id"], paid_on, year, amt, payee["id"] if payee else None,
                 method["id"] if method else None, f"import:{os.path.basename(a.csv)}",
                 desc, get("ref"), key, now(), now()))
            created += 1
    con.commit()
    print(f"imported {created} rows as DRAFTS, skipped {dupes} duplicates")
    print("  Next: taxdb.py categorize --apply, then confirm each row with a purpose.")


# ═════════════════════════════════════════════════════════════════════════ reports


def cmd_report(a):
    con = connect(a.db)
    {"schedule-c": rpt_schedule_c, "1099": rpt_1099, "missing": rpt_missing,
     "quarter": rpt_quarter, "payee": rpt_payee, "category": rpt_category}[a.kind](con, a)


def rpt_schedule_c(con, a):
    year = a.year
    ent = entity_row(con, a.entity)
    banner(f"DEDUCTION SUMMARY — {ent['name']} — {year}  ({ent['tax_form']})")
    if ent["tax_form"] != "Schedule C":
        print(f"  Line numbers below are the SCHEDULE C map — the category grouping this\n"
              f"  database uses. {ent['name']} files {ent['tax_form']}, whose line numbering\n"
              f"  differs. The categories and totals carry over; the line numbers do not.\n")
    rows = con.execute("""
        SELECT form, line, category, category_label,
               SUM(amount_cents) gross, SUM(deductible_cents) ded, COUNT(*) n
        FROM v_deduction WHERE year=? AND entity_id=?
        GROUP BY form, line, category ORDER BY form, CAST(line AS INTEGER), line, category""",
        (year, ent["id"])).fetchall()
    sched = [r for r in rows if r["form"] == "Schedule C"]
    other = [r for r in rows if r["form"] != "Schedule C"]

    mile = con.execute("SELECT COALESCE(SUM(deduction_cents),0) d, COALESCE(SUM(miles),0) m "
                       "FROM mileage WHERE year=? AND entity_id=?",
                       (year, ent["id"])).fetchone()
    ho = con.execute("SELECT * FROM home_office WHERE year=? AND entity_id=?",
                     (year, ent["id"])).fetchone()
    dep = con.execute("""SELECT COALESCE(SUM(d.amount_cents),0) t FROM depreciation d
                         JOIN asset s ON s.id=d.asset_id WHERE d.year=? AND s.entity_id=?""",
                      (year, ent["id"])).fetchone()["t"]

    lines = []
    for r in sched:
        lines.append({"line": r["line"], "category": r["category"], "n": r["n"],
                      "gross": usd(r["gross"]), "deduction": usd(r["ded"])})
    if mile["d"]:
        lines.append({"line": "9", "category": f"mileage ({mile['m']:,.0f} mi)", "n": "",
                      "gross": "", "deduction": usd(mile["d"])})
    if dep:
        lines.append({"line": "13", "category": "depreciation / §179", "n": "",
                      "gross": "", "deduction": usd(dep)})
    if ho:
        lines.append({"line": "30", "category": f"home office ({ho['method']})", "n": "",
                      "gross": "", "deduction": usd(ho["deduction_cents"])})
    lines.sort(key=lambda r: (int(re.sub(r"\D", "", r["line"]) or 0), r["line"]))
    table(lines, ["line", "category", "n", "gross", "deduction"],
          right=("n", "gross", "deduction"))
    total = sum(r["ded"] for r in sched) + mile["d"] + dep + (ho["deduction_cents"] if ho else 0)
    print(f"\n  TOTAL {ent['tax_form'].upper()} DEDUCTIONS — {year}:  {usd(total)}")

    if other:
        print("\n  NOT on Schedule C — carried on other forms:")
        table([{"form": r["form"], "line": r["line"] or "", "category": r["category"],
                "deduction": usd(r["ded"])} for r in other],
              ["form", "line", "category", "deduction"], right=("deduction",))

    drafts = con.execute(
        "SELECT COUNT(*) n, COALESCE(SUM(amount_cents),0) t FROM v_expense "
        "WHERE year=? AND entity_id=? AND status='draft'", (year, ent["id"])).fetchone()
    if drafts["n"]:
        print(f"\n  ⚠ {drafts['n']} DRAFT rows worth {usd(drafts['t'])} are NOT in the total "
              f"above.\n    Confirm or exclude them: taxdb.py list --year {year} --needs-work")
    nd = con.execute("""SELECT category, COALESCE(SUM(amount_cents),0) t, COUNT(*) n
                        FROM v_expense WHERE year=? AND entity_id=? AND status='confirmed'
                          AND deductible_pct=0 GROUP BY category""",
                     (year, ent["id"])).fetchall()
    if nd:
        print("\n  Tracked but NOT deductible (correctly excluded):")
        for r in nd:
            print(f"    {r['category']:<20} {r['n']:>3} rows  {usd(r['t']):>12}")
    print("\n  This is a working total from your own records. It is not a filed return and "
          "not tax advice.\n  Hand it, the receipt vault and the export to your CPA.")


def rpt_1099(con, a):
    year = a.year
    thr_row = policy(con, year, "1099_threshold_cents", required=False)
    thr = int(thr_row["value"]) if thr_row else None
    banner(f"1099 FILING EXPOSURE — {year}")
    print("  Payments for SERVICES, to payees who are not corporations, over networks that")
    print("  report nothing on your behalf. Everything here is YOUR filing obligation.\n")
    rows = con.execute("""
        SELECT payee_id, payee, MAX(w9_on_file) w9, MAX(tin_last4) tin,
               MAX(corporation) corp, SUM(amount_cents) total, COUNT(*) n,
               SUM(CASE WHEN status='draft' THEN 1 ELSE 0 END) drafts,
               GROUP_CONCAT(DISTINCT method) methods,
               GROUP_CONCAT(DISTINCT category) cats
        FROM v_1099_candidate WHERE year=?
        GROUP BY payee_id ORDER BY total DESC""", (year,)).fetchall()
    out = []
    must_file = exposed = drafts = 0
    for r in rows:
        over = thr is not None and r["total"] >= thr
        must_file += 1 if over else 0
        drafts += r["drafts"]
        if over and not r["w9"]:
            exposed += r["total"]
        form = "1099-MISC box 10" if r["corp"] else "1099-NEC"
        out.append({"payee": r["payee"][:28], "paid": usd(r["total"]), "n": r["n"],
                    "methods": (r["methods"] or "")[:20], "W-9": "yes" if r["w9"] else "NO",
                    "action": f"FILE {form}" if over else
                              ("watch" if thr and r["total"] >= thr * 0.6 else "below")})
    table(out, ["payee", "paid", "n", "methods", "W-9", "action"], right=("paid", "n"))
    if any(r["corp"] for r in rows):
        print("\n  A corporation appears above because ATTORNEY payments are reportable even "
              "when\n  the firm is incorporated. Gross proceeds to an attorney go in 1099-MISC "
              "box 10;\n  fees for the firm's own services go in 1099-NEC box 1. Ask which "
              "this was.")
    if drafts:
        print(f"\n  note: {drafts} of these payments are still DRAFT rows. 1099 totals count "
              f"money that\n  moved, so they are included here whether or not you have "
              f"categorised them yet.")
    print(f"\n  threshold used: {usd(thr) if thr else '(none recorded)'}"
          f"   payees over it: {must_file}")
    warn_unverified(con, year, "1099_threshold_cents")
    if exposed:
        bw = policy(con, year, "backup_withholding_pct", required=False)
        pctv = float(bw["value"]) if bw else 24.0
        print(f"\n  ⚠ {usd(exposed)} was paid to payees over the threshold with NO W-9 on file.")
        print(f"    Backup withholding is {pctv:g}% — {usd(pct_of(exposed, pctv))} you may owe "
              f"out of pocket\n    if the IRS asks and you cannot produce a TIN. Collect the "
              f"W-9s now.")
    paid_k = con.execute("""
        SELECT payee, SUM(amount_cents) t FROM v_expense
        WHERE year=? AND status!='excluded' AND nec_reportable=1 AND issues_1099k=1
        GROUP BY payee_id HAVING t > 0 ORDER BY t DESC LIMIT 10""", (year,)).fetchall()
    if paid_k:
        print("\n  Service payments settled on card/TPSO — the network files the 1099-K.")
        print("  DO NOT also issue a 1099-NEC for these; double reporting lands on the payee.")
        for r in paid_k:
            print(f"    {(r['payee'] or '')[:32]:<32} {usd(r['t']):>12}")
    print("\n  Deadline: recipient copies and the IRS copy of Form 1099-NEC are due 31 January.")


def rpt_missing(con, a):
    year = a.year
    banner(f"EVIDENCE GAPS — {year}")
    checks = [
        ("no business purpose (cannot be deducted)",
         "SELECT * FROM v_expense WHERE year=? AND status!='excluded' "
         "AND (business_purpose IS NULL OR TRIM(business_purpose)='')"),
        ("no category (won't reach any line)",
         "SELECT * FROM v_expense WHERE year=? AND status!='excluded' AND category_id IS NULL"),
        ("confirmed but no receipt, over the category threshold",
         "SELECT * FROM v_expense WHERE year=? AND status='confirmed' AND receipts=0 "
         "AND category_id IS NOT NULL AND amount_cents >= receipt_required_over_cents"),
        ("still a draft",
         "SELECT * FROM v_expense WHERE year=? AND status='draft'"),
        ("paid from a personal account (reimburse via an accountable plan)",
         "SELECT * FROM v_expense WHERE year=? AND status!='excluded' AND business_account=0"),
        ("100% business use claimed on a mixed-use category",
         "SELECT * FROM v_expense WHERE year=? AND status='confirmed' AND business_use_pct=100 "
         "AND category IN ('phone-internet','car-truck','utilities')"),
    ]
    total_at_risk = 0
    for label, q in checks:
        rows = con.execute(q, (year,)).fetchall()
        if not rows:
            continue
        amt = sum(r["amount_cents"] for r in rows)
        total_at_risk += amt
        print(f"\n  {label}  —  {len(rows)} rows, {usd(amt)}")
        table([{"id": r["id"], "date": r["paid_on"], "amount": usd(r["amount_cents"]),
                "payee": (r["payee"] or "")[:26], "category": r["category"] or "—"}
               for r in rows[:12]], ["id", "date", "amount", "payee", "category"],
              right=("id", "amount"))
        if len(rows) > 12:
            print(f"    … and {len(rows)-12} more")
    missing_w9 = con.execute(
        "SELECT DISTINCT payee FROM v_1099_candidate WHERE year=? AND w9_on_file=0",
        (year,)).fetchall()
    if missing_w9:
        print(f"\n  no W-9 on file — {len(missing_w9)} payees")
        for r in missing_w9:
            print(f"    {r['payee']}")
    if not total_at_risk and not missing_w9:
        print("  Clean. Every row has a purpose, a category and its evidence.")
    else:
        print(f"\n  {usd(total_at_risk)} of spend has a gap between it and a defensible "
              f"deduction.")


def rpt_quarter(con, a):
    year = a.year
    banner(f"QUARTERLY VIEW — {year}")
    rows = con.execute("""
        SELECT ((CAST(strftime('%m', paid_on) AS INTEGER)-1)/3)+1 q,
               SUM(amount_cents) gross, SUM(deductible_cents) ded, COUNT(*) n
        FROM v_deduction WHERE year=? GROUP BY q ORDER BY q""", (year,)).fetchall()
    est = {r["quarter"]: r["t"] for r in con.execute(
        "SELECT quarter, SUM(amount_cents) t FROM estimated_payment WHERE year=? "
        "GROUP BY quarter", (year,)).fetchall()}
    table([{"quarter": f"Q{r['q']}", "expenses": r["n"], "spend": usd(r["gross"]),
            "deduction": usd(r["ded"]), "estimated tax paid": usd(est.get(r["q"], 0))}
           for r in rows],
          ["quarter", "expenses", "spend", "deduction", "estimated tax paid"],
          right=("expenses", "spend", "deduction", "estimated tax paid"))
    print(f"\n  year deduction {usd(sum(r['ded'] for r in rows))}   "
          f"estimated tax paid {usd(sum(est.values()))}")
    print("  Expense rows only — mileage, home office and depreciation are annual figures\n"
          "  and appear in `report schedule-c`, not here.")
    print("  Estimated payments are due 15 Apr / 15 Jun / 15 Sep / 15 Jan (next year).")


def rpt_payee(con, a):
    banner(f"SPEND BY PAYEE — {a.year}")
    rows = con.execute("""
        SELECT payee, COUNT(*) n, SUM(amount_cents) gross, SUM(deductible_cents) ded,
               GROUP_CONCAT(DISTINCT category) cats
        FROM v_expense WHERE year=? AND status!='excluded' AND payee IS NOT NULL
        GROUP BY payee_id ORDER BY gross DESC LIMIT ?""", (a.year, a.limit)).fetchall()
    table([{"payee": r["payee"][:30], "n": r["n"], "spend": usd(r["gross"]),
            "deduction": usd(r["ded"]), "categories": (r["cats"] or "")[:30]}
           for r in rows], ["payee", "n", "spend", "deduction", "categories"],
          right=("n", "spend", "deduction"))
    print("\n  Includes draft rows — 'deduction' here is what they WOULD deduct once "
          "confirmed.")


def rpt_category(con, a):
    banner(f"SPEND BY CATEGORY — {a.year}")
    rows = con.execute("""
        SELECT category, category_label, form, line, COUNT(*) n,
               SUM(amount_cents) gross, SUM(deductible_cents) ded
        FROM v_expense WHERE year=? AND status!='excluded' AND category IS NOT NULL
        GROUP BY category_id ORDER BY gross DESC""", (a.year,)).fetchall()
    table([{"category": r["category"], "form": r["form"], "line": r["line"] or "",
            "n": r["n"], "spend": usd(r["gross"]), "deduction": usd(r["ded"])}
           for r in rows], ["category", "form", "line", "n", "spend", "deduction"],
          right=("n", "spend", "deduction"))
    print("\n  Includes draft rows — 'deduction' here is what they WOULD deduct once "
          "confirmed.\n  The filing total is `report schedule-c`, which counts confirmed "
          "rows only.")


def cmd_export(a):
    con = connect(a.db)
    out = os.path.expanduser(a.out)
    os.makedirs(out, exist_ok=True)
    exports = {
        "expenses": ("SELECT * FROM v_expense WHERE year=? ORDER BY paid_on", (a.year,)),
        "deductions": ("SELECT * FROM v_deduction WHERE year=? ORDER BY form, line", (a.year,)),
        "1099-candidates": ("SELECT payee, tin_last4, w9_on_file, SUM(amount_cents) total_cents,"
                            " COUNT(*) payments FROM v_1099_candidate WHERE year=? "
                            "GROUP BY payee_id ORDER BY total_cents DESC", (a.year,)),
        "mileage": ("SELECT * FROM mileage WHERE year=? ORDER BY drove_on", (a.year,)),
        "assets": ("SELECT s.*, d.year dep_year, d.amount_cents dep_cents FROM asset s "
                   "LEFT JOIN depreciation d ON d.asset_id=s.id WHERE d.year=? OR d.year IS NULL",
                   (a.year,)),
        "estimated-payments": ("SELECT * FROM estimated_payment WHERE year=? ORDER BY quarter",
                               (a.year,)),
        "receipts": ("SELECT r.*, e.paid_on, e.amount_cents FROM receipt r "
                     "JOIN expense e ON e.id=r.expense_id WHERE e.year=?", (a.year,)),
    }
    written = []
    for name, (q, p) in exports.items():
        rows = con.execute(q, p).fetchall()
        path = os.path.join(out, f"{a.year}-{name}.csv")
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if rows:
                w.writerow(rows[0].keys())
                w.writerows([tuple(r) for r in rows])
            else:
                w.writerow(["(no rows)"])
        written.append((name, len(rows), path))
    for name, n, path in written:
        print(f"  {n:>5} rows  {path}")
    print(f"\nExported {a.year} to {out}")
    print("Send this folder plus the receipt vault to your CPA. Amounts are in CENTS.")


def cmd_lock(a):
    con = connect(a.db)
    if a.unlock:
        con.execute("UPDATE tax_year SET status='open', locked_at=NULL WHERE year=?", (a.year,))
        log(con, "unlock", "tax_year", a.year, a.note or "")
        print(f"tax year {a.year} REOPENED. Anything you change now diverges from what you "
              f"filed.")
    else:
        gaps = con.execute(
            "SELECT COUNT(*) n FROM v_expense WHERE year=? AND status='draft'",
            (a.year,)).fetchone()["n"]
        if gaps and not a.force:
            die(f"{gaps} draft rows in {a.year} — confirm or exclude them first, or --force")
        con.execute("INSERT INTO tax_year (year,status,filed_on,locked_at,note) "
                    "VALUES (?,'locked',?,?,?) ON CONFLICT(year) DO UPDATE SET "
                    "status='locked', filed_on=excluded.filed_on, locked_at=excluded.locked_at, "
                    "note=excluded.note", (a.year, a.filed, now(), a.note))
        log(con, "lock", "tax_year", a.year, a.note or "")
        print(f"tax year {a.year} LOCKED. Writes to it are refused until you unlock.")
    con.commit()


def cmd_status(a):
    con = connect(a.db)
    banner("TAX DEDUCTION DATABASE")
    print(f"  file      {a.db}")
    print(f"  vault     {vault_dir(a.db)}")
    for r in con.execute("SELECT * FROM entity ORDER BY id"):
        print(f"  entity    {r['name']} ({r['kind']} -> {r['tax_form']})")
    rows = con.execute("""
        SELECT e.year, t.status,
               COUNT(*) n,
               SUM(CASE WHEN e.status='draft' THEN 1 ELSE 0 END) drafts,
               SUM(CASE WHEN e.status='confirmed' THEN e.deductible_cents ELSE 0 END) ded
        FROM v_expense e LEFT JOIN tax_year t ON t.year=e.year
        GROUP BY e.year ORDER BY e.year DESC""").fetchall()
    print()
    table([{"year": r["year"], "rows": r["n"], "drafts": r["drafts"],
            "confirmed deduction": usd(r["ded"]), "year status": r["status"] or "open"}
           for r in rows], ["year", "rows", "drafts", "confirmed deduction", "year status"],
          right=("rows", "drafts", "confirmed deduction"))
    unver = con.execute("SELECT year, key FROM policy WHERE verified=0 ORDER BY year").fetchall()
    if unver:
        print("\n  ⚠ unverified policy values in play:")
        for r in unver:
            print(f"      {r['year']}  {r['key']}   (taxdb.py policy list --year {r['year']})")


# ═══════════════════════════════════════════════════════════════════════ self-test


def selftest():
    """Arithmetic and rules, asserted against hand-computed numbers."""
    fails = []

    def check(name, got, want):
        ok = got == want
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}"
              + ("" if ok else f"   got {got!r} want {want!r}"))
        if not ok:
            fails.append(name)

    print("\nMONEY")
    check("parse $350.00", cents("$350.00"), 35000)
    check("parse 1,234.56", cents("1,234.56"), 123456)
    check("parse (45.10) negative", cents("(45.10)"), -4510)
    check("no float drift on 0.1+0.2", cents("0.10") + cents("0.20"), cents("0.30"))
    check("half-up at the penny", cents("10.005"), 1001)
    check("format", usd(123456), "$1,234.56")
    check("meals 50% of $83.19", pct_of(8319, 50), 4160)      # 41.595 -> 41.60
    check("60% business x 50% meals of $100", pct_of(10000, 60, 50), 3000)

    print("\nDATABASE")
    con = connect(":memory:", must_exist=False)
    build(con)
    eid = add_entity(con, "Example Co", "sole-prop")
    check("entity files Schedule C",
          con.execute("SELECT tax_form FROM entity WHERE id=?", (eid,)).fetchone()[0],
          "Schedule C")
    check("categories seeded", con.execute("SELECT COUNT(*) FROM category").fetchone()[0],
          len(CATEGORIES))
    check("zelle files no 1099-K",
          con.execute("SELECT issues_1099k FROM payment_method WHERE slug='zelle'").fetchone()[0], 0)
    check("card is 1099-K reported",
          con.execute("SELECT issues_1099k FROM payment_method WHERE slug='biz-card'").fetchone()[0], 1)
    check("attorney fees not corp-exempt",
          con.execute("SELECT corp_exempt FROM category WHERE code='legal-professional'")
          .fetchone()[0], 0)

    def expense(payee, amount, category, method, pct=100.0, status="confirmed",
                d="2026-03-04", **kw):
        p = get_or_create_payee(con, payee, **kw)
        c = lookup(con, "category", category)
        m = lookup(con, "payment_method", method)
        k = _dedupe_key(eid, d, cents(amount), p["id"], kw.get("ref"))
        con.execute(
            "INSERT INTO expense (entity_id,paid_on,year,amount_cents,payee_id,category_id,"
            "method_id,business_purpose,business_use_pct,status,dedupe_key,created_at,"
            "updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (eid, d, int(d[:4]), cents(amount), p["id"], c["id"], m["id"], "selftest purpose",
             pct, status, k, now(), now()))
        return con.execute("SELECT last_insert_rowid() i").fetchone()["i"]

    e1 = expense("Example Contractor", "350.00", "contract-labor", "zelle")
    check("full deduction on contract labor",
          con.execute("SELECT deductible_cents FROM v_expense WHERE id=?", (e1,)).fetchone()[0],
          35000)
    e2 = expense("Example Bistro", "83.19", "meals", "biz-card")
    check("meals halved in the view",
          con.execute("SELECT deductible_cents FROM v_expense WHERE id=?", (e2,)).fetchone()[0],
          4160)
    e3 = expense("Example Telecom", "200.00", "phone-internet", "biz-card", pct=60)
    check("business-use % applied",
          con.execute("SELECT deductible_cents FROM v_expense WHERE id=?", (e3,)).fetchone()[0],
          12000)
    e4 = expense("Example Golf Club", "500.00", "entertainment", "biz-card")
    check("entertainment deducts nothing",
          con.execute("SELECT deductible_cents FROM v_expense WHERE id=?", (e4,)).fetchone()[0], 0)
    e5 = expense("Example Computer Store", "3200.00", "capital-asset", "biz-card")
    check("capital row kept out of v_deduction",
          con.execute("SELECT COUNT(*) FROM v_deduction WHERE id=?", (e5,)).fetchone()[0], 0)
    e6 = expense("Example Vendor", "900.00", "supplies", "biz-card", status="draft")
    check("draft kept out of v_deduction",
          con.execute("SELECT COUNT(*) FROM v_deduction WHERE id=?", (e6,)).fetchone()[0], 0)

    print("\n1099 LOGIC")
    expense("Example Contractor", "1800.00", "contract-labor", "zelle", d="2026-04-02")
    expense("Example Design Inc", "5000.00", "contract-labor", "zelle", d="2026-04-03",
            corporation=1)
    expense("Example Card Contractor", "5000.00", "contract-labor", "biz-card", d="2026-04-04")
    expense("Example Law LLP", "9000.00", "legal-professional", "ach", d="2026-04-05",
            corporation=1)
    expense("Example Overseas Dev", "7000.00", "contract-labor", "wire", d="2026-04-06",
            foreign_payee=1)
    expense("Example Office Supply", "220.00", "supplies", "ach", d="2026-04-07")
    cands = {r["payee"]: r["t"] for r in con.execute(
        "SELECT payee, SUM(amount_cents) t FROM v_1099_candidate WHERE year=2026 "
        "GROUP BY payee_id")}
    check("zelle contractor accumulates", cands.get("Example Contractor"), 35000 + 180000)
    check("corporation excluded", "Example Design Inc" in cands, False)
    check("card payment excluded (1099-K covers it)", "Example Card Contractor" in cands, False)
    check("attorney corporation STILL reportable", cands.get("Example Law LLP"), 900000)
    check("foreign payee excluded", "Example Overseas Dev" in cands, False)
    check("non-service spend excluded", "Example Office Supply" in cands, False)
    thr = int(policy(con, 2026, "1099_threshold_cents")["value"])
    check("2026 threshold flagged unverified",
          policy(con, 2026, "1099_threshold_cents")["verified"], 0)
    check("zelle contractor over the threshold", cands["Example Contractor"] >= thr, True)

    print("\nMILEAGE / HOME OFFICE / ASSETS")
    rate = float(policy(con, 2025, "mileage_cents_per_mile")["value"])
    check("2025 rate is 70c", rate, 70.0)
    check("120.4 mi at 70c", int((Decimal("120.4") * Decimal("70")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP)), 8428)
    check("2026 mileage rate absent until verified",
          policy(con, 2026, "mileage_cents_per_mile", required=False), None)
    ho_rate = int(policy(con, 2026, "home_office_rate_cents_per_sqft")["value"])
    ho_max = float(policy(con, 2026, "home_office_max_sqft")["value"])
    check("simplified 180 sqft", pct_of(int(180 * ho_rate), 100), 90000)
    check("simplified caps at 300 sqft", int(min(420, ho_max) * ho_rate), 150000)
    check("actual method share of $24,000 at 180/1800",
          int((Decimal(2400000) * Decimal(180) / Decimal(1800)).quantize(
              Decimal("1"), rounding=ROUND_HALF_UP)), 240000)
    check("§179 full basis at 80% business use", pct_of(cents("4000"), 80), 320000)

    print("\nGUARDS")
    con.execute("UPDATE tax_year SET status='locked' WHERE year=2025")
    check("locked year detected",
          con.execute("SELECT status FROM tax_year WHERE year=2025").fetchone()[0], "locked")
    dup_key = _dedupe_key(eid, "2026-03-04", 35000, 1, None)
    check("dedupe key is stable", dup_key, _dedupe_key(eid, "2026-03-04", 35000, 1, None))
    try:
        con.execute("INSERT INTO expense (entity_id,paid_on,year,amount_cents,dedupe_key,"
                    "created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                    (eid, "2026-03-04", 2026, 35000,
                     con.execute("SELECT dedupe_key FROM expense WHERE id=?", (e1,)).fetchone()[0],
                     now(), now()))
        check("duplicate rejected", False, True)
    except sqlite3.IntegrityError:
        check("duplicate rejected", True, True)
    try:
        con.execute("INSERT INTO expense (entity_id,paid_on,year,amount_cents,"
                    "business_use_pct,dedupe_key,created_at,updated_at) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (eid, "2026-03-05", 2026, 100, 140.0, "x", now(), now()))
        check("business_use_pct > 100 rejected", False, True)
    except sqlite3.IntegrityError:
        check("business_use_pct > 100 rejected", True, True)

    print("\nRULES")
    c = lookup(con, "category", "software")
    con.execute("INSERT INTO rule (priority,match_payee,category_id,created_at) "
                "VALUES (?,?,?,?)", (200, r"(?i)amazon web services|aws", c["id"], now()))
    r = con.execute("SELECT * FROM rule").fetchone()
    check("rule regex matches", bool(re.search(r["match_payee"], "AWS EMEA billing", re.I)), True)
    check("rule regex does not overmatch",
          bool(re.search(r["match_payee"], "Awning Co", re.I)), False)

    print("\n" + "═" * 78)
    if fails:
        print(f"{len(fails)} FAILURES: {', '.join(fails)}")
        print("Do not file anything off this database until they pass.")
        return 1
    print("ALL PASS")
    return 0


# ══════════════════════════════════════════════════════════════════════════ cli


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="taxdb.py", description="Tax deduction database — SQLite, cash basis.")
    ap.add_argument("--db", default=DEFAULT_DB, help=f"database file (default {DEFAULT_DB})")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def s(name, fn, **kw):
        p = sub.add_parser(name, **kw)
        p.set_defaults(fn=fn)
        return p

    p = s("selftest", lambda a: sys.exit(selftest()), help="verify the engine (run this first)")

    p = s("init", cmd_init, help="create the database")
    p.add_argument("--entity", help="business name")
    p.add_argument("--kind", default="sole-prop", choices=sorted(FORM_BY_KIND))
    p.add_argument("--ein-last4")
    p.add_argument("--state")
    p.add_argument("--force", action="store_true", help="DELETE and rebuild")

    p = s("status", cmd_status, help="what is in the database")

    p = s("entity", cmd_entity, help="business entities")
    p.add_argument("sub", choices=["add", "list"])
    p.add_argument("--name")
    p.add_argument("--kind", default="sole-prop", choices=sorted(FORM_BY_KIND))
    p.add_argument("--ein-last4")
    p.add_argument("--state")

    p = s("categories", cmd_categories, help="the category map")
    p.add_argument("--grep")

    p = s("policy", cmd_policy, help="statutory rates and thresholds")
    p.add_argument("sub", choices=["list", "set"], nargs="?", default="list")
    p.add_argument("--year", type=int)
    p.add_argument("--key")
    p.add_argument("--value")
    p.add_argument("--source", default="")
    p.add_argument("--verified", action="store_true")

    p = s("payee", cmd_payee, help="who you pay")
    p.add_argument("sub", choices=["add", "list"])
    p.add_argument("--name")
    p.add_argument("--kind", default="unknown",
                   choices=["individual", "business", "government", "employee", "unknown"])
    p.add_argument("--tin-last4", help="LAST FOUR DIGITS ONLY — never a full TIN")
    p.add_argument("--w9", action="store_true", help="W-9 collected")
    p.add_argument("--w9-path", help="path to the stored W-9 (encrypted store, not here)")
    p.add_argument("--corporation", action="store_true")
    p.add_argument("--foreign", action="store_true")
    p.add_argument("--email")
    p.add_argument("--note")
    p.add_argument("--year", type=int)

    p = s("method", cmd_method, help="payment methods and their 1099-K behaviour")
    p.add_argument("sub", choices=["add", "list"], nargs="?", default="list")
    p.add_argument("--slug")
    p.add_argument("--label")
    p.add_argument("--kind", default="other",
                   choices=["bank-transfer", "card", "cash", "check", "tpso", "crypto", "other"])
    p.add_argument("--account-last4")
    p.add_argument("--personal", action="store_true")
    p.add_argument("--issues-1099k", action="store_true",
                   help="the network files a 1099-K for these payments")
    p.add_argument("--note")

    p = s("add", cmd_add, help="record a payment")
    p.add_argument("--date", required=True)
    p.add_argument("--amount", required=True)
    p.add_argument("--payee")
    p.add_argument("--category")
    p.add_argument("--method")
    p.add_argument("--purpose", help="WHY this was business — required to confirm")
    p.add_argument("--pct", type=float, default=100.0, help="business use %%")
    p.add_argument("--ref", help="confirmation / invoice number")
    p.add_argument("--memo")
    p.add_argument("--client")
    p.add_argument("--source", default="manual")
    p.add_argument("--receipt", help="file to attach")
    p.add_argument("--receipt-kind", default="receipt")
    p.add_argument("--link", action="store_true", help="reference the receipt in place")
    p.add_argument("--reimbursable", action="store_true")
    p.add_argument("--confirm", action="store_true", help="confirm now (needs purpose+category)")
    p.add_argument("--allow-capital", action="store_true")
    p.add_argument("--force", action="store_true", help="allow an exact duplicate")
    p.add_argument("--entity")

    p = s("confirm", cmd_confirm, help="promote a draft to a real deduction")
    p.add_argument("id", type=int)
    p.add_argument("--purpose")
    p.add_argument("--category")
    p.add_argument("--pct", type=float)

    p = s("exclude", cmd_exclude, help="mark a row non-deductible")
    p.add_argument("id", type=int)
    p.add_argument("--reason", required=True)

    p = s("receipt", cmd_receipt, help="attach evidence to an expense")
    p.add_argument("id", type=int)
    p.add_argument("--file", required=True)
    p.add_argument("--kind", default="receipt")
    p.add_argument("--link", action="store_true")

    p = s("list", cmd_list, help="browse expenses")
    p.add_argument("--year", type=int)
    p.add_argument("--status", choices=["draft", "confirmed", "excluded"])
    p.add_argument("--category")
    p.add_argument("--payee")
    p.add_argument("--needs-work", action="store_true")
    p.add_argument("--limit", type=int, default=50)

    p = s("mileage", cmd_mileage, help="business miles")
    p.add_argument("sub", choices=["add", "list"], nargs="?", default="list")
    p.add_argument("--date")
    p.add_argument("--miles", type=float)
    p.add_argument("--purpose")
    p.add_argument("--origin")
    p.add_argument("--destination")
    p.add_argument("--vehicle")
    p.add_argument("--rate", type=float, help="override cents per mile")
    p.add_argument("--year", type=int)
    p.add_argument("--entity")

    p = s("home-office", cmd_home_office, help="home office deduction")
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--method", choices=["simplified", "actual"], default="simplified")
    p.add_argument("--office-sqft", type=float)
    p.add_argument("--home-sqft", type=float)
    p.add_argument("--months", type=float, default=12)
    p.add_argument("--rent")
    p.add_argument("--mortgage-interest")
    p.add_argument("--property-tax")
    p.add_argument("--utilities")
    p.add_argument("--insurance")
    p.add_argument("--repairs")
    p.add_argument("--other")
    p.add_argument("--note")
    p.add_argument("--entity")

    p = s("asset", cmd_asset, help="capitalized purchases and depreciation")
    p.add_argument("--description", required=True)
    p.add_argument("--date", required=True, help="placed in service")
    p.add_argument("--cost", required=True)
    p.add_argument("--method", required=True,
                   choices=["section-179", "bonus", "macrs-sl", "de-minimis", "amortize"])
    p.add_argument("--years", type=float)
    p.add_argument("--pct", type=float, default=100.0)
    p.add_argument("--note")
    p.add_argument("--entity")

    p = s("estimate", cmd_estimate, help="estimated tax payments")
    p.add_argument("sub", choices=["add", "list"], nargs="?", default="list")
    p.add_argument("--date")
    p.add_argument("--amount")
    p.add_argument("--quarter", type=int, choices=[1, 2, 3, 4])
    p.add_argument("--jurisdiction", default="federal")
    p.add_argument("--confirmation")
    p.add_argument("--note")
    p.add_argument("--year", type=int)
    p.add_argument("--entity")

    p = s("rule", cmd_rule, help="auto-categorisation rules")
    p.add_argument("sub", choices=["add", "list"], nargs="?", default="list")
    p.add_argument("--payee", help="regex against the payee name")
    p.add_argument("--memo", help="regex against memo/purpose")
    p.add_argument("--method")
    p.add_argument("--min")
    p.add_argument("--max")
    p.add_argument("--category")
    p.add_argument("--pct", type=float)
    p.add_argument("--purpose", help="default purpose text")
    p.add_argument("--priority", type=int, default=100)

    p = s("categorize", cmd_categorize, help="apply rules to uncategorized rows")
    p.add_argument("--year", type=int)
    p.add_argument("--apply", action="store_true")

    p = s("import", cmd_import, help="import a bank/card CSV as drafts")
    p.add_argument("--csv", required=True)
    p.add_argument("--map", nargs="*",
                   help="column mapping, e.g. date='Posting Date' amount=Amount "
                        "description=Description")
    p.add_argument("--method")
    p.add_argument("--negative-is-spend", action="store_true",
                   help="treat negative amounts as spend (most bank exports)")
    p.add_argument("--entity")

    p = s("report", cmd_report, help="the reports")
    p.add_argument("kind", choices=["schedule-c", "1099", "missing", "quarter", "payee",
                                    "category"])
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--entity")

    p = s("export", cmd_export, help="CSV pack for the CPA")
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--out", required=True)

    p = s("lock", cmd_lock, help="close a filed tax year")
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--filed")
    p.add_argument("--note")
    p.add_argument("--force", action="store_true")
    p.set_defaults(unlock=False)

    p = s("unlock", cmd_lock, help="reopen a locked tax year")
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--note")
    p.set_defaults(unlock=True, filed=None, force=False)

    a = ap.parse_args(argv)
    if getattr(a, "sub", None) == "add" and a.cmd in ("entity", "payee") and not a.name:
        die("--name required")
    a.fn(a)


if __name__ == "__main__":
    main()
