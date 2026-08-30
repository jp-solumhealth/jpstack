# Data Sources — gather and cross-confirm

The whole point of this skill is that numbers are **verified across sources**, not invented. Read API
keys from `~/.claude/.api-keys.json`. Pull from every source available, then build the **Verified
Inputs table** (one row per number → value + confirming source(s)). When sources disagree, surface it.

## Verified Inputs table (assemble this before building)

| Input | Value | Source(s) | Status |
|-------|-------|-----------|--------|
| Prior-auth rate | $16/auth | SOW deck p.8 + 5/22 call | confirmed |
| Re-auths / mo | 30 | 5/18 call (Nick) | confirmed |
| Admin hrs saved | 50–150 | 5/22 call (client-stated) | client estimate |
| Monthly claim base | — | not found | ESTIMATE — needs confirm |

Anything `ESTIMATE` must be flagged to JP and shown in yellow on the Assumptions tab.

## Fathom (call transcripts) — usually the richest source for pricing & value drivers

Base `MCP: mcp__claude_ai_Fathom__*`, header `Authorization: Bearer <key>` (_none — MCP_).

Find the prospect's calls, then pull the summary + sentences:
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
Mine the transcript for: per-unit pricing, monthly volumes, the hours/$ value drivers (quote the
client saying them), pain points, objections, agreed next steps. `date` is Unix ms. Note: Fathom =
JP's meetings; Fathom = Juliana's meetings (`https://api.fathom.ai/external/v1/meetings`, `X-Api-Key`).

## HubSpot — confirm deal economics & stage

Base `https://api.hubapi.com`, `Authorization: Bearer <key>` (`keys.hubspot.key`).
Search the company, get associated deals + contacts, read deal `amount`, `dealstage`, notes. Use this
to confirm the contract value and that the model's annual figure is consistent with the deal record.
Pipeline "Revenue Rocket 🚀": stage id `closedwon` is labeled **"Proposal Sent"** (not Closed Won) —
verify labels via `GET /crm/v3/pipelines/deals` before trusting any stage id.

## Gmail — confirm what was actually sent/agreed in writing

Use the Gmail MCP tools (`mcp__claude_ai_Gmail__search_threads`, `get_thread`) or the gws-gmail skill.
Search the contact's email + company domain for: quoted prices, volume commitments, scope, and any
numbers the client put in writing. Email confirmations outrank verbal recollection when they conflict.

## Apollo — company context (size, sites, growth)

Base `https://api.apollo.io`, `X-Api-Key` (`keys["apollo.io"].key`). Enrich by domain to sanity-check
scale (headcount, locations) against the volumes in the model — e.g., does "360 active clients" fit a
practice of this size? Flag mismatches >20%.

## Cross-confirmation rules

- **Two-source minimum for anything that drives the headline** (pricing, core volumes). One source =
  flag it.
- **Written > verbal** when they conflict (Gmail/SOW over a call recollection).
- **Client-stated value drivers** (hours saved, $/hr) are quoted and attributed, never silently
  changed. If they look aggressive (e.g., billable hours valued at full reimbursement vs. margin),
  note it as a CFO-scrutiny item — don't quietly "fix" the client's own number without asking.
- **On pushback, re-verify from source** — re-open the transcript/email, don't just restate.
