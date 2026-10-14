# Solum Health ICP Classification Criteria

Use these rules to classify conference attendees as ICP or non-ICP for Solum Health.
Solum Health sells AI-powered front office automation (intake, scheduling, prior auth,
benefits verification, patient communication) to therapy and outpatient practices.

## Primary ICP (High Priority — Enrich Immediately)

These are direct buyers or key decision-makers at target companies.

### Roles
- Practice Owner / Founder
- CEO, COO, CFO of a therapy/behavioral health organization
- VP of Operations / VP of Clinical Operations
- Director of Operations
- Regional Director / Area Director (multi-site)
- Managing Partner

### Company Types
- Behavioral health groups (mental health, counseling)
- ABA therapy providers
- PT / OT / Speech therapy groups
- Multi-location outpatient clinics
- Substance use disorder (SUD) treatment centers
- Psychiatric group practices
- Counseling center groups
- IDD (Intellectual/Developmental Disability) service providers

### Company Size Signals
- 5+ providers (too small = solo practice, not a fit)
- Multiple locations preferred
- Growing or recently acquired practices
- PE-backed behavioral health platforms

## Secondary ICP (Medium Priority — Enrich If Capacity Allows)

These people influence buying decisions or manage the processes Solum automates.

### Roles
- Office Manager / Practice Manager
- Billing Director / RCM Director / Revenue Cycle Manager
- Director of Intake / Patient Access Director
- Clinical Director (if also handles operations)
- Director of Admissions
- IT Director at a therapy organization
- Chief of Staff

### Additional Company Types
- Virtual/telehealth therapy platforms
- Residential treatment programs with outpatient arms
- PHP/IOP programs
- Pediatric therapy groups
- Integrated behavioral-physical health clinics

## NOT ICP — Do Not Enrich

Skip these entirely. Don't waste Apollo credits.

### Roles to Exclude
- Individual clinicians / solo practitioners (therapists, psychologists, social workers
  without management/ownership role)
- Sales reps and account executives at vendor companies
- Marketing managers at non-healthcare companies
- Consultants (unless they specifically advise therapy practices on operations)
- Professors / researchers (unless also practice owners)
- Government employees (CMS, state agencies)
- Insurance/payer employees (Aetna, UHC, etc.)
- Pharma representatives
- Hospital system administrators (too large, different workflow)
- EHR vendor employees (competitors or adjacent)

### Company Types to Exclude
- Health systems / hospitals (500+ beds, enterprise sales cycle)
- Insurance companies / payers
- Pharmaceutical companies
- Medical device manufacturers
- Staffing agencies
- Law firms (even healthcare-focused)
- Accounting firms
- Real estate companies
- Technology vendors / SaaS companies (unless they're also running a practice)
- Academic institutions
- Government agencies

## "Maybe" Classification

When you're unsure, classify as "Maybe" and include a note. Common edge cases:

- **Title says "Director" but company is unclear**: Mark Maybe, enrich to check company type
- **Company is healthcare but not clearly therapy/behavioral**: Mark Maybe, check via Apollo
- **Person is a consultant who advises behavioral health practices**: Mark Maybe, they can
  be referral partners
- **Company is a large health system but has a behavioral health division**: Mark Maybe,
  the BH division lead could be relevant
- **Virtual-only provider**: Mark Maybe, depends on size. Virtual therapy groups with 10+
  clinicians are a fit.
- **PE firm investing in behavioral health**: Mark as Secondary ICP. They influence
  portfolio company decisions and can introduce Solum to all their holdings.

## Role Category Labels

When classifying, assign one of these labels:

| Label | Description |
|---|---|
| Practice Owner | Owns or co-owns the practice |
| C-Suite | CEO, COO, CFO, CTO, CMO |
| VP/Director Ops | VP or Director of Operations, Regional Director |
| Clinic Manager | Office Manager, Practice Manager, Clinic Administrator |
| Billing/RCM | Billing Director, RCM Manager, Revenue Cycle Lead |
| Clinical Director | Clinical Director with operational responsibilities |
| Intake/Access | Director of Intake, Patient Access, Admissions |
| PE/Investor | Private equity, investor, board member in BH |
| Consultant | Consultant or advisor to therapy practices |
| Other | Doesn't fit above categories but still ICP |

## Company Type Labels

| Label | Description |
|---|---|
| Behavioral Health | Mental health, counseling groups |
| ABA | Applied behavior analysis providers |
| PT/OT/Speech | Physical, occupational, speech therapy |
| SUD Treatment | Substance use disorder / addiction treatment |
| Mental Health | Psychiatric practices, psychology groups |
| Multi-Specialty | Multiple therapy types under one org |
| Virtual/Telehealth | Primarily virtual therapy providers |
| Residential+ | Residential with outpatient arm |
| Pediatric Therapy | Child/adolescent focused therapy |
| IDD Services | Intellectual/developmental disability |
| PE-Backed Platform | PE portfolio company in behavioral health |
| Other Healthcare | Healthcare adjacent, not clearly above |

## Scoring Shortcut

For quick classification when processing large lists:

1. **Title contains**: owner, CEO, COO, CFO, founder, president, partner, VP operations,
   director operations → Check company type. If therapy/BH → Primary ICP.

2. **Title contains**: manager, director (billing/intake/clinical/office), administrator
   → Check company type. If therapy/BH → Secondary ICP.

3. **Title contains**: therapist, counselor, psychologist, social worker (WITHOUT
   owner/director/manager) → Not ICP (individual clinician).

4. **Company name contains**: therapy, behavioral, mental health, counseling, ABA,
   rehabilitation, recovery, wellness (clinical context), psychiatric → Likely target company.

5. **Company name contains**: hospital, health system, insurance, pharma, university,
   staffing, consulting, legal → Likely NOT target company (check edge cases).
