---
name: precall-brief
version: 1.0.0
description: >
  Builds a branded HTML pre-call intelligence brief ~10 minutes before every
  intro/discovery call with a NEW prospect. Detects qualifying calls from the
  HubSpot-synced calendar, then researches deal context, lead source, deal
  priorities, insurances accepted, places of service, and recent news/LinkedIn
  activity. Designed to be driven by /loop so it fires automatically. Use when
  the user says "pre-call brief", "prep my next call", "brief me before my
  intro calls", or runs /loop /precall-brief.
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Pre-Call Brief — Automatic Intro-Call Intelligence

Fires ahead of every **intro/discovery call with a new prospect**. Follow-ups,
monthly touchpoints, business-case reviews, interviews, and internal meetings are
deliberately excluded — they are already-known accounts and don't need this.

## Step 1 — Find calls that need a brief

```bash
python3 ~/.claude/skills/precall-brief/scripts/find_calls.py
```

Returns `{due, upcoming, sleep}`. `due` = qualifying calls starting within 12
minutes that have no brief on disk yet. Override the lead time with
`PRECALL_LEAD_MIN=20 python3 ...`.

**If `due` is empty:** say one line — next qualifying call and when — and stop.
Do not build anything. Do not narrate what you checked.

**If `due` is non-empty:** build one brief per call, in order.

## Step 2 — Research (per call)

Read keys from `~/.claude/.api-keys.json`. The detector already gives you
`deal_id`, `company_id`, `contact_ids`, `emails`, and `domain` — use them, don't
re-search. Pull these in parallel where possible:

**a. Deal context + source — HubSpot.**
`GET /crm/v3/objects/deals/{deal_id}?properties=dealname,dealstage,amount,closedate,hs_analytics_source,hs_analytics_source_data_1,hs_analytics_source_data_2,createdate,description`
and the contact's `hs_analytics_source`, `hs_latest_source`, `jobtitle`,
`hs_lead_status`. The source answers "where did they come from" — inbound form,
outbound sequence, referral, conference. If the deal is null (no deal record yet),
say so plainly; that is itself a finding worth flagging.

**b. How they actually came in — Gmail.**
Search `from:{domain} OR to:{domain}` with no date bound, oldest first. The first
message in the thread is the real source of truth for how the relationship
started, and usually states what they asked for. Read full bodies, not snippets.
Quote their own words for the "what they want" section — never paraphrase a
prospect's stated pain into marketing language.

**c. Prior calls — Fathom.** Usually none for a true intro, but check:
`curl -s 'https://api.fathom.ai/external/v1/meetings?include_summary=true' -H 'X-Api-Key: <fathom key>'`
and look for the domain in `calendar_invitees`. If there IS a prior call, this is
not really an intro — say so at the top of the brief.

**d. Company enrichment — Apollo.** `POST /api/v1/organizations/enrich` with the
domain. Take headcount, industry, location, LinkedIn URL, funding.

**e. Website — insurances and places of service.** This is the part no API gives
you. Use gstack browse (never `mcp__claude-in-chrome__*`):

```bash
B=~/.claude/skills/gstack/browse/dist/browse
$B goto https://{domain} && $B text
```

Then check the pages that actually carry this information — typically
`/insurance`, `/insurances`, `/locations`, `/services`, `/contact`, `/about`,
`/what-we-treat`. Extract:
- **Insurances accepted** — name the payers verbatim as listed. Medicaid plans
  matter most; note the state Medicaid program by name when present.
- **Places of service** — clinic / in-home / school / telehealth, plus every
  physical location and state. This drives licensing and payer-mix questions.
- **Services and populations** — ABA, PT, OT, speech, primary care, age ranges.

If a page 404s or the site is thin, say "not published on their site" rather than
inferring. An unverified payer list on a sales call is worse than no payer list.

**f. Recent signals — news and LinkedIn.** Use the Apollo LinkedIn URL, browse the
company page, and capture anything from the last ~90 days: new locations, funding,
hiring pushes, leadership changes, posts. Also try a quick news lookup on the
company name. Recent hiring in intake/RCM roles is a strong buying signal for
Solum — call it out explicitly when you see it.

## Step 3 — Build the HTML

Write to the `brief_path` the detector supplied (under
`~/Documents/Claude/solum-ops/precall-briefs/`). Self-contained single file —
inline CSS, no external assets except the Google Fonts import.

**Brand:** Montserrat throughout. Navy `#011C40` headers and the time block,
Solum Blue `#468AF7` for links/accents, page background `#F2F2F9`, white cards,
Teal `#70D3C6` for positive signals, Purple `#A16CF4` for watch-outs. Never use
accent colors as large background fills.

Sections, in this order — the top third must be readable in 30 seconds:

1. **Header** — company name, call title, start time in ET, minutes until start,
   attendee names + titles, and the meeting link as a button.
2. **The 60-second version** — 3 bullets max. Who they are, what they asked for
   (their words), and the single sharpest question to open with.
3. **Deal context** — stage, amount, close date, deal age, owner. Plus source:
   how they arrived, and the first-contact date and channel from Gmail.
4. **Top priorities** — what this prospect is actually trying to solve, ranked,
   each traced to a quote or a source. If you have fewer than three real ones,
   show fewer. Never pad.
5. **Insurances accepted** — as a tag list. Flag Medicaid plans distinctly, since
   those carry the heaviest auth burden and are Solum's strongest wedge.
6. **Places of service** — locations, states, and delivery settings.
7. **Recent signals** — news, LinkedIn posts, hiring, expansion. Dated.
8. **Open questions** — what you could NOT verify. This section is mandatory and
   must never be empty; if everything verified, say what you'd still confirm live.

Every fact carries its origin inline (`HubSpot`, `Gmail 6/12`, `website`,
`Apollo`, `LinkedIn`). Anything inferred is labelled **ASSUMPTION**. This is a
hard rule — JP will read these on a live call and cannot afford an unsourced
number.

## Step 4 — Report

One line per brief: company, call time in ET, file path. Nothing else.

## Loop usage

```
/loop /precall-brief
```

Self-paced. The detector returns `sleep` — the seconds until roughly 12 minutes
before the next qualifying call, clamped to [60s, 1h]. Pass that straight to
ScheduleWakeup as `delaySeconds`. When nothing is scheduled it idles at 1 hour.

The brief file on disk is the state — a call with an existing brief is never
rebuilt, so restarting the loop is always safe.
