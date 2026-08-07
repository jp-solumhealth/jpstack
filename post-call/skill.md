---
name: post-call
description: >
  Runs after any prospect meeting (Fireflies). Two outputs: (1) HubSpot pipeline
  hygiene — checks/creates/advances deals per qualification rules, (2) Post-call
  follow-up email — drafted in JP's voice using the REQUIRED template that always
  leads with prospect pain points pulled verbatim from the transcript. Use when the
  user says "post call", "post-call skill", "after my calls", "create deals from my
  meetings", "sync calls to HubSpot", "post call summary", "follow up on [company]",
  "write recap for [company]", "what deals need to be created", or any variation of
  cleaning up pipeline / writing follow-ups after prospect meetings.
---

# Post-Call

Keep the HubSpot pipeline accurate after JP's prospect meetings. Calls are not free —
deals not entered get lost.

## Core Rule (do not deviate)

For every prospect on a Fireflies meeting in the target window (default: last 7 days)
that does NOT already have a HubSpot deal, **first run the qualification analysis below**,
then create the deal accordingly.

**If qualified → create at SQL. If not qualified → create at Unqualified.** Never default
to SQL without confirming the qualification signals.

### Qualification Analysis (run BEFORE creating)

A call is **SQL-qualified** only if MOST of these are true (≥3 of 5):

1. **Decision-maker on the call** — CEO, owner, founder, COO, head of ops, or someone
   who can sign / has explicit authority. Coordinator / staff alone ≠ qualified.
2. **Specific pain articulated** — concrete problem named (denials %, manual hours,
   staffing gap, MEG-style incumbent failure, payer complexity). Generic curiosity ≠ pain.
3. **Pricing discussed** — JP shared pricing AND prospect engaged with it (asked for
   proposal, asked about volume tiers, agreed to send VA / contract). Just "what does
   it cost?" without engagement ≠ qualified.
4. **Concrete next step** — proposal, contract, audit, demo with stakeholder, free
   trial signup. "Let me think about it" ≠ next step.
5. **No hard blocker** — not "we're 6 months out", not "just exploring", not
   "checking 5 vendors". Some friction is fine; a stop sign is not.

If <3 of 5 → **Unqualified** (HubSpot stage ID `1426510546`, label "Unqualified", 0%).

### Defaults when QUALIFIED (SQL)

- **Stage:** `contractsent` (SQL, 60%)
- **Close date:** exactly 3 months from today
- **Amount tier (based on prospect size):**
  - **$6,000** — Small / single-location practice
  - **$18,000** — Mid-size / multi-provider single-org
  - **$30,000** — Big / multi-location or multi-state system

### Defaults when UNQUALIFIED

- **Stage:** `1426510546` (Unqualified, 0%)
- **Close date:** 3 months from today (for reporting consistency)
- **Amount:** leave blank (don't anchor a number on a dead deal)

### Universal defaults (both)

- **Pipeline:** `default` (Revenue Rocket 🚀)
- **Associate the contact** from the meeting (search by email; create only if missing)
- **Champion property:** set if the referrer is known (e.g., Taylor, Martin Ayala).
  Add the option to the `champion` enum first if missing. Leave blank if unknown.

### When a deal already exists

- **Earlier stage (Outreach Started, Meeting Booked, Discovery Completed)** AND the
  call was qualified → advance to SQL, refresh close date to 3mo out
- **Earlier stage** AND the call was NOT qualified → leave stage, just refresh dates
- **SQL or later** → do not change the stage; rename if generic; refresh overdue dates
- **Ghost Client / Closed Lost** AND a real qualified call happened → move to
  Re-engaged Lead first, then advance based on call quality

## Sizing Cues (extract from the transcript)

| Tier | Amount | Signals |
|---|---|---|
| Small | $6,000 | Solo practice, single clinic, <100 calls/wk, <50 auths/mo, single provider |
| Mid | $18,000 | Multiple providers, single state, 100–300 calls/wk, 50–200 auths/mo |
| Big multi-location | $30,000 | Multi-state expansion, 500+ clients, 200+ auths/mo, multiple sites |

If unclear → default to **$6,000** and flag for confirmation. Never guess larger.

## Workflow

### Phase 1: Pull recent meetings
- Fireflies GraphQL: `transcripts(mine: true, limit: 30)` — filter to last 7 days
- For each meeting, identify if it was a prospect call (skip internal team calls,
  existing customers, non-Solum projects like Ocala / Roman Coliseum)

### Phase 2: Check HubSpot for each prospect
- Search deals by company name (CONTAINS_TOKEN)
- Search contacts by participant email
- Match deals → meetings carefully (messy names like "X - Nuevo tipo de objeto Deal" are common)

### Phase 3: Categorize
- **NO deal exists** → create with rule above
- **Deal in early stage** → advance to SQL + refresh close date
- **Deal in SQL+** → leave stage, fix name/close date if needed
- **Internal/customer/non-prospect** → skip

### Phase 3.5: Capture deal intelligence (EHR / CRM / Products / Signed Proposal)

**Always do this for every matched or created deal.** Extract the company/deal name from
the call, find the matching HubSpot deal, then PATCH these custom properties. This is how
the pipeline stays enriched after every conversation.

| Property (internal name) | Source | Rule |
|---|---|---|
| `ehr_system` | Call transcript | Set to the EHR/EMR the prospect names (CentralReach, Raintree, Atlas, Rethink, WebABA, Tebra/Kareo, Lumary, NPAWorks, etc.). |
| `crm_system` | Call transcript | Set to the CRM they name (HubSpot, Salesforce, Zoho, none). Leave blank if never mentioned. |
| `products` | **SIGNED proposal/SOW ONLY** | **Never populate from call discussion.** Only the itemized/priced line items from a signed proposal go here. Products merely *discussed* on a call belong in the debrief, NOT this field. |
| `signed_proposal` | Uploaded file | When a signed proposal/SOW exists, upload it (`POST /files/v3/files`, folder `/signed-proposals`, `{"access":"PRIVATE"}`) and set this field to the returned file id. Then extract `products` from it. |

Capture rules:
- **EHR / CRM are conversation-derived** → safe to capture on any call. This is the
  default action every post-call run.
- **Products + Signed Proposal are commitment-derived** → only when a proposal is signed
  and itemized. Pull the *exact priced line items*, not paraphrased categories.
- Never overwrite a non-empty `ehr_system` / `crm_system` with a vaguer value — only refine.
- If EHR/CRM is not stated on the call, leave blank and flag it in the report ("EHR not stated").

PATCH pattern:
```bash
curl -s -X PATCH "https://api.hubapi.com/crm/v3/objects/deals/{id}" \
  -H "Authorization: Bearer <HUBSPOT_KEY>" -H "Content-Type: application/json" \
  -d '{"properties":{"ehr_system":"CentralReach","crm_system":""}}'
```

### Phase 3.6: Closing a deal LOST (mandatory questionnaire)

**Never move a deal to Closed Lost (`closedlost`) bare.** Every Closed Lost requires all three,
set in the same workflow:

1. **`lost_reason`** (dropdown / enumeration) — pick the closest category:
   `competitor` · `price` · `product_fit` · `segment_fit` · `no_decision` · `timing` ·
   `no_response` · `in_house` · `other`.
2. **`closed_lost_reason`** (textarea) — the free-text context. Always fill; **required** when
   `lost_reason=other`. Put the competitor name here when `lost_reason=competitor`.
3. **A Note on the deal** (`POST /crm/v3/objects/notes`, associate with `associationTypeId:214`)
   summarizing what was lost, why, and the **follow-up plan** so the deal stays re-engageable.

```bash
curl -s -X PATCH "https://api.hubapi.com/crm/v3/objects/deals/{id}" \
  -H "Authorization: Bearer <HUBSPOT_KEY>" -H "Content-Type: application/json" \
  -d '{"properties":{"dealstage":"closedlost","lost_reason":"competitor","closed_lost_reason":"Lost to <Competitor>. <Why>. FUP: <plan>."}}'
```

Hard enforcement on human reps is **UI-only** (the pipelines API stage object has no
`requiredProperties` field). JP enables it at: Settings → Data Management → Objects → Deals →
Pipelines → Revenue Rocket 🚀 → Closed Lost → "Set up required properties for this stage".

### Phase 4: Report back to JP
For each prospect, output:
- Status: CREATED / ADVANCED / UPDATED / SKIPPED
- Deal name, ID, URL
- Stage + amount tier used + reasoning ("mid-size: 200 auths/mo, multi-state expansion")
- **Deal intelligence captured:** EHR system, CRM system (and products only if a signed proposal was processed)
- What JP owes from the call (next action)

Then ask if any amount tiers should be adjusted before moving on.

## Source: Fathom daily sweep (draft-and-queue + apply)

Post-call now runs on TWO meeting sources:
- **Fireflies** (JP's calls) — the manual workflow above (`transcripts(mine: true, ...)`).
- **Fathom** (JP's Fathom-recorded calls) — an automated **daily sweep** at
  `~/Documents/Claude/solum-ops/fathom-post-call/` (launchd → `run_sweep.sh`).

### Draft-and-queue mode (what the daily sweep does, unattended)
The sweep fetches new **prospect** Fathom calls (skips internal + existing customers via
`config.json`), then drafts post-call output into **review files** — it NEVER touches
HubSpot and NEVER sends email. Each `reviews/<date>-<company>.md` holds: the proposed deal
action + qualification reasoning, EHR/CRM captured, the verbatim pain points, and the
pain-points-first follow-up email. `reviews/INBOX.md` indexes pending + skipped meetings.
The sweep does NOT check HubSpot for existing deals (the apply step does).

### Apply mode (interactive, run by JP)
When JP says **"apply the Fathom review for <Company>"** (or "apply all Fathom reviews"):
1. Read the review file(s) in `~/Documents/Claude/solum-ops/fathom-post-call/reviews/`.
2. **Re-verify against HubSpot first** (the draft skipped this): search deals by company
   (CONTAINS_TOKEN) + contacts by attendee email. This is the dedupe gate — the proposed
   action may become ADVANCE/UPDATE instead of CREATE, or already exist.
3. Execute the normal post-call write logic (Phases 2–3.6 above): create/advance the deal
   per the qualification, set EHR/CRM (Phase 3.5), associate the contact.
4. Create the follow-up email as a **Gmail draft** (do NOT auto-send unless JP says "send").
5. Note the outcome at the bottom of the review file (deal URL + applied date), or move it to
   `reviews/applied/`, so it isn't re-applied.

Never apply blindly: if the live HubSpot state contradicts the drafted action, surface the
discrepancy and ask before writing. All the Important Constraints below still hold.

## Important Constraints

- Never invent contacts — if a participant email isn't in HubSpot, flag it and ask
- Never set the deal owner to anyone other than JP unless instructed
- Never change a deal stage backwards (e.g., SQL → Discovery)
- Never overwrite an existing amount with a tier estimate — if amount is already set, leave it
- Always echo the deal URL so JP can verify in one click

## Follow-Up Email Format (REQUIRED)

Every post-call follow-up email JP sends MUST use this exact structure. The
non-negotiable rule: **lead with the prospect's pain points in their own words from
the transcript.** No company context, no "great meeting you" filler before the pains.

### The template

```
Hey [First Name],​

Great meeting you. Thanks for sharing your challenges at [Company Name].

Quick recap of what stood out:

- [Specific pain #1 in their own words, with a number/quote from the transcript, e.g. "VOBs taking 20+ min per patient"]
- [Specific pain #2 with quantification, e.g. "denials piling up on [PAYER NAME]"]
- [Optional pain #3 only if it strengthens the case for the CTA]

Best place to start is our Free Insurance Audit, it surfaces exactly where you're leaking revenue, and we build the rollout and Scope of Work around those numbers. If you're up for it, happy to send over the BAA so we can pull the info and run the audit.

If useful in the meantime, here's an overview of the product and success metrics from Provider Groups like yours (Here)

Best,
Juan Pablo Montoya
Founder, Solum Health
+1 628 276 2659
```

### Rules for the pain bullets

1. **Pull from the transcript verbatim or near-verbatim.** Use the prospect's
   actual words. Quote phrases when they are punchy ("are my glasses ready?",
   "denials piling up").
2. **Quantify everything possible** from the transcript: patient volume, fax count,
   denial %, auth volume, # of staff, etc. Only use numbers the prospect actually
   said. Never invent metrics.
3. **2–4 bullets.** Pick the pains most aligned with the CTA (Free Insurance Audit
   → lead with eligibility, denials, intake, fax-volume pains). Skip pains Solum
   does not solve (e.g., for sub-ICP voice-AI requests, do not bullet voice pain).
4. **Order by acuity.** Biggest pain first. The reader should see the most painful
   line on first scan.
5. **No softening.** Do not generalize "they have intake challenges" — write
   "manual insurance card collection slowing intake across ~200 patients/month".
6. **No clinical pain.** Focus on administrative/operational pain only (per JP's
   global rule).

### When the CTA does not fit

If the prospect is sub-ICP (single-doctor micro-practice, hobbyist, partner, vendor
pitching JP, etc.) and the Free Insurance Audit CTA does not make sense, replace
the CTA paragraph with a lighter touch ("Here's the info you asked for: [links].
Happy to do a quick onboarding when you're ready.") but **still lead with pains
first.** The pain-points-first rule applies to every recap, regardless of fit.

### For internal analysis (not the email)

When the user asks for a *post-call analysis* (not the email itself), use the same
ordering: lead with **Main Challenges** as the first section, then context, deal
status, ICP fit, recommendation. See [feedback_post_call_summary_format] in memory.

## API References

- HubSpot deals search: `POST /crm/v3/objects/deals/search`
- HubSpot contacts search: `POST /crm/v3/objects/contacts/search`
- HubSpot deal create: `POST /crm/v3/objects/deals` with associations
- HubSpot deal update: `PATCH /crm/v3/objects/deals/{id}`
- HubSpot pipeline lookup: `GET /crm/v3/pipelines/deals`
- HubSpot file upload (signed proposals): `POST /files/v3/files` (multipart; folder `/signed-proposals`, `{"access":"PRIVATE"}`)
- Fireflies: `POST https://api.fireflies.ai/graphql`
- API keys: `~/.claude/.api-keys.json`

### Custom deal properties (Deal Information group)
| Internal name | Label | Type | Populated by |
|---|---|---|---|
| `ehr_system` | EHR System | text | Post-call (from transcript) |
| `crm_system` | CRM System | text | Post-call (from transcript) |
| `products` | Products | textarea | Signed proposal line items ONLY |
| `signed_proposal` | Signed Proposal | file | Uploaded signed proposal/SOW |
| `lost_reason` | Lost Reason | enumeration (dropdown) | Set on Closed Lost (competitor/price/product_fit/segment_fit/no_decision/timing/no_response/in_house/other) |
| `closed_lost_reason` | Closed Lost Reason | textarea | Free context on Closed Lost (competitor name + why + FUP) |
