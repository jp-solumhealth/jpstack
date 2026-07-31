# HIPAA required elements, optional provisions, and citations

Map every BAA against this before reading a single commercial clause. The purpose is to
separate genuine compliance defects from commercial asks — the two get very different
treatment in the report and in the negotiation.

## The eleven required elements — 45 C.F.R. § 164.504(e)(2)

A BAA that contains all of these is **compliant**. Say so plainly and do not negotiate any
of them. Fighting a required element signals we do not know the regulation and costs
credibility on the asks that matter.

| § 164.504(e)(2) | Requirement | Typical clause caption |
|---|---|---|
| (i) | Establish permitted and required uses and disclosures of PHI | Permitted Use and Disclosures |
| (ii)(A) | BA will not use or disclose PHI other than as permitted or required by the contract or by law | Permitted Use / general covenant |
| (ii)(B) | BA will use appropriate safeguards, and comply with Subpart C of Part 164 for ePHI | Safeguards |
| (ii)(C) | BA will report uses/disclosures not provided for, and Breaches, to the covered entity | Reporting of Security Incident / Reporting of Breach |
| (ii)(D) | BA will ensure subcontractors agree to the same restrictions and conditions | Agents / Subcontractors |
| (ii)(E) | BA will make PHI available for individual access under § 164.524 | Access to Designated Record Set |
| (ii)(F) | BA will make PHI available for amendment under § 164.526 | Amendments to Designated Record Set |
| (ii)(G) | BA will make available the information required for an accounting under § 164.528 | Accounting of Disclosures |
| (ii)(H) | BA will make internal practices, books and records available **to the Secretary** | Access to Records |
| (ii)(I) | BA will return or destroy all PHI at termination where feasible | Return of PHI |
| (iii) | Covered entity may terminate the contract for a material breach by the BA | Termination for Cause |

**Note on (ii)(H).** The requirement runs to the *Secretary*, not to the customer. A general
customer audit right is a customer-imposed contractual ask, not a regulatory one. Label it
that way — it changes the negotiation.

**Note on (iii).** The regulation requires the covered entity to *have* a termination right.
It says nothing about who sets the cure period or whether the services agreement dies with
the BAA. Those are commercial and fully negotiable.

## Subcontractor BAAs

The required elements are the same. The governing provisions differ:

- **§ 164.502(e)(1)(ii)** — a business associate may disclose PHI to a subcontractor only
  with satisfactory assurances, in the form of a written agreement, that the subcontractor
  will appropriately safeguard the information.
- **§ 164.308(b)(2)** — the Security Rule counterpart for ePHI.
- **§ 164.314(a)** — the required implementation specifications for those contracts.
- **§ 160.103** — defines "business associate" to include a subcontractor that creates,
  receives, maintains or transmits PHI on behalf of a business associate.

The standard those provisions set is **"satisfactory assurances"** in writing. It is not
immediacy, not direct regulator cooperation, and not any specific notice window. When a
counterparty's flow-down clause cites these provisions and then demands more than they
require, point at the mismatch — the clause overshoots the standard it invokes.

**Direct liability.** Subcontractors have been directly liable for applicable HIPAA
violations since the 2013 Omnibus Rule (78 Fed. Reg. 5566). Never argue reduced exposure
from subcontractor status.

## Optional provisions worth asking for

None of these are required, so a form that omits them is not defective. All of them are
things we usually want, and all are ordinary asks.

| Provision | Citation | Why we want it |
|---|---|---|
| Right to **de-identify** PHI | § 164.502(d)(1), standard at § 164.514(b) | Without express permission, de-identification may itself exceed the permitted-use scope. Needed before any de-identified analytics or model work. |
| **Data aggregation** services | § 164.504(e)(2)(i)(B) | Required if we benchmark or aggregate across customers. |
| **Use and disclosure** for our own management and administration | § 164.504(e)(4)(i)(B) | Many forms permit *use* but not *disclosure*, which blocks sharing PHI with our own counsel or auditors. Disclosure requires either a legal requirement or written assurances of confidentiality and breach notification. |
| Right to **supplement** a breach notice | — | Forensics rarely resolve individual identification inside a short window. |
| **Unsuccessful Security Incident** carve-out | acknowledged in HHS Security Rule guidance | Without it, § 164.304 makes attempted access reportable. |

## Timing benchmarks

| Obligation | Regulatory outer limit | Common negotiated position |
|---|---|---|
| BA reports Breach to covered entity | **60 calendar days** from discovery — § 164.410(b) | 5 to 15 business days |
| Covered entity notifies individuals | 60 calendar days — § 164.404(b) | — |
| Notice to media (500+ in a state) | 60 calendar days — § 164.406 | — |
| Notice to Secretary | § 164.408 | — |
| Law enforcement delay permitted | § 164.412 | Keep it |

**Discovery standard.** § 164.410(a)(2) treats a breach as discovered on the first day it is
known, or by exercising reasonable diligence would have been known, to any person other than
the one committing it who is an employee, officer or agent of the business associate. A BAA
clause reproducing this **tracks the regulation** — it is not a defect and should not be
flagged as one. The negotiable part is the deadline attached to it, not the standard.

## Definitions that matter

| Term | Citation | Trap |
|---|---|---|
| Security Incident | § 164.304 | Includes **attempted** unauthorised access. If the BAA leaves it undefined, a catch-all "undefined terms take their HIPAA meaning" clause imports the attempts. This is the most consequential undefined term in any BAA. |
| Breach | § 164.402 | Distinct from Security Incident. Confirm the BAA distinguishes them; many collapse the two. |
| Unsecured PHI | § 164.402 | Ties to the HHS encryption/destruction guidance. |
| Designated Record Set | § 164.501 | Frequently used capitalised and never defined. Confirm we actually maintain one — for eligibility and benefits data we often do not. |
| PHI / ePHI | § 160.103 | Check the BAA limits these to information **we** create, receive, maintain or transmit. An unlimited definition sweeps in the customer's whole estate. |

## Other citations used in review

- § 164.308(a)(1)(ii)(A) — risk analysis.
- § 164.308(a)(1)(ii)(C) — workforce sanction policy. Already required; a BAA clause
  imposing it adds no burden.
- § 164.522 — restrictions and confidential communications. Not required elements.
- § 164.524, § 164.526, § 164.528 — individual access, amendment, accounting.
- HITECH Act and the 2013 Omnibus Rule — direct liability of business associates and
  subcontractors.

## Accuracy rules

- Never claim a provision violates HIPAA unless the basis is stated and holds.
- Distinguish four categories every time: **required by law**, **common market practice**,
  **customer-specific contractual ask**, **prudent risk management**.
- Do not invent citations. If unsure of a pinpoint, cite the section and describe the rule
  rather than guessing a subsection.
- Aggressive is not unlawful. Most of what is worth negotiating is perfectly legal.
