---
name: account-agent
description: >
  One dedicated agent per client, from signature to renewal. Its single goal is to maximize the
  client's lifetime value: keep them from churning, get them to first value fast, and grow volume,
  locations and products. On signature it builds the account from scratch (contract and BAA check,
  client folder, account brief, stakeholder map, baseline metrics, onboarding plan). After that it
  runs on a cadence, watches every metric and signal on the client side, updates the account's
  memory and drafts the next action for approval. Use when a deal is signed or moves to closed won,
  a DocuSeal proposal or BAA is completed, or when the user says "account agent", "set up the
  client", "new client signed", "client health", "is [client] at risk", "how is [client] doing",
  "maximize LTV", "churn risk", "renewal", "expansion", or "portfolio review".
---

# Account Agent

One engine, run once per client. Each client gets its own memory (the **Account Brief**) and its
own loop:

> read new data → update the brief → check stage gates and health rules → draft the next action →
> human approves → log the result

**The agent owns an outcome, not a script.** Its long-term goal is the client's lifetime value.
The steps below are what it must *know* and the *brakes* it must respect, not a workflow to replay.
Within the brakes it chooses its own strategy for the account. Workflows cap a smart model: every
model upgrade should make the agent better, not bump into steps someone hard-coded.

The agent is obsessive by design. Nothing on the client side is too small to record: a slower
reply, a new location, a payer that keeps failing, a champion who changed jobs, an invoice paid
late. The brief is where all of that accumulates, so that the next run (and the next person)
starts from everything that is known.

## Hard rules

1. **Client data never goes in this repo.** The brief, the folder and every number live in the
   client's Drive folder (or `jpstack-private`). This file holds only the method. Use placeholders
   like `[Client]` in anything committed.
2. **No PHI in the agent's context.** Read aggregate counts only (cases per day, turnaround,
   automation rate). If a source holds patient-level rows, count them and move on. Never copy names,
   DOBs or member IDs into the brief.
3. **Nothing reaches the client without approval.** The agent drafts emails, invites and messages
   to an approval queue (Slack DM or Gmail draft). It never sends. It never edits CRM stages or
   moves shared folders without the user saying so; it lists the fix instead.
4. **Never guess.** Every fact in the brief carries its source and date. Unknown is written as
   `UNKNOWN`, and every UNKNOWN that matters becomes a question in the next action.
5. **Rules, not vibes, for health.** The health score is computed from the thresholds below, so it
   is explainable and stable. The LLM reads unstructured text (calls, emails) and turns it into
   facts; it does not invent the score.

---

## Triggers

| Trigger | Mode | Detected by |
|---|---|---|
| **Client signs** (primary) | `init` | HubSpot deal enters the closed-won stage, **or** a DocuSeal email "`Proposal … has been completed by`" arrives, **or** the user says a client signed |
| Daily / weekly cadence | `run` | Scheduled task, tiered: Tier 1 daily, Tier 2 and 3 weekly |
| Material event | `run` | Volume drop, SLA miss streak, escalation email, champion job change, late invoice |
| "How are my clients doing" | `portfolio` | User request, or Monday scheduled run |

The signature trigger is a scheduled task that runs every morning, looks for deals that reached
closed won (or DocuSeal proposal completions) since the last run, and runs `init` for every client
that has no Account Brief yet. A client with a brief is never re-initialized; it gets `run`.

---

## Mode `init`: build the account from scratch

Run all ten steps. Do the research in parallel (subagents for contract, comms/CRM, external) and
write the brief yourself.

### 1. Identify the account
Resolve one canonical record: legal entity name, DBA, HubSpot company id, deal id, primary contact,
Drive folder id. Flag mismatches (deal with no company record, contact on a personal email domain,
entity name on the contract different from the CRM name).

### 2. Contract gate (blocking)
Read every signed document in full. Extract into the brief, with exact clause quotes for anything
that matters:

- **Services in scope** and anything explicitly out of scope
- **Commercial terms**: unit prices, minimums, setup fees, volume tiers, billing frequency, payment
  terms, who receives invoices
- **Term**: start date, initial term, auto-renew, notice window, termination for convenience and
  for cause, early termination fees
- **Service levels**: turnaround, accuracy, credits, support hours, reporting obligations
- **Client obligations**: what they must provide before we can start (payer list, portal
  credentials, user list, data feed). These are the onboarding dependencies.
- **Key dates**: every date a renewal or churn agent must act on, written as `YYYY-MM-DD → event`

**BAA check.** PHI cannot flow until all of these are true. Any "no" is a red blocker:

| Check | Pass when |
|---|---|
| Executed | Signed by both parties, dated |
| Right type | Covered-entity BAA for a provider; **subcontractor** BAA when the client is itself a business associate (billing company, MSO, RCM vendor) |
| Right parties | Legal entity names match the contract and the CRM; signer has authority |
| Upstream chain | For a subcontractor BAA: the client has BAAs with the practices whose PHI they will send |
| Core terms | Breach notice window, flow-down to our subcontractors, return or destruction of PHI at end |
| Filed | Both signed PDFs sit in `01 Contract & Compliance` |

Also confirm a master agreement exists if the BAA or proposal refers to one. A proposal alone is a
weak contract: note what it does not cover.

### 3. Folder
Every client folder has the same shape, so an agent (or a new hire) can find anything:

```
[Client]/
  00 Account Brief            ← Google Doc, the agent's memory (see template below)
  01 Contract & Compliance/   ← signed proposal/MSA, BAA, amendments, W-9, COI
  02 Onboarding/              ← RFI, kickoff recording and notes, payer and CPT lists, access log
  03 Meetings & Comms/        ← call notes and summaries, QBR decks
  04 Metrics & Reports/       ← monthly usage and SLA reports, ROI one-pagers sent to the client
  05 Billing/                 ← invoices, payment history, disputes
  99 Archive/
```

Create what is missing. Moving files that other people own, or moving the client folder between
`Active` / `Inactive`, is a proposed change for the user to approve.

### 4. Stakeholder map
For each person: name, role, decision power (economic buyer / champion / user / blocker), contact
channel, last touch, sentiment, what they personally care about. One contact is a red flag in itself.

### 5. What they bought, in their words
From the sales calls and emails: the pain, why now, what success looks like for them in 90 days,
the volume they expect, the systems they use, who else they evaluated, and every promise we made.
Promises go into the open-loops list with an owner and a date.

### 6. Opportunity map (whitespace)
Current scope versus full potential: locations, providers, practices (for a billing company or
MSO, **each practice they serve is a separate expansion unit**), products not yet sold, payers not
yet covered. Write an estimated full-potential value as a range with its assumptions, and mark
facts versus estimates.

### 7. External signals
Company footprint (registry, website, reviews, headcount, job posts), the champion's background,
acquisition or roll-up news. Set watches for champion job change and hiring of verification or
billing staff (growth, or a sign they plan to bring the work in-house).

### 8. Baseline metrics
Record day-0 values for every metric in the next section, even when the value is zero or UNKNOWN.
The baseline is what every later run compares against.

### 9. Onboarding plan with dates
Turn client obligations and our setup work into a dated checklist ending at **first value**. Each
item gets an owner. Default stall rules: any item idle for more than 5 business days is amber,
more than 10 is red.

### 10. HubSpot hygiene list
Stage matches reality, company record exists and is associated, all contacts associated, close
date equals signature date, amount equals contracted value, renewal date set. List the fixes;
apply them only with approval.

Output of `init`: the Account Brief, the folder, a one-screen summary for the user, and the first
drafted action.

---

## Metrics (per client, never company-wide)

**A. Value delivered.** The strongest churn predictors for an ops service.

| Metric | Definition | Amber | Red |
|---|---|---|---|
| Turnaround vs SLA | Median and p90 hours from request to result | p90 over SLA 1 week | over SLA 2 weeks running |
| Accuracy | Denials or rework caused by our result ÷ results delivered | > 2% | > 5% |
| Hands-off rate | Share completed with no human touch | falling 2 weeks | falling 4 weeks |
| ROI to client | Hours saved, denials avoided, revenue protected, in their numbers | not computed | client cannot state it |
| Time to first value | Signature → first result delivered on SLA | > 14 days | > 30 days |

**B. Usage, the earliest warning**

| Metric | Definition | Amber | Red |
|---|---|---|---|
| Volume vs baseline | This week ÷ trailing 4-week average | < 0.8 | < 0.6, or zero for 5 business days |
| Share of their volume | Our volume ÷ their total new patients or encounters | flat 8 weeks | falling |
| Footprint | Locations, practices or providers live ÷ total | — | shrinking |
| Active users | Client users active in the last 14 days | 1 user | 0 users |

**C. Relationship**

| Metric | Amber | Red |
|---|---|---|
| Their reply latency (median, trailing 30 days) | doubled vs baseline | no reply to 2 follow-ups |
| Contacts engaged | 1 | 0 in 30 days |
| Days since meaningful touch (call, QBR, real reply) | > 21 (Tier 1) | > 45 |
| Escalations and complaint themes | 1 open | 2+ open, or repeated theme |
| Champion status | role change | left the company |

**D. Commercial**

| Metric | Amber | Red |
|---|---|---|
| Invoice days late | > 7 | > 30, or disputed |
| Days to renewal or notice window | < 120 | < 60 with health not green |
| Price vs value delivered | discount above standard | client asking for price cuts |

**E. External**: champion job change, acquisition or roll-up, new locations, job posts for
billing or verification staff, competitor named in calls.

**Lagging outcomes**, reported monthly across the portfolio: gross revenue retention, net revenue
retention, logo churn, expansion revenue, gross margin per account, time to first value.

## Health score

Start at 100. Each amber costs 5 and each red costs 15, capped at 30 per group (A to E) so one bad
group cannot hide the others. **Green ≥ 75, Amber 50–74, Red < 50.** Any of these forces Red
regardless of score: contract gate failed, BAA missing, zero volume for 10 business days after
go-live, champion left, notice of termination.

## Journey stages and exit gates

| Stage | Exit gate | Default max time |
|---|---|---|
| 0 Signed | Contract gate passed, kickoff held, client obligations listed | 5 business days |
| 1 Onboarding | Access, payers, users and setup complete; first request received | 14 days |
| 2 First value | First N results delivered on SLA, ROI number shared with client | 30 days from signature |
| 3 Adoption | ≥ target share of their volume, 2+ contacts engaged, volume stable 4 weeks | 90 days |
| 4 Expansion | Next location, practice or product live | ongoing |
| 5 Renewal | Renewed or expanded; process starts 120 days before term end | — |
| 6 Advocacy | Reference, case study or referral given | — |

The agent's only job at each stage is to clear that stage's gate. When the max time passes, the
account turns amber; at twice the max time, red.

**Signed but not live** is the most dangerous state an account can be in: the client has spent
nothing on switching, so walking away costs them nothing. Treat any account still in stage 0 or 1
after 30 days as red, with the CEO as owner.

## Priority across accounts

`priority = current annual value × churn probability + expansion potential × likelihood`

Churn probability comes from the health band (Green 0.05, Amber 0.25, Red 0.6 as a starting
calibration, refit from the intervention log once there are outcomes). Tier by priority:

| Tier | Runs | Human touch |
|---|---|---|
| 1 | Daily | Weekly check-in, quarterly business review, exec sponsor on both sides |
| 2 | Weekly | Monthly |
| 3 | Weekly | Only when an alert fires |

---

## Mode `run`

1. Load the Account Brief.
2. Pull what changed since `last_run`: emails and calls with the client's domain and contacts, CRM
   activity, ops volume and SLA for the client, invoices, Slack mentions, external signals.
3. Append facts to the brief's log, each with date and source.
4. Recompute metrics against baseline and recompute the health score. Note every threshold crossed.
5. Check the current stage gate and the stall clock.
6. Choose **one** next action (the highest-leverage one) and draft it. Up to two backups.
7. Update `last_run`, the health history line and open loops.
8. Post a 5-line digest to the approval queue: health and change, what moved, the risk, the
   drafted action, what the agent needs from the user.

## Mode `portfolio`

Run `run` for every Tier 1 account, read the latest brief for the rest, rank all accounts by
priority, and return the five accounts to touch this week with the drafted action for each. Feed
the top three into `/chief-of-staff`.

## Plays library

| Situation | Play |
|---|---|
| Signed, onboarding stalled | CEO call (not email) within 48h: reconfirm their goal, remove the blocker, offer to do their obligations for them (we pull payer list, we set up users), set a go-live date on the call |
| Volume drop | Same-day check with ops for a cause on our side, then a call with the champion framed around their volume, not our revenue |
| SLA misses | Tell them before they notice: what happened, what changed, credit if the contract says so |
| Single-threaded | Ask the champion to bring their ops lead or owner to a results review |
| Champion left | Within 7 days: reach the new owner with the ROI one-pager and a reset call |
| Renewal in 120 days | Results review with ROI, then the renewal and expansion proposal in the same conversation |
| Green and growing | Ask for the next location or practice; ask for a reference |
| Billing company or MSO client | Their practices are the whitespace: map each practice, prove value on one, then roll out practice by practice |

## Self-improvement loop: how the fleet learns

One account agent getting smarter is not the goal. The goal is that **when one agent learns
something, every account agent knows it the next morning.** That takes four stores and one nightly
job.

**Stores** (all private: Drive or `jpstack-private`, never this repo)

| Store | Scope | Written by | Read by |
|---|---|---|---|
| Account Brief | One client | That client's agent | That client's agent, humans |
| Plays & lessons library | All clients | Nightly learning job (human-approved) | Every agent, every run |
| Action ledger | All clients | Every agent and the approval queue | Learning job, evals |
| Eval set | All clients | Learning job | Evals before any playbook change ships |

**Action ledger.** Every drafted action gets one row: date, client, stage, health, play used,
draft, **human decision (approved / edited / rejected)**, the edit diff and the reason, then the
outcome at 14 and 30 days. Human edits are the most valuable training signal there is. Never let
a reviewer fix a draft without the fix landing in the ledger.

**Escalation closes the loop.** When the agent is stuck (missing data, needs a call, needs a
decision), it raises `NEED HUMAN: <what, why, by when>` to the approval queue. The human resolves
it and writes one line on *how*. That line goes into the ledger. An escalation that is resolved
but not written back is a lesson the fleet will pay for again.

**Nightly learning job** (runs after all account runs)
1. Read yesterday's ledger rows, edits, rejections, escalations and every outcome that matured.
2. Cluster them: recurring edit (the agent's tone, timing or ask is wrong), recurring escalation
   (a missing tool or data source), plays that won or lost.
3. Propose changes: a new lesson, a play rewrite, a threshold change, a new data source to wire up.
4. Replay each proposed change against the eval set. Ship only changes that do not make past
   decisions worse.
5. Post the proposals for one-click approval. Approved lessons are in every agent's context the
   next morning.

Track **time from mistake to fleet-wide lesson** and drive it down. Target: under 24 hours.

### Evals: as much effort as the agent itself

Budget roughly the same time and tokens on evals as on the agent. Three questions only, per client,
per action:

| Eval | Question | Measured by |
|---|---|---|
| Advanced | Did the account move forward? | Stage gate cleared, volume up, renewal signed, expansion live |
| Value | Did the client get real value, not just a push? | SLA met, ROI number they repeat back, no complaint after the action |
| Came back | Is the relationship stronger? | They reply faster, engage more people, renew, refer |

Activity counts (emails sent, calls logged) are not evals. Two more checks keep the fleet honest:

- **Best-human benchmark.** For each play, name the best account outcome a human achieved with it
  and hold the agent to that bar. Below it, the play goes back to a human.
- **Calibration.** Each month, compare predicted churn probability per health band to what
  happened, and refit the band probabilities.

**Cost per account.** Log model spend per client per month next to retained and expansion revenue
for that client. That ratio tells you where to run Tier 1 cadence and where weekly is enough.

### How the pieces fit

```
                 ┌────────── Plays & lessons library ◄─── nightly learning job ◄──┐
                 │                (read every run)          (proposes, evals,       │
                 ▼                                           human approves)       │
 signals ──► account agent (one per client) ──► draft / NEED HUMAN ──► approval queue
 (CRM, ops,      │  writes own Account Brief                          │  approved /
  email, calls,  │                                                    │  edited / rejected
  billing,       ▼                                                    ▼  + reason
  external)   portfolio agent ──► /chief-of-staff, /weekly-review   action ledger ──► outcomes
              (ranks all accounts, catches conflicts)                    (14 / 30 days)
```

Related skills feed the same loop: `/meeting-followup` writes call facts into the brief,
`/ops-metrics` supplies per-client volume and turnaround, `/postmortem` lessons about client work
go into the plays library, and `/win-loss` checks closed deals against the account agent's lessons.

### Bounded experiment

Before raising autonomy across the book, pick one account or one segment (for example billing
companies) and let the agent run it with more freedom: it sends routine messages without approval,
sets its own cadence, and reports daily. Bounded blast radius, real numbers, a clear success target
for the month. Widen autonomy only where the evals say it beats the human baseline.

## Account Brief template

```
# [Client]: Account Brief
Last run: YYYY-MM-DD · Stage: N · Health: Green/Amber/Red (score) · Tier: N · Owner: [name]

## 1. Snapshot (5 lines max)
## 2. Contract & compliance          (terms, key dates, BAA checklist, gaps)
## 3. Stakeholders                    (table)
## 4. What they bought, in their words (pain, success criteria, promises made)
## 5. Opportunity map                 (current scope vs full potential, assumptions)
## 6. Metrics                         (baseline, current, threshold status)
## 7. Onboarding / stage plan         (dated checklist with owners)
## 8. Open loops                      (who owes what by when)
## 9. Risks and signals               (red / amber / green flags)
## 10. Next action                    (drafted, awaiting approval)
## 11. Log                            (append only: date · source · fact)
## 12. Health history                 (date · score · band · reason)
## 13. Intervention log               (date · play · result after 14 / 30 days)
```

The intervention log is how the system learns which plays save accounts and which drive
expansion. Never skip it.
