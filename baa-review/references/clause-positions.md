# Recurring BAA clauses — pattern, position, proposed wording

Each entry: what the clause looks like, why it bites, the position to take with its basis,
and wording to propose. Adapt the wording; do not paste it blind. Every "market" claim below
carries its basis — never assert market practice without one.

Priority key: **T1** blocks signature. **T2** should be fixed, tradeable for speed on T1.

---

## 1. The "Limitation of Liability" clause that removes limitations — T1

**Pattern.** "The indemnification provisions set forth herein shall in no event be subject to
any limitation of liability or damages set forth in the Agreement, and no express or implied
agreement or arrangement between the Parties shall in any way reduce or limit Business
Associate's liability thereof."

**Why it bites.** It does the opposite of its caption. Combined with an Inconsistency clause
giving the BAA priority "in every instance," it voids the services-agreement cap before that
agreement is even drafted. The words "no express or implied agreement" are broad enough to
reach the consequential-damages waiver too, so exposure is not merely uncapped but may include
lost profits.

**Position.** Non-negotiable. Basis: no vendor can carry unlimited liability against a bounded
revenue stream, and an uninsurable vendor is a continuity risk to the customer. Offer a higher
sub-limit for PHI claims — that concedes their real concern while restoring a ceiling.

**Proposed wording**

> Except in the case of a Party's gross negligence or willful misconduct, each Party's total
> aggregate liability arising out of or relating to this BAA, whether in contract, tort
> (including negligence), strict liability or otherwise, shall not exceed the total fees paid
> and payable by Covered Entity to Business Associate under the Agreement during the twelve
> (12) months immediately preceding the event giving rise to the claim. Neither Party shall be
> liable for any indirect, incidental, special, consequential, exemplary or punitive damages,
> or for lost profits or lost revenue, arising out of or relating to this BAA. This Section
> applies to all obligations under this BAA, including without limitation the Mitigation,
> Indemnification and Patient Notifications Indemnification provisions.

**The final sentence is load-bearing.** Without it the cap does not reach cost-shifting
clauses elsewhere in the document. Name every such clause explicitly.

**Fallback.** 24 months of trailing fees, or a fixed sub-limit for PHI claims. Set the figure
at or below confirmed cyber-liability limits — the excess is uninsured. If limits are unknown,
leave it blank and say why.

---

## 2. One-way, no-fault indemnity — T1

**Pattern.** "Business Associate agrees to indemnify, defend and hold harmless Covered Entity
and its affiliates... from and against any and all claims, losses, liabilities, costs and any
other expenses resulting from, or relating to, the acts or omissions of Business Associate."

**Why it bites.** Four defects stacked. It runs one way. "Acts or omissions" is strict
liability, not fault. "Relating to" sweeps in indirect claims. And with no third-party-claim
limiter, "hold harmless against any and all claims, losses, liabilities and costs" reads as
covering the customer's own first-party losses — an uncapped direct-damages clause wearing an
indemnity caption. There is usually no notice, defence-control or consent-to-settle machinery
either.

**Position.** Non-negotiable in substance, flexible in drafting. Mutuality is the easy sell:
the customer's own clause elsewhere covenants not to request impermissible uses, and as drafted
that covenant has no remedy attached.

**Proposed wording**

> Each Party (the "Indemnifying Party") agrees to indemnify, defend and hold harmless the other
> Party and its officers, directors, employees and agents from and against any and all
> third-party claims, losses, liabilities, costs and expenses (including reasonable attorneys'
> fees) to the extent resulting from the Indemnifying Party's negligent acts or omissions,
> willful misconduct, or breach of this BAA. The indemnified Party shall provide prompt written
> notice of any such claim and reasonable cooperation in its defense, and the Indemnifying Party
> shall have the right to control the defense and settlement of the claim; provided that no
> settlement imposing any liability or non-monetary obligation on the indemnified Party shall be
> entered into without that Party's prior written consent, not to be unreasonably withheld.

---

## 3. Cost-shifting hidden outside the Indemnification section — T1

**Pattern.** Buried in a clause captioned *Mitigation*: "In the event a security incident or
Breach has occurred as a result of the acts or omissions of Business Associate... Business
Associate shall pay for all the costs related to the resulting investigation, mitigation, and
notice/reporting."

**Why it bites.** It is an independent, uncapped cost-shift on a no-fault trigger, sitting
where nobody looks for financial terms. **Repairing the indemnity does not touch it.** Forms
frequently carry the same notification costs in three places — Mitigation, the general
indemnity, and a separate patient-notification indemnity.

**Position.** Non-negotiable that it sits inside the cap. The obligation itself is reasonable
and need not be resisted. Frame the change as consolidating overlapping clauses.

**Proposed wording**

> ...in each case subject to the limitation of liability set forth in this BAA and without
> duplication of any amounts recovered under the Indemnification or Patient Notifications
> Indemnification provisions.

**Review action.** Grep the whole document for "shall pay", "costs", "expenses" and
"reimburse". Every hit that moves money must be named in the cap.

---

## 4. Undefined "Security Incident" — T1, and the cheapest win in the document

**Pattern.** The BAA requires reporting of "any security incident" but never defines it, while
a general clause routes undefined terms to their HIPAA meanings.

**Why it bites.** § 164.304 defines security incident to include **attempted** unauthorised
access. Read literally, every port scan, blocked probe and failed login becomes individually
reportable inside the contractual window.

**Position.** The carve-out is non-negotiable; timing is tradeable. Basis: HHS guidance
accompanying the Security Rule has long acknowledged that routine unsuccessful attempts need
not be individually reported and that a contract may provide for aggregate or no reporting of
them. It also serves the customer — real notices stop being buried.

**Proposed wording** (definitions section)

> "Security Incident" shall have the same meaning as the term "security incident" in 45 CFR
> § 164.304, provided that Security Incident shall exclude Unsuccessful Security Incidents.
> "Unsuccessful Security Incidents" means pings and other broadcast attacks on a firewall, port
> scans, unsuccessful log-on attempts, denial of service attacks, packet sniffing, and any
> combination of the foregoing, in each case that does not result in unauthorized access to, or
> acquisition, use or disclosure of, PHI. The Parties acknowledge that Unsuccessful Security
> Incidents occur routinely and require no individual report, and this BAA constitutes notice
> of them.

Then point the reporting clause at the defined term and add: *For the avoidance of doubt,
Unsuccessful Security Incidents are excluded from this reporting obligation.*

**Tactic.** Ask for the carve-out **without** asking for more time. Conceding the counterparty's
window while fixing the definition is a much easier trade and usually lands in one round.

---

## 5. Reporting windows — T1 or T2 depending on severity

**Pattern.** 24 hours, 2 days, or 3 business days, with full individual identification demanded
up front and no right to supplement.

**Why it bites.** § 164.410(b) allows 60 calendar days. Anything shorter is pure commercial
overlay. Forensics rarely identify affected individuals inside a few days, so the clause is
often unperformable as written — and a missed notice is a breach that feeds the indemnity and
the termination right.

**Position.** Open at 10 business days; 5 is an acceptable landing. The **right to supplement**
matters more than the number and is rarely contested.

**Proposed wording**

> ...without unreasonable delay and in no event later than ten (10) business days following
> Discovery. Any notice shall include, to the extent then known, [required content]. Business
> Associate shall supplement its notice with additional information as it becomes available.

**Subcontractor context.** Ask what the upstream deadline is and work backwards. A short window
driven by their covered entity is a different conversation from one their lawyer invented.

**Do not flag** the imputed-knowledge discovery standard as a defect — it tracks § 164.410(a)(2).

---

## 6. Subcontractor flow-down that cannot be obtained — T2, but uncurable

**Pattern.** "Business Associate shall require its subcontractors to notify it immediately of
any potential breach... and to cooperate with Business Associate and Covered Entity in all
investigations... and provide any and all information concerning such breach to Covered Entity
and/or Federal or State regulatory or investigative agency."

**Why it bites.** "Immediately" and "potential" are unbounded, and direct cooperation with a
customer's customer and with regulators is not available on hyperscaler paper. If the terms
cannot be obtained we are in continuous, uncurable breach from day one.

**Position.** Align to the standard the clause already cites. Note that § 164.502(e)(1)(ii) and
§ 164.308(b)(2) require **satisfactory assurances**, not immediacy — the sentence overshoots
its own citation.

**Proposed wording**

> Business Associate's subcontractors operate on a no-data-retention basis with respect to PHI.
> Business Associate shall require its subcontractors and/or agents to report Breaches of
> Unsecured PHI to Business Associate on terms no less protective than those set forth in this
> BAA, and Business Associate shall notify Covered Entity of any Breach of Unsecured PHI
> affecting Covered Entity's PHI in accordance with this BAA. Business Associate shall
> reasonably cooperate with Covered Entity in connection with any investigation relating to such
> a Breach. Nothing in this BAA shall require Business Associate to amend, renegotiate or execute
> any additional agreement with any subcontractor beyond the business associate agreement
> required by the HIPAA Rules.

**Keep the written flow-down sentence unchanged.** Conceding it visibly is what makes the rest
of the ask land.

---

## 7. Audit and access to records — T2

**Pattern.** Access "in a time and manner designated by Covered Entity" to "records, books,
**agreements**, policies and procedures." Often duplicated, with two clauses under the same
caption saying different things.

**Why it bites.** Unbounded and customer-scheduled. "Agreements" would require producing our
contracts with other customers, which we cannot lawfully do. No frequency cap, confidentiality
protection, cost allocation or third-party-report substitution.

**Position.** Keep the Secretary-access sentence untouched — that is § 164.504(e)(2)(ii)(H) and
is required. Put the customer's own review right on ordinary terms.

**Proposed wording**

> Business Associate agrees, upon at least thirty (30) days' prior written notice and upon terms
> mutually agreed by the Parties, to make available during normal business hours at Business
> Associate's offices all records, books, policies and procedures relating to the use or
> disclosure of Covered Entity's PHI, for purposes of enabling Covered Entity to determine
> Business Associate's compliance with the terms of this BAA. Any such review shall be conducted
> by Covered Entity or by an independent auditor mutually agreed by the Parties in writing, and
> shall not be conducted by any other third party without Business Associate's prior written
> consent. Any such review shall be subject to Business Associate's reasonable confidentiality
> and security requirements and shall exclude information relating to Business Associate's other
> customers and Business Associate's proprietary or trade secret information.

Add a current third-party audit report as an alternative means of satisfying a request where one
exists. Do not claim a certification we do not hold.

---

## 8. Termination — T2

**Pattern.** Cure "within the time period specified by Covered Entity"; termination of the BAA
also terminates the services agreement; no reciprocal right for us.

**Position.** Thirty-day cure floor, mutual, and decoupled. Frame mutuality around their own
covenant not to request impermissible uses — as drafted it has no remedy.

**Proposed wording**

> Upon either Party's knowledge of a material breach of this BAA by the other Party, the
> non-breaching Party shall provide written notice describing the breach and a period of not less
> than thirty (30) days to cure... Termination of this BAA shall not automatically terminate the
> Agreement, which shall terminate only in accordance with its own terms.

---

## 9. Return or destruction of PHI — T2

**Pattern.** "Shall retain no copies" with no backup or legal-retention carve-out, no timeline,
no export format.

**Why it bites.** Literal compliance is usually impossible where rolling or immutable backups
exist. The infeasibility exception helps but requires asserting infeasibility rather than having
it agreed. Certifying destruction must be truthful.

**Position.** The continuing-protection formulation is what makes this acceptable to a
counterparty: the data stays protected, it is simply not deleted on demand.

**Proposed wording**

> Notwithstanding the foregoing, Business Associate may retain PHI (i) contained in routine
> backup, archival or disaster-recovery media created in the ordinary course of business, until
> such media are overwritten or expire in accordance with Business Associate's standard retention
> cycle, and (ii) to the extent required to comply with applicable law or professional
> record-retention obligations. Business Associate shall not use or disclose any PHI so retained
> for any purpose other than that which necessitated its retention, and the protections of this
> BAA shall continue to apply for so long as it is retained.

**Confirm backup architecture with Engineering before accepting any deletion clause.**

---

## 10. Absolute compliance warranty — T2

**Pattern.** "Business Associate represents, warrants and covenants that it is, and shall
continue to be, in compliance with the Privacy Rule and the Security Rule."

**Why it bites.** Unqualified by materiality, reasonableness or knowledge. Any technical
non-conformity becomes a warranty breach feeding the indemnity and the termination right.

**Proposed wording**

> Business Associate covenants that it shall maintain a compliance program reasonably designed to
> comply with the Privacy Rule and the Security Rule to the extent applicable to Business
> Associate, and shall comply with such rules in all material respects.

---

## 11. Permitted use anchored to a blank Agreement — T1

**Pattern.** `[INSERT NAME OF AGREEMENT]` in the recital, with the permitted-use clause limiting
use to services "specified in the Agreement."

**Why it bites.** The lawful scope of PHI processing is indeterminate at signature. Worse, if the
blank names only a pilot, the BAA may not attach to the MSA signed later, leaving production
volume uncovered.

**Proposed wording**

> WHEREAS, Covered Entity has entered into that certain [Pilot Agreement] dated [____], together
> with any master services agreement, order form, statement of work or other successor or
> superseding agreement between the Parties for the same or substantially similar services
> (collectively, the "Agreement"), with Business Associate; and

Pair with a permitted-use clause covering everything agreed under those terms, so AI-assisted
processing, subcontracted infrastructure and portal automation are unambiguously in scope.

---

## 12. De-identified data — T2

**Pattern.** "Business Associate may not use, disclose, sell, or otherwise commercialize
deidentified PHI for purposes unrelated to the Services." Often no right to de-identify at all.

**Why it bites.** Cross-customer model or service improvement is arguably "unrelated." And
without an express right under § 164.502(d)(1), de-identification may itself exceed permitted use.

**Position.** Concede the no-sale limit explicitly and volunteer the no-PHI-for-training covenant.
Volunteering both is what makes the carve-in credible.

**Proposed wording**

> Business Associate may de-identify PHI in accordance with 45 C.F.R. § 164.514(b), and may use
> and disclose such de-identified data to operate, evaluate, maintain and improve its services.
> Business Associate shall not use Protected Health Information to train or improve any
> general-purpose artificial intelligence or machine learning model, and shall not sell or
> otherwise commercialize Covered Entity's de-identified data, or disclose it in any form that
> identifies Covered Entity or any Individual.

---

## 13. Smaller recurring items — T2

| Clause | Problem | Ask |
|---|---|---|
| Survival | "All rights and obligations survive" — perpetual uncapped indemnity, no end state | Enumerate surviving clauses; limit indemnity survival to pre-termination acts |
| Regulatory reports | Our own filings need customer pre-approval | Narrow to notices made *on their behalf*; preserve our independent legal obligations |
| Customer policies | Minimum-necessary policies incorporated by reference, never provided | Limit to policies provided in writing, with a period to implement changes |
| Counterparty definition | "and its managed practices" — open-ended indemnified group | Schedule the entities; additions by mutual agreement |
| Oral notice | Effective on the call, written confirmation days later | Delete, or ineffective until written confirmation |
| Cure clause | No timeframe, no written-notice requirement | Cross-reference the termination cure period |
| Individual rights | "Time and manner designated by Covered Entity"; not limited to records we hold | Limit to PHI in our possession in a DRS we maintain; add a response period |

---

## What to concede early, and what never to volunteer

**Concede visibly and early** — it buys speed on T1: audit cadence and location, the written
flow-down sentence, most drafting cleanup, governing law where it already suits us, reporting
timing once the Security Incident carve-out is secured.

**Never volunteer** — none of these are usually asked for, and each is a new obligation:
cyber-insurance limits, a security-controls schedule, certifications we do not hold, SLAs or
uptime commitments, data-localisation commitments.

**Always open with the scrivener's errors.** Provider forms reliably contain them — a
self-referential amendment clause, "no less than X days" where they mean "no later than", a
missing defined term. They cost nothing, they are plainly correct, and they establish that the
document was read closely before the liability asks arrive.
