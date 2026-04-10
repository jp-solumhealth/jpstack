---
name: conference-prep
description: >
  Full conference preparation workflow in 7 sequential phases with user checkpoints between
  each phase. Extracts attendees, classifies ICPs, enriches contacts via Apollo-first waterfall
  (Apollo → Crustdata → Hunter.io finder), validates ALL emails through Hunter.io verifier,
  outputs three ICP lists (Attendees, Non-Attendees, Participating Companies), uploads
  validated leads to Instantly, and generates a branded curated agenda document.
  Use this skill whenever the user mentions conference prep, conference preparation, conference
  intro, pre-conference planning, "who's going to [conference]", attendee enrichment, conference
  prospecting, attendee list analysis, pre-conference research, or any request involving
  preparing for an upcoming conference. Even if the user just says "prep for [conference]"
  or "get ready for [event]", assume they want the full workflow unless they say otherwise.
---

# Conference Prep

Seven sequential phases, each with a checkpoint where the user reviews results before
proceeding. This ensures every phase lands correctly and nothing compounds downstream.

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
7. **Phase-gated execution**: NEVER proceed to the next phase without user confirmation.
   Each phase ends with a checkpoint summary and the question: "Ready for Phase [N+1]?"

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

---

## Phase 1: Conference Confirmation & Setup

**Goal**: Confirm the right conference, verify all tools are connected, create project folder.

### Steps

1. Ask for the conference name if not provided
2. Search the web for: official website, dates, location, agenda URL, attendee/sponsor list URL
3. Present what you found and confirm: "Is this the right conference? [Name], [Dates], [Location]"
4. Ask the user for their attendee data source (screenshot, PDF, CSV, URL, or "I don't have one yet")
5. Create the project output folder: `~/Documents/Claude/[ConferenceName]-[Year]/`
6. Read `~/.claude/.api-keys.json` and verify all required API keys are present:
   - Apollo MCP tools: test with a simple search
   - Crustdata: verify key exists
   - Hunter.io: verify key exists
   - Instantly: verify key exists
7. Report any missing keys and resolve before proceeding

### Checkpoint 1

Present to user:
```
✅ Phase 1 Complete — Conference Confirmed

Conference: [Name]
Dates: [Dates]
Location: [Venue, City]
Agenda URL: [URL]
Attendee source: [format provided]
Project folder: ~/Documents/Claude/[ConferenceName]-[Year]/

API Status:
  Apollo MCP:  ✅ Connected
  Crustdata:   ✅ Key found
  Hunter.io:   ✅ Key found
  Instantly:   ✅ Key found

Ready for Phase 2? (Extract & classify attendees)
```

**STOP and wait for user confirmation before proceeding.**

---

## Phase 2: Extract Attendees & Classify ICPs

**Goal**: Parse the attendee data, classify everyone against ICP criteria, produce a
clean list of who matters.

### Steps

**2.1 — Extract Attendees**

Handle whatever input format the user provides:
- **Screenshot/Image**: Read the image directly (Claude has vision). Extract every name, title,
  and company visible.
- **PDF**: Read the PDF and extract attendee data.
- **CSV/Text list**: Parse directly.
- **URL**: Fetch the page and extract attendee data.
- **No list available**: Skip extraction, note that Phase 3 will rely on company prospecting only.

Output a structured list: `[{first_name, last_name, title, company, source: "attendee_list"}]`

Also extract all company names from the conference sponsor list, exhibitor list, and attendee
company names. Store these as the `participating_companies` list.

**2.2 — ICP Classification**

Read `references/icp-criteria.md` for the full ICP classification rules.

For each extracted attendee, classify against Solum Health's ICP criteria. Assign:
- **ICP Match**: Yes / No / Maybe
- **ICP Tier**: Primary / Secondary / Not ICP
- **Role Category**: Practice Owner, C-Suite, VP/Director Ops, Clinic Manager, Billing/RCM,
  Clinical Director, Intake/Access, PE/Investor, Consultant, Other
- **Company Type**: Behavioral Health, ABA, PT/OT/Speech, Mental Health, SUD Treatment,
  Multi-Specialty, Virtual/Telehealth, Residential+, Pediatric Therapy, IDD Services,
  PE-Backed Platform, Other Healthcare
- **Reason**: Brief explanation of why they are/aren't ICP

Initialize the processing ledger. Add each ICP/Maybe contact with
`list_assignment: "icp_attendees"`.

### Checkpoint 2

Present to user:
```
✅ Phase 2 Complete — Attendees Extracted & Classified

Total attendees extracted: [N]
ICP matches (Yes): [N] — [list names + companies]
ICP matches (Maybe): [N] — [list names + companies]
Not ICP: [N] (skipped)

Companies identified for prospecting: [N]
Sponsor/exhibitor companies: [N]

Proceeding to Phase 3 will use Apollo API credits to enrich [X] contacts.
Estimated Apollo calls: [N people searches] + [N org enrichments]

Ready for Phase 3? (Apollo enrichment)
```

**STOP and wait for user confirmation before proceeding.**

---

## Phase 3: Apollo Enrichment & Company Prospecting

**Goal**: Enrich all ICP contacts via Apollo, find C-level non-attendees at attendee
companies, and prospect sponsor/exhibitor companies. This is the heaviest API phase.

### Steps

**3.1 — Apollo Contact Enrichment (ICPs from Phase 2)**

For each ICP person (Yes or Maybe):
1. First try `apollo_people_match` with first_name, last_name, and company domain
2. If no match, try `apollo_mixed_people_api_search` with name + company name
3. Extract and store: **email, phone, LinkedIn URL**, current title, company size, revenue

For lists with 10+ people, use `apollo_people_bulk_match` for efficiency.

Also run `apollo_organizations_enrich` on each unique company for employee count, revenue,
industry classification.

Update ledger: mark `apollo: done` for each contact.

**3.2 — Post-Enrichment Reclassification**

Re-evaluate all "Maybe" contacts using enriched company data:
- Solo practice (<5 providers) or outside behavioral health → reclassify to "Not ICP", remove
- Company confirms as a fit (5+ providers, behavioral health) → upgrade to ICP = Yes

**3.3 — ICP Non-Attendees (C-levels at attendee companies)**

For each unique company from the attendee list:
1. Run `apollo_mixed_people_api_search` filtered by ICP titles:
   "CEO", "COO", "CFO", "Owner", "Founder", "President", "VP Operations",
   "Director of Operations"
2. Cross-reference against the original attendee list. EXCLUDE anyone already on it.
3. Classify remaining people against ICP criteria.
4. ICP matches go into ledger with `list_assignment: "icp_non_attendees"`.

**3.4 — ICP from Participating Companies (sponsors/exhibitors)**

For each sponsor/exhibitor company in behavioral health / therapy / healthcare ops
(not already covered in 3.3):
1. Run `apollo_mixed_companies_search` to find the company
2. Run `apollo_organizations_enrich` for company details
3. Run `apollo_mixed_people_api_search` filtered by ICP titles
4. Classify and add to ledger with `list_assignment: "icp_participating_companies"`

### Checkpoint 3

Present to user:
```
✅ Phase 3 Complete — Apollo Enrichment Done

ICP Attendees enriched: [N]
  - With email: [N]  |  Missing email: [N]
  - With phone: [N]  |  With LinkedIn: [N]
  - Reclassified from Maybe → Not ICP: [N] (removed)

ICP Non-Attendees found: [N] (C-levels at attendee companies)
  - With email: [N]  |  Missing email: [N]

ICP from Participating Companies: [N]
  - With email: [N]  |  Missing email: [N]

Total contacts needing waterfall enrichment (missing email/phone/LinkedIn): [N]
Estimated Crustdata calls: [N]
Estimated Hunter.io finder calls: [N]

Ready for Phase 4? (Waterfall enrichment + email validation)
```

**STOP and wait for user confirmation before proceeding.**

---

## Phase 4: Waterfall Enrichment & Email Validation

**Goal**: Fill gaps from Apollo using Crustdata and Hunter.io, then validate ALL emails.

### Steps

**4.1 — Crustdata People Enrichment**

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

Note: If endpoint returns 404, try `/screener/people/search` as fallback. Log which worked.

Skip if Apollo already found all three fields. Update ledger: mark `crustdata: done`.

**4.2 — Hunter.io Email Finder**

For contacts STILL missing email after Apollo AND Crustdata:

```
GET https://api.hunter.io/v2/email-finder?domain={COMPANY_DOMAIN}&first_name={FIRST}&last_name={LAST}&api_key={HUNTER_KEY}
```

Extract email from `response.data.email` if confidence >= 70.
Update ledger: mark `hunter_finder: done`.

**4.3 — Email Validation (ALL Emails)**

Validate EVERY non-null email through Hunter.io email-verifier, regardless of source.

Rules:
- Do NOT send null, empty, or blank emails. Skip them.
- Check ledger: if already verified, do not verify again.
- For lists with 50+ contacts, add 1-second delay between calls (rate limiting).

```
GET https://api.hunter.io/v2/email-verifier?email={EMAIL}&api_key={HUNTER_KEY}
```

**Keep only**: `status = "valid"` OR `status = "accept_all"`
**Discard**: `status = "invalid"`, `status = "disposable"`, `status = "unknown"`
**Null email contacts**: Include in CSV with empty email field and note
"No email found — target via LinkedIn or in-person." Do NOT upload to Instantly.

### Checkpoint 4

Present to user:
```
✅ Phase 4 Complete — Enrichment & Validation Done

Waterfall enrichment results:
  Crustdata found data for: [N] contacts
  Hunter.io finder found emails for: [N] contacts

Email validation results:
  Total emails validated: [N]
  Valid / accept_all: [N] ✅
  Invalid / disposable / unknown: [N] ❌ (removed)
  No email found: [N] (kept for LinkedIn/in-person)

Emails by source:
  Apollo: [N]  |  Crustdata: [N]  |  Hunter.io: [N]

Final counts:
  ICP Attendees (with valid email): [N]
  ICP Non-Attendees (with valid email): [N]
  ICP Participating Companies (with valid email): [N]

Ready for Phase 5? (Generate CSVs + upload to Instantly)
```

**STOP and wait for user confirmation before proceeding.**

---

## Phase 5: Output CSVs & Instantly Upload

**Goal**: Produce the three CSV files and upload validated leads to Instantly campaigns.

### Steps

**5.1 — Output Three CSVs**

Save to `~/Documents/Claude/[ConferenceName]-[Year]/`:

**List 1: `[ConferenceName]_[Year]_ICP_Attendees.csv`**
Columns: First Name | Last Name | Title | Company | Company Type | ICP Tier | Role Category |
Email | Email Status | Phone | LinkedIn | Company Size | Company Revenue | Enrichment Sources |
Notes

**List 2: `[ConferenceName]_[Year]_ICP_Non_Attendees.csv`**
Same columns plus: Source Company

**List 3: `[ConferenceName]_[Year]_ICP_Participating_Companies.csv`**
Same columns plus: Source Company

Also save `[ConferenceName]_[Year]_Processing_Summary.txt` with full breakdown.

**5.2 — Create Instantly Campaigns**

```
POST https://api.instantly.ai/api/v2/campaigns
Headers: Authorization: Bearer {INSTANTLY_KEY}, Content-Type: application/json
Body: { "name": "[ConferenceName] [Year] - [List Name]" }
```

Create one campaign per list (3 total). Record each `campaign_id`.

**5.3 — Upload Leads**

```
POST https://api.instantly.ai/api/v2/leads/add
Headers: Authorization: Bearer {INSTANTLY_KEY}, Content-Type: application/json
Body: {
  "campaign_id": "{CAMPAIGN_ID}",
  "skip_if_in_workspace": true,
  "skip_if_in_campaign": true,
  "leads": [...]
}
```

Max 1000 leads per request. Only upload contacts with validated emails.
Lead fields: email, first_name, last_name, company_name, custom_variables (title, linkedin,
phone, icp_tier, role_category, company_type, conference, list_source).

**5.4 — Verify Upload via API**

For each campaign:
```
GET https://api.instantly.ai/api/v2/campaigns/{campaign_id}
Headers: Authorization: Bearer {INSTANTLY_KEY}
```
Verify lead count matches what was uploaded.

**Note on sequences**: This skill does NOT create email sequences. Remind user:
"Leads are loaded. Add your email sequences in Instantly before activating the campaigns."

### Checkpoint 5

Present to user:
```
✅ Phase 5 Complete — CSVs Saved & Leads Uploaded to Instantly

Files saved:
  📄 [ConferenceName]_[Year]_ICP_Attendees.csv ([N] contacts)
  📄 [ConferenceName]_[Year]_ICP_Non_Attendees.csv ([N] contacts)
  📄 [ConferenceName]_[Year]_ICP_Participating_Companies.csv ([N] contacts)
  📄 [ConferenceName]_[Year]_Processing_Summary.txt

Instantly campaigns:
  "[ConferenceName] [Year] - ICP Attendees" → [N] leads uploaded ✅
  "[ConferenceName] [Year] - ICP Non-Attendees" → [N] leads uploaded ✅
  "[ConferenceName] [Year] - ICP Participating Companies" → [N] leads uploaded ✅

⚠️  Add email sequences in Instantly before activating campaigns.

Ready for Phase 6? (Research & curate conference agenda)
```

**STOP and wait for user confirmation before proceeding.**

---

## Phase 6: Curated Agenda Research & Verification

**Goal**: Research the full conference agenda, curate the best sessions, verify all data
for accuracy before generating the document.

Read `references/brand-guide.md` for voice and brand guidelines.

### Steps

**6.1 — Agenda Research**

Search the web for the conference's full agenda:
- Session titles, descriptions, times, tracks, locations
- Speaker names, titles, companies
- Networking events, receptions, breakfasts
- Any pre-conference workshops or special events

Store all raw agenda data in a structured format for verification.

**6.2 — Session Curation**

Select 6-10 sessions most relevant to behavioral health practice owners/operators.
Prioritize:
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
- Connects to real operational impact (revenue, time, margin, growth)
- Sounds like a knowledgeable colleague giving advice, not a summary

**6.3 — Data Verification Checkpoint**

Run a systematic verification pass on all curated data BEFORE generating the document:

1. **Speaker verification**: Verify each speaker's name, title, and company against source
   data. Flag any mismatches or inferred details.
2. **Session time/location verification**: Cross-reference every time, track, and location
   against raw agenda data.
3. **Completeness check**: Every session has title, speaker(s), time, location, "Why attend."
4. **Consistency check**: Chronological order, correct concurrent session notes, correct dates.
5. **Content accuracy**: Speaker descriptions match actual roles. No fabricated credentials.

**6.4 — Humanization Pass**

QA check on all "Why attend" text:
- No AI buzzwords (leverage, streamline, robust, comprehensive, cutting-edge, etc.)
- No dashes as punctuation (use commas, periods, or restructure)
- Vary sentence length
- Sound like a practitioner giving advice, not a content marketer
- No hedging language — be direct

### Checkpoint 6

Present to user:
```
✅ Phase 6 Complete — Agenda Curated & Verified

Total sessions in full agenda: [N]
Sessions selected: [N]
Networking events included: [N]

Curated sessions:
  Day 1:
    • [Time] — [Title] — [Speaker(s)]
    • [Time] — [Title] — [Speaker(s)]
  Day 2:
    • [Time] — [Title] — [Speaker(s)]
    ...

Verification results:
  Speaker data verified: [N]/[N] ✅
  Times/locations verified: [N]/[N] ✅
  Issues found & fixed: [N]

[Show the full list of curated sessions with "Why attend" snippets so user can review
the content before it gets baked into the HTML document]

Ready for Phase 7? (Generate branded HTML document)
```

**STOP and wait for user confirmation before proceeding.**

---

## Phase 7: Generate Branded Agenda Document

**Goal**: Generate the final HTML document and present the complete summary.

Read the template at `assets/prep-document-template.html` for the exact HTML structure
and styling to follow.

### Steps

**7.1 — Generate Branded HTML Document**

Generate an HTML file following the template structure. Include:

1. **Header**: Solum Health logo (CDN AVIF URL from brand guide) + conference title +
   "Executive Guide for Healthcare Leaders" subtitle + date/venue badge
2. **Intro paragraph**: 2-3 sentences on why this conference matters. Mention total sessions
   and how many were selected.
3. **Day sections**: Organized by day with colored day-label pills
4. **Session cards**: Grid layout with time/track column + content column (title, speakers,
   "Why attend" insight box)
5. **Networking callouts**: Teal-background bars for receptions, lunches, breaks
6. **Concurrent session notes**: When sessions overlap, help the reader choose
7. **Footer**: JP Montoya contact card (name, title, email, phone, website)

Brand colors:
- Navy primary: #011C40
- Accent blue: #468AF7
- Teal: #70D3C6 / #146055
- Accent BG: #E5DFF4
- Background: #F2F2F9
- Surface: #ffffff

Font: DM Sans (Google Fonts).

Save to: `~/Documents/Claude/[ConferenceName]-[Year]/[ConferenceName]_[Year]_Curated_Agenda.html`

### Checkpoint 7 — Final Summary

```
✅ Phase 7 Complete — All Done!

📁 All files in: ~/Documents/Claude/[ConferenceName]-[Year]/

Lead Intelligence:
  📄 ICP_Attendees.csv — [N] contacts
  📄 ICP_Non_Attendees.csv — [N] contacts
  📄 ICP_Participating_Companies.csv — [N] contacts
  📄 Processing_Summary.txt

Curated Agenda:
  📄 Curated_Agenda.html — [N] sessions from [Total] total

Instantly Campaigns:
  🚀 [ConferenceName] [Year] - ICP Attendees ([N] leads)
  🚀 [ConferenceName] [Year] - ICP Non-Attendees ([N] leads)
  🚀 [ConferenceName] [Year] - ICP Participating Companies ([N] leads)
  ⚠️  Add email sequences before activating

Pipeline summary:
  Total attendees extracted: [N]
  ICP matches: [N] (Primary: [N], Secondary: [N])
  Emails by source: Apollo [N] / Crustdata [N] / Hunter.io [N]
  Emails validated: [N] / [Total] ([%] pass rate)
  Contacts with no email: [N] (LinkedIn/in-person targets)

Want me to adjust anything? I can re-score ICPs, add/remove sessions,
change the document style, or re-run enrichment for specific contacts.
```

---

## Important Notes

- **Phase-gated execution is critical**: Each phase MUST complete and get user approval before
  the next begins. This prevents cascading errors and wasted API credits. If the user says
  "run all phases," confirm once then proceed with abbreviated checkpoints (just the summary
  line, no full stop).
- **Apollo is primary**: Always try Apollo first. Only use Crustdata and Hunter.io finder
  as fallbacks for missing data.
- **Processing ledger prevents waste**: Every contact is tracked through every step. Never
  call the same API for the same contact twice.
- **Hunter.io has two roles**: (1) Email FINDER as a waterfall fallback. (2) Email VERIFIER
  for ALL emails. Different endpoints. Do not confuse them.
- **Instantly API**: Use `POST /api/v2/leads/add` (NOT `/leads`). Max 1000 leads per request.
- **API error handling**: If an API call fails, retry once after 5 seconds. If it fails again,
  mark the contact as `enrichment_failed` in the ledger and continue. Report all failures.
- **Rate limiting**: Hunter.io — add 1-second delay between calls for 50+ contacts. Report
  expected credit usage before starting Phase 4 so user can approve.
- **Empty-set handling**: If a list has zero validated leads, skip Instantly campaign creation
  for that list. Report it but don't error out.
- **Privacy**: Attendee data and enriched lists are internal only. The curated agenda is the
  shareable, client-facing piece.
- **Data verification is not optional**: Phase 6 verification must run before HTML generation.

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
