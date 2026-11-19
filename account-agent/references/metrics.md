# Account agent: metric dictionary

The confirmed list of metrics the account agent computes, with one definition, formula, grain,
source and threshold for each. `SKILL.md` uses these names. Thresholds here override any
older copy elsewhere.

**Status legend:**
- `defined`: agreed, but not yet mapped to a source.
- `mapped`: the source table and columns are known.
- `verified`: the computed value matches a known reality check (see the end of this file).

Grain is **per client per day** unless stated. "Client" means the paying account in the
registry (`cs.clients.client_id`), never a patient. No metric reads or stores patient-level
data. Every product metric comes from aggregate views.

## Placeholders to resolve when mapping the product database

| Placeholder | Meaning |
|---|---|
| `<requests>` | One row per verification / prior-auth / check request |
| `<requests>.client_id` | Owning client (organization / tenant) |
| `<requests>.created_at`, `.completed_at` | Request received, result delivered |
| `<requests>.type` | VOB, PA, eligibility, monitoring … |
| `<requests>.status` | Final status (completed, failed, cancelled …) |
| `<requests>.touched_by_human` | Whether a person worked it (or derive from an events table) |
| `<requests>.rework` | Whether it was reopened or corrected after delivery |
| `<users>` | Client-side users, joined to `client_id`, with `last_sign_in_at` (Supabase Auth) |
| `<invoices>` | Billing system invoices: client, amount, issued_at, due_at, paid_at |

---

## A. Value delivered

| ID | Metric | Formula | Amber | Red | Source | Status |
|---|---|---|---|---|---|---|
| A1 | Turnaround p50 / p90 (hours) | percentile of `completed_at − created_at` over completed requests, trailing 7 days | p90 over SLA for 1 week | p90 over SLA 2 weeks running | product | defined |
| A2 | Accuracy (error rate) | requests with `rework` ÷ completed, trailing 30 days | > 2% | > 5% | product | defined |
| A3 | Hands-off rate | completed with `touched_by_human = false` ÷ completed, trailing 7 days | falling 2 weeks | falling 4 weeks | product | defined |
| A4 | Time to first value (days) | first `completed_at` for the client − signature date | > 14 | > 30 | product + contract | defined |
| A5 | ROI to client | hours saved = completed × minutes-per-manual-task ÷ 60; plus denials avoided where known | not computed | client cannot state it | product + assumptions | defined |

## B. Usage (the earliest warning)

| ID | Metric | Formula | Amber | Red | Source | Status |
|---|---|---|---|---|---|---|
| B1 | Volume vs baseline | requests this 7 days ÷ (trailing 28 days ÷ 4) | < 0.8 | < 0.6, or 0 for 5 business days | product | defined |
| B2 | Days since last request | today − max(`created_at`) | > 3 business days | > 5 business days | product | defined |
| B3 | Active users (14 days) | client users with `last_sign_in_at` in the last 14 days | 1 | 0 | Supabase Auth | defined |
| B4 | Footprint | locations / practices / NPIs live ÷ total known | — | shrinking | product + brief | defined |
| B5 | Product mix | request types used ÷ types contracted | below contracted | — | product + contract | defined |
| B6 | Volume vs contractual minimum | monthly billable units × unit price ÷ monthly minimum | < 1.0 | < 0.5 | product + contract | defined |

## C. Relationship

| ID | Metric | Formula | Amber | Red | Source | Status |
|---|---|---|---|---|---|---|
| C1 | Client reply latency | median hours from our email to their reply, trailing 30 days | doubled vs baseline | no reply to 2 follow-ups | Gmail | defined |
| C2 | Contacts engaged | distinct client people who emailed or joined a call in 30 days | 1 | 0 | Gmail, calls | defined |
| C3 | Days since meaningful touch | days since last call, business review or substantive reply | > 21 (Tier 1) | > 45 | calls, Gmail | defined |
| C4 | Open escalations | unresolved complaints / escalations | 1 | 2+, or a repeated theme | Gmail, Slack, tickets | defined |
| C5 | Champion status | role change / departure of the main contact | role change | left | CRM, external | defined |

## D. Commercial

| ID | Metric | Formula | Amber | Red | Source | Status |
|---|---|---|---|---|---|---|
| D1 | Billing started | first invoice exists by the contractual due date | — | due date passed, no invoice | billing + contract | defined |
| D2 | Days late | today − `due_at` for the oldest unpaid invoice | > 7 | > 30, or disputed | billing | defined |
| D3 | Days to notice window | non-renewal notice deadline − today | < 120 | < 60 and health not green | contract | defined |
| D4 | Commercial terms on paper | signed order has tier, minimum and fees | — | missing | contract | defined |

## E. External

| ID | Metric | Signal | Amber | Red | Source | Status |
|---|---|---|---|---|---|---|
| E1 | Champion job change | profile shows new employer or title | title change | left | people data | defined |
| E2 | Acquisition / roll-up | news or registry | announced | closed | web | defined |
| E3 | Insourcing signal | job posts for verification / billing / auth staff | 1 post | 2+ posts | jobs data | defined |
| E4 | Expansion signal | new location or provider announced | — (green signal) | — | web | defined |

---

## Health score

```
score = 100 − Σ over groups A–E of min(30, 5 × ambers + 15 × reds)
band  = Green ≥ 75 · Amber 50–74 · Red < 50
```

**Forced Red, regardless of score:**
- contract gate failed (D4)
- BAA missing or its chain is incomplete
- zero volume for 10 business days after go-live
- champion left (C5)
- notice of termination received
- signed but not live after 30 days (A4 with no first value)

Starting churn probability per band, refitted monthly from outcomes: Green 0.05 · Amber 0.25 ·
Red 0.6.

## Portfolio metrics (monthly)

| Metric | Formula |
|---|---|
| Gross revenue retention | revenue this month from clients active 12 months ago, contraction and churn only ÷ their revenue 12 months ago |
| Net revenue retention | same cohort including expansion ÷ their revenue 12 months ago |
| Logo churn | clients lost this month ÷ clients at start of month |
| Time to first value | median A4 over clients signed in the period |
| Signed but not live | count of clients past signature with no first value |
| Expansion revenue | revenue increase from existing clients |

## Agent quality and loop metrics (weekly)

| Metric | Formula | Target |
|---|---|---|
| Approval rate | approved ÷ drafted actions | ≥ 60% in pilot, rising |
| Edit rate | edited ÷ approved | falling week over week |
| False-red rate | clients flagged Red that a human rates healthy | < 10% |
| Calibration | predicted churn probability per band vs realized, monthly | within ±10 pts |
| Mistake-to-lesson time | hours from a rejected or edited draft to an approved lesson | < 24 h |
| Cost per account | model spend per client per month ÷ that client's retained + expansion revenue | tracked |

---

## Reference SQL (aggregate views; schema `cs`)

These are templates. Replace the placeholders after mapping the schema. The agent's database
role may read only `cs.*`.

```sql
-- B1, B2: daily volume per client
create view cs.v_client_volume_daily as
select client_id,
       date_trunc('day', created_at)::date as day,
       count(*)                                        as requests,
       count(*) filter (where status = 'completed')    as completed
from <requests>
group by 1, 2;

-- A1, A3: turnaround and hands-off, trailing 7 days
create view cs.v_client_quality_7d as
select client_id,
       percentile_cont(0.5) within group (order by extract(epoch from completed_at - created_at) / 3600) as tat_p50_h,
       percentile_cont(0.9) within group (order by extract(epoch from completed_at - created_at) / 3600) as tat_p90_h,
       avg((not touched_by_human)::int)::numeric                                                       as hands_off_rate
from <requests>
where status = 'completed' and completed_at >= now() - interval '7 days'
group by 1;

-- A4: first value
create view cs.v_client_first_value as
select client_id, min(completed_at) as first_value_at
from <requests>
where status = 'completed'
group by 1;

-- B3: active users (Supabase Auth)
create view cs.v_client_active_users as
select u.client_id,
       count(*) filter (where au.last_sign_in_at >= now() - interval '14 days') as active_14d,
       max(au.last_sign_in_at)                                                   as last_login
from <users> u join auth.users au on au.id = u.auth_user_id
group by 1;
```

---

## Verification checks (how a metric moves to `verified`)

Each metric must reproduce a fact a human already knows before any agent acts on it:

1. **Signed-not-live account:** an account that signed but never sent a request must show
   B1 = 0, B2 = days since signature, A4 = no value, and band Red (forced).
2. **Known healthy account:** a client the team considers healthy must come out Green. If it
   doesn't, tune thresholds before any agent runs.
3. **Volume totals:** total requests per client for the last full month must match the
   operations report for that month within 1%.
4. **Turnaround:** A1 for one client and one week must match a manual spot check of 10 requests.
5. **Logins:** B3 for one client must match the users the team knows are active.
6. **Billing:** D1 and D2 must match the billing system for three clients picked at random.

Record each check's date and result next to the metric in the private registry. Only `verified`
metrics feed the health score. Metrics still `defined` or `mapped` show as UNKNOWN.
