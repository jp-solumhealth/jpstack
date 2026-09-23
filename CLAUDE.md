# jpstack

15 Claude Code skills for running a healthcare AI startup as a solo CEO.
Pairs with [gstack](https://github.com/garrytan/gstack) for engineering execution.

## THIS REPOSITORY IS PUBLIC

Never commit, push, or otherwise publish real financial, tax, or personal data here.
This is a hard rule, not a preference. It applies to every file in the repo —
skills, references, scripts, tests, commit messages, PR bodies and issues alike.

**Never publish:**

- Real payee, client, patient, contractor or employee names — especially paired with
  an amount, a date, or what they were paid for.
- Amounts, balances, invoices, payroll, revenue figures or bank/card details taken
  from a real transaction.
- Tax identifiers of any kind: SSN, EIN, TIN — not even partially, beyond a last-4.
- Account, routing or card numbers; confirmation codes from a real payment.
- Databases, receipt vaults, CPA exports, bank downloads or statement screenshots.

**Instead:** use obviously fake placeholders in every example and test —
`Example Contractor`, `Example Co`, `ABC123`, `000-00-0000`, round invented amounts.
If a skill needs real data to run, it reads it at runtime from a local, gitignored
store. Real data belongs on the user's machine, or in a PRIVATE repository — never
in this one, and never in a screenshot pasted into an issue or PR.

A user sharing a receipt or statement in chat is giving you input to work from, NOT
permission to publish it. Ask before putting any detail from it into a file.

A `PreToolUse` hook (`.claude/hooks/guard-sensitive-data.sh`) blocks commits and
pushes carrying data files or recognizable PII. It is a backstop for the mechanical
cases — it cannot tell a real person's name from a fictional one. That judgment is
yours. Never work around the guard to publish real data; if it fires, fix the data.

To make the guard block a specific real name or string, add it to
`.claude/private-terms.txt` (gitignored, one term per line). If the file does not
exist, create it locally — it is never published.

## Available Slash Commands

### Founder Operating System
| Command | What It Does |
|---------|-------------|
| `/chief-of-staff` | Morning briefing from HubSpot + Fireflies + Apollo |
| `/pmf-pulse` | Multi-source PMF intelligence: calls, Reddit, Indeed, competitors |
| `/product-insights` | Sprint planning: feature requests, bugs, RICE scores from calls |
| `/weekly-retro` | Friday scorecard: revenue pace, deals, calls, outreach, content |
| `/investor-report` | Monthly investor update DOCX from KPIs + calls |

### Sales & Revenue
| Command | What It Does |
|---------|-------------|
| `/tax-deductions` | Deduction database: log receipts, track 1099 duties, export for the CPA |
| `/pricing-coach` | Weekly sales call pricing analysis and coaching |
| `/conference-prep` | Pre-event: lead enrichment + branded agenda |
| `/post-conference-insights` | Post-event: branded PDF one-pager |
| `/post-conference-fup` | Post-event: segment contacts, build sequences, track ROI |
| `/prior-auth-review` | Prior auth review demo using NPI/ICD-10/CMS MCP |

### Content & Brand
| Command | What It Does |
|---------|-------------|
| `/x-healthcare-posts` | X posts and threads for Healthcare AI audience |
| `/linkedin-carousel-builder` | Branded carousel PDFs for LinkedIn |
| `/fact-check` | Verify data claims before publishing |
| `/solum-health-brand` | Auto-applies Solum Health design system |

### Engineering (via gstack)
| Command | What It Does |
|---------|-------------|
| `/plan-ceo-review` | Rethink the problem, find the 10-star product |
| `/plan-eng-review` | Architecture, data flow, edge cases, test matrix |
| `/review` | Paranoid code review for production bugs |
| `/ship` | Sync, test, push, open PR |
| `/retro` | Engineering retro: commits, LOC, test ratios |
