# Florida lien waivers — ch. 713

Reference for the waiver side of a construction draw. Florida-specific. Not legal advice;
the statutory forms should be confirmed against the current text of ch. 713 before a set
is signed, and counsel should see anything unusual.

## The four forms

Florida Statutes **§713.20** prescribes the forms. Two axes, so four documents:

|  | **Conditional** | **Unconditional** |
|---|---|---|
| **Progress payment** | Effective only when the cheque clears. Safe for the lienor. | Effective on signature, paid or not. |
| **Final payment** | Same, for the last payment. | Releases everything. |

**§713.20(2): a waiver that departs from the statutory form is unenforceable** in the ways
that matter. Do not improve the drafting of the operative language. Additions belong in the
exceptions paragraph, which the statute contemplates.

## The central conflict, and how to resolve it

Construction loan agreements almost always require **unconditional** partial waivers as a
condition precedent to funding a draw. The lender wants no lien risk before it wires.

A lienor should never sign an unconditional waiver for money it has not received. That is
not a negotiating position, it is the whole point of the instrument: the signature
extinguishes the lien whether or not the cheque arrives.

The sequence that satisfies both:

1. Contractor signs **conditional** waivers covering the work in the draw.
2. Those go to the lender with the draw request.
3. Lender funds; borrower pays the contractor.
4. Contractor swaps them for **unconditional** waivers covering the same work.
5. Unconditional set goes into the file for the *next* draw's condition precedent.

If the lender will not accept conditional waivers at step 2, the borrower is being asked to
have its contractor take unsecured credit risk on the lender's funding. Say so plainly and
ask for the swap mechanic in writing.

**Never generate an unconditional waiver for an amount the payment ledger shows as
outstanding.** Check the payment tracker before generating, every time. `draw_calc.py
waivers` prints the exposure; `build_waivers.js --exclude-unpaid` cuts the amount and adds a
visible deduction line to the appendix so the schedule still foots.

## Partial waivers: the exceptions paragraph does the work

A waiver naming a date releases everything through that date unless it says otherwise. On a
progress draw covering some activities and part of another, the exceptions paragraph must
name, explicitly:

- which activities are covered in full;
- which activity is covered only to the extent completed, and through what date;
- the balance of that activity, and every later activity, as **not** covered;
- change order work, retainage, and anything furnished after the date, as not covered;
- that it binds the signing lienor only, not its subcontractors or suppliers.

Attach an itemised appendix and incorporate it by reference. A number with no schedule
behind it invites an argument about what was released.

**Commission on an activity still in progress.** Where the contractor's fee is a percentage
of cost, an in-progress activity has not earned the whole percentage. Take it at the
completion factor (60% on the RBI deal) and state on the schedule what the full percentage
would have been and that the balance is not released. Otherwise the contractor has waived a
lien for a fee it has not finished earning.

## Who has to sign

The general contractor's waivers are **not** the requirement. Loan agreements typically
require waivers from the GC *and* from every subcontractor, supplier and material provider
for each work item in the draw (RBI's is §2.8.7(o)(iii)). The GC set is usually three or
four documents; the sub and supplier set is dozens, takes the longest to collect, and is
the thing that actually delays funding.

Start the sub and supplier collection when the draw is first scoped, not when the GC set
comes back signed.

Check whether the GC contract already obliges the contractor to produce them. On the RBI
deal, Art. IV §4.1(c)–(f) of the GC agreement already requires itemised invoices, ch. 713
unconditional partial waivers, workers' comp proof and evidence prior-phase vendors were
paid — so the lender's evidence package needs no negotiation, just a request citing the
clause.

## Execution and notarisation

Fill everything that is the company's to state. Leave exactly four fields:

| Field | Who completes it | Why |
|---|---|---|
| `By: ______` | The signatory | Wet signature, in the notary's presence |
| Notary signature | The notary | — |
| Personally Known / Produced Identification | The notary | Their attestation, not yours |
| Type of Identification Produced | The notary | Their attestation, not yours |

**FS 117.05** requires the notary to complete the jurat personally. Pre-filling the notary's
signature, their ID determination, or their seal is improper and can void the notarisation.
`build_waivers.js` will not produce those filled; the selftest asserts it.

The **jurat date** is different — it is a date, not an attestation, and pre-filling it is
normal when the signing is scheduled. But if the signing slips, the date must change. Three
dates move together: the DATED line, the jurat day/month/year, and the "work complete
through" date if the period is also re-cut. Change them in the deal config, not in the
document.

The **title line** is the company's to state, so fill it — but only from something that
records the office. A title taken from memory should be checked against the corporate
records or the Sunbiz officer listing before it goes on a sworn document.

## Traps

- **A waiver is not a receipt.** Signing acknowledges release of lien rights, not that the
  money arrived. Reconcile against the payment ledger separately.
- **Retainage.** If the contract withholds retainage, say so in the exceptions paragraph.
  If the contract *says* it withholds retainage but no retainage is actually being held
  (check the payment history against the contract phases), the exception is describing
  something that is not happening — and the owner has no punch-list leverage.
- **Notice of Commencement.** Waivers reference the job; the NOC governs priority. If the
  NOC was recorded after the mortgage, or has expired, the waiver set is not the problem
  you have.
- **Owner entity naming.** The waiver names the owner as the form asks. If the loan
  documents and the construction contract describe the same entity differently (state of
  organisation, LLC vs Inc.), fix it in the source contract; do not paper over it in the
  waiver.
- **"To date" is load-bearing.** A schedule headed *Activities 1, 2 and 3* reads as three
  finished activities. *Activities 1, 2 and 3 to date* reads as a snapshot. Use the second
  whenever a partial activity is in scope.
