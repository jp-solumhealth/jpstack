"""Estimate monthly rent + gross yield from rental comps."""
from __future__ import annotations

from statistics import median, quantiles

from .scrapers.base import Listing, Subject


def estimate(rent_comps: list[Listing], subject: Subject, appraised_mid: float | None) -> dict:
    rents = [l.price_cop for l in rent_comps if l.price_cop]
    n = len(rents)
    if not rents:
        return {"n_rent_comps": 0, "rent": {"p25": None, "p50": None, "p75": None}, "gross_yield_pct": None}

    if n >= 4:
        q = quantiles(rents, n=4)
        p25, p50, p75 = q[0], q[1], q[2]
    else:
        p25 = min(rents)
        p50 = median(rents)
        p75 = max(rents)

    gross_yield = None
    if appraised_mid and p50:
        gross_yield = (p50 * 12) / appraised_mid * 100

    return {
        "n_rent_comps": n,
        "rent": {"p25": p25, "p50": p50, "p75": p75},
        "gross_yield_pct": gross_yield,
    }
