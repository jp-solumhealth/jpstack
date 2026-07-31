# Multi-Role Stakeholder Review & Scorecard

A full QA reviews the contract independently from each seat that will read it before signature. Run
the ten roles as **parallel subagent benches** over a flattened text dump of the document, grouped
into 2-3 benches to keep them independent, then reconcile. Each bench returns findings classified
Critical / High / Medium / Low with quoted text and a one-line fix, plus its category scores.

**Tell every bench the deliberate choices** (e.g., no insurance clause, the chosen cap structure,
business case as an appendix, sentence-case disclaimers) so it does not flag them as defects. And
require **adversarial verification**: a finding that does not survive a re-read of the actual clause
is a false positive — drop it and say so.

## The ten roles

### Legal bench

1. **Head of Legal (our side).** Legal consistency, enforceability, governing law, defined terms,
   cross-references, internal conflicts, liability allocation, IP, confidentiality, HIPAA, AI
   provisions, indemnification, termination, payment protections. *Would I approve this for
   signature? Is our side protected?*
2. **Opposing counsel (their GC).** Read as the other side: ambiguity, aggressive provisions, hidden
   obligations, unreasonable risk, unclear definitions, commercial imbalance, unnecessary
   complexity. *Predict the redlines ranked by likelihood; identify the wording changes we could
   make now that pre-empt them without giving up substance.*
3. **Security Officer.** Every security clause matches the published Trust Center; nothing invented
   (no SOC 2 / audit-frequency / response-time commitments beyond it). Flag any residual overpromise.
4. **HIPAA Officer.** BA/Subcontractor architecture, PHI handling, minimum-necessary and breach
   notification living in the BAA, subprocessor flow-down, de-identification granted in the BAA,
   consistency with a Subcontractor BAA. *Does anything here water down the BAA?*

### Executive bench

5. **CEO.** Long-term growth, accidental overpromise, delivery risk, custom-development or roadmap
   commitments, product-evolution restrictions, pricing limitations, scalability.
6. **CFO.** Revenue protection, billing, renewals, payment timing, late fees, implementation
   recovery, out-of-scope monetization, pricing flexibility (escalator? renewal pricing?),
   **termination exposure quantified** (worst-case and best-case collected revenue on every exit
   path), revenue leakage, cash-flow. *What single change most protects recurring revenue without
   looking one-sided?* (Usually a CPI-capped renewal escalator.)
7. **COO / Operations.** Can we consistently deliver every SLA/target? Impossible SLAs, support and
   escalation promises, implementation assumptions, customer and payer dependencies, manual-review
   requirements. Are customer-dependency reliefs stated strongly enough to excuse us when the
   customer is late? Is "business hours" defined?
8. **VP Engineering.** API/integration language, product and development obligations, custom-endpoint
   obligations, roadmap commitments, technical feasibility. *Are we ever obligated to build
   customer-specific functionality without a separate signed SOW? Any delivery-date commitment?*

### Market / format bench

9. **Enterprise Procurement.** Ease of negotiation, commercial clarity, readability, organization,
   pricing transparency, support, renewals, appendices. *Can procurement extract price, term, exit,
   minimums, and scope in under five minutes? What's missing (a plain ACV line, an order-of-documents
   list, defined renewal pricing)?*
10. **Enterprise Customer Success.** Where could a customer reasonably **misunderstand** support,
    implementation, professional services, scope, response/turnaround times, or the exit-cost
    mechanics? Quote each ambiguity and give clearer wording. Test the "without penalty" exit that
    actually costs accrued minimums; "near real-time"; "complete request"; the go/no-go review;
    minimum-vs-usage interplay.

Add a **plain-language editor** and a **commercial-benchmark** pass to the market bench (worst
run-on sentences with tightened versions; gaps vs current enterprise SaaS market paper — renewal
mechanics, support model, transition assistance — respecting the client's deliberate omissions).

## Scorecard (1-10 each)

Legal Quality · Commercial Quality · Negotiation Readiness · Formatting · Readability · Operational
Feasibility · Security · HIPAA · Governing-Law Compliance · Executive Friendliness · Procurement
Friendliness · **Overall Contract Readiness**.

State the residual deductions (e.g., a deliberately contested cap posture, a lean support model, an
enforceability caveat) so the score is honest.

## Final recommendation

Choose one and justify it in two lines:

- **APPROVED** — ready to send as-is.
- **APPROVED WITH MINOR CHANGES** — only execution items or trivial edits remain; name them.
- **APPROVED WITH MAJOR REVISIONS** — real drafting defects must be fixed first; list them.
- **DO NOT SEND** — structural problems; explain.

Separate drafting defects (fix in the document) from execution steps (attach the BAA, verify the
entity name, complete factual verifications). The predictable negotiation should land on the terms
the client chose to defend, not on drafting defects.
