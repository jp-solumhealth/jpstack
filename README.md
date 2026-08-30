# jpstack

Opinionated Claude Code skills for running a healthcare AI startup as a solo founder —
daily briefings, sales intelligence, conference pipelines, product signals, and content
creation, all as slash commands.

Built and used daily at [Solum Health](https://getsolum.com).

## Install

```bash
git clone https://github.com/jp-solumhealth/jpstack.git ~/Documents/Claude/Skills/jpstack
cd ~/Documents/Claude/Skills/jpstack
./install.sh          # symlinks every skill into ~/.claude/skills/
```

Or cherry-pick one:

```bash
ln -s ~/Documents/Claude/Skills/jpstack/chief-of-staff ~/.claude/skills/chief-of-staff
```

Most skills expect one or more of: HubSpot, Fathom, Apollo, Instantly, Google Workspace.
See `setup/` for connection notes.

---

## Daily & Weekly Operations

| Skill | What it does |
|-------|--------------|
| `chief-of-staff` | Daily CEO morning briefing across HubSpot pipeline, Fathom meetings, Instantly outreach and email. Surfaces hot deals, at-risk deals, action items and the day's priorities. |
| `weekly-review` | Weekly CEO dashboard: pipeline movement, meeting highlights, outreach stats, cross-referenced for accuracy, plus next-week priorities. |
| `weekly-retro` | Weekly business retrospective for a solo founder — deals closed/lost, call quality, what moved and what stalled. |

## Sales — Before and After the Call

| Skill | What it does |
|-------|--------------|
| `precall-brief` | Branded HTML pre-call intelligence brief ~10 minutes before every intro/discovery call with a new prospect. |
| `meeting-prep` | One-page prep brief before any sales or customer call: company context, relationship history, deal status, past meeting highlights, talking points. |
| `post-call` | Runs after any prospect meeting: HubSpot pipeline hygiene (create/advance deals per qualification rules) plus a follow-up email that leads with the prospect's own words. |
| `meeting-followup` | Post-meeting package: follow-up email draft, HubSpot deal notes with stage/amount recommendations, and an internal debrief with buying signals and objections. |
| `pricing-coach` | Weekly pricing conversation coach — extracts every pricing moment from the week's calls and scores it. |
| `win-loss` | Systematic win-loss analysis across all deals. |

## Sales — Proposals & Business Cases

| Skill | What it does |
|-------|--------------|
| `sow-builder` | Scoped Statements of Work with an embedded business case, cross-referenced across Fathom, HubSpot and Apollo so every number traces to a source. |
| `solum-business-case` | CFO-grade business case: variable-driven multi-tab Excel model (scenarios, ROI, payback) and an optional matching deck. |
| `business-case-builder` | Lighter branded 1–2 slide PPTX business case with ROI. Prefer `solum-business-case` for anything CFO-facing. |
| `one-pager-builder` | Single-page branded PDF opportunity brief aimed at a prospect's C-suite. |

## Conferences & Prospecting

| Skill | What it does |
|-------|--------------|
| `conference-prep` | Full conference prep: attendee extraction, ICP classification, contact enrichment waterfall, email validation, Instantly upload, and a curated agenda document. |
| `post-conference-fup` | Post-conference follow-up engine — segments contacts by engagement level and drives the right sequence for each. |
| `post-conference-insights` | Branded 1–2 page conference recap that positions the company as a thought leader. |
| `waalaxy-prospecting` | Turns a raw attendee or prospect list into a Waalaxy-ready LinkedIn CSV: ICP gate before any API spend, title resolution, email waterfall, first-name hygiene. |
| `icp-research` | Derives or stress-tests an Ideal Customer Profile from evidence, using a parallel agent fan-out plus an adversarial red team. |

## Marketing & Content

| Skill | What it does |
|-------|--------------|
| `linkedin-carousel-builder` | Branded LinkedIn carousel PDFs built for engagement. |
| `x-healthcare-posts` | X/Twitter posts and threads for a Healthcare AI audience. |
| `site-review` | Website SEO and conversion audit — technical SEO, intake/lead form assessment, CRO — with built-in fact-checking. |
| `solum-health-brand` | Brand guidelines and visual identity, invoked first on any design task and used to QA the output. |

## Product & Company Intelligence

| Skill | What it does |
|-------|--------------|
| `pmf-pulse` | Product-market fit intelligence aggregated from calls, CRM, and prospect signals. |
| `product-insights` | Feature requests, bug reports and usage patterns rolled up for sprint planning and roadmap. |
| `team-feedback` | Formats platform feedback — new rules, bugs, feature requests — in a strict WHEN/THEN/Example shape the engineering team can act on. |
| `investor-report` | Monthly investor report: metrics from Sheets plus customer-conversation insights, output as a structured DOCX. |

## Healthcare Domain

| Skill | What it does |
|-------|--------------|
| `prior-auth-review` | Automates payer-side review of prior authorization requests. |

## Quality & Process

| Skill | What it does |
|-------|--------------|
| `fact-check` | Verifies claims and figures before anything ships. |
| `doc-conversion-qa` | Quality gate for document format conversions (PDF↔PPTX↔DOCX) — blocks "done" until fidelity is checked. |
| `postmortem` | Captures and consults lessons from past failures so the same mistake is not repeated. |

---

## Status notes

These skills predate the Fireflies → Fathom migration and still reference the retired
Fireflies API. They need updating before use:

- `pmf-pulse`
- `product-insights`
- `post-conference-fup`
- `weekly-retro`

Every other skill that reads meetings uses the Fathom MCP.

## Related repositories

| Repo | Contents |
|------|----------|
| `jpstack-private` *(private)* | Legal, real-estate and personal-finance skills that embed real counterparty names, deal records and rate cards. |
| `google-ads-report` *(private)* | Daily Google Ads performance report and optimization skill. |

Third-party skills used alongside these — and how to reinstall them — are listed in
[`THIRD-PARTY.md`](THIRD-PARTY.md).

## License

MIT — see [LICENSE](LICENSE).
