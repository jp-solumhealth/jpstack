"""Catastro Medellín lookup — best-effort. Same pattern as Bogotá module."""
from __future__ import annotations

from playwright.async_api import BrowserContext

from ..scrapers.base import polite_sleep, safe_goto


PORTAL = "https://www.medellin.gov.co/Mapas/InfoCatastral/"


async def lookup(ctx: BrowserContext, address: str | None, cedula_catastral: str | None = None) -> dict:
    if not address and not cedula_catastral:
        return {"status": "skipped", "reason": "no address or cédula catastral"}

    page = await ctx.new_page()
    try:
        if not await safe_goto(page, PORTAL):
            return {"status": "manual", "reason": "portal did not load"}
        await polite_sleep(2, 3)
        text = (await page.evaluate("() => document.body.innerText || ''")).strip()
        return {
            "status": "manual",
            "reason": "Catastro Medellín map portal requires interactive use; flagged for manual lookup",
            "address": address,
            "cedula_catastral": cedula_catastral,
            "portal": PORTAL,
            "page_text_sample": text[:500],
        }
    finally:
        await page.close()
