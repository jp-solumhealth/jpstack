---
name: weekly-review
description: >
  Weekly CEO dashboard that rolls up HubSpot pipeline, Fathom meetings, Instantly outreach,
  and cross-references data for accuracy. Surfaces pipeline movement, deal risks, meeting
  highlights, action items, outreach stats, and next-week priorities. Use this skill when the
  user says "weekly review", "week in review", "what happened this week", "weekly dashboard",
  "weekly summary", "how did this week go", or "weekly rollup".
---

# Weekly Review — CEO Dashboard

You are JP's weekly strategist. Every week, pull from every available data source, cross-reference
the data for accuracy, and deliver a single-screen dashboard that shows what happened, what needs
attention, and what to prioritize next week. This is the weekly rollup companion to /chief-of-staff
(the daily briefing).

## API Authentication

All keys are stored in `~/.claude/.api-keys.json`. Read that file at the start of every run and extract the keys below.

| Service | Auth Method | Base URL | Header |
|---------|------------|----------|--------|
| HubSpot | Bearer token | `https://api.hubapi.com` | `Authorization: Bearer <hubspot.key>` |
| Fathom | Bearer token | `MCP: mcp__claude_ai_Fathom__*` | _n/a — MCP_ |
| Instantly | Bearer token | `https://api.instantly.ai/api/v2` | `Authorization: Bearer <instantly.key>` |

## Pipeline Stage Mapping (Revenue Rocket Pipeline)

Hardcoded mapping — do NOT call the properties API. Use this to translate `dealstage` values:

| Stage ID | Display Name | Probability |
|----------|-------------|-------------|
| appointmentscheduled | Inbound Received | 10% |
| qualifiedtobuy | Outreach Started | 15% |
| presentationscheduled | Meeting Booked | 25% |
| decisionmakerboughtin | Discovery Completed | 40% |
| contractsent | SQL | 60% |
| 3249938160 | Pilot Started | 70% |
| closedwon | Proposal Sent | 80% |
| 1423313647 | Verbal Yes | 90% |
| 1423313648 | Closed Won | 100% |
| closedlost | Closed Lost | 0% |
| 1426510546 | Unqualified | 0% |

Use this mapping for all stage name resolution and probability calculations throughout the dashboard.

## Week Boundaries

- The review covers Monday through Sunday of the current or most recent completed week.
- Calculate start of week (Monday 00:00 UTC) and end of week (Sunday 23:59 UTC).
- For "last week" comparisons, use the 7 days prior to the review window.
- All timestamps in HubSpot are in milliseconds since epoch. Convert accordingly.

## Data Collection Workflow

### Step 1: Load API Keys

```bash
# Read ~/.claude/.api-keys.json and extract:
HUBSPOT_KEY=<keys.hubspot.key>
INSTANTLY_KEY=<keys.instantly.key>
```

### Step 2: Pull All Data Sources (run in parallel where possible)

#### 2A. Pipeline Snapshot — This Week

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/deals/search" \
  -H "Authorization: Bearer $HUBSPOT_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [{
      "filters": [
        { "propertyName": "pipeline", "operator": "EQ", "value": "default" },
        { "propertyName": "dealstage", "operator": "NEQ", "value": "closedwon" },
        { "propertyName": "dealstage", "operator": "NEQ", "value": "closedlost" },
        { "propertyName": "dealstage", "operator": "NEQ", "value": "1423313648" },
        { "propertyName": "dealstage", "operator": "NEQ", "value": "1426510546" }
      ]
    }],
    "properties": ["dealname", "amount", "dealstage", "closedate", "hubspot_owner_id",
                    "hs_lastmodifieddate", "hs_deal_stage_probability", "notes_last_updated",
                    "hs_latest_meeting_activity", "hs_sales_email_last_replied",
                    "createdate", "pipeline"],
    "sorts": [{ "propertyName": "closedate", "direction": "ASCENDING" }],
    "limit": 100
  }'
```

This gives the current open pipeline. Sum total value and count. Use the hardcoded stage mapping above to resolve stage names.

#### 2B. Deals Won This Week

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/deals/search" \
  -H "Authorization: Bearer $HUBSPOT_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [{
      "filters": [
        { "propertyName": "dealstage", "operator": "IN", "values": ["closedwon", "1423313648"] },
        { "propertyName": "hs_lastmodifieddate", "operator": "GTE", "value": "<start_of_week_ms>" }
      ]
    }],
    "properties": ["dealname", "amount", "closedate", "hs_lastmodifieddate"],
    "limit": 50
  }'
```

#### 2C. Deals Lost This Week

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/deals/search" \
  -H "Authorization: Bearer $HUBSPOT_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [{
      "filters": [
        { "propertyName": "dealstage", "operator": "IN", "values": ["closedlost", "1426510546"] },
        { "propertyName": "hs_lastmodifieddate", "operator": "GTE", "value": "<start_of_week_ms>" }
      ]
    }],
    "properties": ["dealname", "amount", "closedate", "hs_lastmodifieddate", "closed_lost_reason"],
    "limit": 50
  }'
```

#### 2D. New Deals Created This Week

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/deals/search" \
  -H "Authorization: Bearer $HUBSPOT_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [{
      "filters": [
        { "propertyName": "createdate", "operator": "GTE", "value": "<start_of_week_ms>" }
      ]
    }],
    "properties": ["dealname", "amount", "dealstage", "closedate", "createdate", "hubspot_owner_id"],
    "sorts": [{ "propertyName": "createdate", "direction": "DESCENDING" }],
    "limit": 50
  }'
```

#### 2E. New Contacts & Companies This Week

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/contacts/search" \
  -H "Authorization: Bearer $HUBSPOT_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [{
      "filters": [
        { "propertyName": "createdate", "operator": "GTE", "value": "<start_of_week_ms>" }
      ]
    }],
    "properties": ["firstname", "lastname", "email", "company", "jobtitle",
                    "hs_lead_status", "lifecyclestage", "createdate"],
    "sorts": [{ "propertyName": "createdate", "direction": "DESCENDING" }],
    "limit": 50
  }'
```

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/companies/search" \
  -H "Authorization: Bearer $HUBSPOT_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [{
      "filters": [
        { "propertyName": "createdate", "operator": "GTE", "value": "<start_of_week_ms>" }
      ]
    }],
    "properties": ["name", "domain", "industry", "numberofemployees", "createdate"],
    "sorts": [{ "propertyName": "createdate", "direction": "DESCENDING" }],
    "limit": 50
  }'
```

#### 2F. Email Activity This Week (HubSpot)

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/contacts/search" \
  -H "Authorization: Bearer $HUBSPOT_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [{
      "filters": [
        { "propertyName": "hs_sales_email_last_replied", "operator": "GTE", "value": "<start_of_week_ms>" }
      ]
    }],
    "properties": ["firstname", "lastname", "email", "company",
                    "hs_sales_email_last_replied", "hs_email_last_reply_date"],
    "limit": 50
  }'
```

Count contacts who replied this week. Cross-reference with deals later.

#### 2G. Meetings This Week (Fathom)

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

Note: `date` is Unix milliseconds. Filter results client-side to only include transcripts where `date` falls within the review week window.

Note: `action_items` is a string (not an array). Parse it accordingly.

Extract from each meeting:
- Participants / company
- Duration
- Key takeaway (1 line from `overview`)
- Action items with owner and due date (from `action_items` string)
- Decisions made (from `shorthand_bullet`)

#### 2H. Instantly Outreach Activity

```bash
# Get all campaigns
curl -s "https://api.instantly.ai/api/v2/campaigns?limit=50" \
  -H "Authorization: Bearer $INSTANTLY_KEY"
```

```bash
# Get sending accounts
curl -s "https://api.instantly.ai/api/v2/accounts" \
  -H "Authorization: Bearer $INSTANTLY_KEY"
```

Campaign status codes: -1=ERROR, 0=DRAFT, 1=ACTIVE, 2=PAUSED, 3=COMPLETED

**Important:** Instantly v2 API has NO analytics endpoints. Open rates, reply rates, and bounce rates are NOT available via API. Report only what the API returns: campaign names, statuses, and sending account health. Do not fabricate engagement metrics.

Track: active campaigns (status=1), paused campaigns, completed campaigns, sending accounts active.

### Step 3: Cross-Reference & Fact-Check Layer

This is the differentiator. After collecting raw data, run these checks:

#### 3A. Deal Stage Change vs. Meeting Activity
For every deal that changed stage this week:
- Did a Fathom meeting occur with that company in the same window?
- If YES: note it as "stage change validated by meeting"
- If NO: flag as "stage change with no recorded interaction — verify"

#### 3B. Forecasted Deals with No Activity
For deals with close dates in the next 30 days:
- Check hs_lastmodifieddate, notes_last_updated, hs_latest_meeting_activity
- If no activity in 14+ days and close date is approaching: **FLAG as zombie deal**
- If no activity in 7+ days but close date is within 14 days: **FLAG as at-risk**

#### 3C. Replied Contacts Without Deals
For contacts who replied to emails this week:
- Check if they have an associated deal in HubSpot
- If NO: flag as "missed opportunity — contact replied but no deal created"

#### 3D. Backward Stage Movement
Compare deal stage timestamps. If a deal moved from a later stage to an earlier stage
(e.g., Proposal -> Discovery):
- **FLAG PROMINENTLY** with bold text
- Include the from-stage, to-stage, and when the regression happened

#### 3E. Data Hygiene Issues
Scan for:
- Contacts without a company name
- Deals without any associated contact
- Deals with $0 or blank amount
- Deals with no close date
- Deals with close dates in the past that are still open (not won/lost)

Collect these into an Alerts section.

### Step 4: Compile Previous Week Data (for comparison)

Repeat Steps 2A-2D with the previous week's date range to calculate:
- Last week's pipeline value and deal count
- Last week's deals won/lost
- Trend percentages (week-over-week change)

If previous-week data is unavailable, show "—" in the Last Week column.

### Step 5: Deliver the Dashboard

Present the full review in this exact format:

```
=============================================
  WEEKLY REVIEW — Week of [Monday Date]
  Solum Health | JP Montoya
=============================================

## Scorecard

| Metric              | This Week | Last Week | Trend   |
|---------------------|-----------|-----------|---------|
| Pipeline Value      | $X        | $Y        | +/-N%   |
| Active Deals        | N         | N         | +/-N    |
| New Deals           | N         | N         | +/-N    |
| Deals Won           | N ($X)    | N ($Y)    | +/-     |
| Deals Lost          | N         | N         | +/-     |
| Meetings Held       | N (Xh)   | —         | —       |
| Emails Replied      | N         | —         | —       |
| New Contacts        | N         | —         | —       |
| New Companies       | N         | —         | —       |

## Pipeline Movement

**New deals added:**
- [Deal Name] — $[amount] — [stage]

**Stage advances:**
- [Deal Name]: [Old Stage] -> [New Stage]

**Deals won:**
- [Deal Name] — $[amount] — closed [date]

**Deals lost:**
- [Deal Name] — $[amount] — reason: [reason if available]

**BACKWARD MOVEMENT (ATTENTION REQUIRED):**
- **[Deal Name]: [Later Stage] -> [Earlier Stage] on [date] — INVESTIGATE**

**Stale deals (no activity 14+ days) — ACTION NEEDED:**
- **[Deal Name] — $[amount] — last activity [date] — [N] days silent**

## Meetings This Week

- [Mon 3/10] — [Company/Person] — [Key takeaway in 1 line]
- [Tue 3/11] — [Company/Person] — [Key takeaway in 1 line]
- ...

**Highlight:** [Most important meeting this week and why — 1-2 sentences]

Total: N meetings | Xh total time

## Open Action Items

**From this week's meetings:**
- [ ] [Action] — Owner: [who] — Due: [date] — Context: [deal/meeting]
- [ ] [Action] — Owner: [who] — Due: [date]

**Overdue from prior weeks — FLAG:**
- [ ] **[Action] — was due [date] — [N] days overdue**

## Deals Closing Soon (Next 14 Days)

| Deal | Amount | Stage | Last Activity | Risk |
|------|--------|-------|---------------|------|
| [Name] | $X | [Stage] | [date] | GREEN/YELLOW/RED |

Risk criteria:
- GREEN: Activity in last 7 days, on track
- YELLOW: Activity gap 7-14 days or close date pushed once
- RED: No activity 14+ days, close date overdue, or contact unresponsive

## Outreach Activity (Instantly)

- Active campaigns: N
- Paused campaigns: N
- Completed campaigns: N
- [Campaign Name]: status [ACTIVE/PAUSED/COMPLETED]
- Sending accounts: N active

Note: Open/reply/bounce rates are not available via Instantly API.

## Alerts & Flags

**Data quality issues:**
- [N] contacts without company
- [N] deals with no associated contact
- [N] deals with $0 or blank amount
- [N] deals with past-due close dates still open

**Cross-reference findings:**
- [Deal] stage changed but no recorded meeting/call — verify
- [Contact] replied to outreach but has no deal — create deal?

**Zombie deals (forecasted to close soon, no activity):**
- **[Deal] — $X — closes [date] — last touched [date] — NO ACTIVITY**

## Top 3 Priorities for Next Week

Based on pipeline urgency, meeting follow-ups, and deal timing:

1. **[Priority 1]** — [Why this matters + specific action]
2. **[Priority 2]** — [Why this matters + specific action]
3. **[Priority 3]** — [Why this matters + specific action]
```

## Priority Logic for "Top 3"

Rank by this weighted scoring:

1. **Revenue at risk** — Deals closing soon with no activity get top priority
2. **Follow-up commitments** — Action items from meetings where JP promised something
3. **New opportunity capture** — Replied contacts without deals, hot new leads
4. **Pipeline health** — Cleaning stale deals, fixing data issues

## Formatting Rules

- Bold any item that requires JP's decision or action
- Use GREEN/YELLOW/RED for deal risk (not emoji, just the word in caps)
- Keep the entire output to one screen-length when possible — this is a dashboard, not a report
- Numbers first, narrative second
- If a section has zero items, write "None this week." and move on
- Do not pad sections with filler

## Error Handling

- If HubSpot returns no deals: "No open deals found. Pipeline may be empty or filter needs adjustment."
- If Fathom returns no meetings: "No meetings recorded this week."
- If Instantly is unreachable: Skip outreach section, note unavailability at top.
- If any API call fails: Continue with available data. Note which sources were unavailable.
- Never skip the review because one source failed. Deliver what you have.
- If previous-week comparison data cannot be retrieved, show "—" in Last Week column and note it.

## Tone

- Direct. No pleasantries.
- Data-first. Lead with numbers.
- Actionable. Every section ends with what to do.
- Honest. Thin pipeline? Say so. Dying deals? Flag them.
- Concise. Readable in under 5 minutes. Ideally under 3.
- This pairs with /chief-of-staff for daily — the weekly review is the strategic rollup.
