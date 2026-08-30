---
name: investor-report
description: >
  Generate concise investor reports for Solum Health. Pulls metrics from Google Sheets,
  analyzes customer conversations from Fathom, and produces a structured DOCX report
  matching the investor update template. Use this skill when the user says "investor
  report", "investor update", "monthly report for investors", "board update", "generate
  investor deck", "how are we doing this month", or any variation of wanting a periodic
  investor-facing summary. Default period: previous calendar month. User can specify a
  different period.
---

# Investor Report

Generate a concise, data-driven investor report for Solum Health. Pulls metrics from
Google Sheets and customer conversation insights from Fathom. Outputs a DOCX file
matching the investor update template.

## API Authentication

### Fathom

Fathom is accessed via MCP tools (`mcp__claude_ai_Fathom__*`). There is no REST/GraphQL endpoint and no API key.

No API key is required — Fathom is wired through JP's claude.ai connection:

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

## Template Structure

The DOCX template lives at:
`~/Documents/Claude/Agents/Investor Report/Investor Update Template.docx`

The report follows this EXACT structure. No headings, no markdown. Just bold section
labels followed by bullet lists or a metrics table. Font is Montserrat 11pt, US Letter,
1" margins.

```
Subject: Investor Update {Month} {Year} - Solum Health 🚀

What do we do?, again.
{One-line positioning statement. Same line every month. Reminds investors what we do.}
Default: "Solum Health helps Specialty Clinics grow with a 24/7 AI front desk that
automates intake and insurance verification tasks."

{1-2 sentence exec summary leading with the biggest news of the month. Founder voice,
conversational, first person ("we"). End with what it means commercially, not a
metrics recap.}

Metrics:
  {3-column table: Metric | Value ({Month} {Year}) | MoM Δ vs {PrevMonth} {Year}}
  Rows: Clients (Live), Clients (Signed), ARR, Cash on Hand (USD), Monthly Burn (USD),
  Runway (Months). Use ▲ / ▼ / 0% for direction.

Asks:
  * {Specific request: intros, hires, advice}
  * {Another ask}

Highlights:
  * {Product launch, with revenue/upsell signal}
  * {Commercial win: closes, upsells, win-backs}
  * {Pipeline event: dinner, conference, event}

Lowlights:
  * {Outage or incident with what we did about it}
  * {Bottleneck (e.g., signed-to-live conversion)}
  * {Internal tooling or KPI gap being fixed}

Shout outs: (OPTIONAL — skip the section entirely if no names. Don't leave a blank header.)
  * {Thank specific investors or people who helped}

Goals/priorities for next month:
  * {Conversion goal: convert N signed to live}
  * {Sales goal: close N more, reaching N total customers; key logos by name}
  * {Product or motion goal: ship X, start PLG, etc.}

{Closing paragraph 1: founder voice. Excited / pull from customers. Acknowledge the
biggest constraint by name (ACV expansion, payor automation, etc.).}

{Closing paragraph 2: confidence statement on year-end goal with a number, plus
pipeline reasoning. Direct, not hedged.}

Best,
Juan Pablo Montoya
Founder, Solum Health
989 Market St, San Francisco, California
+1 628 276 2659
```

## DOCX Generation

Generate the report as a `.docx` file using `docx-js`. Match the template exactly:

- Font: Montserrat 11pt (22 half-points). JP's preferred font.
- Page: US Letter (12240 x 15840 DXA), 1" margins
- Line spacing: 1.15 (276 twips)
- Section labels: Bold, no colon space after
- Bullet items: Standard bullet list with 720 indent, 360 hanging
- Metrics: 3-column table (Metric | Value | MoM Δ). Bold first column.
- Empty paragraph between sections
- No headings, no horizontal rules
- Full signature block at the bottom (name, title, address, phone)

Save output to: `~/Documents/Claude/Agents/Investor Report/Solum Health Investor Update {Month} {Year}.docx`

## Data Sources

### 1. Google Sheets (KPI Dashboard)

**Spreadsheet ID:** `1zjXHQGdQXerCsWJ9fNZGaNoS-U8vwXHt`
**Sheet GID:** `1150083451`

Try reading via `gws sheets +read`. If unavailable, ask the user to paste metrics or
provide them inline. Never block the report on a single data source.

Core metrics to extract:
- Clients (Live) and Clients (Signed)
- ARR and MRR
- Cash on Hand
- Monthly Burn
- Runway (Months)
- MoM deltas for all

### 2. Fathom (Customer Conversations)

Pull customer-facing calls from the reporting period using the Fathom MCP tools.

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

The `date` field is a Unix millisecond timestamp. Filter results client-side to the reporting period:

```bash
# Convert period boundaries to Unix ms
PERIOD_START_MS=$(date -j -f "%Y-%m-%d" "{periodStart}" "+%s")000
PERIOD_END_MS=$(date -j -f "%Y-%m-%d" "{periodEnd}" "+%s")000

# Then filter with jq:
| jq --arg start "$PERIOD_START_MS" --arg end "$PERIOD_END_MS" \
  '[.data.transcripts[] | select((.date | tonumber) >= ($start | tonumber) and (.date | tonumber) <= ($end | tonumber))]'
```

If the period has 50+ meetings, make a second call and adjust the date filter to cover the earlier half.

Note: `action_items` is a string (not an array). Parse it as plain text.

**Filter to customer calls only:**

KEEP calls where:
- Title contains a company name + "Solum" (e.g., "TRAAC X Solum Health")
- Title contains "Assessment", "FUP", "Onboarding", "Demo", "Touchpoint", "Alignment"
- At least one participant is NOT @getsolum.com

EXCLUDE calls where:
- All participants are @getsolum.com (internal)
- Title contains "Daily", "Weekly Master-Room", "Roman Coliseum", "CEO Operations",
  "Growth Solum", "Product Operations", "Standup", "Interview"
- Title suggests personal/non-business meetings

For calls with summaries, extract:
- Customer name and topics discussed
- Expansion signals (new locations, more services, referrals)
- Risk signals (pricing concerns, churn, competitor mentions)
- Key themes across all calls

## Writing Rules

These are non-negotiable:

1. **Use the founder's actual words.** If the user provides bullet points or notes, use
   their phrasing. Clean up typos and grammar but do NOT rewrite their voice.
2. **No AI language.** Ban: "significant progress", "gaining traction", "we're excited",
   "leveraging", "streamlining", "driving growth", "robust". If it sounds like ChatGPT
   wrote it, rewrite it.
3. **No em dashes.** Use commas or periods instead.
4. **Short sentences.** 2-3 sentences per bullet max.
5. **Specific over vague.** Name the client, name the number, name the action.
6. **First person.** "We" not "the company" or "Solum Health".
7. **Conversational.** Like you're writing to people who already know the business.
8. **Honest about lows.** Say what went wrong, say why, say what you're doing. No spin.
9. **Always proofread.** JP's drafts often have Spanglish typos ("scalign", "aimign",
   "fortunatley", "breache", "HIPPA", "KPs", "Clientrs", "fromc ustomers", "importante",
   "portcos"). Always normalize: scaling, aiming, fortunately, breach, HIPAA, KPIs,
   clients, "from customers", important, "portfolio companies" (or keep "portcos" — VC
   slang is fine if intentional). Fix without flagging unless the meaning is unclear.
10. **Match JP's phrasing patterns.** He likes:
    - "That is our sweet spot right now." (declarative ICP statement)
    - "Strong early signal that this is a real revenue line, not just a feature."
    - "Out of our control but customers felt it." (honest framing for incidents)
    - "We have only ever lost two customers..." (qualifies bad news with context)
    - "I remain confident in our goal of closing the year at $X..." (sign-off)
11. **Lead the exec summary with the news, not the metrics.** "April was a product
    month. We launched X..." beats "ARR up 12% MoM." Metrics belong in the table.
12. **Asks are short.** 2-3 bullets max. No verbose justification. Each ask should be
    one sentence.
13. **Goals can run on.** JP often packs 2-3 related ideas into a single goal bullet
    (e.g., "Close 3 more, reaching 26 total. Confirm kickoff with our biggest fish, a
    700-location therapy clinic. Designing a Florida pilot..."). Don't over-split.
14. **"$X to $Y" not "$X-$Y".** Skill rule against em/en dashes still applies even
    though JP sometimes uses them.
15. **Subject line format:** "Investor Update {Month} {Year} - Solum Health 🚀"
    (the rocket emoji is part of the standard).

## Workflow

1. **Determine period:** Default = previous calendar month. Parse user input for custom range.
2. **Collect metrics:** Try Google Sheet first. Fall back to user-provided data.
3. **Pull Fathom data:** Query the Fathom MCP tools via curl (see above). Filter by date range client-side. Extract customer calls and summaries. Analyze themes.
4. **Ask the user for their input:** Before generating, ask for:
   - Any specific highlights they want to include
   - Any lowlights or challenges
   - Asks for investors
   - Shout outs
   - Goals for next month
   If the user already provided this info, skip asking.
5. **Generate the DOCX:** Use docx-js to create the file matching the template format exactly.
6. **Validate:** Run `python scripts/office/validate.py` on the output.
7. **Tell the user** where the file was saved.

## DOCX Code Reference

Use this structure for generating the document with docx-js:

```javascript
const { Document, Packer, Paragraph, TextRun, AlignmentType, LevelFormat } = require('docx');
const fs = require('fs');

const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0,
        format: LevelFormat.BULLET,
        text: "\u2022",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } }
      }]
    }]
  },
  styles: {
    default: {
      document: {
        run: { font: "Arial", size: 22 }  // 11pt
      }
    }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      // Subject line: "Subject:" bold + rest normal
      new Paragraph({
        children: [
          new TextRun({ text: "Subject:", bold: true }),
          new TextRun(" Solum Health Investor Update: {Month} {Year}")
        ]
      }),
      // Empty line
      new Paragraph({}),
      // Exec summary
      new Paragraph({ children: [new TextRun("{exec summary}")] }),
      // Empty line
      new Paragraph({}),
      // Metrics header
      new Paragraph({ children: [new TextRun({ text: "Metrics:", bold: true })] }),
      // Metric bullets with bold labels
      new Paragraph({
        numbering: { reference: "bullets", level: 0 },
        children: [
          new TextRun({ text: "Revenue:", bold: true }),
          new TextRun(" ${value} ({delta})")
        ]
      }),
      // ... more metrics
      // Empty line
      new Paragraph({}),
      // Asks header
      new Paragraph({ children: [new TextRun({ text: "Asks:", bold: true })] }),
      // Ask bullets (normal text)
      // ... same pattern for Highlights, Lowlights, Shout outs, Goals
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outputPath, buffer);
});
```

Each section follows the same pattern:
1. Bold label paragraph (e.g., "Highlights:")
2. Bullet list items using numbering reference
3. Empty paragraph separator

## Integration Notes

- Depends on: Fathom API (key in ~/.claude/.api-keys.json), docx npm package (install globally: `npm install -g docx`)
- Optional: Google Sheets via gws CLI
- Template reference: `~/Documents/Claude/Agents/Investor Report/Investor Update Template.docx`
- Output goes to same directory with month/year in filename
