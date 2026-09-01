# Service Type Codes (X12 EB03)

The service type code (STC) tells the payer *which* benefit you are asking about. Get it
wrong and you get a technically valid answer to the wrong question — plan-wide coverage
when you needed the behavioral health copay.

Rules of thumb:

- **`30` Health Benefit Plan Coverage** is the default and the right choice for "is this
  person covered at all". Most payers return their fullest benefit set for `30`.
- **Send one code per request.** Not all payers support all codes, and many reject requests
  carrying several. If you need cost share for three services, run three checks.
- If a payer returns nothing useful for a specific code, fall back to `30` and read the
  plan-wide lines.

## Common codes

| Code | Service type | Ask it when you need |
|------|--------------|----------------------|
| `30` | Health Benefit Plan Coverage | Active coverage, plan dates, plan-wide deductible/OOP |
| `1` | Medical Care | General medical cost share |
| `98` | Professional (Physician) Visit — Office | Office visit copay |
| `A0` | Professional (Physician) Visit — Outpatient | Outpatient visit cost share |
| `A3` | Professional (Physician) Visit — Home | Home visit coverage |
| `2` | Surgical | Surgical benefits |
| `4` | Diagnostic X-Ray | Imaging cost share |
| `5` | Diagnostic Lab | Lab cost share |
| `62` | MRI/CAT Scan | Advanced imaging — usually where prior auth shows up |
| `73` | Diagnostic Medical | Diagnostic procedures not otherwise classified |
| `47` | Hospital | Facility benefits |
| `48` | Hospital — Inpatient | Inpatient admission cost share, auth requirements |
| `50` | Hospital — Outpatient | Outpatient facility cost share |
| `51` | Hospital — Emergency Accident | ER benefits, accident |
| `52` | Hospital — Emergency Medical | ER benefits, medical |
| `86` | Emergency Services | ER copay |
| `UC` | Urgent Care | Urgent care copay |
| `88` | Pharmacy | Drug benefit, and whether it is carved out to a PBM |
| `MH` | Mental Health | Behavioral health coverage |
| `A4` | Psychiatric | Psychiatric benefits |
| `A6` | Psychotherapy | Therapy visit copay and visit limits |
| `A7` | Psychiatric — Inpatient | Inpatient behavioral health |
| `A8` | Psychiatric — Outpatient | Outpatient behavioral health |
| `AD` | Occupational Therapy | OT visits and limits |
| `AE` | Physical Medicine | PT visits and limits |
| `AF` | Speech Therapy | Speech therapy visits and limits |
| `AG` | Skilled Nursing Care | SNF benefits |
| `42` | Home Health Care | Home health visits and auth |
| `45` | Hospice | Hospice benefits |
| `76` | Dialysis | Dialysis coverage |
| `78` | Chemotherapy | Chemo coverage |
| `6` | Radiation Therapy | Radiation oncology |
| `12` | Durable Medical Equipment Purchase | DME purchase |
| `18` | Durable Medical Equipment Rental | DME rental |
| `33` | Chiropractic | Chiro visits and limits |
| `35` | Dental Care | Dental benefits (`AD` qualifier for CDT codes) |
| `40` | Oral Surgery | Oral surgery — often split between medical and dental |
| `AL` | Vision (Optometry) | Vision benefits, often carved out |
| `80` | Immunizations | Vaccine coverage |
| `81` | Routine Physical | Preventive visit, usually $0 |
| `82` | Family Planning | Family planning benefits |
| `BT` | Gynecological | GYN benefits |
| `BU` | Obstetrical | OB benefits |
| `BV` | Obstetrical/Gynecological | Combined OB/GYN |
| `65` | Newborn Care | Newborn coverage |
| `68` | Well Baby Care | Well-child visits |
| `20` | Second Surgical Opinion | Second-opinion requirement |
| `13` | Ambulatory Service Center Facility | ASC facility benefits |
| `93` | Podiatry | Podiatry benefits |
| `BG` | Cardiac Rehabilitation | Cardiac rehab visits |

## Mapping from a procedure code

If you have a CPT/HCPCS code and not an STC, two options:

1. **Ask by procedure code.** Send `encounter.procedureCode` with
   `productOrServiceIDQualifier: "HC"` (or `"AD"` for CDT). Only some payers answer at code
   level, but when they do the answer is specific to that procedure.
2. **Map to the nearest STC** using the table above — CPT 99213 → `98`, CPT 70553 → `62`,
   CPT 90837 → `A6`, CPT 97110 → `AE`.
