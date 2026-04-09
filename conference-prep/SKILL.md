---
name: conference-prep
description: >
  Full conference preparation workflow with two parallel tracks: (1) Lead intelligence pipeline
  that extracts attendees, classifies ICPs, enriches contacts via Apollo-first waterfall
  (Apollo → Crustdata → Hunter.io finder), validates ALL emails through Hunter.io verifier,
  outputs three ICP lists (Attendees, Non-Attendees, Participating Companies), and uploads
  validated leads to Instantly via API; (2) Branded curated agenda document with pre-execution
  data verification, top session picks, "Why attend" insights, and JP Montoya contact info.
  Use this skill whenever the user mentions conference prep, conference preparation, conference
  intro, pre-conference planning, "who's going to [conference]", attendee enrichment, conference
  prospecting, attendee list analysis, pre-conference research, or any request involving
  preparing for an upcoming conference. Even if the user just says "prep for [conference]"
  or "get ready for [event]", assume they want the full workflow unless they say otherwise.
---

# Conference Prep

Two parallel tracks that run together: build your prospect lists AND know exactly where to
spend your time at the event.

## Core Principle

This skill produces two things: actionable lead intelligence (who to talk to and how to reach
them) and a curated agenda document that makes JP Montoya look like the most prepared person
in the room. The prospect lists are for internal use. The agenda document is shareable with
clients and prospects as a value-add.

## Key Operating Rules

1. **Apollo-first enrichment**: Apollo is always the primary data source for contact-level
   enrichment. Only fall back to other sources when Apollo has gaps.
2. **Processing ledger**: Maintain an in-memory ledger tracking every contact through every
   enrichment and validation step. Structure: `{contact_id: {apollo: done|skipped, crustdata:
   done|skipped|not_needed, hunter_finder: done|skipped|not_needed, hunter_verifier:
   done|skipped, email, phone, linkedin, email_status, list_assignment}}`. Never run the same
   enrichment or verification call twice for the same contact.
3. **No duplicate API calls**: Before calling any enrichment or verification endpoint, check
   the ledger. If a contact already has a result from that source, skip it.
4. **Output paths**: ALL outputs go to `~/Documents/Claude/[ConferenceName]-[Year]/`. Create
   the project folder if it does not exist.
5. **Email validation is mandatory**: Every non-null email must pass Hunter.io email-verifier
   before inclusion in any output list. Only `status = "valid"` or `status = "accept_all"`
   emails are included. Do NOT send null or empty email strings to the verifier.
6. **Three output lists**: ICP Attendees, ICP Non-Attendees, ICP from Participating
   Companies. These are distinct populations with no overlap.

## API Configuration

All API keys are stored in `~/.claude/.api-keys.json`. Read this file at the start of
execution. Expected keys:

| Service | Key Name in JSON | Auth Method |
|---|---|---|
| Apollo | Use Apollo MCP tools directly | MCP connection |
| Crustdata | `crustdata` or `crustdata_api_key` | `Authorization: Token {KEY}` header |
| Hunter.io | `hunter` or `hunter_api_key` | Query param `api_key={KEY}` |
| Instantly | `instantly` or `instantly_api_key` | `Authorization: Bearer {KEY}` header |

If a key is missing, ask the user before proceeding. Use the api-key-manager skill to store
any newly provided keys.

## The Workflow

### Phase 0: Conference Confirmation

Before anything else, confirm the conference details with the user:
1. Ask for the conference name if not provided
2. Search the web for: official website, dates, location, agenda URL, attendee/sponsor list URL
3. Present what you found and confirm: "Is this the right conference? [Name], [Dates], [Location]"
4. Ask the user for their attendee data source (screenshot, PDF, CSV, URL, or "I don't have one yet")
5. Create the project output folder: `~/Documents/Claude/[ConferenceName]-[Year]/`
6. Read `~/.claude/.api-keys.json` and verify all required API keys are present (Crustdata,
   Hunter.io, Instantly). Apollo uses MCP tools. If any key is missing, ask the user now.

Only proceed after confirmation. Getting the wrong conference wastes everything downstream.

### Phase 1: Parallel Execution

Launch Track A and Track B simultaneously. They don't depend on each other.

---

#### Track A: Lead Intelligence Pipeline

Run as a Task agent. This is the heavy lift. Read `references/icp-criteria.md` for the full
ICP classification rules.

Initialize the processing ledger at the start of Track A.

**Step A1 — Extract Attendees**

Handle whatever input format the user provides:
- **Screenshot/Image**: Read the image directly (Claude has vision). Extract every name, title,
  and company visible. If the image is a conference app screenshot, attendee directory, or
  badge photo, parse accordingly.
- **PDF**: Read the PDF and extract attendee data.
- **CSV/Text list**: Parse directly.
- **URL**: Fetch the page and extract attendee data.
- **No list available**: Skip to Step A4 (company prospecting only). Mark A1-A3 as skipped.

Output a structured list: `[{first_name, last_name, title, company, source: "attendee_list"}]`

Also extract all company names from the conference sponsor list, exhibitor list, and attendee
company names. Store these as the `participating_companies` list for use in A4.

**Step A2 — ICP Classification**

For each extracted attendee, classify against Solum Health's ICP criteria (see
`references/icp-criteria.md`). Assign:
- **ICP Match**: Yes / No / Maybe
- **ICP Tier**: Primary / Secondary / Not ICP
- **Role Category**: Practice Owner, C-Suite, VP/Director Ops, Clinic Manager, Billing/RCM,
  Clinical Director, Intake/Access, PE/Investor, Consultant, Other
- **Company Type**: Behavioral Health, ABA, PT/OT/Speech, Mental Health, SUD Treatment,
  Multi-Specialty, Virtual/Telehealth, Residential+, Pediatric Therapy, IDD Services,
  PE-Backed Platform, Other Healthcare
- **Reason**: Brief explanation of why they are/aren't ICP

Only proceed to enrichment for ICP Match = Yes or Maybe. Skip "No" entirely to save API calls.
Add each ICP/Maybe contact to the ledger with `list_assignment: "icp_attendees"`.

**Empty-set guard**: If zero contacts match ICP = Yes or Maybe, skip A3-A6 for attendees.
Report to user: "No ICP matches found in the attendee list. Proceeding with company
prospecting only (A4)."

**Step A3 — Apollo Enrichment (Contact-Level, ICPs Only)**

Apollo is the PRIMARY enrichment source. Use Apollo MCP tools for contact-level enrichment
of each ICP match. The goal: get verified contact info, company size, and context.

For each ICP person:
1. First try `apollo_people_match` with their first_name, last_name, and company domain
   (or company name if domain unknown)
2. If no match, try `apollo_mixed_people_api_search` with name + company name
3. Extract and store: **email, phone, LinkedIn URL**, current title, company size, company revenue

For efficiency with large lists (10+ people), use `apollo_people_bulk_match` instead of
individual calls.

Also run `apollo_organizations_enrich` on each unique company to get:
- Employee count, revenue range, industry classification
- This helps refine ICP scoring (a solo practice vs. a 200-person group matters)

Update the ledger: mark `apollo: done` for each contact. Record which fields were found
(email, phone, linkedin) and which are still missing.

**Step A3b — Post-Enrichment Reclassification**

After Apollo enrichment reveals company details (employee count, revenue, industry), re-evaluate
all "Maybe" contacts:
- If the company turns out to be a solo practice (<5 providers) or outside behavioral health,
  reclassify to "Not ICP" and remove from enrichment pipeline.
- If the company confirms as a fit (5+ providers, behavioral health), upgrade to ICP = Yes.
- This prevents wasting waterfall API calls on contacts that don't qualify.

**Step A4 — Company Prospecting + ICP Non-Attendees**

This step produces TWO populations:
1. **ICP Non-Attendees**: C-level/senior contacts at companies whose employees ARE on the
   attendee list, but these specific people are NOT on the attendee list themselves.
2. **ICP from Participating Companies**: ICP contacts at sponsor/exhibitor companies.

**Part A4a — ICP Non-Attendees (C-levels at attendee companies)**

For each unique company from the attendee list (Step A1):
1. Run `apollo_mixed_people_api_search` filtered by ICP titles at that company:
   Search for: "CEO", "COO", "CFO", "Owner", "Founder", "President", "VP Operations",
   "Director of Operations"
2. Cross-reference results against the original attendee list from A1. EXCLUDE anyone
   already on the attendee list (by name match).
3. Classify remaining people against ICP criteria.
4. ICP matches go into ledger with `list_assignment: "icp_non_attendees"`.

**Part A4b — ICP from Participating Companies (sponsors/exhibitors)**

For each company from the sponsor/exhibitor list that looks like it could be in behavioral
health / therapy / healthcare operations (and is NOT already covered in A4a):
1. Run `apollo_mixed_companies_search` to find the company
2. Run `apollo_organizations_enrich` to get company details
3. Run `apollo_mixed_people_api_search` filtered by ICP titles at that company
4. Classify found people against ICP criteria
5. ICP matches go into ledger with `list_assignment: "icp_participating_companies"`.

Update ledger: mark `apollo: done` for all new contacts from A4.

**Step A5 — Waterfall Enrichment for Gaps**

After Apollo (A3 + A4), check the ledger for contacts missing email, phone, or LinkedIn.
Run the waterfall ONLY for contacts with gaps. Never re-process contacts that already have
complete data from Apollo.

**Waterfall order:**

**5a. Crustdata People Enrichment**

For contacts missing email OR phone OR LinkedIn after Apollo:

```
POST https://api.crustdata.com/screener/person/search
Headers: Authorization: Token {CRUSTDATA_KEY}, Content-Type: application/json
Body: {
  "filters": [
    {"field": "person_name", "operator": "contains", "value": "{FULL_NAME}"},
    {"field": "company_name", "operator": "contains", "value": "{COMPANY}"}
  ],
  "limit": 1
}
```

Note: If the endpoint returns 404, try `/screener/people/search` as a fallback. Crustdata's
API versions vary. Log which endpoint worked for future calls in this session.

Extract any email, phone, or LinkedIn URL from the response that Apollo did not provide.
Update ledger: mark `crustdata: done`. Record newly found fields.

**5b. Hunter.io Email Finder**

For contacts STILL missing email after Apollo AND Crustdata:

```
GET https://api.hunter.io/v2/email-finder?domain={COMPANY_DOMAIN}&first_name={FIRST}&last_name={LAST}&api_key={HUNTER_KEY}
```

This is the email FINDER endpoint (not verifier). It discovers email addresses.
Extract the email from `response.data.email` if confidence >= 70.
Update ledger: mark `hunter_finder: done`. Record found email.

**Important**: Skip Crustdata if Apollo already found all three fields. Skip Hunter.io finder
if email was found by Apollo or Crustdata. The ledger prevents any double-processing.

**Step A6 — Email Validation (ALL Emails)**

After the waterfall is complete, validate EVERY email in the ledger through Hunter.io
email-verifier. This applies to ALL emails regardless of source (Apollo, Crustdata, or
Hunter.io finder).

**Rules:**
- Do NOT send null, empty, or blank emails to the verifier. Skip them entirely.
- Check the ledger: if an email has already been verified, do not verify again.

For each non-empty email:
```
GET https://api.hunter.io/v2/email-verifier?email={EMAIL}&api_key={HUNTER_KEY}
```

**Keep only**: `status = "valid"` OR `status = "accept_all"`
**Discard from output**: `status = "invalid"`, `status = "disposable"`, `status = "unknown"`
**Null email contacts**: Contacts with no email from any source are still valuable for
in-person targeting at the conference and LinkedIn outreach. Include them in CSV output with
empty email field and note "No email found — target via LinkedIn or in-person." Do NOT upload
these to Instantly (Instantly requires a valid email).

Update ledger: mark `hunter_verifier: done`, record `email_status`.

**Step A7 — Output: Three Lists as CSVs**

Produce three CSV files, saved to `~/Documents/Claude/[ConferenceName]-[Year]/`:

**List 1: `[ConferenceName]_[Year]_ICP_Attendees.csv`**
Contacts from ledger where `list_assignment = "icp_attendees"` AND email is validated.

Columns: First Name | Last Name | Title | Company | Company Type | ICP Tier | Role Category |
Email | Email Status | Phone | LinkedIn | Company Size | Company Revenue | Enrichment Sources |
Notes

**List 2: `[ConferenceName]_[Year]_ICP_Non_Attendees.csv`**
Contacts from ledger where `list_assignment = "icp_non_attendees"` AND email is validated.
These are C-levels at attendee companies who are NOT on the attendee list themselves.

Columns: Same as List 1, plus: Source Company (the attendee company that led to them)

**List 3: `[ConferenceName]_[Year]_ICP_Participating_Companies.csv`**
Contacts from ledger where `list_assignment = "icp_participating_companies"` AND email validated.

Columns: Same as List 1, plus: Source Company (sponsor/exhibitor company)

Also save a `[ConferenceName]_[Year]_Processing_Summary.txt` with counts and breakdown.

**Step A8 — Instantly Integration**

After CSV output, upload validated leads to Instantly for campaign sequencing.

**8a. Read API key** from `~/.claude/.api-keys.json`.

**8b. Create one campaign per list:**

```
POST https://api.instantly.ai/api/v2/campaigns
Headers: Authorization: Bearer {INSTANTLY_KEY}, Content-Type: application/json
Body: {
  "name": "[ConferenceName] [Year] - [List Name]"
}
```

Record the `campaign_id` from each response.

**8c. Upload leads** to each campaign (max 1000 per request, batch if needed):

```
POST https://api.instantly.ai/api/v2/leads/add
Headers: Authorization: Bearer {INSTANTLY_KEY}, Content-Type: application/json
Body: {
  "campaign_id": "{CAMPAIGN_ID}",
  "skip_if_in_workspace": true,
  "skip_if_in_campaign": true,
  "leads": [
    {
      "email": "contact@example.com",
      "first_name": "Jane",
      "last_name": "Doe",
      "company_name": "Acme Health",
      "custom_variables": {
        "title": "CEO",
        "linkedin": "https://linkedin.com/in/janedoe",
        "phone": "555-123-4567",
        "icp_tier": "Primary",
        "role_category": "C-Suite",
        "company_type": "Behavioral Health",
        "conference": "[ConferenceName] [Year]",
        "list_source": "icp_attendees|icp_non_attendees|icp_participating_companies"
      }
    }
  ]
}
```

Only upload contacts that have a validated email. Skip contacts with no email.

**8d. Log results**: Record leads uploaded per campaign, skipped count, and any errors.

**Note on `skip_if_in_workspace`**: This flag skips leads whose email already exists anywhere
in the Instantly workspace (from prior campaigns). For conference outreach, this is intentional
to avoid spamming existing contacts. If you want to re-engage existing leads via a new
conference campaign, set `skip_if_in_workspace: false` and only use `skip_if_in_campaign: true`.

**Note on sequences**: This skill creates campaigns and uploads leads but does NOT create
email sequences (templates, follow-up cadence). Sequences must be configured manually in
Instantly before launching, because email copy requires user review and approval. After
upload, remind the user: "Leads are loaded. Add your email sequences in Instantly before
activating the campaigns."

**Step A9 — Verify Instantly Upload**

**Primary: API-based verification** (reliable, no auth issues):
1. For each campaign created in A8, call:
   ```
   GET https://api.instantly.ai/api/v2/campaigns/{campaign_id}
   Headers: Authorization: Bearer {INSTANTLY_KEY}
   ```
2. Check the lead count in the response matches what was uploaded
3. Report: "Uploaded [X] leads to [Campaign Name]. API verification: [PASS/FAIL]."

**Optional: UI verification via Playwright** (if user requests visual confirmation):
1. Navigate to `https://app.instantly.ai` and find the campaigns
2. Take a screenshot showing lead counts
3. This requires the user to be logged in — if auth fails, skip and rely on API verification

---

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

Store all raw agenda data in a structured format for verification in B3.

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

**Step B3 — Data Verification Checkpoint**

BEFORE generating the HTML document, run a systematic verification pass on all curated data.
This step catches AI hallucinations and data errors before they reach the final output.

**Verification checks:**

1. **Speaker verification**: For each speaker mentioned in a curated session, verify their
   name, title, and company against the original source data from B1. Flag any mismatches.
   If a speaker's name or title was inferred (not directly from source), mark it and attempt
   web verification.

2. **Session time/location verification**: Cross-reference every session time, track, and
   location against the raw agenda data. Ensure no times were transposed or locations swapped.

3. **Completeness check**: Verify that every curated session has title, at least one speaker,
   time, track/location, and "Why attend" paragraph. No day sections empty. Networking events
   have correct times and locations. No duplicate sessions.

4. **Consistency check**: Sessions in chronological order within each day. Concurrent session
   notes reference the correct sessions. Day labels match actual conference dates.

5. **Content accuracy**: Re-read each "Why attend" paragraph and verify speaker descriptions
   match their actual roles. No fabricated credentials or inaccurate company descriptions.

**Output**: A verification report noting any corrections made. Fix issues before proceeding.

**Step B4 — Generate Branded HTML Document**

Generate an HTML file following the template structure in `assets/prep-document-template.html`.
The document must include:

1. **Header**: Solum Health logo (use CDN AVIF URL from brand guide) + conference title +
   "Executive Guide for Healthcare Leaders" subtitle + date/venue badge
2. **Intro paragraph**: 2-3 sentences positioning why this conference matters and what
   the curated picks focus on. Mention the total number of sessions and how many were selected.
3. **Day sections**: Organized by day with colored day-label pills
4. **Session cards**: Grid layout with time/track column + content column containing title,
   speakers, and "Why attend" insight box
5. **Networking callouts**: Teal-background bars for receptions, lunches, networking breaks
6. **Concurrent session notes**: When sessions overlap, add a note helping the reader choose
7. **Footer**: JP Montoya contact card with name, title, email, phone, website

Brand colors (from brand guide):
- Navy primary: #011C40
- Accent blue: #468AF7
- Teal: #70D3C6 / #146055
- Accent BG: #E5DFF4
- Background: #F2F2F9
- Surface: #ffffff

Font: DM Sans (from Google Fonts) for the HTML version.

**Step B5 — Humanization Pass**

Run a quick QA check on all "Why attend" text:
- No AI buzzwords (leverage, streamline, robust, comprehensive, cutting-edge, innovative,
  harness, synergy, holistic, etc.)
- No dashes as punctuation (use commas, periods, or restructure)
- Vary sentence length
- Sound like a practitioner giving advice, not a content marketer
- No hedging language ("might", "could potentially") — be direct

---

### Phase 2: Assembly & Review

Once both tracks complete:

1. Save the curated agenda HTML to `~/Documents/Claude/[ConferenceName]-[Year]/[ConferenceName]_[Year]_Curated_Agenda.html`
2. All three CSVs should already be saved from A7
3. Save processing summary from Track A
4. Open the HTML document for user review
5. Report:
   - Total attendees extracted
   - ICP matches found (breakdown by tier and list)
   - Emails found per source (Apollo vs. Crustdata vs. Hunter.io finder)
   - Emails validated vs. failed vs. no email
   - Leads uploaded to Instantly (per campaign, with verification status)
   - Number of sessions curated from total agenda
   - Data verification results from B3
6. Ask: "Want me to adjust anything? I can re-score ICPs, add/remove sessions, change the
   document style, or re-run enrichment for specific contacts."

## Important Notes

- **Apollo is primary**: Always try Apollo first. Only use Crustdata and Hunter.io finder
  as fallbacks for missing data. This saves API credits on secondary sources.
- **Processing ledger prevents waste**: Every contact is tracked through every step. If you
  restart or retry, check the ledger first. Never call the same API for the same contact twice.
- **Hunter.io has two roles**: (1) Email FINDER as a fallback in the waterfall when Apollo and
  Crustdata fail to find an email. (2) Email VERIFIER for ALL emails regardless of source.
  These are different endpoints. Do not confuse them.
- **Instantly API**: Use `POST /api/v2/leads/add` (NOT `/leads`). Max 1000 leads per request.
  Standard campaign settings: text_only, no tracking, Mon-Fri 8am-5pm America/Detroit,
  daily_limit 30.
- **Privacy**: The attendee data and enriched lists are for internal sales use only. The
  curated agenda document is the shareable, client-facing piece.
- **The agenda document is the value-add**. It positions JP as someone who does homework,
  curates signal from noise, and shares it generously. That's the rapport builder.
- **Data verification is not optional**. Step B3 must run before B4. AI-generated session
  data is prone to hallucination on speaker names and session details. Verify everything.
- **API error handling**: If an API call fails (timeout, 429 rate limit, 500 error), retry
  once after 5 seconds. If it fails again, mark the contact as `enrichment_failed` in the
  ledger and continue with the next contact. Report all failures in the Processing Summary.
- **Rate limiting**: Hunter.io has per-second and per-month limits. For lists with 50+ contacts,
  add a 1-second delay between verification calls. Report expected API credit usage before
  starting A6 so the user can approve the cost.
- **Empty-set handling**: If a list has zero validated leads after A6, skip Instantly campaign
  creation for that list. Report it but don't error out.

## File Dependencies

- **Logo**: `assets/solum_logo.png` or CDN: `https://cdn.prod.website-files.com/66ccf770fcc17846279d79cd/6748cf9b5bac5ff27b9e6bff_solumnewlogo.avif`
- **HTML Template**: `assets/prep-document-template.html` (reference for layout/styling)
- **ICP Criteria**: `references/icp-criteria.md`
- **Brand Guide**: `references/brand-guide.md`
- **API Keys**: `~/.claude/.api-keys.json` (Crustdata, Hunter.io, Instantly)
- **Apollo**: Apollo MCP tools (must be connected)
- **Crustdata**: HTTP API at `https://api.crustdata.com`
- **Hunter.io**: HTTP API at `https://api.hunter.io/v2` (email-finder + email-verifier)
- **Instantly**: HTTP API at `https://api.instantly.ai/api/v2`
- **Web access**: WebSearch + WebFetch for agenda research
- **Playwright**: Browser tools for Instantly UI verification (Step A9)

## Output

Default output directory: `~/Documents/Claude/[ConferenceName]-[Year]/`

Files produced:
- `[ConferenceName]_[Year]_Curated_Agenda.html`
- `[ConferenceName]_[Year]_ICP_Attendees.csv`
- `[ConferenceName]_[Year]_ICP_Non_Attendees.csv`
- `[ConferenceName]_[Year]_ICP_Participating_Companies.csv`
- `[ConferenceName]_[Year]_Processing_Summary.txt`

Instantly campaigns created:
- "[ConferenceName] [Year] - ICP Attendees"
- "[ConferenceName] [Year] - ICP Non-Attendees"
- "[ConferenceName] [Year] - ICP Participating Companies"
