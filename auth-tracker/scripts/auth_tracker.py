#!/usr/bin/env python3
"""
auth_tracker.py — authorization visit-balance tracker.

Counts authorized visits when they OCCUR, never when they are scheduled, and fires
a reauthorization trigger before the allotment runs out. Also answers the inverse
question — "does this pending authorization actually need submitting?" — which is
the manual triage step blocking automation on the Raintree side.

    python3 auth_tracker.py selftest      # the contract; must print ALL PASS
    python3 auth_tracker.py demo          # the 10-authorized / 20-scheduled scenario
    python3 auth_tracker.py triage        # premature-pending-auth triage walkthrough

WHY THIS EXISTS
    Authorizations are granted in visits. We tracked them in dates. A clinic given
    10 visits could schedule 20, deliver all 20, and discover the overage only when
    the claims denied. Two clients hit the same wall from opposite directions:

      - Visit-based tracking asked for repeatedly since June; escalated to the
        top priority on the Aug 28 touchpoint. Needs a burn-down and a trigger.
      - A coordinator manually triages every pending authorization, dismissing the
        ones whose current auth still has visits left. That is a human performing
        this module's arithmetic, and it blocks the whole automation pipeline.

    Same counter. Both problems.

THE THREE RULES THAT MATTER
    1. Only an appointment in a terminal OCCURRED state consumes an allotment.
       Scheduled, cancelled and no-show never decrement.
    2. Occurring is necessary but not sufficient. Consumption follows the billed
       codes: an evaluation-only visit (97161-97163) does not consume, because the
       payer does not require prior auth for it unless treatment codes ride along
       on the same date of service.
    3. The ledger is append-only. A visit restatused after the fact reverses its
       entry rather than mutating a counter, so every balance is auditable and
       every correction is reversible.

Requirements, open unknowns and provenance: ../references/requirements.md
"""
from __future__ import annotations
import argparse, sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Iterable

# ══════════════════════════════════════════════════ STATUS + CODE SEMANTICS

class ApptStatus(str, Enum):
    SCHEDULED   = "scheduled"
    CONFIRMED   = "confirmed"
    OCCURRED    = "occurred"        # the only status that can consume
    NO_SHOW     = "no_show"
    CANCELLED   = "cancelled"
    LATE_CANCEL = "late_cancelled"  # billable to some payers; does not consume in v1
    RESCHEDULED = "rescheduled"

CONSUMING_STATUSES = frozenset({ApptStatus.OCCURRED})

# PT evaluation codes. An eval-only date of service does not require prior auth,
# so it does not draw down the allotment. If any other treatment code is billed on
# the same date, the visit consumes normally.
EVAL_ONLY_CODES = frozenset({"97161", "97162", "97163"})


class Basis(str, Enum):
    """How a consumption decision was reached — recorded per ledger row so the
    balance's own reliability can be audited later."""
    BILLED_CODES = "billed_codes"   # authoritative: we saw what was billed
    ATTENDANCE   = "attendance"     # fallback: status only, codes unknown


class Severity(str, Enum):
    SOFT = "soft"   # limit can be extended with a medical-necessity review
    HARD = "hard"   # hard stop; stop scheduling


class TriggerKind(str, Enum):
    AUTH_EXHAUSTING = "auth_exhausting"
    PLAN_LIMIT       = "plan_limit_approaching"
    PA_THRESHOLD     = "pa_required_after_n"
    MNR_THRESHOLD    = "mnr_required_after_n"


class Triage(str, Enum):
    DISMISS       = "dismiss"        # current auth still covers it
    HOLD_FOR_DOCS = "hold_for_docs"  # cannot submit, documentation missing
    SUBMIT        = "submit"         # genuinely needs a new authorization


# ══════════════════════════════════════════════════ DOMAIN OBJECTS

@dataclass(frozen=True)
class Appointment:
    id: str
    patient_id: str
    on: date
    status: ApptStatus
    program: str = "PT"              # service line / Raintree "program"
    location: str = ""
    billed_codes: tuple[str, ...] = ()   # empty => codes unknown, attendance basis

    def is_eval_only(self) -> bool:
        return bool(self.billed_codes) and all(c in EVAL_ONLY_CODES for c in self.billed_codes)


@dataclass
class Authorization:
    id: str
    patient_id: str
    payer: str
    program: str
    approved_visits: int
    valid_from: date
    valid_to: date
    hard_limit: bool = True
    # Visits consumed before this system started counting. Until an opening balance
    # is confirmed, the auth reports a balance but never fires a trigger — an
    # unconfirmed balance is a guess, and a guess that pages someone is worse than
    # silence.
    opening_consumed: int = 0
    opening_confirmed: bool = False
    # Thresholds captured by the benefits check but never previously evaluated.
    pa_required_after: int | None = None
    mnr_required_after: int | None = None
    active: bool = True

    def covers(self, appt: Appointment) -> bool:
        return (self.active
                and self.program == appt.program
                and self.valid_from <= appt.on <= self.valid_to)


@dataclass
class PlanLimit:
    """Benefit-year visit cap. Counts visits at EVERY provider, so our own ledger
    is a floor, not the truth. When the payer reports a used-to-date figure, that
    number wins."""
    patient_id: str
    benefit_year: int
    limit_visits: int
    hard_limit: bool = True
    payer_reported_used: int | None = None
    payer_reported_on: date | None = None
    opening_confirmed: bool = False


@dataclass(frozen=True)
class LedgerEntry:
    appointment_id: str
    auth_id: str
    on: date
    delta: int          # +1 consume, -1 reversal
    basis: Basis
    reason: str


@dataclass(frozen=True)
class Trigger:
    kind: TriggerKind
    severity: Severity
    patient_id: str
    auth_id: str | None
    remaining: int
    threshold: int
    projected_exhaustion: date | None
    missing_documents: tuple[str, ...]
    message: str

    def ready_to_submit(self) -> bool:
        return not self.missing_documents


# ══════════════════════════════════════════════════ THE ENGINE

class AuthTracker:
    """Append-only ledger plus derived balances. Every public method is idempotent:
    replaying the same appointment state twice changes nothing."""

    REAUTH_THRESHOLD = 3        # fire at <= 3 visits remaining
    EXPIRY_HORIZON   = 30       # "not expiring soon" for triage, in days
    CADENCE_WINDOW   = 42       # days of history used to estimate visit cadence

    def __init__(self, *, threshold: int = REAUTH_THRESHOLD) -> None:
        self.threshold = threshold
        self.auths: dict[str, Authorization] = {}
        self.plan_limits: dict[tuple[str, int], PlanLimit] = {}
        self.ledger: list[LedgerEntry] = []
        self._counted: dict[str, str] = {}          # appointment_id -> auth_id
        self._fired: dict[tuple[str, str], int] = {}  # (kind, key) -> remaining at last fire
        self.unattributed: list[Appointment] = []
        self._documents: dict[str, set[str]] = {}   # patient_id -> documents on file

    # ---------------------------------------------------------------- setup

    def add_authorization(self, auth: Authorization) -> None:
        self.auths[auth.id] = auth

    def add_plan_limit(self, pl: PlanLimit) -> None:
        self.plan_limits[(pl.patient_id, pl.benefit_year)] = pl

    def set_documents(self, patient_id: str, documents: Iterable[str]) -> None:
        self._documents[patient_id] = set(documents)

    def confirm_opening_balance(self, auth_id: str, consumed: int) -> None:
        """Backfill. Every patient mid-episode at launch has consumed visits this
        system never saw; without this the balance is wrong for the whole panel on
        day one, which is worse than shipping no balance at all."""
        a = self.auths[auth_id]
        a.opening_consumed = consumed
        a.opening_confirmed = True

    # ------------------------------------------------------- consumption rule

    @staticmethod
    def consumption(appt: Appointment) -> tuple[bool, Basis, str]:
        """Does this appointment draw down an allotment? Returns (consumes, basis, why)."""
        if appt.status not in CONSUMING_STATUSES:
            return False, Basis.ATTENDANCE, f"status {appt.status.value} is not occurred"
        if appt.billed_codes:
            if appt.is_eval_only():
                return False, Basis.BILLED_CODES, "evaluation-only date of service"
            return True, Basis.BILLED_CODES, "treatment codes billed"
        # Codes unknown. Count it — under-counting silently authorizes overage —
        # but record the weaker basis so accuracy can be measured.
        return True, Basis.ATTENDANCE, "occurred; billed codes unknown"

    # ----------------------------------------------------------- attribution

    def attribute(self, appt: Appointment) -> Authorization | None:
        """Which authorization does this visit draw against? Deterministic: among
        the authorizations covering the visit, prefer one with visits left, then
        the one expiring soonest, then the lowest id."""
        candidates = [a for a in self.auths.values()
                      if a.patient_id == appt.patient_id and a.covers(appt)]
        if not candidates:
            return None
        candidates.sort(key=lambda a: (self.remaining(a.id) <= 0, a.valid_to, a.id))
        return candidates[0]

    # -------------------------------------------------------------- balances

    def consumed(self, auth_id: str) -> int:
        a = self.auths[auth_id]
        return a.opening_consumed + sum(e.delta for e in self.ledger if e.auth_id == auth_id)

    def remaining(self, auth_id: str) -> int:
        return self.auths[auth_id].approved_visits - self.consumed(auth_id)

    def plan_consumed(self, patient_id: str, year: int) -> int:
        pl = self.plan_limits.get((patient_id, year))
        if pl and pl.payer_reported_used is not None:
            # The payer sees every provider; we only see ours.
            return pl.payer_reported_used
        return sum(e.delta for e in self.ledger
                   if e.on.year == year
                   and self.auths[e.auth_id].patient_id == patient_id)

    def plan_remaining(self, patient_id: str, year: int) -> int | None:
        pl = self.plan_limits.get((patient_id, year))
        if pl is None:
            return None
        return pl.limit_visits - self.plan_consumed(patient_id, year)

    # ------------------------------------------------------------- ingestion

    def record(self, appt: Appointment) -> list[Trigger]:
        """Ingest an appointment's current state. Safe to replay."""
        consumes, basis, why = self.consumption(appt)
        prior_auth_id = self._counted.get(appt.id)

        if not consumes:
            if prior_auth_id:      # was counted, has since been restatused or recoded
                self.ledger.append(LedgerEntry(appt.id, prior_auth_id, appt.on, -1,
                                               basis, f"reversal: {why}"))
                del self._counted[appt.id]
            return []

        if prior_auth_id:          # already counted; nothing to do
            return []

        auth = self.attribute(appt)
        if auth is None:
            # No authorization covers this visit. Scheduling outside the current
            # auth window is exactly what raises a premature pending auth upstream.
            self.unattributed.append(appt)
            return []

        self.ledger.append(LedgerEntry(appt.id, auth.id, appt.on, +1, basis, why))
        self._counted[appt.id] = auth.id
        return self.evaluate(auth.id, as_of=appt.on)

    def record_many(self, appts: Iterable[Appointment]) -> list[Trigger]:
        out: list[Trigger] = []
        for a in appts:
            out.extend(self.record(a))
        return out

    # ------------------------------------------------------------ evaluation

    def evaluate(self, auth_id: str, *, as_of: date) -> list[Trigger]:
        auth = self.auths[auth_id]
        out: list[Trigger] = []
        remaining = self.remaining(auth_id)
        used = self.consumed(auth_id)

        if auth.opening_confirmed and remaining <= self.threshold:
            out.extend(self._fire(
                TriggerKind.AUTH_EXHAUSTING, auth.id, remaining, self.threshold,
                Severity.HARD if auth.hard_limit else Severity.SOFT, auth, as_of,
                f"{remaining} visit(s) left on {auth.id} ({auth.payer}); reauthorize now"))

        for kind, after in ((TriggerKind.PA_THRESHOLD, auth.pa_required_after),
                            (TriggerKind.MNR_THRESHOLD, auth.mnr_required_after)):
            if after is not None and used >= after:
                out.extend(self._fire(
                    kind, f"{auth.id}:{kind.value}", after - used, after,
                    Severity.SOFT, auth, as_of,
                    f"{used} visits used; {kind.value.replace('_', ' ')} at {after}"))

        year = as_of.year
        pl = self.plan_limits.get((auth.patient_id, year))
        if pl and pl.opening_confirmed:
            pr = self.plan_remaining(auth.patient_id, year)
            if pr is not None and pr <= self.threshold:
                out.extend(self._fire(
                    TriggerKind.PLAN_LIMIT, f"{auth.patient_id}:{year}", pr, self.threshold,
                    Severity.HARD if pl.hard_limit else Severity.SOFT, auth, as_of,
                    f"{pr} visit(s) left on the {year} plan cap for {auth.patient_id}"))
        return out

    def _fire(self, kind, key, remaining, threshold, severity, auth, as_of, msg):
        """Fire once per crossing. Re-fires only when the balance drops further, so
        a coordinator is not paged three times for the same auth."""
        seen = self._fired.get((kind.value, key))
        if seen is not None and remaining >= seen:
            return []
        self._fired[(kind.value, key)] = remaining
        yield Trigger(
            kind=kind, severity=severity, patient_id=auth.patient_id, auth_id=auth.id,
            remaining=remaining, threshold=threshold,
            projected_exhaustion=self.project_exhaustion(auth.id, as_of),
            missing_documents=self.missing_documents(auth.patient_id),
            message=msg,
        )

    # --------------------------------------------------------------- support

    REQUIRED_DOCS = ("signed_progress_note", "treatment_plan")

    def missing_documents(self, patient_id: str) -> tuple[str, ...]:
        """An authorization cannot be submitted without these on file. Surfacing it
        on the trigger is what turns an alert into something actionable."""
        have = self._documents.get(patient_id, set())
        return tuple(d for d in self.REQUIRED_DOCS if d not in have)

    def cadence_per_week(self, auth_id: str, as_of: date) -> float | None:
        """Visits per week over the recent window. Three visits remaining is five
        days of runway at 3x/week and three weeks at 1x/week — the same number
        means very different lead time against a payer's turnaround."""
        window_start = as_of - timedelta(days=self.CADENCE_WINDOW)
        dates = sorted(e.on for e in self.ledger
                       if e.auth_id == auth_id and e.delta > 0 and e.on >= window_start)
        if len(dates) < 2:
            return None
        span_days = max((dates[-1] - dates[0]).days, 1)
        return len(dates) / (span_days / 7.0)

    def project_exhaustion(self, auth_id: str, as_of: date) -> date | None:
        rate = self.cadence_per_week(auth_id, as_of)
        remaining = self.remaining(auth_id)
        if not rate or remaining <= 0:
            return None
        return as_of + timedelta(days=round(remaining / rate * 7))

    # ----------------------------------------------------------------- triage

    def triage_pending(self, patient_id: str, program: str, as_of: date) -> tuple[Triage, str]:
        """Should this pending authorization actually be submitted?

        Replaces the manual step a coordinator performs on every case: dismiss it
        when the current authorization still has visits and is not expiring soon;
        hold it when the documentation is not there yet; otherwise submit."""
        live = [a for a in self.auths.values()
                if a.patient_id == patient_id and a.program == program and a.active
                and a.valid_from <= as_of <= a.valid_to]
        if live:
            live.sort(key=lambda a: a.valid_to)
            cur = live[0]
            remaining = self.remaining(cur.id)
            days_left = (cur.valid_to - as_of).days
            if remaining > self.threshold and days_left > self.EXPIRY_HORIZON:
                return (Triage.DISMISS,
                        f"{cur.id} still has {remaining} visits and {days_left} days; "
                        f"scheduled beyond the window is not a reason to submit")
        missing = self.missing_documents(patient_id)
        if missing:
            return Triage.HOLD_FOR_DOCS, "missing " + ", ".join(missing)
        return Triage.SUBMIT, "no covering authorization with visits remaining"

    # ------------------------------------------------------------- reporting

    def balance_report(self, auth_id: str, as_of: date) -> str:
        a = self.auths[auth_id]
        rem, used = self.remaining(auth_id), self.consumed(auth_id)
        rate = self.cadence_per_week(auth_id, as_of)
        proj = self.project_exhaustion(auth_id, as_of)
        conf = "" if a.opening_confirmed else "  ⚠ opening balance unconfirmed — no triggers"
        bar = "█" * max(rem, 0) + "·" * min(used, a.approved_visits)
        return (f"  {a.id}  {a.payer:<18} {a.program}\n"
                f"    approved {a.approved_visits:>3}   used {used:>3}   remaining {rem:>3}   [{bar}]\n"
                f"    cadence {rate:.1f}/wk   projected exhaustion {proj}" .replace("None", "n/a")
                + conf)


# ══════════════════════════════════════════════════ SELF-TEST — THE CONTRACT

def selftest() -> int:
    fails: list[str] = []

    def check(name, cond):
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        if not cond:
            fails.append(name)

    D = date(2026, 9, 1)
    def auth(**kw):
        base = dict(id="A1", patient_id="P1", payer="Aetna", program="PT",
                    approved_visits=10, valid_from=D, valid_to=D + timedelta(days=90),
                    opening_confirmed=True)
        base.update(kw)
        return Authorization(**base)

    def appt(i, status=ApptStatus.OCCURRED, day=0, codes=("97110",), patient="P1", program="PT"):
        return Appointment(f"appt-{i}", patient, D + timedelta(days=day), status,
                           program=program, billed_codes=codes)

    print("\n  ── the scenario this exists to prevent ──")
    t = AuthTracker(); t.add_authorization(auth())
    t.record_many(appt(i, ApptStatus.SCHEDULED, day=i * 3) for i in range(20))
    check("20 scheduled against a 10-visit auth consumes nothing", t.remaining("A1") == 10)
    check("...and fires no trigger", t._fired == {})

    print("\n  ── occurrence semantics ──")
    t = AuthTracker(); t.add_authorization(auth())
    t.record_many(appt(i, ApptStatus.OCCURRED, day=i * 3) for i in range(4))
    check("4 occurred visits decrement to 6", t.remaining("A1") == 6)
    t.record(appt(90, ApptStatus.NO_SHOW, day=40))
    t.record(appt(91, ApptStatus.CANCELLED, day=41))
    t.record(appt(92, ApptStatus.LATE_CANCEL, day=42))
    check("no-show, cancel and late-cancel never decrement", t.remaining("A1") == 6)
    t.record(appt(0, ApptStatus.OCCURRED, day=0))
    check("replaying the same appointment is idempotent", t.remaining("A1") == 6)

    print("\n  ── billed-code rule ──")
    t = AuthTracker(); t.add_authorization(auth())
    t.record(appt(1, codes=("97161",)))
    check("evaluation-only date of service does not consume", t.remaining("A1") == 10)
    t.record(appt(2, codes=("97161", "97110")))
    check("eval plus a treatment code consumes", t.remaining("A1") == 9)
    t.record(appt(3, codes=()))
    check("unknown codes fall back to attendance and consume", t.remaining("A1") == 8)
    check("...and the ledger records the weaker basis",
          any(e.basis is Basis.ATTENDANCE and e.delta > 0 for e in t.ledger))

    print("\n  ── retroactive correction ──")
    t = AuthTracker(); t.add_authorization(auth())
    t.record(appt(1, ApptStatus.OCCURRED))
    t.record(appt(2, ApptStatus.OCCURRED, day=3))
    check("two visits counted", t.remaining("A1") == 8)
    t.record(appt(2, ApptStatus.NO_SHOW, day=3))
    check("restatus to no-show reverses the entry", t.remaining("A1") == 9)
    check("reversal is appended, never edited in place", len(t.ledger) == 3)
    t.record(appt(2, ApptStatus.NO_SHOW, day=3))
    check("reversal is itself idempotent", t.remaining("A1") == 9 and len(t.ledger) == 3)

    print("\n  ── the trigger ──")
    t = AuthTracker(); t.add_authorization(auth())
    fired = t.record_many(appt(i, day=i * 3) for i in range(6))
    check("no trigger while 4 visits remain", fired == [])
    fired = t.record(appt(7, day=21))
    check("trigger fires at exactly 3 remaining", len(fired) == 1 and fired[0].remaining == 3)
    check("severity follows the hard limit", fired[0].severity is Severity.HARD)
    check("payload projects an exhaustion date", fired[0].projected_exhaustion is not None)
    again = t.record(appt(7, day=21))
    check("no duplicate trigger for the same balance", again == [])
    dropped = t.record(appt(8, day=24))
    check("re-fires when the balance drops further", len(dropped) == 1 and dropped[0].remaining == 2)

    print("\n  ── opening balance gate ──")
    t = AuthTracker(); t.add_authorization(auth(opening_confirmed=False, opening_consumed=8))
    fired = t.record(appt(1))
    check("unconfirmed opening balance suppresses the trigger", fired == [])
    check("...but the balance is still computed", t.remaining("A1") == 1)
    t.confirm_opening_balance("A1", 8)
    fired = t.record(appt(2, day=3))
    check("confirming the backfill lets it fire", len(fired) == 1 and fired[0].remaining == 0)

    print("\n  ── plan cap, counted separately ──")
    t = AuthTracker(); t.add_authorization(auth(approved_visits=30))
    t.add_plan_limit(PlanLimit("P1", 2026, limit_visits=6, opening_confirmed=True))
    fired = t.record_many(appt(i, day=i * 3) for i in range(3))
    check("far from the auth limit, no auth trigger",
          all(f.kind is not TriggerKind.AUTH_EXHAUSTING for f in fired))
    check("but the plan cap fires", any(f.kind is TriggerKind.PLAN_LIMIT for f in fired))
    t2 = AuthTracker(); t2.add_authorization(auth(approved_visits=30))
    t2.add_plan_limit(PlanLimit("P1", 2026, limit_visits=30, payer_reported_used=28,
                                opening_confirmed=True))
    check("payer-reported usage overrides our own count",
          t2.plan_remaining("P1", 2026) == 2)

    print("\n  ── VOB thresholds we already collect but never evaluated ──")
    t = AuthTracker(); t.add_authorization(auth(approved_visits=30, pa_required_after=6,
                                                mnr_required_after=12))
    fired = t.record_many(appt(i, day=i * 3) for i in range(6))
    check("PA-required-after-N fires off the same counter",
          any(f.kind is TriggerKind.PA_THRESHOLD for f in fired))
    fired = t.record_many(appt(i, day=i * 3) for i in range(6, 12))
    check("M&R-required-after-N fires off the same counter",
          any(f.kind is TriggerKind.MNR_THRESHOLD for f in fired))

    print("\n  ── attribution across concurrent authorizations ──")
    t = AuthTracker()
    t.add_authorization(auth(id="A-early", approved_visits=2,
                             valid_to=D + timedelta(days=30)))
    t.add_authorization(auth(id="A-late", approved_visits=10,
                             valid_from=D, valid_to=D + timedelta(days=120)))
    t.record_many(appt(i, day=i) for i in range(3))
    check("drains the sooner-expiring auth first", t.remaining("A-early") == 0)
    check("then spills into the next", t.remaining("A-late") == 9)
    t2 = AuthTracker()
    t2.add_authorization(auth(id="A-pt", program="PT", approved_visits=5))
    t2.add_authorization(auth(id="A-pelvic", program="PELVIC", approved_visits=5))
    t2.record(appt(1, program="PELVIC"))
    check("service line is respected", t2.remaining("A-pt") == 5 and t2.remaining("A-pelvic") == 4)

    print("\n  ── visits outside every authorization window ──")
    t = AuthTracker(); t.add_authorization(auth(valid_to=D + timedelta(days=10)))
    t.record(appt(1, day=60))
    check("an uncovered visit is flagged, not silently dropped", len(t.unattributed) == 1)
    check("...and does not corrupt the balance", t.remaining("A1") == 10)

    print("\n  ── triage: the manual step this replaces ──")
    t = AuthTracker(); t.add_authorization(auth(approved_visits=10))
    t.set_documents("P1", ("signed_progress_note", "treatment_plan"))
    t.record_many(appt(i, day=i * 3) for i in range(2))
    verdict, _ = t.triage_pending("P1", "PT", D + timedelta(days=10))
    check("dismisses a premature pending auth", verdict is Triage.DISMISS)
    t.record_many(appt(i, day=i * 3) for i in range(2, 9))
    verdict, _ = t.triage_pending("P1", "PT", D + timedelta(days=30))
    check("submits once the visits are nearly gone", verdict is Triage.SUBMIT)
    t.set_documents("P1", ("treatment_plan",))
    verdict, why = t.triage_pending("P1", "PT", D + timedelta(days=30))
    check("holds when documentation is missing", verdict is Triage.HOLD_FOR_DOCS)
    check("...and names what is missing", "signed_progress_note" in why)

    print("\n  ── alerts are actionable ──")
    t = AuthTracker(); t.add_authorization(auth())
    t.set_documents("P1", ("treatment_plan",))
    fired = t.record_many(appt(i, day=i * 3) for i in range(7))
    trig = next(f for f in fired if f.kind is TriggerKind.AUTH_EXHAUSTING)
    check("trigger reports it is not submittable yet", not trig.ready_to_submit())
    check("...and lists the blocking document",
          trig.missing_documents == ("signed_progress_note",))

    print()
    if fails:
        print(f"  {len(fails)} FAILED: " + "; ".join(fails))
        return 1
    print("  ALL PASS")
    return 0


# ══════════════════════════════════════════════════ DEMOS

def demo() -> None:
    D = date(2026, 9, 1)
    t = AuthTracker()
    t.add_authorization(Authorization(
        id="AUTH-4471", patient_id="P-1029", payer="Aetna", program="PT",
        approved_visits=10, valid_from=D, valid_to=D + timedelta(days=90),
        opening_confirmed=True, pa_required_after=None, mnr_required_after=None))
    t.set_documents("P-1029", ("treatment_plan",))

    print("\n  Ten visits authorized. Twenty booked. Watch the balance.\n")
    booked = [Appointment(f"a{i}", "P-1029", D + timedelta(days=i * 3),
                          ApptStatus.SCHEDULED, billed_codes=("97110",)) for i in range(20)]
    t.record_many(booked)
    print(f"    after booking all 20:  remaining = {t.remaining('AUTH-4471')}"
          "   ← scheduling consumes nothing\n")

    print("  Now they start happening.\n")
    for i, a in enumerate(booked):
        occurred = Appointment(a.id, a.patient_id, a.on, ApptStatus.OCCURRED,
                               billed_codes=("97161",) if i == 0 else ("97110",))
        for trig in t.record(occurred):
            flag = "READY" if trig.ready_to_submit() else "BLOCKED"
            print(f"    ▲ {trig.kind.value:<22} {trig.remaining} left   "
                  f"exhausts ~{trig.projected_exhaustion}   [{flag}]")
            if trig.missing_documents:
                print(f"      needs: {', '.join(trig.missing_documents)}")
        if i in (0, 6, 9, 12):
            note = "  (evaluation only — does not consume)" if i == 0 else ""
            print(f"    visit {i + 1:>2} occurred  →  remaining "
                  f"{t.remaining('AUTH-4471'):>3}{note}")
        if t.remaining("AUTH-4471") <= 0 and i >= 12:
            print(f"\n    visit {i + 1} was delivered with the allotment exhausted."
                  "\n    Without the trigger above, nobody would know until the claim denied.")
            break
    print()
    print(t.balance_report("AUTH-4471", D + timedelta(days=40)))
    print()


def triage_demo() -> None:
    D = date(2026, 9, 1)
    t = AuthTracker()
    t.add_authorization(Authorization(
        id="AUTH-8802", patient_id="P-77", payer="Optum", program="PT",
        approved_visits=12, valid_from=D, valid_to=D + timedelta(days=90),
        opening_confirmed=True))
    t.set_documents("P-77", ("signed_progress_note", "treatment_plan"))
    print("\n  A pending authorization is raised every time a patient books beyond")
    print("  the current window. Most of them should never be submitted.\n")
    for used, day, label in ((2, 10, "early in the episode"),
                             (7, 30, "mid-episode"),
                             (10, 60, "nearly exhausted")):
        t2 = AuthTracker()
        t2.add_authorization(t.auths["AUTH-8802"].__class__(**t.auths["AUTH-8802"].__dict__))
        t2.set_documents("P-77", ("signed_progress_note", "treatment_plan"))
        t2.record_many(Appointment(f"x{i}", "P-77", D + timedelta(days=i), ApptStatus.OCCURRED,
                                   billed_codes=("97110",)) for i in range(used))
        verdict, why = t2.triage_pending("P-77", "PT", D + timedelta(days=day))
        print(f"    {label:<22} {used:>2} used, {t2.remaining('AUTH-8802'):>2} left"
              f"   →  {verdict.value.upper()}")
        print(f"      {why}")
    t.set_documents("P-77", ())
    verdict, why = t.triage_pending("P-77", "PT", D + timedelta(days=60))
    print(f"\n    documentation missing        →  {verdict.value.upper()}")
    print(f"      {why}\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("selftest", "demo", "triage"), nargs="?", default="selftest")
    a = p.parse_args()
    if a.cmd == "selftest":
        sys.exit(selftest())
    if a.cmd == "demo":
        demo()
    else:
        triage_demo()


if __name__ == "__main__":
    main()
