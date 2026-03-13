---
name: conference-prep
description: >
  Full conference preparation workflow with two parallel tracks: (1) Lead intelligence pipeline
  that extracts attendees from screenshots/lists, classifies ICPs for Solum Health, enriches
  via Apollo API, verifies emails via Hunter.io, and prospects participating companies to produce
  two output lists (ICP Attendees + ICP from Participating Companies); (2) Branded curated agenda
  document with top session picks, "Why attend" insights, and JP Montoya contact info. Use this
  skill whenever the user mentions conference prep, conference preparation, conference intro,
  pre-conference planning, "who's going to [conference]", attendee enrichment, conference
  prospecting, attendee list analysis, pre-conference research, or any request involving preparing
  for an upcoming conference. Even if the user just says "prep for [conference]" or "get ready
  for [event]", assume they want the full workflow unless they say otherwise.
---

# Conference Prep

Two parallel tracks that run together: build your prospect lists AND know exactly where to
spend your time at the event.

## Core Principle

This skill produces two things: actionable lead intelligence (who to talk to and how to reach
them) and a curated agenda document that makes JP Montoya look like the most prepared person
in the room. The prospect lists are for internal use. The agenda document is shareable with
clients and prospects as a value-add.

## The Workflow

### Phase 0: Conference Confirmation

Before anything else, confirm the conference details with the user:
1. Ask for the conference name if not provided
2. Search the web for: official website, dates, location, agenda URL, attendee/sponsor list URL
3. Present what you found and confirm: "Is this the right conference? [Name], [Dates], [Location]"
4. Ask the user for their attendee data source (screenshot, PDF, CSV, URL, or "I don't have one yet")

Only proceed after confirmation. Getting the wrong conference wastes everything downstream.

### Phase 1: Parallel Execution

Launch all of these simultaneously. They don't depend on each other.

#### Track A: Lead Intelligence Pipeline

Run as a Task agent. This is the heavy lift. Read `references/icp-criteria.md` for the full
ICP classification rules.

**Step A1 — Extract Attendees**

Handle whatever input format the user provides:
- **Screenshot/Image**: Read the image directly (Claude has vision). Extract every name, title,
  and company visible. If the image is a conference app screenshot, attendee directory, or
  badge photo, parse accordingly.
- **PDF**: Read the PDF and extract attendee data.
- **CSV/Text list**: Parse directly.
- **URL**: Fetch the page and extract attendee data.
- **No list available**: Skip to Step A4 (company prospecting only).

Output a structured list: `[{name, title, company}]`

**Step A2 — ICP Classification**

For each extracted attendee, classify against Solum Health's ICP criteria (see
`references/icp-criteria.md`). Assign:
- **ICP Match**: Yes / No / Maybe
- **ICP Tier**: Primary / Secondary / Not ICP
- **Role Category**: Practice Owner, C-Suite, VP/Director Ops, Clinic Manager, Billing/RCM,
  Clinical Director, Other
- **Company Type**: Behavioral Health, ABA, PT/OT/Speech, Mental Health, SUD Treatment,
  Multi-Specialty, Virtual/Telehealth, Other
- **Reason**: Brief explanation of why they are/aren't ICP

Only proceed to enrichment for ICP Match = Yes or Maybe. Skip "No" entirely to save API calls.

**Step A3 — Apollo Enrichment (ICPs only)**

Use Apollo MCP tools to enrich each ICP match. The goal: get verified contact info, company
size, and additional context.

For each ICP person:
1. First try `apollo_people_match` with their name + company domain
2. If no match, try `apollo_mixed_people_api_search` with name + company name
3. Extract: email, phone, LinkedIn URL, company size, company revenue, current title

For efficiency with large lists (10+ people), use `apollo_people_bulk_match` instead of
individual calls.

Also run `apollo_organizations_enrich` on each unique company to get:
- Employee count, revenue range, industry classification
- This helps refine ICP scoring (a solo practice vs. a 200-person group matters)

**Step A4 — Company Prospecting (runs in parallel with A1-A3)**

This track finds ICPs at companies that are attending/sponsoring the conference, even if
those specific people aren't on the attendee list.

1. Extract all company names from the conference sponsor list, exhibitor list, and attendee
   company names
2. For each company that looks like it could be in behavioral health / therapy / healthcare
   operations:
   - Run `apollo_mixed_companies_search` to find the company
   - Run `apollo_organizations_enrich` to get company details
   - Run `apollo_mixed_people_api_search` filtered by ICP titles at that company
     (search for: "CEO", "COO", "Owner", "VP Operations", "Director of Operations",
     "Clinic Manager", "Office Manager", "Billing Director")
3. Classify found people against ICP criteria
4. These go into the "ICP Non-Attendees (Participating Companies)" list

**Step A5 — Email Verification via Hunter.io**

After Apollo enrichment, verify every email address through Hunter.io.

Use WebFetch to call the Hunter.io API:
```
GET https://api.hunter.io/v2/email-verifier?email={EMAIL}&api_key={HUNTER_API_KEY}
```

Check for the Hunter.io API key:
1. Look for it in environment variable `HUNTER_API_KEY`
2. If not found, ask the user for their Hunter.io API key
3. Store it for the session using the api-key-manager skill if available

Only include contacts where Hunter.io returns `status` = "valid" or "accept_all".
Mark "unknown" as unverified but still include with a flag.
Exclude "invalid" and "disposable" entirely.

**Step A6 — Output: Two Lists**

Produce two structured outputs:

**List 1: ICP Attendees** (confirmed on attendee list + verified)
Columns: Name | Title | Company | Company Type | ICP Tier | Role Category | Email |
Email Status | Phone | LinkedIn | Company Size | Notes

**List 2: ICP from Participating Companies** (found via company prospecting, not on attendee list)
Same columns as List 1, plus: Source Company (how we found them)

Save both lists as:
- CSV files for easy import into CRM/Apollo sequences
- A formatted summary in the prep document

#### Track B: Curated Agenda Document

Run as a Task agent. Read `references/brand-guide.md` for voice and brand guidelines.
Read the template at `assets/prep-document-template.html` for the exact HTML structure
and styling to follow.

**Step B1 — Agenda Research**

Search the web for the conference's full agenda:
- Session titles, descriptions, times, tracks, locations
- Speaker names, titles, companies
- Networking events, receptions, breakfasts
- Any pre-conference workshops or special events

**Step B2 — Session Curation**

From the full agenda, select the 6-10 sessions most relevant to behavioral health
practice owners and operators. Prioritize sessions about:
1. AI and automation in healthcare operations
2. Revenue cycle, billing, denial management
3. Payer strategy, value-based care
4. Workforce retention and burnout
5. Practice growth and scaling
6. Technology adoption and digital transformation
7. M&A and consolidation trends
8. Patient access and intake optimization

For each selected session, write a "Why attend" insight paragraph that:
- Explains why this session matters for a practice owner/operator
- References specific speakers and what makes their perspective valuable
- Connects the session topic to real operational impact (revenue, time, margin, growth)
- Sounds like a knowledgeable colleague giving advice, not a summary

**Step B3 — Generate Branded HTML Document**

Generate an HTML file following the template structure in `assets/prep-document-template.html`.
The document must include:

1. **Header**: Solum Health logo + conference title + "Executive Guide for Healthcare Leaders"
   subtitle + date/venue badge
2. **Intro paragraph**: 2-3 sentences positioning why this conference matters and what
   the curated picks focus on. Mention the total number of sessions and how many were selected.
3. **Day sections**: Organized by day with colored day-label pills
4. **Session cards**: Grid layout with time/track column + content column containing title,
   speakers, and "Why attend" insight box
5. **Networking callouts**: Teal-background bars for receptions, lunches, networking breaks
6. **Concurrent session notes**: When sessions overlap, add a note helping the reader choose
7. **Footer**: JP Montoya contact card with name, title, email, phone, website

Brand colors (from brand guide):
- Navy primary: #0E1C36 (or #011C40 for the HTML variant)
- Accent blue: #468AF7
- Teal: #70D3C6 / #267688
- Background: #F2F2F9
- Surface: #ffffff

Font: DM Sans (from Google Fonts) for the HTML version.

**Step B4 — Humanization Pass**

Run a quick QA check on all "Why attend" text:
- No AI buzzwords (leverage, streamline, robust, comprehensive, etc.)
- No dashes as punctuation (use commas, periods, or restructure)
- Vary sentence length
- Sound like a practitioner giving advice, not a content marketer

### Phase 2: Assembly & Review

Once both tracks complete:

1. Save the curated agenda HTML to `~/[ConferenceName]_[Year]_Curated_Agenda.html`
2. Save ICP Attendees CSV to `~/[ConferenceName]_[Year]_ICP_Attendees.csv`
3. Save ICP Companies CSV to `~/[ConferenceName]_[Year]_ICP_Companies.csv`
4. Open the HTML document for user review
5. Report:
   - Total attendees extracted
   - ICP matches found (with breakdown by tier)
   - Emails verified vs. unverified
   - Additional ICPs found via company prospecting
   - Number of sessions curated from total agenda
6. Ask: "Want me to adjust anything? I can re-score ICPs, add/remove sessions, or
   change the document style."

## Important Notes

- **Apollo API limits**: Be mindful of rate limits. Batch where possible. Don't enrich
  non-ICPs.
- **Hunter.io costs**: Each verification costs a credit. Only verify emails that came from
  Apollo enrichment (already likely valid). Don't verify obviously bad emails.
- **Privacy**: The attendee data and enriched lists are for internal sales use only. The
  curated agenda document is the shareable, client-facing piece.
- **The agenda document is the value-add**. It positions JP as someone who does homework,
  curates signal from noise, and shares it generously. That's the rapport builder.

## File Dependencies

- **Logo**: `assets/solum_logo.png` or `~/solum_logo.png`
- **HTML Template**: `assets/prep-document-template.html` (reference for layout/styling)
- **ICP Criteria**: `references/icp-criteria.md`
- **Brand Guide**: `references/brand-guide.md`
- **Apollo**: Apollo MCP tools (must be connected)
- **Hunter.io**: API key required (check env var `HUNTER_API_KEY` or ask user)
- **Web access**: WebSearch + WebFetch for agenda research

## Output

Default output paths:
- `~/[ConferenceName]_[Year]_Curated_Agenda.html`
- `~/[ConferenceName]_[Year]_ICP_Attendees.csv`
- `~/[ConferenceName]_[Year]_ICP_Companies.csv`
