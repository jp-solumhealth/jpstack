---
name: pricing-coach
description: >
  Weekly pricing conversation coach for Solum Health sales calls. Pulls calls from Fathom,
  extracts all pricing moments, scores each conversation against proven benchmarks, and delivers
  a coaching report with what worked, what didn't, and specific improvement recommendations.
  Use this skill when the user says "pricing coach", "pricing feedback", "review my pricing",
  "how did pricing go this week", "pricing report", "score my calls", "pricing review",
  "weekly pricing", "sales coaching", or any variation of wanting feedback on how pricing
  conversations went. Also trigger when the user asks to "run the pricing coach" or
  "check my pricing this week". Default period: last 7 days. User can specify a different
  date range.
---

# Pricing Coach

Analyze Solum Health sales calls for pricing conversation quality. Pull calls from Fathom,
extract pricing moments, score against proven benchmarks, and deliver actionable coaching.

## API Authentication

Fathom API key is stored in `~/.claude/.api-keys.json` under _none — MCP_.

Load the key at the start of every run:

```bash
```

All Fathom access is via MCP tools (`mcp__claude_ai_Fathom__*`). No endpoint, no key, no headers.

All API calls run via Bash tool with curl, piped through python3 for JSON processing.

## Core Principle

This is a feedback loop, not a report generator. The goal is to catch bad pricing habits
early, reinforce what's working, and give JP concrete scripts to use on the next call. Every
recommendation should reference a specific moment from a specific call.

## The Workflow

### Phase 0: Date Range

Determine the analysis period:
- Default: last 7 days from today
- If user specifies a range (e.g., "last 2 weeks", "this month", "Feb 10-24"), use that
- Calculate `fromDate` and `toDate` as Unix millisecond timestamps for Fathom filtering

### Phase 1: Call Discovery

Fetch recent transcripts from Fathom and filter for pricing-related calls client-side.

**Step 1: Pull all recent transcripts**

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

**Step 2: Filter results client-side**

Since the Fathom MCP tools does not support keyword search in the basic query, filter the returned transcripts using python3:

- Parse the `date` field (Unix millisecond timestamp) and keep only transcripts within the date range
- Check `title` for prospect/company names
- Check `summary.overview` for pricing keywords: "pricing", "price", "cost", "free", "monthly", "500", "trial", "$"
- A call qualifies if its title or overview contains any pricing keyword

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

Note: `action_items` is a string, not an array. `date` is a Unix millisecond timestamp.

Deduplicate by meeting ID. Exclude internal calls (weekly team meetings, 1:1s with Juliana,
investor calls). Focus on prospect and client-facing calls only.

Identification rules for excluding non-sales calls:
- Title contains "Weekly", "Monthly Touchpoint", "Standup", "Team", "Internal"
- Participants are all @getsolum.com emails
- Title suggests investor/recruiting (e.g., "Silversmith", "X JP" where X is a first name only)

**KEEP** calls titled: "Assessment", "FUP", "Onboarding", "Demo", any company name "X Solum Health"

### Phase 2: Call Analysis

For each qualifying call, retrieve the full summary by transcript ID:

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

For each call, extract:

1. **Pricing tactic used** -- What approach was taken?
   - Free trial/test offered
   - $500/mo Growth tier pitched
   - $2,500/mo Scale tier pitched
   - Enterprise/custom pricing discussed
   - Per-unit pricing presented
   - No pricing discussed (ran out of time)
   - Pricing sent async (email/doc)

2. **Prospect reaction** -- How did they respond?
   - Positive acceptance ("sounds good", "let's do it", "not a big deal")
   - Price anchoring concern ("that seems expensive", "what's the total")
   - Confusion ("what does that include", "what's the difference")
   - Sticker shock ("that's a lot", silence, subject change)
   - No reaction (pricing wasn't reached)

3. **Key pricing quotes** -- Direct quotes from prospect about pricing/cost/value

4. **Conversion signal** -- Did the call result in:
   - Next step scheduled
   - Trial/test initiated
   - Onboarding started
   - Stalled / no next step
   - Follow-up promised but vague

### Phase 3: Scoring

Score each call 1-5 against the proven benchmarks. Read `references/scoring-rubric.md`
for the detailed rubric.

**Quick reference:**

| Score | Criteria |
|-------|----------|
| **5** | Free trial offered + accepted, OR prospect said yes to a plan, OR onboarding started |
| **4** | Pricing discussed clearly, prospect understood, next step scheduled |
| **3** | Pricing discussed but with confusion/clarification needed, neutral outcome |
| **2** | Pricing created friction, confusion, or pushback. No clear next step |
| **1** | Pricing never discussed, ran out of time, or prospect explicitly objected |

**Benchmark violations to flag:**
- Pricing discussed before showing results/demo (violates "Show, Then Price")
- 12+ line items presented (violates simplification)
- Product naming confusion occurred (self-check vs eligibility check etc.)
- Setup fee was negotiated instead of waived/included
- Enterprise prospect got per-unit pricing instead of flat rate
- Implementation timeline not mentioned
- No free trial/test offered on a first call

### Phase 4: Report Generation

Generate a markdown report saved to `~/Documents/Solum_Pricing_Coach_{date}.md`

**Report structure:**

```
# Pricing Coach Report
## Week of {startDate} - {endDate}

### Weekly Score: X.X / 5.0 (trend: up/down/flat vs last report if available)

### Calls Analyzed: N

---

## Scorecard

| Call | Date | Prospect | Tactic | Reaction | Score | Flag |
|------|------|----------|--------|----------|-------|------|
| ... per call row ... |

---

## What Worked This Week
[2-3 specific moments that scored 4-5, with quotes and why they worked]

## What Needs Work
[2-3 specific moments that scored 1-2, with quotes and what to do differently]

## Benchmark Violations
[List each violation with the call, what happened, and the correct play]

## Scripts to Use Next Week
[2-3 concrete scripts for upcoming calls based on this week's patterns]

## Enterprise Pipeline Check
[Status of any enterprise deals, whether pricing has been delivered, and urgency flags]

---

*Generated by Pricing Coach | Benchmarks: ~/Documents/Solum_Pricing_Benchmarks.md*
*Full pricing analysis: ~/Documents/Solum_Pricing_Analysis.md*
```

### Phase 5: Delivery

1. Save the report to `~/Documents/Solum_Pricing_Coach_{YYYY-MM-DD}.md`
2. Display a summary to the user with:
   - Weekly score and trend
   - Top win (best pricing moment)
   - Top fix (worst pricing moment + recommended script)
   - Any urgent flags (enterprise deals without pricing, stalled prospects)
3. Ask: "Want me to drill into any specific call or prepare scripts for upcoming meetings?"

## Scoring Calibration

The scoring is calibrated against the proven benchmarks documented in
`~/Documents/Solum_Pricing_Benchmarks.md` and the pricing structure proposed in
`~/Documents/Solum_Pricing_Analysis.md`. Key benchmarks:

- Free trial win rate: 86% (6/7 prospects)
- Paid-first win rate: 25% (1/4 prospects)
- $500/mo acceptance rate at <200 clients: 100%
- Average score across Feb 5-26 baseline: 3.7/5
- Target weekly score: 4.0+/5

## Important Notes

- **Fathom API access required.** Key stored in `~/.claude/.api-keys.json`.
- **All API calls run via Bash tool with curl**, piped through python3 for JSON processing.
- **Exclude internal calls.** Only score prospect/client-facing conversations.
- **Be direct in coaching.** This isn't a pat on the back. If pricing was bad, say so and
  say exactly what to do differently. Use the benchmarks as the standard.
- **Quote the prospect.** Every recommendation should tie back to something the prospect
  actually said on a call.
- **Track enterprise deals.** Attain ABA, Pomm RI, and any 1,000+ client prospect need
  flat-rate pricing delivered within 1 week of first pricing discussion. Flag if overdue.
