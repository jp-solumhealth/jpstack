# jpstack

**12 opinionated Claude Code skills for running a healthcare AI startup as a solo founder.**

Built by [JP Montoya](https://linkedin.com/in/jpmontoya), CEO of [Solum Health](https://getsolum.com) (YC S22). These are the exact skills I use daily to run sales, find PMF, prep for conferences, coach my pricing, plan sprints, and build content — all from the terminal.

## The Skills

### Founder Operating System

| Skill | Slash Command | Role | What It Does |
|-------|--------------|------|--------------|
| [Chief of Staff](chief-of-staff/) | `/chief-of-staff` | Daily Briefer | Pulls HubSpot pipeline, Fireflies meetings, Apollo sequences. Classifies deals as HOT/AT RISK/STALE. Delivers a prioritized morning briefing in under 3 minutes. |
| [PMF Pulse](pmf-pulse/) | `/pmf-pulse` | Strategy Advisor | Multi-source intelligence engine: customer calls, Reddit pain points, Indeed role attrition, competitor benchmarks (Ahrefs), industry forums. Tells you where to focus, what to cut, where to double down. |
| [Product Insights](product-insights/) | `/product-insights` | Sprint Planner | Aggregates feature requests, bugs, UX friction, and workflow gaps from customer calls and CRM. RICE-scores everything. Feeds engineering with prioritized, evidence-backed sprint items. |
| [Investor Report](investor-report/) | `/investor-report` | Board Reporter | Pulls KPIs from Google Sheets and customer call insights from Fireflies. Outputs a structured DOCX matching our investor update template. |

### Sales & Revenue

| Skill | Slash Command | Role | What It Does |
|-------|--------------|------|--------------|
| [Pricing Coach](pricing-coach/) | `/pricing-coach` | Sales Coach | Analyzes sales calls from Fireflies for pricing conversation quality. Scores each call 1-5 against proven benchmarks (86% free trial win rate), flags violations, delivers coaching reports with scripts. |
| [Conference Prep](conference-prep/) | `/conference-prep` | Event Strategist | Two parallel tracks: (1) Lead intelligence pipeline — extract attendees, classify ICPs, enrich via Apollo, verify emails. (2) Branded curated agenda with top session picks. |
| [Post-Conference Insights](post-conference-insights/) | `/post-conference-insights` | Thought Leadership | Turns any conference into a branded 1-2 page PDF one-pager with stat cards, insight sections, and role-based action items. Anti-AI detection pass included. |
| [Prior Auth Review](prior-auth-review/) | `/prior-auth-review` | Product Demo | Automates payer review of prior authorization requests using NPI, ICD-10, and CMS Coverage MCP connectors. Reduces 30-60 min reviews to under 5 minutes. |

### Content & Brand

| Skill | Slash Command | Role | What It Does |
|-------|--------------|------|--------------|
| [X Healthcare Posts](x-healthcare-posts/) | `/x-healthcare-posts` | Content Creator | High-performing X posts and threads for Healthcare AI audiences. Car Dealership Guy style operator voice. Optimized for X's Heavy Ranker algorithm. |
| [LinkedIn Carousel Builder](linkedin-carousel-builder/) | `/linkedin-carousel-builder` | Visual Content | Branded carousel PDFs (1080x1350, 4:5 portrait) with safe zone compliance, mobile-optimized typography, and Playwright export. |
| [Fact Check](fact-check/) | `/fact-check` | QA Engineer | Verifies numerical claims and data-driven statements before finalization. Writes verification scripts, classifies claims, produces audit reports. |
| [Solum Health Brand](solum-health-brand/) | `/solum-health-brand` | Brand Guardian | Auto-activates on any Solum Health content. Complete design system: colors, typography (DM Sans), gradients, spacing, CSS starter. |

## Who This Is For

Founder-CEOs running B2B sales at early-stage startups, especially in healthcare. If you're:

- Doing founder-led sales and want your CRM to talk to you every morning
- Trying to find PMF and need market intelligence from Reddit, Indeed, competitors, and customers — all in one report
- Planning sprints with actual customer evidence instead of gut feel
- Attending 10+ conferences a year and need a system for lead gen + prep
- Building content for X and LinkedIn without a marketing team
- Coaching yourself on pricing conversations

These skills assume you have Claude Code with MCP connectors for HubSpot, Apollo, Fireflies, and optionally Google Workspace.

## Installation

```bash
# Clone into your Claude skills directory
git clone https://github.com/jp-solumhealth/jpstack.git ~/.claude/skills/jpstack

# Run setup to create symlinks
cd ~/.claude/skills/jpstack && ./setup
```

The `setup` script creates symlinks from `~/.claude/skills/<skill-name>` to each skill directory. No binaries, no background processes.

## Requirements

- [Claude Code](https://claude.ai/code) with skills support
- MCP connectors (optional but recommended):
  - **HubSpot** — for Chief of Staff and Product Insights
  - **Fireflies** — for Pricing Coach, Product Insights, PMF Pulse, and Investor Report
  - **Apollo.io** — for Conference Prep lead enrichment and PMF Pulse
  - **Ahrefs** — for PMF Pulse competitor benchmarking
  - **ICD-10 / NPI / CMS Coverage** — for Prior Auth Review demo
- Python 3.10+ with `fpdf2` — for Post-Conference PDF generation
- Playwright — for LinkedIn Carousel export

## How Skills Work

Each skill is a directory with a `SKILL.md` file that Claude Code loads as instructions when invoked via slash command. Some skills include:

- `references/` — Rubrics, checklists, brand guides, and criteria docs
- `scripts/` — Python scripts for PDF generation, data analysis
- `assets/` — Templates, logos, and design files

## Customizing for Your Startup

1. **Fork this repo** and replace Solum Health brand with yours in `solum-health-brand/SKILL.md`
2. **Update ICP criteria** in `conference-prep/references/icp-criteria.md` with your target customer profile
3. **Adjust pricing benchmarks** in `pricing-coach/references/scoring-rubric.md` to match your pricing model
4. **Update PMF Pulse** with your competitive landscape and Reddit search terms in `pmf-pulse/SKILL.md`
5. **Swap MCP connectors** — the skills reference HubSpot/Apollo/Fireflies but the patterns work with any CRM/dialer

## About Solum Health

[Solum Health](https://getsolum.com) builds AI-powered front-office automation for healthcare providers. Our AI assistant **Annie** handles prior authorization, insurance verification, patient intake, and claims management.

## License

MIT
