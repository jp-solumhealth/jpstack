# property-appraisal-co

Indicative residential-property appraisal for Colombia, designed to support **collateralized lending** decisions. Takes a free-text description (or a listing URL, or a matrícula inmobiliaria) and produces a spreadsheet with sale comps, rent comps, valuation range, gross yield, and a suggested max loan amount at a configurable LTV.

Sources scraped: **Fincaraíz, Metrocuadrado, Vivienda.com, MercadoLibre Inmuebles**. Enrichment: **constructora + año de construcción**, **Catastro Bogotá / Medellín** (best-effort, surfaces a manual link), **SNR / matrícula** (best-effort).

Browser automation runs through a local **Kernel** sandboxed Chromium (Docker), driven by Playwright over CDP.

> **Indicative only — not a certified avalúo (Resolución SNR / RNA).** Comps are listing prices, not closed sales.

---

## What you get

An XLSX with five tabs:

1. **Summary** — subject card, valuation range (P25/P50/P75 × m²), rent estimate, gross yield, suggested loan, confidence flag, disclaimer.
2. **Sale comps** — every kept comp with link back to the original listing.
3. **Rent comps** — same shape for rentals.
4. **Enrichment** — constructora, año, catastro flags, SNR status.
5. **Log** — per-portal scrape stats + dropped-comp reasons.

---

## Prerequisites

- macOS or Linux with **Docker** installed and running (`docker --version`)
- **Python 3.10+**
- **Git** (to clone the Kernel images repo)
- ~10 GB free disk (Kernel image ≈ 2 GB; build cache extra)

---

## One-time setup

### 1. Clone the Kernel images repo

```sh
git clone https://github.com/kernel/kernel-images.git ~/kernel-images
```

### 2. Build the Kernel Chromium-headful Docker image

```sh
cd ~/kernel-images/images/chromium-headful
IMAGE=kernel-docker ./build-docker.sh
```

This creates a local image tagged `kernel-docker`. Re-runs are fast (cached).

### 3. Drop this skill folder somewhere convenient

```sh
# Pick a path you like — the skill is self-contained inside this folder.
mv property-appraisal-co ~/property-appraisal-co
cd ~/property-appraisal-co
```

### 4. Install Python deps

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install playwright openpyxl
# Playwright doesn't need its own browsers — we connect to Kernel via CDP.
```

### 5. Point the skill at your Kernel repo (only if not at `~/Documents/Claude/Agents/kernel-images`)

Edit `scripts/kernel_docker.py`, line ~8:

```python
KERNEL_REPO = Path.home() / "kernel-images/images/chromium-headful"
```

…to match where you cloned `kernel-images`.

---

## Running an appraisal

From the skill folder root:

```sh
python -m scripts.run_appraisal "apartaestudio 25m Chico Bogotá edificio Otoño"
```

Other input forms the parser accepts:

| Input | Example |
|-------|---------|
| Free text | `"3 hab 90m Chapinero Bogotá"` |
| Matrícula inmobiliaria | `"50C-1234567"` |
| Listing URL | `"https://www.fincaraiz.com.co/inmueble/..."` |
| Mixed | `"apto 120m El Poblado Medellín 3 hab edificio Aurora"` |

### Flags

| Flag | Default | Effect |
|------|---------|--------|
| `--ltv 0.55` | `0.60` | Loan-to-value applied to median appraised value |
| `--no-rent` | off | Skip rent comps (faster) |
| `--portals fincaraiz,metrocuadrado` | all 4 | Restrict to specific portals |
| `--max-comps 50` | `30` | Cap comps per portal |
| `--out-dir /path/to/dir` | `~/Documents/Claude/property-appraisal-co/outputs` | Where to write the XLSX |

### Console output (example)

```json
{
  "out": "/home/you/.../el-chico-25m-20260509-1742.xlsx",
  "n_sale_comps": 18,
  "n_rent_comps": 11,
  "appraised_mid": 295000000,
  "rent_p50": 2400000,
  "gross_yield_pct": 9.76,
  "max_loan_cop": 177000000,
  "confidence": "high"
}
```

---

## How it works

```
input parser → kernel_docker.ensure_running()
            ↓
       Playwright over CDP (single browser, sequential portals)
            ↓
  search_sales (×4 portals)        search_rentals (×4 portals)
            ↓                              ↓
        comp_filter ←-- subject -→     comp_filter
            ↓                              ↓
        valuation                      rent_estimator
            ↓                              ↓
            └──────── loan_sizer ──────────┘
                          ↓
                    enrichment
              (constructora / catastro / SNR)
                          ↓
                     xlsx_writer → outputs/<barrio>-<m2>m-<ts>.xlsx
```

### Comp filter rules

Default keeps a listing if **all** of:
- Same city as subject
- Same barrio OR adjacent barrio (extend `BARRIO_ADJACENCY` in `scripts/comp_filter.py`)
- m² within ±20% of subject
- Bedrooms within ±1 of subject
- (If listing date present) within last 90 days
- Not a duplicate (URL or price+m²+barrio hash)

### Confidence flag

| n comps kept | Confidence |
|---|---|
| ≥ 15 | `high` |
| 8–14 | `medium` |
| < 8 | `low` |

---

## Important caveats

- **Anti-bot.** Fincaraíz and MercadoLibre sit behind Cloudflare. Kernel's headful Chrome usually passes, but if a portal blocks, the skill logs the failure and continues with the rest.
- **Catastro / SNR.** Both portals require interactive forms (Bogotá) or paid VUR requests (SNR). The skill captures the deep links and flags them as `manual` for v1. Wire credentials in `scripts/enrichment/snr.py` if you want full automation.
- **Listing prices ≠ closed sales.** Apply your own market adjustment before writing a loan.
- **Geography.** v1 tunes for **Bogotá** and **Medellín**. Other cities work but with thinner barrio adjacency data.

---

## Folder layout

```
property-appraisal-co/
├── README.md               (this file)
├── skill.md                (skill manifest — used by Claude / agent harnesses)
└── scripts/
    ├── run_appraisal.py    (CLI entry point)
    ├── kernel_docker.py    (boots/reuses Kernel container)
    ├── input_parser.py     (free-text → Subject)
    ├── comp_filter.py
    ├── valuation.py
    ├── rent_estimator.py
    ├── loan_sizer.py
    ├── xlsx_writer.py
    ├── scrapers/
    │   ├── base.py
    │   ├── _card_extract.py
    │   ├── fincaraiz.py
    │   ├── metrocuadrado.py
    │   ├── vivienda.py
    │   └── mercadolibre.py
    └── enrichment/
        ├── constructora.py
        ├── catastro_bogota.py
        ├── catastro_medellin.py
        └── snr.py
```

---

## Troubleshooting

**`KernelError: CDP endpoint never came up`** — container started but Chromium didn't expose port 9222 in time. Run `docker logs kernel-docker` to inspect. The image needs ≥4 GB RAM allocated to Docker.

**`No price`/`barrio not adjacent` drops everything** — the portals returned a different DOM than expected. Check the **Log** tab; if a single portal is the culprit, restrict with `--portals` and inspect that scraper.

**Captcha page captured** — the Kernel container ships a remote-view URL on startup. SSH-tunnel to it, complete the captcha once; cookies persist for the container's lifetime.

**Want to extend to a new city** — add the barrio adjacency to `BARRIO_ADJACENCY` in `comp_filter.py` and the city/barrio hints in `input_parser.py`.

---

## License & credit

Skill code: do whatever you want with it. Kernel images: see the upstream repo at `github.com/kernel/kernel-images`.
