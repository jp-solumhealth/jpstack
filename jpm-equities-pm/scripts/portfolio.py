#!/usr/bin/env python3
"""portfolio.py — analyze a personal holdings CSV. Prints a Markdown review.

Reads portfolio.csv (schema in templates/portfolio-schema.md), pulls live prices via
yfinance, and reports: holdings table, allocation (by asset class + sector), concentration
(top-5 weight, HHI), unrealized P/L, drift vs targets (optional), TLH candidates, and
portfolio return vs SPY for context.

Usage:
  python3 portfolio.py                                  # default ~/Documents/Claude/hedge-fund-jpm/portfolio/
  python3 portfolio.py --csv path/to/portfolio.csv --out review.md
  python3 portfolio.py --targets targets.csv            # asset_class,target_pct for drift

Honest about limits: with only current holdings + cost basis (no transaction history) it
reports UNREALIZED return, not a true time-weighted return. SPY changes are shown for context.
If yfinance is unavailable, supply a `price` column in the CSV.
"""
import argparse, csv, os, sys, datetime

HOME = os.path.expanduser("~")
DEFAULT_CSV = os.path.join(HOME, "Documents/Claude/hedge-fund-jpm/portfolio/portfolio.csv")


def load_rows(path):
    with open(path, newline="") as f:
        return [ {k.strip(): (v.strip() if v else "") for k, v in r.items()}
                 for r in csv.DictReader(f) ]


def get_prices(tickers):
    """Return {ticker: price}. CASH handled by caller. None on failure."""
    try:
        import yfinance as yf
    except ImportError:
        return None
    out = {}
    try:
        data = yf.download(tickers, period="5d", interval="1d",
                           auto_adjust=True, progress=False)["Close"]
        if hasattr(data, "columns"):
            for t in tickers:
                try:
                    out[t] = float(data[t].dropna().iloc[-1])
                except Exception:
                    out[t] = None
        else:  # single ticker -> Series
            out[tickers[0]] = float(data.dropna().iloc[-1])
    except Exception:
        return None
    return out


def spy_returns():
    try:
        import yfinance as yf
        h = yf.Ticker("SPY").history(period="1y", auto_adjust=True)["Close"].dropna()
        last = float(h.iloc[-1])
        y1 = last / float(h.iloc[0]) - 1
        jan = h[h.index >= f"{h.index[-1].year}-01-01"]
        ytd = last / float(jan.iloc[0]) - 1 if len(jan) else None
        return ytd, y1
    except Exception:
        return None, None


def fnum(x, money=True):
    return (f"${x:,.0f}" if money else f"{x:,.2f}") if x is not None else "—"


def main():
    ap = argparse.ArgumentParser(description="Analyze a personal holdings CSV.")
    ap.add_argument("--csv", default=DEFAULT_CSV)
    ap.add_argument("--targets", help="CSV with asset_class,target_pct for drift analysis")
    ap.add_argument("--out", help="write the Markdown report here")
    args = ap.parse_args()
    today = datetime.date.today().isoformat()

    if not os.path.exists(args.csv):
        print(f"No portfolio CSV at {args.csv}\n"
              f"Create one from templates/portfolio-schema.md (or pass --csv).")
        sys.exit(1)
    rows = load_rows(args.csv)

    tickers = sorted({r["ticker"].upper() for r in rows
                      if r.get("asset_class", "").lower() != "cash" and r["ticker"].upper() != "CASH"})
    prices = get_prices(tickers) if tickers else {}
    price_src = "yfinance (live)"
    if prices is None:  # yfinance failed; fall back to CSV price column
        prices, price_src = {}, "CSV price column"

    holdings, missing = [], []
    for r in rows:
        t = r["ticker"].upper()
        shares = float(r.get("shares") or 0)
        cost = float(r.get("cost_basis_per_share") or 0)
        is_cash = r.get("asset_class", "").lower() == "cash" or t == "CASH"
        if is_cash:
            px = cost  # cash row: cost_basis_per_share holds the $ amount, shares=1
        else:
            px = prices.get(t)
            if px is None and r.get("price"):
                px = float(r["price"])
            if px is None:
                missing.append(t)
                continue
        mv = shares * px
        basis = shares * cost
        pl = mv - basis if not is_cash else 0.0
        plpct = (pl / basis) if basis and not is_cash else 0.0
        # holding period
        lt = None
        if r.get("purchase_date"):
            try:
                d0 = datetime.date.fromisoformat(r["purchase_date"])
                lt = (datetime.date.today() - d0).days >= 365
            except ValueError:
                pass
        holdings.append({"ticker": t, "account": r.get("account", ""),
                         "asset_class": r.get("asset_class", ""), "sector": r.get("sector", "") or "—",
                         "shares": shares, "price": px, "mv": mv, "basis": basis,
                         "pl": pl, "plpct": plpct, "lt": lt, "is_cash": is_cash})

    total = sum(h["mv"] for h in holdings) or 1.0
    for h in holdings:
        h["weight"] = h["mv"] / total

    # aggregates
    def agg(key):
        out = {}
        for h in holdings:
            out[h[key] or "—"] = out.get(h[key] or "—", 0) + h["weight"]
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    by_class, by_sector = agg("asset_class"), agg("sector")
    eq = [h for h in holdings if not h["is_cash"]]
    eq_sorted = sorted(eq, key=lambda h: -h["weight"])
    top5 = sum(h["weight"] for h in eq_sorted[:5])
    hhi = sum((h["weight"]) ** 2 for h in eq) * 10000  # basis-point HHI on equity sleeve
    tot_basis = sum(h["basis"] for h in holdings if not h["is_cash"])
    tot_eqmv = sum(h["mv"] for h in holdings if not h["is_cash"])
    unreal = (tot_eqmv / tot_basis - 1) if tot_basis else None
    ytd, y1 = spy_returns()

    # drift
    drift = None
    if args.targets and os.path.exists(args.targets):
        tg = {r["asset_class"]: float(r["target_pct"]) for r in load_rows(args.targets)}
        drift = []
        for ac, tgt in tg.items():
            cur = by_class.get(ac, 0) * 100
            drift.append((ac, tgt, cur, cur - tgt))

    L = []
    L.append(f"# Portfolio review — {today}")
    L.append(f"_Source: {args.csv} · prices: {price_src} · total value {fnum(total)}_\n")
    if missing:
        L.append(f"> ⚠️ No price for: {', '.join(missing)} — add a `price` column or fix the ticker. Excluded below.\n")

    L.append("## Holdings")
    L.append("| Ticker | Acct | Class | Sector | Shares | Price | Value | Weight | Unreal P/L | % | Hold |")
    L.append("|---|---|---|---|--:|--:|--:|--:|--:|--:|:--:|")
    for h in eq_sorted + [h for h in holdings if h["is_cash"]]:
        hold = "—" if h["lt"] is None or h["is_cash"] else ("LT" if h["lt"] else "ST")
        L.append(f"| {h['ticker']} | {h['account']} | {h['asset_class']} | {h['sector']} | "
                 f"{h['shares']:,.0f} | {fnum(h['price'], False)} | {fnum(h['mv'])} | {h['weight']*100:.1f}% | "
                 f"{fnum(h['pl'])} | {h['plpct']*100:+.1f}% | {hold} |")

    L.append("\n## Allocation")
    L.append("**By asset class:** " + " · ".join(f"{k} {v*100:.0f}%" for k, v in by_class.items()))
    L.append("\n**By sector (% of portfolio):** " + " · ".join(f"{k} {v*100:.0f}%" for k, v in by_sector.items()))

    L.append("\n## Concentration")
    L.append(f"- Top-5 equity weight: **{top5*100:.0f}%**")
    L.append(f"- HHI (equity sleeve): **{hhi:,.0f}** "
             f"({'concentrated' if hhi>2500 else 'moderate' if hhi>1500 else 'diversified'})")
    over = [h for h in eq_sorted if h["weight"] > 0.10]
    if over:
        L.append(f"- ⚠️ Single names over 10%: " + ", ".join(f"{h['ticker']} {h['weight']*100:.0f}%" for h in over))

    if drift:
        L.append("\n## Drift vs targets")
        L.append("| Asset class | Target % | Current % | Drift |")
        L.append("|---|--:|--:|--:|")
        for ac, tgt, cur, dr in drift:
            flag = " ⚠️" if abs(dr) >= 5 else ""
            L.append(f"| {ac} | {tgt:.0f}% | {cur:.0f}% | {dr:+.1f}%{flag} |")
        L.append("\n_Rebalance only on band breach; direct new cash to underweight first; mind taxes._")
    else:
        L.append("\n## Drift vs targets\n_No targets file. Pass `--targets targets.csv` (asset_class,target_pct) to enable._")

    L.append("\n## Performance (context — not time-weighted)")
    L.append(f"- Unrealized return on equity holdings (value vs cost): **{unreal*100:+.1f}%**" if unreal is not None else "- Unrealized return: —")
    L.append(f"- SPY for context: YTD {ytd*100:+.1f}% · 1Y {y1*100:+.1f}%" if ytd is not None else "- SPY context unavailable")
    L.append("- _True alpha needs transaction history (TWR). This is a snapshot, not a track record._")

    tlh = [h for h in eq_sorted if h["pl"] < 0]
    L.append("\n## Tax-loss harvesting candidates")
    if tlh:
        L.append("| Ticker | Acct | Unrealized loss | % | Holding |")
        L.append("|---|---|--:|--:|:--:|")
        for h in sorted(tlh, key=lambda x: x["pl"]):
            hold = "—" if h["lt"] is None else ("LT" if h["lt"] else "ST")
            L.append(f"| {h['ticker']} | {h['account']} | {fnum(h['pl'])} | {h['plpct']*100:.1f}% | {hold} |")
        L.append("\n_Prioritize ST losses (offset higher-taxed ST gains); $3k/yr offsets ordinary income, "
                 "rest carries forward. Watch the 30-day wash-sale window across ALL accounts (incl. IRAs/DRIPs)._")
    else:
        L.append("_No positions at an unrealized loss._")

    report = "\n".join(L)
    if args.out:
        with open(args.out, "w") as f:
            f.write(report + "\n")
        print(f"Wrote {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
