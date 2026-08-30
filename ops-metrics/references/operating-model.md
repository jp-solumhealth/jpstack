# Operating Model — Routing, Assignment, and WIP

## The assignment question

The intuitive move when a queue runs late is to **give every account a named
worker**. It feels like accountability. In queueing terms it is the opposite: it
converts one fast pooled queue into many slow private ones.

### Why dedicating workers to accounts backfires

1. **Check the arithmetic first.** Dedicated coverage is only available when
   accounts are few relative to staff. Divide live accounts by case-working
   staff before anything else — the answer is often five or ten accounts each,
   which is not dedication, just fragmentation.
2. **Pooling loss.** Account arrivals are lumpy and independent. In a pooled
   queue, one worker's quiet morning absorbs another's spike. In dedicated
   queues that slack is stranded — someone idles while someone else is twenty
   cases deep. Simulated at equal capacity, dedicated assignment roughly
   **quadruples p90 age and doubles the backlog** versus pooling.
3. **Single points of failure.** One person out sick takes all of their
   accounts' SLA down with them, because nobody else knows those accounts.
4. **It optimizes the wrong axis.** In payer-facing work, handle time is driven
   by the **payer** — portal availability, hold times, plan rules — not by the
   client. Account specialization buys familiarity with intake quirks (minutes).
   Payer specialization buys portal access and script fluency (tens of minutes).

### Separate the two jobs the instinct is bundling

| Job | Structure |
|---|---|
| **Owning the relationship** | One named **account owner**: escalations, expectation-setting, the weekly note. This is the accountability the instinct is reaching for, and it costs no queue capacity. |
| **Doing the work** | One **pooled queue**, worked in deadline order, with **payer/channel specialization** layered on top. |

So: **pool the work, name the owner, specialize by payer.**

### The hidden reason per-account assignment keeps getting proposed

Usually it is because **each account wants a different output** — which fields,
in-network only, place of service, which service types. That knowledge lives in
individual workers' heads, which is what makes dedicating them feel necessary.

**Encode it in the platform as a per-account output template instead.** Written
down once, any worker can serve any account — which is the precondition that
makes pooling work at all. Chasing it with staffing instead of configuration
guarantees the fragmentation above.

---

## Routing

Classify every item at intake, automatically, before a human sees it:

1. **Channel** — self-service (portal/EDI) vs phone-only. Self-service work is
   several times faster; it should never sit behind a phone case in the same
   person's day.
2. **Payer** — routes to whoever holds that portal credential and script.
3. **Complexity** — standard / secondary coverage / out-of-network / exceptions.
4. **Deadline** — derived from arrival time and the SLA commitment.

### Work in this order
Deadline first, then age, then complexity. **Never** by "easiest available" —
that is the mechanism that leaves months-old items open while the daily numbers
look fine.

## Batching

Phone work should be **batched by payer**, not interleaved. One hold queue,
several cases in the same session, is the difference between 45 minutes per case
and 45 minutes for three. Respect payer office hours and time zones when
scheduling the blocks — a call placed before the payer opens is pure hold time.

## WIP limits

Cap concurrent in-progress items per worker (start at 3). Unlimited WIP is why
items get marked "in progress" and then age, and it is the direct cause of the
most common defect class in this kind of operation: **items marked complete that
were never done**, closed to clear a crowded board.

## Daily rhythm

| When | What |
|---|---|
| Start of day | Queue is already ordered by deadline. No manual hand-assignment. |
| Mid-morning | Self-service block — highest-throughput window, clear the fast lane |
| Midday | Batched phone block, grouped by payer, at best answer-rate hours |
| End of day | Anything at risk of breaching overnight is flagged and owned, not left |

If a lead is spending the day routing work by hand, that is roughly a full
worker of capacity going into a job a deadline-ordered queue does for free.

## Escalation triggers

Automatic, not discretionary:

- item crossing 80% of its SLA clock → surfaces to the ops manager
- item crossing 2x the SLA → surfaces to the account owner **before** the client notices
- automation failure rate above 15% for a day → engineering ticket, same day
- checks-per-unit above 2.0 for any account → retry storm, stop and fix

Every one of these exists so the operator sees the miss before the client does.
The alternative is learning about it from a client who was keeping count.
