"""Fincaraíz scraper — search by city + barrio + transaction, paginate, extract cards."""
from __future__ import annotations

from urllib.parse import quote

from playwright.async_api import BrowserContext

from .base import Subject, Listing, polite_sleep, safe_goto
from ._card_extract import extract_cards_from_page

SOURCE = "fincaraiz"
BASE = "https://www.fincaraiz.com.co"


def _slug(s: str) -> str:
    return s.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")


def _search_url(subject: Subject, transaction: str, page_n: int) -> str:
    trans_slug = "venta" if transaction == "venta" else "arriendo"
    city = _slug(subject.city or "bogota")
    barrio = _slug(subject.barrio) if subject.barrio else ""
    path = f"/finca-raiz/{trans_slug}/apartamentos/{city}"
    if barrio:
        path += f"/{barrio}"
    qs = f"?pagina={page_n}" if page_n > 1 else ""
    return f"{BASE}{path}/{qs}"


async def _search(ctx: BrowserContext, subject: Subject, transaction: str, max_results: int) -> list[Listing]:
    page = await ctx.new_page()
    out: list[Listing] = []
    try:
        for n in range(1, 4):
            url = _search_url(subject, transaction, n)
            ok = await safe_goto(page, url)
            if not ok:
                break
            await polite_sleep()
            cards = await extract_cards_from_page(page, source=SOURCE, transaction=transaction)
            if not cards:
                break
            for c in cards:
                c.city = subject.city
                c.barrio = c.barrio or subject.barrio
            out.extend(cards)
            if len(out) >= max_results:
                break
    finally:
        await page.close()
    return out[:max_results]


async def search_sales(ctx: BrowserContext, subject: Subject, max_results: int = 30) -> list[Listing]:
    return await _search(ctx, subject, "venta", max_results)


async def search_rentals(ctx: BrowserContext, subject: Subject, max_results: int = 30) -> list[Listing]:
    return await _search(ctx, subject, "arriendo", max_results)


async def scrape_listing(ctx: BrowserContext, url: str) -> Listing | None:
    """Scrape a single FincaRaíz listing as the subject."""
    page = await ctx.new_page()
    try:
        if not await safe_goto(page, url):
            return None
        await polite_sleep()
        text = (await page.evaluate("() => document.body.innerText || ''")).strip()
        from ._card_extract import _parse_card_text
        return _parse_card_text(text, source=SOURCE, url=url, transaction="venta")
    finally:
        await page.close()
