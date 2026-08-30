# Metric Definitions

The rule: **every metric names an owner, a target, and a decision it drives.**
A metric that changes nothing when it moves is reporting, not management.

---

## Tier 1 — Turnaround (the metric clients actually buy)

| Metric | Definition | Target | Why |
|---|---|---|---|
| Same-day completion % | closed on the calendar day it arrived, for items arriving before the daily cutoff | **60%** | Set it to whatever same-day share was actually promised to clients |
| % completed < 24h | closed within 24h of arrival | **95%** | The contracted SLA — an SLA hit 80% of the time is not an SLA |
| p90 turnaround | 90th percentile arrival→close | **< 24h** | Averages hide escalations; the p90 is what a client feels |
| Implied TAT | `carryover / completions_per_day` | **< 1.0 day** | Derivable from any digest that reports carryover, with no new tooling |

**Measure from arrival, not from first touch.** Time-to-first-touch is a
comfortable metric that lets a queue rot while looking responsive.

## Tier 2 — Flow (the leading indicators)

| Metric | Definition | Target | Why |
|---|---|---|---|
| Arrival rate | `completions + Δcarryover` | tracked | The demand signal nobody is currently measuring |
| Net queue change | `arrivals − completions`, daily | **≤ 0 weekly** | A positive weekly net is a backlog forming, visible weeks before the escalation |
| Queue carryover | open items from prior days | **< 1 day of capacity** | Already instrumented |
| Utilization | `arrivals × avg handle time / available case-minutes` | **70-85%** | Above 85%, wait times go non-linear. This is physics, not effort |

## Tier 3 — Aging (where churn is born)

| Metric | Target |
|---|---|
| Open > 24h | < 5% of open |
| Open > 72h | **0** |
| Oldest open item | **< 5 days** |
| Per-client pending rate | **< 3%** |

Report the oldest item **by name and client**, every day. Anything that can be
counted but not named will be ignored.

## Tier 4 — Quality (rework is invisible demand)

| Metric | Definition | Target |
|---|---|---|
| First-pass yield | closed correct, no client correction | **> 97%** |
| Rework rate | items reopened or corrected after close | **< 3%** |
| Defect mix | wrong copay / DED / OOP / auth / network status | tracked |
| False-complete rate | marked complete but not done | **0** |

A defect costs the handle time twice **and** a unit of client trust once. Weight
it accordingly — one defect is worth roughly three clean cases in impact.

## Tier 5 — Automation (free capacity, or a silent tax)

| Metric | Target |
|---|---|
| Hands-off rate | **> 85%** |
| Automation failure rate | **< 10%** |
| Checks per unit | **< 2.0** (above this is a retry storm) |
| Manual fallback minutes/day | tracked — this is the true cost of automation failure |

Every automated check that fails silently becomes an unbudgeted manual case.
Failure rate is a *capacity* metric, not an engineering metric.

## Tier 6 — Capacity & people

| Metric | Definition | Note |
|---|---|---|
| Handle time by channel | median minutes, portal vs phone | The single biggest capacity lever |
| Handle time by payer | median minutes, per payer | Drives routing and the per-payer TAT commitment |
| Portal share | % of VOBs completed via portal | Raising this raises capacity more than hiring does |
| Occupancy | case-minutes / paid minutes | 70-85%; sustained >85% causes attrition |
| Throughput per rep | completions/rep/day | **Diagnostic only — never a target.** See below |

---

## On quotas

A per-rep volume quota is the most tempting and most damaging metric in this set.

- As a **floor**, it punishes reps holding the hardest payer queues — the phone
  cases nobody else wants — and pushes them to cherry-pick easy work.
- As a **ceiling**, it caps the reps who found leverage. When per-rep counts
  cluster exactly at the minimum rather than spreading around it, the quota has
  stopped measuring and started capping.

Check the **distribution** every week. Clustering at the number is the tell.

Better: hold the team accountable to **SLA attainment and first-pass yield**,
and hold the *system* accountable to throughput. Individual volume becomes a
coaching input, normalized by channel and payer difficulty — never a public
leaderboard.
