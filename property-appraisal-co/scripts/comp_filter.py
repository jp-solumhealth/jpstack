"""Filter raw listings down to comparable sales/rentals."""
from __future__ import annotations

import hashlib
from dataclasses import asdict
from datetime import datetime, timedelta

from .scrapers.base import Listing, Subject


# Minimal barrio adjacency for v1 — extend in data/*.json once smoke tests confirm needs.
BARRIO_ADJACENCY: dict[str, set[str]] = {
    "el chico": {"chico norte", "chico reservado", "chico alto", "el retiro", "lago gaitan", "antiguo country"},
    "chapinero": {"chapinero alto", "chapinero central", "el chico", "quinta camacho", "rosales"},
    "el poblado": {"provenza", "manila", "lalinde", "patio bonito", "los balsos"},
}


def _norm(s: str | None) -> str:
    return (s or "").strip().lower()


def _adjacent(a: str, b: str) -> bool:
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return False
    if a == b:
        return True
    return b in BARRIO_ADJACENCY.get(a, set()) or a in BARRIO_ADJACENCY.get(b, set())


def _dedupe_key(l: Listing) -> str:
    base = f"{round(l.price_cop or 0)}|{round(l.m2_built or 0)}|{_norm(l.barrio)}"
    return hashlib.md5(base.encode()).hexdigest()


def filter_comps(
    listings: list[Listing],
    subject: Subject,
    *,
    m2_pct: float = 0.20,
    bed_tol: int = 1,
    days: int = 90,
    require_price: bool = True,
) -> tuple[list[Listing], list[tuple[Listing, str]]]:
    """Return (kept, dropped_with_reason)."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    seen_urls: set[str] = set()
    seen_keys: set[str] = set()
    kept: list[Listing] = []
    dropped: list[tuple[Listing, str]] = []

    for l in listings:
        if l.url in seen_urls:
            dropped.append((l, "duplicate URL"))
            continue
        seen_urls.add(l.url)

        if require_price and not l.price_cop:
            dropped.append((l, "no price"))
            continue

        if subject.city and _norm(l.city) and _norm(l.city) != _norm(subject.city):
            dropped.append((l, f"different city ({l.city})"))
            continue

        if subject.barrio and l.barrio and not _adjacent(l.barrio, subject.barrio):
            dropped.append((l, f"barrio not adjacent ({l.barrio})"))
            continue

        if subject.m2_built and l.m2_built:
            lo = subject.m2_built * (1 - m2_pct)
            hi = subject.m2_built * (1 + m2_pct)
            if not (lo <= l.m2_built <= hi):
                dropped.append((l, f"m² out of band ({l.m2_built})"))
                continue

        if subject.bedrooms and l.bedrooms is not None:
            if abs(l.bedrooms - subject.bedrooms) > bed_tol:
                dropped.append((l, f"bedrooms diff > {bed_tol}"))
                continue

        if l.listing_date:
            try:
                d = datetime.fromisoformat(l.listing_date)
                if d < cutoff:
                    dropped.append((l, "older than 90 days"))
                    continue
            except ValueError:
                pass

        key = _dedupe_key(l)
        if key in seen_keys:
            dropped.append((l, "duplicate (price/m²/barrio)"))
            continue
        seen_keys.add(key)

        kept.append(l)

    return kept, dropped
