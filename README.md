# jpstack

**jpstack turns your terminal into a full operating system for running a startup as a solo founder.**

14 opinionated workflow skills that handle the business side — daily briefings, PMF intelligence, sprint planning, sales coaching, conference pipelines, investor reports, and content creation — all as slash commands.

### Without jpstack

- You check HubSpot, Fireflies, Apollo, and email separately every morning
- Conference follow-up dies in a spreadsheet. Half the leads never get an email
- Sprint planning is vibes. "I think customers want X" with no receipts
- Pricing conversations repeat the same mistakes because nobody is watching
- You spend 3 hours on an investor update that should take 30 minutes
- Content sits in a doc for weeks because there's no system to ship it

### With jpstack

| Skill | Mode | What it does |
|-------|------|-------------|
| `/chief-of-staff` | Daily briefer | Pulls HubSpot, Fireflies, Apollo. Classifies deals HOT/AT RISK/STALE. Prioritized morning briefing in under 3 minutes. |
| `/pmf-pulse` | Strategy advisor | Aggregates customer calls, Reddit pain points, Indeed attrition signals, Ahrefs competitor data, industry forums. Tells you where to focus and what to cut. |
| `/product-insights` | Sprint planner | Extracts feature requests, bugs, UX friction from customer calls. RICE-scores everything. Feeds engineering with evidence, not opinions. |
| `/weekly-retro` | Friday scorecard | Reviews all channels: revenue pace, deals won/lost, calls made, outreach performance, content published. Week-over-week trends. |
| `/investor-report` | Board reporter | Pulls KPIs from Google Sheets + call insights from Fireflies. Outputs a structured DOCX in your template. |
| `/pricing-coach` | Sales coach | Scores each sales call 1-5 against proven benchmarks. Flags violations. Delivers coaching reports with specific scripts to use next week. |
| `/conference-prep` | Event strategist | Pre-event: enriches attendee list via Apollo, classifies ICPs, builds branded curated agenda. |
| `/post-conference-insights` | Thought leader | Post-event: branded 1-2 page PDF one-pager with stat cards and action items. Anti-AI detection pass included. |
| `/post-conference-fup` | Pipeline builder | Post-event: segments contacts HOT/WARM/COOL/COLD, builds tailored sequences, creates deals, tracks conference ROI. |
| `/prior-auth-review` | Product demo | Automates payer PA review using NPI, ICD-10, CMS Coverage connectors. 30-min review in under 5 minutes. |
| `/x-healthcare-posts` | Content creator | X posts and threads for Healthcare AI audiences. Operator voice. Optimized for Heavy Ranker algorithm. |
| `/linkedin-carousel-builder` | Visual content | Branded carousel PDFs (1080x1350, 4:5) with safe zones, mobile typography, Playwright export. |
| `/fact-check` | QA engineer | Verifies numerical claims before publishing. Writes verification scripts, classifies claims, produces audit reports. |
| `/solum-health-brand` | Brand guardian | Auto-activates on any content. Full design system: colors, DM Sans, gradients, spacing, CSS starter. |

## Demo: one conference, four skills

I use jpstack to run the full lifecycle of every conference. One event generates 40-60 qualified leads and $200K+ in pipeline when the system works.

```
You:   /conference-prep BHASe 2026

jpstack: [Runs two parallel tracks]

         Track A — Lead Intelligence:
         Extracted 847 attendees from conference app.
         Classified 94 as ICP (Primary: 31, Secondary: 63).
         Enriched via Apollo. Verified 67 emails via Hunter.io.
         Saved: BHASe_2026_ICP_Attendees.csv (67 verified contacts)

         Track B — Curated Agenda:
         Analyzed 84 sessions. Selected top 8 for practice owners.
         Generated branded HTML document with "Why attend" insights.
         Saved: BHASe_2026_Curated_Agenda.html

         [You attend the conference. Take notes on who you met.]

You:   /post-conference-insights BHASe 2026

jpstack: [Research + content generation + humanization + PDF]

         Generated 2-page branded PDF: 4 stat cards, 5 insight sections,
         role-based action items for billing, clinical, front desk, owners.
         AI detection score: 11%. Ship it.
         Saved: BHASe_2026_OnePager_Solum_Health.pdf

You:   /post-conference-fup BHASe 2026

jpstack: Segmentation complete:

         HOT — Met & Engaged: 8 contacts
           1. Sarah Chen — CEO at Horizons ABA (discussed PA pain, wants demo)
           2. Marcus Williams — COO at Cedar Grove (pricing conversation started)
           ...

         WARM — Replied / Brief Contact: 14 contacts
         COOL — No Response / Didn't Meet: 31 contacts
         COLD — Badge Scan Only: 14 contacts

         Does this segmentation look right?

You:   Yes, move Marcus to HOT. Build the sequences.

jpstack: [Drafts 8 personalized HOT emails, creates 3 Apollo sequences,
         creates HubSpot deals for HOT contacts]

         Pipeline created: $340K across 8 deals
         WARM sequence: 14 contacts enrolled (4-touch, 10 days)
         COOL sequence: 31 contacts enrolled (4-touch, 14 days)
         COLD sequence: 14 contacts enrolled (3-touch value-first, 14 days)
```

8 personalized follow-ups sent within 24 hours. 59 contacts in automated sequences. Zero leads lost to "I'll follow up later" syndrome.

## Who this is for

You are a founder-CEO running B2B sales at an early-stage startup. You are doing founder-led sales, attending conferences, planning sprints, sending investor updates, and building content — all yourself or with a tiny team.

You want your CRM, call recordings, outreach tools, and market data to talk to each other and tell you what to do next. Not in a dashboard. In your terminal. As actionable output.

This is not a prompt pack. It is an operating system for founders who sell.

## The full conference lifecycle

jpstack includes a complete conference pipeline across 3 skills:

```
BEFORE                    DURING              AFTER
/conference-prep    →    [attend]    →    /post-conference-insights
  - ICP attendee list                       - Branded PDF one-pager
  - Apollo enrichment                       - Share with prospects
  - Curated agenda

                                         /post-conference-fup
                                           - Segment HOT/WARM/COOL/COLD
                                           - Personalized emails for HOT
                                           - Apollo sequences for rest
                                           - HubSpot deals + ROI tracking
```

## Pairs with gstack

jpstack handles business execution. [gstack](https://github.com/garrytan/gstack) handles engineering execution. Install both.

| gstack Skill | What It Does |
|-------------|--------------|
| `/plan-ceo-review` | Rethink the problem. Find the 10-star product. |
| `/plan-eng-review` | Architecture, data flow, diagrams, edge cases, test matrix. |
| `/review` | Find bugs that pass CI but blow up in production. |
| `/ship` | Sync main, run tests, push branch, open PR. |
| `/qa` | Systematic QA testing with health scores and structured reports. |
| `/browse` | Headless Chromium. Give the agent eyes on your live app. |
| `/retro` | Engineering retro: commits, LOC, test ratios, contributor feedback. |

## Install

Open your terminal and paste this:

```bash
git clone https://github.com/jp-solumhealth/jpstack.git ~/.claude/skills/jpstack && cd ~/.claude/skills/jpstack && ./setup
```

That's it. The `setup` script creates symlinks from `~/.claude/skills/<skill-name>` to each skill directory. No binaries, no background processes, no build step.

### Install both stacks

```bash
git clone https://github.com/jp-solumhealth/jpstack.git ~/.claude/skills/jpstack && cd ~/.claude/skills/jpstack && ./setup
git clone https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup
```

### What gets installed

- Skill files (Markdown prompts) in `~/.claude/skills/jpstack/`
- Symlinks at `~/.claude/skills/chief-of-staff`, `~/.claude/skills/pricing-coach`, etc.
- Reference files: scoring rubrics, ICP criteria, brand guides, anti-AI checklists
- Scripts: PDF generator for post-conference one-pagers
- Assets: HTML templates, logos

Everything lives inside `~/.claude/skills/`. Nothing touches your PATH or runs in the background.

### MCP connectors (recommended)

These skills pull from your existing tools. The more connectors you have, the more skills light up:

| Connector | Skills that use it |
|-----------|--------------------|
| **HubSpot** | chief-of-staff, product-insights, weekly-retro, post-conference-fup |
| **Fireflies** | pricing-coach, product-insights, pmf-pulse, investor-report, weekly-retro |
| **Apollo.io** | conference-prep, post-conference-fup, pmf-pulse, weekly-retro |
| **Ahrefs** | pmf-pulse competitor benchmarking |
| **ICD-10 / NPI / CMS** | prior-auth-review product demo |

Skills degrade gracefully. If a connector isn't available, the skill uses what it can and tells you what's missing.

### Other requirements

- Python 3.10+ with `fpdf2` — for post-conference PDF generation
- Playwright — for LinkedIn carousel export

## Upgrading

```bash
cd ~/.claude/skills/jpstack && git pull && ./setup
```

## Uninstalling

```bash
for s in chief-of-staff pmf-pulse product-insights weekly-retro investor-report pricing-coach conference-prep post-conference-insights post-conference-fup prior-auth-review x-healthcare-posts linkedin-carousel-builder fact-check solum-health-brand; do rm -f ~/.claude/skills/$s; done && rm -rf ~/.claude/skills/jpstack
```

## How I use these skills

Built by [JP Montoya](https://linkedin.com/in/jpmontoya), CEO of [Solum Health](https://getsolum.com) (YC S22).

I built jpstack because I was spending more time context-switching between tools than actually selling. HubSpot tab, Fireflies tab, Apollo tab, Google Sheets tab, content doc tab. Five tools open, none of them talking to each other.

Now I start every morning with `/chief-of-staff`. It pulls everything and tells me what matters today. On Fridays I run `/weekly-retro` to see if the week moved the needle on revenue. Before every conference I run `/conference-prep`. After every conference I run `/post-conference-fup` within 24 hours.

The unlock is not any single skill. It is that they all share context. The attendee list from `/conference-prep` feeds into `/post-conference-fup`. The call data from `/pricing-coach` shows up in `/weekly-retro`. The PMF signals from `/pmf-pulse` inform what `/product-insights` recommends for the sprint.

That compounding is the point.

## Customizing for your startup

1. Fork this repo and replace brand in `solum-health-brand/SKILL.md`
2. Update ICP criteria in `conference-prep/references/icp-criteria.md`
3. Adjust pricing benchmarks in `pricing-coach/references/scoring-rubric.md`
4. Update PMF competitors and Reddit search terms in `pmf-pulse/SKILL.md`
5. Set your revenue target in `weekly-retro/SKILL.md`
6. Swap MCP connectors — patterns work with any CRM, dialer, or outreach tool

## About Solum Health

[Solum Health](https://getsolum.com) builds AI-powered front-office automation for healthcare providers. Our AI assistant Annie handles prior authorization, insurance verification, patient intake, and claims management.

## License

MIT
