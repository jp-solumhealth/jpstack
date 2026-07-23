---
name: contract-review
description: >
  Use for legal review, QA, and negotiation of a commercial contract — SaaS/vendor/customer
  agreements, order forms, MSAs, BAAs, healthcare-technology contracts, and their terms &
  conditions — as counsel for one side (default: protect Solum Health). Reviews the liability
  stack, HIPAA/healthcare-regulatory posture, cross-reference and defined-term integrity,
  Order-Form-vs-Terms consistency, and commercial economics; predicts the other side's redlines;
  and returns ranked findings, a scorecard, and an APPROVED / APPROVED WITH CHANGES / DO NOT SEND
  recommendation. Triggers: "review this contract", "legal review", "run QA on the contract",
  "is this agreement ok", "review the customer agreement / order form / MSA / SaaS agreement",
  "review the BAA", "liability cap review", "check the indemnity", "does this protect us",
  "review as opposing counsel", "what will their GC push back on", "redline this",
  "align the terms with the order form", "contract scorecard", "HIPAA subcontractor posture",
  "healthcare contract review", or any commercial agreement / order form / terms PDF or DOCX
  dropped in with intent to vet, align, or negotiate it before signing.
---

# Commercial Contract Review & QA

End-to-end legal QA of a commercial agreement: verify the document is internally consistent, the
liability and risk allocation protects our side, the healthcare/HIPAA posture is correct, and the
economics are sound — then predict the counterparty's redlines, rank findings by risk, and give a
signature recommendation. **Quote actual clause text for every finding. Trace every cross-reference.
Never trust a summary — read the operative language and show where it breaks.**

Default posture: **counsel for Solum Health.** Protect our side wherever market practice reasonably
allows, but never draft an obviously one-sided or bad-faith clause — a term a court won't enforce,
or that reads as overreach, taxes the whole negotiation. State the client's deliberate choices up
front and do not flag them as defects.

## When to use

- A customer agreement, order form, MSA, vendor paper, BAA, or terms & conditions arrives and needs
  vetting, alignment, or a signature decision.
- The user asks to review liability/indemnity, align an order form with embedded terms, run a
  multi-role QA, predict the other side's redlines, produce a scorecard, or clean the drafting.
- Any healthcare-technology contract where HIPAA (Business Associate vs Subcontractor), AKS/Stark/
  FCA/EKRA, FMV pricing, or PHI handling is in play.

Not for: real-estate loan closings (use `real-estate-closing-check`), drafting the counterparty's
paper, or SOW scoping from calls (use `sow-builder`).

## Establish the deal facts first (do not skip)

Before reading a single clause, pin the facts the whole review hangs on, from the user or the
source docs — never invent them:

- **Parties and roles.** Who is vendor, who is customer, who is the Business Associate vs the
  Subcontractor, is there a downstream provider-client book?
- **The economics.** Rates, minimums, ramp, term length, renewal, termination rights.
- **The deliberate choices.** What has the client already decided (e.g., no insurance clause,
  a specific cap structure, business case as an appendix)? These are constraints, not findings.
- **The document set and precedence.** Order Form, Terms & Conditions, Key/Special Terms,
  Definitions, Appendices (BAA, proposal, business case) — and their order of precedence.

Record these; every later phase checks against them.

## Phase 1 — Structure & consistency

The most common real defect is an Order Form / Key Terms that says one thing and embedded Terms that
say another, reconciled only by fragile "Notwithstanding" overrides. Check:

- **Order-of-precedence** exists, is stated once, and ranks the documents sensibly (a BAA controls
  PHI handling; a Section 9 liability cap should still govern aggregate liability — see
  `references/liability-and-risk.md`).
- **Alignment.** Where the Order Form modifies the Terms, prefer editing the Terms directly to match
  the deal over stacking overrides. Every generic Term that contradicts the deal (evaluation
  periods, convenience termination, default minimums, unilateral amendment, one-sided publicity) is
  a consistency defect even if an override "handles" it.
- **Cross-references resolve.** Every "Section N" and "Section N of the Terms" points to a section
  that exists. After any restructure, check that no reference dangles (a moved Definitions section
  is the classic trap: "Section 11 of the Terms" must then appear nowhere).
- **Defined-term hygiene.** Every capitalized defined term is defined once, used consistently, and
  not orphaned. Flag capitalized-but-undefined terms and defined-but-unused terms.
- **Modification recap.** If the Order Form modifies the Terms, a recap should list exactly which
  sections it modifies and supplements — and that list must be complete and correct.

`references/drafting-standards.md` has the cross-reference and defined-term discipline in full.

## Phase 2 — Liability stack (the engine)

This is where a contract is won or lost for our side. Reconstruct the entire stack from the operative
clauses and confirm it is internally consistent, top to bottom (`references/liability-and-risk.md`):

- **Consequential-damages waiver** (mutual), **direct-liability cap**, **indemnity treatment**,
  **carve-outs**, and the **uncapped set**.
- Confirm how **security-incident / data-breach / PHI liability** is capped — inside the general cap,
  or a separate super-cap — and that the drafting actually attaches to the right subsection.
- Confirm **indemnities** are capped (or deliberately uncapped) and that the cap magnitude and basis
  (e.g., trailing-12-month fees vs a multiple of annualized contract value, with or without a floor)
  match what was agreed.
- Watch for **collisions**: a clause that caps and uncaps the same claim; a "Notwithstanding" that
  accidentally re-exposes indemnities to the consequential-damages waiver; a floor that makes an
  early-term cap either meaningless or larger than intended.
- Verify the **precedence override** blocks a BAA or exhibit from silently displacing the cap.

## Phase 3 — Healthcare, HIPAA & security

For any healthcare-tech deal, work `references/healthcare-regulatory.md` top to bottom:

- **HIPAA posture.** Business Associate vs **Subcontractor** (45 C.F.R. § 160.103), BAA as a
  **condition precedent** to any PHI processing, construction consistent with §§ 164.502(e) /
  164.308(b), de-identification per § 164.514, and a **no-PHI-for-AI-training** covenant that
  survives termination. Confirm the BAA (not the vendor's redlined paper) is the attached instrument
  and that its liability terms do not fight the main cap.
- **Fraud & abuse.** Anti-Kickback Statute, Stark, False Claims Act, EKRA; **fair-market-value**
  per-item pricing (never a percentage of amounts approved/paid/recovered, never tied to referrals);
  the non-billing of failed transactions framed as an administrative convention, not contingency
  pricing; OIG/SAM **exclusion & debarment** reps; **TCPA** / Junk Fax for any outreach.
- **Security.** Reference the vendor's Trust Center as the **source of truth**; do not invent
  certifications, audit frequencies, or response times. A no-material-degradation covenant plus
  report access under NDA and a subprocessor list with change notice is market and safe.
- **Clinical guardrails.** Assistive-only, licensed Health Professional review before clinical/
  billing use, no guarantee of approval/payment/turnaround, all ROI figures are estimates not
  warranties, with an anti-reliance acknowledgment.

## Phase 4 — Commercial & economics

Read as CFO and CEO (`references/review-roles.md`):

- **Revenue protection.** Greater-of minimums, no rollover, minimums surviving to the termination
  date, firm committed periods, no downgrades mid-term, a **renewal escalator** (CPI-capped is the
  single highest-leverage, least-aggressive protection), determinate payment triggers.
- **Termination exposure, quantified.** Compute the worst-case and best-case collected revenue for
  every exit path (earliest notice, latest notice). Show the numbers.
- **Revenue leakage.** Definitional edges (e.g., an eligibility transaction used as a benefit-check
  substitute riding free), uncapped pass-throughs, indeterminate fee triggers, agreement-to-agree
  targets.
- **Verify every number.** Re-derive all arithmetic (run-rates, annualized values, cap magnitudes,
  business-case figures) from the rates and volumes. Never relay a figure you have not recomputed.
  Label estimates as estimates; keep committed floors distinct from targets.

## Phase 5 — Multi-role stakeholder review (run the benches)

For a full QA, review the contract independently from each stakeholder's seat. Dispatch these as
parallel subagent benches on a flattened text dump, then reconcile (`references/review-roles.md` has
each role's checklist and questions):

1. **Head of Legal (our side)** — enforceability, consistency, are we protected, would I sign.
2. **Opposing counsel (their GC)** — ambiguity, overreach, hidden obligations; predict the redlines
   ranked by likelihood, and the zero-cost concessions to pre-empt them.
3. **CEO** — growth, overpromise, accidental custom-dev or roadmap commitments, scalability.
4. **CFO** — revenue protection, leakage, termination exposure, cash-flow, pricing flexibility.
5. **COO / Operations** — can we actually deliver every SLA/target; are customer dependencies strong
   enough to excuse us; is "business hours" defined.
6. **VP Engineering** — API/integration scope, no customer-specific build obligation without a
   signed SOW, no delivery-date commitments.
7. **Security Officer** — every security clause matches the published Trust Center; nothing invented.
8. **HIPAA Officer** — BA/Subcontractor architecture, PHI handling, BAA consistency.
9. **Procurement** — can the deal (price, term, exit, minimums, scope) be extracted in five minutes.
10. **Customer Success** — where a customer could reasonably misunderstand support, turnaround,
    scope, or the exit-cost mechanics.

Verify findings adversarially before reporting them — a plausible-sounding finding that does not
survive a re-read of the actual clause is a false positive; say so and drop it.

## Phase 6 — Deterministic QA + drafting cleanup

`scripts/contract_qa.py <file.docx|.pdf>` — flags the mechanical defects a human skims past:
em/en dashes, straight quotes, all-caps wall-of-text clauses (conspicuousness/readability),
buzzwords and AI tells, drafting brackets/TBDs, table-width mismatches (DOCX), and every
"Section N.N" reference with no matching heading (dangling-reference heuristic). Run it on the final
file. Then apply the drafting standard (`references/drafting-standards.md`): plain modern English,
active voice, short sentences, sentence-case conspicuous disclaimers (bold, not walls of caps), no
legalese/archaic terms, American spelling, and none of the AI-generation tells.

## Phase 7 — Findings, scorecard, recommendation

- **Rank every finding** Critical / High / Medium / Low, each with the quoted text, a concrete
  failure scenario (inputs → wrong outcome), and a one-line fix. Critical/High block signature.
- **Scorecard** (1-10): Legal Quality, Commercial Quality, Negotiation Readiness, Formatting,
  Readability, Operational Feasibility, Security, HIPAA, Governing-Law Compliance, Executive
  Friendliness, Procurement Friendliness, Overall Contract Readiness.
- **Recommendation** — one of: APPROVED · APPROVED WITH MINOR CHANGES · APPROVED WITH MAJOR
  REVISIONS · DO NOT SEND. Say what the "minor changes" are; separate drafting defects from
  execution steps (e.g., physically attaching the BAA).

## Red flags — stop and confirm

- Order Form and Terms describe the same thing differently → reconcile; the override is not enough.
- A cap that also uncaps the same claim (indemnity for willful misconduct capped and uncapped).
- A "Notwithstanding Section 9.3(a)" that pulls indemnities back under the consequential-damages bar.
- Minimums that survive **the customer's** termination for the vendor's own uncured breach → a
  penalty-doctrine loser that reads as bad faith; carve it out.
- Data-breach / PHI liability silently outside the cap, or a BAA whose own liability clause fights
  the main cap.
- Invented security certifications, audit frequencies, or SLAs not in the Trust Center.
- Percentage-of-recovery or referral-linked pricing in a federal-program contract (AKS/EKRA).
- A defined term used before/without definition; "Section 11 of the Terms" after Definitions moved.
- Unilateral amendment or one-sided publicity against a firm, non-cancelable commitment.
- Renewal pricing frozen forever with no escalator; uncapped pass-through charges.
- Em-dashes, buzzwords, wall-of-caps clauses, "[Attach … here]" brackets in a document called final.

## Output

Never inline-dump the full contract. Deliverables go to the deal's project folder: a ranked QA
report (MD), a themed HTML preview of the agreement for readable review, and — when negotiating — a
clause revision schedule (current clause / plain comment / proposed language / priority). Lead every
summary with the recommendation and the 2-3 needle-movers, then the ranked findings. Plain language,
no AI tells; legal wording only inside quoted or proposed clauses. Worked example (the reference
build): `~/Documents/Claude/solum-ops/legal/Raintree/` — a Solum × Raintree customer agreement,
order form, aligned terms, and the `Raintree_OrderForm_Master_QA_Report.md`.

## Common mistakes

- Reviewing the Order Form but not the embedded Terms — the economics live in the Order Form; the
  risk lives in the Terms and the BAA.
- Trusting a "Notwithstanding" override instead of aligning the Terms to the deal.
- Reporting a plausible finding without re-reading the clause — verify before you flag.
- Relaying a run-rate, cap, or business-case number you did not recompute from the rates.
- Removing a willful-misconduct **cap exception** but leaving the willful-misconduct **indemnity
  trigger** (different clauses; know which one you are touching).
- Letting a cap-magnitude change (e.g., 1× → 3×) pass without stating who it now exposes and by how
  much — a higher cap is worse for whoever carries the larger risk (usually the vendor, on breach).
- Flagging the client's deliberate choices (no insurance, chosen cap, appendix business case) as
  defects.
