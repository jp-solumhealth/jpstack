# Florida rates, recorded rate cards, and the closing-cost record

Everything here was read off a real settlement statement or is a Florida statutory /
promulgated rate. Nothing is estimated unless it says **ESTIMATE**.

---

## 1 — Florida statutory and promulgated rates

| Charge | Rate | Formula | Who pays (Marion County custom) |
|---|---|---|---|
| Deed documentary stamps | $0.70 per $100 | `ceil(price/100) * 100 * 0.0070` | Seller |
| Note documentary stamps | $0.35 per $100 | `ceil(loan/100) * 100 * 0.0035` | Buyer |
| Intangible tax on mortgage | 0.20% | `loan * 0.002` | Buyer |
| Clerk recording | $10.00 first page + $8.50 each additional | `10 + 8.50*(pages-1)` | Per document |
| Owner's title policy | $5.75/1,000 to $100k, then $5.00/1,000 to $1M, then $2.50/1,000 | see below | Seller |
| Lender's policy, simultaneous issue | $25.00 flat | — | Buyer |

**Owner's premium worked example, $279,000:** `100 × 5.75 = 575.00` + `179 × 5.00 = 895.00`
= **$1,470.00**.

**Rounding:** standard practice rounds coverage up to the next $1,000. Next Chapter prices on
the *exact* sale price — on $279,900 that is $1,474.50 rather than $1,475.00. A $0.50
difference in the seller's favour. Pass `--exact-premium` to reproduce it.

**Page counts that recur:**

| Document | Pages | Recording |
|---|---|---|
| Deed | 2 | $18.50 |
| Notice of Commencement termination | 2–3 | $18.50 / $27.00 |
| Residential mortgage | ~20 | $171.50 |

### Tax proration — the one everyone gets wrong

Florida bills property tax **in arrears**. The year's bill is issued in November and is due
by 31 March of the following year. At any closing before then, *nobody has paid* — but the
seller owned the property from 1 January, so the seller owes that slice and hands it to the
buyer, who will pay the full bill in November.

It appears **twice** on a HUD-1: a seller debit (line 511) and an equal buyer credit (line 211).

```
amount = annual_tax / 365 * days(Jan 1 → closing, closing day included)
```

**Assessment date is 1 January.** On a new build that means the year of construction is
assessed on the **land only**. 8 Pine Track broke ground 4 March 2026, so its 2026 bill is
~$290 against a $23,000 lot (≈12.6 mills, normal for unincorporated Marion County). The
**following** January picks up the finished house and the bill jumps to roughly
**$2,600–$3,600** *(ESTIMATE)*. That does not affect the sale closing, but it does drive the
buyer's escrow reserves — and it means any house that has not closed before its first
post-construction assessment carries a materially bigger proration.

Convention note: prorate *through and including* the closing date, or through the day before.
One day's difference. Pick one and make both statements match.

### Benchmarks

| Measure | Florida norm |
|---|---|
| Seller closing costs **including** commission | 6.0% – 9.0% of price |
| Seller closing costs **excluding** commission | 1.0% – 3.0% of price |
| Title agency fees alone | 0.25% – 0.40% of price |

---

## 2 — Recorded rate cards

Fee levels are **not comparable across transaction types**. A three-property construction-loan
closing is far more work than a one-house sale. Compare sale cards to sale cards.

### SALE, one house

| Service | Marion Lake Sumter | Next Chapter |
|---|---|---|
| Settlement / closing fee — seller | 465.00 | 385.00 |
| Settlement / closing fee — buyer | 510.00 | 750.00 |
| Title / abstract search | 85.00 | 75.00 |
| Municipal lien search | 140.00 | 165.00 |
| E-recording — seller | 6.99 | 5.25 |
| E-recording — buyer | 13.90 | 10.50 |
| Online notary (RON) | **not quoted** | 175.00 |
| Technology / secure-document fee | — | 25.00 |
| Warehousing fee | 45.00 | — |
| Seller ID verification | 19.00 (**and 19.00 to the buyer**) | — |
| Courier | — | 150.00 (buyer) |
| **Seller-side total** | **760.99** | **830.25** |
| **Seller-side, +$175 notary on both** | **935.99** | **830.25** |
| Underwriter | Alliant National | Investors Title |

Sources: Marion Lake — HUD-1 file `JANETCASH`, 8 Pine Track Trail, settlement 24 Aug 2026
(DRAFT COPY, printed 23 Jul 2026). Next Chapter — ALTA file `Test 1`, 8 Pine Track, settlement
26 Aug 2026 (a MOCK file: buyer, seller, escrow officer and lender all blank), buyer-side
figures from the **closed** ALTA file `26-543`, 31 Juniper Drive, 16 Mar 2026.

**Next Chapter's card is stable** — identical $385 / $75 / $165 on a closed file and on a quote
five months later. Its technology fee appears as "Secure Document Fee $25", "Technology Fee $25"
and "$50" across three statements: same charge, three names.

### LOAN, three properties (RBI construction loan, Jul 2026)

| Service | GO GO Titles | Next Chapter |
|---|---|---|
| Settlement / closing fee | 850.00 | 750.00 |
| Notary | 325.00 | 175.00 |
| Title search | 255.00 | 225.00 |
| Lien search | 575.00 | 495.00 |
| Endorsements | 377.35 | 402.35 |
| Escrow disbursement | 200.00 | — |
| Courier / overnight | 75.00 | 175.00 |
| E-recording | 25.00 | 36.75 |
| Deed preparation ×3 | 500.00 | — |
| LLC affidavit | 240.00 | — |
| NOC recording | 135.00 | 136.50 |
| UCC | 65.00 | 65.00 |
| Technology fee | — | 50.00 |
| **Total** | **3,622.35** | **2,510.60** |

Sources: GO GO — Combined Grid Settlement Statement file `2026-191-FL`, close 17 Jul 2026.
Next Chapter — HUD-1 file `26-757`. GO GO's $1,111.75 premium is almost entirely four lines
nobody else bills: deed prep $500, LLC affidavit $240, escrow disbursement $200, notary +$150.

### Fees to strike on sight

`technology` · `secure_doc` · `warehousing` · `id_verification` · `escrow_disbursement`.
Pass `--strike-junk`. The seller-ID-verification charge on the Marion Lake card is billed to
**both** sides — the buyer is paying to verify the seller's identity.

### What the agency keeps vs collects

The payee decides it. A fee payable to the agency is revenue; a fee payable to a search vendor,
underwriter or Simplifile is a pass-through you would pay at any agency.

| | Marion Lake | Next Chapter |
|---|---|---|
| Agency keeps | 535.99 | 410.00 |
| Passed through | 225.00 | 420.25 |
| Total | 760.99 | 830.25 |

**ESTIMATE, not disclosed anywhere:** Florida title agents typically retain ~70% of the
promulgated premium, remitting ~30% to the underwriter. On a ~$1,470 premium that is ~$1,030 —
roughly double the service fees. It is identical between agencies because the rate is
promulgated, so it never affects the choice.

---

## 3 — The closing-cost record: 8 Pine Track Trail

Seller Coco Global Management LLC · Marion County FL · parcel 9017-0275-04 · 1,400 sf model ·
cost basis **$210,474.47** (OC2 col F, F121) · started 4 Mar 2026.

### Marion Lake Sumter HUD-1 (file JANETCASH, price $279,000)

| Line | Charge | Seller | Buyer |
|---|---|---|---|
| 703 | Commission @ 4.50% (701 listing 2.00% $5,580 · 702 selling 2.50% $6,975) | 12,555.00 | |
| 1101 | Settlement or closing fee | 465.00 | 510.00 |
| 1102 | Abstract / title search → Alliant National | 85.00 | |
| 1108/1110 | Owner's title policy | 1,470.00 | |
| 1109 | Lender's policy, simultaneous | | 25.00 |
| 1201 | Recording — deed 18.50 + mortgage 171.50 | | 190.00 |
| 1203 | State doc-stamps — deed / note | 1,953.00 | 947.45 |
| 1204 | Intangible tax | | 541.26 |
| 1205 | NOC termination recording | 18.50 | |
| 1301 | Survey (estimated) | | 500.00 |
| 1303 | Municipal lien search → Total Tax & Lien Searchers | 140.00 | |
| 1304 | E-recording | 6.99 | 13.90 |
| 1305 | Warehousing fee | 45.00 | |
| 1306 | Seller ID verification | 19.00 | 19.00 |
| **1400** | **Total settlement charges** | **16,757.49** | **2,746.61** |
| 511/211 | County tax proration, 1 Jan → 24 Aug (236 d) | 187.58 | (187.58) |
| **603/303** | **Cash to seller / from buyer** | **262,054.93** | **7,929.03** |

### Next Chapter ALTA (file "Test 1", price $279,900)

| Charge | Seller |
|---|---|
| Listing agent commission 2.50% | 6,997.50 |
| Selling agent commission 2.50% | 6,997.50 |
| Seller credit to buyer | 5,000.00 |
| Title settlement fee → Next Chapter | 385.00 |
| Title search fee → Investors Title | 75.00 |
| Owner's title policy → Investors Title | 1,474.50 |
| Municipal lien search → ABC Municipal Lien Search | 165.00 |
| Online notary | 175.00 |
| Technology fee → Next Chapter | 25.00 |
| E-recording fee → Simplifile | 5.25 |
| Documentary stamp tax (deed) → Simplifile | 1,959.30 |
| Termination of NOC → Simplifile | 27.00 |
| **Subtotal** | **23,286.05** |
| **Due to seller** | **256,613.95** |
| *County tax proration* | *MISSING — should be ~189.17 at 26 Aug* |

### Cost ratios (Marion Lake structure, notary added, survey removed)

| | Amount | % price | % basis | % margin |
|---|---|---|---|---|
| Commission | 12,555.00 | 4.500% | 5.97% | 18.32% |
| Statutory + promulgated | 3,441.50 | 1.234% | 1.64% | 5.02% |
| Title agency fees | 935.99 | 0.335% | 0.44% | 1.37% |
| Tax proration | 187.58 | 0.067% | 0.09% | 0.27% |
| **Closing costs, ex-commission ex-concession** | **4,565.07** | **1.636%** | **2.17%** | **6.66%** |
| Seller concession (50/50 split, verified costs) | 1,113.81 | 0.399% | — | 1.63% |
| Buyer line items (survey removed) | 2,227.61 | 0.798% | — | 3.25% |
| Both sides, ex-commission | 6,792.68 | 2.435% | — | 9.91% |

Gross margin $68,525.53. Per sf: price $199.29 · basis $150.34 · closing costs $3.26 · net $186.26.

**The headline is 1.636%.** The concession is a price adjustment, not a cost of closing, and is
kept out of it. Commission sits on top at 4.500% and is **69% of everything the seller pays**.

### Comparable: 31 Juniper Drive (Next Chapter file 26-543, CLOSED 16 Mar 2026)

Same seller entity. Price $257,000 · net to seller **$246,473.00** (ties the model's D126 exactly).
Commission was **2.00% listing only** ($5,140) with no selling-agent line on the seller statement.
Also carried: Affidavit of No Mortgage $10.00, LLC affidavits $18.50 ×2, water test $325.00,
brokerage transaction fee $495.00 to Professional Realty of Ocala, 2025 taxes $688.66 POC.

**Use this file as the template for what a Coco Global seller statement should contain.** Every
one of those lines is absent from both 8 Pine Track statements.

---

## 4 — Open items on 8 Pine Track

1. Commission rate — 4.50% or 5.00%? The 0.5-point gap is **entirely the listing side** and worth $1,399.50.
2. Is the $5,000 seller credit a real term? The model budgets $3,000.
3. The ALTA is missing the tax proration (~$189).
4. No mortgage payoff line on either statement — confirm the parcel is unencumbered.
5. HUD lines 900 (prepaids) and 1000 (escrow reserves) are **blank** — not credible on a
   financed purchase, and it is what a percentage concession attaches to.
6. ZIP conflict: 34472 on the HUD vs 34480 on the ALTA. Verify against parcel 9017-0275-04.
7. **Ask Marion Lake in writing whether RON is included in the $465 settlement fee.** That one
   answer decides the title company: included → Marion Lake wins by $69.26; extra → Next Chapter
   wins by $105.74.
