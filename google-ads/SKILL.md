---
name: google-ads
description: >
  Ten-stage Google Ads operating system for a B2B healthcare AI company: builds a brand brain,
  mines customer language, maps competitor angles, builds the keyword universe, designs the
  account structure, writes RSA copy, briefs intent-specific landing pages and video creative,
  runs a daily audit, and produces a weekly scaling plan and test roadmap. Read-only against the
  ad account by default: it recommends, you approve. Use when the user says "google ads",
  "adwords", "paid search", "PPC", "search campaigns", "keyword research", "RSA copy", "ad copy",
  "ads audit", "campaign audit", "scaling plan", "PMax", "Demand Gen", "landing page for ads",
  "search terms report", or any variation of wanting help planning, writing, or running Google Ads.
  Accepts a stage argument: brain, language, competitors, keywords, structure, copy, conversions,
  landing, creative, audit, scale. With no argument, it picks the next unfinished stage.
---

# Google Ads — Paid Search Operating System

Research feeds keywords. Keywords feed campaigns. Campaign data feeds landing pages. Landing
pages feed creative. Creative feeds new angles. Audits feed next week's tests. Each stage writes
a file that the next stage reads, so the loop compounds instead of restarting every Monday.

## Core Principles

1. **Context first, recommendations second.** Output quality tracks input quality. Stage 0 is
   not optional. If the brain file is thin, stop and ask for what's missing.
2. **Every campaign has a job.** It exists to produce a specific signal, and a named metric
   decides whether it scales, holds, or gets cut. No job, no budget.
3. **We sell to practices, not patients.** Solum's buyer is the owner, practice manager, billing
   lead, or clinical director at an ABA, behavioral health, or specialty practice. The problem is
   admin load (prior auth, VOB, intake, denials). Never write copy that targets patients or
   implies a medical outcome.
4. **Pipeline, not clicks.** For B2B SaaS the real conversion is a qualified demo that becomes a
   HubSpot deal. Optimize to cost per SQL and pipeline per dollar, not CTR or form fills.
5. **Recommend, don't touch.** This skill never changes budgets, bids, keywords, or ads in the
   live account without explicit approval of the specific change. See Guardrails.

## Workspace

All stage outputs live in `./google-ads-workspace/` in the current working directory (create it on first
run). Each stage reads the files before it.

```
google-ads-workspace/
  00-brain.md              # Stage 0: brand profile + open questions
  01-language-bank.md      # Stage 1: quotes / pain / outcome / stage / angle
  02-competitor-map.md     # Stage 2: competitor table + validated + white-space angles
  03-keywords.md           # Stage 3: keyword universe + 30-day launch plan
  04-account-structure.md  # Stage 4: campaigns, ad groups, budgets, kill rules
  05-rsa/<ad-group>.md     # Stage 5: RSA copy per ad group
  06-conversions.md        # Stage 6: conversion tracking + offline import plan
  07-landing/<intent>.md   # Stage 7: landing page briefs
  08-creative/<concept>.md # Stage 8: video + static concepts
  audits/YYYY-MM-DD.md     # Stage 9: daily audit + action list
  scale/YYYY-WW.md         # Stage 10: weekly scaling plan + test roadmap
```

If invoked with no argument, list which files exist and run the first missing stage. Stages 9
and 10 are recurring and always runnable once Stage 4 exists.

## Guardrails (read before every stage)

**Account safety**
- Default mode is read-only. Pull data from the Google Ads MCP if connected, otherwise ask for a
  CSV export (Campaigns, Ad groups, Search terms, Keywords, Ads, Assets, Landing pages).
- Output changes as a proposed action list. Apply a change only after the user approves that
  specific change in this conversation. "Looks good" on a list of 12 means ask which ones.
- Never raise any budget by more than 20% in one step. Never pause a campaign with conversions
  in the last 14 days without flagging it as high risk.
- Never add broad match to a campaign on Maximize Conversions / tCPA without a negative list in
  place.

**Healthcare ad policy**
- Google restricts personalized advertising on health topics. Remarketing lists must be built from
  B2B visitors to product and pricing pages, never from content about patient conditions, and ad
  copy must not imply knowledge of a viewer's health status.
- Never pass PHI into Google Ads, GA4, or conversion imports. Offline conversions use GCLID +
  HubSpot deal stage + value only. No patient names, diagnoses, or member IDs anywhere.
- No outcome guarantees ("guaranteed approvals", "eliminate denials"). Every number in ad copy or
  a landing page (time saved, approval rate, dollars recovered) must pass `/fact-check` or come
  from a named customer who agreed to be quoted.

**Writing rules** (apply to every line of copy this skill writes)
- Operator voice: plain, specific, numbers over adjectives. Sounds like a practice owner talking
  to another practice owner.
- Banned: "revolutionize", "unlock", "seamless", "game-changer", "cutting-edge", "leverage",
  "empower", "streamline your workflow", "in today's fast-paced", "elevate", "harness",
  "robust", "supercharge", em-dash chains, and rhetorical question openers.
- Use the customer's words from `01-language-bank.md` before inventing new ones.
- Apply `/solum-health-brand` to any visual output.

---

## Stage 0: Build the Brand Brain

**Gather context.** Pull in parallel, whatever is available:

| Source | What to pull |
|--------|-------------|
| Website (WebFetch) | getsolum.com home, product pages, pricing, case studies |
| HubSpot | Closed-won deals last 180 days: segment, size, source, cycle length. Lost reasons. |
| Fathom / call notes | 10 most recent discovery calls: pains, objections, exact phrases |
| Google Drive | Brand guidelines, objection docs, past landing pages, winning ad copy |
| Google Ads (MCP or CSV) | 90-day search terms report, campaign performance, current ads |
| User-provided | Competitor URLs, Ads Transparency Center links, offer details |

Also read `pmf-pulse` and `product-insights` outputs if they exist in the working directory.

**Then run:**

> Act as the Google Ads strategy brain for Solum Health. Read all gathered context and create a
> working brand profile covering: ICP (by practice type, size, role), core pain points, buying
> triggers, objections, emotional language customers use, top products/modules, strongest offers,
> competitor positioning, current funnel gaps, and Google Ads opportunities. Do not make
> recommendations yet. First summarise the context and list what is missing.

**Write** `00-brain.md`, then **stop** and show the user the "What's missing" list. Do not proceed
to Stage 1 until the user fills the gaps or says to continue without them.

---

## Stage 1: Customer Language Mining

Keyword tools show volume. They don't show the sentence a burned-out billing manager types into
Reddit at 11pm. That sentence is the ad.

**Search** (WebSearch, run in parallel), substituting the brain's pain points:

```
"prior authorization" (frustrating OR nightmare OR "on hold") site:reddit.com
"ABA" (billing OR "prior auth" OR "authorization") site:reddit.com
"verification of benefits" OR "insurance verification" "takes forever" site:reddit.com
"practice manager" OR "front desk" (overwhelmed OR burnout) insurance site:reddit.com
"claims denied" OR "denial" "behavioral health" site:reddit.com
[competitor] review site:g2.com OR site:capterra.com
YouTube comments on practice-management / ABA billing explainer videos
Practice-owner Facebook groups and forums surfaced by search (quote only public posts)
```

Also mine Fathom/Fireflies transcripts for the same phrases. Customer calls outrank Reddit.

**Prompt:**

> From these sources, extract the exact words people use when describing the problem, what they
> have tried, why those solutions failed, what outcome they want, and what would make them buy.
> Format as a table: Quote / Source / Pain Point / Desired Outcome / Funnel Stage / Possible Ad
> Angle.

Keep quotes verbatim. Strip usernames and anything that identifies a patient. Target 40+ rows.

**Write** `01-language-bank.md`.

---

## Stage 2: Competitor Angle Map

**Default competitors** (override from the brain): CentralReach, Waystar, Availity, CoverMyMeds,
plus any competitor the user names or that appears in lost-deal reasons.

**Research** each via Google Ads Transparency Center, LinkedIn/Meta Ad Library, landing pages,
pricing pages, demo-request flows, guarantees, and G2/Capterra reviews.

**Prompt 1:**

> Build a table with one row per competitor: offer, main promise, ad hooks, landing page angle,
> proof used, objections handled, pricing position, and what they are NOT saying.

**Prompt 2:**

> Based on this research, identify the 5 most validated market angles and the 5 biggest
> white-space angles Solum can own. For each angle, give the funnel stage it belongs to and which
> campaign type should test it first.

An angle is **validated** when 3+ competitors run it. You don't need to be original there, you
need a sharper version backed by a real number. **White space** is what nobody says: often the
thing customers complain about in G2 reviews of the market leader.

**Write** `02-competitor-map.md`.

---

## Stage 3: Keyword Research

**Prompt 1:**

> Using the language bank, competitor map, product pages, and search terms data, build the full
> Google Ads keyword universe for Solum Health. Split it into: branded, competitor,
> high-intent product ("prior authorization software", "ABA billing software"), problem-aware
> ("prior auth taking too long"), solution-aware ("automate insurance verification"),
> comparison ("[competitor] alternative", "[competitor] vs"), use-case / specialty ("ABA prior
> auth", "behavioral health VOB"), role ("practice manager tools"), and negative keywords. For
> each keyword give: funnel stage, intent level (H/M/L), match type, campaign / ad group, and
> landing page angle.

**Negative keyword seeds** (always include): jobs, job, salary, hiring, remote, certification,
course, training, CPT code lookup, free template, patient, "how to become", "what is" (for BOF
campaigns), Medicaid application, member login, portal login, and every competitor's login term.

**Prompt 2:**

> Prioritise this into a 30-day launch plan. Separate must-launch keywords from phase 2 tests.
> Flag keywords that are high volume but low commercial intent, and keywords where the searcher is
> more likely a patient or job-seeker than a practice buyer.

Get volume and CPC from the Google Ads MCP Keyword Planner if connected. If not, mark volumes as
"unverified" rather than guessing.

**Write** `03-keywords.md`.

---

## Stage 4: Campaign Architecture

**Prompt 1:**

> Turn the finalized keyword plan into a complete Google Ads account structure. Include campaign
> names, ad group names, keyword match types, bidding strategy, starting budget split, exclusions,
> negative keyword rules, and when each campaign launches.

Use this structure, adapted for B2B lead gen (no Shopping, no Merchant Center):

| # | Campaign | Launch | Notes |
|---|----------|--------|-------|
| 1 | Brand Search | Day 1 | Exact + phrase on brand. Protects brand, cheap signal. |
| 2 | NB Search — High Intent | Day 1 | Product + use-case keywords. Most of the budget. |
| 3 | NB Search — Problem-Aware | Day 14 | Pain-phrase keywords. Content-offer landing pages. |
| 4 | Competitor Search | Day 14 | "[competitor] alternative / vs". Comparison pages only. |
| 5 | Remarketing (Display / YouTube) | Day 21 | B2B site visitors to product and pricing pages only. Brand excluded. |
| 6 | PMax — lead gen | Day 30+ | Only after 30+ offline conversions imported. Brand exclusions on. |
| 7 | Demand Gen | Day 45+ | Video concepts from Stage 8. Customer-match lists from HubSpot (hashed). |
| 8 | TOF Search Tests | Rolling | One new angle at a time, capped budget. |

Naming: `SOL | {Type} | {Theme} | {Geo}`, e.g. `SOL | NB-Search | Prior Auth | US`.

Bidding: start on Maximize Clicks with a CPC cap or Manual CPC until there are 15+ conversions in
30 days per campaign, then Maximize Conversions, then tCPA once CPA is stable across two weeks.

**Prompt 2:**

> Explain why each campaign exists, what signal it is meant to produce, and what metric decides
> whether it scales, holds, or gets cut. Give numeric thresholds.

**Write** `04-account-structure.md`.

---

## Stage 5: RSA Copy Production

For each ad group in `04-account-structure.md`:

**Prompt 1:**

> Write responsive search ad copy for [MODULE] targeting [KEYWORD]. Funnel stage: [BOF/MOF/TOF].
> Use the language bank and competitor white space. Give 15 headlines (max 30 characters) and 4
> descriptions (max 90 characters). Include benefit-led, problem-led, proof-led, offer-led, and
> urgency-led headlines. Headline 1 must match the search intent. Follow the writing rules.

**Prompt 2:**

> Create 3 ad variations for this keyword: direct-response, proof-heavy, and problem-agitation.
> Explain which buyer each variation is for (owner, practice manager, billing lead).

Stage tone:
- **BOF**: Solum is the obvious answer. Name the task, the time saved, the next step.
- **MOF**: make the benefit believable. Proof, specifics, customer type.
- **TOF**: make the problem impossible to ignore. Their words, their Tuesday afternoon.

**Validate lengths with code, not by eye:**

```bash
python3 - <<'EOF'
import re, sys
text = open("google-ads-workspace/05-rsa/<ad-group>.md").read()
for kind, limit in (("H", 30), ("D", 90)):
    for line in re.findall(rf"^{kind}\d+:\s*(.+)$", text, re.M):
        n = len(line.strip())
        print(("OK  " if n <= limit else "OVER"), f"{n:>3}/{limit}", line.strip())
EOF
```

Write headlines as `H1: ...` and descriptions as `D1: ...` so the check works. Fix every `OVER`
before showing the user. Run `/fact-check` on any headline with a number.

**Write** `05-rsa/<ad-group>.md`.

---

## Stage 6: Conversion Tracking & Offline Import

This replaces the e-commerce feed stage. For B2B, bad conversion data is the most common reason
smart bidding fails, so this stage runs before scaling anything.

**Audit and propose:**

1. **Primary conversion**: demo booked (calendar confirmation, not form view). Secondary: form
   submit, pricing page 60s+, content download. Only the primary one should be a bidding goal.
2. **Enhanced conversions for leads**: hashed work email from the demo form.
3. **Offline conversion import from HubSpot**: capture GCLID in a hidden form field, store it on the
   contact, and import at deal stages `SQL`, `Opportunity`, `Closed Won` with values.
   Check with `get_properties` that a GCLID property exists on contacts; if not, flag it.
4. **Attribution**: data-driven; conversion window 90 days (B2B cycles are long).
5. **PHI check**: confirm nothing beyond email, GCLID, stage, and value is sent.

**Prompt:**

> Audit current conversion actions against this spec. Tell me exactly what to change, in what
> order, and which campaigns are currently bidding on the wrong goal.

**Write** `06-conversions.md`.

---

## Stage 7: Landing Page Angles

One generic homepage cannot convert a billing lead searching "ABA prior auth software" and an
owner searching "CentralReach alternative". Build one page per intent.

**Prompt 1:**

> Build a landing page brief for [MODULE] targeting people searching [KEYWORD]. Awareness stage:
> [PROBLEM-AWARE / SOLUTION-AWARE / PRODUCT-AWARE]. Structure: hero headline, subheadline, proof
> bar, problem section using customer language, how it works, product section, comparison
> section, customer stories, objection handling (HIPAA/BAA, EHR integration, implementation time,
> price), FAQ, CTA. The first screen must match the search query.

**Prompt 2:**

> Create 5 landing page angle variations for this module based on different search intents. For
> each: hero, core promise, proof required, objections to handle, and CTA.

Hand the chosen brief to Claude Code to build the page with `/solum-health-brand` applied, then run
`/site-review` on the result before it gets traffic.

**Write** `07-landing/<intent>.md`.

---

## Stage 8: Creative Production

For YouTube, Demand Gen, and remarketing. Use whichever image/video generation connector is
available; if none is connected, output the prompts and scripts only.

**Prompt 1:**

> Create a 9-shot YouTube ad concept for [MODULE] based on this angle: [ANGLE]. Style:
> [UGC-style founder talk / screen-recording demo / animated explainer]. For each shot: scene
> description, voiceover, on-screen text. Put the hook in the first 5 seconds, before the skip
> button.

**Prompt 2:**

> Create 5 new creative concepts from the strongest pain points in the language bank. Each concept:
> hook, visual metaphor, script, image prompts, animation prompts, and CTA.

Rules: no real patient likeness or data on screen; use synthetic or blurred demo data in product
footage. Voiceover follows the writing rules; read it aloud once and cut anything a person
wouldn't say.

**Write** `08-creative/<concept>.md`.

---

## Stage 9: Daily Campaign Audit (recurring)

**Pull** via Google Ads MCP, or ask for a CSV export. Also pull from HubSpot: deals created in the
window with `hs_analytics_source = PAID_SEARCH` and their stages.

**Prompt 1:**

> Compare the last 7 days of Google Ads performance to the previous 7. For each campaign show:
> spend, conversions (primary), CPA, cost per SQL, pipeline created, CPC, CTR, impression share,
> search lost IS (rank), search lost IS (budget), and top search terms. Flag: CPA up 20%+,
> cost per SQL up 20%+, budget-limited winners, rank-limited campaigns, branded leakage in
> non-branded campaigns, wasted-spend queries (spend with zero conversions, or job/patient
> intent), and ad groups spending with no conversions in 14 days.

**Prompt 2:**

> Turn this audit into an action list. For each action: campaign, issue, evidence, recommended
> change, risk level (low/med/high), and expected impact.

Low-volume caution: if a campaign has under 10 conversions in the window, say the comparison is
noise and recommend holding unless spend is clearly wasted.

**Write** `audits/YYYY-MM-DD.md`. Show the action list and ask which items to apply.

---

## Stage 10: Weekly Scaling Plan (recurring, Fridays)

**Prompt 1:**

> Compare performance across 7, 14, and 30-day windows. Identify campaigns, keywords, ads, and
> landing pages with consistent green signals. Recommend which budgets to increase by 15-20%,
> which to hold, which to decrease, and which tests to launch next. Do not recommend scaling
> anything unless the signal is consistent across all three windows AND holds on cost per SQL,
> not just cost per lead.

**Prompt 2:**

> Create next week's testing roadmap: 3 keyword tests, 3 creative tests, 2 landing page tests,
> 2 conversion/offer tests, and 1 campaign structure test. Rank by expected impact and
> implementation difficulty. One variable per test.

Feed the winners back: new winning phrases go into `01-language-bank.md`, new negatives into
`03-keywords.md`, winning angles into Stage 7 and 8 briefs.

**Write** `scale/YYYY-WW.md`. The summary also feeds `/weekly-retro`.

---

## Output Format (every stage)

End every stage with:

```
STAGE {n} COMPLETE — {name}
Saved: google-ads-workspace/{file}
Key findings: {3 bullets}
Needs your input: {questions, or "none"}
Next: /google-ads {next-stage}
```
