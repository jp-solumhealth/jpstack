"""Catastro Bogotá lookup — best-effort.

Public portal: https://www.catastrobogota.gov.co/  (consulta ciudadana)
Endpoint accepts address or cédula catastral. Site uses JS-heavy forms; we drive
it with Playwright. If the form changes, this returns {"status": "manual",
"reason": "..."} and the orchestrator carries on.
"""
from __future__ import annotations

from playwright.async_api import BrowserContext

from ..scrapers.base import polite_sleep, safe_goto


PORTAL = "https://www.catastrobogota.gov.co/"


async def lookup(ctx: BrowserContext, address: str | None, cedula_catastral: str | None = None) -> dict:
    if not address and not cedula_catastral:
        return {"status": "skipped", "reason": "no address or cédula catastral"}

    page = await ctx.new_page()
    try:
        if not await safe_goto(page, PORTAL):
            return {"status": "manual", "reason": "portal did not load"}
        await polite_sleep(2, 3)
        # Catastro Bogotá uses iframes and a multi-step form. Rather than maintain
        # brittle selectors here, we capture the raw page text and let the
        # orchestrator surface it to JP for a manual confirm. v2 can wire the
        # actual form fields once the smoke test confirms the current DOM.
        text = (await page.evaluate("() => document.body.innerText || ''")).strip()
        return {
            "status": "manual",
            "reason": "Catastro Bogotá form requires interactive captcha; flagged for manual confirmation",
            "address": address,
            "cedula_catastral": cedula_catastral,
            "portal": PORTAL,
            "page_text_sample": text[:500],
        }
    finally:
        await page.close()
