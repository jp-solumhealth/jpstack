# jpstack

**14 opinionated Claude Code skills for running a healthcare AI startup as a solo founder.**

Built by [JP Montoya](https://linkedin.com/in/jpmontoya), CEO of [Solum Health](https://getsolum.com) (YC S22). These are the exact skills I use daily to run sales, find PMF, prep for conferences, coach my pricing, plan sprints, and build content — all from the terminal.

Pairs with [gstack](https://github.com/garrytan/gstack) for engineering execution. jpstack handles the business side, gstack handles the code side.

## The Skills

### Founder Operating System

| Skill | Slash Command | What It Does |
|-------|--------------|--------------|
| [Chief of Staff](chief-of-staff/) | `/chief-of-staff` | Morning briefing from HubSpot pipeline, Fireflies meetings, Apollo sequences. Classifies deals as HOT/AT RISK/STALE. |
| [PMF Pulse](pmf-pulse/) | `/pmf-pulse` | Multi-source PMF intelligence: customer calls, Reddit pain points, Indeed role attrition, Ahrefs competitor benchmarks, industry forums. Where to focus, what to cut, where to double down. |
| [Product Insights](product-insights/) | `/product-insights` | Sprint planning data: feature requests, bugs, UX friction, workflow gaps from customer calls. RICE-scored and ready for engineering. |
| [Weekly Retro](weekly-retro/) | `/weekly-retro` | Friday scorecard across all channels: revenue pace vs. $2M target, deals won/lost, calls made, outreach performance, content published. Trend tracking week-over-week. |
| [Investor Report](investor-report/) | `/investor-report` | Monthly investor update DOCX from Google Sheets KPIs + Fireflies call insights. |

### Sales & Revenue

| Skill | Slash Command | What It Does |
|-------|--------------|--------------|
| [Pricing Coach](pricing-coach/) | `/pricing-coach` | Analyzes sales calls for pricing quality. Scores 1-5 against proven benchmarks (86% free trial win rate), flags violations, delivers coaching with scripts. |
| [Conference Prep](conference-prep/) | `/conference-prep` | Pre-conference: Lead enrichment via Apollo + branded curated agenda with top session picks. |
| [Post-Conference Insights](post-conference-insights/) | `/post-conference-insights` | Post-conference: Branded 1-2 page PDF one-pager with stat cards and role-based action items. Anti-AI detection pass. |
| [Post-Conference Follow-Up](post-conference-fup/) | `/post-conference-fup` | Post-conference: Segments contacts into HOT/WARM/COOL/COLD, builds tailored Apollo sequences for each segment, creates HubSpot deals, tracks conference ROI. |
| [Prior Auth Review](prior-auth-review/) | `/prior-auth-review` | Product demo: Automates payer PA review using NPI, ICD-10, CMS Coverage MCP connectors. 30-min review in under 5 minutes. |

### Content & Brand

| Skill | Slash Command | What It Does |
|-------|--------------|--------------|
| [X Healthcare Posts](x-healthcare-posts/) | `/x-healthcare-posts` | X posts and threads for Healthcare AI audiences. Car Dealership Guy style. Optimized for Heavy Ranker algorithm. |
| [LinkedIn Carousel Builder](linkedin-carousel-builder/) | `/linkedin-carousel-builder` | Branded carousel PDFs (1080x1350, 4:5) with safe zone compliance and Playwright export. |
| [Fact Check](fact-check/) | `/fact-check` | Verifies numerical claims before finalization. Writes verification scripts, classifies claims, produces audit reports. |
| [Solum Health Brand](solum-health-brand/) | `/solum-health-brand` | Auto-activates on any Solum content. Full design system: colors, DM Sans typography, gradients, CSS starter. |

## Companion: gstack (Engineering Execution)

jpstack handles business execution. For engineering execution, install [gstack](https://github.com/garrytan/gstack) alongside:

| gstack Skill | What It Does |
|-------------|--------------|
| `/plan-ceo-review` | Rethinks the problem before building. "What is the 10-star product?" |
| `/plan-eng-review` | Architecture review: data flow, diagrams, edge cases, test matrix |
| `/review` | Paranoid code review: N+1 queries, race conditions, trust boundaries |
| `/ship` | Release workflow: sync main, run tests, push branch, open PR |
| `/qa` | Systematic QA testing with health scores and structured reports |
| `/retro` | Engineering retro: commit history, LOC, test ratios, PR sizes |
| `/browse` | Headless Chromium for testing web apps |

```bash
# Install both stacks
git clone https://github.com/jp-solumhealth/jpstack.git ~/.claude/skills/jpstack
git clone https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
cd ~/.claude/skills/jpstack && ./setup
cd ~/.claude/skills/gstack && ./setup
```

## The Full Conference Lifecycle

jpstack includes a complete conference pipeline across 3 skills:

```
BEFORE                    DURING              AFTER
/conference-prep    →    [attend]    →    /post-conference-insights
  - ICP attendee list                       - Branded PDF one-pager
  - Apollo enrichment                       - Shareable with prospects
  - Curated agenda doc
                                         /post-conference-fup
                                           - Segment HOT/WARM/COOL/COLD
                                           - Personalized emails for HOT
                                           - Apollo sequences for rest
                                           - HubSpot deals + ROI tracking
```

## Requirements

- [Claude Code](https://claude.ai/code) with skills support
- MCP connectors (optional but recommended):
  - **HubSpot** — Chief of Staff, Product Insights, Weekly Retro, Post-Conference FUP
  - **Fireflies** — Pricing Coach, Product Insights, PMF Pulse, Investor Report, Weekly Retro
  - **Apollo.io** — Conference Prep, Post-Conference FUP, PMF Pulse, Weekly Retro
  - **Ahrefs** — PMF Pulse competitor benchmarking
  - **ICD-10 / NPI / CMS Coverage** — Prior Auth Review demo
- Python 3.10+ with `fpdf2` — Post-Conference PDF generation
- Playwright — LinkedIn Carousel export

## Installation

```bash
git clone https://github.com/jp-solumhealth/jpstack.git ~/.claude/skills/jpstack
cd ~/.claude/skills/jpstack && ./setup
```

## Customizing for Your Startup

1. Fork and replace brand in `solum-health-brand/SKILL.md`
2. Update ICP criteria in `conference-prep/references/icp-criteria.md`
3. Adjust pricing benchmarks in `pricing-coach/references/scoring-rubric.md`
4. Update PMF Pulse competitors and Reddit terms in `pmf-pulse/SKILL.md`
5. Set your revenue target in `weekly-retro/SKILL.md`
6. Swap MCP connectors — patterns work with any CRM/dialer

## About Solum Health

[Solum Health](https://getsolum.com) builds AI-powered front-office automation for healthcare providers. Our AI assistant **Annie** handles prior authorization, insurance verification, patient intake, and claims management.

## License

MIT
