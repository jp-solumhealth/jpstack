# Liability Stack & Risk Allocation

The liability section is where a commercial contract is won or lost for our side. Reconstruct the
whole stack from the operative clauses, confirm it is internally consistent, and rank every gap.

## The five components of a liability stack

Read all of these together — a defect is almost always an inconsistency *between* them:

1. **Consequential-damages waiver** (usually mutual). Excludes indirect, incidental, special,
   exemplary, punitive, consequential damages, and lost profits/revenue/goodwill/data/business.
   "Even if advised of the possibility."
2. **Direct-liability cap.** The ceiling on everything not carved out. Common bases:
   - 1× trailing-12-month fees (classic SaaS; *low and volatile early in a ramp* — after Month 2 of
     a ramp it may be near zero).
   - A multiple of **annualized contract value** (e.g., 3× the annual commitment). More stable, and
     for a mutual cap it raises exposure for whoever carries the larger risk.
   - Before full scale is reached, annualize off the **most recent full invoiced month × 12**, then
     apply the multiple. This avoids the near-zero early cap.
   - With or without a **dollar floor** (e.g., never less than $1,000,000). A floor keeps an early
     cap meaningful but raises early exposure for both sides — state the trade.
3. **Indemnity treatment.** Indemnities are usually carved out of the direct cap, then either left
   uncapped or **re-capped** at a higher number (a "super-cap", e.g., 3× annualized). If carved out
   and not re-capped, they are uncapped — confirm that is intended.
4. **Carve-outs / the uncapped set.** What sits outside all caps. Keep this minimal and defensible:
   typically **the customer's payment obligation** always, and often fraud and willful misconduct.
   Note: some deals deliberately cap *everything* and rely on public policy to handle fraud silently
   (a court will not enforce a cap on a party's own deliberate fraud regardless of the drafting).
5. **Precedence override.** A clause ensuring a BAA or exhibit cannot silently displace the cap:
   "the BAA controls PHI handling, but Section 9 governs each party's aggregate liability; this
   Section controls over any conflict, integration, or entire-agreement clause in the BAA."

## Where security-incident / data-breach / PHI liability sits

The single most-negotiated point in a healthcare SaaS deal. Decide and state it explicitly:

- **Inside the general cap** (vendor-favorable): "the cap in this Section applies to all liability of
  every kind, including any security incident, data breach, or breach of confidentiality (including
  unauthorized access to or disclosure of PHI)."
- **A separate super-cap** (customer-favorable): breach liability capped at a higher multiple.
- **Uncapped** (rare, dangerous for a vendor): avoid unless forced.

If the customer's downstream book is large (they serve providers/patients), expect their GC to
demand a breach super-cap or a privacy/security indemnity. That is the deal's most contested term —
know the fallback before the call.

## Coherence checks — run every one

- **No double-treatment.** A single claim must not be both capped and uncapped. The classic bug: an
  indemnity **for** willful misconduct (Section 8 trigger) that is simultaneously inside a "3× cap on
  Section 8 indemnities" and named in an "uncapped: willful misconduct" carve-out. Resolve: either
  the cap excepts willful-misconduct-driven indemnities, or the carve-out excludes them.
- **Consequential-damages preservation.** If the consequential-damages exclusion (§9.1) is what also
  exempts indemnities from being barred, a "Notwithstanding §9.3(a)" that re-caps indemnities can
  accidentally pull them back under §9.1. Add: "Section 9.1 continues not to apply to Section 8
  indemnities."
- **The override attaches to the right words.** "Notwithstanding Sections 9.3(a), 9.3(b), and the
  last sentence of Section 9.3" only works if those exact subsections exist and say what you think.
  Re-read them after any edit to §9.
- **Gross negligence.** Capping (not exculpating) gross negligence between sophisticated parties is
  generally defensible; model exposure as if it might not hold. Do not advertise it as an exception
  if the client wants a clean universal cap.
- **Warranty remedy is not hollow.** "Sole remedy = re-performance, else pro-rata refund of pre-paid
  fees" is empty when billing is monthly-in-arrears (pre-paid ≈ 0). Expect the customer to carve the
  security/safeguards warranty out of the exclusive remedy.

## Indemnity scope (IP and general)

- **IP indemnity** should exclude: claims from customer data, from combination with non-vendor
  systems, from modifications not made by the vendor, and from use outside the documentation. Pair
  with an IP-remedies clause (procure / modify / replace / refund) as the **sole and exclusive**
  IP remedy.
- **Customer indemnity** in a healthcare deal should reach the customer's and its clients'
  professional/medical services, billing/coding, and payer/government inquiries — **except to the
  extent the claim results from the vendor's own material breach** (the zero-cost carve that
  pre-empts the obvious redline and removes the indefensible "covers our own errors" reading).

## Risk ranking

Rank every finding and lead with the needle-movers:

- **Critical** — a defect that makes a clause unenforceable, self-contradictory, or exposes the
  client to uncapped/unintended liability. Blocks signature.
- **High** — a real gap a sophisticated GC will catch and that materially shifts risk or economics.
  Negotiate before signing.
- **Medium** — a genuine issue reconciled only by careful reading; fix to avoid a redline.
- **Low** — cosmetic, cross-reference, or defined-term hygiene.

For each: quote the text, give a concrete failure scenario (inputs → wrong outcome), and a one-line
fix. Separate **drafting defects** from **execution steps** (attaching the BAA, verifying an entity
name) in the recommendation.

## Predict the counterparty's redlines (adversarial pass)

Put on opposing counsel's hat and rank what they will send, most-likely first. Typical for a
vendor-favorable healthcare SaaS paper:

1. A data-breach super-cap and/or an ordinary-negligence privacy/security indemnity.
2. SLA credits once the commitment is firm.
3. Insurance requirements (cyber / tech E&O) — if the client omitted insurance deliberately, have
   COI/limits ready as a response, not contract text.
4. Paid transition assistance at exit.
5. A longer invoice-dispute window (15 → 30 days).
6. Striking a payment condition on the license grant.
7. A competing-products clarifier for the customer's own independently developed features.

For each, decide the fallback **before** the negotiation, and identify the **zero-cost pre-emptions**
(the material-breach carve on the customer indemnity; a defined "business hours"; a for-cause carve
on surviving minimums) that buy credibility without giving up substance.
