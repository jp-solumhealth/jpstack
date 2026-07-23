---
name: property-appraisal-co
description: >
  Generate an indicative appraisal for a Colombian residential property to support
  collateralized lending decisions. Scrapes Fincaraíz, Metrocuadrado, Vivienda.com,
  and MercadoLibre Inmuebles via a local Kernel-managed Chromium (Docker), enriches
  with constructora + año de construcción + Catastro (Bogotá/Medellín) + SNR
  (best-effort), and outputs an XLSX with sale comps, rent comps, valuation range,
  estimated rent, gross yield, and a suggested LTV-based max loan amount. Use this
  skill when the user says "appraise this apartment", "avalúo", "valoración",
  "comps for [address]", "what's this property worth", "estimate value of matrícula
  [N]", or pastes a Fincaraíz/Metrocuadrado/Vivienda/MercadoLibre listing URL with
  intent to value it.
---

# Property Appraisal — Colombia (Kernel-powered)

Build a defensible indicative appraisal for a Colombian apartment so JP can size a collateralized mortgage. Always surface the comps and the math — never just a single number.

## Trigger Patterns

Activate this skill when the user says any of:
- "appraise [address/property]" / "avalúo de [...]"
- "valoración de este apartamento"
- "comps for [address]" / "comparables en [barrio]"
- "what's this property worth" / "cuánto vale este apto"
- "estimate value of matrícula [N]" / "matrícula inmobiliaria [N]"
- pastes a listing URL from fincaraiz.com.co, metrocuadrado.com, vivienda.com.co, or mercadolibre.com.co/inmuebles
- "underwrite this property" / "loan-size [property]"

## Input Modes (flexible)

The user may provide ANY of:

1. **Address card** — city + barrio + street + m² + bedrooms (+ optional: bathrooms, parking, estrato, year, admin fee)
2. **Matrícula inmobiliaria** — e.g., `50C-1234567` (Bogotá Zona Centro). Use it to recover address + cédula catastral via SNR/VUR before scraping.
3. **Listing URL** — Fincaraíz / Metrocuadrado / Vivienda / MercadoLibre. Scrape the listing as the subject, then run comps.
4. **Shorthand free-text** — e.g., "apartaestudio 25m Chico Bogotá", "edificio Otoño Chicó". Parse city + barrio + m² + type; ask for missing critical fields (city, barrio, m²).

If critical fields are missing after parsing, ask **once** for the minimum: city, barrio, m², bedrooms.

## Workflow

### Step 1 — Parse and normalize input

Run `scripts/input_parser.py` with the raw user text. It returns a `Subject` dict with:
`city, barrio, address?, m2_built, m2_private?, bedrooms, bathrooms?, parking?, estrato?, year_built?, admin_fee?, matricula?, listing_url?, building_name?, raw`.

For matrícula-only input, call `scripts/enrichment/snr.py::resolve_matricula(matricula)` first; if it succeeds, populate address + cédula catastral and continue. If blocked, log and proceed with whatever the user gave.

For listing URL, call the matching scraper's `scrape_listing(url)` to populate the Subject.

### Step 2 — Boot Kernel container

Call `scripts/kernel_docker.py::ensure_running()`. It:
- Checks if container `kernel-docker` is up; if yes, returns the existing CDP URL.
- Else runs `~/Documents/Claude/Agents/kernel-images/images/chromium-headful/run-docker.sh` with `IMAGE=kernel-docker`.
- Waits up to 60s for `http://localhost:9222/json/version` to respond, returns the `webSocketDebuggerUrl`.

Tell the user "Kernel browser starting…" if first boot.

### Step 3 — Scrape sale comps from 4 portals

In a single Playwright context (one `chromium.connect_over_cdp(ws)`), run all 4 scrapers sequentially (parallel tabs in the same browser is faster but riskier for anti-bot — sequential first):
- `scrapers/fincaraiz.py::search_sales(subject)`
- `scrapers/metrocuadrado.py::search_sales(subject)`
- `scrapers/vivienda.py::search_sales(subject)`
- `scrapers/mercadolibre.py::search_sales(subject)`

Each returns a list of `Listing` dicts. Cap at 30 per portal or 3 pages, whichever first. Polite delays (1.5–3s between requests, randomized).

If a portal blocks (Cloudflare/captcha), log it in the run log and continue with the others — never fail the whole run on one portal.

### Step 4 — Filter to comps

Call `scripts/comp_filter.py::filter_comps(listings, subject)`. Keeps listings that match:
- Same city
- Same barrio OR adjacent barrio (use `data/bogota_barrios.json`, `data/medellin_barrios.json` adjacency lists)
- m² built within ±20% of subject
- bedrooms within ±1
- Listed within last 90 days (skip filter if no date)
- Not duplicate (URL hash + (price, m², barrio) tuple)

### Step 5 — Valuation

Call `scripts/valuation.py::value(comps, subject)`. Returns:
- `price_per_m2_p25, p50, p75`
- `appraised_low = p25 * subject.m2_built`
- `appraised_mid = p50 * subject.m2_built`
- `appraised_high = p75 * subject.m2_built`
- `n_comps`, `confidence` ∈ {`high` ≥15, `medium` ≥8, `low` <8}

### Step 6 — Rent comps + yield

Re-run scrapers in `arriendo` mode (`search_rentals(subject)`). Filter the same way. Call `scripts/rent_estimator.py::estimate(rent_comps, subject, appraised_mid)`. Returns:
- `rent_p25, p50, p75` (monthly COP)
- `gross_yield_pct = (rent_p50 * 12) / appraised_mid * 100`

### Step 7 — Enrichment

Run in parallel where possible:
- `enrichment/constructora.py::find(subject, sale_comps)` — looks for `proyecto`, `constructora`, `año de construcción` in the listing payloads first; if blank, runs a Google search for "<building_name> <barrio> constructora año" and parses the top result.
- `enrichment/catastro_bogota.py::lookup(address)` if city == Bogotá — returns `area_terreno, area_construida, uso, anio_construccion, valor_catastral`.
- `enrichment/catastro_medellin.py::lookup(address)` if city == Medellín.
- `enrichment/snr.py::owner_history(matricula)` if matrícula provided. Flag as "manual lookup required" if VUR credentials are not configured (no auto-payment).

### Step 8 — Loan sizing

Call `scripts/loan_sizer.py::size(appraised_mid, ltv=0.60)`. Returns `max_loan_cop = ltv * appraised_mid`. LTV is overrideable via skill arg `--ltv 0.55`.

### Step 9 — Write XLSX

Call `scripts/xlsx_writer.py::write(subject, valuation, rent, enrichment, loan, sale_comps, rent_comps, log, out_path)`.

Output path: `~/Documents/Claude/property-appraisal-co/outputs/<barrio>-<m2>m-<YYYYMMDD-HHMM>.xlsx`.

Tabs:
1. **Summary** — subject card, valuation range, rent estimate, gross yield, suggested loan, confidence flag, top 3 enrichment highlights, disclaimer ("indicative only — not a certified avalúo").
2. **Sale comps** — every kept comp with URL, price, m², price/m², bedrooms, barrio, listing date, source portal.
3. **Rent comps** — same shape, monthly rent.
4. **Enrichment** — constructora, año, catastro fields, SNR ownership chain (or "manual" flag).
5. **Log** — scrape stats per portal (returned/kept/dropped + reason), warnings, errors.

### Step 10 — Report back to user

In the chat, surface:
- One-line valuation: "**$XXX – $YYY M COP** (median **$ZZZ M**), n=N comps, confidence: medium"
- Estimated rent + gross yield
- Suggested max loan @ 60% LTV
- File path to the XLSX
- Any portals that failed to load (so JP knows what to re-run)

## Skill Arguments

- `--ltv <0..1>` — override loan-to-value (default 0.60)
- `--no-rent` — skip rent comps (faster)
- `--portals <csv>` — restrict to e.g. `fincaraiz,metrocuadrado`
- `--max-comps <N>` — cap comps per portal (default 30)

## Disclaimers (always include in Summary tab)

- "Indicative valuation only — not a certified avalúo (Resolución SNR / RNA)."
- "Comps are listing prices, not closed sales. Apply a market-specific adjustment if used for underwriting."
- "Constructora and año de construcción are best-effort and may be missing."

## Files

- `scripts/run_appraisal.py` — entry point (CLI)
- `scripts/input_parser.py`
- `scripts/kernel_docker.py`
- `scripts/scrapers/{base,fincaraiz,metrocuadrado,vivienda,mercadolibre}.py`
- `scripts/enrichment/{constructora,catastro_bogota,catastro_medellin,snr}.py`
- `scripts/comp_filter.py`
- `scripts/valuation.py`
- `scripts/rent_estimator.py`
- `scripts/loan_sizer.py`
- `scripts/xlsx_writer.py`

## Setup (one-time)

```sh
# 1. Build the Kernel image
cd ~/Documents/Claude/Agents/kernel-images/images/chromium-headful
IMAGE=kernel-docker ./build-docker.sh

# 2. Python deps
pip install playwright openpyxl rapidfuzz python-dateutil
playwright install chromium  # only needed if you want a local Playwright too; CDP doesn't require it
```

## Invocation example

```
appraise apartaestudio 25m Chico Bogotá edificio Otoño
```

The skill parses → `{city: Bogotá, barrio: El Chicó, m2_built: 25, building_name: Otoño, type: apartaestudio}`, asks for bedrooms if needed (apartaestudio = 0 or 1), runs the workflow, and returns a path to `outputs/el-chico-25m-YYYYMMDD-HHMM.xlsx`.
