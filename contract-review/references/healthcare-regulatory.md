# Healthcare, HIPAA & Regulatory Review

For any healthcare-technology contract, work this top to bottom. Quote the clause; cite the
regulation. Solum Health's posture: a technology provider and (usually) a HIPAA **Subcontractor**,
never a provider, payer, biller, or clearinghouse, giving no medical/legal/coding/reimbursement
advice.

## HIPAA posture — Business Associate vs Subcontractor

Get this right first; it drives the whole PHI architecture.

- **Covered Entity (CE)** — the provider/payer.
- **Business Associate (BA)** — a vendor handling PHI for a CE (45 C.F.R. § 160.103).
- **Subcontractor** — a vendor handling PHI for a BA. If the customer is itself a BA of downstream
  CEs (e.g., an RCM/EHR company serving provider clients), then **we are a Subcontractor**, and the
  attached instrument must be a **Subcontractor Business Associate Agreement**, not a plain BAA.

Confirm in the contract:

- The Subcontractor status is stated (45 C.F.R. § 160.103) and the agreement is construed consistent
  with **§§ 164.502(e)** (BA/subcontractor contracts) and **§ 164.308(b)** (business associate
  contracts / written assurances).
- The BAA is a **condition precedent** to any PHI processing — no Platform access, no PHI, before it
  is executed and before the effective date.
- The **attached** BAA is our Subcontractor master, not the counterparty's redlined vendor BAA, so
  its liability terms already match (or defer to) the main Section 9 cap. If it is the customer's
  paper, check for an uncapped-indemnity or liability clause that fights the main cap.
- **De-identification** rights (§ 164.514(b)) and data-aggregation rights are granted **in the BAA**,
  not only in the Terms — a Subcontractor's permissible uses flow from the BAA chain. If the Terms
  grant de-identified-data use but the BAA does not, and the BAA controls PHI, the rights are
  stranded.
- **No PHI for AI training.** PHI is never used to train, develop, test, or improve AI models or for
  general product development; such work uses only De-identified Data (§ 164.514), and the covenant
  **survives termination**. Confirm no savings clause ("nothing restricts us from enhancing the
  Platform") reopens a PHI-training backdoor — add "for clarity, this does not permit any use of PHI
  prohibited by the first sentence."
- **Breach notification, minimum-necessary, and PHI return/destruction** live in the BAA, not the
  main body — confirm the body does not restate or contradict them, and that the body's data-return
  window aligns with the BAA.

## Fraud & abuse — the FMV pricing spine

Federal-program dollars flow through these contracts; a mispriced fee is a compliance problem, not
just a commercial one.

- **Anti-Kickback Statute (AKS)**, **Stark Law**, **False Claims Act (FCA)**, and **EKRA** (the
  Eliminating Kickbacks in Recovery Act) — each party represents compliance; the customer owns its
  and its clients' billing, coding, and claims.
- **Fair-market value, per-item pricing.** Fees are FMV for technology services, earned per item
  processed **regardless of the payer's outcome**, **never a percentage** of any amount approved,
  paid, or recovered, and **not tied to referrals**. This is the clause that keeps the deal clean
  under AKS/EKRA — a percentage-of-recovery or referral-linked fee is the classic violation.
- **Administrative-convention framing.** The non-billing of payer non-responses, failed
  transactions, and retries is an **administrative convention, not outcome-based/contingency
  pricing** — say so, or a reviewer may read free-on-failure as contingency pricing.
- **Exclusion & debarment.** Each party reps neither it nor its personnel is excluded/debarred from
  any federal healthcare program (OIG LEIE / SAM), with prompt notice on change; uncured exclusion
  within 30 days is cause for termination.
- **TCPA / Junk Fax.** All Platform outreach is directed to **payers, not patients**; the customer
  owns patient communications and TCPA / Junk Fax Prevention Act compliance. If any feature could
  contact patients, the "payers not patients" representation is inaccurate — verify.

## Clinical guardrails

- **Assistive only.** All clinical, medical-necessity, coding, and treatment decisions remain with
  the customer's or its clients' licensed **Health Professionals**, who review AI outputs before any
  clinical or billing use.
- **No guarantee.** Payers decide authorizations and payment; no guarantee of approval, payment,
  turnaround, approval rate, or savings. All ROI/business-case figures are **estimates, not
  warranties**, with an **anti-reliance** acknowledgment ("Customer has not relied on any projection
  or savings figure").
- **Third-party dependencies.** The Platform depends on systems outside our control (the customer's
  platform, payer APIs/portals, clearinghouses); their failures are not our breach.

## Security — Trust Center as source of truth

- Reference the published **Trust Center** as the source of truth for certifications and controls;
  **do not invent** SOC 2 / HITRUST / ISO claims, audit frequencies, or response times.
- Safe, market language: an information-security program covering encryption, access controls,
  authentication, audit logging, vulnerability management, incident response, disaster recovery,
  business continuity, and secure development, **consistent with the Trust Center as updated from
  time to time**; a **no-material-degradation** covenant; report access under NDA; a **subprocessor**
  list with advance-notice for new subprocessors handling PHI.
- Verify each named program element actually appears in the Trust Center before it goes in the
  contract — "consistent with the Trust Center" makes an unsupported element an overstatement.

## Governing law

Delaware law and exclusive Delaware venue are the Solum default; add a mutual jury-trial waiver.
Anti-reliance + a fraud carve-out are Abry-compatible for Delaware.
