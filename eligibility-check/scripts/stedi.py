#!/usr/bin/env python3
"""Stedi healthcare client: payer search + real-time eligibility checks (270/271).

Reads STEDI_API_KEY from the environment (or a .env file in the repo root).
Stdlib only — no pip install needed.

Usage:
  stedi.py payers "aetna"
  stedi.py payers "blue cross" --page-size 20
  stedi.py payer 60054
  stedi.py check --payer 60054 --npi 1999999984 --org "Solum Health" \
      --first Jane --last Doe --dob 19000101 --member-id AETNA12345 \
      --service-type 30 --save outputs/jane-doe.json
  stedi.py check --input request.json
  stedi.py batch 01a00614-0d77-76f2-9797-ef935558b834 --results --save-dir outputs/batch
  stedi.py roster patients.csv --payer-column payerId --out outputs/roster.csv

`batch` inspects a batch submitted to Stedi's async Batch Eligibility API or
uploaded as CSV in the portal. `roster` is the local alternative: one real-time
check per CSV row, no batch involved.

Every command exits non-zero on transport or API errors, and on eligibility
responses that carry AAA rejection errors, so it can be used in scripts.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

# Real-time checks and payer lookups live on the healthcare host; everything about
# batches lives on the eligibility-manager host. Sending a batch request to the
# healthcare host is a 404, which reads like "batch not found" — it is not.
BASE_URL = os.environ.get("STEDI_BASE_URL", "https://healthcare.us.stedi.com")
MANAGER_URL = os.environ.get("STEDI_MANAGER_URL", "https://manager.us.stedi.com")
API_VERSION = "2024-04-01"
TIMEOUT = 60

# EB01 benefit codes, for responses where the payer omits the human-readable name.
BENEFIT_CODES = {
    "1": "Active Coverage",
    "2": "Active - Full Risk Capitation",
    "3": "Active - Services Capitated",
    "4": "Active - Services Capitated to Primary Care Physician",
    "5": "Active - Pending Investigation",
    "6": "Inactive",
    "7": "Inactive - Pending Eligibility Update",
    "8": "Inactive - Pending Investigation",
    "A": "Co-Insurance",
    "B": "Co-Payment",
    "C": "Deductible",
    "CB": "Coverage Basis",
    "D": "Benefit Description",
    "E": "Exclusions",
    "F": "Limitations",
    "G": "Out of Pocket (Stop Loss)",
    "H": "Unlimited",
    "I": "Non-Covered",
    "J": "Cost Containment",
    "K": "Reserve",
    "L": "Primary Care Provider",
    "M": "Pre-existing Condition",
    "MC": "Managed Care Coordinator",
    "N": "Services Restricted to Following Provider",
    "O": "Not Deemed a Medical Necessity",
    "P": "Benefit Disclaimer",
    "Q": "Second Surgical Opinion Required",
    "R": "Other or Additional Payor",
    "S": "Prior Year(s) History",
    "T": "Card Report Lost/Stolen",
    "U": "Contact Following Entity for Eligibility or Benefit Information",
    "V": "Cannot Process",
    "W": "Other Source of Data",
    "X": "Health Care Facility",
    "Y": "Spend Down",
}

NETWORK_INDICATOR = {"Y": "in-network", "N": "out-of-network", "W": "not applicable", "U": "unknown"}

# Benefit categories worth pulling to the top of a summary.
FINANCIAL_NAMES = ("Co-Payment", "Co-Insurance", "Deductible", "Out of Pocket (Stop Loss)")


class StediError(RuntimeError):
    """An error returned by Stedi, or a local validation failure."""


# --------------------------------------------------------------------------- auth


def load_dotenv() -> None:
    """Populate os.environ from the repo-root .env, without overriding real env vars."""
    env_path = pathlib.Path(__file__).resolve().parents[2] / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def api_key() -> str:
    load_dotenv()
    key = os.environ.get("STEDI_API_KEY", "").strip()
    if not key:
        raise StediError(
            "STEDI_API_KEY is not set. Export it, or copy .env.example to .env and fill it in."
        )
    return key


# ---------------------------------------------------------------------- transport


def request(
    method: str,
    path: str,
    params: dict | None = None,
    body: dict | None = None,
    base: str | None = None,
) -> dict:
    url = f"{base or BASE_URL}/{API_VERSION}/{path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})

    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    # Stedi takes the raw API key in Authorization — no "Bearer " prefix.
    req.add_header("Authorization", api_key())
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            raise StediError(f"HTTP {exc.code} from {method} {path}: {raw[:500]}") from exc
        detail = payload.get("message") or payload.get("error") or json.dumps(payload)[:500]
        hint = ""
        if exc.code in (401, 403):
            hint = " (check STEDI_API_KEY, and that the key's account has this API enabled)"
        elif exc.code == 404:
            hint = (
                " (a batch or check id is only visible to the key that created it —"
                " test and live keys see separate data, as do separate Stedi accounts)"
            )
        raise StediError(f"HTTP {exc.code} from {method} {path}{hint}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise StediError(f"Could not reach {url}: {exc.reason}") from exc


# ------------------------------------------------------------------- validation


def validate_npi(npi: str) -> str:
    """Check the 10-digit NPI Luhn check digit. Payers reject bad NPIs at the edge."""
    npi = re.sub(r"\D", "", npi or "")
    if len(npi) != 10:
        raise StediError(f"NPI must be 10 digits, got {npi or '(empty)'!r}")
    # NPI Luhn is computed over the 9-digit base prefixed with the 80840 issuer id.
    digits = [int(d) for d in "80840" + npi[:9]]
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    if (total + int(npi[9])) % 10 != 0:
        raise StediError(f"NPI {npi} fails check-digit validation")
    return npi


def validate_date(value: str, field: str) -> str:
    value = re.sub(r"\D", "", value or "")
    if len(value) != 8:
        raise StediError(f"{field} must be YYYYMMDD, got {value or '(empty)'!r}")
    return value


def build_request(args: argparse.Namespace) -> dict:
    """Assemble an eligibility request body from CLI flags."""
    if not (args.member_id or args.dob or args.last):
        raise StediError("Supply at least one of --member-id, --dob, --last")

    subscriber: dict = {}
    if args.member_id:
        subscriber["memberId"] = args.member_id
    if args.first:
        subscriber["firstName"] = args.first
    if args.last:
        subscriber["lastName"] = args.last
    if args.dob:
        subscriber["dateOfBirth"] = validate_date(args.dob, "--dob")

    encounter: dict = {}
    if args.service_type:
        encounter["serviceTypeCodes"] = list(args.service_type)
    if args.dos:
        encounter["dateOfService"] = validate_date(args.dos, "--dos")
    if args.procedure_code:
        encounter["procedureCode"] = args.procedure_code
        encounter["productOrServiceIDQualifier"] = args.procedure_qualifier

    body: dict = {
        "tradingPartnerServiceId": args.payer,
        "provider": {"organizationName": args.org, "npi": validate_npi(args.npi)},
        "subscriber": subscriber,
    }
    if encounter:
        body["encounter"] = encounter
    if args.dependent_first or args.dependent_last or args.dependent_dob:
        dependent: dict = {}
        if args.dependent_first:
            dependent["firstName"] = args.dependent_first
        if args.dependent_last:
            dependent["lastName"] = args.dependent_last
        if args.dependent_dob:
            dependent["dateOfBirth"] = validate_date(args.dependent_dob, "--dependent-dob")
        body["dependents"] = [dependent]
    return body


# --------------------------------------------------------------------- rendering


def benefit_name(entry: dict) -> str:
    return entry.get("name") or BENEFIT_CODES.get(entry.get("code", ""), entry.get("code", "?"))


def amount_of(entry: dict) -> str:
    if entry.get("benefitAmount") not in (None, ""):
        return f"${entry['benefitAmount']}"
    if entry.get("benefitPercent") not in (None, ""):
        try:
            return f"{float(entry['benefitPercent']) * 100:g}%"
        except (TypeError, ValueError):
            return f"{entry['benefitPercent']}"
    return ""


def coverage_status(response: dict) -> str:
    """Prefer planStatus, fall back to the EB01 active/inactive codes."""
    for plan in response.get("planStatus") or []:
        if plan.get("status"):
            return plan["status"]
    for entry in response.get("benefitsInformation") or []:
        if entry.get("code") in ("1", "2", "3", "4", "5"):
            return benefit_name(entry)
        if entry.get("code") in ("6", "7", "8"):
            return benefit_name(entry)
    return "Unknown"


def collect_errors(response: dict) -> list[str]:
    """Gather AAA rejection errors from wherever the payer put them."""
    messages: list[str] = []

    def walk(node, path="") -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "errors" and isinstance(value, list):
                    for err in value:
                        if not isinstance(err, dict):
                            continue
                        code = err.get("code", "")
                        text = err.get("description") or err.get("message") or ""
                        loc = f" [{path}]" if path else ""
                        messages.append(f"{code} {text}".strip() + loc)
                else:
                    walk(value, f"{path}.{key}" if path else key)
        elif isinstance(node, list):
            for item in node:
                walk(item, path)

    walk(response)
    return messages


def summarize(response: dict) -> str:
    lines: list[str] = []
    subscriber = response.get("subscriber") or {}
    payer = response.get("payer") or {}

    name = " ".join(x for x in (subscriber.get("firstName"), subscriber.get("lastName")) if x)
    lines.append(f"Coverage status : {coverage_status(response)}")
    if name:
        lines.append(f"Member          : {name} ({subscriber.get('memberId', 'no member id')})")
    if payer.get("name"):
        lines.append(f"Payer           : {payer['name']}")
    if response.get("meta", {}).get("traceId"):
        lines.append(f"Trace ID        : {response['meta']['traceId']}")

    for plan in response.get("planStatus") or []:
        detail = plan.get("planDetails") or ""
        stcs = ", ".join(plan.get("serviceTypeCodes") or [])
        bits = [b for b in (plan.get("status"), detail, f"STC {stcs}" if stcs else "") if b]
        lines.append("Plan            : " + " | ".join(bits))

    for period, value in (response.get("planDateInformation") or {}).items():
        lines.append(f"{period:<16}: {value}")

    benefits = response.get("benefitsInformation") or []
    financial = [b for b in benefits if benefit_name(b) in FINANCIAL_NAMES]
    if financial:
        lines.append("")
        lines.append("Cost share:")
        for entry in financial:
            amount = amount_of(entry)
            parts = [
                benefit_name(entry),
                amount,
                entry.get("coverageLevel") or "",
                entry.get("timeQualifier") or "",
                NETWORK_INDICATOR.get(entry.get("inPlanNetworkIndicatorCode", ""), ""),
            ]
            stcs = ", ".join(entry.get("serviceTypeCodes") or [])
            if stcs:
                parts.append(f"STC {stcs}")
            lines.append("  - " + " | ".join(p for p in parts if p))

    other = [b for b in benefits if benefit_name(b) not in FINANCIAL_NAMES]
    if other:
        lines.append("")
        lines.append(f"Other benefit lines ({len(other)}):")
        for entry in other[:15]:
            note = entry.get("benefitsDateInformation") or entry.get("additionalInformation") or ""
            if isinstance(note, (dict, list)):
                note = json.dumps(note)
            desc = " | ".join(
                p
                for p in (
                    benefit_name(entry),
                    ", ".join(entry.get("serviceTypeCodes") or []),
                    amount_of(entry),
                    str(note)[:80],
                )
                if p
            )
            lines.append(f"  - {desc}")
        if len(other) > 15:
            lines.append(f"  ... {len(other) - 15} more (see the saved JSON)")

    errors = collect_errors(response)
    if errors:
        lines.append("")
        lines.append("Errors reported by the payer:")
        lines.extend(f"  ! {e}" for e in errors)

    return "\n".join(lines)


def save_json(path: str, payload: dict) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nRaw response saved to {target} (contains PHI — keep it out of git)")


# --------------------------------------------------------------------- commands


def cmd_payers(args: argparse.Namespace) -> int:
    result = request(
        "GET",
        "payers/search",
        params={
            "query": args.query,
            "pageSize": args.page_size,
            "eligibilityCheck": "SUPPORTED" if args.eligibility_only else None,
        },
    )
    items = result.get("items") or result.get("payers") or []
    if not items:
        print(f"No payers matched {args.query!r}")
        return 1
    for item in items:
        payer = item.get("payer", item)
        aliases = ", ".join(payer.get("aliases") or [])
        print(f"{payer.get('primaryPayerId', '?'):<12} {payer.get('displayName') or payer.get('name', '?')}")
        print(f"{'':<12} stediId={payer.get('stediId', '?')}" + (f"  aliases={aliases}" if aliases else ""))
    return 0


def cmd_payer(args: argparse.Namespace) -> int:
    print(json.dumps(request("GET", f"payer/{urllib.parse.quote(args.stedi_id)}"), indent=2))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    if args.input:
        body = json.loads(pathlib.Path(args.input).read_text(encoding="utf-8"))
    else:
        missing = [f for f in ("payer", "npi", "org") if not getattr(args, f)]
        if missing:
            raise StediError("Missing required flags: " + ", ".join("--" + m for m in missing))
        body = build_request(args)

    if args.dry_run:
        print(json.dumps(body, indent=2))
        return 0

    response = request("POST", "change/medicalnetwork/eligibility/v3", body=body)

    if args.raw:
        print(json.dumps(response, indent=2))
    else:
        print(summarize(response))
    if args.save:
        save_json(args.save, response)

    return 1 if collect_errors(response) else 0


def pick(source: dict, *keys: str, default: str = "") -> str:
    """First present, non-empty value among `keys`. Shields against field renames."""
    for key in keys:
        value = source.get(key)
        if value not in (None, "", [], {}):
            return value if isinstance(value, str) else json.dumps(value)
    return default


def paged(path: str, params: dict | None = None, max_pages: int = 50) -> list[dict]:
    """Collect every page of a list endpoint, following whichever cursor key it uses."""
    items: list[dict] = []
    params = dict(params or {})
    for _ in range(max_pages):
        page = request("GET", path, params=params, base=MANAGER_URL)
        items.extend(page.get("items") or page.get("checks") or page.get("results") or [])
        cursor = page.get("nextPageToken") or page.get("nextCursor") or page.get("pageToken")
        if not cursor:
            return items
        params["pageToken"] = cursor
    print(f"Warning: stopped after {max_pages} pages; results may be truncated", file=sys.stderr)
    return items


def cmd_batch(args: argparse.Namespace) -> int:
    """Inspect a batch submitted to the async Batch Eligibility API or via portal CSV."""
    batch_id = urllib.parse.quote(args.batch_id)

    status = request("GET", f"eligibility-manager/batch/{batch_id}", base=MANAGER_URL)
    print(f"Batch {args.batch_id}")
    print(f"  status     : {pick(status, 'status', 'batchStatus', default='unknown')}")
    for label, keys in (
        ("submitted ", ("createdAt", "submittedAt")),
        ("updated   ", ("updatedAt", "completedAt")),
        ("total     ", ("totalCount", "total", "checkCount")),
        ("completed ", ("completedCount", "completed")),
        ("errored   ", ("errorCount", "failedCount", "errors")),
        ("name      ", ("name", "filename", "description")),
    ):
        value = pick(status, *keys)
        if value != "":
            print(f"  {label}: {value}")

    items = paged(f"eligibility-manager/batch/{batch_id}/items", {"pageSize": args.page_size})
    if not items:
        print("\nNo per-check items returned. The batch may still be queued, or the id may "
              "belong to another account.")
        return 1

    tally: dict[str, int] = {}
    failures: list[tuple[str, str, str]] = []
    for item in items:
        state = pick(item, "status", "state", default="unknown")
        tally[state] = tally.get(state, 0) + 1
        if state.upper() not in ("COMPLETED", "SUCCESS", "SUCCEEDED"):
            subscriber = item.get("subscriber") or item.get("member") or {}
            who = " ".join(
                x for x in (subscriber.get("firstName", ""), subscriber.get("lastName", "")) if x
            ) or pick(subscriber, "memberId", default="?")
            reason = pick(item, "error", "errorMessage", "failureReason", "message")
            if not reason:
                nested = collect_errors(item)
                reason = "; ".join(nested) if nested else ""
            failures.append((pick(item, "eligibilityCheckId", "checkId", "id", default="?"), who, reason))

    print(f"\nChecks ({len(items)}):")
    for state, count in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {count:>5}  {state}")

    if failures:
        print(f"\nNot completed ({len(failures)}):")
        for check_id, who, reason in failures[: args.max_failures]:
            print(f"  {check_id}  {who}  {reason}"[:200])
        if len(failures) > args.max_failures:
            print(f"  ... {len(failures) - args.max_failures} more (raise --max-failures)")

    if args.results:
        completed = paged(
            "eligibility-manager/polling/batch-eligibility", {"batchId": args.batch_id}
        )
        print(f"\nCompleted results returned by polling: {len(completed)}")
        for index, result in enumerate(completed, start=1):
            response = result.get("response") or result.get("eligibilityResponse") or result
            if args.save_dir:
                save_json(f"{args.save_dir}/check-{index}.json", result)
            elif index <= 3:
                print(f"\n--- result {index} ---")
                print(summarize(response))
        if args.save_dir:
            print(f"Wrote {len(completed)} response files to {args.save_dir}/")

    if args.save:
        save_json(args.save, {"status": status, "items": items})

    return 1 if failures else 0


def cmd_roster(args: argparse.Namespace) -> int:
    """Run one real-time check per CSV row. Columns map to the check flags by name."""
    rows = list(csv.DictReader(pathlib.Path(args.csv).open(encoding="utf-8-sig")))
    if not rows:
        raise StediError(f"{args.csv} has no data rows")

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    failures = 0

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["row", "member", "memberId", "payerId", "status", "errors"])

        for index, row in enumerate(rows, start=1):
            payer = (row.get(args.payer_column) or args.payer or "").strip()
            member_label = " ".join(
                x for x in ((row.get("firstName") or "").strip(), (row.get("lastName") or "").strip()) if x
            )
            try:
                if not payer:
                    raise StediError(f"no payer id (column {args.payer_column!r} empty and --payer unset)")
                body = {
                    "tradingPartnerServiceId": payer,
                    "provider": {
                        "organizationName": (row.get("organizationName") or args.org or "").strip(),
                        "npi": validate_npi(row.get("npi") or args.npi or ""),
                    },
                    "subscriber": {
                        k: v
                        for k, v in (
                            ("memberId", (row.get("memberId") or "").strip()),
                            ("firstName", (row.get("firstName") or "").strip()),
                            ("lastName", (row.get("lastName") or "").strip()),
                            (
                                "dateOfBirth",
                                validate_date(row["dateOfBirth"], "dateOfBirth")
                                if (row.get("dateOfBirth") or "").strip()
                                else "",
                            ),
                        )
                        if v
                    },
                    "encounter": {
                        "serviceTypeCodes": [
                            (row.get("serviceTypeCode") or args.service_type_default).strip()
                        ]
                    },
                }
                response = request("POST", "change/medicalnetwork/eligibility/v3", body=body)
                errors = collect_errors(response)
                status = coverage_status(response)
                writer.writerow(
                    [index, member_label, body["subscriber"].get("memberId", ""), payer, status, "; ".join(errors)]
                )
                if args.save_dir:
                    save_json(f"{args.save_dir}/row-{index}.json", response)
                print(f"[{index}/{len(rows)}] {member_label or 'row ' + str(index)}: {status}")
                if errors:
                    failures += 1
            except StediError as exc:
                writer.writerow([index, member_label, (row.get("memberId") or ""), payer, "ERROR", str(exc)])
                print(f"[{index}/{len(rows)}] {member_label or 'row ' + str(index)}: ERROR — {exc}")
                failures += 1

    print(f"\nWrote {out_path} — {len(rows) - failures}/{len(rows)} checks returned benefits")
    return 1 if failures else 0


# ------------------------------------------------------------------------- main


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("payers", help="search the Stedi payer network by name, id, or alias")
    p.add_argument("query")
    p.add_argument("--page-size", type=int, default=10)
    p.add_argument(
        "--eligibility-only",
        action="store_true",
        help="only payers that support eligibility checks",
    )
    p.set_defaults(func=cmd_payers)

    p = sub.add_parser("payer", help="retrieve one payer record by Stedi payer id")
    p.add_argument("stedi_id")
    p.set_defaults(func=cmd_payer)

    p = sub.add_parser("check", help="run a real-time eligibility check (270/271)")
    p.add_argument("--payer", help="tradingPartnerServiceId: payer id, Stedi payer id, or alias")
    p.add_argument("--npi", help="billing/rendering provider NPI (10 digits)")
    p.add_argument("--org", help="provider organization name")
    p.add_argument("--first")
    p.add_argument("--last")
    p.add_argument("--dob", help="subscriber date of birth, YYYYMMDD")
    p.add_argument("--member-id")
    p.add_argument(
        "--service-type",
        action="append",
        metavar="STC",
        help="service type code; repeatable, but most payers prefer one per request (default 30)",
    )
    p.add_argument("--dos", help="date of service, YYYYMMDD (defaults to today at the payer)")
    p.add_argument("--procedure-code", help="CPT/HCPCS/CDT code, for payers that support code-level checks")
    p.add_argument("--procedure-qualifier", default="HC", help="HC=CPT/HCPCS, AD=CDT (default HC)")
    p.add_argument("--dependent-first")
    p.add_argument("--dependent-last")
    p.add_argument("--dependent-dob")
    p.add_argument("--input", help="path to a full request JSON body (ignores the flags above)")
    p.add_argument("--save", help="write the raw response JSON here")
    p.add_argument("--raw", action="store_true", help="print raw JSON instead of the summary")
    p.add_argument("--dry-run", action="store_true", help="print the request body and exit")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("batch", help="inspect a Stedi batch by id: status, per-check states, failures")
    p.add_argument("batch_id")
    p.add_argument("--results", action="store_true", help="also poll for completed 271 responses")
    p.add_argument("--save-dir", help="write each polled response JSON into this directory")
    p.add_argument("--save", help="write the status + items JSON here")
    p.add_argument("--page-size", type=int, default=100)
    p.add_argument("--max-failures", type=int, default=25, help="how many failing checks to print")
    p.set_defaults(func=cmd_batch)

    p = sub.add_parser("roster", help="run one real-time check per CSV row and write a summary CSV")
    p.add_argument("csv", help="columns: firstName,lastName,dateOfBirth,memberId,payerId[,npi,organizationName,serviceTypeCode]")
    p.add_argument("--out", default="outputs/eligibility-roster.csv")
    p.add_argument("--payer-column", default="payerId")
    p.add_argument("--payer", help="fallback payer id for rows with an empty payer column")
    p.add_argument("--npi", help="fallback provider NPI")
    p.add_argument("--org", help="fallback provider organization name")
    p.add_argument("--service-type-default", default="30")
    p.add_argument("--save-dir", help="also write each raw response JSON into this directory")
    p.set_defaults(func=cmd_roster)

    return ap


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "check" and not args.input and not args.service_type:
        args.service_type = ["30"]  # 30 = Health Benefit Plan Coverage
    try:
        return args.func(args)
    except StediError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
