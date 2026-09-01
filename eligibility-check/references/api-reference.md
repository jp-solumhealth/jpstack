# Stedi Healthcare API Reference

Condensed reference for the endpoints this skill uses. Canonical docs:
<https://www.stedi.com/docs/healthcare/api-reference>.

Response field names below reflect the documented shape at the time of writing.
`scripts/stedi.py` reads them defensively and always keeps the raw JSON, so if Stedi
renames or adds a field the summary degrades rather than breaks. When something looks
missing, print `--raw` and check the live shape against the docs.

---

## Auth

Every request carries the API key **raw** in the `Authorization` header — no `Bearer`
prefix:

```
Authorization: <STEDI_API_KEY>
Content-Type: application/json
```

Base URL: `https://healthcare.us.stedi.com/2024-04-01`

---

## Real-Time Eligibility Check (270/271)

`POST /change/medicalnetwork/eligibility/v3`

### Request

```json
{
  "tradingPartnerServiceId": "60054",
  "provider": {
    "organizationName": "Solum Health",
    "npi": "1999999984"
  },
  "subscriber": {
    "memberId": "W123456789",
    "firstName": "Jane",
    "lastName": "Doe",
    "dateOfBirth": "19000101"
  },
  "encounter": {
    "serviceTypeCodes": ["30"],
    "dateOfService": "20260901"
  }
}
```

| Field | Notes |
|-------|-------|
| `tradingPartnerServiceId` | **Required.** The payer ID. Primary payer ID, Stedi payer ID, or any alias on the payer record. Look it up with Search Payers rather than guessing. |
| `provider.npi` | **Required.** 10 digits, must pass check-digit validation. In test mode any valid-checksum NPI works. |
| `provider.organizationName` | **Required.** Any name in test mode. |
| `subscriber` | At least one of `memberId`, `dateOfBirth`, `lastName`. Payers are only obliged to answer when `memberId` + `dateOfBirth` + `firstName` + `lastName` are all supplied — send all four when you have them. |
| `subscriber.dateOfBirth` | `YYYYMMDD`. |
| `encounter.serviceTypeCodes` | Defaults to `30` (Health Benefit Plan Coverage) when omitted. Prefer one code per request; many payers reject multiples. |
| `encounter.dateOfService` | `YYYYMMDD`. Omit for "today". Some payers reject future or far-past dates. |
| `encounter.procedureCode` + `productOrServiceIDQualifier` | Code-level check where the payer supports it. `HC` = CPT/HCPCS, `AD` = CDT (dental). |
| `dependents[]` | Same name/DOB shape, for checks on a dependent under the subscriber's policy. |
| `controlNumber` | **Deprecated** — Stedi generates one per check. Do not send it. |

### Response

Top-level shapes worth reading:

| Field | What it holds |
|-------|---------------|
| `meta.traceId` | Stedi's identifier for the transaction. Quote it in support tickets. |
| `subscriber` / `dependents` | The patient as the payer has them on file — often the authoritative spelling, address, and member ID. |
| `payer` | Payer name and identifiers as returned in the 271. |
| `planStatus[]` | `status` (e.g. `Active Coverage`), `planDetails`, `serviceTypeCodes`. The clearest coverage answer. |
| `planDateInformation` | Plan begin/end, eligibility begin/end. |
| `benefitsInformation[]` | The bulk of the answer — one entry per benefit line. See below. |
| `errors[]` (top level and nested) | AAA rejections. Presence means the lookup failed, not that the patient is uninsured. |

### `benefitsInformation[]` entries

| Field | What it holds |
|-------|---------------|
| `code` | X12 EB01 code. `1` Active Coverage, `6` Inactive, `A` Co-Insurance, `B` Co-Payment, `C` Deductible, `G` Out of Pocket (Stop Loss), `F` Limitations, `I` Non-Covered, `R` Other or Additional Payor, `U` Contact Following Entity. |
| `name` | Human-readable form of `code`. |
| `serviceTypeCodes` | Which services this line applies to. A line with no codes applies plan-wide. |
| `coverageLevel` / `coverageLevelCode` | `Individual`, `Family`, `Employee and Spouse`, etc. |
| `timeQualifier` | `Calendar Year`, `Remaining`, `Visit`, `Service Year`. **`Remaining` is the number that matters** for a deductible or OOP max. |
| `benefitAmount` | Dollar amount. |
| `benefitPercent` | Decimal fraction — `0.2` means 20%. |
| `inPlanNetworkIndicatorCode` | `Y` in-network, `N` out-of-network, `W` not applicable, `U` unknown. |
| `authOrCertIndicator` | Whether prior auth or certification is required. |
| `benefitsRelatedEntities` | Carve-out vendors, delegated networks, the entity to call. |
| `additionalInformation` | Free text — visit limits, plan notes. Read it; payers hide real limits here. |

---

## Search Payers

`GET /payers/search?query=<text>&pageSize=<n>`

Case-insensitive with fuzzy matching. `query` takes a payer name, ID, or alias. Add
`eligibilityCheck=SUPPORTED` (also `claimStatus=SUPPORTED`, `claimSubmission=SUPPORTED`) to
restrict to payers supporting that transaction. Returns matching payer records with
`primaryPayerId`, `stediId`, `aliases`, display names, and supported transaction types.

## Retrieve Payer

`GET /payer/{stediId}` — one payer record by Stedi payer ID.

---

## Test Mode

- Sandbox accounts are free and limited to test mode; they can only create test API keys.
- Test keys hit the **same production endpoints** and return realistic mock benefits —
  active coverage indicators, copays, deductibles — without contacting a payer.
- Mock responses only come back for a **fixed set of predefined requests**. The patient
  fields (name, DOB, member ID) must match the documented values exactly; anything else
  returns an error. Any organization name and any checksum-valid NPI are accepted.
- Get the current mock request values from
  <https://www.stedi.com/docs/healthcare/api-reference/mock-requests-eligibility-checks> —
  Stedi adds mocks over time, so treat the docs page as the source of truth rather than
  hardcoding a member ID here.
- Test mode also covers the Stedi Agent payer for end-to-end workflow testing.

---

## Not wrapped by this skill

Available on the same API and worth knowing about:

- **Batch Eligibility Check** — asynchronous bulk 270s, for rosters large enough that
  per-row real-time calls are the wrong tool.
- **Claim Status (276/277)** — where a submitted claim stands with the payer.
- **Professional Claims (837P)** — claim submission.
- **Insurance Discovery** — find coverage when the patient cannot produce a card.
- **Coordination of Benefits** — which plan is primary.
- **Raw X12 eligibility** — post a 270 and get a 271 back as EDI, when a downstream system
  needs the wire format.
