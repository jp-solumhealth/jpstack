#!/usr/bin/env python3
"""
auth_tracker.py — correct Healthie's accrued visit count.

Healthie already owns the authorization: the authorization number, the approved
visit count, the start and stop dates, the referral flags, visits used and visits
left. All of it lives on InsuranceAuthorizationType and all of it is fine.

One number is wrong. Healthie's tracker accrues against a client's *scheduled and
occurred* appointments, so a clinic given 10 visits that books 20 sees 20 consumed.
This module recomputes that one number from occurred appointments only, writes it
back, and raises a reauthorization alert when the corrected balance runs low.

    python3 auth_tracker.py selftest    # the contract; must print ALL PASS
    python3 auth_tracker.py demo        # 10 authorized, 20 booked, 6 occurred
    python3 auth_tracker.py queries     # print the GraphQL documents

WHAT THIS DELIBERATELY DOES NOT DO
    It does not keep its own authorization records, visit limits, referral state or
    approved counts. Healthie has those and they are correct. Re-storing them would
    create a second source of truth to reconcile, which is a bigger problem than the
    one being fixed. This reads Healthie, corrects one field, writes it back.

FIELD NAMES MARKED "unverified"
    Healthie's docs and both API endpoints are unreachable from the build
    environment, so InsuranceAuthorizationType's GraphQL field names below are
    inferred from its documented UI fields, not read from the schema. The object,
    the mutation `createInsuranceAuthorization`, `pm_status` and its values, and the
    webhook events are all confirmed. Run `queries` and check the marked names
    against introspection before wiring this to a live key.

Requirements, provenance and the API assessment: ../references/requirements.md
"""
from __future__ import annotations
import argparse, sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Protocol

# ══════════════════════════════════════════════════ TRANSPORT

ENDPOINT         = "https://api.gethealthie.com/graphql"
SANDBOX_ENDPOINT = "https://staging-api.gethealthie.com/graphql"

# Pin the version. Without the header Healthie serves the 2024-06-01 baseline,
# which paginates several of the fields below differently.
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Basic <API_KEY>",     # literal "Basic" + the raw key, not base64
    "AuthorizationSource": "API",
    "Healthie-GraphQL-API-Version": "2026-01-01",
    # "AuthorizationShard": "<SHARD_ID>",   # sharded customers only
}

# ══════════════════════════════════════════════════ GRAPHQL DOCUMENTS

# Read the authorization Healthie already holds. Reachable from both User and
# Policy; Policy is preferred because a patient with two policies has one
# authorization per policy.
#   confirmed:   user, insurance_authorization
#   unverified:  every field inside insurance_authorization
GQL_AUTHORIZATION = """
query AuthorizationForPatient($id: ID!) {
  user(id: $id) {
    id
    insurance_authorization {
      id
      authorization_number      # unverified
      number_of_visits          # unverified — the approved allotment
      visits_used               # unverified — the number this module corrects
      visits_left               # unverified
      start_date                # unverified
      end_date                  # unverified
      referral_required         # unverified
      referral_obtained         # unverified
    }
  }
}
"""

# Every appointment in the authorization window. We ask for pm_status and count
# ourselves rather than trusting a server-side filter, because the filter argument
# names are the least certain part of this document and a wrong filter fails silent
# — it returns fewer rows, which reads as a healthier balance than the truth.
#   confirmed:   appointments, pm_status, PageInfo, cursor pagination params
#   unverified:  the filter argument names
GQL_OCCURRED_APPOINTMENTS = """
query AppointmentsInWindow(
  $userId: ID!, $startDate: String!, $endDate: String!,
  $after: Cursor, $pageSize: Int!
) {
  appointments(
    user_id: $userId
    start_date: $startDate      # unverified
    end_date: $endDate          # unverified
    should_paginate: true
    page_size: $pageSize
    after: $after
  ) {
    id
    datetime
    pm_status
    appointment_type { id name }
  }
  appointmentsCount(user_id: $userId)
}
"""

# Write the corrected number back.
#   unverified:  that updateInsuranceAuthorization exists at all. createInsurance-
#                Authorization is confirmed by name; update is convention, not fact.
#                If it does not exist, the fallback is delete-and-recreate, which is
#                materially worse under Healthie's absent idempotency contract and
#                should be escalated rather than quietly implemented.
GQL_UPDATE_AUTHORIZATION = """
mutation CorrectVisitsUsed($input: updateInsuranceAuthorizationInput!) {
  updateInsuranceAuthorization(input: $input) {
    insurance_authorization { id visits_used visits_left }
    messages { field message }
  }
}
"""

# Healthie posts only { resource_id, resource_id_type, event_type } — no status, no
# body. Each event costs a follow-up query. There is no appointment.status_changed
# event, so appointment.updated is the transition signal and the diff is ours to do.
GQL_REGISTER_WEBHOOK = """
mutation RegisterWebhook($input: createWebhookInput!) {
  createWebhook(input: $input) {
    webhook { id url event_type }
    messages { field message }
  }
}
"""

WEBHOOK_EVENTS = (
    "appointment.updated",              # a visit may have become Occurred
    "appointment.created",              # booking — drives the over-booking warning
    "appointment.deleted",
    "insurance_authorization.updated",  # someone edited the auth in the Healthie UI
    "insurance_authorization.created",
)

# ══════════════════════════════════════════════════ THE ONE RULE

# Confirmed pm_status values. "Late Cancellation" and "Checked-In" exist only if
# enabled on the account — neither accrues here, but Late Cancellation is billable
# to some payers and needs a per-client decision before launch.
OCCURRED       = "Occurred"
NON_ACCRUING   = ("No-Show", "Re-Scheduled", "Cancelled", "Late Cancellation",
                  "Checked-In", None, "")

# Evaluation-only dates of service need no prior authorization unless treatment
# codes are billed the same day. Off by default: it is a real payer rule but it
# needs the claim to resolve, and this module's remit is the scheduled/occurred
# correction alone. Turn on only with claim data available.
EVAL_ONLY_CODES = frozenset({"97161", "97162", "97163"})


def accrues(pm_status: str | None, *, billed_codes: tuple[str, ...] = (),
            apply_eval_rule: bool = False) -> bool:
    """The correction, in one function. Scheduled never accrues; occurred does."""
    if pm_status != OCCURRED:
        return False
    if apply_eval_rule and billed_codes and all(c in EVAL_ONLY_CODES for c in billed_codes):
        return False
    return True


# ══════════════════════════════════════════════════ HEALTHIE SHAPES

@dataclass(frozen=True)
class HealthieAppointment:
    id: str
    on: date
    pm_status: str | None
    billed_codes: tuple[str, ...] = ()


@dataclass
class HealthieAuthorization:
    """Mirrors InsuranceAuthorizationType. We never author these fields except
    visits_used and visits_left."""
    id: str
    patient_id: str
    authorization_number: str
    number_of_visits: int
    visits_used: int              # as Healthie currently has it — usually wrong
    start_date: date
    end_date: date
    referral_required: bool = False
    referral_obtained: bool = False

    @property
    def visits_left(self) -> int:
        return self.number_of_visits - self.visits_used


@dataclass(frozen=True)
class Correction:
    patient_id: str
    authorization_id: str
    healthie_visits_used: int     # what Healthie said
    corrected_visits_used: int    # occurred only
    corrected_visits_left: int
    scheduled_not_occurred: int   # the size of the error
    opening_adjustment: int
    written: bool

    @property
    def drift(self) -> int:
        return self.healthie_visits_used - self.corrected_visits_used

    def __str__(self) -> str:
        return (f"{self.authorization_id}: Healthie said {self.healthie_visits_used} used, "
                f"actually {self.corrected_visits_used} "
                f"({self.corrected_visits_left} left, drift {self.drift:+d})")


@dataclass(frozen=True)
class Alert:
    patient_id: str
    authorization_id: str
    authorization_number: str
    visits_left: int
    end_date: date
    referral_missing: bool
    message: str


class HealthieClient(Protocol):
    """The four calls this needs. Implement against the documents above."""
    def authorization(self, patient_id: str) -> HealthieAuthorization | None: ...
    def appointments(self, patient_id: str, start: date, end: date
                     ) -> list[HealthieAppointment]: ...
    def update_visits_used(self, authorization_id: str, used: int, left: int) -> list[dict]: ...


# ══════════════════════════════════════════════════ THE ENGINE

class VisitAccrual:
    """Recompute visits_used from occurred appointments and push it back."""

    THRESHOLD = 3   # alert at this many visits left or fewer

    def __init__(self, client: HealthieClient, *, threshold: int = THRESHOLD,
                 apply_eval_rule: bool = False) -> None:
        self.client = client
        self.threshold = threshold
        self.apply_eval_rule = apply_eval_rule
        # Healthie does not deduct visits delivered before its tracker was switched
        # on, and neither can we — those appointments may predate the integration
        # entirely. Carried per authorization, entered once by whoever onboards the
        # client. Without it, every mid-episode patient launches with a balance that
        # is too generous, which is the failure mode that loses trust fastest.
        self.opening: dict[str, int] = {}

    def set_opening(self, authorization_id: str, visits_already_used: int) -> None:
        self.opening[authorization_id] = visits_already_used

    # ------------------------------------------------------------------ counting

    def count_occurred(self, appts: list[HealthieAppointment]) -> int:
        return sum(1 for a in appts
                   if accrues(a.pm_status, billed_codes=a.billed_codes,
                              apply_eval_rule=self.apply_eval_rule))

    def count_scheduled_not_occurred(self, appts: list[HealthieAppointment]) -> int:
        """The size of Healthie's error — booked but not yet delivered."""
        return sum(1 for a in appts if a.pm_status not in (OCCURRED,)
                   and a.pm_status not in ("No-Show", "Cancelled", "Re-Scheduled"))

    # ------------------------------------------------------------------ the sync

    def sync(self, patient_id: str, *, write: bool = True
             ) -> tuple[Correction, Alert | None]:
        auth = self.client.authorization(patient_id)
        if auth is None:
            raise LookupError(f"no authorization on file for {patient_id}")

        # Capture what Healthie said before the writeback below mutates it — the
        # drift figure is the whole point of this run and it is measured against
        # the number we found, not the number we left behind.
        healthie_said = auth.visits_used

        appts = self.client.appointments(patient_id, auth.start_date, auth.end_date)
        opening = self.opening.get(auth.id, 0)
        used = self.count_occurred(appts) + opening
        # Never report more consumed than was approved, and never a negative balance.
        used = max(0, min(used, auth.number_of_visits))
        left = auth.number_of_visits - used

        written = False
        if write and used != auth.visits_used:
            # No idempotency contract anywhere in this API, so this is a read-then-
            # write against a value we just read. It is safe only because it is
            # idempotent by construction: writing the same corrected number twice is
            # a no-op, and we skip the call entirely when nothing changed.
            messages = self.client.update_visits_used(auth.id, used, left)
            # A validation failure is HTTP 200 with an empty errors[] and a populated
            # messages list. Branching on transport errors alone reports a writeback
            # that never happened.
            if messages:
                raise RuntimeError(f"updateInsuranceAuthorization rejected: {messages}")
            written = True

        correction = Correction(
            patient_id=patient_id,
            authorization_id=auth.id,
            healthie_visits_used=healthie_said,
            corrected_visits_used=used,
            corrected_visits_left=left,
            scheduled_not_occurred=self.count_scheduled_not_occurred(appts),
            opening_adjustment=opening,
            written=written,
        )
        return correction, self._alert(auth, left)

    def _alert(self, auth: HealthieAuthorization, left: int) -> Alert | None:
        if left > self.threshold:
            return None
        missing_referral = auth.referral_required and not auth.referral_obtained
        note = " Referral required and not on file." if missing_referral else ""
        return Alert(
            patient_id=auth.patient_id,
            authorization_id=auth.id,
            authorization_number=auth.authorization_number,
            visits_left=left,
            end_date=auth.end_date,
            referral_missing=missing_referral,
            message=(f"{left} visit(s) left on authorization {auth.authorization_number} "
                     f"(expires {auth.end_date}). Reauthorize now.{note}"),
        )

    # ---------------------------------------------------------------- over-booking

    def overbooked_by(self, patient_id: str) -> int:
        """Booked beyond what is authorized. Fires off appointment.created, before
        a single unauthorized visit has been delivered — which is the difference
        between preventing the loss and reporting it."""
        auth = self.client.authorization(patient_id)
        if auth is None:
            return 0
        appts = self.client.appointments(patient_id, auth.start_date, auth.end_date)
        committed = self.count_occurred(appts) + self.count_scheduled_not_occurred(appts)
        committed += self.opening.get(auth.id, 0)
        return max(0, committed - auth.number_of_visits)


# ══════════════════════════════════════════════════ TEST DOUBLE

class FakeHealthie:
    """Stands in for the GraphQL client, including its worst habit: reporting
    scheduled appointments as consumed."""

    def __init__(self, auth: HealthieAuthorization, appts: list[HealthieAppointment]):
        self._auth, self._appts, self.writes = auth, appts, []

    def authorization(self, patient_id: str) -> HealthieAuthorization | None:
        return self._auth if self._auth.patient_id == patient_id else None

    def appointments(self, patient_id, start, end) -> list[HealthieAppointment]:
        return [a for a in self._appts if start <= a.on <= end]

    def update_visits_used(self, authorization_id: str, used: int, left: int) -> list[dict]:
        self.writes.append((authorization_id, used, left))
        self._auth.visits_used = used
        return []

    def healthie_native_count(self) -> int:
        """What Healthie's own tracker would say: scheduled AND occurred."""
        return sum(1 for a in self._appts
                   if a.pm_status not in ("No-Show", "Cancelled", "Re-Scheduled"))


# ══════════════════════════════════════════════════ SELF-TEST — THE CONTRACT

def _fixture(*, approved=10, occurred=0, scheduled=0, noshow=0, cancelled=0,
             healthie_used=None, referral_required=False, referral_obtained=False):
    D = date(2026, 9, 1)
    auth = HealthieAuthorization(
        id="IA-1", patient_id="P1", authorization_number="AUTH-4471",
        number_of_visits=approved, visits_used=0, start_date=D,
        end_date=D + timedelta(days=90),
        referral_required=referral_required, referral_obtained=referral_obtained)
    appts, n = [], 0
    for status, count in ((OCCURRED, occurred), ("Scheduled", scheduled),
                          ("No-Show", noshow), ("Cancelled", cancelled)):
        for _ in range(count):
            appts.append(HealthieAppointment(f"a{n}", D + timedelta(days=n), status,
                                             billed_codes=("97110",)))
            n += 1
    client = FakeHealthie(auth, appts)
    auth.visits_used = client.healthie_native_count() if healthie_used is None else healthie_used
    return client, auth


def selftest() -> int:
    fails: list[str] = []

    def check(name, cond):
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        if not cond:
            fails.append(name)

    print("\n  ── the correction ──")
    client, auth = _fixture(approved=10, occurred=6, scheduled=14)
    check("Healthie's own count includes the scheduled ones", auth.visits_used == 20)
    corr, alert = VisitAccrual(client).sync("P1")
    check("corrected count is the 6 that occurred", corr.corrected_visits_used == 6)
    check("balance is 4, not -10", corr.corrected_visits_left == 4)
    check("drift is reported", corr.drift == 14)
    check("the write happened", corr.written and client.writes == [("IA-1", 6, 4)])
    check("no alert at 4 remaining", alert is None)

    print("\n  ── nothing else accrues ──")
    client, _ = _fixture(approved=10, occurred=3, scheduled=5, noshow=4, cancelled=6)
    corr, _ = VisitAccrual(client).sync("P1")
    check("no-shows and cancellations never accrue", corr.corrected_visits_used == 3)
    for status in NON_ACCRUING:
        if not accrues(status):
            continue
        fails.append(f"{status} accrued")
    check("no non-accruing status slips through", not any("accrued" in f for f in fails))
    check("only the exact string 'Occurred' accrues",
          accrues("Occurred") and not accrues("occurred") and not accrues("Scheduled"))

    print("\n  ── idempotence ──")
    client, _ = _fixture(approved=10, occurred=6, scheduled=4)
    acc = VisitAccrual(client)
    acc.sync("P1")
    corr2, _ = acc.sync("P1")
    check("a second sync writes nothing", len(client.writes) == 1 and not corr2.written)
    check("...and reports the same balance", corr2.corrected_visits_used == 6)

    print("\n  ── the alert ──")
    client, _ = _fixture(approved=10, occurred=7, scheduled=6)
    corr, alert = VisitAccrual(client).sync("P1")
    check("fires at exactly 3 remaining", alert is not None and alert.visits_left == 3)
    check("carries the authorization number a coordinator needs",
          alert.authorization_number == "AUTH-4471")
    client, _ = _fixture(approved=10, occurred=8, referral_required=True)
    _, alert = VisitAccrual(client).sync("P1")
    check("flags a required referral that is not on file", alert.referral_missing)
    check("...and says so in the message", "Referral required" in alert.message)

    print("\n  ── opening balance ──")
    client, _ = _fixture(approved=10, occurred=2, scheduled=3)
    acc = VisitAccrual(client)
    acc.set_opening("IA-1", 6)
    corr, alert = acc.sync("P1")
    check("visits delivered before we started counting are carried", corr.corrected_visits_used == 8)
    check("...and can push the balance into alert range", alert is not None)
    check("the adjustment is visible, not hidden", corr.opening_adjustment == 6)

    print("\n  ── never reports an impossible balance ──")
    client, _ = _fixture(approved=10, occurred=14)
    corr, _ = VisitAccrual(client).sync("P1")
    check("consumed is capped at approved", corr.corrected_visits_used == 10)
    check("balance floors at zero, never negative", corr.corrected_visits_left == 0)

    print("\n  ── over-booking, before any visit is delivered ──")
    client, _ = _fixture(approved=10, occurred=0, scheduled=20)
    acc = VisitAccrual(client)
    check("20 booked against 10 authorized is caught at booking time",
          acc.overbooked_by("P1") == 10)
    client, _ = _fixture(approved=10, occurred=2, scheduled=5)
    check("booking within the allotment is not flagged",
          VisitAccrual(client).overbooked_by("P1") == 0)

    print("\n  ── writeback failures are not silent ──")
    client, _ = _fixture(approved=10, occurred=5, scheduled=3)
    client.update_visits_used = lambda *_a: [{"field": "visits_used", "message": "invalid"}]
    try:
        VisitAccrual(client).sync("P1")
        check("a populated messages list raises", False)
    except RuntimeError as e:
        check("a populated messages list raises", "rejected" in str(e))

    print("\n  ── read-only mode ──")
    client, _ = _fixture(approved=10, occurred=6, scheduled=4)
    corr, _ = VisitAccrual(client).sync("P1", write=False)
    check("shadow run computes without writing",
          corr.corrected_visits_used == 6 and not corr.written and client.writes == [])

    print("\n  ── the evaluation rule stays off unless asked for ──")
    D = date(2026, 9, 1)
    auth = HealthieAuthorization("IA-1", "P1", "AUTH-4471", 10, 0, D, D + timedelta(days=90))
    evals = [HealthieAppointment(f"e{i}", D + timedelta(days=i), OCCURRED, ("97161",))
             for i in range(3)]
    check("default counts an eval visit",
          VisitAccrual(FakeHealthie(auth, evals)).count_occurred(evals) == 3)
    check("opt-in excludes eval-only dates of service",
          VisitAccrual(FakeHealthie(auth, evals), apply_eval_rule=True).count_occurred(evals) == 0)

    print()
    if fails:
        print(f"  {len(fails)} FAILED: " + "; ".join(fails))
        return 1
    print("  ALL PASS")
    return 0


# ══════════════════════════════════════════════════ DEMO

def demo() -> None:
    client, auth = _fixture(approved=10, occurred=6, scheduled=14)
    print(f"\n  Authorization {auth.authorization_number} — {auth.number_of_visits} visits approved")
    print(f"  20 appointments booked, 6 of them occurred.\n")
    print(f"    Healthie says used ......... {auth.visits_used:>3}"
          f"   (left {auth.number_of_visits - auth.visits_used:>3})   ← scheduled + occurred")
    corr, alert = VisitAccrual(client).sync("P1")
    print(f"    corrected to ............... {corr.corrected_visits_used:>3}"
          f"   (left {corr.corrected_visits_left:>3})   ← occurred only")
    print(f"    still booked, not delivered  {corr.scheduled_not_occurred:>3}")
    print(f"\n  {corr}")
    print(f"  alert: {alert.message if alert else 'none — 4 visits left'}")
    print(f"\n  Same patient, at booking time: over-booked by "
          f"{VisitAccrual(client).overbooked_by('P1')} visits.\n")


def queries() -> None:
    for name, doc in (("authorization", GQL_AUTHORIZATION),
                      ("appointments", GQL_OCCURRED_APPOINTMENTS),
                      ("writeback", GQL_UPDATE_AUTHORIZATION),
                      ("webhook", GQL_REGISTER_WEBHOOK)):
        print(f"\n{'─' * 72}\n{name}\n{'─' * 72}{doc}")
    print(f"\n{'─' * 72}\nheaders\n{'─' * 72}")
    for k, v in HEADERS.items():
        print(f"  {k}: {v}")
    print(f"\n  endpoint: {ENDPOINT}\n  sandbox:  {SANDBOX_ENDPOINT}")
    print(f"\n  webhook events to register:")
    for e in WEBHOOK_EVENTS:
        print(f"    {e}")
    print()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("cmd", choices=("selftest", "demo", "queries"), nargs="?", default="selftest")
    a = p.parse_args()
    if a.cmd == "selftest":
        sys.exit(selftest())
    demo() if a.cmd == "demo" else queries()


if __name__ == "__main__":
    main()
