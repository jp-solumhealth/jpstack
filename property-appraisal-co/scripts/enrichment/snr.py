"""SNR / VUR matrícula inmobiliaria lookup.

Ventanilla Única de Registro (VUR) requires payment per certificate. We do not
auto-pay. This module:
  - Validates matrícula format (e.g., '50C-1234567').
  - Reports status='manual' with a deep-link the user can complete themselves.

If the user later configures `SNR_API_KEY` in env (no public API exists today),
this is the place to hook it in.
"""
from __future__ import annotations

import os
import re

MATRICULA_RE = re.compile(r"^\d{2,3}[A-Z]-\d{5,8}$")


def _valid(matricula: str) -> bool:
    return bool(MATRICULA_RE.match(matricula.strip().upper()))


async def resolve_matricula(matricula: str) -> dict:
    """Best-effort: confirm format and return manual-lookup deep link."""
    matricula = matricula.strip().upper()
    if not _valid(matricula):
        return {"status": "invalid", "matricula": matricula, "reason": "format must be like 50C-1234567"}
    return {
        "status": "manual",
        "matricula": matricula,
        "deep_link": f"https://radicacion.supernotariado.gov.co/app/static/html/index.jsf",
        "reason": "VUR requires authenticated/paid request — fill manually and feed result back.",
    }


async def owner_history(matricula: str) -> dict:
    if not os.getenv("SNR_API_KEY"):
        return {
            "status": "manual",
            "matricula": matricula,
            "reason": "No SNR_API_KEY configured. Pull Certificado de Tradición y Libertad manually.",
        }
    # Placeholder — wire real API here if/when JP gets credentials.
    return {"status": "not_implemented", "matricula": matricula}
