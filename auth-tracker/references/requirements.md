# Visit balance tracker — requirements and provenance

Consolidated from client calls, then checked against what the Healthie API actually
exposes. Every requirement here traces to something a client said on a recorded call.

## The core defect

Authorizations are granted in **visits**. We tracked them in **dates** — an expiry
reminder 45 days out. The operational risk is volume, not time:

> "We were given 10 visits. They've got scheduled 20 visits. We only know how many
> are left when there's been an occurred visit. So we now have five."

Three distinct failures:

1. **Wrong axis** — alerting on expiry, a dimension the clinic does not manage.
   Expiry "very rarely is the issue anyway."
2. **Wrong event** — where visits were surfaced at all, they were *scheduled*
   visits, not *completed* ones. Worse than no number, because cancellations and
   no-shows inflate it.
3. **No balance object** — the approved count is written once, by hand, and never
   decremented. Nothing represents *remaining*.

## The same gap, from a second client

A different integration hit this from the opposite direction. There, a coordinator
manually triages every pending authorization. Two scenarios drive that triage:

- **Premature pending auth** — raised when a patient schedules outside the current
  authorization's date range. *Dismissed if the current auth has sufficient visits
  and is not expiring soon.*
- **Missing documentation** — an auth cannot be submitted without a signed progress
  note or treatment plan.

The first is a human performing this module's arithmetic. That manual step is the
stated blocker on automating the whole authorization pipeline, and it is why this
is built as a shared capability rather than a single-client feature.

That client also needs **authorization history** — last auth by specialty, its dates
and program — to derive the next authorization. See the Healthie constraint below;
history cannot live in the EHR.

## Consumption rules

| Rule | Source |
|---|---|
| Only a terminal *occurred* status consumes. Scheduled, cancelled, no-show never do. | Stated twice on the same call: "not after scheduling, after completion" |
| Trigger at **≤3 visits remaining** | Confirmed explicitly: "three or less" |
| Applies to the **plan visit limit** too, not just the authorization | "if someone has like 30 visits, we want to proactively know" |
| An **evaluation-only** date of service does not consume | Eval codes 97161–97163 need no PA unless other treatment codes are billed the same date |
| The trigger **notifies**; a human submits | "We cannot automatically initiate the full authorization if you are not inputting the documents" |
| Plan limits are **cross-provider** — the payer's visits-used figure beats our count | Benefit-year caps count visits at every practice |
| **Backfill required** — patients mid-episode have consumed visits we never saw | Healthie's own tracker has the same behaviour and requires manual adjustment |

## Healthie constraints that shape the implementation

Established by assessment of the published schema; see the Healthie Auth API Map.

- **The native tracker counts scheduled *and* occurred appointments.** It cannot be
  used as a source of truth. It is a display surface only.
- **`insurance_authorization` is `has_one`** on both User and Policy. Healthie cannot
  hold concurrent authorizations or any history. **Solum is the system of record**;
  Healthie receives a one-way projection of the current balance.
- **`BillingItem` has no relationship to `Appointment`.** A charge cannot be joined
  back to the visit that produced it. The only path from visit to claim is
  `FormAnswerGroup` — the charting note.
- **`form_answer_group.signed` is the recommended consumption signal.** It is the
  earliest event tied to something the clinic must do to get paid, which is what
  makes a data source trustworthy. Appointment status is faster but depends on
  calendar hygiene nobody is paid to maintain.
- **No idempotency contract.** Every write must be query-first.
- **No `appointment.status_changed` event.** Diff `appointment.updated` against
  last-known status; webhook payloads carry only a resource id.

## Open

- Exact GraphQL field names on `InsuranceAuthorizationType`.
- Whether `updateInsuranceAuthorization` exists — the writeback design depends on it.
- Whether Late Cancellation / Checked-In statuses are enabled per account, and
  whether a late cancel should consume.
- Whether the native tracker recalculates from the calendar after we overwrite it.
- Attribution rule when a patient holds two live authorizations, and whether general
  PT and pelvic floor draw on the same allotment.
- Whether the ≤3 threshold should instead be days of runway; cadence varies 1×–3×
  weekly and payer turnaround varies from days to weeks.

## Status of this module

`scripts/auth_tracker.py` implements the counter, the trigger and the triage against
the rules above, with the self-test as the contract. It currently keys consumption on
appointment status with a billed-code overlay. Per the Healthie assessment, the
primary signal should move to the signed charting note before this is wired to live
data — the ledger and trigger logic are unaffected by that change; only the ingestion
event is.
