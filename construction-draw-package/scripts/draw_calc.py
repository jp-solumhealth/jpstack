#!/usr/bin/env python3
"""Construction draw and lien-waiver engine.

Every figure comes from a deal config in ../deals/. Nothing is hardcoded except the
self-test expectations, which are the verified RBI Ocala Draw 1 outputs.

    python3 draw_calc.py selftest              # run this FIRST, every time
    python3 draw_calc.py waivers  --deal rbi-ocala
    python3 draw_calc.py draw     --deal rbi-ocala --number 1
    python3 draw_calc.py schedule --deal rbi-ocala
    python3 draw_calc.py reconcile --deal rbi-ocala
"""
import argparse
import json
import sys
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path

DEALS = Path(__file__).resolve().parent.parent / "deals"


def m(x):
    """Money: half-up to the cent. Never use round() — it is banker's rounding."""
    return D(str(x)).quantize(D("0.01"), rounding=ROUND_HALF_UP)


def load(name):
    p = DEALS / f"{name}.json"
    if not p.exists():
        sys.exit(f"no deal config at {p}\navailable: "
                 f"{', '.join(sorted(f.stem for f in DEALS.glob('*.json')))}")
    return json.loads(p.read_text())


# --------------------------------------------------------------- ledger (waivers)
def ledger_activity(prop, act):
    """Hard cost + commission for one activity, from the cost ledger."""
    a = prop["ledger"][str(act)]
    return D(str(a["hard"])), D(str(a["commission"]))


def waiver_amount(cfg, prop):
    """What a progress waiver on this property releases.

    Full activities carry the full commission. A partial activity carries the
    commission scaled by its completion factor, because the activity is still
    running and the balance has not been earned.
    """
    total = D("0")
    for act in cfg["waiver"]["full_activities"]:
        hard, comm = ledger_activity(prop, act)
        total += hard + comm
    for act, factor in cfg["waiver"].get("partial_activities", {}).items():
        hard, comm_full = ledger_activity(prop, int(act))
        total += hard + m(comm_full * D(str(factor)))
    return m(total)


def cmd_waivers(cfg, _args):
    print("=" * 78)
    print("LIEN WAIVER AMOUNTS  —  what each waiver would release")
    print("=" * 78)
    pct = D(str(cfg["commission_pct"]))
    grand = D("0")
    grand_unpaid = D("0")
    for p in cfg["properties"]:
        amt = waiver_amount(cfg, p)
        unpaid = m(p["unpaid"])
        grand += amt
        grand_unpaid += unpaid
        print(f"\nLetter {p['letter']}  {p['address']}")
        print(f"  parcel {p['parcel']}   permit {p['permit']}")
        for act in cfg["waiver"]["full_activities"]:
            hard, comm = ledger_activity(p, act)
            items = p["ledger"][str(act)]["items"]
            foots = m(sum(D(str(v)) for _, v in items)) == m(hard)
            print(f"  Activity {act}: hard {m(hard):>12,}  + {pct * 100:g}% comm "
                  f"{m(comm):>10,}  = {m(hard + comm):>12,}   "
                  f"[{len(items)} items {'foot' if foots else 'DO NOT FOOT'}]")
        for act, factor in cfg["waiver"].get("partial_activities", {}).items():
            hard, cfull = ledger_activity(p, int(act))
            cpart = m(cfull * D(str(factor)))
            print(f"  Activity {act}: hard {m(hard):>12,}  + comm at "
                  f"{D(str(factor)) * 100:g}% {cpart:>10,}  = {m(hard + cpart):>12,}   "
                  f"[full 9% would be {m(cfull):,}; "
                  f"{m(cfull - cpart):,} NOT released]")
        print(f"  {'WAIVER AMOUNT':<28}{amt:>14,}")
        print(f"  {'ledger still marks unpaid':<28}{unpaid:>14,}"
              f"   -> if unpaid, waive only {m(amt - unpaid):,}")
    print("\n" + "-" * 78)
    print(f"{'TOTAL RELEASED':<30}{grand:>14,}")
    print(f"{'TOTAL FLAGGED UNPAID':<30}{grand_unpaid:>14,}")
    print(f"{'TOTAL IF UNPAID EXCLUDED':<30}{m(grand - grand_unpaid):>14,}")
    if grand_unpaid > 0:
        print("\n  ** A lienor must not release a lien for money it has not received. **")
        print("  Confirm payment before these are signed, or cut the amounts.")
    return grand, grand_unpaid


# ------------------------------------------------------------------ draw request
def draw_activity(prop, act):
    a = prop["draw_schedule"][str(act)]
    return D(str(a["hard"])), D(str(a["commission"]))


def advance_rate(cfg):
    """Holdback / total construction cost.

    Draw at this rate, never at 100% of completed work. Drawing 100% leaves the
    remaining reserve short of the remaining cost, which lets the lender refuse
    further disbursements and call the deficiency in cash.
    """
    total = sum(sum(draw_activity(p, a)) for p in cfg["properties"]
                for a in cfg["draw"]["all_activities"])
    return D(str(cfg["loan"]["holdback"])) / total, total


def cmd_draw(cfg, args):
    rate, constr = advance_rate(cfg)
    acts = args.activities or cfg["draw"]["activities"]
    loan = cfg["loan"]
    fee = D(str(loan["inspection_fee"]))

    print("=" * 78)
    print(f"DRAW REQUEST #{args.number}  —  activities {', '.join(map(str, acts))}, "
          f"{len(cfg['properties'])} properties")
    print("=" * 78)
    print(f"Construction cost to fund (all activities)  : {m(constr):>14,}")
    print(f"Construction reserve / holdback             : "
          f"{m(loan['holdback']):>14,}")
    print(f"Implied advance rate                        : {rate * 100:>13.4f}%")
    print(f"Borrower equity retained                    : "
          f"{m(constr - D(str(loan['holdback']))):>14,}  "
          f"({(1 - rate) * 100:.2f}%)")
    print()
    hdr = f"{'PROPERTY':<24}" + "".join(f"{'ACT ' + str(a):>13}" for a in acts)
    print(hdr + f"{'WORK VALUE':>14}{'ADVANCE':>14}")
    work = D("0")
    for p in cfg["properties"]:
        vals = [sum(draw_activity(p, a)) for a in acts]
        wv = sum(vals)
        work += wv
        print(f"{p['address'].split(',')[0]:<24}"
              + "".join(f"{m(v):>13,}" for v in vals)
              + f"{m(wv):>14,}{m(wv * rate):>14,}")
    gross = m(work * rate)
    print("-" * 78)
    print(f"{'TOTAL':<24}" + " " * (13 * len(acts)) + f"{m(work):>14,}{gross:>14,}")
    print()
    print(f"Draw requested (gross)                      : {gross:>14,}")
    basis = loan["inspection_fee_basis"].replace("_", " ")
    print(f"{'Less inspection fee (' + basis + ')':<44}: {m(-fee):>14,}")
    print(f"NET FUNDING TO BORROWER                     : {m(gross - fee):>14,}")
    print(f"  if the lender bills per property instead  : "
          f"{m(gross - fee * len(cfg['properties'])):>14,}")

    # ---- reserve sufficiency: the test that justifies the pro-rata rate ----
    print("\nRESERVE SUFFICIENCY TEST")
    remaining_acts = [a for a in cfg["draw"]["all_activities"] if a not in acts]
    future = sum(sum(draw_activity(p, a)) for p in cfg["properties"]
                 for a in remaining_acts)
    rem = D(str(loan["holdback"])) - gross
    print(f"Holdback after this draw                    : {m(rem):>14,}")
    print(f"Cost still to complete                      : {m(future):>14,}")
    print(f"Equity required to complete                 : {m(future - rem):>14,}")
    print(f"Reserve as % of remaining cost              : {rem / future * 100:>13.2f}%")
    ok = abs((rem / future) - rate) < D("0.0001")
    print(f"  -> {'equals the advance rate: provably sufficient. PASS' if ok else 'PRO-RATA BROKEN'}")

    print("\nLOAN BALANCE")
    bal = D(str(loan["disbursed_at_close"])) + gross
    r = D(str(loan["interest_rate"]))
    print(f"Principal before / after                    : "
          f"{m(loan['disbursed_at_close']):>14,} / {m(bal):,}")
    print(f"Monthly interest before / after             : "
          f"{m(D(str(loan['disbursed_at_close'])) * r / 12):>14,} / {m(bal * r / 12):,}")
    print(f"Undrawn holdback (accrues no interest)      : "
          f"{m(D(str(loan['face'])) - bal):>14,}")
    assert m(D(str(loan["disbursed_at_close"])) + D(str(loan["holdback"]))) == m(loan["face"]), \
        "loan waterfall broken: disbursed + holdback != face"
    print("  -> disbursed + holdback = loan face. PASS")
    return gross, rate


def cmd_schedule(cfg, _args):
    rate, _ = advance_rate(cfg)
    print("=" * 78)
    print(f"FULL DRAW SCHEDULE  —  every advance at {rate * 100:.4f}%")
    print("=" * 78)
    run = D(str(cfg["loan"]["holdback"]))
    for n, act in enumerate(cfg["draw"]["all_activities"], 1):
        wv = sum(sum(draw_activity(p, act)) for p in cfg["properties"])
        adv = m(wv * rate)
        run -= adv
        print(f"Draw #{n} — activity {act}   work {m(wv):>12,}   "
              f"advance {adv:>12,}   holdback left {m(run):>12,}")
    print(f"{'residual':>62} {m(run):>12,}")
    assert abs(run) < D("0.02"), f"holdback does not fully draw: {run}"
    print("  -> holdback exhausts to zero at the final activity. PASS")
    return run


def cmd_reconcile(cfg, _args):
    """The two schedules disagree. Report the delta; never silently pick one."""
    print("=" * 78)
    print("LEDGER vs DRAW SCHEDULE  —  activities the waivers cover")
    print("=" * 78)
    acts = cfg["waiver"]["full_activities"]
    print(f"{'PROPERTY':<24}{'COST LEDGER':>16}{'DRAW SCHEDULE':>16}{'DELTA':>12}")
    tot = D("0")
    for p in cfg["properties"]:
        led = m(sum(sum(ledger_activity(p, a)) for a in acts))
        dw = m(sum(sum(draw_activity(p, a)) for a in acts))
        tot += dw - led
        print(f"{p['address'].split(',')[0]:<24}{led:>16,}{dw:>16,}{m(dw - led):>12,}")
    print("-" * 68)
    print(f"{'TOTAL DELTA':<24}{'':>16}{'':>16}{m(tot):>12,}")
    if tot:
        print(f"\n  The lender's schedule claims {m(tot):,} more than the cost ledger "
              f"supports.\n  Reconcile before submitting: the same facts back the "
              f"borrower certification.")
    return m(tot)


# ----------------------------------------------------------------------- selftest
def cmd_selftest(_cfg, _args):
    """Reproduce the verified RBI Ocala Draw 1 package. Every expectation below was
    checked against the delivered documents on 5 Aug 2026."""
    cfg = load("rbi-ocala")
    fails = []

    def chk(cond, label):
        print(f"  {'PASS' if cond else 'FAIL'}  {label}")
        if not cond:
            fails.append(label)

    print("=" * 78)
    print("SELFTEST — RBI Ocala, Draw 1 (verified 5 Aug 2026)")
    print("=" * 78)

    print("\nWaiver amounts")
    expect = {"A": "94180.86", "B": "94591.10", "C": "93830.59"}
    for p in cfg["properties"]:
        chk(waiver_amount(cfg, p) == m(expect[p["letter"]]),
            f"Letter {p['letter']} waiver = ${expect[p['letter']]}")
    total = m(sum(waiver_amount(cfg, p) for p in cfg["properties"]))
    chk(total == m("282602.55"), f"three waivers total ${total:,}")

    print("\nEvery ledger line item foots to its activity subtotal")
    for p in cfg["properties"]:
        for act in ("1", "2", "3"):
            a = p["ledger"][act]
            chk(m(sum(D(str(v)) for _, v in a["items"])) == m(a["hard"]),
                f"Letter {p['letter']} activity {act} items foot to {m(a['hard']):,}")

    print("\nCommission is 9% of hard cost on completed activities")
    pct = D(str(cfg["commission_pct"]))
    for p in cfg["properties"]:
        for act in ("1", "2"):
            a = p["ledger"][act]
            chk(m(D(str(a["hard"])) * pct) == m(a["commission"]),
                f"Letter {p['letter']} activity {act} commission = "
                f"{m(a['commission']):,}")

    print("\nActivity 3 commission held back to 60% (work still running)")
    exp3 = {"A": "1201.81", "B": "1204.42", "C": "1190.50"}
    for p in cfg["properties"]:
        _, cfull = ledger_activity(p, 3)
        chk(m(cfull * D("0.60")) == m(exp3[p["letter"]]),
            f"Letter {p['letter']} activity 3 at 60% = ${exp3[p['letter']]}")

    print("\nReduced amounts if the flagged sums are genuinely unpaid")
    expred = {"A": "68535.34", "B": "68897.16", "C": "68394.36"}
    for p in cfg["properties"]:
        red = m(waiver_amount(cfg, p) - D(str(p["unpaid"])))
        chk(red == m(expred[p["letter"]]),
            f"Letter {p['letter']} reduced = ${expred[p['letter']]}")
    redtot = m(sum(waiver_amount(cfg, p) - D(str(p["unpaid"]))
                   for p in cfg["properties"]))
    chk(redtot == m("205826.86"), f"reduced total ${redtot:,}")

    print("\nDraw mechanics")
    rate, constr = advance_rate(cfg)
    chk(f"{rate * 100:.4f}" == "91.0285", f"advance rate {rate * 100:.4f}%")
    chk(m(constr) == m("533790.15"), f"construction to fund {m(constr):,}")
    work12 = sum(sum(draw_activity(p, a)) for p in cfg["properties"] for a in (1, 2))
    chk(m(work12) == m("215009.16"), f"activity 1+2 work value {m(work12):,}")
    chk(m(work12 * rate) == m("195719.51"), f"draw 1 advance {m(work12 * rate):,}")
    expdraw = ["195719.51", "101328.81", "117716.99", "71135.59"]
    run = D(str(cfg["loan"]["holdback"]))
    got = []
    for act in cfg["draw"]["all_activities"]:
        wv = sum(sum(draw_activity(p, act)) for p in cfg["properties"])
        got.append(m(wv * rate))
    got = [m(got[0] + got[1])] + got[2:]   # draw 1 = activities 1+2 together
    for i, (g, e) in enumerate(zip(got, expdraw), 1):
        chk(g == m(e), f"draw #{i} advance ${e}")
        run -= g
    chk(abs(run) < D("0.02"), f"holdback exhausts to zero (residual {m(run):,})")
    chk(m(D(str(cfg["loan"]["disbursed_at_close"])) + D(str(cfg["loan"]["holdback"])))
        == m(cfg["loan"]["face"]), "disbursed at close + holdback = loan face")

    print("\nLedger vs draw schedule divergence (known, documented)")
    for p in cfg["properties"]:
        led = m(sum(sum(ledger_activity(p, a)) for a in (1, 2)))
        dw = m(sum(sum(draw_activity(p, a)) for a in (1, 2)))
        chk(m(dw - led) in (m("869.79"), m("869.78")),
            f"Letter {p['letter']} draw exceeds ledger by {m(dw - led):,}")
    delta = m(sum(m(sum(sum(draw_activity(p, a)) for a in (1, 2)))
                  - m(sum(sum(ledger_activity(p, a)) for a in (1, 2)))
                  for p in cfg["properties"]))
    chk(delta == m("2609.36"), f"total divergence ${delta:,} "
                               f"($797.97 hard + 9% per property)")

    print("\n" + "=" * 78)
    if fails:
        print(f"RESULT: {len(fails)} FAILURE(S)")
        for f in fails:
            print("   FAILED:", f)
        print("=" * 78)
        sys.exit(1)
    print("RESULT: ALL PASS")
    print("=" * 78)


CMDS = {"waivers": cmd_waivers, "draw": cmd_draw, "schedule": cmd_schedule,
        "reconcile": cmd_reconcile, "selftest": cmd_selftest}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=sorted(CMDS))
    ap.add_argument("--deal", default="rbi-ocala")
    ap.add_argument("--number", type=int, default=1, help="draw number")
    ap.add_argument("--activities", type=int, nargs="+",
                    help="override which activities this draw covers")
    args = ap.parse_args()
    cfg = None if args.command == "selftest" else load(args.deal)
    CMDS[args.command](cfg, args)


if __name__ == "__main__":
    main()
