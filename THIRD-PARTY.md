# Third-party skills

Skills installed alongside `jpstack` that are **owned and maintained upstream**. They are
deliberately *not* vendored into this repository — that would fork someone else's work and
let it drift. This file records what is installed and how to restore it.

Restore everything with:

```bash
npx skills add coreyhaines31/marketingskills --yes
npx skills add jamesgray007/hoai-course --skill writing-linkedin-posts --yes
npx skills add vercel-labs/next-skills --skill next-best-practices --yes
npx skills add google-labs-code/stitch-skills --skill shadcn-ui --yes
npx skills add googleworkspace/cli --yes
npx skills add vercel-labs/skills --skill find-skills --yes
npx skills add anthropics/skills --skill skill-creator --yes
git clone https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
```

## Marketing — [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills)

| Skill | Use |
|-------|-----|
| `cold-email` | B2B cold outreach emails and follow-up sequences |
| `sales-enablement` | Pitch decks, one-pagers, objection handling, demo scripts |
| `copywriting` | Write and improve marketing copy |
| `content-strategy` | Content strategy, topics, editorial calendar |
| `email-sequence` | Drip campaigns and lifecycle email flows |
| `pricing-strategy` | Pricing, packaging, monetization |
| `seo-audit` | Audit and diagnose SEO issues |

## Social — [jamesgray007/hoai-course](https://github.com/jamesgray007/hoai-course)

| Skill | Use |
|-------|-----|
| `writing-linkedin-posts` | LinkedIn posts in a Top Voice style |

## Engineering — [garrytan/gstack](https://github.com/garrytan/gstack)

Installed as a bundle at `~/.claude/skills/gstack/`, with individual skills symlinked out.

| Skill | Use |
|-------|-----|
| `browse` | Fast headless web browsing |
| `plan-ceo-review` | CEO/founder-mode plan review |
| `plan-eng-review` | Engineering-manager-mode plan review |
| `ship` | Merge, test, review, bump, PR |
| `review` | Pre-landing PR review |
| `retro` | Weekly engineering retrospective |

## Frontend

| Skill | Source | Use |
|-------|--------|-----|
| `next-best-practices` | [vercel-labs/next-skills](https://github.com/vercel-labs/next-skills) | Next.js conventions, RSC, data patterns |
| `shadcn-ui` | [google-labs-code/stitch-skills](https://github.com/google-labs-code/stitch-skills) | shadcn/ui discovery, install, customization |

## Google Workspace — [googleworkspace/cli](https://github.com/googleworkspace/cli)

Tracked in `~/.agents/.skill-lock.json`.

`gws-docs` · `gws-docs-write` · `gws-drive` · `gws-gmail` · `gws-sheets` ·
`gws-sheets-append` · `gws-sheets-read` · `gws-slides`

## Utility

| Skill | Source | Use |
|-------|--------|-----|
| `find-skills` | [vercel-labs/skills](https://github.com/vercel-labs/skills) | Discover and install new agent skills |
| `skill-creator` | [anthropics/skills](https://github.com/anthropics/skills) | Create, modify and improve skills |
| `api-key-manager` | Local (custom) | Store and manage API keys across sessions |
