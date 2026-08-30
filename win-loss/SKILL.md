---
name: win-loss
description: Systematic win-loss analysis across all deals. Use when someone says "win-loss analysis", "why did we lose [deal]", "why did we win [deal]", "deal analysis", "analyze our pipeline", "what patterns do you see in our deals", or asks about deal outcomes, pipeline health, or sales patterns.
---

# Win-Loss Analysis

Perform rigorous, data-driven win-loss analysis by pulling from HubSpot, Fathom, and Apollo via direct HTTP API calls, then cross-referencing everything before drawing conclusions.

## API Authentication

All API calls use the Bash tool with `curl`, piped through `python3 -m json.tool` (or `python3 -c '...'`) for parsing.

Load keys at the start of every run:

```bash
KEYS=$(cat ~/.claude/.api-keys.json)
```

| Service | Auth Method | Base URL | Header |
|---------|------------|----------|--------|
| HubSpot | Bearer token | `https://api.hubapi.com` | `Authorization: Bearer <key>` |
| Fathom | Bearer token | `MCP: mcp__claude_ai_Fathom__*` | `Authorization: Bearer <key>` |
| Apollo | API key header | `https://api.apollo.io/v1` | `X-Api-Key: <key>` |

Key extraction (bash):

```bash
HS_KEY=$(python3 -c "import json; print(json.load(open('$HOME/.claude/.api-keys.json'))['keys']['hubspot']['key'])")
AP_KEY=$(python3 -c "import json; print(json.load(open('$HOME/.claude/.api-keys.json'))['keys']['apollo.io']['key'])")
```

## HubSpot Pipeline Stage Mapping (Revenue Rocket)

Hardcoded stage IDs for the Revenue Rocket pipeline:

| Stage | ID | Probability |
|-------|----|-------------|
| Appointment Scheduled | `appointmentscheduled` | 20% |
| Qualified to Buy | `qualifiedtobuy` | 40% |
| Presentation Scheduled | `presentationscheduled` | 60% |
| Decision Maker Bought-In | `decisionmakerboughtin` | 80% |
| Contract Sent | `contractsent` | 90% |
| Closed Won | `closedwon` | 100% |
| Closed Lost | `closedlost` | 0% |

## Execution Steps

### Step 1: Determine Scope

Ask the user (or infer from their request):
- **Single deal analysis** — "why did we lose Action Seating" or "analyze the [Company] deal"
- **Portfolio analysis** — "win-loss analysis", "analyze our pipeline", "what patterns do you see"

### Step 2: Pull All Data

Regardless of scope, gather everything first. Do NOT skip any source.

#### 2a. HubSpot — Deal Data

Use direct curl to the HubSpot CRM Search API:

1. **All deals** — POST to `https://api.hubapi.com/crm/v3/objects/deals/search`

```bash
curl -s -X POST "https://api.hubapi.com/crm/v3/objects/deals/search" \
  -H "Authorization: Bearer $HS_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 100,
    "properties": [
      "dealname", "amount", "dealstage", "closedate", "createdate",
      "pipeline", "hs_lastmodifieddate", "hs_deal_stage_probability",
      "closed_lost_reason", "closed_won_reason", "notes_last_updated",
      "num_notes", "num_associated_contacts", "hs_analytics_source"
    ],
    "filterGroups": []
  }' | python3 -m json.tool
```

2. **Associated contacts** for each deal:

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/deals/$DEAL_ID/associations/contacts" \
  -H "Authorization: Bearer $HS_KEY" | python3 -m json.tool
```

Then fetch each contact:

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/contacts/$CONTACT_ID?properties=firstname,lastname,email,jobtitle,company" \
  -H "Authorization: Bearer $HS_KEY" | python3 -m json.tool
```

3. **Associated companies** for each deal:

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/deals/$DEAL_ID/associations/companies" \
  -H "Authorization: Bearer $HS_KEY" | python3 -m json.tool
```

Then fetch each company:

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/companies/$COMPANY_ID?properties=name,domain,industry,numberofemployees" \
  -H "Authorization: Bearer $HS_KEY" | python3 -m json.tool
```

4. **Deal notes and activity** — search engagements associated with the deal:

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/deals/$DEAL_ID/associations/notes" \
  -H "Authorization: Bearer $HS_KEY" | python3 -m json.tool
```

5. **Stage history** — track how long each deal spent in each stage. Use the deal properties `hs_date_entered_*` and `hs_date_exited_*` for each stage.

#### 2b. Fathom — Conversation Intelligence

Use the Fathom MCP tools (no curl, no key):

1. **Fetch recent transcripts**:

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

**Important notes on Fathom response format:**
- `date` is Unix milliseconds (divide by 1000 for epoch seconds)
- `action_items` is a string (not an array)
- `participants` is a list of email strings

2. **Get a specific transcript by ID** (for full content):

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

3. **Match transcripts to deals** by searching `participants` for contact email addresses from HubSpot.

4. Extract from each transcript:
   - Direct quotes about pain points
   - Objections raised (pricing, timing, competition, internal resistance)
   - Competitor names mentioned
   - Pricing discussions (what was quoted, reactions)
   - Buying signals ("when can we start", "who else needs to approve")
   - Decision-maker identification
   - Next steps discussed vs. what actually happened

#### 2c. Apollo — Company Enrichment

Use direct curl to the Apollo API with `X-Api-Key` header:

1. **Enrich each company** associated with deals:

```bash
curl -s "https://api.apollo.io/v1/organizations/enrich?domain=$COMPANY_DOMAIN" \
  -H "X-Api-Key: $AP_KEY" | python3 -m json.tool
```

Fields returned: company size (employees), industry and sub-industry, annual revenue, funding stage and total raised, technologies used, location.

2. **Enrich key contacts** by email:

```bash
curl -s -X POST "https://api.apollo.io/v1/people/match" \
  -H "X-Api-Key: $AP_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "contact@example.com"
  }' | python3 -m json.tool
```

Fields returned: title, seniority, department.

3. Use this to build ICP pattern analysis.

### Step 3: Internal Fact-Check Layer

Before any analysis, run these integrity checks. Flag every issue found.

#### Data Quality Checks

| Check | How | Flag If |
|-------|-----|---------|
| Stale close dates | Compare `closedate` to today | Close date is in the past but deal is still open |
| Zombie deals | Check activity on closed-lost deals | Closed-lost deal has emails/calls in last 30 days |
| Ghost deals | Check `num_notes` and last activity | Deal has zero notes or no activity in 60+ days |
| Amount mismatches | Compare HubSpot `amount` to pricing discussed in Fathom | Amount differs by more than 20% from what was quoted verbally |
| Missing contacts | Check `num_associated_contacts` | Deal has zero associated contacts |
| Stage bottlenecks | Calculate days in current stage | Deal has been in same stage for 2x the average |
| Pipeline fiction | Check deals marked "closing this month" | No activity in last 14 days on a deal closing within 30 days |

#### Cross-Reference Checks

- If HubSpot says "closed lost — went with competitor", search Fathom for which competitor and why
- If HubSpot says "closed lost — pricing", check Fathom for what price was quoted and what their reaction was
- If a deal has no close reason in HubSpot, attempt to find the reason in Fathom transcripts
- Compare deal timeline in HubSpot stages vs. actual meeting cadence in Fathom

### Step 4A: Single Deal Analysis

When analyzing a specific deal, produce this report:

```
## Win-Loss: [Deal Name]

### Deal Snapshot
| Field | Value |
|-------|-------|
| Company | [name] |
| Amount | $[amount] |
| Stage | [stage] |
| Created | [date] |
| Closed | [date] |
| Days in Pipeline | [n] |
| Outcome | Won / Lost / Open |
| Loss Reason (HubSpot) | [reason or "not recorded"] |

### Company Profile (Apollo)
- Industry: [industry]
- Size: [employees]
- Revenue: [revenue]
- Funding: [stage, amount]
- ICP Fit: Strong / Moderate / Weak — [why]

### Timeline
Map every touchpoint chronologically:
- [Date] — First contact (source: [how they came in])
- [Date] — Discovery call (Fathom transcript available: yes/no)
- [Date] — Stage moved to [stage]
- [Date] — Demo / proposal sent
- [Date] — Last activity
- [Date] — Outcome

### What They Said (from Fathom transcripts)
Pull DIRECT QUOTES. Do not paraphrase. Organize by theme:

**Pain Points:**
> "[exact quote]" — [Contact Name], [Date]

**Objections:**
> "[exact quote]" — [Contact Name], [Date]

**Competitor Mentions:**
> "[exact quote]" — [Contact Name], [Date]

**Buying Signals (if any):**
> "[exact quote]" — [Contact Name], [Date]

**Pricing Reactions:**
> "[exact quote]" — [Contact Name], [Date]

### Pricing Analysis
- Amount in HubSpot: $[amount]
- What was discussed in calls: [details from Fathom]
- Match: Yes / No — [explain discrepancy]
- Price sensitivity level: Low / Medium / High

### Root Cause Analysis
Go beyond the surface. "Went dark" is not a root cause. Dig into:
1. **Primary cause** — the single biggest factor
2. **Contributing factors** — secondary issues that compounded
3. **Process failures** — what we could have done differently
4. **Timing factors** — was the timing right for them?

### Data Quality Issues
Flag anything found in the fact-check layer for this deal.

### Lessons
- **Repeat:** [what worked or would work again]
- **Change:** [what to do differently next time]
- **Watch for:** [early warning signs we missed]
```

### Step 4B: Portfolio Analysis

When analyzing all deals, produce this report:

```
## Win-Loss Portfolio Analysis
*Analysis Date: [today's date]*
*Deals Analyzed: [n won] + [n lost] + [n open] = [total]*

### Pipeline Metrics
| Metric | Value |
|--------|-------|
| Total Deals | [n] |
| Open Deals | [n] |
| Won | [n] |
| Lost | [n] |
| Win Rate | [%] |
| Avg Deal Size (Won) | $[amount] |
| Avg Deal Size (Lost) | $[amount] |
| Avg Sales Cycle (Won) | [days] |
| Avg Sales Cycle (Lost) | [days] |
| Pipeline Value (Open) | $[amount] |
| Weighted Pipeline | $[amount] |

### Stage Funnel
Show deals by stage with average days in stage and conversion rate to next stage:
| Stage | Deals | Avg Days | Conversion to Next |
|-------|-------|----------|-------------------|
| [stage] | [n] | [days] | [%] |

### Patterns in Wins
Analyze won deals for common traits:

**ICP Profile of Winning Deals:**
- Company size range: [range]
- Industries: [list]
- Common pain points: [list with frequency]
- Decision-maker titles: [list]
- Lead source: [breakdown]

**What Worked:**
- Messaging that resonated (with transcript evidence)
- Objections we overcame and how
- Average touchpoints to close

### Patterns in Losses
Analyze lost deals for common traits:

**Why We Lose:**
| Reason | Count | % of Losses |
|--------|-------|-------------|
| [reason] | [n] | [%] |

**Where Deals Stall:**
- Stage with highest drop-off: [stage]
- Average days before going dark: [days]

**Competitor Displacement:**
| Competitor | Times Mentioned | Deals Lost To | Key Differentiator They Cited |
|-----------|----------------|---------------|-------------------------------|
| [name] | [n] | [n] | [what prospects said] |

### Zombie Deals (Immediate Action Required)
Deals that need attention right now:

| Deal | Issue | Amount | Last Activity | Recommended Action |
|------|-------|--------|---------------|--------------------|
| [name] | Stale close date | $[x] | [date] | [action] |
| [name] | Closed lost but still active | $[x] | [date] | [action] |
| [name] | No activity 60+ days | $[x] | [date] | [action] |

### Data Quality Report
| Issue | Count | Deals Affected |
|-------|-------|----------------|
| Missing close reason | [n] | [list] |
| No associated contacts | [n] | [list] |
| No notes or activity | [n] | [list] |
| Amount = $0 or blank | [n] | [list] |

### Recommendations

**ICP Refinement:**
Based on win patterns, the ideal customer profile should be refined to:
- [specific, data-backed recommendations]

**Process Improvements:**
- [specific changes to sales process with evidence]

**Pricing Adjustments:**
- [data-backed pricing observations]

**Pipeline Hygiene:**
- [specific cleanup actions needed]

**Follow-Up List:**
Deals worth re-engaging and why:
| Deal | Why Re-engage | Suggested Approach |
|------|---------------|--------------------|
| [name] | [reason from transcript/activity] | [approach] |
```

## Rules

1. **Never guess.** If data is missing, say so. Do not fill in blanks with assumptions.
2. **Use direct quotes.** When citing what prospects said, pull exact quotes from Fathom transcripts. Paraphrasing loses the signal.
3. **Cross-reference everything.** HubSpot data alone is unreliable. Always verify against Fathom and Apollo.
4. **Flag data quality issues prominently.** Bad data leads to bad decisions. Surface every inconsistency.
5. **"Went dark" is not a root cause.** Dig deeper. Why did they go dark? What was the last thing discussed? Was there a trigger?
6. **Separate facts from interpretation.** Present the data first, then your analysis. Make it clear which is which.
7. **Be blunt.** This is an internal tool. Do not soften bad news. If the pipeline is fiction, say so.
8. **Include the "so what."** Every insight should connect to a specific action.
9. **Time-box the data pull.** If a data source is unavailable or returns errors, note it and continue with what you have. Do not block the entire analysis on one failed API call.
10. **Save the output.** Write the final report to `~/Documents/Claude/Agents/reports/win-loss-[date].md` so it is preserved.

## Related Skills

- pricing-strategy
- pricing-coach
