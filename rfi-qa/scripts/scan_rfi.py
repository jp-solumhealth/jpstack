#!/usr/bin/env python3
"""Deterministic QA scan of a client RFI Google Sheet.

Input: the JSON saved from the Google Sheets `get_spreadsheet` call described in
SKILL.md (includeGridData=true plus the field mask listed there).

It reads every place a value can hide in a sheet (cells, formulas, notes, links,
smart chips, dropdown option lists, conditional-format rules, named ranges,
protected ranges, filter views, hidden rows, columns and tabs) and flags:

  FOREIGN_ORG      text naming a company that is not the client, a payer or a known vendor.
                   Any hit in a dropdown option list, note or hidden place is a hard failure.
  FOREIGN_DOMAIN   an email domain that is neither the client's nor Solum's
  DOMAIN_TYPO      an email domain a character or two away from the client's domain
  NPI              every 10-digit number that passes the NPI check digit, with the NPI
                   type its column implies (Group -> NPI-2, Individual -> NPI-1).
                   Each one still has to be looked up in NPPES (see SKILL.md).
  BAD_NPI          a 10-digit number in an NPI column that fails the check digit
  PLACEHOLDER      template text left in a data or answer cell ("please add the rest", "TBD")
  STATUS_MISMATCH  Completed with an empty answer, or Pending with an answer
  HARDCODED_COUNT  a progress counter typed as text instead of a formula
  HEADERLESS_DV    a dropdown column with no header
  EMPTY_TAB        a tab with headers and no data rows
  HIDDEN           hidden tabs, rows or columns (shared with the client even if hidden)

Usage:
  python3 -I scan_rfi.py SHEET.json --client "Client Name" [--client "Legal name"] \
      --domain clientdomain.com [--allow "Extra payer or vendor"]

Exit code 1 on any hard failure (FOREIGN_ORG, FOREIGN_DOMAIN, BAD_NPI), so a caller can
gate on it. Nothing is written to disk; client data stays in the conversation.
"""
import argparse
import difflib
import json
import re
import sys

LEGAL_SUFFIX = re.compile(r"\b(LLC|L\.L\.C\.?|Inc\.?|Incorporated|Corp\.?|Corporation|PLLC|LLP|Ltd\.?|P\.C\.|PC|PA|Co\.)\b")
ORG_WORD = re.compile(
    r"\b(ABA|Autism|Behavioral|Behavior|Therapy|Therapies|Clinic|Center|Centre|Health|Healthcare|"
    r"Group|Solutions|Services|Pediatrics|Partners|Associates|Academy|Institute|Agency|Network)\b", re.I)

# Organizations that legitimately appear in an RFI: payers, clearinghouses, EHRs, portals.
DEFAULT_ALLOW = [
    "medicaid", "medicare", "health first colorado", "aetna", "anthem", "bcbs", "blue cross", "blue shield",
    "cigna", "evernorth", "unitedhealthcare", "united healthcare", "uhc", "optum", "humana", "tricare",
    "kaiser", "molina", "centene", "ambetter", "wellcare", "magellan", "carelon", "beacon", "medica",
    "highmark", "elevance", "caresource", "amerigroup", "oscar", "oxford", "umr", "meritain", "aetna better health",
    "availity", "change healthcare", "waystar", "stedi", "office ally", "trizetto", "navinet",
    "centralreach", "central reach", "rethink", "catalyst", "theralytics", "aloha", "motivity", "ensora",
    "therapynotes", "simplepractice", "kareo", "athena", "nppes", "cms", "caqh",
    "solum", "getsolum",
]
# RFI vocabulary that contains org-looking words but is not a company.
GENERIC = [
    "home", "clinic", "school", "community", "telehealth", "office", "day care", "daycare",
    "group npi", "behavior analyst", "assistant behavior analyst", "behavior technician",
    "aba direct", "aba services", "aba therapy", "behavioral health", "mental health",
    "health plan", "health insurance", "place of service", "places of service",
]
ORG_PHRASE = re.compile(
    r"\b(?:[A-Z][A-Za-z'&.\-]+\s+){1,5}(?:ABA|Autism|Behavioral|Behavior|Therapy|Therapies|Clinic|Center|"
    r"Centre|Health|Healthcare|Group|Solutions|Services|Pediatrics|Partners|Associates|Academy|Institute|"
    r"Agency|Network)\b")
HEADER_HINT = re.compile(r"comment|source|question|note|detail|item|instruction|how to use", re.I)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})")
TEN = re.compile(r"(?<![\d-])(\d{10})(?![\d-])")
PLACEHOLDER_RE = re.compile(r"please (add|fill|complete)|\btbd\b|\btbc\b|\bxx+\b|lorem|placeholder|\[[^\]]*\]|<[^>]*>|\?\?", re.I)


def col(i):
    s, i = "", i + 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def npi_ok(n):
    """NPI check digit: Luhn over the prefix 80840 plus the 10 digits."""
    total = 0
    for idx, d in enumerate(int(c) for c in reversed("80840" + n)):
        if idx % 2 == 1:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", s.lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet_json")
    ap.add_argument("--client", action="append", required=True, help="client name variant; repeat")
    ap.add_argument("--domain", required=True, help="client email domain")
    ap.add_argument("--own-domain", action="append", default=["getsolum.com"])
    ap.add_argument("--allow", action="append", default=[], help="extra payer/vendor allowed to appear")
    a = ap.parse_args()

    client = [norm(t).strip() for t in a.client]
    client_compact = [t.replace(" ", "") for t in client]
    allow = [norm(t).strip() for t in DEFAULT_ALLOW + a.allow]
    ok_domains = {a.domain.lower()} | {d.lower() for d in a.own_domain}

    data = json.load(open(a.sheet_json))
    data = data.get("content", data)
    flags = []

    def flag(kind, where, text):
        flags.append((kind, where, str(text)[:140]))

    def foreign_org(text):
        """Return the offending text if it names an organization that is not allowed."""
        n = " " + norm(text) + " "
        compact = n.replace(" ", "")
        if any(c and (f" {c} " in n or c in compact) for c in client + client_compact):
            # Client named in the string; still check the rest of a list like "X LLC, Y LLC".
            parts = re.split(r"[;\n]|,(?=\s*[A-Z])", text)
            if len(parts) == 1:
                return None
            hits = [p for p in parts if foreign_org(p)]
            return "; ".join(hits) or None
        if LEGAL_SUFFIX.search(text):
            return text.strip()
        # A capitalized name ending in an org word ("Sunny Path ABA", "Bright Path Therapy").
        for m in ORG_PHRASE.finditer(text):
            phrase = " " + norm(m.group(0)) + " "
            for t in sorted(allow + GENERIC, key=len, reverse=True):
                phrase = phrase.replace(f" {t} ", " ")
            name_words = [w for w in phrase.split() if not ORG_WORD.fullmatch(w)]
            if name_words:
                return text.strip()
        return None

    def check_text(where, text, kind_place, header=""):
        if not text:
            return
        hit = foreign_org(text)
        if hit:
            flag("FOREIGN_ORG", where, hit)
        for m in EMAIL_RE.finditer(text):
            dom = m.group(1).lower()
            if dom in ok_domains or any(dom.endswith("." + d) for d in ok_domains):
                continue
            close = difflib.SequenceMatcher(None, dom, a.domain.lower()).ratio()
            flag("DOMAIN_TYPO" if close >= 0.85 else "FOREIGN_DOMAIN", where, m.group(0))
        for m in TEN.finditer(text):
            n = m.group(1)
            h = header.lower()
            want = "NPI-2 (organization)" if "group" in h or "organization" in h else (
                "NPI-1 (individual)" if "individual" in h or "rendering" in h else "type unknown")
            if npi_ok(n):
                flag("NPI", where, f"{n}  expected {want}  [{header}]")
            elif "npi" in h:
                flag("BAD_NPI", where, f"{n} fails the NPI check digit")
        if kind_place == "data" and PLACEHOLDER_RE.search(text) and not HEADER_HINT.search(header):
            flag("PLACEHOLDER", where, text)

    print("TITLE:", data["properties"]["title"])
    check_text("spreadsheet title", data["properties"]["title"], "meta")
    for nr in data.get("namedRanges", []) or []:
        flag("NAMED_RANGE", "spreadsheet", nr.get("name"))
        check_text("named range", nr.get("name", ""), "meta")
    if data.get("developerMetadata"):
        check_text("developer metadata", json.dumps(data["developerMetadata"]), "meta")

    for sh in data["sheets"]:
        p = sh["properties"]
        t = p["title"]
        print(f"\n===== TAB '{t}'")
        if p.get("hidden"):
            flag("HIDDEN", t, "whole tab is hidden but still shared with the client")
        check_text(f"{t} (tab name)", t, "meta")
        for k in ("protectedRanges", "filterViews", "basicFilter", "developerMetadata"):
            if sh.get(k):
                check_text(f"{t} {k}", json.dumps(sh[k]), "meta")
        for cf in sh.get("conditionalFormats", []) or []:
            rule = cf.get("booleanRule") or cf.get("gradientRule") or {}
            for v in rule.get("condition", {}).get("values", []) or []:
                check_text(f"{t} conditional format", v.get("userEnteredValue", ""), "meta")

        for g in sh.get("data", []):
            r0, c0 = g.get("startRow", 0), g.get("startColumn", 0)
            hr = [r0 + i + 1 for i, m in enumerate(g.get("rowMetadata", []) or []) if m.get("hiddenByUser")]
            hc = [col(c0 + i) for i, m in enumerate(g.get("columnMetadata", []) or []) if m.get("hiddenByUser")]
            if hr:
                flag("HIDDEN", t, f"hidden rows {hr}")
            if hc:
                flag("HIDDEN", t, f"hidden columns {hc}")

            rows = g.get("rowData", []) or []
            grid = [[(v.get("formattedValue") or "").strip() for v in (row.get("values") or [])] for row in rows]

            def is_header(vals):
                filled = [v for v in vals if v]
                return len(filled) >= 3 and all(len(v) <= 45 and not re.fullmatch(r"[\d ,.$%-]+", v) for v in filled)

            # First header-like row, plus later ones that start a new section after a blank row.
            header_rows = []
            for i, vals in enumerate(grid):
                if is_header(vals) and (not header_rows or (i > 0 and not any(grid[i - 1]))):
                    header_rows.append(i)
            first_header = header_rows[0] if header_rows else None

            def header_for(ri, ci):
                for h in reversed([x for x in header_rows if x < ri]):
                    if ci < len(grid[h]) and grid[h][ci]:
                        return grid[h][ci]
                return ""

            dvs = {}
            data_rows = 0
            for ri, row in enumerate(rows):
                if first_header is not None and ri > first_header and ri not in header_rows and any(grid[ri]):
                    data_rows += 1
                for ci, v in enumerate(row.get("values", []) or []):
                    addr = f"{t}!{col(c0 + ci)}{r0 + ri + 1}"
                    hdr = header_for(ri, ci)
                    place = "data" if (first_header is not None and ri > first_header and ri not in header_rows
                                       and ci > 0) else "label"
                    uev = v.get("userEnteredValue", {}) or {}
                    fv = v.get("formattedValue") or ""
                    if "formulaValue" in uev:
                        check_text(addr + " formula", uev["formulaValue"], "meta", hdr)
                    if fv:
                        check_text(addr, fv, place, hdr)
                        if re.fullmatch(r"\s*\d+\s+of\s+\d+\s+completed\s*", fv, re.I) and "formulaValue" not in uev:
                            flag("HARDCODED_COUNT", addr, fv)
                    if v.get("note"):
                        flag("NOTE", addr, v["note"])
                        check_text(addr + " note", v["note"], "meta", hdr)
                    if v.get("hyperlink"):
                        check_text(addr + " link", v["hyperlink"], "meta", hdr)
                    if v.get("chipRuns"):
                        check_text(addr + " smart chip", json.dumps(v["chipRuns"]), "meta", hdr)
                    dv = v.get("dataValidation")
                    if dv:
                        cond = dv.get("condition", {})
                        vals = tuple(x.get("userEnteredValue", "") for x in cond.get("values", []) or [])
                        dvs.setdefault((ci, cond.get("type"), vals), []).append(ri)

            for (ci, typ, vals), rws in dvs.items():
                rng = f"{t}!{col(c0 + ci)}{r0 + min(rws) + 1}:{col(c0 + ci)}{r0 + max(rws) + 1}"
                print(f"  DROPDOWN {rng} ({len(rws)} cells) {typ} {list(vals)}")
                for v in vals:
                    check_text(rng + " dropdown option", v, "meta")
                if not header_for(min(rws), ci):
                    flag("HEADERLESS_DV", rng, "dropdown column has no header above it")
            if first_header is not None and data_rows == 0:
                flag("EMPTY_TAB", t, "headers but no data rows")

            # Status vs answer on the main RFI tab (STATUS / ANSWERS columns).
            if first_header is not None:
                hdrs = [h.upper() for h in grid[first_header]]
                if "STATUS" in hdrs and "ANSWERS" in hdrs:
                    si, ai = hdrs.index("STATUS"), hdrs.index("ANSWERS")
                    for ri in range(first_header + 1, len(grid)):
                        vals = grid[ri] + [""] * 10
                        status, answer, q = vals[si], vals[ai], vals[0]
                        where = f"{t}!row {r0 + ri + 1}"
                        if status == "Completed" and not answer:
                            flag("STATUS_MISMATCH", where, f"Completed, ANSWERS empty: {q}")
                        elif status.startswith("Pending") and answer:
                            flag("STATUS_MISMATCH", where, f"Pending, but answered: {answer}")

    print("\n===== FLAGS")
    order = ["FOREIGN_ORG", "FOREIGN_DOMAIN", "BAD_NPI", "DOMAIN_TYPO", "NPI", "HIDDEN", "NOTE",
             "NAMED_RANGE", "STATUS_MISMATCH", "HARDCODED_COUNT", "PLACEHOLDER", "HEADERLESS_DV", "EMPTY_TAB"]
    seen = set()
    for kind, where, text in sorted(flags, key=lambda f: order.index(f[0])):
        if (kind, where, text) in seen:
            continue
        seen.add((kind, where, text))
        print(f"{kind:16} {where:44} {text}")
    hard = [f for f in flags if f[0] in ("FOREIGN_ORG", "FOREIGN_DOMAIN", "BAD_NPI")]
    print(f"\n{len(seen)} flags, {len(hard)} hard failures.")
    print("RESULT:", "FAIL - remove every foreign organization before the client sees this sheet" if hard
          else "PASS on automated checks. Still verify every NPI in NPPES and read the sheet by hand.")
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    main()
