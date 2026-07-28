"""Parse user free-text into a Subject object."""
from __future__ import annotations

import re

from .scrapers.base import Subject


_M2_RE = re.compile(r"(\d{2,4})\s*(m\b|mt|mts|m2|m²)", re.IGNORECASE)
_BED_RE = re.compile(r"(\d)\s*(hab|alc|dorm|bed)", re.IGNORECASE)
_MATRICULA_RE = re.compile(r"\b(\d{2,3}[A-Z]-\d{5,8})\b")
_URL_RE = re.compile(r"https?://\S+")

CITY_HINTS = {
    "bogota": "Bogotá", "bogotá": "Bogotá", "bog": "Bogotá",
    "medellin": "Medellín", "medellín": "Medellín", "mde": "Medellín",
    "cali": "Cali", "barranquilla": "Barranquilla", "cartagena": "Cartagena",
}

# Common Bogotá/Medellín barrios — extend as needed
BARRIO_HINTS = {
    "chico": "El Chicó", "chicó": "El Chicó", "chico norte": "Chico Norte",
    "chapinero": "Chapinero", "rosales": "Rosales", "el retiro": "El Retiro",
    "santa barbara": "Santa Bárbara", "usaquen": "Usaquén", "cedritos": "Cedritos",
    "salitre": "Salitre", "modelia": "Modelia", "country": "Antiguo Country",
    "poblado": "El Poblado", "el poblado": "El Poblado", "provenza": "Provenza",
    "laureles": "Laureles", "envigado": "Envigado",
}

TYPE_HINTS = {
    "apartaestudio": ("apartaestudio", 0),
    "estudio": ("apartaestudio", 0),
    "loft": ("loft", 0),
    "apto": ("apartamento", None),
    "apartamento": ("apartamento", None),
    "casa": ("casa", None),
}


def parse(text: str) -> Subject:
    raw = text.strip()
    s = Subject(raw=raw)

    low = raw.lower()

    # URL?
    m = _URL_RE.search(raw)
    if m:
        s.listing_url = m.group(0)

    # Matrícula?
    m = _MATRICULA_RE.search(raw.upper())
    if m:
        s.matricula = m.group(1)

    # m²
    m = _M2_RE.search(raw)
    if m:
        try:
            s.m2_built = float(m.group(1))
        except ValueError:
            pass

    # bedrooms
    m = _BED_RE.search(raw)
    if m:
        s.bedrooms = int(m.group(1))

    # type → infer bedrooms for apartaestudio
    for key, (_typ, beds) in TYPE_HINTS.items():
        if key in low:
            if beds is not None and not s.bedrooms:
                s.bedrooms = beds
            break

    # city
    for key, val in CITY_HINTS.items():
        if re.search(rf"\b{re.escape(key)}\b", low):
            s.city = val
            break

    # barrio
    for key, val in BARRIO_HINTS.items():
        if re.search(rf"\b{re.escape(key)}\b", low):
            s.barrio = val
            break

    # building name — look for "edificio X" or "edif X" or "ed. X"
    m = re.search(r"(?:edificio|edif\.?|ed\.)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ][\w\sÁÉÍÓÚáéíóúñÑ\.&-]{2,40})", raw, re.IGNORECASE)
    if m:
        s.building_name = m.group(1).strip().rstrip(",.;")
    else:
        # If user wrote a capitalized word right after the m² + barrio, treat as building name
        # (heuristic — silent if no match)
        pass

    return s


def missing_fields(s: Subject) -> list[str]:
    missing = []
    if not s.city:
        missing.append("city")
    if not s.barrio and not s.matricula and not s.listing_url:
        missing.append("barrio")
    if not s.m2_built and not s.matricula and not s.listing_url:
        missing.append("m2_built")
    return missing


if __name__ == "__main__":
    import sys, json
    s = parse(" ".join(sys.argv[1:]) or "apartaestudio 25m Chico Bogotá edificio Otoño")
    from dataclasses import asdict
    print(json.dumps(asdict(s), indent=2, ensure_ascii=False))
    print("Missing:", missing_fields(s))
