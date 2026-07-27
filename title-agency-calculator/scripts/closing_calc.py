#!/usr/bin/env python3
"""
closing_calc.py — Florida title-agency and closing-cost calculator.

Runs a full closing estimate from first principles: FL statutory charges computed
from the price and loan, a named title-agency rate card, tax proration, seller net,
buyer cash to close, the three-bucket classification, and every cost percentage.

    python3 closing_calc.py selftest
    python3 closing_calc.py cards
    python3 closing_calc.py estimate --price 279000 --agency marion-lake \
        --loan 270630 --close 2026-08-24 --annual-tax 290.11 --commission 4.5 \
        --basis 210474.47 --sf 1400 --notary 175
    python3 closing_calc.py compare --price 279000 --loan 270630 \
        --close 2026-08-24 --annual-tax 290.11 --commission 4.5

SELF-TEST IS THE CONTRACT. It reproduces verified closings to the penny (8 Pine
Track under both agencies, and the CLOSED 31 Juniper file). If `selftest` does not
print ALL PASS, a rate card or formula has drifted — fix it before quoting anything.

Rate cards, statutory formulas and provenance: ../references/fl-rates-and-ratecards.md
"""
from __future__ import annotations
import argparse, math, sys
from datetime import date, datetime

# ══════════════════════════════════════════════════ FL STATUTORY FORMULAS
DEED_STAMP_RATE = 0.0070      # $0.70 per $100 of consideration
NOTE_STAMP_RATE = 0.0035      # $0.35 per $100 of note
INTANGIBLE_RATE = 0.0020      # 0.20% of the secured amount
SIMULTANEOUS    = 25.00       # lender's policy issued simultaneously with owner's
REC_FIRST, REC_ADDL = 10.00, 8.50

def deed_stamps(price):  return round(math.ceil(price / 100) * 100 * DEED_STAMP_RATE, 2)
def note_stamps(loan):   return round(math.ceil(loan / 100) * 100 * NOTE_STAMP_RATE, 2)
def intangible(loan):    return round(loan * INTANGIBLE_RATE, 2)
def recording(pages):    return round(REC_FIRST + REC_ADDL * max(0, pages - 1), 2)

def owners_premium(coverage, round_up=True):
    """FL promulgated original owner's rate: $5.75/1,000 to $100k; $5.00/1,000 $100k-$1M;
    $2.50/1,000 above $1M. round_up=True rounds coverage to the next $1,000 (standard
    practice); some agents price on the exact figure — see the reference file."""
    base = math.ceil(coverage / 1000) * 1000 if round_up else coverage
    if base <= 100_000:
        return round(base / 1000 * 5.75, 2)
    if base <= 1_000_000:
        return round(575 + (base - 100_000) / 1000 * 5.00, 2)
    return round(575 + 4_500 + (base - 1_000_000) / 1000 * 2.50, 2)

def proration(annual_tax, closing: date, start: date | None = None, inclusive=True):
    """FL taxes are billed in ARREARS — the bill lands in November, due the following
    March. At any closing before that, the seller owes Jan 1 -> closing and hands it to
    the buyer. Returns (amount, days). Seller DEBIT / buyer CREDIT, equal and opposite."""
    start = start or date(closing.year, 1, 1)
    days = (closing - start).days + (1 if inclusive else 0)
    return round(annual_tax / 365 * days, 2), days

# ══════════════════════════════════════════════════ RECORDED RATE CARDS
# Every figure was read off a real statement. Provenance in the reference file.
CARDS = {
 "marion-lake": {
   "name": "Marion Lake Sumter Title", "underwriter": "Alliant National",
   "context": "SALE, 1 house — HUD-1 file JANETCASH, 8 Pine Track Trail, Aug 2026",
   "seller": {"settlement": 465.00, "title_search": 85.00, "lien_search": 140.00,
              "erecording": 6.99, "warehousing": 45.00, "id_verification": 19.00},
   "buyer":  {"settlement": 510.00, "erecording": 13.90, "id_verification": 19.00},
   "keeps":  ["settlement", "erecording", "warehousing", "id_verification"],
   "notary_quoted": False,
 },
 "next-chapter": {
   "name": "Next Chapter Title", "underwriter": "Investors Title",
   "context": "SALE, 1 house — ALTA 'Test 1', 8 Pine Track; buyer side from CLOSED 31 Juniper 26-543",
   "seller": {"settlement": 385.00, "title_search": 75.00, "lien_search": 165.00,
              "erecording": 5.25, "technology": 25.00, "notary": 175.00},
   "buyer":  {"settlement": 750.00, "courier": 150.00, "secure_doc": 25.00, "erecording": 10.50},
   "keeps":  ["settlement", "technology"],
   "notary_quoted": True,
 },
 "next-chapter-loan": {
   "name": "Next Chapter Title (loan)", "underwriter": "Investors Title",
   "context": "LOAN, 3 properties — HUD-1 26-757, RBI construction loan, Jul 2026. NOT comparable to a 1-house sale.",
   "seller": {},
   "buyer":  {"settlement": 750.00, "notary": 175.00, "title_search": 225.00,
              "lien_search": 495.00, "erecording": 36.75, "endorsements": 402.35,
              "courier": 175.00, "technology": 50.00, "ucc": 65.00, "noc_recording": 136.50},
   "keeps":  ["settlement", "technology", "courier", "endorsements"], "notary_quoted": True,
 },
 "gogo": {
   "name": "GO GO Titles", "underwriter": "WFG National",
   "context": "LOAN, 3 properties — Combined Grid 2026-191-FL, RBI loan, Jul 2026. NOT comparable to a 1-house sale.",
   "seller": {},
   "buyer":  {"settlement": 850.00, "notary": 325.00, "title_search": 255.00,
              "lien_search": 575.00, "escrow_disbursement": 200.00, "courier": 75.00,
              "erecording": 25.00, "deed_prep": 500.00, "llc_affidavit": 240.00,
              "noc_recording": 135.00, "ucc": 65.00, "endorsements": 377.35},
   "keeps":  ["settlement", "notary", "escrow_disbursement", "courier", "deed_prep",
              "llc_affidavit", "title_search", "lien_search"], "notary_quoted": True,
 },
}
JUNK = {"technology", "secure_doc", "warehousing", "id_verification", "escrow_disbursement"}
SALE_CARDS = ["marion-lake", "next-chapter"]


# ══════════════════════════════════════════════════ THE CALC
class Closing:
    def __init__(self, price, agency, *, loan=0.0, close=None, annual_tax=0.0,
                 commission_pct=4.5, basis=None, sf=None, concession=0.0,
                 survey=0.0, force_notary=None, strike_junk=False, noc_pages=2,
                 deed_pages=2, mortgage_pages=20, owners_round_up=True):
        self.price, self.loan = price, loan
        self.card, self.agency = CARDS[agency], agency
        self.close = close or date.today()
        self.annual_tax, self.commission_pct = annual_tax, commission_pct
        self.basis, self.sf, self.survey = basis, sf, survey
        self.noc_pages = noc_pages

        sc, bc = dict(self.card["seller"]), dict(self.card["buyer"])
        if strike_junk:
            sc = {k: v for k, v in sc.items() if k not in JUNK}
            bc = {k: v for k, v in bc.items() if k not in JUNK}
        if force_notary is not None:
            (sc if self.card["seller"] else bc)["notary"] = force_notary
        self.sc = {k: v for k, v in sc.items() if v}
        self.bc = {k: v for k, v in bc.items() if v}

        self.deed_stamps   = deed_stamps(price)
        self.owners_prem   = owners_premium(price, owners_round_up)
        self.noc_recording = recording(noc_pages)
        self.note_stamps   = note_stamps(loan) if loan else 0.0
        self.intangible    = intangible(loan) if loan else 0.0
        self.lenders_prem  = SIMULTANEOUS if loan else 0.0
        self.buyer_recording = recording(deed_pages) + (recording(mortgage_pages) if loan else 0.0)
        self.proration, self.prorate_days = (proration(annual_tax, self.close)
                                             if annual_tax else (0.0, 0))
        self.commission = round(price * commission_pct / 100, 2)
        self.concession = concession

    # ---- buckets
    @property
    def title_agency(self):  return round(sum(self.sc.values()), 2)
    @property
    def title_agency_keeps(self):
        return round(sum(v for k, v in self.sc.items() if k in self.card["keeps"]), 2)
    @property
    def statutory_seller(self):
        return round(self.deed_stamps + self.owners_prem + self.noc_recording, 2)
    @property
    def seller_charges(self):
        """Everything on the settlement statement's seller column except proration/concession."""
        return round(self.commission + self.title_agency + self.statutory_seller, 2)
    @property
    def seller_total(self):
        return round(self.seller_charges + self.proration + self.concession, 2)
    @property
    def net_to_seller(self): return round(self.price - self.seller_total, 2)
    @property
    def closing_costs(self):
        """HEADLINE: closing costs ex-commission and ex-concession. A concession is a
        price adjustment, not a cost of closing."""
        return round(self.title_agency + self.statutory_seller + self.proration, 2)
    @property
    def all_in_title(self):  return round(self.title_agency + self.owners_prem, 2)
    @property
    def buyer_charges(self):
        return round(sum(self.bc.values()) + self.note_stamps + self.intangible
                     + self.lenders_prem + self.buyer_recording + self.survey, 2)
    def buyer_cash(self, deposit=0.0):
        return round((self.price + self.buyer_charges)
                     - (deposit + self.loan + self.proration + self.concession), 2)

    # ---- output
    def report(self, deposit=0.0):
        W, w = 92, 44
        line = lambda: print("-" * W)
        pct = lambda v: f"{v/self.price:>9.3%}"
        print(f"\n{'='*W}\n{self.card['name']}  [{self.agency}]  ·  underwriter {self.card['underwriter']}")
        print(f"{self.card['context']}\n{'='*W}")
        print(f"  Price {self.price:>13,.2f}   loan {self.loan:>12,.2f}   closing {self.close}")
        if self.basis:
            m = self.price - self.basis
            print(f"  Basis {self.basis:>13,.2f}   margin {m:>10,.2f}"
                  + (f"   {self.sf:,} sf" if self.sf else ""))

        print(f"\n  SELLER SIDE{'':<33}{'AMOUNT':>12}{'% price':>10}  BUCKET"); line()
        rows = [(f"Real-estate commission ({self.commission_pct:g}%)", self.commission, "BROKER"),
                ("Deed documentary stamps (0.70%)", self.deed_stamps, "STATUTORY"),
                ("Owner's title policy (promulgated)", self.owners_prem, "STATUTORY"),
                (f"NOC / release recording ({self.noc_pages}pg)", self.noc_recording, "STATUTORY")]
        rows += [(f"Title — {k.replace('_',' ')}", v, "TITLE") for k, v in sorted(self.sc.items())]
        if self.proration:
            rows.append((f"County tax proration ({self.prorate_days}d)", self.proration, "FORMULA"))
        if self.concession:
            rows.append(("Seller concession", self.concession, "DEAL"))
        for lbl, amt, bkt in rows:
            print(f"  {lbl:<{w}}{amt:>12,.2f}{pct(amt)}  {bkt}")
        line()
        print(f"  {'TOTAL SELLER COST':<{w}}{self.seller_total:>12,.2f}{pct(self.seller_total)}")
        print(f"  {'NET TO SELLER':<{w}}{self.net_to_seller:>12,.2f}{pct(self.net_to_seller)}")

        print(f"\n  COST OVER THE PRICE OF THE HOUSE"); line()
        for lbl, v in [("Commission", self.commission),
                       ("Statutory / promulgated", self.statutory_seller),
                       ("Title agency fees", self.title_agency),
                       ("Tax proration", self.proration),
                       ("Seller concession (price adjustment)", self.concession)]:
            if v: print(f"  {lbl:<{w}}{v:>12,.2f}{pct(v)}")
        line()
        cc = self.closing_costs
        print(f"  {'CLOSING COSTS — EX-COMMISSION, EX-CONCESSION':<{w}}{cc:>12,.2f}{pct(cc)}  <<<")
        if self.basis:
            m = self.price - self.basis
            print(f"      vs cost basis {cc/self.basis:>7.2%}   vs gross margin {cc/m:>7.2%}")
            print(f"      total seller cost: {self.seller_total/self.basis:.2%} of basis · "
                  f"{self.seller_total/m:.2%} of margin")
        if self.sf:
            print(f"      per sf: price {self.price/self.sf:,.2f} · closing {cc/self.sf:,.2f} · "
                  f"net {self.net_to_seller/self.sf:,.2f}")
        bench = "inside" if 0.010 <= cc / self.price <= 0.030 else "OUTSIDE"
        print(f"      FL benchmark ex-commission 1.0%-3.0% → {bench} the range")

        print(f"\n  TITLE DETAIL"); line()
        print(f"  {'Title agency fees (all lines)':<{w}}{self.title_agency:>12,.2f}"
              f"{pct(self.title_agency)}")
        print(f"  {'  the agency keeps':<{w}}{self.title_agency_keeps:>12,.2f}")
        print(f"  {'  passed to third parties':<{w}}"
              f"{self.title_agency-self.title_agency_keeps:>12,.2f}")
        print(f"  {'ALL-IN TITLE (fees + promulgated premium)':<{w}}{self.all_in_title:>12,.2f}"
              f"{pct(self.all_in_title)}")
        junk = round(sum(v for k, v in self.sc.items() if k in JUNK), 2)
        if junk: print(f"  {'  of which strikeable house fees':<{w}}{junk:>12,.2f}")
        if not self.card["notary_quoted"]:
            print(f"  !! this card quotes NO notary — pass --notary before comparing agencies")

        if self.bc or self.loan:
            print(f"\n  BUYER SIDE{'':<34}{'AMOUNT':>12}{'% price':>10}"); line()
            for k, v in sorted(self.bc.items()):
                print(f"  {'Title — '+k.replace('_',' '):<{w}}{v:>12,.2f}{pct(v)}")
            for lbl, v in [("Note documentary stamps (0.35%)", self.note_stamps),
                           ("Intangible tax (0.20%)", self.intangible),
                           ("Lender's policy, simultaneous", self.lenders_prem),
                           ("Recording (deed + mortgage)", self.buyer_recording),
                           ("Survey", self.survey)]:
                if v: print(f"  {lbl:<{w}}{v:>12,.2f}{pct(v)}")
            line()
            print(f"  {'TOTAL BUYER CHARGES':<{w}}{self.buyer_charges:>12,.2f}"
                  f"{pct(self.buyer_charges)}")
            if deposit or self.loan:
                print(f"  {'CASH FROM BUYER':<{w}}{self.buyer_cash(deposit):>12,.2f}")
            comb = round(cc + self.buyer_charges, 2)
            print(f"  {'BOTH SIDES, EX-COMMISSION':<{w}}{comb:>12,.2f}{pct(comb)}")
            print(f"\n  !! prepaids (HUD 900) and escrow reserves (HUD 1000) are NOT modelled here.")
            print(f"     A financed buyer usually adds $3,000-$6,000. Get the Loan Estimate before")
            print(f"     agreeing to a percentage concession — see SKILL.md.")


def compare(price, agencies=None, notary=175.00, **kw):
    agencies = agencies or SALE_CARDS
    W = 92
    print(f"\n{'='*W}\nAGENCY COMPARISON — like-for-like (notary forced onto every card at "
          f"{notary:,.2f})\n{'='*W}")
    runs = {a: Closing(price, a, force_notary=notary, **kw) for a in agencies}
    keys = sorted({k for r in runs.values() for k in r.sc})
    hdr = "".join(f"{CARDS[a]['name'][:16]:>18}" for a in agencies)
    print(f"  {'TITLE AGENCY LINE':<30}{hdr}"); print("-" * W)
    for k in keys:
        print(f"  {k.replace('_',' '):<30}"
              + "".join(f"{runs[a].sc.get(k, 0):>18,.2f}" for a in agencies))
    print("-" * W)
    for lbl, fn in [("TITLE AGENCY TOTAL", lambda r: r.title_agency),
                    ("  agency keeps", lambda r: r.title_agency_keeps),
                    ("ALL-IN TITLE (+ premium)", lambda r: r.all_in_title),
                    ("CLOSING COSTS EX-COMMISSION", lambda r: r.closing_costs),
                    ("NET TO SELLER", lambda r: r.net_to_seller)]:
        print(f"  {lbl:<30}" + "".join(f"{fn(runs[a]):>18,.2f}" for a in agencies))
    print(f"  {'  closing costs as % of price':<30}"
          + "".join(f"{runs[a].closing_costs/price:>17.3%} " for a in agencies))
    best = min(agencies, key=lambda a: runs[a].closing_costs)
    spread = max(runs[a].closing_costs for a in agencies) - runs[best].closing_costs
    print(f"\n  >>> Lowest closing costs: {CARDS[best]['name']} — by ${spread:,.2f}")
    print(f"  >>> Remember: only the title-agency bucket is shoppable. The premium, deed")
    print(f"      stamps and recording are identical at every agency in Florida.")
    return runs


# ══════════════════════════════════════════════════ SELF-TEST
def selftest():
    fails = []
    def chk(label, got, want, tol=0.005):
        ok = abs(got - want) < tol
        print(f"  {'PASS' if ok else 'FAIL'}  {label:<50}{got:>13,.2f}  want {want:>13,.2f}")
        if not ok: fails.append(label)

    print("\n── FL statutory formulas ──")
    chk("deed stamps on 279,000",         deed_stamps(279_000),     1_953.00)
    chk("deed stamps on 279,900",         deed_stamps(279_900),     1_959.30)
    chk("deed stamps on 257,000",         deed_stamps(257_000),     1_799.00)
    chk("note stamps on 270,630",         note_stamps(270_630),       947.45)
    chk("intangible on 270,630",          intangible(270_630),        541.26)
    chk("owner's premium on 279,000",     owners_premium(279_000),  1_470.00)
    chk("owner's premium on 257,000",     owners_premium(257_000),  1_360.00)
    chk("owner's premium on 279,900 (exact-price basis)",
        owners_premium(279_900, round_up=False),                    1_474.50)
    chk("recording, 2 pages",             recording(2),                18.50)
    chk("recording, 3 pages",             recording(3),                27.00)
    p, d = proration(290.11, date(2026, 8, 24))
    chk("proration Jan1→Aug24 @ 290.11",  p,                          187.58, 0.02)
    chk("  day count",                    d,                          236)

    print("\n── 8 Pine Track Trail · Marion Lake Sumter (HUD-1 JANETCASH) ──")
    a = Closing(279_000, "marion-lake", loan=270_630, close=date(2026, 8, 24),
                annual_tax=290.11, commission_pct=4.5, basis=210_474.4746, sf=1400)
    chk("title agency fees",              a.title_agency,             760.99)
    chk("  agency keeps",                 a.title_agency_keeps,       535.99)
    chk("statutory seller",               a.statutory_seller,       3_441.50)
    chk("seller charges (HUD line 1400)", a.seller_charges,        16_757.49)
    chk("proration (HUD line 511)",       a.proration,                187.58, 0.02)
    chk("net to seller (HUD line 603)",   a.net_to_seller,        262_054.93, 0.02)
    chk("all-in title",                   a.all_in_title,           2_230.99)
    b = Closing(279_000, "marion-lake", loan=270_630, close=date(2026, 8, 24),
                annual_tax=290.11, commission_pct=4.5, survey=500.00)
    chk("buyer charges (HUD line 103)",   b.buyer_charges,          2_746.61)
    chk("buyer cash (HUD line 303)",      b.buyer_cash(deposit=3_000), 7_929.03, 0.02)

    print("\n── 8 Pine Track Trail · Next Chapter (ALTA 'Test 1') ──")
    c = Closing(279_900, "next-chapter", close=date(2026, 8, 26), commission_pct=5.0,
                concession=5_000.00, noc_pages=3, owners_round_up=False)
    chk("title agency fees",              c.title_agency,             830.25)
    chk("  agency keeps",                 c.title_agency_keeps,       410.00)
    chk("owner's premium as billed",      c.owners_prem,            1_474.50)
    chk("seller total (ALTA subtotal)",   c.seller_total,          23_286.05)
    chk("net to seller (ALTA)",           c.net_to_seller,        256_613.95)
    chk("closing costs ex-commission (no proration on the ALTA)",
                                          c.closing_costs,          4_291.05)

    print("\n── 31 Juniper Drive · Next Chapter (file 26-543, CLOSED 03/16/2026) ──")
    j = Closing(257_000, "next-chapter", close=date(2026, 3, 16), commission_pct=2.0,
                noc_pages=3)
    chk("deed stamps",                    j.deed_stamps,            1_799.00)
    chk("owner's premium",                j.owners_prem,            1_360.00)
    chk("commission (listing only, 2.0%)",j.commission,             5_140.00)

    print("\n── headline ratios · 8 Pine Track ──")
    n = Closing(279_000, "marion-lake", loan=270_630, close=date(2026, 8, 24),
                annual_tax=290.11, commission_pct=4.5, force_notary=175.00)
    chk("closing costs with required notary", n.closing_costs,      4_565.07, 0.02)
    r = n.closing_costs / 279_000
    ok = abs(r - 0.016362) < 0.00002
    print(f"  {'PASS' if ok else 'FAIL'}  {'  as % of price':<50}{r:>13.3%}  want       1.636%")
    if not ok: fails.append("cost ratio")

    print("\n" + ("ALL PASS — formulas and rate cards are intact."
                  if not fails else f"{len(fails)} FAILURE(S): {fails}"))
    return 1 if fails else 0


def show_cards():
    for k, c in CARDS.items():
        print(f"\n{k}  —  {c['name']}   [underwriter: {c['underwriter']}]")
        print(f"  {c['context']}")
        for side in ("seller", "buyer"):
            if c[side]:
                print(f"  {side:<7}" + "  ".join(f"{a}={b:,.2f}" for a, b in c[side].items())
                      + f"   [total {sum(c[side].values()):,.2f}]")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["estimate", "compare", "selftest", "cards"])
    ap.add_argument("--price", type=float); ap.add_argument("--loan", type=float, default=0.0)
    ap.add_argument("--agency", default="marion-lake", choices=list(CARDS))
    ap.add_argument("--close", type=lambda s: datetime.strptime(s, "%Y-%m-%d").date())
    ap.add_argument("--annual-tax", type=float, default=0.0,
                    help="full-year tax bill; FL assesses as of Jan 1 so a new build is LAND ONLY")
    ap.add_argument("--commission", type=float, default=4.5)
    ap.add_argument("--basis", type=float); ap.add_argument("--sf", type=int)
    ap.add_argument("--deposit", type=float, default=0.0)
    ap.add_argument("--survey", type=float, default=0.0)
    ap.add_argument("--concession", type=float, default=0.0)
    ap.add_argument("--concession-pct", type=float,
                    help="seller pays this %% of the buyer's charges instead of a flat amount")
    ap.add_argument("--concession-cap", type=float, help="dollar cap on the computed concession")
    ap.add_argument("--notary", type=float, help="force this notary fee onto the card")
    ap.add_argument("--strike-junk", action="store_true",
                    help="drop technology / warehousing / ID-verification / escrow-disbursement")
    ap.add_argument("--noc-pages", type=int, default=2)
    ap.add_argument("--deed-pages", type=int, default=2)
    ap.add_argument("--mortgage-pages", type=int, default=20,
                    help="typical residential mortgage is ~20 pages ($171.50 to record)")
    ap.add_argument("--exact-premium", action="store_true",
                    help="price the owner's policy on the exact sale price, not rounded up")
    a = ap.parse_args()

    if a.cmd == "selftest": sys.exit(selftest())
    if a.cmd == "cards":    show_cards(); return
    if not a.price: ap.error("--price is required")

    kw = dict(loan=a.loan, close=a.close, annual_tax=a.annual_tax, commission_pct=a.commission,
              basis=a.basis, sf=a.sf, survey=a.survey, strike_junk=a.strike_junk,
              noc_pages=a.noc_pages, deed_pages=a.deed_pages,
              mortgage_pages=a.mortgage_pages, owners_round_up=not a.exact_premium)
    if a.cmd == "compare":
        compare(a.price, notary=a.notary or 175.00, **kw); return

    c = Closing(a.price, a.agency, concession=a.concession, force_notary=a.notary, **kw)
    if a.concession_pct:
        conc = round(c.buyer_charges * a.concession_pct / 100, 2)
        capped = min(conc, a.concession_cap) if a.concession_cap else conc
        print(f"\n  Concession = {a.concession_pct:g}% of buyer charges {c.buyer_charges:,.2f} "
              f"= {conc:,.2f}" + (f" → capped at {capped:,.2f}" if capped != conc else ""))
        c.concession = capped
    c.report(deposit=a.deposit)


if __name__ == "__main__":
    main()
