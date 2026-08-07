"""Property-appraisal-co orchestrator.

Usage:
    python -m scripts.run_appraisal "apartaestudio 25m Chico Bogotá edificio Otoño"
    python -m scripts.run_appraisal --ltv 0.55 --portals fincaraiz,metrocuadrado "..."
    python -m scripts.run_appraisal --no-rent "https://www.fincaraiz.com.co/inmueble/..."

Run from the skill folder root (i.e., property-appraisal-co/) so `scripts.*`
imports resolve.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from .input_parser import parse, missing_fields
from .kernel_docker import ensure_running
from .scrapers.base import CDPContext, Subject, Listing
from .scrapers import fincaraiz, metrocuadrado, vivienda, mercadolibre
from . import comp_filter, valuation, rent_estimator, loan_sizer, xlsx_writer
from .enrichment import constructora as enr_constructora
from .enrichment import catastro_bogota, catastro_medellin, snr as enr_snr


PORTALS = {
    "fincaraiz": fincaraiz,
    "metrocuadrado": metrocuadrado,
    "vivienda": vivienda,
    "mercadolibre": mercadolibre,
}

DEFAULT_OUTPUT_DIR = Path.home() / "Documents/Claude/property-appraisal-co/outputs"


def _slug(s: str | None) -> str:
    if not s:
        return "subject"
    return s.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")


async def _run(args: argparse.Namespace) -> Path:
    subject = parse(args.query)
    missing = missing_fields(subject)
    if missing:
        print(f"⚠  Missing fields: {missing}. Provide them and re-run, or accept best-effort.", file=sys.stderr)

    portals_to_run = args.portals.split(",") if args.portals else list(PORTALS.keys())

    ws_url = ensure_running()
    print(f"✓ Kernel CDP at {ws_url}")

    log: list[dict] = []
    sale_listings: list[Listing] = []
    rent_listings: list[Listing] = []
    enrichment: dict = {}

    async with CDPContext(ws_url) as ctx:
        # If user gave a listing URL, populate subject from it
        if subject.listing_url:
            for name, mod in PORTALS.items():
                if name in subject.listing_url:
                    sub = await mod.scrape_listing(ctx, subject.listing_url)
                    if sub:
                        for f in ("price_cop", "m2_built", "bedrooms", "bathrooms", "parking", "estrato"):
                            v = getattr(sub, f, None)
                            if v is not None and not getattr(subject, f, None):
                                setattr(subject, f, v if f != "price_cop" else getattr(subject, f, None))
                    break

        # Sale comps
        for name in portals_to_run:
            mod = PORTALS.get(name)
            if not mod:
                continue
            try:
                got = await mod.search_sales(ctx, subject, max_results=args.max_comps)
                sale_listings.extend(got)
                log.append({"portal": name, "transaction": "venta", "returned": len(got), "kept": None, "dropped": None, "notes": ""})
            except Exception as e:
                log.append({"portal": name, "transaction": "venta", "returned": 0, "kept": 0, "dropped": 0, "notes": f"error: {e}"})

        # Rent comps
        if not args.no_rent:
            for name in portals_to_run:
                mod = PORTALS.get(name)
                if not mod:
                    continue
                try:
                    got = await mod.search_rentals(ctx, subject, max_results=args.max_comps)
                    rent_listings.extend(got)
                    log.append({"portal": name, "transaction": "arriendo", "returned": len(got), "kept": None, "dropped": None, "notes": ""})
                except Exception as e:
                    log.append({"portal": name, "transaction": "arriendo", "returned": 0, "kept": 0, "dropped": 0, "notes": f"error: {e}"})

        # Filter
        sale_kept, sale_dropped = comp_filter.filter_comps(sale_listings, subject)
        rent_kept, rent_dropped = comp_filter.filter_comps(rent_listings, subject)
        for entry in log:
            if entry["transaction"] == "venta":
                entry["kept"] = sum(1 for l in sale_kept if l.source == entry["portal"])
                entry["dropped"] = sum(1 for l, _ in sale_dropped if l.source == entry["portal"])
            else:
                entry["kept"] = sum(1 for l in rent_kept if l.source == entry["portal"])
                entry["dropped"] = sum(1 for l, _ in rent_dropped if l.source == entry["portal"])

        # Valuation
        val = valuation.value(sale_kept, subject)
        # Rent
        rent_res = rent_estimator.estimate(rent_kept, subject, val.get("appraised", {}).get("mid"))
        # Loan
        loan = loan_sizer.size(val.get("appraised", {}).get("mid"), ltv=args.ltv)

        # Enrichment
        try:
            enrichment = await enr_constructora.find(ctx, subject, sale_kept)
        except Exception as e:
            enrichment = {"error_constructora": str(e)}

        if (subject.city or "").lower().startswith("bogot"):
            try:
                enrichment["catastro_bogota"] = await catastro_bogota.lookup(ctx, subject.address)
            except Exception as e:
                enrichment["catastro_bogota"] = {"status": "error", "reason": str(e)}
        elif (subject.city or "").lower().startswith("medell"):
            try:
                enrichment["catastro_medellin"] = await catastro_medellin.lookup(ctx, subject.address)
            except Exception as e:
                enrichment["catastro_medellin"] = {"status": "error", "reason": str(e)}

        if subject.matricula:
            try:
                enrichment["snr"] = await enr_snr.resolve_matricula(subject.matricula)
                enrichment["snr_owner"] = await enr_snr.owner_history(subject.matricula)
            except Exception as e:
                enrichment["snr"] = {"status": "error", "reason": str(e)}

    # Write XLSX
    out_dir = Path(args.out_dir or DEFAULT_OUTPUT_DIR)
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M")
    fname = f"{_slug(subject.barrio) or 'subject'}-{int(subject.m2_built) if subject.m2_built else 'na'}m-{stamp}.xlsx"
    out_path = out_dir / fname

    out_path = xlsx_writer.write(
        subject=subject, valuation=val, rent=rent_res, enrichment=enrichment,
        loan=loan, sale_comps=sale_kept, rent_comps=rent_kept, log=log,
        out_path=out_path,
    )

    print(json.dumps({
        "out": str(out_path),
        "n_sale_comps": len(sale_kept),
        "n_rent_comps": len(rent_kept),
        "appraised_mid": val.get("appraised", {}).get("mid"),
        "rent_p50": rent_res.get("rent", {}).get("p50"),
        "gross_yield_pct": rent_res.get("gross_yield_pct"),
        "max_loan_cop": loan.get("max_loan_cop"),
        "confidence": val.get("confidence"),
    }, indent=2, default=str))
    return out_path


def main() -> None:
    p = argparse.ArgumentParser(description="Indicative property appraisal for Colombia.")
    p.add_argument("query", help="Free-text describing the property, or a listing URL, or a matrícula.")
    p.add_argument("--ltv", type=float, default=0.60)
    p.add_argument("--no-rent", action="store_true")
    p.add_argument("--portals", help="Comma-separated subset of: fincaraiz,metrocuadrado,vivienda,mercadolibre")
    p.add_argument("--max-comps", type=int, default=30)
    p.add_argument("--out-dir", type=str, default=None)
    args = p.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
