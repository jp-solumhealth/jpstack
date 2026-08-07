"""Compute price/m² distribution and apply to the subject."""
from __future__ import annotations

from statistics import median, quantiles

from .scrapers.base import Listing, Subject


def value(comps: list[Listing], subject: Subject) -> dict:
    pps = [l.price_per_m2 for l in comps if l.price_per_m2]
    n = len(pps)
    if not pps or not subject.m2_built:
        return {
            "n_comps": n,
            "confidence": "low",
            "price_per_m2": {"p25": None, "p50": None, "p75": None},
            "appraised": {"low": None, "mid": None, "high": None},
            "note": "Insufficient comps or missing subject m²",
        }

    if n >= 4:
        q = quantiles(pps, n=4)  # [p25, p50, p75]
        p25, p50, p75 = q[0], q[1], q[2]
    else:
        p25 = min(pps)
        p50 = median(pps)
        p75 = max(pps)

    confidence = "high" if n >= 15 else "medium" if n >= 8 else "low"

    return {
        "n_comps": n,
        "confidence": confidence,
        "price_per_m2": {"p25": p25, "p50": p50, "p75": p75},
        "appraised": {
            "low": p25 * subject.m2_built,
            "mid": p50 * subject.m2_built,
            "high": p75 * subject.m2_built,
        },
    }
