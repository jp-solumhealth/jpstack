"""Find constructora + año de construcción for the subject building.

Strategy:
1. Look across the comp listings already scraped — many include `proyecto` or
   `constructora` fields directly in the card text.
2. If the subject has a `building_name`, run a Google search for
   "<building_name> <barrio> <city> constructora año construcción" and parse
   the top results.
"""
from __future__ import annotations

import re
from collections import Counter

from playwright.async_api import BrowserContext

from ..scrapers.base import Subject, Listing, polite_sleep, safe_goto


_YEAR_RE = re.compile(r"\b(19[5-9]\d|20[0-3]\d)\b")
_CONSTRUCTORA_RE = re.compile(r"constructora[:\s]+([A-Z][\w\s&\.-]{2,60})", re.IGNORECASE)
_PROYECTO_RE = re.compile(r"proyecto[:\s]+([A-Z][\w\s&\.-]{2,60})", re.IGNORECASE)


def from_listings(comps: list[Listing]) -> dict:
    """Best-effort extraction from already-scraped comp text."""
    constructoras: Counter[str] = Counter()
    proyectos: Counter[str] = Counter()
    years: Counter[int] = Counter()
    for c in comps:
        text = (c.raw or {}).get("card_text", "") + " " + (c.title or "")
        for m in _CONSTRUCTORA_RE.finditer(text):
            constructoras[m.group(1).strip().title()] += 1
        for m in _PROYECTO_RE.finditer(text):
            proyectos[m.group(1).strip().title()] += 1
        for m in _YEAR_RE.finditer(text):
            y = int(m.group(1))
            # Filter implausible years for "year built"
            if 1960 <= y <= 2030:
                years[y] += 1
    return {
        "constructora": constructoras.most_common(1)[0][0] if constructoras else None,
        "proyecto": proyectos.most_common(1)[0][0] if proyectos else None,
        "anio_construccion_guess": years.most_common(1)[0][0] if years else None,
        "_signal_counts": {
            "constructora": dict(constructoras),
            "proyecto": dict(proyectos),
            "anio": dict(years),
        },
    }


async def google_lookup(ctx: BrowserContext, subject: Subject) -> dict:
    """Fallback: Google for the building name."""
    if not subject.building_name:
        return {}
    page = await ctx.new_page()
    try:
        q = f"{subject.building_name} {subject.barrio or ''} {subject.city or ''} constructora año construcción".strip()
        url = f"https://www.google.com/search?q={q.replace(' ', '+')}"
        if not await safe_goto(page, url):
            return {}
        await polite_sleep()
        text = (await page.evaluate("() => document.body.innerText || ''")).strip()
        constructora = None
        anio = None
        m = _CONSTRUCTORA_RE.search(text)
        if m:
            constructora = m.group(1).strip().title()
        m = _YEAR_RE.search(text)
        if m:
            y = int(m.group(1))
            if 1960 <= y <= 2030:
                anio = y
        return {"constructora_google": constructora, "anio_google": anio, "google_query": q}
    finally:
        await page.close()


async def find(ctx: BrowserContext, subject: Subject, comps: list[Listing]) -> dict:
    out = from_listings(comps)
    g = await google_lookup(ctx, subject)
    out.update(g)
    # Reconcile
    out["constructora_final"] = out.get("constructora") or out.get("constructora_google")
    out["anio_final"] = out.get("anio_construccion_guess") or out.get("anio_google")
    return out
