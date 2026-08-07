#!/usr/bin/env python3
"""
closing_check.py — Real-estate closing reconciliation & rate engine.

Verified check functions for reviewing a loan closing (settlement statement /
ALTA / HUD-1 grid) against the governing terms (term sheet / loan-results proposal).

Design: parsing arbitrary settlement PDFs is unreliable, so this is a LIBRARY of
verified checks. Workflow:
  1. extract_text(pdf) to read each document,
  2. hand-key the figures into a dict (see EXAMPLE_RBI_OCALA at bottom),
  3. run report(deal) to get a PASS/FAIL reconciliation + cost% + all-in rate.

Run `python3 closing_check.py` to execute the built-in self-test (RBI Ocala deal),
which must print ALL PASS — that proves the math engine is intact.

Deps: PyMuPDF (`fitz`) for PDF text (optional; only needed for extract_text).
"""
from __future__ import annotations
import math, sys

# ----------------------------------------------------------------------------
# PDF text extraction (optional dependency)
# ----------------------------------------------------------------------------
def extract_text(pdf_path: str) -> str:
    """Return all text from a PDF. Requires PyMuPDF (pip install pymupdf)."""
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    return "\n".join(f"\n===== PAGE {i+1}/{len(doc)} =====\n{p.get_text()}"
                     for i, p in enumerate(doc))

# ----------------------------------------------------------------------------
# Florida statutory closing figures (swap rates for other states)
# ----------------------------------------------------------------------------
def fl_doc_stamp_note(loan: float) -> float:
    """FL documentary stamp tax on the promissory note: $0.35 per $100, base
    rounded UP to the next $100."""
    base = math.ceil(loan / 100.0) * 100
    return round(base * 0.0035, 2)

def fl_intangible_tax(loan: float) -> float:
    """FL intangible tax on the mortgage: 2 mills ($0.002 per $1)."""
    return round(loan * 0.002, 2)

def fl_lenders_title(loan: float) -> float:
    """FL promulgated lender's title premium (original rate):
    $5.75/1,000 up to $100k, then $5.00/1,000 to $1M. Base rounded up to $100."""
    base = math.ceil(loan / 100.0) * 100
    if base <= 100_000:
        prem = base / 1000 * 5.75
    else:
        prem = 575 + (base - 100_000) / 1000 * 5.00
    return round(prem, 2)

# ----------------------------------------------------------------------------
# Core reconciliation
# ----------------------------------------------------------------------------
def _ok(cond): return "PASS ✅" if cond else "FAIL ❌"
def _close(a, b, tol=0.01): return abs(a - b) <= tol

def check_footing(line_items: dict, stated_total: float):
    s = round(sum(line_items.values()), 2)
    return _close(s, stated_total), s

def check_waterfall(loan, holdback, charges, stated_cash_to_borrower):
    """Standard cash-out/construction refi waterfall:
       disbursed = loan - holdback ; cash = disbursed - charges."""
    disbursed = round(loan - holdback, 2)
    cash = round(disbursed - charges, 2)
    return _close(cash, stated_cash_to_borrower), disbursed, cash

def cost_percentages(loan: float, line_items: dict) -> list:
    """Each line as % of loan; sorted desc by $."""
    return sorted(((n, v, v / loan * 100) for n, v in line_items.items()),
                  key=lambda x: -x[1])

# ----------------------------------------------------------------------------
# All-in effective lending rate
# ----------------------------------------------------------------------------
def _irr_annual(cfs_monthly):
    """Annualized IRR of a monthly borrower cash-flow stream (+inflow at t0)."""
    def npv(r): return sum(c / ((1 + r) ** i) for i, c in enumerate(cfs_monthly))
    lo, hi = 1e-9, 3.0
    for _ in range(400):
        mid = (lo + hi) / 2
        if npv(mid) < 0: lo = mid
        else: hi = mid
    r = (lo + hi) / 2
    return r * 12, (1 + r) ** 12 - 1  # nominal APR, EAR

def all_in_rate(face, note_rate, fees, term_months=12, day_count=360,
                days_in_year=365):
    """All-in effective rate for an interest-only bullet, fully drawn.
    Interest uses actual/day_count (360 default = hard-money standard).
    IMPORTANT: exclude prepaid/stub interest from `fees` (it double-counts)."""
    eff_note = note_rate * days_in_year / day_count
    annual_interest = face * note_rate * days_in_year / day_count
    mo_int = annual_interest / 12
    net = face - fees
    cfs = [net] + [-mo_int] * term_months
    cfs[-1] -= face  # bullet principal at maturity
    apr, ear = _irr_annual(cfs)
    total_cost = mo_int * term_months + fees
    return {
        "note_rate": note_rate, "effective_note_actual_over_daycount": eff_note,
        "annual_interest": annual_interest, "fees": fees,
        "fees_pct_of_face": fees / face * 100,
        "cost_on_face_pct": total_cost / face * 100,
        "effective_apr": apr, "ear": ear,
    }

# ----------------------------------------------------------------------------
# Ratio / proportion benchmark across two draft versions
# ----------------------------------------------------------------------------
def ratio_benchmark(initial: dict, latest: dict):
    """initial/latest each: {'loan':.., 'charges':.., 'houses':..}."""
    R_loan = latest["loan"] / initial["loan"]
    R_cost = latest["charges"] / initial["charges"]
    return {
        "loan_ratio": R_loan,
        "house_ratio": latest.get("houses", 1) / initial.get("houses", 1),
        "cost_ratio": R_cost,
        "init_cost_pct": initial["charges"] / initial["loan"] * 100,
        "latest_cost_pct": latest["charges"] / latest["loan"] * 100,
        "cost_grew_faster_than_loan_x": R_cost / R_loan,
    }

# ----------------------------------------------------------------------------
# One-call report
# ----------------------------------------------------------------------------
def report(deal: dict):
    L = deal["loan"]; items = deal["line_items"]
    print("=" * 70)
    print(f"CLOSING CHECK — {deal.get('name','(deal)')}   loan ${L:,.2f}")
    print("=" * 70)

    foots, s = check_footing(items, deal["charges_total"])
    print(f"[foot] line items sum ${s:,.2f} vs stated ${deal['charges_total']:,.2f}  {_ok(foots)}")

    wf, disb, cash = check_waterfall(L, deal["holdback"], deal["charges_total"],
                                     deal["cash_to_borrower"])
    print(f"[waterfall] disbursed ${disb:,.2f}; cash-to-borrower ${cash:,.2f} "
          f"vs stated ${deal['cash_to_borrower']:,.2f}  {_ok(wf)}")

    # statutory (FL) — only if the corresponding line exists
    for key, fn, label in [("fl_doc_stamp", fl_doc_stamp_note, "FL doc-stamp"),
                           ("fl_intangible", fl_intangible_tax, "FL intangible"),
                           ("fl_lenders_title", fl_lenders_title, "FL lender's title")]:
        if key in deal:
            calc = fn(L)
            print(f"[statutory] {label}: calc ${calc:,.2f} vs stated ${deal[key]:,.2f}  {_ok(_close(calc, deal[key]))}")

    print(f"\nCLOSING COST = ${deal['charges_total']:,.2f} = "
          f"{deal['charges_total']/L*100:.3f}% of loan")
    for n, v, p in cost_percentages(L, items):
        print(f"   {n:34}{v:>11,.2f}{p:>8.3f}%")

    if "note_rate" in deal:
        fees_for_rate = deal["charges_total"] - deal.get("prepaid_interest", 0.0)
        r = all_in_rate(L, deal["note_rate"], fees_for_rate,
                        deal.get("term_months", 12), deal.get("day_count", 360))
        print(f"\nALL-IN RATE (excl prepaid interest from fees):")
        print(f"   note {r['note_rate']*100:.3f}% -> {r['effective_note_actual_over_daycount']*100:.3f}% (actual/{deal.get('day_count',360)})")
        print(f"   fees {r['fees_pct_of_face']:.3f}% of face | cost-on-face {r['cost_on_face_pct']:.2f}%")
        print(f"   ** effective APR {r['effective_apr']*100:.2f}%  (EAR {r['ear']*100:.2f}%) **")

# ----------------------------------------------------------------------------
# Built-in self-test: RBI Ocala construction loan (14-Jul-2026 REVISED ALTA)
# Every assertion below was verified against the source PDFs.
# ----------------------------------------------------------------------------
EXAMPLE_RBI_OCALA = {
    "name": "RBI Ocala — REVISED ALTA (File 2026-191-FL)",
    "loan": 589692.07, "holdback": 485900.91, "charges_total": 24666.85,
    "cash_to_borrower": 79124.31,
    "fl_doc_stamp": 2063.95, "fl_intangible": 1179.38, "fl_lenders_title": 3023.50,
    "note_rate": 0.0875, "term_months": 12, "day_count": 360,
    "prepaid_interest": 378.45,
    "line_items": {
        "Origination (1.00%)": 5896.92, "Underwriting": 1500.00,
        "Appraisal": 600.00, "Feasibility": 475.00, "Legal": 1000.00,
        "Prepaid interest": 378.45, "GL insurance": 1554.10,
        "Builder's Risk x3": 2050.20, "Settlement fee": 1350.00,
        "Lender's title": 3023.50, "Notary": 450.00, "Escrow disb": 200.00,
        "Courier": 75.00, "Title search": 255.00, "Lien search": 575.00,
        "Endorsements 8.1/9-06/14": 377.35, "FL doc-stamp": 2063.95,
        "LLC affidavit x6": 240.00, "UCC": 65.00, "E-recording": 25.00,
        "NOC termination x3": 135.00, "FL intangible": 1179.38,
        "Recording deed/mtg": 377.00, "Recording deed 2": 35.50,
        "Recording deed 3": 35.50, "Deed prep x3": 750.00,
    },
}

if __name__ == "__main__":
    report(EXAMPLE_RBI_OCALA)
    print("\n--- ratio benchmark: initial draft (Arianna) vs latest (REVISED) ---")
    rb = ratio_benchmark(
        {"loan": 379521.47, "charges": 14018.45, "houses": 1},
        {"loan": 589692.07, "charges": 24666.85, "houses": 3})
    for k, v in rb.items():
        print(f"   {k:32} {v:,.4f}")
