---
name: sow-builder
description: >
  Generate scoped Statements of Work (SOWs) with embedded business cases for Solum Health
  prospects. Pulls real data from Fireflies (call transcripts), HubSpot (deal records, emails),
  and Apollo (company enrichment), then cross-references all sources to produce an accurate,
  conservative proposal. Use this skill when the user says "build a SOW", "create a proposal",
  "SOW", "statement of work", "scope of work", "write a proposal", "build a business case",
  "SOW for [company]", "proposal for [company]", or any variation of wanting a scoped proposal
  or statement of work for a prospect or client.
---

# SOW Builder

Generate production-ready Statements of Work with embedded business cases for Solum Health
prospects. Every number is sourced, every claim is cross-referenced, and every assumption
is flagged.

## Core Principle

A SOW is a commitment document. Overpromise here and you lose trust, margin, or both. Every
number must be conservative. Every scope item must be validated. If data conflicts across
sources, flag it and use the lower number. The internal fact-check section exists so JP can
catch issues before sending.

## The Workflow

### Phase 0: Identify the Company

1. Get the company name from the user. If ambiguous, ask for clarification.
2. Normalize the name for searching across systems (e.g., "Supportive Care" vs "Supportive Care ABA").

### Phase 1: Data Collection

Run ALL of these in parallel where possible. The goal is to pull every data point available
before writing a single word.

#### 1A. Fireflies — Call Transcripts

Search for ALL transcripts mentioning this company:

```
fireflies_search: keyword:"{company_name}" scope:title from:2025-01-01 limit:50
```

Also search for key contacts by name if known.

For each matching transcript, retrieve the full summary:
```
fireflies_get_summary: id:{transcript_id}
```

Extract from each call:
- **Pain points** — What problems did they describe? Use their exact words.
- **Requirements** — What did they say they need? Features, integrations, workflows.
- **Volume data** — Any numbers: orders/month, claims/month, auth requests, call volumes, employee counts, patient counts, client counts.
- **Pricing discussions** — What pricing was discussed? What was their reaction?
- **Technical constraints** — What EMR do they use? Phone system? Clearinghouse? Any IT restrictions?
- **Integration needs** — What systems need to connect? APIs, SFTP, manual upload?
- **Timeline expectations** — When do they want to go live? Any deadlines?
- **Decision makers** — Who else needs to approve? Who's the champion?
- **Competitive mentions** — Are they evaluating alternatives? Who?
- **Objections raised** — What concerns came up?

#### 1B. HubSpot — Deal & Contact Records

Search for the company and related records:

```
search_crm_objects: objectType:"companies" query:"{company_name}"
search_crm_objects: objectType:"deals" query:"{company_name}"
search_crm_objects: objectType:"contacts" query:"{company_name}"
```

Extract:
- **Deal stage** — Where are they in the pipeline?
- **Deal amount** — What's the expected value?
- **Contacts** — Names, titles, emails of all stakeholders
- **Email history** — Any requirements, questions, or data shared via email
- **Company properties** — Industry, size, location, website
- **Notes** — Any internal notes from previous interactions
- **Associated activities** — Meetings logged, tasks, follow-ups

#### 1C. Apollo — Company Enrichment

Enrich the company profile:

```
apollo_organizations_enrich: domain:"{company_domain}"
```

If domain unknown, search first:
```
apollo_mixed_companies_search: q:"{company_name}"
```

Extract:
- **Company size** — Employee count, headcount growth
- **Revenue** — Annual revenue or revenue range
- **Funding** — Total raised, last round, investors
- **Industry** — Primary industry, sub-industry
- **Technology stack** — What tools they use (may reveal EMR, phone system)
- **Key people** — C-suite, VP-level contacts
- **Locations** — HQ, offices, states they operate in

### Phase 2: Data Synthesis & Fact-Check

Before writing anything, perform the internal fact-check:

#### 2A. Cross-Reference Volume Numbers

Compare volume data across all sources:
- Call transcript #1 vs call transcript #2 vs email vs deal notes
- If numbers differ, document the discrepancy and use the LOWER number for business case
- Flag: "On {date} call, prospect said {X}. On {date} call, prospect said {Y}. Using {lower} for SOW."

#### 2B. Verify Pricing Alignment

Check that pricing discussed matches current Solum pricing tiers:
- Growth: $500/mo (up to ~200 clients)
- Scale: $2,500/mo (200-1,000 clients)
- Enterprise: Custom (1,000+ clients)
- Per-unit pricing: varies by service type
- Flag any pricing that was quoted but doesn't match current structure

#### 2C. Requirements Completeness Check

Build a master requirements list from ALL sources:
- Go through every call transcript and extract each requirement mentioned
- Go through every email and extract each requirement mentioned
- Go through deal notes for any requirements
- Deduplicate but don't drop — if something was mentioned once on call #1 and never again, it still belongs
- Flag requirements that may be technically impossible or need engineering scoping

#### 2D. Technical Feasibility Check

For each integration requirement:
- Is this an EMR Solum already integrates with? (Flag if unknown)
- Is this a standard clearinghouse connection? (Flag if non-standard)
- Does the phone system integration exist? (Flag if new)
- Are there any data format requirements that need validation?

### Phase 3: SOW Generation

Generate the SOW in markdown format. Use Solum Health branding guidelines from the
`solum-health-brand` skill for any PDF generation.

#### Document Structure

```markdown
## Statement of Work: {Company Name} x Solum Health
**Prepared:** {today's date} | **Version:** 1.0
**Prepared by:** JP Montoya, CEO, Solum Health
**Contact:** jp@getsolum.com | (628) 276-2659

---

### 1. Executive Summary

{2-3 paragraphs. Who they are (size, location, specialty). What they need from Solum
and why — use the specific pain points from their own calls/emails. Why now — what's
the trigger driving this decision (growth, staff turnover, compliance, cost pressure).
End with the value proposition: what Solum delivers and the expected impact.}

---

### 2. Current State & Challenges

{Use their own words from transcripts. Each challenge should be a subsection with:}

#### {Challenge 1: e.g., "Manual Prior Authorization Process"}
- **The problem:** {description using prospect's language}
- **Impact:** {quantified where possible — hours/week, error rate, revenue leakage}
- **Source:** {which call/email this came from}

#### {Challenge 2}
...

#### {Challenge N}
...

---

### 3. Scope of Work

#### Phase 1: {Name — e.g., "Prior Authorization Automation"}
**Timeline:** {weeks/months}

| Deliverable | Description | Inputs Required | Output |
|-------------|-------------|-----------------|--------|
| {item} | {what Solum delivers} | {what we need from them} | {what they get} |

**Integration Requirements:**
- {EMR connection details}
- {Phone system details}
- {Clearinghouse details}

**Explicitly NOT Included:**
- {Scope boundary 1}
- {Scope boundary 2}

#### Phase 2: {Name}
...

#### Phase 3 (if applicable): {Name}
...

---

### 4. Business Case

#### Volume Data (from {company_name})
| Metric | Value | Source |
|--------|-------|--------|
| {e.g., Monthly orders} | {number} | {call date or email date} |
| {e.g., Monthly auth requests} | {number} | {call date or email date} |
| {e.g., Current staff handling this} | {number} | {call date or email date} |

#### Current Cost Estimate
| Cost Component | Calculation | Monthly Cost |
|----------------|-------------|--------------|
| {e.g., Staff labor} | {N staff x $X/hr x Y hrs/week x 4.33} | ${amount} |
| {e.g., Overtime} | {estimate} | ${amount} |
| {e.g., Error/rework cost} | {estimate} | ${amount} |
| **Total Current Cost** | | **${total}** |

#### Projected Cost with Solum
| Component | Calculation | Monthly Cost |
|-----------|-------------|--------------|
| Solum platform fee | {tier or per-unit x volume} | ${amount} |
| Remaining staff cost (if any) | {reduced headcount estimate} | ${amount} |
| **Total with Solum** | | **${total}** |

#### ROI Summary
| Metric | Value |
|--------|-------|
| Monthly savings | ${current - projected} |
| Annual savings | ${monthly x 12} |
| Solum annual cost | ${solum monthly x 12} |
| Net annual savings | ${annual savings - annual cost} |
| ROI | {net savings / solum cost x 100}% |
| Payback period | {months to recoup implementation fee} |

*All calculations use conservative assumptions. See Section 7 for assumptions.*

---

### 5. Implementation Plan

| Phase | Timeline | Milestones | {Company} Responsibilities |
|-------|----------|------------|---------------------------|
| Kickoff & Setup | Week 1-2 | {milestones} | {what they provide} |
| Configuration | Week 3-4 | {milestones} | {what they provide} |
| Testing | Week 5-6 | {milestones} | {what they provide} |
| Go-Live | Week 7-8 | {milestones} | {what they provide} |
| Optimization | Month 3+ | {milestones} | {what they provide} |

**Go/No-Go Checkpoints:**
- After setup: confirm integrations working
- After testing: confirm accuracy meets threshold
- After 30 days: review metrics and adjust

---

### 6. Pricing

| Item | Unit | Rate | Estimated Monthly |
|------|------|------|-------------------|
| {Service line 1} | {per order / per auth / flat} | ${rate} | ${monthly} |
| {Service line 2} | {unit} | ${rate} | ${monthly} |
| **Monthly Total** | | | **${total}** |

**Implementation Fee:** ${amount} (one-time)

**Payment Terms:**
- Monthly invoicing, net 30
- Implementation fee due at kickoff
- {Any special terms discussed}

**Guarantee:** {If discussed — e.g., "30-day money-back guarantee on platform fees"}

---

### 7. Requirements & Assumptions

#### Technical Requirements
- {EMR: name, version, API access needed}
- {Phone system: type, forwarding capability}
- {Clearinghouse: name, connection type}
- {Data formats: HL7, FHIR, CSV, etc.}
- {Network/VPN requirements if any}

#### Assumptions
- {Volume assumption: using {X} orders/month based on {source}}
- {Staffing assumption: current team of {N} handling {function}}
- {Cost assumption: average hourly rate of ${X} for {role}}
- {Timeline assumption: {company} provides access within {X} days of kickoff}
- {Growth assumption: volume flat for Year 1 projections}

#### Dependencies & Risks
| Risk | Mitigation |
|------|------------|
| {e.g., EMR integration delay} | {mitigation approach} |
| {e.g., Data quality issues} | {mitigation approach} |

---

### 8. Fact-Check Notes

> **INTERNAL ONLY — Remove this section before sending to prospect.**

#### Data Discrepancies
- {Any volume numbers that differ across sources}
- {Any pricing that was quoted differently at different times}
- {Any requirements that appeared in one source but not others}

#### Assumptions Needing Validation
- {Assumptions made without direct prospect confirmation}
- {Cost estimates based on industry averages rather than their data}
- {Technical integrations not yet validated by engineering}

#### Open Questions
- {Questions that need answers before finalizing the SOW}
- {Clarifications needed from the prospect}
- {Internal decisions needed (pricing approval, timeline commitment)}

#### Unvalidated Integrations
- {Any integration mentioned that Solum hasn't confirmed it can support}
- {Any EMR/system where connectivity is assumed but not tested}
```

### Phase 4: Output & Delivery

1. **Save the SOW** as markdown to the relevant project folder:
   `~/Documents/Claude/SALES/{company-name}-sow.md`

2. **Generate a PDF** using the `/pdf` skill with Solum Health branding:
   - Font: DM Sans
   - Colors: Navy (#011C40) headers, Solum Blue (#468AF7) accents
   - Logo: Include Solum Health logo at top
   - Footer: "Confidential | Solum Health | getsolum.com"
   - Save to: `~/Documents/Claude/SALES/{company-name}-sow.pdf`

3. **Display a summary** to the user:
   - Company name and deal stage
   - Key pain points identified (top 3)
   - Total scope (number of phases, timeline)
   - Business case headline (monthly savings, ROI)
   - Data quality score (how much was sourced vs assumed)
   - Open questions that need resolving
   - Fact-check flags that need attention

4. **Ask the user:**
   - "Want me to adjust any numbers or scope items?"
   - "Should I remove the Fact-Check section and generate a client-ready version?"
   - "Any pricing changes before I finalize?"

## Rules

### Data Integrity
- NEVER fabricate volume numbers. If no data exists, write "TBD — confirm with prospect" and flag it.
- NEVER round up. If they said "about 350 orders," use 350, not 400.
- ALWAYS cite the source for every number (which call, which email, which date).
- If a number appears in multiple sources with different values, use the LOWER value and flag the discrepancy.

### Business Case Conservative
- Use the lower end of any ranges given by the prospect.
- Assume ZERO growth in Year 1 projections unless the prospect explicitly stated growth plans.
- Use conservative hourly rates for labor cost estimates ($18-25/hr for admin staff, $35-50/hr for clinical staff) unless prospect provided specific numbers.
- Do NOT include "soft" savings (improved morale, better patient experience) in the ROI calculation. Mention them qualitatively only.
- Round savings DOWN to the nearest $100.

### Scope Management
- ALWAYS include a "What's NOT Included" section for every phase.
- If a requirement was mentioned but is vague, list it as "requires scoping" rather than committing to it.
- If a prospect asked for something once in passing, include it in Requirements but note it needs confirmation.
- Custom integrations, custom reporting, and training beyond standard onboarding should be explicitly called out as included or excluded.

### Technical Honesty
- If Solum hasn't integrated with their specific EMR before, say "integration to be validated" not "we support this."
- If a phone system integration is non-standard, flag it as a risk.
- If data format requirements are unclear, list them as open questions.

### Branding
- Use Solum Health brand guidelines from the `solum-health-brand` skill for all visual formatting.
- The SOW should look professional enough to send to a VP or CFO.
- Use clean tables, clear section breaks, and consistent formatting.
- No jargon that the prospect wouldn't understand. If using a technical term, explain it.

### Privacy
- Do NOT include Fireflies transcript IDs or raw transcript text in the client-facing sections.
- The "Source" column in tables should reference "Discovery call ({date})" or "Email ({date})", not internal system references.
- The Fact-Check section (Section 8) is internal only and must be removed before sending.

## Handling Missing Data

If a data source is unavailable or returns no results:

| Source | Fallback |
|--------|----------|
| Fireflies returns no transcripts | Ask user: "I couldn't find call transcripts for {company}. Can you share the key details from your calls?" |
| HubSpot has no deal record | Proceed with available data, note "No HubSpot deal record found" in Fact-Check |
| Apollo returns no enrichment | Use company website and any data from calls. Note "Company enrichment unavailable" in Fact-Check |
| No volume data from any source | Mark all volume fields as "TBD" and flag: "Business case cannot be completed without volume data from prospect" |
| No pricing discussed yet | Use standard Solum pricing tiers based on estimated company size. Note "Pricing not yet discussed with prospect" |

## Quick Reference: Solum Pricing Tiers

| Tier | Monthly | Best For |
|------|---------|----------|
| Growth | $500/mo | Small practices, <200 clients |
| Scale | $2,500/mo | Mid-size, 200-1,000 clients |
| Enterprise | Custom | Large orgs, 1,000+ clients, flat-rate |
| Per-unit | Varies | Volume-based, typically $2-8/unit depending on service |

Implementation fees: typically $0-2,500 depending on integration complexity.
Free trial: available for Growth tier, 2-4 week test period.

## Important Notes

- **Fireflies, HubSpot, and Apollo MCPs are required.** If any are not connected, tell the user which ones are missing and proceed with available sources.
- **This is a living document.** After generating, the user will likely want to iterate. Support edits, re-pulls, and version bumps.
- **The SOW is not a contract.** It's a scoping document. Do not include legal terms, liability clauses, or binding language. If the prospect needs a contract, that's a separate step.
- **Speed matters.** The user wants this generated quickly after calls, not days later. Optimize for fast data pulls and assembly.
