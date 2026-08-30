---
name: business-case-builder
description: >
  Build branded 1-2 slide PPTX business cases with ROI analysis for Solum Health prospects.
  Pulls deal context from Fathom transcripts, HubSpot data, and prior SOW specs to generate
  a decision-ready one-pager with before/after comparison, ROI metrics, investment summary,
  and phased timeline. Use this skill when the user says "build a business case",
  "business case for [company]", "ROI analysis for [deal]", "one-pager for [company]",
  "make the case for [company]", "ROI deck", "decision doc for [company]",
  or any variation of wanting a visual business justification document for a prospect.
---

# Business Case Builder

Generate branded, decision-ready PPTX business cases for Solum Health prospects. Every number must be sourced or clearly labeled as an estimate. The output should make the decision obvious in 60 seconds.

## Core Principle

A business case is read by someone who wasn't on the calls. It needs to stand alone. Every claim needs a number. Every number needs a source or a clearly stated assumption. The framing is always about empowering the client's team with better tools — never about replacing headcount.

## API Authentication

All API keys are stored in `~/.claude/.api-keys.json`. Read this file first to get credentials.

| Service | Auth Method | Base URL |
|---------|-------------|----------|
| HubSpot | `Authorization: Bearer <key>` | `https://api.hubapi.com` |
| Fathom | _n/a — MCP, no auth header_ | `mcp__claude_ai_Fathom__list_meetings` |

Use direct HTTP calls via `curl` with the Bash tool. Pipe through `python3` for JSON processing.

## The Workflow

### Phase 1: Gather Context

Before writing anything, collect every data point available. Run these in parallel where possible.

**1A. Check for existing SOW or deal research:**
Look in `~/Documents/Claude/solum-ops/sow/` for any existing specs, summary reports, or generators for this company. These contain confirmed data from prior calls.

**1B. Pull Fathom transcripts:**
```
# Fathom MCP — no curl, no API key. See ~/.claude/skills/_shared/fathom-meetings.md
mcp__claude_ai_Fathom__list_meetings(
  created_after: "<ISO8601 start of window>",
  max_pages: 3,
  include_summary: true,
  include_action_items: true
)
# -> recording_id, title, date, url, recorded_by, calendar_invitees
# Then, for verbatim quotes:
mcp__claude_ai_Fathom__get_meeting_transcript(recording_id: <id>)
```
Filter by company name in title. Extract:
- Volume data (auths/month, patients, transactions)
- Team size and roles
- Current process pain points (in their own words)
- Pricing discussions (what was quoted, reactions)
- Technology stack (EHR, CRM, clearinghouse)
- Growth plans (new locations, more clients)

**1C. Pull HubSpot deal data:**
```bash
curl -s "https://api.hubapi.com/crm/v3/objects/deals/search" \
  -H "Authorization: Bearer <HUBSPOT_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"filterGroups":[{"filters":[{"propertyName":"dealname","operator":"CONTAINS_TOKEN","value":"<company>"}]}],"properties":["dealname","amount","dealstage","closedate","hs_lastmodifieddate"]}'
```

### Phase 2: Build the Data Model

Before designing slides, structure all the numbers. Fill in what you have, flag what's missing, and estimate what you can.

```
COMPANY PROFILE
- Name:
- Industry/Specialty:
- Size (employees, locations, patients/clients):
- EHR/CRM:
- Growth trajectory:

CURRENT STATE
- Process being automated:
- Volume (monthly/annual):
- Team handling it (headcount, roles):
- Estimated time per unit (minutes):
- Total monthly hours spent:
- Hourly rate (fully loaded):
- Annual labor cost:
- Current cost per unit:
- Error/rework rate:
- Revenue at risk from errors:
- Key person dependency:

WITH SOLUM
- Solum cost per unit:
- Implementation fee:
- Monthly cost at full volume:
- Annual cost:
- Submission SLA:
- Expected error reduction:
- Expected automation rate:

ROI
- Cost reduction per unit (%):
- Annual savings (labor redeployment):
- Risk prevented (revenue protected):
- Payback period:
- Capacity freed (hours/month):

PILOT PLAN
- Phase 1 scope:
- Phase 2 scope:
- Timeline (weeks):
- Go/no-go gates:
```

**For missing data, use these industry benchmarks:**

| Metric | ABA | PT/Rehab | Hospice/Home Health | General |
|--------|-----|----------|---------------------|---------|
| Auth processing time | 30-45 min | 20-30 min | 25-40 min | 30 min avg |
| Auth cycle (submission to approval) | 14-21 days | 10-14 days | 7-14 days | 14 days avg |
| Denial rate | 5-8% | 3-5% | 4-7% | 5% avg |
| Reauth frequency | Every 6 months | Every 15-20 visits | Per episode | Varies |
| Admin staff hourly rate (fully loaded) | $25-30 | $22-28 | $24-30 | $25-30 |
| Revenue per patient/month | $3,000-8,000 | $200-500/visit | $4,000-6,000 | Varies |

Always label estimates: "Based on industry benchmarks for [vertical]" — never present estimates as confirmed data.

### Phase 3: Design the Slides

Generate using `pptxgenjs` (Node.js). Follow the Solum Health brand style.

**Brand Style:**
```js
const C = {
  darkBg:    "0B1437",   // Navy (headers, dark bars)
  lightBg:   "EFF3F8",   // Light blue (page background)
  blue:      "4A90D9",   // Mid blue (accent)
  green:     "00C9A7",   // Teal green (positive, savings)
  red:       "E8614D",   // Coral red (costs, current state)
  purple:    "9B6DD7",   // Muted purple
  teal:      "00B4D8",   // Bright teal
  white:     "FFFFFF",
  darkText:  "1A1A2E",   // Body text
  muted:     "6B7B8D",   // Secondary text
};
```
- Font: Montserrat (bold headers, regular body)
- Logo: `/Users/juanmontoya/Documents/Claude/Claude Tasks/assets/solum_logo.png`
- Layout: 16:9 (10" × 5.625")
- Always include footer: Solum logo, getsolum.com, CONFIDENTIAL
- Use factory functions for shadows/lines (pptxgenjs quirk — never reuse objects)

**Slide 1 — The Case (always required)**

```
┌──────────────────────────────────────────────────────┐
│ [DARK HEADER]                                         │
│ "BUSINESS CASE" label (blue, small, tracked)          │
│ Headline: the key value proposition in one line        │
│ Subline: Company × Solum Health | Date                │
├───────────────────────┬──────────────────────────────┤
│  CURRENT PROCESS      │  WITH SOLUM                   │
│  (red accent card)    │  (green accent card)          │
│  6 bullet comparisons │  6 bullet comparisons         │
├───────────────────────┴──────────────────────────────┤
│  4 METRIC STAT BOXES (colored accent tops)            │
│  [Cost reduction %] [Risk prevented] [SLA] [Payback]  │
├──────────────────────────────────────────────────────┤
│ [DARK BAR] Investment summary: per-unit pricing        │
├──────────────────────────────────────────────────────┤
│ [TIMELINE] Compact horizontal phased rollout           │
├──────────────────────────────────────────────────────┤
│ [FOOTER] Logo | getsolum.com | CONFIDENTIAL           │
└──────────────────────────────────────────────────────┘
```

**Slide 2 — The Detail (optional, for complex deals)**

Only add if the deal has enough data to justify a second slide. Use for:
- Detailed ROI table (current cost breakdown vs. Solum cost)
- Volume breakdown by payer/service/location
- Per-payer or per-service pricing detail
- Expansion roadmap beyond the pilot

### Phase 4: Generate the PPTX

Save the generator script to:
`~/Documents/Claude/solum-ops/sow/<company-slug>-business-case.js`

Save the output to:
`~/Documents/Claude/solum-ops/sow/<company-slug>-business-case.pptx`

Run with: `node <company-slug>-business-case.js`

After generation, run a text-fit audit:
- Check every text element fits within its container
- Verify no text overlaps with adjacent elements or the footer
- Confirm all numbers match the data model

### Phase 5: Present to User

Show:
- File path where the PPTX was saved
- Summary of confirmed vs. estimated data points
- Any flags or gaps the user should address before sending

Ask:
- "Want me to adjust any numbers or framing?"
- "Is there data I should verify before you send this?"

## Tone & Framing Rules

These are non-negotiable:

1. **"Repurpose" not "replace."** Frame as: team gets better tools, focuses on higher-value work. Never mention headcount reduction, FTE savings, or staff cuts.

2. **Champion the day-to-day person.** If there's a named person who does the work (like "Devin handles auths"), position them as the pilot lead and quality reviewer — not the person being automated away.

3. **Numbers first.** Lead with the math: cost per unit comparison, annual impact, payback period. The ROI should be self-evident from the numbers without needing narrative persuasion.

4. **Conservative estimates.** When using industry benchmarks, use the low end of ranges. Under-promise. If the math works with conservative numbers, the deal is real.

5. **Source everything.** Every number either has a source (call date, email date, confirmed by [name]) or is clearly labeled "industry estimate." Never present guesses as facts.

6. **No AI language.** Ban: "leverage", "streamline", "robust", "comprehensive", "cutting-edge", "state-of-the-art." Write like a CFO, not a marketing team.

7. **One-page test.** If the department head can't understand the business case in 60 seconds looking at Slide 1, it's too complex. Simplify.

## Handling Missing Data

| Situation | Approach |
|-----------|----------|
| No volume data | Ask the user. If unavailable, note "Volume TBD — business case assumes [X] based on company size" |
| No hourly rate | Use $25-30/hr fully loaded (industry standard for admin staff) |
| No error/denial rate | Use industry benchmarks for the vertical, labeled as estimates |
| No team size | Ask the user. This is critical for the cost calculation. |
| No pricing discussed | Use standard Solum pricing tiers from the SOW builder skill |
| No growth data | Omit the growth section rather than guessing |

## Example Headline Formulas

Pick the one that best fits the data:

- "Repurpose [X] hours/month from [manual process] to [higher-value work]"
- "[Process] automation reduces cost per [unit] by [X]% while improving [metric]"
- "Same team, [X]% lower cost per [unit], [Y]-hour SLA"
- "Protect $[X] in annual revenue while cutting [process] cost by [Y]%"

## Reference: Solum Pricing Tiers

| Tier | Monthly | Best For |
|------|---------|----------|
| Growth | $500/mo | Small practices, <200 clients |
| Scale | $2,500/mo | Mid-size, 200-1,000 clients |
| Enterprise | Custom | Large orgs, 1,000+ clients |
| Per-unit (auth) | ~$10/auth | Volume-based authorization processing |
| Per-unit (verification) | ~$2-3/check | Volume-based eligibility/verification |
| Implementation | $0-2,500 | Depends on integration complexity |

## Related Skills

- `sow-builder` — For the full scope of work document (comes after or alongside the business case)
- `meeting-prep` — For pre-call intelligence before discovery
- `meeting-followup` — For post-call deliverables including deal notes
