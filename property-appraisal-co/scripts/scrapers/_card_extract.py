"""Heuristic listing-card extractor — used by all 4 portal scrapers.

Real estate portals share a common card pattern: a clickable anchor wrapping a
block of text with price, m², bedrooms, and a barrio label. Rather than maintain
4 brittle selector sets, we parse cards via text heuristics. Site-specific
scrapers handle URL building and pagination only.
"""
from __future__ import annotations

import re
from playwright.async_api import Page, ElementHandle
from .base import Listing, parse_cop, parse_int, parse_m2


_LISTING_HREF_RE = re.compile(
    r"(inmueble|propiedad|apartamento|casa|MCO-|/p/|/finca-raiz/|/inmuebles/|/listing/)",
    re.IGNORECASE,
)


async def extract_cards_from_page(page: Page, source: str, transaction: str) -> list[Listing]:
    """Walk anchors on the page, group nearby text, build Listing objects.

    Strategy:
      1. Collect all <a> tags whose href looks like a listing detail page.
      2. For each, take the bounding-box text (innerText of the closest container).
      3. Heuristically pull price ($...), m² (number+m²/mts), bedrooms (n+hab/alc).
    """
    anchors: list[ElementHandle] = await page.query_selector_all("a[href]")
    out: list[Listing] = []
    seen_urls: set[str] = set()

    for a in anchors:
        try:
            href = await a.get_attribute("href")
        except Exception:
            continue
        if not href or not _LISTING_HREF_RE.search(href):
            continue

        # Normalize URL
        url = href if href.startswith("http") else f"{page.url.split('/', 3)[0]}//{page.url.split('/', 3)[2]}{href}"
        url = url.split("#", 1)[0]
        if url in seen_urls:
            continue
        seen_urls.add(url)

        # Climb to the nearest "card" container with multi-line text
        try:
            container = await a.evaluate_handle(
                """(el) => {
                    let n = el;
                    for (let i = 0; i < 5; i++) {
                        if (!n.parentElement) break;
                        n = n.parentElement;
                        const t = (n.innerText || "").trim();
                        if (t.includes("$") && (t.includes("m²") || t.toLowerCase().includes("mts") || t.toLowerCase().includes("m2"))) {
                            return n;
                        }
                    }
                    return el;
                }"""
            )
            text = (await container.evaluate("(n) => n.innerText || ''")).strip()
        except Exception:
            text = ""

        if not text or "$" not in text:
            continue

        listing = _parse_card_text(text, source=source, url=url, transaction=transaction)
        if listing:
            out.append(listing)

    return out


def _parse_card_text(text: str, *, source: str, url: str, transaction: str) -> Listing | None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None
    # Title — first non-price line under ~120 chars
    title = next((ln for ln in lines if "$" not in ln and len(ln) < 140), lines[0])

    # Price — first line with $
    price_line = next((ln for ln in lines if "$" in ln), "")
    price = parse_cop(price_line)

    # m²
    m2 = None
    for ln in lines:
        m2 = parse_m2(ln)
        if m2:
            break

    # Bedrooms — look for "hab", "alc", "dorm"
    bedrooms = None
    for ln in lines:
        m = re.search(r"(\d+)\s*(hab|alc|dorm)", ln, re.IGNORECASE)
        if m:
            bedrooms = int(m.group(1))
            break

    # Bathrooms — "baño"
    bathrooms = None
    for ln in lines:
        m = re.search(r"(\d+)\s*ba(ñ|n)o", ln, re.IGNORECASE)
        if m:
            bathrooms = int(m.group(1))
            break

    # Parking — "garaje", "parqueadero", "estacionamient"
    parking = None
    for ln in lines:
        m = re.search(r"(\d+)\s*(garaj|parq|estacionam)", ln, re.IGNORECASE)
        if m:
            parking = int(m.group(1))
            break

    # Estrato
    estrato = None
    for ln in lines:
        m = re.search(r"estrato\s*(\d)", ln, re.IGNORECASE)
        if m:
            estrato = int(m.group(1))
            break

    if not price and not m2:
        return None  # not a real listing card

    return Listing(
        source=source,
        url=url,
        title=title[:200],
        price_cop=price,
        transaction=transaction,
        m2_built=m2,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        parking=parking,
        estrato=estrato,
        raw={"card_text": text[:1000]},
    )
