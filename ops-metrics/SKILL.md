---
name: ops-metrics
description: Weekly operations review for a verification or prior-auth team. Derives arrival rate, implied turnaround, aging and capacity headroom from a daily volume digest, then names the one constraint to fix this week. Use when the user says "ops metrics", "ops review", "how is the ops team doing", "VOB throughput", "why is the backlog growing", or "turnaround time".
---

# Ops Metrics

Turns a daily volume digest into a decision. Most digests report what was
*completed*. This skill derives what was *demanded*, what is *aging*, and where
the *constraint* actually sits — the three things completions cannot tell you.

## Core principle

**Completions are a lagging vanity metric. Queue dynamics are the truth.**

A team completing 65 cases a day looks healthy until you notice 67 arrived. That
gap is invisible on every daily report and compounds silently into a backlog —
and the backlog *is* the turnaround time.

---

## Step 1 — Pull the series

Read the daily operations digest for the period requested (default: trailing 8
weeks). Parse each day into:

| Field | Typical source line |
|---|---|
| `completed` | "VOBs: N" / cases closed |
| `carryover` | "queue carryover (open from before today)" |
| `pa_created` / `submitted` / `decided` / `backlog` | prior-auth funnel |
| `automation_handsoff_pct` | share needing no human touch |
| `automation_failure_pct` | attempted automated checks that got no answer |

Guard rails that matter more than they look:

- **Never interpolate a missing day.** Leave it blank and note the gap.
- **Drop duplicate re-posts** of the same date, and check whether they agree —
  if a re-post disagrees, the field is a live snapshot, not a daily close, and
  everything derived from it is directional only.
- **Exclude holidays and zero-volume days** from weekday averages, or you will
  invent a Monday problem that is really a holiday.
- **Never mix metric definitions across a format change.** If the digest changed
  how it measures automation, treat the two eras as separate series.
- **Distrust tiny cohorts.** A day showing 0% or 100% is usually n=1.

## Step 2 — Derive what nobody is reporting

```
arrivals(t)  = completed(t) + [carryover(t+1) - carryover(t)]
net_queue(t) = arrivals(t) - completed(t)
implied_TAT  = carryover / completed_per_day          # Little's Law, in days
utilization  = (arrivals x avg_handle_time) / (case_workers x productive_minutes)
```

`implied_TAT` is the honest turnaround number and it needs no new tooling. If
carryover is 100 and the team finishes 65/day, the queue is already 1.5 days
deep — a sub-24h SLA is arithmetically out of reach no matter what any single
case's timestamps say.

Report each against the prior week and the trailing 4-week average.

## Step 3 — Locate the constraint

Walk these in order and stop at the first that binds:

1. **Utilization above ~85%** → capacity. Queueing is non-linear; past 85% the
   wait-time curve goes vertical. No assignment cleverness fixes this — only
   more capacity or less handle time.
2. **Channel mix** → self-service portal and EDI work runs several times faster
   than phone work. Portal share is usually the largest lever on capacity, and
   it is gated by credentials and integrations, not by effort.
3. **Quota ceiling** → if per-worker counts cluster exactly *at* the minimum
   rather than spreading around it, the floor has become a ceiling. Check the
   distribution, never the mean.
4. **Automation failure rate** → every failed automated check becomes unplanned
   manual work. Also check *checks per unit*: above ~2.0 is a retry storm
   burning capacity against a wall.
5. **Rework** → defects re-enter the queue as new work and cost client trust
   twice. Rework is demand in disguise.

## Step 4 — Aging, not averages

Averages hide the tail that generates escalations. Always report:

- open >24h, open >72h, open >7d
- the single oldest open item — **by name and account**, not just a count
- any account whose pending rate exceeds 3%

Anything that can be counted but not named will be ignored.

## Step 5 — Output

Produce a one-screen review:

1. **The number that matters this week** — one sentence naming the binding constraint.
2. **Scorecard** — arrivals, completions, net queue, implied TAT, same-day %,
   aging buckets, automation hands-off/failure, first-pass yield, with trends.
3. **Three actions** — specific, owned, sized. Not "improve throughput."
4. **Watch list** — accounts or payers trending toward escalation.

Say plainly which figures are measured and which are derived. Apply the
`solum-health-brand` design system when rendering to HTML or PDF.

## References

- `references/metric-definitions.md` — definition, target and owner per metric
- `references/operating-model.md` — routing, assignment and WIP rules
