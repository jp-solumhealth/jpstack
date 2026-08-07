"""Shared Playwright/CDP helpers for portal scrapers."""
from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Callable

from playwright.async_api import async_playwright, BrowserContext, Page, TimeoutError as PWTimeout


# ---------- Data shapes ----------

@dataclass
class Subject:
    city: str = ""
    barrio: str = ""
    address: str | None = None
    m2_built: float = 0.0
    m2_private: float | None = None
    bedrooms: int = 0
    bathrooms: int | None = None
    parking: int | None = None
    estrato: int | None = None
    year_built: int | None = None
    admin_fee: float | None = None
    matricula: str | None = None
    listing_url: str | None = None
    building_name: str | None = None
    raw: str = ""


@dataclass
class Listing:
    source: str
    url: str
    title: str = ""
    price_cop: float | None = None
    transaction: str = "venta"  # "venta" | "arriendo"
    m2_built: float | None = None
    m2_private: float | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    parking: int | None = None
    estrato: int | None = None
    admin_cop: float | None = None
    year_built: int | None = None
    constructora: str | None = None
    proyecto: str | None = None
    barrio: str | None = None
    city: str | None = None
    listing_date: str | None = None  # ISO date if found
    lat: float | None = None
    lng: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def price_per_m2(self) -> float | None:
        if self.price_cop and self.m2_built and self.m2_built > 0:
            return self.price_cop / self.m2_built
        return None


# ---------- Numeric / text helpers ----------

_PRICE_RX = re.compile(r"[\$\s]*([\d.,]+)\s*(millón|millones|mil|m|M)?", re.IGNORECASE)


def parse_cop(text: str) -> float | None:
    """Parse Colombian price strings: '$ 350.000.000', '350 millones', '$1.2M'."""
    if not text:
        return None
    t = text.replace("\xa0", " ").strip()
    # Remove currency symbols and 'COP'
    t = re.sub(r"COP|\$|pesos", "", t, flags=re.IGNORECASE).strip()
    # Detect modifier
    mod_mult = 1
    low = t.lower()
    if "millon" in low or low.endswith(" m") or low.endswith("m"):
        mod_mult = 1_000_000
        t = re.sub(r"millones?|m$", "", t, flags=re.IGNORECASE).strip()
    elif "mil" in low:
        mod_mult = 1_000
        t = re.sub(r"mil", "", t, flags=re.IGNORECASE).strip()
    # Remove thousands separators (.) — Colombian uses '.' as thousand sep
    digits = re.sub(r"[^\d,]", "", t)
    if not digits:
        return None
    if "," in digits:
        # Treat ',' as decimal
        try:
            val = float(digits.replace(".", "").replace(",", "."))
        except ValueError:
            return None
    else:
        try:
            val = float(digits.replace(".", ""))
        except ValueError:
            return None
    return val * mod_mult


def parse_int(text: str) -> int | None:
    if not text:
        return None
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None


def parse_m2(text: str) -> float | None:
    if not text:
        return None
    m = re.search(r"([\d]+([.,]\d+)?)\s*m", text, re.IGNORECASE)
    if not m:
        return None
    return float(m.group(1).replace(",", "."))


# ---------- Browser context ----------

class CDPContext:
    """Async helper that connects to an existing Kernel Chromium via CDP."""

    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self._pw = None
        self._browser = None
        self._context: BrowserContext | None = None

    async def __aenter__(self) -> BrowserContext:
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.connect_over_cdp(self.ws_url)
        # Reuse the default context that the headful Chromium ships with
        if self._browser.contexts:
            self._context = self._browser.contexts[0]
        else:
            self._context = await self._browser.new_context()
        return self._context

    async def __aexit__(self, *exc):
        try:
            if self._browser is not None:
                await self._browser.close()
        finally:
            if self._pw is not None:
                await self._pw.stop()


async def polite_sleep(lo: float = 1.5, hi: float = 3.0) -> None:
    await asyncio.sleep(random.uniform(lo, hi))


async def safe_goto(page: Page, url: str, timeout_ms: int = 30_000) -> bool:
    try:
        await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        return True
    except PWTimeout:
        return False


def listing_to_dict(l: Listing) -> dict:
    d = asdict(l)
    d["price_per_m2"] = l.price_per_m2
    return d
