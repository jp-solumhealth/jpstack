---
name: meeting-prep
description: >
  Generates a one-page meeting prep brief before any sales or customer call.
  Pulls from HubSpot, Fathom, and Apollo via direct HTTP API calls,
  cross-references data across sources, and delivers a structured brief with
  company context, relationship history, deal status, past meeting highlights,
  and recommended talking points. Use this skill when the user says
  "prep for my meeting with...", "meeting prep", "get ready for my call with...",
  "prep me for [company]", "what do I need to know before my call with...",
  or "brief me on [company/person]".
---

# Meeting Prep — Pre-Call Intelligence Brief

Your job is to build a comprehensive, cross-referenced meeting prep brief before JP gets on a sales or customer call. Pull from every available data source, verify data consistency across sources, and deliver a structured brief that makes JP the most prepared person on the call.

## API Authentication

All API calls use the Bash tool with `curl`, piping output through `python3 -m json.tool` (or `python3 -c '...'`) for JSON processing. Read API keys from `~/.claude/.api-keys.json` at the start of every run.

| Service    | Base URL                              | Auth Method                          | Key path in `.api-keys.json` |
|------------|---------------------------------------|--------------------------------------|------------------------------|
| HubSpot    | `https://api.hubapi.com`              | `Authorization: Bearer <KEY>`        | `keys.hubspot.key`           |
| Fathom  | `MCP: mcp__claude_ai_Fathom__*`    | `Authorization: Bearer <KEY>`        | _none — MCP_         |
| Apollo     | `https://api.apollo.io`               | `X-Api-Key: <KEY>`                   | `keys["apollo.io"].key`      |

### HubSpot Deal Pipeline Stage Mapping

Use this mapping to translate internal stage IDs to human-readable names:

| Stage ID                  | Stage Name            |
|---------------------------|-----------------------|
| `appointmentscheduled`    | Inbound Received      |
| `qualifiedtobuy`          | Outreach Started      |
| `presentationscheduled`   | Meeting Booked        |
| `decisionmakerboughtin`   | Discovery Completed   |
| `contractsent`            | SQL                   |
| `3249938160`              | Pilot Started         |
| `closedwon`               | Proposal Sent         |
| `1423313647`              | Verbal Yes            |
| `1423313648`              | Closed Won            |

Note: The `closedwon` ID is misleadingly named — it actually maps to "Proposal Sent", not a closed-won state. The real Closed Won stage is `1423313648`.

## Trigger Patterns

Activate this skill when the user says any of the following:
- "prep for my meeting with [company/person]"
- "meeting prep [company/person]"
- "get ready for my call with [company/person]"
- "prep me for [company/person]"
- "what do I need to know before my call with [company/person]"
- "brief me on [company/person]"
- "prep [company/person]"
- "call prep [company/person]"

## Input Parsing

Extract the following from the user's request:
- **Company name** (required) — the organization being met with
- **Person name** (optional) — specific contact(s) at the company
- **Meeting date/time** (optional) — when the meeting is scheduled

If only a person name is given, use HubSpot and Apollo to resolve their company. If ambiguous, ask the user to clarify before proceeding.

## Data Collection Workflow

All data collection uses direct HTTP API calls via `curl` in the Bash tool. Parse JSON responses with `python3`.

### Step 1: Resolve Identifiers

Start by finding the company and contact in HubSpot so you have IDs for subsequent queries.

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/companies/search" \
  -H "Authorization: Bearer <HUBSPOT_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [{
      "filters": [{
        "propertyName": "name",
        "operator": "CONTAINS_TOKEN",
        "value": "<company name>"
      }]
    }],
    "properties": ["name", "domain", "industry", "numberofemployees", "city", "state",
                    "country", "phone", "description", "hs_lastmodifieddate",
                    "notes_last_updated", "createdate", "hubspot_owner_id",
                    "hs_num_open_deals", "hs_total_deal_value"],
    "limit": 5
  }' | python3 -m json.tool
```

If a person name was provided:
```bash
curl -s "https://api.hubapi.com/crm/v3/objects/contacts/search" \
  -H "Authorization: Bearer <HUBSPOT_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [{
      "filters": [
        { "propertyName": "firstname", "operator": "CONTAINS_TOKEN", "value": "<first name>" },
        { "propertyName": "lastname", "operator": "CONTAINS_TOKEN", "value": "<last name>" }
      ]
    }],
    "properties": ["firstname", "lastname", "email", "jobtitle", "phone",
                    "company", "hs_lead_status", "lifecyclestage", "createdate",
                    "notes_last_updated", "hs_sales_email_last_replied",
                    "hs_email_last_reply_date", "hubspot_owner_id",
                    "hs_sequences_is_enrolled"],
    "limit": 5
  }' | python3 -m json.tool
```

If no person name was provided, search for all contacts associated with the company.

### Step 2: Pull All Data Sources (run in parallel)

#### 2A. HubSpot — Deals

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/deals/search" \
  -H "Authorization: Bearer <HUBSPOT_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [{
      "filters": [{
        "propertyName": "associations.company",
        "operator": "EQ",
        "value": "<companyId>"
      }]
    }],
    "properties": ["dealname", "amount", "dealstage", "pipeline", "closedate",
                    "createdate", "hs_lastmodifieddate", "hubspot_owner_id",
                    "hs_deal_stage_probability", "description",
                    "notes_last_updated", "hs_is_closed_won",
                    "hs_is_closed", "hs_acv", "hs_mrr"],
    "limit": 20
  }' | python3 -m json.tool
```

If company association search does not work, search by deal name containing the company name as a fallback.

To get pipeline stage definitions (verify against the stage mapping table above):
```bash
curl -s "https://api.hubapi.com/crm/v3/pipelines/deals" \
  -H "Authorization: Bearer <HUBSPOT_KEY>" | python3 -m json.tool
```

#### 2B. HubSpot — Engagement History

Search for contacts associated with the company to understand the full engagement timeline:
```bash
curl -s "https://api.hubapi.com/crm/v3/objects/contacts/search" \
  -H "Authorization: Bearer <HUBSPOT_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [{
      "filters": [{
        "propertyName": "company",
        "operator": "CONTAINS_TOKEN",
        "value": "<company name>"
      }]
    }],
    "properties": ["firstname", "lastname", "email", "jobtitle", "phone",
                    "hs_lead_status", "lifecyclestage", "createdate",
                    "notes_last_updated", "hs_sales_email_last_replied",
                    "hs_email_last_reply_date", "hs_email_sends_since_last_engagement",
                    "num_notes", "num_contacted_notes", "hs_sequences_is_enrolled",
                    "hs_analytics_num_page_views", "hs_analytics_num_visits"],
    "limit": 20
  }' | python3 -m json.tool
```

#### 2C. Fathom — Past Meeting Transcripts

Search for meetings with this company/person using the GraphQL API. Note: `summary.action_items` is a string (not an array), and `date` is Unix milliseconds.

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

Also try searching by person name if provided (same query, filter by person name).

For each relevant meeting found, pull the full summary by transcript ID:
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

Extract from each meeting:
- Key discussion topics and decisions
- Pain points mentioned by the prospect/customer
- Pricing or budget discussions (exact numbers)
- Action items assigned to either party
- Objections raised
- Competitors mentioned
- Timeline or urgency signals
- Direct quotes that reveal priorities or concerns

#### 2D. Apollo — Company Enrichment

```bash
curl -s "https://api.apollo.io/v1/organizations/enrich?domain=<company domain from HubSpot>" \
  -H "X-Api-Key: <APOLLO_KEY>" | python3 -m json.tool
```

Extract:
- Company size (headcount, headcount growth)
- Funding information (total raised, last round, investors)
- Industry and sub-industry
- Technology stack
- LinkedIn URL
- Key executives
- Annual revenue estimate
- Recent news or job postings

If domain is not available, search by name:
```bash
curl -s -X POST "https://api.apollo.io/v1/mixed_companies/search" \
  -H "X-Api-Key: <APOLLO_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "q_organization_name": "<company name>",
    "per_page": 3
  }' | python3 -m json.tool
```

#### 2E. Apollo — Contact Enrichment

If a specific person is the meeting attendee:
```bash
curl -s -X POST "https://api.apollo.io/v1/people/match" \
  -H "X-Api-Key: <APOLLO_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"email": "<contact email>"}' | python3 -m json.tool
```

Or if no email:
```bash
curl -s -X POST "https://api.apollo.io/v1/mixed_people/search" \
  -H "X-Api-Key: <APOLLO_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "q_person_name": "<person name>",
    "q_organization_name": "<company name>",
    "per_page": 3
  }' | python3 -m json.tool
```

Extract:
- Current title and seniority
- LinkedIn profile URL
- Previous companies and roles
- Time in current role
- Department

#### 2F. Apollo — Job Postings (Buying Signals)

```bash
curl -s "https://api.apollo.io/v1/organizations/<apollo_org_id>/job_postings" \
  -H "X-Api-Key: <APOLLO_KEY>" | python3 -m json.tool
```

Look for:
- Hiring for roles related to Solum's value prop (billing, RCM, operations, tech)
- Growth signals (lots of clinical hiring = scaling)
- Pain signals (hiring for roles Solum could replace or augment)

### Step 3: Internal Fact-Check Layer

Before assembling the brief, cross-reference data across sources. Check for and flag:

#### Data Consistency
- **Title mismatch**: Does the contact's title in HubSpot match Apollo? If not, note which is likely current.
- **Company size discrepancy**: Does HubSpot's employee count match Apollo's? Flag if >20% difference.
- **Deal amount vs. transcript**: If Fathom transcripts mention specific pricing ($X/mo, $X/yr), compare against the HubSpot deal amount. Flag any discrepancy with exact quotes.
- **Contact info**: Is the email/phone in HubSpot consistent with Apollo?

#### Staleness Detection
- **Deal stage age**: Calculate days in current stage. Flag if >30 days with a warning.
- **Last activity gap**: Calculate days since last touchpoint (email, call, meeting, note). Flag if >14 days.
- **Close date accuracy**: Is the close date in the past? Has it been pushed more than once?
- **Stale contact data**: If HubSpot contact was last modified >90 days ago, note the data may be outdated.

#### Action Item Tracking
- Review action items from previous Fathom meetings.
- Cross-reference against HubSpot notes and activity timeline.
- Classify each action item as:
  - **COMPLETED**: Evidence of follow-through in HubSpot activity or subsequent meeting
  - **PENDING**: No evidence of completion
  - **UNKNOWN**: Cannot determine status from available data

#### Missing Data Flags
- No deal associated with this company? Flag it.
- No email history? Flag it.
- No previous meetings? Note this is a first meeting.
- Contact has no title? Flag for update.

### Step 4: Assemble the Brief

Present the brief in this exact format. Keep it dense and scannable. No filler.

```
================================================================
  MEETING PREP: [Company Name]
  [Meeting Date if known] | Prepared [today's date]
================================================================

ATTENDEES
---------
[Name] — [Title] (from [source: HubSpot/Apollo])
[Name] — [Title]
  LinkedIn: [URL if available]
  Email: [email] | Phone: [phone]
  Time in role: [X months/years, from Apollo]
  Previous: [previous company/role if notable]

COMPANY SNAPSHOT
-----------------
Industry:      [industry]
Size:          [employee count] ([growth trend if available])
Location:      [city, state]
Founded:       [year]
Funding:       [total raised / last round / investors]
Revenue est:   [if available from Apollo]
EMR/Tech:      [technology stack from Apollo]
Domain:        [website]
LinkedIn:      [company LinkedIn URL]

Key facts:
- [Notable fact 1 from Apollo enrichment]
- [Notable fact 2]
- [Recent job postings relevant to Solum]

RELATIONSHIP HISTORY
---------------------
First contact:     [date from HubSpot createdate]
Total touchpoints: [count of emails + calls + meetings + notes]
Last interaction:  [date and type — email/call/meeting]
Days since last:   [calculated]

Timeline:
  [Date] — [Event: first email, first call, demo, proposal sent, etc.]
  [Date] — [Event]
  [Date] — [Event]
  ...

DEAL STATUS
------------
Deal:          [deal name]
Stage:         [current stage name] (since [date])
Days in stage: [calculated] [FLAG if >30 days]
Amount:        $[amount] ([monthly/annual])
Close date:    [date] [FLAG if past due or pushed]
Pipeline:      [pipeline name]
Probability:   [%]
Owner:         [name]

[If multiple deals, list each]
[If no deal exists: "No deal record found — consider creating one after this meeting"]

PREVIOUS MEETING HIGHLIGHTS
-----------------------------
[Meeting date] — [meeting title]
  Key topics discussed:
  - [topic 1]
  - [topic 2]

  Their pain points (in their words):
  - "[direct quote from transcript]"
  - "[direct quote]"

  Decisions made:
  - [decision 1]

  Competitors mentioned:
  - [competitor name + context]

  Action items from this meeting:
  - [JP] [action item] — Status: [COMPLETED/PENDING/UNKNOWN]
  - [Prospect] [action item] — Status: [COMPLETED/PENDING/UNKNOWN]

[Repeat for each past meeting, most recent first]
[If no meetings found: "No previous meetings on record. This appears to be a first meeting."]

THEIR PRIORITIES (from their own words)
-----------------------------------------
Based on transcript analysis and email history:
1. [Priority 1 — with source: "quote" from meeting on date]
2. [Priority 2 — with source]
3. [Priority 3 — with source]

[If no transcript data: "No direct quotes available. Priorities inferred from deal context and industry."]

OPEN QUESTIONS / RISKS
------------------------
- [Unresolved question from past meetings]
- [Risk factor: e.g., "No executive sponsor identified"]
- [Risk factor: e.g., "Close date has been pushed twice"]
- [Risk factor: e.g., "Competitor [X] was mentioned favorably in last call"]
- [Missing info: "Budget not discussed yet"]
- [Missing info: "Decision-making process unclear"]

RECOMMENDED TALKING POINTS
----------------------------
Lead with:
1. [Specific opener based on their priorities and last interaction]
2. [Reference to specific pain point they mentioned]

Address:
3. [Pending action item or follow-up from last meeting]
4. [Objection handling for known concerns]

Advance the deal:
5. [Specific ask to move to next stage]
6. [Timeline or urgency angle based on their signals]

Avoid:
- [Topic or approach to stay away from, with reason]
- [Sensitive area based on past interactions]

FACT-CHECK NOTES
-----------------
[List any discrepancies found during cross-referencing]
- [e.g., "Title mismatch: HubSpot says 'Director of Ops', Apollo says 'VP Operations' — Apollo updated more recently, likely current"]
- [e.g., "Deal amount is $50K in HubSpot but transcript from Feb 12 discussed $4K/month ($48K/yr) — minor discrepancy, verify on call"]
- [e.g., "Action item from Jan meeting (send case study) — no evidence of completion in HubSpot"]

[If no discrepancies: "All data consistent across sources."]

DATA FRESHNESS
---------------
HubSpot company: last modified [date]
HubSpot contacts: last modified [date]
HubSpot deal: last modified [date]
Fathom: [X] meetings found, most recent [date]
Apollo: enrichment as of [today]
================================================================
```

## Error Handling

- If HubSpot returns no company match: try alternate spellings, abbreviations, or domain search. If still nothing, note "Company not found in HubSpot" and continue with Apollo data.
- If Fathom returns no meetings: say "No previous meetings recorded." Continue with other sources.
- If Apollo enrichment fails: skip the company snapshot details that require Apollo. Note the source was unavailable.
- If any API call fails: continue with available data. Note which sources were unavailable at the top of the brief.
- Never skip the brief because one source failed. Deliver what you have, clearly noting gaps.

## Tone & Style

- Dense, scannable, no fluff. This is a working document, not a narrative.
- Data-first. Lead with facts, not opinions.
- Direct quotes from transcripts are gold. Always include them when available.
- Every recommendation must be grounded in data from the sources. No generic sales advice.
- Flag unknowns explicitly. "Unknown" is better than a guess.
- The entire brief should be readable in under 3 minutes.

## Required APIs

| Service    | Endpoints Used                                                                 |
|------------|--------------------------------------------------------------------------------|
| HubSpot    | `POST /crm/v3/objects/{objectType}/search`, `GET /crm/v3/pipelines/deals`     |
| Fathom  | `list_meetings`, `get_meeting_transcript`, `get_meeting_summary`                         |
| Apollo     | `GET /v1/organizations/enrich`, `POST /v1/people/match`, `POST /v1/mixed_people/search`, `POST /v1/mixed_companies/search`, `GET /v1/organizations/{id}/job_postings` |

All calls are executed via the Bash tool using `curl -s` with appropriate headers, piping JSON output through `python3` for parsing and filtering.

## Post-Brief Actions

After delivering the brief, ask:
1. "Want me to pull the full transcript from any of these meetings?"
2. "Should I update any stale data in HubSpot before your call?"
3. "Need me to draft any follow-up materials for after the meeting?"
