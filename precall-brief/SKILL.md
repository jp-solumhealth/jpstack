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

**This is a call plan, not a research report.** JP reads it in the two minutes
before he joins, on a call that is often only 15 minutes. Anything that does not
change what he says or asks is cut. Target under 4,000px tall — if it runs
longer, you are dumping research instead of deciding what matters.

**Brand** — QA against the `solum-health-brand` skill, which is authoritative:

- Font `'DM Sans', sans-serif` via the Google Fonts import. (The global CLAUDE.md
  line naming Montserrat is stale for web/CSS; the brand system and the jpstack
  README both specify DM Sans.)
- Navy `#011C40` hero and headings · Solum Blue `#468AF7` accents and rules ·
  page `#F2F2F9` · white cards · Teal `#70D3C6` positive/wedge · Purple/Lavender
  `#A16CF4`/`#E5DFF4` warnings. Never an accent as a large background fill.
- Radius `8px` cards, `20px` pills, `6px` small. Shadow `0 1px 3px rgba(1,28,64,.08)`.
- `SolumHealth` wordmark top-left of the hero — "Health" in Teal.
- Section headings are **real headings**: 23px, weight 700, Navy, with an optional
  grey qualifier beside them. Never tiny uppercase grey labels — those are the
  page's navigation and must be the strongest text on it after the H1.

Sections, in this order. The order is the point: act first, evidence second.

1. **Hero** — wordmark, company, call type, start time in ET. A pill stating the
   duration and the posture it forces (e.g. "15 MIN — GO NARROW"). A meta strip:
   who, role, stage, footprint, source.
2. **Your call plan** — the whole reason the brief exists, and visually dominant
   (blue top rule, numbered navy discs). Contains exactly:
   - **Three questions**, ranked, each with one line on why it matters and what
     it unlocks. Real questions in quotes, phrased the way he'd say them.
   - **The angle** (teal panel) — the specific pitch *if* the call goes well, and
     the concrete next step to propose. Name the motion (usually the free
     insurance audit) and cite a comparable that recently converted.
   - **Do not do this** (lavender panel) — the trap. Prior history that would
     embarrass him, a stakeholder who churned, a competitor already in play.
     Omit the panel entirely when there is no trap; never pad it.
3. **Deal context** — stage, amount, close date, created. Flag missing amount or
   close date as something to set on the call.
4. **Payer mix** — two columns by state. Medicaid plans in Teal, everything else
   neutral. Follow with one card of interpretation, not a third list.
5. **Footprint & signals** — merged. Locations compressed to a single line
   (count + names inline), delivery settings, hiring, expansion, news. Location
   names are low-value; never give them a grid of their own.

Open questions belong **inside the call plan as the three questions** — not as a
trailing section. If a question isn't worth asking live, it isn't worth printing.

Every fact carries its origin inline (`HubSpot`, `Gmail 6/12`, `website`,
`Apollo`, `job boards`). Anything inferred is labelled **ASSUMPTION**. This is a
hard rule — JP reads these on a live call and cannot afford an unsourced number.

**QA before you finish.** Serve the file and screenshot it — do not ship a brief
you have not looked at:
```bash
cd <brief dir> && (python3 -m http.server 8899 &) 
# then render http://localhost:8899/<file>?v=N  (the ?v= is required; the
# server sends Last-Modified and the browser will otherwise show a stale page)
```
Check: page under ~4,000px, call plan above the fold on a laptop, no section
wider than the viewport, every claim sourced.

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
