---
name: seo
description: >
  Solum Health SEO operator built on OpenSEO (open-source Semrush/Ahrefs alternative, MCP at
  app.openseo.so/mcp). Seeds OpenSEO with Solum's ICP, competitors, and money pages, then runs
  keyword research, competitor gaps, site audits, and prospect local-SEO checks, and turns the
  results into content and sales actions. Use when asked for "SEO", "keyword research",
  "what should we rank for", "organic traffic", "competitor keywords", "content gaps",
  "backlinks", "SEO pulse", or "local SEO for a prospect".
  NOTE: For a single-page on-page + conversion (CRO/intake) review of a site, use /site-review.
  This skill works from search data: rankings, demand, competitors, and crawls.
---

# SEO — Solum Health on OpenSEO

OpenSEO provides the data (DataForSEO keywords, SERPs, rankings, backlinks, site crawls,
Search Console) and ten generic workflow skills. This skill adds what they don't know:
who Solum sells to, who we compete with, which pages make money, and how SEO output
feeds the rest of jpstack.

Source: https://github.com/every-app/open-seo (MIT). Don't copy their skills here; call
them when installed and fall back to the MCP tools directly when not.

## Usage

```
/seo                          → SEO pulse (default): what moved, what to do this week
/seo setup                    → one-time: seed the OpenSEO project with Solum context
/seo keywords [seeds]         → keyword opportunities for Solum's ICP
/seo competitors [domain]     → what a competitor ranks for that we don't
/seo audit [domain]           → crawl + ranking audit (default: getsolum.com)
/seo prospect <practice>      → local SEO snapshot of a prospect practice (sales asset)
```

## Step 0: Connection check (always, free)

1. Look for OpenSEO MCP tools. Their names end in `whoami`, `list_projects`,
   `get_project_context`, etc.; the prefix depends on how it was installed
   (`mcp__openseo__*` or `mcp__plugin_openseo_openseo__*`).
2. Call `whoami` to confirm the connection and show remaining credits.
3. If OpenSEO is not connected, stop and give the user the install steps:

```bash
# Recommended: plugin = MCP + all 10 OpenSEO skills in one step (run inside Claude Code)
/plugin marketplace add every-app/open-seo
/plugin install openseo@openseo

# Or MCP only
claude mcp add --transport http --scope user openseo https://app.openseo.so/mcp
```

   OpenSEO needs an account (hosted: free tier, $10/mo, or pay-as-you-go credits) or a
   self-hosted instance with a DataForSEO API key. Don't fall back to guessing metrics
   without it. If Ahrefs MCP is connected, offer that as the data source instead.

4. `list_projects` → find the project for `getsolum.com`. If none exists, run `/seo setup`.

**Delegating to OpenSEO skills:** if the plugin is installed, its skills are
`/openseo:<name>` (standalone installs: `/<name>`). Where a mode below says "delegate",
invoke that skill *after* Solum context is in the project; it reads context from
OpenSEO. If the skills aren't installed, follow the listed MCP tools inline.

## Solum Health context (the seed)

Confirm this with the user before writing it to OpenSEO. It changes as the company does.

| Section | Content |
|---------|---------|
| `business_overview` | Solum Health (getsolum.com, YC S22): AI that automates the healthcare front office (prior authorization, insurance eligibility/benefits verification, patient intake, claims follow-up). Primary ICP: ABA therapy and behavioral/mental health practices and groups in the US. Buyers: practice owners, CEOs/COOs, billing and intake managers. |
| `current_goal` | Non-branded organic demo requests from ICP practices. Measure: demo-form conversions from organic + top-10 rankings for buying-intent terms. Ask the user for the current target and timeframe. |
| `positioning` | Replaces manual phone/fax/portal work on PAs and VOBs for high-volume, payer-heavy specialties. Claims must be defensible: pull numbers only from /fact-check-verified sources. |
| `writing_preferences` | Operator voice, no hype, no unverified clinical or outcome claims (YMYL: Google holds health content to a higher bar). Apply /solum-health-brand for anything visual. |

**Competitors** (`addCompetitors`, same list /pmf-pulse tracks): waystar.com, availity.com,
covermymeds.com, centralreach.com, collectly.com, tebra.com. Then run `find_serp_competitors` on
the seeds below and ask the user which search-only competitors to add. Those are often
content sites and RCM agencies, not product competitors.

**Seed keywords:** prior authorization software, AI prior authorization, insurance
verification automation, eligibility verification software, patient intake automation,
ABA billing software, ABA prior authorization, behavioral health billing, claims denial
management, healthcare front office automation.

**Key pages** (`addKeyPages`): discover from getsolum.com's sitemap. Tag the homepage
and demo page `money`, product pages `money`, and blog/resource hubs `hub`. Confirm
the list with the user.

## Modes

### `/seo setup`: seed the project (free, one time)

Delegate to `seo-project-setup` if installed, but pre-fill every answer from the table
above so the user confirms rather than types. Otherwise: `create_project` (if needed) →
`get_project_context` → `update_project_context` with the sections, competitors, and
key pages. Ask whether Google Search Console is connected on the project's Integrations
page. It's the best first-party signal and it's free.

### `/seo` (default): SEO pulse

Designed to run weekly (pairs with /weekly-retro on Fridays). Steps 1–4 are free
read-only calls. Only step 5 spends credits:

1. `get_project_context` and read the research log. Reuse anything under 30 days old.
2. `get_search_console_performance` (if connected): clicks/impressions trend, plus
   striking-distance queries with `minPosition: 5, maxPosition: 20, minImpressions: 50`.
3. `get_google_analytics_key_events` by organic landing page (if GA4 is connected):
   did organic traffic produce demo requests? Then `get_search_opportunities`, which
   scores Search Console pages ranking 4–20 by demand and business value.
4. `get_rank_tracker` for the project's tracker: winners/losers since the last check
   (`lastCheckedAt` shows freshness). If no tracker exists, offer to create one for the
   top 20 seed keywords and quote the cost with `estimate_rank_tracker_cost` first.
5. `get_ranked_keywords` for 1–2 competitors only if the user asks or it's been 30+ days.

Output (terminal, under one screen):

```
SEO PULSE — [date]
Organic clicks (28d): X (▲/▼ Y% vs prior)   Impressions: X   Credits left: X
Organic demo requests (28d): X   Top converting landing page: [url]
Striking distance (pos 4–20): [top 5 queries → page → position → impressions]
Movers: [keyword: old → new position]
This week: 1–3 actions, each tied to a page and a query
```

If Search Console and GA4 aren't connected, say that the pulse is running without
first-party data, and point to the project's Integrations page in OpenSEO.

### `/seo keywords [seeds]`: opportunity research

Delegate to `keyword-research` (then `keyword-clustering` if >30 keywords survive).
Solum-specific filters on top:
- Drop patient/consumer intent ("what is ABA therapy", "prior authorization meaning" for
  patients). We sell to practices, not families. Keep "how to" terms only when the searcher
  is a practice operator (e.g. "how to get ABA prior authorization approved faster").
- Prefer payer-specific long tails ("[payer] ABA prior authorization", "[payer] VOB")
  where CPC shows commercial intent even at low volume. B2B volume is small, so CPC matters
  more than volume.
- Tag saved keywords `icp:aba`, `icp:behavioral-health`, `product:prior-auth`,
  `product:vob`, `product:intake`, plus `intent:<intent>`. Save only after the user confirms.

### `/seo competitors [domain]`: gap analysis

Delegate to `competitor-analysis` (one domain) or `competitive-landscape` (the market).
Default domain: the next competitor not analyzed in the research log. Report which
of their traffic-driving pages target our ICP. A Waystar page ranking for hospital RCM
terms is not our gap. Hand content gaps to the "Feed the rest of jpstack" step below.

### `/seo audit [domain]`: site audit

Delegate to `seo-audit`. Default domain getsolum.com. Before reporting, run
/site-review on the top 1–3 money pages the audit names: OpenSEO covers crawl and
rankings, and site-review covers the demo form, CTAs, and trust signals it can't see.

### `/seo prospect <practice name or domain>`: sales asset

For ABA/behavioral health practices in pipeline or from /conference-prep lists. Local
search is how families find these practices, so it's a real pain we can show them in a
first meeting.

1. Delegate to `local-seo`: `search_local_businesses` to find the practice's listing,
   `get_business_profile`, `get_business_reviews`, and `get_local_rank_grid` for
   "ABA therapy near me" / "[city] ABA therapy" / "autism therapy [city]".
2. Confirm the budget first: rank grids cost more than single lookups. Run one keyword
   at a time unless the user asks for more.
3. Output a one-screen snapshot: where they show up in the map pack vs. 2–3 nearby
   competitors, review count/rating vs. those competitors, and profile gaps. Offer to turn it into a
   branded one-pager via /one-pager-builder.
4. Don't create an OpenSEO project per prospect unless the user wants one. Use a
   single "Prospects" project and log each run in its research log.

## Feed the rest of jpstack

End every run with the handoffs that apply:

| Finding | Hand to |
|---------|---------|
| Content gap / striking-distance query | /x-healthcare-posts or /linkedin-carousel-builder for distribution; a blog brief for the page itself |
| Demand trend for a product line | /pmf-pulse (market timing signal) |
| Pulse numbers | /weekly-retro content channel |
| Any stat going into published content | /fact-check first |
| Prospect snapshot | /one-pager-builder + the HubSpot deal notes |

## Guardrails

- **Credits:** state estimated spend before site audits, rank grids, and research
  batches over ~150 keywords, and check the research log to avoid re-buying data.
- **No invented metrics.** If OpenSEO returns nothing, write `unknown`. Provider traffic
  numbers are estimates, not visits. Say so when comparing to Search Console.
- **Rankings are dated.** A ranking claim that drives a recommendation needs a live
  `get_serp_results` check from this run, with the query and date.
- **No PHI.** Never paste patient data, call transcripts, or payer portal content into
  OpenSEO project context or reports. That context is stored on OpenSEO's servers.
- **Writes need confirmation:** `save_keywords`, `addCompetitors`, and overwriting a
  context section (merge into existing prose rather than replacing it).
- Reports saved with `save_report` live in OpenSEO. Give the user the link, the verdict,
  and the top action in chat.
