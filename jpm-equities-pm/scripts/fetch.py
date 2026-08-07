#!/usr/bin/env python3
"""fetch.py — pull free fundamentals + market data for a ticker.

Sources (no paid key):
  - SEC EDGAR companyfacts API (data.sec.gov) for reported financials.
  - yfinance (Yahoo) for price, shares, beta (computed by regression vs SPY), dividends.

Usage:
  python3 fetch.py AAPL                 # human-readable summary to stdout
  python3 fetch.py AAPL --json out.json # also dump structured data
  python3 fetch.py AAPL --years 5

Degrades gracefully: if a source/package/network fails, it says so and tells you which
numbers to paste in manually. It never invents data.

SEC requires a descriptive User-Agent with contact info. Set EDGAR_UA env var, e.g.:
  export EDGAR_UA="JP Montoya jp@getsolum.com"
"""
import argparse, json, os, sys, datetime, urllib.request, urllib.error

EDGAR_UA = os.environ.get("EDGAR_UA", "equity-research-skill contact: jp@getsolum.com")
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

# US-GAAP concepts we care about (first match wins per line item)
CONCEPTS = {
    "Revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet"],
    "NetIncome": ["NetIncomeLoss"],
    "OperatingIncome": ["OperatingIncomeLoss"],
    "GrossProfit": ["GrossProfit"],
    "OCF": ["NetCashProvidedByUsedInOperatingActivities"],
    "Capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "Assets": ["Assets"],
    "Equity": ["StockholdersEquity"],
    "LongTermDebt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "Cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "SharesDiluted": ["WeightedAverageNumberOfDilutedSharesOutstanding"],
}


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": EDGAR_UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def cik_for(ticker):
    data = _get(TICKERS_URL)
    t = ticker.upper()
    for row in data.values():
        if row.get("ticker", "").upper() == t:
            return int(row["cik_str"]), row.get("title", "")
    return None, None


def annual_series(facts, concept_list, years):
    """Return list of (fy, val) for annual (FY) facts, most recent `years`.

    Companies report the same line item under different US-GAAP tags over time (e.g. Apple's
    revenue moved from 'Revenues' to 'RevenueFromContractWithCustomerExcludingAssessedTax').
    A naive 'first tag with any data' pick can latch onto a stale tag, so evaluate ALL candidate
    tags and choose the one with the most recent fiscal year (tie-break: most data points).
    """
    usgaap = facts.get("facts", {}).get("us-gaap", {})
    best = None  # (latest_fy, n_points, series)
    for c in concept_list:
        if c not in usgaap:
            continue
        units = usgaap[c].get("units", {})
        key = "USD" if "USD" in units else ("shares" if "shares" in units else None)
        if not key:
            continue
        out = {}
        for p in units[key]:
            if p.get("fp") == "FY" and p.get("form") in ("10-K", "20-F") and p.get("fy"):
                out[p["fy"]] = p["val"]  # later filings overwrite -> latest restatement
        if not out:
            continue
        cand = (max(out), len(out), [(fy, out[fy]) for fy in sorted(out)[-years:]])
        if best is None or (cand[0], cand[1]) > (best[0], best[1]):
            best = cand
    return best[2] if best else []


def fetch_edgar(ticker, years):
    cik, title = cik_for(ticker)
    if cik is None:
        return {"error": f"no CIK found for {ticker} (foreign/ETF/not in EDGAR?)"}
    facts = _get(FACTS_URL.format(cik=cik))
    res = {"cik": cik, "name": title, "financials": {}}
    for label, concepts in CONCEPTS.items():
        s = annual_series(facts, concepts, years)
        if s:
            res["financials"][label] = {str(fy): v for fy, v in s}
    return res


def fetch_market(ticker):
    try:
        import yfinance as yf
    except ImportError:
        return {"error": "yfinance not installed — run: python3 -m pip install yfinance"}
    out = {}
    try:
        tk = yf.Ticker(ticker)
        fast = getattr(tk, "fast_info", {}) or {}
        out["price"] = fast.get("last_price") or fast.get("lastPrice")
        out["shares_out"] = fast.get("shares") or fast.get("sharesOutstanding")
        out["market_cap"] = fast.get("market_cap") or fast.get("marketCap")
        info = {}
        try:
            info = tk.get_info()
        except Exception:
            pass
        out["beta_yahoo"] = info.get("beta")
        out["sector"] = info.get("sector")
        out["name"] = info.get("longName") or info.get("shortName")
        out["beta_regressed"] = regressed_beta(ticker)
    except Exception as e:
        out["error"] = f"yfinance error: {e}"
    return out


def regressed_beta(ticker, lookback="3y"):
    """Beta = cov(stock, mkt)/var(mkt) on weekly returns vs SPY. Returns None on failure."""
    try:
        import yfinance as yf
        df = yf.download([ticker, "SPY"], period=lookback, interval="1wk",
                         auto_adjust=True, progress=False)["Close"].dropna()
        if len(df) < 30:
            return None
        rets = df.pct_change().dropna()
        cov = rets[ticker].cov(rets["SPY"])
        var = rets["SPY"].var()
        return round(cov / var, 2) if var else None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description="Fetch free fundamentals + market data for a ticker.")
    ap.add_argument("ticker")
    ap.add_argument("--years", type=int, default=5)
    ap.add_argument("--json", help="write structured JSON to this path")
    args = ap.parse_args()
    t = args.ticker.upper()
    today = datetime.date.today().isoformat()

    print(f"# {t} — data pull ({today})")
    print(f"# EDGAR User-Agent: {EDGAR_UA}\n")

    edgar = {}
    try:
        edgar = fetch_edgar(t, args.years)
    except urllib.error.HTTPError as e:
        edgar = {"error": f"EDGAR HTTP {e.code} — set EDGAR_UA env var with your name+email"}
    except Exception as e:
        edgar = {"error": f"EDGAR fetch failed: {e}"}

    market = fetch_market(t)

    if edgar.get("error"):
        print(f"[EDGAR] {edgar['error']}\n  -> paste the income statement / balance sheet from the 10-K.")
    else:
        print(f"[EDGAR] {edgar.get('name','')} (CIK {edgar.get('cik')})")
        fin = edgar.get("financials", {})
        for label, series in fin.items():
            vals = ", ".join(f"{fy}:{v:,}" for fy, v in series.items())
            print(f"  {label}: {vals}")
        if not fin:
            print("  no annual us-gaap facts parsed — read the 10-K directly.")

    print()
    if market.get("error"):
        print(f"[Market] {market['error']}\n  -> paste current price, diluted shares, and beta.")
    else:
        print(f"[Market] price={market.get('price')}  shares_out={market.get('shares_out')}  "
              f"mktcap={market.get('market_cap')}")
        print(f"         beta (regressed vs SPY)={market.get('beta_regressed')}  "
              f"beta (Yahoo) [ESTIMATE]={market.get('beta_yahoo')}  sector={market.get('sector')}")

    print("\nNOTE: verify every figure's as-of date. Consensus estimates are NOT pulled here — "
          "tag any you add as [ESTIMATE]. Read the primary filing for anything that matters.")

    if args.json:
        with open(args.json, "w") as f:
            json.dump({"ticker": t, "as_of": today, "edgar": edgar, "market": market}, f, indent=2)
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    main()
