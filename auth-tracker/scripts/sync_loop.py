#!/usr/bin/env python3
"""
sync_loop.py — keep the authorization dashboard on completed sessions.

Healthie owns every authorization field and is right about all of them except one:
its tracker accrues visits against a client's *scheduled and occurred* appointments.
This sweeps the panel on an interval, recomputes visits_used from occurred
appointments only, and renders the dashboard from the corrected number.

    python3 sync_loop.py once                    # one sweep, shadow mode, print dashboard
    python3 sync_loop.py once --write            # one sweep, write corrections back
    python3 sync_loop.py loop --interval 3600    # daemon; hourly by default
    python3 sync_loop.py once --json out.json    # dashboard as JSON for a UI
    python3 sync_loop.py selftest                # the contract

DEFAULTS ARE DELIBERATELY TIMID
    Shadow mode is the default. The sweep computes and reports but writes nothing
    until --write is passed. Overwriting a live authorization field across a whole
    panel on the first run is not a thing to do by accident, and the drift column
    tells you what the writes would have been.

WHY A LOOP AND NOT ONLY WEBHOOKS
    Webhooks are the fast path and should also be wired — appointment.updated is
    what makes a correction land within minutes. But Healthie's payloads carry only
    a resource id, delivery is retried rather than guaranteed-exactly-once, and a
    missed event leaves a balance silently stale. The sweep is the floor: whatever
    the events missed, the next pass repairs. Run both.
"""
from __future__ import annotations
import argparse, json, random, sys, time
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from auth_tracker import (                       # noqa: E402
    VisitAccrual, HealthieAuthorization, HealthieAppointment, FakeHealthie,
    Correction, Alert, OCCURRED,
)

# ══════════════════════════════════════════════════ PACING

class Pacer:
    """Healthie publishes no rate limit, so we impose one rather than discover
    theirs in production. Each patient costs at least two calls (authorization,
    then appointments), so a panel of 400 is ~800 calls per sweep."""

    def __init__(self, calls_per_second: float = 4.0, sleeper=time.sleep) -> None:
        self.min_gap = 1.0 / calls_per_second if calls_per_second > 0 else 0.0
        self._last = 0.0
        self._sleep = sleeper
        self.waited = 0.0

    def wait(self, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        gap = now - self._last
        if self._last and gap < self.min_gap:
            self._sleep(self.min_gap - gap)
            self.waited += self.min_gap - gap
        self._last = time.monotonic() if now is None else now


def backoff_delays(attempts: int = 4, base: float = 2.0, jitter: bool = True):
    """2s, 4s, 8s, 16s with jitter. Reads are safe to retry; the writeback is not
    retried here — see the idempotency note in sync()."""
    for i in range(attempts):
        d = base * (2 ** i)
        yield d * (0.5 + random.random() / 2) if jitter else d


# ══════════════════════════════════════════════════ SWEEP

@dataclass
class Row:
    patient_id: str
    patient_name: str
    authorization_number: str
    approved: int
    healthie_said_used: int
    actually_used: int
    left: int
    drift: int
    booked_not_delivered: int
    overbooked_by: int
    end_date: str
    days_to_expiry: int
    alerting: bool
    referral_missing: bool
    written: bool

    @property
    def urgency(self) -> tuple:
        """Sort key: alerting first, then fewest visits left, then soonest expiry."""
        return (not self.alerting, self.left, self.days_to_expiry)


@dataclass
class SweepResult:
    started: str
    finished: str
    rows: list[Row]
    failures: list[tuple[str, str]]
    wrote: int
    shadow: bool

    @property
    def alerts(self) -> list[Row]:
        return [r for r in self.rows if r.alerting]

    @property
    def overbooked(self) -> list[Row]:
        return [r for r in self.rows if r.overbooked_by > 0]

    @property
    def total_drift(self) -> int:
        return sum(r.drift for r in self.rows)


class PanelSweep:
    def __init__(self, client, panel, *, write: bool = False, threshold: int = 3,
                 pacer: Pacer | None = None, on_alert=None) -> None:
        self.client = client
        self.panel = panel              # iterable of (patient_id, display_name)
        self.write = write
        self.accrual = VisitAccrual(client, threshold=threshold)
        self.pacer = pacer or Pacer()
        self.on_alert = on_alert or (lambda alert, row: None)

    def run(self, today: date | None = None) -> SweepResult:
        today = today or date.today()
        started = datetime.now().isoformat(timespec="seconds")
        rows: list[Row] = []
        failures: list[tuple[str, str]] = []
        wrote = 0

        for patient_id, name in self.panel:
            self.pacer.wait()
            try:
                # One patient's bad data must not end the sweep. A panel-wide abort
                # on a single malformed record is how a nightly job silently stops
                # reporting for everyone.
                correction, alert = self.accrual.sync(patient_id, write=self.write)
                auth = self.client.authorization(patient_id)
                over = self.accrual.overbooked_by(patient_id)
            except LookupError:
                continue                      # no authorization on file; not an error
            except Exception as exc:          # noqa: BLE001 — deliberate isolation
                failures.append((patient_id, f"{type(exc).__name__}: {exc}"))
                continue

            row = Row(
                patient_id=patient_id,
                patient_name=name,
                authorization_number=auth.authorization_number,
                approved=auth.number_of_visits,
                healthie_said_used=correction.healthie_visits_used,
                actually_used=correction.corrected_visits_used,
                left=correction.corrected_visits_left,
                drift=correction.drift,
                booked_not_delivered=correction.scheduled_not_occurred,
                overbooked_by=over,
                end_date=auth.end_date.isoformat(),
                days_to_expiry=(auth.end_date - today).days,
                alerting=alert is not None,
                referral_missing=bool(alert and alert.referral_missing),
                written=correction.written,
            )
            rows.append(row)
            wrote += 1 if correction.written else 0
            if alert:
                self.on_alert(alert, row)

        rows.sort(key=lambda r: r.urgency)
        return SweepResult(
            started=started,
            finished=datetime.now().isoformat(timespec="seconds"),
            rows=rows, failures=failures, wrote=wrote, shadow=not self.write,
        )


# ══════════════════════════════════════════════════ DASHBOARD

def render(result: SweepResult, *, limit: int = 40) -> str:
    if not result.rows and not result.failures:
        return "  No authorizations on file for this panel.\n"

    w = "SHADOW — nothing written" if result.shadow else f"{result.wrote} corrected"
    out = [
        "",
        f"  AUTHORIZATION DASHBOARD — counted on completed sessions",
        f"  {result.finished}   {len(result.rows)} authorizations   {w}",
        "",
        f"  {'PATIENT':<20} {'AUTH':<12} {'APPR':>4} {'USED':>5} {'LEFT':>5} "
        f"{'DRIFT':>6} {'BOOKED':>7} {'EXPIRES':>9}",
        f"  {'-' * 20} {'-' * 12} {'-' * 4} {'-' * 5} {'-' * 5} {'-' * 6} {'-' * 7} {'-' * 9}",
    ]
    for r in result.rows[:limit]:
        flag = "!" if r.alerting else (">" if r.overbooked_by else " ")
        drift = f"{r.drift:+d}" if r.drift else "·"
        out.append(
            f"{flag} {r.patient_name[:20]:<20} {r.authorization_number[:12]:<12} "
            f"{r.approved:>4} {r.actually_used:>5} {r.left:>5} {drift:>6} "
            f"{r.booked_not_delivered:>7} {r.days_to_expiry:>7}d"
        )
    if len(result.rows) > limit:
        out.append(f"  … {len(result.rows) - limit} more")

    out.append("")
    if result.alerts:
        out.append(f"  ! {len(result.alerts)} need reauthorization now "
                   f"(≤3 visits left):")
        for r in result.alerts[:10]:
            ref = "  — referral missing" if r.referral_missing else ""
            out.append(f"      {r.patient_name} · {r.authorization_number} · "
                       f"{r.left} left{ref}")
    if result.overbooked:
        out.append(f"  > {len(result.overbooked)} booked beyond the authorization:")
        for r in result.overbooked[:10]:
            out.append(f"      {r.patient_name} · {r.overbooked_by} visits over "
                       f"· not yet delivered")
    if result.total_drift:
        out.append(f"")
        out.append(f"  Healthie over-counted by {result.total_drift} visits across "
                   f"the panel — scheduled appointments it had already deducted.")
    if result.failures:
        out.append(f"")
        out.append(f"  {len(result.failures)} patient(s) could not be read:")
        for pid, err in result.failures[:5]:
            out.append(f"      {pid}: {err}")
    out.append("")
    return "\n".join(out)


def to_json(result: SweepResult) -> str:
    return json.dumps({
        "started": result.started, "finished": result.finished,
        "shadow": result.shadow, "wrote": result.wrote,
        "total_drift": result.total_drift,
        "alerting": len(result.alerts), "overbooked": len(result.overbooked),
        "rows": [asdict(r) for r in result.rows],
        "failures": [{"patient_id": p, "error": e} for p, e in result.failures],
    }, indent=2)


# ══════════════════════════════════════════════════ THE LOOP

def loop(sweep: PanelSweep, *, interval: float = 3600.0, max_iterations: int | None = None,
         sleeper=time.sleep, printer=print) -> list[SweepResult]:
    """Sweep, report, wait, repeat. A failed sweep backs off and retries rather than
    exiting — a dashboard that stops updating silently is worse than a stale one,
    so every outcome is reported."""
    results, n = [], 0
    while max_iterations is None or n < max_iterations:
        n += 1
        try:
            r = sweep.run()
            results.append(r)
            printer(render(r))
        except Exception as exc:              # noqa: BLE001
            printer(f"  sweep failed: {type(exc).__name__}: {exc}")
            for d in backoff_delays():
                sleeper(d)
                try:
                    r = sweep.run()
                    results.append(r)
                    printer(render(r))
                    break
                except Exception:             # noqa: BLE001
                    continue
        if max_iterations is None or n < max_iterations:
            sleeper(interval)
    return results


# ══════════════════════════════════════════════════ SELF-TEST

def _panel(n_patients=3, *, approved=10, occurred=6, scheduled=8):
    D = date(2026, 9, 1)
    clients, panel = {}, []
    for i in range(n_patients):
        pid = f"P{i}"
        auth = HealthieAuthorization(
            id=f"IA-{i}", patient_id=pid, authorization_number=f"AUTH-{4000 + i}",
            number_of_visits=approved, visits_used=0,
            start_date=D, end_date=D + timedelta(days=90 - i * 12))
        appts = []
        for k in range(occurred):
            appts.append(HealthieAppointment(f"o{i}-{k}", D + timedelta(days=k), OCCURRED))
        for k in range(scheduled):
            appts.append(HealthieAppointment(f"s{i}-{k}", D + timedelta(days=30 + k), "Scheduled"))
        c = FakeHealthie(auth, appts)
        auth.visits_used = c.healthie_native_count()
        clients[pid] = c
        panel.append((pid, f"Patient {i}"))
    return _Router(clients), panel


class _Router:
    """Routes per-patient to that patient's fake client."""
    def __init__(self, clients): self.clients = clients
    def authorization(self, pid): 
        c = self.clients.get(pid)
        return c.authorization(pid) if c else None
    def appointments(self, pid, s, e): return self.clients[pid].appointments(pid, s, e)
    def update_visits_used(self, aid, used, left):
        for c in self.clients.values():
            if c._auth.id == aid:
                return c.update_visits_used(aid, used, left)
        return []


def selftest() -> int:
    fails = []
    def check(name, cond):
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        if not cond: fails.append(name)

    print("\n  ── the sweep ──")
    client, panel = _panel(3, approved=10, occurred=6, scheduled=8)
    res = PanelSweep(client, panel, write=False).run(today=date(2026, 9, 1))
    check("every patient in the panel produces a row", len(res.rows) == 3)
    check("counts occurred only", all(r.actually_used == 6 for r in res.rows))
    check("Healthie's number is preserved for comparison",
          all(r.healthie_said_used == 14 for r in res.rows))
    check("drift is reported per row", all(r.drift == 8 for r in res.rows))
    check("panel drift totals", res.total_drift == 24)

    print("\n  ── shadow mode is the default ──")
    check("nothing was written", res.shadow and res.wrote == 0)
    check("...and no client saw a write",
          all(c.writes == [] for c in client.clients.values()))
    res_w = PanelSweep(client, panel, write=True).run(today=date(2026, 9, 1))
    check("--write actually writes", res_w.wrote == 3 and not res_w.shadow)

    print("\n  ── urgency ordering ──")
    client, panel = _panel(1, approved=10, occurred=9, scheduled=0)
    c2, p2 = _panel(1, approved=10, occurred=2, scheduled=0)
    c2.clients["P0"]._auth.id = "IA-9"
    c2.clients["P0"]._auth.patient_id = "Q0"
    c2.clients["P0"]._auth.authorization_number = "AUTH-9999"
    client.clients["Q0"] = c2.clients["P0"]
    merged = panel + [("Q0", "Patient Q")]
    res = PanelSweep(client, merged, write=False).run(today=date(2026, 9, 1))
    check("the alerting patient sorts first", res.rows[0].patient_id == "P0")
    check("...and is flagged", res.rows[0].alerting and not res.rows[1].alerting)

    print("\n  ── one bad patient does not end the sweep ──")
    client, panel = _panel(3)
    broken = client.clients["P1"]
    broken.appointments = lambda *_a: (_ for _ in ()).throw(ValueError("bad page cursor"))
    res = PanelSweep(client, panel, write=False).run(today=date(2026, 9, 1))
    check("the other two still report", len(res.rows) == 2)
    check("the failure is recorded, not swallowed", len(res.failures) == 1)
    check("...with the patient and the reason",
          res.failures[0][0] == "P1" and "bad page cursor" in res.failures[0][1])

    print("\n  ── a patient with no authorization is skipped, not failed ──")
    client, panel = _panel(2)
    panel.append(("P-none", "No Auth"))
    res = PanelSweep(client, panel, write=False).run(today=date(2026, 9, 1))
    check("no row and no failure", len(res.rows) == 2 and res.failures == [])

    print("\n  ── over-booking surfaces on the dashboard ──")
    client, panel = _panel(1, approved=10, occurred=0, scheduled=20)
    res = PanelSweep(client, panel, write=False).run(today=date(2026, 9, 1))
    check("20 booked against 10 authorized is flagged", res.rows[0].overbooked_by == 10)
    check("...before a single visit was delivered", res.rows[0].actually_used == 0)
    check("it appears in the rendered dashboard", "booked beyond" in render(res))

    print("\n  ── pacing ──")
    slept = []
    p = Pacer(calls_per_second=2.0, sleeper=slept.append)
    p.wait(now=100.0); p.wait(now=100.1)
    check("a too-fast second call is paced", slept and slept[0] > 0)
    check("backoff grows and is bounded",
          len(list(backoff_delays())) == 4 and
          list(backoff_delays(jitter=False)) == [2.0, 4.0, 8.0, 16.0])

    print("\n  ── the loop ──")
    client, panel = _panel(2)
    sweeps, sleeps = [], []
    res_list = loop(PanelSweep(client, panel), interval=3600, max_iterations=3,
                    sleeper=sleeps.append, printer=sweeps.append)
    check("runs the requested number of sweeps", len(res_list) == 3)
    check("sleeps between sweeps but not after the last", len(sleeps) == 2)
    check("...for the configured interval", sleeps == [3600, 3600])

    print("\n  ── a failing sweep backs off instead of exiting ──")
    class Flaky:
        def __init__(self): self.n = 0
        def run(self, today=None):
            self.n += 1
            if self.n == 1: raise ConnectionError("502 from Healthie")
            return SweepResult("s", "f", [], [], 0, True)
    out, sl = [], []
    res_list = loop(Flaky(), interval=10, max_iterations=1, sleeper=sl.append, printer=out.append)
    check("the failure is reported", any("sweep failed" in str(o) for o in out))
    check("...and the retry succeeds", len(res_list) == 1)
    check("...after backing off", any(s > 1 for s in sl))

    print("\n  ── JSON output ──")
    client, panel = _panel(2)
    res = PanelSweep(client, panel, write=False).run(today=date(2026, 9, 1))
    parsed = json.loads(to_json(res))
    check("serialises every row", len(parsed["rows"]) == 2)
    check("carries the drift a reviewer needs", parsed["total_drift"] == 16)
    check("declares it was a shadow run", parsed["shadow"] is True)

    print()
    if fails:
        print(f"  {len(fails)} FAILED: " + "; ".join(fails)); return 1
    print("  ALL PASS"); return 0


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("cmd", choices=("once", "loop", "selftest"), nargs="?", default="selftest")
    p.add_argument("--write", action="store_true",
                   help="write corrections back to Healthie (default: shadow)")
    p.add_argument("--interval", type=float, default=3600.0, help="seconds between sweeps")
    p.add_argument("--threshold", type=int, default=3, help="alert at this many visits left")
    p.add_argument("--rate", type=float, default=4.0, help="max API calls per second")
    p.add_argument("--json", metavar="PATH", help="write the dashboard as JSON")
    p.add_argument("--limit", type=int, default=40, help="rows to print")
    a = p.parse_args()

    if a.cmd == "selftest":
        sys.exit(selftest())

    # Demonstration panel. Swap _panel() for a real HealthieClient and the list of
    # patients with active authorizations.
    client, panel = _panel(6, approved=10, occurred=7, scheduled=6)
    sweep = PanelSweep(client, panel, write=a.write, threshold=a.threshold,
                       pacer=Pacer(a.rate))
    if a.cmd == "once":
        res = sweep.run()
        print(render(res, limit=a.limit))
        if a.json:
            with open(a.json, "w") as fh:
                fh.write(to_json(res))
            print(f"  wrote {a.json}\n")
    else:
        print(f"  sweeping every {a.interval:.0f}s — ctrl-c to stop")
        try:
            loop(sweep, interval=a.interval)
        except KeyboardInterrupt:
            print("\n  stopped\n")


if __name__ == "__main__":
    main()
