---
name: baa-review
description: >
  Use when a HIPAA Business Associate Agreement lands and needs vetting, redlining, or a
  signature decision — a BAA on the customer's paper, a subcontractor BAA, a downstream
  BAA from an RCM or clearinghouse, or a BAA exhibit attached to an MSA or order form.
  Triggers: "review this BAA", "can we sign this BAA", "BAA redlines", "the customer sent
  their BAA", "business associate agreement", "subcontractor BAA", "HIPAA agreement",
  "is this BAA ok", "what's wrong with this BAA", "breach notification is too short",
  "they want 24 hour breach notice", "uncapped indemnity in the BAA", "the BAA overrides
  our cap", "do we have to report every security incident", "BAA audit rights", "PHI
  deletion on termination", or any .docx/.pdf BAA dropped in before signing. Also use when
  the BAA gates revenue (pilot cannot start until it is executed).
---

# BAA Review — Legal Counsel

Review and negotiate a HIPAA Business Associate Agreement as counsel for our side.

**Core principle: a BAA is two documents wearing one cover.** Underneath is the regulatory
floor — the elements 45 C.F.R. § 164.504(e)(2) requires, which are not negotiable and
should never be fought. On top is a commercial overlay the counterparty's lawyers added —
liability, indemnity, reporting windows, audit rights, deletion duties — which is fully
negotiable and is where essentially all the risk lives.

**Separate the two before you say a word.** Most provider-side BAAs are HIPAA-perfect and
commercially brutal. Telling a counterparty their BAA is "non-compliant" when it satisfies
every required element destroys credibility for the asks that matter. Lead with "your form
is compliant and well drafted, here are four commercial points."

Quote operative language for every finding. Never review from a summary.

## Establish posture first (do not skip)

Five facts drive the entire review. Get them from the user or the documents. Never invent
them:

1. **Our role.** Business Associate (customer is a covered entity/provider) or
   **Subcontractor** (customer is itself a BA, e.g. an RCM or clearinghouse — 45 C.F.R.
   § 160.103). This picks the master template and changes who is directly liable.
2. **Whose paper.** Ours (use the master) or theirs (surgical redline; do not rewrite
   their form).
3. **The underlying Agreement.** Named, or a blank placeholder? A BAA whose "Agreement" is
   blank has **no ascertainable permitted-use scope** — every permitted use is anchored to
   it. This is a critical finding, not a typo.
4. **What the BAA gates.** If revenue cannot start until it is signed, speed has real
   value and the negotiation must be tiered accordingly.
5. **Contract value.** Needed to size exposure. Compute annualised revenue from the rates
   and volumes; label estimates as estimates.

## The two postures — get this right before anything else

The same document means different things depending on where we sit in the data chain.
Misreading this produces a review that is confidently wrong.

| | **Business Associate** | **Subcontractor** |
|---|---|---|
| Customer is | A covered entity — provider, clinic, health system | Itself a business associate — RCM, billing company, clearinghouse, another vendor |
| We are | BA to the covered entity | Subcontractor BA, one link further down |
| Chain | CE → us | CE → our customer → us |
| Governing | § 164.504(e), § 164.502(e)(1)(i) | § 164.502(e)(1)(ii), § 164.308(b)(2), § 164.314(a) |
| Our master | `Solum_Health_BAA_Master_*.docx` | `Solum_Health_Subcontractor_BAA_Master_*.docx` |

**Both are directly liable.** Since the 2013 Omnibus Rule a subcontractor is itself a
business associate with the same direct HIPAA exposure. "We are only a subcontractor" is
not a risk argument and must never be used as one.

### What changes when we are the Subcontractor

- **Terms must be no less protective than the upstream BAA.** Our customer is contractually
  obliged to push their own obligations down. This is the single most important question in
  a subcontractor BAA review: **is this term boilerplate, or is our customer bound to it by
  their own covered entity?** Ask directly. A 5-day notice window their CE imposed on them
  is not negotiable the way a 5-day window their lawyer invented is.
- **Ask to see the relevant upstream provisions.** Not the whole agreement — the reporting,
  audit, and liability clauses. If they will not show them, treat their "we cannot change
  this" as unverified and say so.
- **Flow-through indemnity is the norm.** Our customer is liable to their CE and will push
  the whole chain down to us. Cap it anyway; a cap does not stop the flow-through, it bounds
  it.
- **Their termination rights are often derivative.** If the upstream BAA dies, ours dies.
  Check whether termination is tied to an agreement we have never seen.
- **Reporting timelines compound.** Our window must leave our customer time to meet theirs.
  Ask what their upstream deadline is and work backwards, rather than negotiating in the
  abstract.

### Our own downstream chain

Whichever posture we are in, our infrastructure and model providers are *our* subcontractors
and need their own BAAs under § 164.502(e)(1)(ii) and § 164.308(b)(2). Two consequences that
show up in nearly every review:

- Flow-down language must be obtainable on **standard provider paper**. Terms like
  "immediately" or "any potential breach", or direct cooperation with our customer and
  regulators, are not available from hyperscalers and create an uncurable day-one breach.
- Where subprocessors operate on a **no-data-retention** basis for PHI, say so in the
  redline. It is a strong, verifiable answer to flow-down demands and usually ends the point.

## Phase 1 — Regulatory floor (what NOT to negotiate)

Map the document against `references/hipaa-required-elements.md` before reading anything
else. If all eleven elements of § 164.504(e)(2) are present, **say so up front and mean
it.** Also identify the *optional* provisions the form omits that we actually want:
de-identification (§ 164.502(d)(1)), data aggregation (§ 164.504(e)(2)(i)(B)), and
disclosure for our own management and administration (§ 164.504(e)(4)(i)(B)).

Absence of a required element is a genuine compliance defect. Presence of an aggressive
term is not. Keep the two categories rigidly separate in the report.

## Phase 2 — The commercial overlay (where the risk is)

Work `references/clause-positions.md`, which carries the recurring aggressive patterns,
the market position on each, and proposed wording. The seven that matter most:

1. **A clause captioned "Limitation of Liability" that removes limitations.** Reads
   "the indemnity shall not be subject to any limitation of liability set forth in the
   Agreement." Combined with an "Inconsistency" clause giving the BAA priority, it voids
   the MSA cap *before it is drafted*, and often the consequential-damages waiver with it.
2. **No-fault triggers.** "Acts or omissions" rather than negligence or breach. Check
   every cost-shifting clause for this phrasing.
3. **Indemnity with no third-party limiter.** "Hold harmless against any and all claims,
   losses, liabilities and costs" with no third-party requirement is an uncapped *direct*
   damages clause wearing an indemnity caption.
4. **Cost-shifting hidden outside the Indemnification section.** Mitigation clauses often
   carry an independent "shall pay all costs of investigation and notification" sentence.
   **Fixing the indemnity alone does not reach it.** Any cap must name every such clause.
5. **Undefined "Security Incident."** Falls back to § 164.304, which covers *attempted*
   access — making every port scan reportable. The unsuccessful-incident carve-out is the
   single highest-value, least-contested fix in any BAA.
6. **Reporting windows far below § 164.410(b)'s sixty days**, with no right to supplement
   as forensics develop.
7. **Flow-down terms no hyperscaler will accept** ("immediately", "potential", direct
   cooperation with the customer and regulators) — an uncurable day-one breach.

For each: state whether it is required by law, common market practice, a customer-specific
contractual ask, or prudent risk management. Give the basis. Never assert "market
standard" without one.

## Phase 3 — Size the exposure

Put the uncapped exposure next to the annual contract value and show the ratio. A
six-figure notification event against an $18K/year account is the whole argument, and it
lands better as arithmetic than as adjectives.

Cap magnitude is the client's call, not ours. Surface the inputs: **the cap should sit at
or below confirmed cyber-liability limits**, because the excess is uninsured. If those
limits are unknown, say so and leave the figure blank. Trailing 12 months of fees is the
common vendor position; 24 is the common concession.

## Phase 4 — Deliver in tiers

Split findings into **must-fix** (unbounded exposure or unperformable obligation) and
**should-fix** (everything else). Signal early that tier 2 is tradeable — it buys speed on
tier 1, which matters when the BAA gates revenue.

Open with any scrivener's errors. They are free, plainly correct, and prove the document
was read closely before the liability asks arrive. Provider forms reliably contain them.

## Phase 5 — Redline delivery (never skip the approval gate)

**REQUIRED:** follow `references/redline-mechanics.md` for the build and verification
steps. The gates:

**Gate 1 — review only.** Findings and recommendation. Do not modify the document,
generate a redline, or state that any recommendation is accepted. Stop and ask which
recommendations are approved.

**Gate 2 — propose wording in two editable files**, keyed by the same edit IDs:
`*_Replacements.md` (clause caption, page, original text, proposed wording) and
`*_Comments.md` (the margin comment for each edit). Both are counterparty-facing — the
clause language becomes the contract and the comments are read by their counsel. The
client edits and hands back. **Only then build the DOCX.**

**Gate 3 — build.** Tracked changes under a named author, one anchored comment per edit,
plus a clean accepted copy.

**Scope discipline.** Apply only the points the client actually raised. If a linked edit is
genuinely needed to make one of their instructions work — e.g. a cap that must name the
Mitigation clause to reach it — surface it as its own numbered proposal. Never slip it in.
Say plainly what you added and why.

**Comment voice.** Same standard as client emails: plain words, short sentences, no
dashes, no buzzwords. Reference standard market terms where it helps the ask land.

## Red flags — stop and confirm

- A "Limitation of Liability" clause that disapplies caps instead of setting one.
- Any cost-shifting clause outside the Indemnification section that a cap would not reach.
- "Acts or omissions" where the trigger should be negligence or breach.
- Indemnity reaching the counterparty's own first-party losses.
- "Security Incident" undefined, or reporting with no unsuccessful-attempt carve-out.
- Subcontractor obligations that cannot be obtained from AWS, Twilio or equivalent.
- BAA termination that automatically terminates the services agreement.
- A cure period set unilaterally by the counterparty, with no floor.
- "Retain no copies" on termination with no backup or legal-retention carve-out.
- Unqualified perpetual survival of every obligation, including an uncapped indemnity.
- Customer policies incorporated by reference that have never been provided.
- An absolute, continuing warranty of Privacy Rule and Security Rule compliance.
- A blank `[INSERT NAME OF AGREEMENT]` — permitted-use scope is undefined.
- The counterparty defined as an entity "and its managed practices" with no schedule.

## Common mistakes

- **Calling an aggressive BAA non-compliant.** Check § 164.504(e)(2) first. Most provider
  forms satisfy every element; the risk is commercial, and saying otherwise burns credibility.
- **Fixing the indemnity and declaring the cap solved** while a Mitigation cost-shift sits
  outside it. Trace every clause that moves money.
- **Flagging the imputed-knowledge discovery standard as a defect.** "Known or reasonably
  should have been known to any employee or agent" *tracks* § 164.410(a)(2). The problem is
  the deadline attached to it, not the standard.
- **Volunteering obligations the form never asked for** — cyber insurance limits, a
  security-controls schedule, an SLA. Absence is favourable. Do not fill it.
- **Asserting "market standard" with no basis.** State the basis or drop the claim.
- **Naming a cap figure without the client's insurance limits.** Leave it blank and say why.
- **Writing proposed clause wording straight into the DOCX.** The client cannot edit their
  own contract language once it is tracked changes. Two files first, always.
- **Reviewing the BAA without the agreement it sits on.** An "Inconsistency" clause
  subordinates that agreement in every instance; the liability picture cannot be closed
  without reading it. Ask for it.

## Reference files

| File | Contents |
|---|---|
| `references/hipaa-required-elements.md` | The § 164.504(e)(2) map, optional provisions worth asking for, and the citation set |
| `references/clause-positions.md` | Recurring aggressive clauses, market position, and proposed wording for each |
| `references/redline-mechanics.md` | Tracked-changes and comment build steps, mandatory verification, toolchain constraints |

Worked example: `~/Documents/Claude/solum-ops/legal/HHF-BAA/` — a provider-paper BAA
reviewed, tiered, redlined with anchored comments, and packaged with a page-referenced
negotiation email. Masters live in `~/Documents/Claude/solum-ops/legal/`; see the
`subcontractor-baa` memory for which template applies.
